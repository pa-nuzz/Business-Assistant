"""Cache Service - Redis-backed caching for API responses and queries."""
import logging
import hashlib
import json
from functools import wraps
from typing import Any, Optional, Callable
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Default cache TTL in seconds
DEFAULT_TTL = 300  # 5 minutes
LONG_TTL = 3600    # 1 hour
SHORT_TTL = 60     # 1 minute


class CacheService:
    """Service for managing cached data with Redis backend."""

    @staticmethod
    def get_key(*parts: str) -> str:
        """Generate a cache key from parts."""
        return ":".join(str(p) for p in parts)

    @staticmethod
    def get_or_set(
        key: str,
        getter: Callable,
        ttl: int = DEFAULT_TTL,
        version: Optional[str] = None
    ) -> Any:
        """Get from cache or compute and store."""
        cached = cache.get(key, version=version)
        if cached is not None:
            return cached
        
        value = getter()
        cache.set(key, value, ttl, version=version)
        return value

    @staticmethod
    def invalidate(*patterns: str) -> int:
        """Invalidate cache keys matching patterns."""
        count = 0
        for pattern in patterns:
            # Try exact key first
            if cache.delete(pattern):
                count += 1
            
            # Try pattern match for Redis
            try:
                # Django cache doesn't support pattern delete natively
                # We use versioned keys for invalidation
                cache.delete_pattern(pattern)
            except AttributeError:
                pass
        
        logger.info(f"Invalidated {count} cache entries for patterns: {patterns}")
        return count

    @staticmethod
    def invalidate_by_prefix(prefix: str) -> None:
        """Invalidate all keys with a given prefix."""
        # Use Redis SCAN if available
        try:
            from django_redis import get_redis_connection
            redis = get_redis_connection("default")
            pattern = f"{prefix}*"
            cursor = 0
            while True:
                cursor, keys = redis.scan(cursor, match=pattern, count=100)
                if keys:
                    redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Could not invalidate by prefix: {e}")


def cached(ttl: int = DEFAULT_TTL, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                arg_hash = hashlib.md5(
                    json.dumps(args, sort_keys=True, default=str).encode()
                ).hexdigest()[:8]
                cache_key += f":{arg_hash}"
            if kwargs:
                kwarg_hash = hashlib.md5(
                    json.dumps(kwargs, sort_keys=True, default=str).encode()
                ).hexdigest()[:8]
                cache_key += f":{kwarg_hash}"
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def cache_model_instance(model_class, ttl: int = LONG_TTL):
    """Cache decorator for model instance lookups."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to find ID in args/kwargs
            instance_id = None
            if args and len(args) > 0:
                instance_id = str(args[0])
            elif 'pk' in kwargs:
                instance_id = str(kwargs['pk'])
            elif 'id' in kwargs:
                instance_id = str(kwargs['id'])
            
            if instance_id:
                cache_key = f"model:{model_class.__name__.lower()}:{instance_id}"
                cached = cache.get(cache_key)
                if cached is not None:
                    return cached
                
                result = func(*args, **kwargs)
                if result:
                    cache.set(cache_key, result, ttl)
                return result
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_model_cache(model_name: str, instance_id: str) -> None:
    """Invalidate cache for a specific model instance."""
    cache_key = f"model:{model_name.lower()}:{instance_id}"
    cache.delete(cache_key)
    logger.debug(f"Invalidated cache for {model_name} {instance_id}")


class QueryCache:
    """Cache for expensive database queries."""
    
    @staticmethod
    def cache_queryset(queryset, key: str, ttl: int = DEFAULT_TTL):
        """Cache a queryset result."""
        def getter():
            return list(queryset)
        
        return CacheService.get_or_set(key, getter, ttl)
    
    @staticmethod
    def cache_count(queryset, key: str, ttl: int = DEFAULT_TTL) -> int:
        """Cache a queryset count."""
        def getter():
            return queryset.count()
        
        return CacheService.get_or_set(key, getter, ttl)


class APICache:
    """Cache for API responses."""
    
    @staticmethod
    def get_response_cache_key(request) -> str:
        """Generate cache key for API response."""
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else 'anon'
        path = request.path
        params = sorted(request.GET.items())
        params_str = json.dumps(params, sort_keys=True)
        
        key = f"api:{user_id}:{path}:{hashlib.md5(params_str.encode()).hexdigest()[:12]}"
        return key
    
    @staticmethod
    def cache_response(request, response_data: dict, ttl: int = DEFAULT_TTL) -> None:
        """Cache an API response."""
        key = APICache.get_response_cache_key(request)
        cache.set(key, response_data, ttl)
    
    @staticmethod
    def get_cached_response(request) -> Optional[dict]:
        """Get cached API response."""
        key = APICache.get_response_cache_key(request)
        return cache.get(key)
    
    @staticmethod
    def invalidate_user_cache(user_id: int) -> None:
        """Invalidate all cached responses for a user."""
        pattern = f"api:{user_id}:*"
        CacheService.invalidate_by_prefix(pattern)
