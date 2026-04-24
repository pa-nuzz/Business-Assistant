"""
Security utilities.

Key rules enforced here:
  1. user_id is ALWAYS taken from the authenticated session — never from model output
  2. File uploads are validated before touching the filesystem
  3. Tool args are sanitized before execution
  4. No raw SQL ever reaches the DB through tools
"""
import re
import os
import logging
import zipfile
from typing import Any
from io import BytesIO

logger = logging.getLogger(__name__)

# ─── File Upload Security ─────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

# Dangerous signatures that indicate executable/malicious content
BLOCKED_SIGNATURES = [
    b"\x4D\x5A",          # Windows executable (MZ)
    b"\x7F\x45\x4C\x46",  # ELF executable
    b"PK\x03\x04",        # ZIP (generic — will be validated further for DOCX)
    b"<?php",             # PHP code
    b"#!/",               # Shell script shebang
    b"<%",                # ASP/JSP tag
]


def _validate_magic_bytes(file_obj, ext: str) -> tuple[bool, str]:
    """
    Validate actual file content (magic bytes) to prevent extension spoofing.
    Uses built-in Python modules — no external dependencies.
    """
    try:
        file_obj.seek(0)
        header = file_obj.read(4096)
        file_obj.seek(0)
    except Exception:
        return False, "Could not read file content for validation."

    if not header:
        return False, "Empty file."

    # Check for dangerous signatures first
    for sig in BLOCKED_SIGNATURES:
        if header.startswith(sig) and ext != "docx":
            # DOCX is a ZIP, so we allow PK header only for docx
            return False, "File content does not match allowed types. Possible executable or script detected."

    if ext == "pdf":
        if not header.startswith(b"%PDF"):
            return False, "Invalid PDF file content."
        return True, ""

    if ext == "docx":
        # DOCX is a ZIP containing word/document.xml
        try:
            with zipfile.ZipFile(BytesIO(header)) as zf:
                if "word/document.xml" not in zf.namelist():
                    return False, "Invalid DOCX file: missing word/document.xml."
            return True, ""
        except zipfile.BadZipFile:
            return False, "Invalid DOCX file: not a valid ZIP archive."

    if ext == "txt":
        # Reject if it looks like a script/executable
        dangerous_patterns = [b"<?php", b"#!/", b"<script", b"<%", b"%PDF", b"\x4D\x5A"]
        lower_header = header.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in lower_header:
                return False, "TXT file contains suspicious content."
        # Check it's mostly readable text
        try:
            header.decode("utf-8")
            return True, ""
        except UnicodeDecodeError:
            # Allow if it's mostly ASCII
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 32}
                                   | set(range(32, 127)))
            non_text = sum(1 for b in header if b not in text_chars)
            if non_text / len(header) > 0.3:
                return False, "File does not appear to be valid text."
            return True, ""

    return False, "Unsupported file type for magic byte validation."


def validate_uploaded_file(file) -> tuple[bool, str]:
    """
    Validates an uploaded file before processing.
    Returns (is_valid, error_message).
    """
    # Check extension
    name = getattr(file, "name", "")
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '.{ext}' not allowed. Use PDF, DOCX, or TXT."

    # Check content type header (can be spoofed, but adds a layer)
    content_type = getattr(file, "content_type", "")
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Suspicious MIME type: {content_type} for file: {name}")
        # Don't reject — MIME headers aren't reliable. Just log it.

    # Check for path traversal in filename
    if ".." in name or "/" in name or "\\" in name:
        return False, "Invalid filename."

    # Validate actual file content (magic bytes)
    valid, error = _validate_magic_bytes(file, ext)
    if not valid:
        return False, error

    return True, ""


# ─── Tool Argument Sanitization ───────────────────────────────────────────────

def sanitize_tool_args(tool_name: str, args: dict, authenticated_user_id: int) -> dict:
    """
    Enforces that user_id in tool args always matches the authenticated user.
    This prevents the AI model from accessing other users' data even if it tries to.
    """
    PROTECTED_TOOLS = {
        "get_business_profile",
        "get_user_memory",
        "save_memory",
        "list_documents",
        "get_document_summary",
        "search_documents",
        "create_task",
        "get_task_details",
        "update_task",
        "delete_task",
        "list_tasks",
    }

    if tool_name in PROTECTED_TOOLS and "user_id" in args:
        if args["user_id"] != authenticated_user_id:
            logger.warning(
                f"Tool {tool_name} attempted with wrong user_id "
                f"(got {args['user_id']}, expected {authenticated_user_id}). "
                f"Overriding to correct user_id."
            )
            args["user_id"] = authenticated_user_id

    return args


def enforce_user_id(tool_name: str, args: dict, user_id: int) -> dict:
    """
    Shorthand — always inject correct user_id into protected tool args.
    Call this before execute_tool() in the agent loop.
    """
    args = dict(args)  # don't mutate original
    args["user_id"] = user_id  # always override, never trust model-provided user_id
    return args


# ─── Input Sanitization ───────────────────────────────────────────────────────

def sanitize_user_message(text: str) -> str:
    """
    Basic sanitization for user messages.
    Strips control characters and excessive whitespace.
    """
    # Remove null bytes and control chars (except newlines/tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize whitespace
    text = re.sub(r" {3,}", "  ", text)
    return text.strip()


def is_safe_doc_id(doc_id: str) -> bool:
    """Validate that a doc_id is a proper UUID (prevents injection)."""
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    return bool(uuid_pattern.match(str(doc_id)))
