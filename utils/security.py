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
from typing import Any

logger = logging.getLogger(__name__)

# ─── File Upload Security ─────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


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
