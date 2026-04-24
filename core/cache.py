"""
Redis caching configuration and utilities.
"""
import logging
import json
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing Redis cache operations."""
    
    @staticmethod
    def get(key: str, default=None):
        """Get value from cache."""
        try:
            value = cache.get(key)
            if value is None:
                return default
            return value
        except Exception as e:
            logger.exception(f"Cache get failed for key: {key}")
            return default
    
    @staticmethod
    def set(key: str, value, timeout: int = 300):
        """Set value in cache with timeout (default 5 minutes)."""
        try:
            cache.set(key, value, timeout)
        except Exception as e:
            logger.exception(f"Cache set failed for key: {key}")
    
    @staticmethod
    def delete(key: str):
        """Delete key from cache."""
        try:
            cache.delete(key)
        except Exception as e:
            logger.exception(f"Cache delete failed for key: {key}")
    
    @staticmethod
    def delete_pattern(pattern: str):
        """Delete keys matching pattern."""
        try:
            from django.core.cache import caches
            redis_cache = caches['default']
            if hasattr(redis_cache, 'client'):
                keys = redis_cache.client.keys(pattern)
                if keys:
                    redis_cache.client.delete(*keys)
        except Exception as e:
            logger.exception(f"Cache delete pattern failed for: {pattern}")
    
    @staticmethod
    def get_or_set(key: str, callback, timeout: int = 300):
        """Get value from cache or set using callback."""
        value = CacheService.get(key)
        if value is None:
            value = callback()
            CacheService.set(key, value, timeout)
        return value
    
    @staticmethod
    def invalidate_user_cache(user_id: int):
        """Invalidate all cache entries for a user."""
        patterns = [
            f"user:{user_id}:*",
            f"profile:{user_id}:*",
            f"tasks:{user_id}:*",
            f"conversations:{user_id}:*",
        ]
        for pattern in patterns:
            CacheService.delete_pattern(pattern)
    
    @staticmethod
    def invalidate_document_cache(doc_id: str):
        """Invalidate cache for a document."""
        patterns = [
            f"document:{doc_id}:*",
            f"document_chunks:{doc_id}:*",
        ]
        for pattern in patterns:
            CacheService.delete_pattern(pattern)


def cache_result(key_prefix: str, timeout: int = 300):
    """
    Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache key
        timeout: Cache timeout in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            result = CacheService.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheService.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
