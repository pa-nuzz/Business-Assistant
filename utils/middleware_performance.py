"""Performance Monitoring Middleware - Request timing, query profiling, slow query alerts."""
import time
import logging
from django.db import connection, reset_queries
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

SLOW_QUERY_THRESHOLD_MS = 500  # Alert if query takes >500ms
SLOW_REQUEST_THRESHOLD_MS = 1000  # Alert if request takes >1s


class PerformanceMonitoringMiddleware:
    """
    Middleware to monitor request performance:
    - Request timing (total duration)
    - Query count and duration profiling
    - Slow query detection and alerting
    - Cache hit/miss tracking
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip monitoring for static/media files
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        start_time = time.perf_counter()
        
        # Enable query logging in DEBUG mode
        if settings.DEBUG:
            reset_queries()
        
        response = self.get_response(request)
        
        # Calculate metrics
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Get query stats
        query_count = 0
        query_time_ms = 0
        if settings.DEBUG:
            queries = connection.queries
            query_count = len(queries)
            query_time_ms = sum(float(q.get('time', 0)) * 1000 for q in queries)
        
        # Add headers for monitoring
        response['X-Request-Duration-Ms'] = f'{duration_ms:.2f}'
        response['X-Query-Count'] = str(query_count)
        response['X-Query-Time-Ms'] = f'{query_time_ms:.2f}'
        
        # Store metrics in cache for dashboard
        self._store_metrics(request, duration_ms, query_count, query_time_ms)
        
        # Alert on slow queries
        if query_time_ms > SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                f"Slow queries detected: {query_count} queries took {query_time_ms:.2f}ms "
                f"for {request.method} {request.path}"
            )
        
        # Alert on slow requests
        if duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                f"Slow request: {request.method} {request.path} took {duration_ms:.2f}ms "
                f"({query_count} queries, {query_time_ms:.2f}ms query time)"
            )
        
        return response
    
    def _store_metrics(self, request, duration_ms, query_count, query_time_ms):
        """Store metrics in cache for real-time dashboard."""
        try:
            # Store in a time-windowed cache key
            timestamp = int(time.time())
            window = timestamp // 60  # 1-minute windows
            
            # Request metrics
            cache_key = f"perf:requests:{window}"
            metrics = cache.get(cache_key, [])
            metrics.append({
                'path': request.path,
                'method': request.method,
                'duration_ms': round(duration_ms, 2),
                'query_count': query_count,
                'query_time_ms': round(query_time_ms, 2),
                'timestamp': timestamp,
            })
            # Keep only last 100 requests per window
            metrics = metrics[-100:]
            cache.set(cache_key, metrics, 300)  # 5 minute TTL
            
            # Aggregate stats per endpoint
            endpoint_key = f"perf:endpoint:{request.method}:{request.path}"
            stats = cache.get(endpoint_key, {
                'count': 0,
                'total_duration': 0,
                'total_queries': 0,
                'slow_count': 0,
            })
            stats['count'] += 1
            stats['total_duration'] += duration_ms
            stats['total_queries'] += query_count
            if duration_ms > SLOW_REQUEST_THRESHOLD_MS:
                stats['slow_count'] += 1
            cache.set(endpoint_key, stats, 3600)  # 1 hour TTL
            
        except Exception:
            pass  # Don't let metrics break the request


class QueryCountAlertMiddleware:
    """
    Alert when a request makes too many database queries.
    Useful for catching N+1 query issues.
    """
    
    MAX_QUERIES = 50  # Alert if more than 50 queries per request
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if settings.DEBUG:
            reset_queries()
        
        response = self.get_response(request)
        
        if settings.DEBUG:
            query_count = len(connection.queries)
            if query_count > self.MAX_QUERIES:
                logger.warning(
                    f"N+1 query alert: {query_count} queries for "
                    f"{request.method} {request.path}"
                )
                # Log the queries for debugging
                for i, query in enumerate(connection.queries[-10:]):
                    logger.debug(f"Query {query_count-10+i}: {query.get('sql', '')[:200]}")
        
        return response
