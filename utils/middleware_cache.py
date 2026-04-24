"""
Cache headers middleware for API responses.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class CacheHeadersMiddleware:
    """
    Middleware to add caching headers to API responses.
    Configurable cache times for different endpoint types.
    """
    
    # Cache times in seconds
    CACHE_TIMES = {
        'public': 300,      # 5 minutes for public data
        'private': 60,      # 1 minute for private user data
        'short': 30,        # 30 seconds for frequently changing data
        'none': 0,          # No caching
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only add cache headers to successful GET requests
        if request.method == 'GET' and response.status_code == 200:
            cache_type = self.get_cache_type(request)
            if cache_type and cache_type != 'none':
                self.add_cache_headers(response, cache_type)
        
        return response
    
    def get_cache_type(self, request):
        """Determine cache type based on request path."""
        path = request.path
        
        # Public endpoints (user profiles, static data)
        if '/api/v1/public/' in path or '/api/health' in path:
            return 'public'
        
        # Private user data (tasks, conversations, documents)
        if '/api/v1/tasks/' in path or '/api/v1/conversations/' in path:
            return 'private'
        
        # Frequently changing data (notifications, activity)
        if '/api/v1/notifications/' in path or '/api/v1/activity/' in path:
            return 'short'
        
        # Default: no caching
        return 'none'
    
    def add_cache_headers(self, response, cache_type):
        """Add cache headers to response."""
        max_age = self.CACHE_TIMES.get(cache_type, 0)
        
        if max_age > 0:
            response['Cache-Control'] = f'private, max-age={max_age}'
            response['X-Cache-TTL'] = str(max_age)
        else:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
