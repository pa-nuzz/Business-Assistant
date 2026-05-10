"""
Rate limiting configuration for API endpoints.
Uses Django REST Framework's ScopedRateThrottle.
"""
from rest_framework.throttling import ScopedRateThrottle


class BurstRateThrottle(ScopedRateThrottle):
    """High burst rate for critical operations (100 requests/minute)."""
    scope = 'burst'
    rate = '100/min'


class StandardRateThrottle(ScopedRateThrottle):
    """Standard rate for regular operations (60 requests/minute)."""
    scope = 'standard'
    rate = '60/min'


class StrictRateThrottle(ScopedRateThrottle):
    """Strict rate for expensive operations (10 requests/minute)."""
    scope = 'strict'
    rate = '10/min'


class UploadRateThrottle(ScopedRateThrottle):
    """Rate limit for file uploads (5 requests/minute)."""
    scope = 'upload'
    rate = '5/min'


class AuthRateThrottle(ScopedRateThrottle):
    """Rate limit for auth operations (20 requests/minute)."""
    scope = 'auth'
    rate = '20/min'


# Rate limit scopes configuration
RATE_LIMIT_SCOPES = {
    # Auth endpoints
    'auth_register': 'auth',
    'auth_login': 'auth',
    'auth_verify': 'auth',
    'auth_password': 'auth',
    
    # Chat endpoints
    'chat': 'standard',
    'chat_stream': 'burst',
    
    # Task endpoints
    'task': 'standard',
    'task_write': 'strict',
    
    # Document endpoints
    'upload': 'upload',
    'document': 'standard',
    
    # Profile endpoints
    'profile': 'standard',
    
    # Admin endpoints
    'admin': 'strict',
}


def get_rate_limit_class(scope: str):
    """Get the appropriate throttle class for a scope."""
    scope_mapping = {
        'burst': BurstRateThrottle,
        'standard': StandardRateThrottle,
        'strict': StrictRateThrottle,
        'upload': UploadRateThrottle,
        'auth': AuthRateThrottle,
    }
    return scope_mapping.get(scope, StandardRateThrottle)
