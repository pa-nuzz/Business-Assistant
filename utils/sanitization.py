"""
Input sanitization utilities.
Uses bleach to strip HTML/JS from user inputs while preserving safe content.
Includes file upload validation with MIME type checking.
"""
import re
import bleach
from pathlib import Path
from typing import Optional
from django.core.exceptions import ValidationError

# Optional python-magic import (requires libmagic system library)
try:
    import magic
    HAS_MAGIC = True
except (ImportError, OSError):
    HAS_MAGIC = False
    magic = None

# ─── File Upload Security (Phase 3.3) ─────────────────────────────────────────
ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown'
]
MAX_UPLOAD_SIZE_MB = 25
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


def validate_file_upload(file) -> None:
    """
    Validate file upload - checks extension, MIME type, and size.
    Raises ValidationError if file is not allowed.
    
    Args:
        file: Django UploadedFile object
        
    Raises:
        ValidationError: If file extension, MIME type, or size is invalid
    """
    # Check file extension
    ext = Path(file.name).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError(f"File type '{ext}' is not allowed. Allowed types: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}")
    
    # Check file size
    if file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(f"File exceeds the {MAX_UPLOAD_SIZE_MB}MB limit.")

    # Check MIME type using python-magic (if available)
    if HAS_MAGIC:
        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)  # Reset file pointer

        if mime not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"File content type '{mime}' does not match allowed types.")
    else:
        # Fallback: validate by content type header only
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"File type '{file.content_type}' is not allowed.")


def sanitize_filename_strict(name: Optional[str]) -> str:
    """
    Strict filename sanitization - removes all special characters.
    Used for uploaded files before saving.
    
    Args:
        name: Original filename
        
    Returns:
        Safe filename with only alphanumeric, underscore, hyphen, and dot
    """
    if not name:
        return "unnamed"
    
    # Remove path traversal attempts
    name = Path(name).name
    
    # Remove all special characters except alphanumeric, underscore, hyphen, dot
    name = re.sub(r'[^\w\-.]', '_', name)
    
    # Remove multiple consecutive dots (prevent .. patterns)
    name = re.sub(r'\.{2,}', '_', name)
    
    # Limit length
    if len(name) > 100:
        name = name[:100]
    
    return name.strip() or "unnamed"

# Define allowed tags and attributes for rich text (if needed)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    '*': ['class']
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_plain_text(text: Optional[str], max_length: int = 10000) -> str:
    """
    Sanitize plain text input - removes ALL HTML/JS.
    Use for: task titles, memory keys, tags, simple text fields.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (truncated if longer)
    
    Returns:
        Clean, sanitized plain text
    """
    if not text:
        return ""
    
    # Strip all HTML tags
    cleaned = bleach.clean(text, tags=[], strip=True)
    
    # Limit length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned.strip()


def sanitize_rich_text(text: Optional[str], max_length: int = 50000) -> str:
    """
    Sanitize rich text input - allows safe HTML tags.
    Use for: task descriptions, comments, memory values.
    
    Args:
        text: Input HTML/text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized HTML with safe tags preserved
    """
    if not text:
        return ""
    
    # Clean with allowed tags
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )
    
    # Limit length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned.strip()


def sanitize_filename(filename: Optional[str]) -> str:
    """
    Sanitize filename - removes path traversal and dangerous characters.
    
    Args:
        filename: Original filename
    
    Returns:
        Safe filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path components
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + '.' + ext if ext else name[:255]
    
    return filename.strip()


def sanitize_search_query(query: Optional[str], max_length: int = 500) -> str:
    """
    Sanitize search query - removes special chars that could affect search.
    
    Args:
        query: Search query string
        max_length: Maximum query length
    
    Returns:
        Clean search query
    """
    if not query:
        return ""
    
    # Remove HTML
    cleaned = bleach.clean(query, tags=[], strip=True)
    
    # Remove SQL-like special characters (defense in depth)
    dangerous_chars = [';', '--', '/*', '*/', '\\', '\x00']
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, ' ')
    
    # Limit length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned.strip()


# Shortcut aliases for cleaner imports
def clean_text(text: Optional[str], max_length: int = 10000) -> str:
    """Alias for sanitize_plain_text."""
    return sanitize_plain_text(text, max_length)


def clean_html(text: Optional[str], max_length: int = 50000) -> str:
    """Alias for sanitize_rich_text."""
    return sanitize_rich_text(text, max_length)
