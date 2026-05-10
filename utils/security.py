"""
Security utilities.

Key rules enforced here:
  1. user_id is ALWAYS taken from the authenticated session — never from model output
  2. File uploads are validated before touching the filesystem
  3. Tool args are sanitized before execution
  4. No raw SQL ever reaches the DB through tools
  5. Enhanced input validation and XSS prevention
"""
import re
import os
import logging
import zipfile
import hashlib
import secrets
from typing import Any, Dict, List
from io import BytesIO
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str
from bleach import clean
from bleach.css_sanitizer import CSSSanitizer

logger = logging.getLogger(__name__)

# ─── Input Validation & Sanitization ────────────────────────────────────────────

# XSS prevention patterns
XSS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'on\w+\s*=',  # onclick=, onload=, etc.
    r'<iframe[^>]*>',
    r'<object[^>]*>',
    r'<embed[^>]*>',
    r'<link[^>]*>',
    r'<meta[^>]*>',
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
    r'(--|#|\/\*|\*\/)',
    r'(\bOR\b.*\b1\s*=\s*1\b)',
    r'(\bAND\b.*\b1\s*=\s*1\b)',
    r'(\'\s*OR\s*\'.*\'.*\')',
    r'(\".*OR.*\".*=.*\")',
]

# CSS sanitizer for safe HTML
CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=[
        'color', 'background-color', 'font-size', 'font-weight', 'text-align',
        'margin', 'padding', 'border', 'width', 'height', 'display', 'position'
    ]
)

def sanitize_html(content: str, allowed_tags: List[str] = None, allowed_attributes: Dict[str, List[str]] = None) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        content: HTML content to sanitize
        allowed_tags: List of allowed HTML tags
        allowed_attributes: Dict of allowed attributes per tag
    
    Returns:
        Sanitized HTML content
    """
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'a', 'span']
    
    if allowed_attributes is None:
        allowed_attributes = {
            'a': ['href', 'title'],
            'span': ['class'],
            '*': ['class']
        }
    
    return clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True,
        css_sanitizer=CSS_SANITIZER
    )

def validate_text_input(text: str, max_length: int = 1000, allow_empty: bool = False) -> str:
    """
    Validate and sanitize text input.
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are allowed
    
    Returns:
        Sanitized text
    
    Raises:
        ValidationError: If input is invalid
    """
    if not allow_empty and not text.strip():
        raise ValidationError("This field is required.")
    
    if len(text) > max_length:
        raise ValidationError(f"Text cannot exceed {max_length} characters.")
    
    # Check for XSS patterns
    text_lower = text.lower()
    for pattern in XSS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            raise ValidationError("Invalid characters detected.")
    
    # Sanitize the text
    sanitized = force_str(text)
    sanitized = sanitized.strip()
    
    return sanitized

def validate_email(email: str) -> str:
    """
    Validate email format and prevent email injection.
    
    Args:
        email: Email address to validate
    
    Returns:
        Normalized email
    
    Raises:
        ValidationError: If email is invalid
    """
    email = email.strip().lower()
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format.")
    
    # Check for injection attempts
    dangerous_chars = ['\n', '\r', '\0', '<', '>', '|', '&', ';']
    if any(char in email for char in dangerous_chars):
        raise ValidationError("Invalid characters in email.")
    
    return email

def validate_url(url: str, allowed_schemes: List[str] = None) -> str:
    """
    Validate URL and prevent malicious URLs.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes
    
    Returns:
        Normalized URL
    
    Raises:
        ValidationError: If URL is invalid
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    url = url.strip()
    
    # Check for dangerous protocols
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:', 'ftp:']
    for scheme in dangerous_schemes:
        if url.lower().startswith(scheme):
            raise ValidationError(f"URL scheme '{scheme}' is not allowed.")
    
    # Basic URL validation
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        raise ValidationError("Invalid URL format.")
    
    return url

def detect_sql_injection(input_text: str) -> bool:
    """
    Detect potential SQL injection attempts.
    
    Args:
        input_text: Text to analyze
    
    Returns:
        True if SQL injection pattern detected
    """
    text_upper = input_text.upper()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text_upper):
            return True
    return False

def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.
    
    Args:
        length: Token length
    
    Returns:
        Secure random token
    """
    return secrets.token_urlsafe(length)

def hash_sensitive_data(data: str, salt: str = None) -> str:
    """
    Hash sensitive data for logging/auditing.
    
    Args:
        data: Data to hash
        salt: Optional salt
    
    Returns:
        Hashed data
    """
    if salt is None:
        salt = "aeiou_ai_default_salt"
    
    return hashlib.sha256(f"{salt}{data}".encode()).hexdigest()

def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """
    Validate file size against maximum allowed size.
    
    Args:
        file_size: File size in bytes
        max_size_mb: Maximum size in MB
    
    Returns:
        True if file size is valid
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\-_.]', '', filename)
    
    # Limit length
    filename = filename[:255]
    
    return filename or "file"

# ─── Rate Limiting Utilities ─────────────────────────────────────────────────────

class RateLimiter:
    """
    Simple in-memory rate limiter for development/testing.
    In production, use Redis-based rate limiting.
    """
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            True if request is allowed
        """
        import time
        
        now = time.time()
        window_start = now - window
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True
        
        return False

# ─── Security Headers Middleware ─────────────────────────────────────────────────

def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for HTTP responses.
    
    Returns:
        Dictionary of security headers
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        ),
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Permissions-Policy': (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), vr=(), magnetometer=(), gyroscope=()'
        )
    }

# ─── Audit Logging ───────────────────────────────────────────────────────────

def log_security_event(event_type: str, details: Dict[str, Any], user_id: int = None):
    """
    Log security events for audit trail.
    
    Args:
        event_type: Type of security event
        details: Event details
        user_id: User ID if applicable
    """
    # Hash sensitive data for logging
    safe_details = {}
    for key, value in details.items():
        if 'password' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
            safe_details[key] = hash_sensitive_data(str(value))
        else:
            safe_details[key] = value
    
    logger.warning(
        f"Security Event: {event_type}",
        extra={
            'event_type': event_type,
            'user_id': user_id,
            'details': safe_details,
            'ip_address': details.get('ip_address'),
            'user_agent': details.get('user_agent')
        }
    )

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
