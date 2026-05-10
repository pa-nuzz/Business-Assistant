"""
Advanced Rate Limiting System for AEIOU AI.

Provides Redis-based rate limiting with:
- Multiple rate limit strategies
- Dynamic rate limit configuration
- Distributed rate limiting
- Rate limit analytics
"""
import json
import time
import logging
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Redis-based rate limiter for distributed applications.
    """
    
    def __init__(self, redis_client: Redis = None):
        self.redis_client = redis_client or self.get_redis_client()
        
        # Rate limit configurations
        self.rate_limits = {
            # Authentication endpoints
            'auth_login': {'requests': 5, 'window': 900},      # 5 per 15 minutes
            'auth_register': {'requests': 3, 'window': 3600},   # 3 per hour
            'auth_reset': {'requests': 3, 'window': 3600},      # 3 per hour
            
            # API endpoints
            'api_default': {'requests': 1000, 'window': 3600},  # 1000 per hour
            'api_upload': {'requests': 50, 'window': 3600},     # 50 per hour
            'api_search': {'requests': 100, 'window': 60},      # 100 per minute
            'api_chat': {'requests': 60, 'window': 60},         # 60 per minute
            
            # File operations
            'file_upload': {'requests': 10, 'window': 3600},    # 10 per hour
            'file_download': {'requests': 100, 'window': 3600}, # 100 per hour
            
            # Admin operations
            'admin_bulk': {'requests': 10, 'window': 3600},    # 10 per hour
            'admin_export': {'requests': 5, 'window': 3600},    # 5 per hour
        }
        
        # Default rate limit for uncategorized requests
        self.default_limit = {'requests': 100, 'window': 3600}
    
    def get_redis_client(self) -> Redis:
        """Get Redis client from Django cache configuration."""
        
        try:
            # Try to get Redis from Django cache
            if hasattr(cache, '_cache') and hasattr(cache._cache, 'client'):
                return cache._cache.client
            
            # Fallback to direct Redis connection
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            return Redis.from_url(redis_url, decode_responses=True)
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ImproperlyConfigured("Redis is required for rate limiting")
    
    def is_allowed(self, key: str, limit_config: Dict[str, int]) -> Dict[str, Any]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique identifier (user ID, IP, etc.)
            limit_config: Rate limit configuration
        
        Returns:
            Dictionary with allowance status and metadata
        """
        try:
            current_time = int(time.time())
            window_start = current_time - limit_config['window']
            
            # Redis key for this rate limit
            redis_key = f"rate_limit:{key}"
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current requests
            pipe.zcard(redis_key)
            
            # Add current request
            pipe.zadd(redis_key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(redis_key, limit_config['window'])
            
            results = pipe.execute()
            current_requests = results[1]
            
            # Check if under limit
            allowed = current_requests < limit_config['requests']
            
            return {
                'allowed': allowed,
                'current_requests': current_requests,
                'limit': limit_config['requests'],
                'window': limit_config['window'],
                'reset_time': current_time + limit_config['window'],
                'remaining': max(0, limit_config['requests'] - current_requests)
            }
            
        except RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow request if Redis is down
            return {
                'allowed': True,
                'current_requests': 0,
                'limit': limit_config['requests'],
                'window': limit_config['window'],
                'reset_time': int(time.time()) + limit_config['window'],
                'remaining': limit_config['requests']
            }
    
    def get_rate_limit_info(self, key: str, category: str) -> Dict[str, Any]:
        """
        Get current rate limit information.
        
        Args:
            key: Unique identifier
            category: Rate limit category
        
        Returns:
            Rate limit information
        """
        limit_config = self.rate_limits.get(category, self.default_limit)
        return self.is_allowed(key, limit_config)
    
    def clear_rate_limit(self, key: str, category: str = None):
        """
        Clear rate limit for a specific key or category.
        
        Args:
            key: Unique identifier
            category: Rate limit category (optional)
        """
        try:
            if category:
                redis_key = f"rate_limit:{category}:{key}"
            else:
                redis_key = f"rate_limit:{key}"
            
            self.redis_client.delete(redis_key)
            
        except RedisError as e:
            logger.error(f"Failed to clear rate limit: {e}")
    
    def get_rate_limit_stats(self, category: str = None) -> Dict[str, Any]:
        """
        Get rate limit statistics.
        
        Args:
            category: Rate limit category (optional)
        
        Returns:
            Rate limit statistics
        """
        try:
            pattern = f"rate_limit:{category}:*" if category else "rate_limit:*"
            keys = self.redis_client.keys(pattern)
            
            stats = {
                'total_keys': len(keys),
                'categories': {},
                'active_limits': 0
            }
            
            for key in keys:
                try:
                    # Extract category from key
                    key_parts = key.split(':')
                    if len(key_parts) >= 2:
                        cat = key_parts[1]
                        
                        # Get current request count
                        current_requests = self.redis_client.zcard(key)
                        
                        if cat not in stats['categories']:
                            stats['categories'][cat] = {
                                'requests': 0,
                                'unique_keys': 0
                            }
                        
                        stats['categories'][cat]['requests'] += current_requests
                        stats['categories'][cat]['unique_keys'] += 1
                        
                        if current_requests > 0:
                            stats['active_limits'] += 1
                            
                except RedisError:
                    continue
            
            return stats
            
        except RedisError as e:
            logger.error(f"Failed to get rate limit stats: {e}")
            return {'error': str(e)}


class RateLimitMiddleware:
    """
    Middleware to apply rate limiting to requests.
    """
    
    def __init__(self):
        self.limiter = RedisRateLimiter()
    
    def get_rate_limit_key(self, request) -> str:
        """
        Generate rate limit key for request.
        
        Args:
            request: Django request object
        
        Returns:
            Rate limit key
        """
        # Use user ID if authenticated, otherwise IP
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        else:
            ip = self.get_client_ip(request)
            return f"ip:{ip}"
    
    def get_client_ip(self, request) -> str:
        """Get client IP address."""
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        return ip or 'unknown'
    
    def get_rate_limit_category(self, request) -> str:
        """
        Determine rate limit category based on request.
        
        Args:
            request: Django request object
        
        Returns:
            Rate limit category
        """
        path = request.path.lower()
        method = request.method.upper()
        
        # Authentication endpoints
        if '/auth/login' in path:
            return 'auth_login'
        elif '/auth/register' in path:
            return 'auth_register'
        elif '/auth/reset' in path:
            return 'auth_reset'
        
        # File operations
        elif '/upload' in path and method == 'POST':
            return 'file_upload'
        elif '/download' in path:
            return 'file_download'
        
        # API operations
        elif '/api/' in path:
            if '/search' in path:
                return 'api_search'
            elif '/chat' in path:
                return 'api_chat'
            elif method in ['POST', 'PUT', 'DELETE']:
                return 'api_upload'  # Treat write operations as uploads
            else:
                return 'api_default'
        
        # Admin operations
        elif '/admin/' in path:
            if '/bulk' in path:
                return 'admin_bulk'
            elif '/export' in path:
                return 'admin_export'
        
        return 'default'
    
    def check_rate_limit(self, request) -> Dict[str, Any]:
        """
        Check if request is allowed based on rate limits.
        
        Args:
            request: Django request object
        
        Returns:
            Rate limit result
        """
        key = self.get_rate_limit_key(request)
        category = self.get_rate_limit_category(request)
        
        # Combine key and category for specific rate limiting
        full_key = f"{category}:{key}"
        
        return self.limiter.get_rate_limit_info(full_key, category)
    
    def get_rate_limit_headers(self, result: Dict[str, Any]) -> Dict[str, str]:
        """
        Get rate limit headers for response.
        
        Args:
            result: Rate limit result
        
        Returns:
            Rate limit headers
        """
        return {
            'X-RateLimit-Limit': str(result['limit']),
            'X-RateLimit-Remaining': str(result['remaining']),
            'X-RateLimit-Reset': str(result['reset_time']),
            'X-RateLimit-Window': str(result['window']),
        }


class RateLimitDecorator:
    """
    Decorator for rate limiting specific views or functions.
    """
    
    def __init__(self, category: str = 'default', key_func=None):
        self.category = category
        self.key_func = key_func
        self.limiter = RedisRateLimiter()
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # Try to get request from args
            request = None
            for arg in args:
                if hasattr(arg, 'META'):  # Django request object
                    request = arg
                    break
            
            if not request:
                # If no request found, allow the call
                return func(*args, **kwargs)
            
            # Get rate limit key
            if self.key_func:
                key = self.key_func(request)
            else:
                key = self.get_default_key(request)
            
            # Check rate limit
            result = self.limiter.get_rate_limit_info(key, self.category)
            
            if not result['allowed']:
                from django.http import JsonResponse
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'limit': result['limit'],
                        'window': result['window'],
                        'reset_time': result['reset_time']
                    },
                    status=429
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    def get_default_key(self, request) -> str:
        """Get default rate limit key."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            return f"ip:{ip}"


# Rate limiting decorators for common use cases
rate_limit_auth = RateLimitDecorator('auth_login')
rate_limit_api = RateLimitDecorator('api_default')
rate_limit_upload = RateLimitDecorator('file_upload')
rate_limit_chat = RateLimitDecorator('api_chat')
rate_limit_search = RateLimitDecorator('api_search')


def rate_limit(category: str = 'default', key_func=None):
    """
    Rate limiting decorator factory.
    
    Args:
        category: Rate limit category
        key_func: Function to generate rate limit key
    
    Returns:
        Rate limit decorator
    """
    return RateLimitDecorator(category, key_func)
