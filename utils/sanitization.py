"""
Input sanitization utilities.
Uses bleach to strip HTML/JS from user inputs while preserving safe content.
"""
import bleach
from typing import Optional

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
