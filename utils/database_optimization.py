"""
Database Optimization Utilities for AEIOU AI.

Provides query optimization, caching strategies, and performance monitoring.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Set
from django.db import connection, models
from django.core.cache import cache
from django.conf import settings
from django.db.models import QuerySet, Prefetch
from django.core.paginator import Paginator
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Database query optimization utilities.
    """
    
    @staticmethod
    def optimize_task_queryset(user_id: int = None, include_related: bool = True) -> QuerySet:
        """
        Get optimized task queryset with proper select_related and prefetch_related.
        
        Args:
            user_id: User ID to filter tasks
            include_related: Whether to include related objects
        
        Returns:
            Optimized QuerySet
        """
        from core.models import Task, TaskTag, TaskComment, TaskAttachment
        
        queryset = Task.objects.all()
        
        if user_id:
            queryset = queryset.filter(
                models.Q(created_by_id=user_id) | 
                models.Q(assignee_id=user_id) | 
                models.Q(user_id=user_id)
            )
        
        if include_related:
            # Select related objects (single relationships)
            queryset = queryset.select_related(
                'created_by',
                'assignee', 
                'business_profile',
                'user'
            )
            
            # Prefetch related objects (many relationships)
            queryset = queryset.prefetch_related(
                Prefetch('tags', queryset=TaskTag.objects.only('id', 'name', 'color')),
                Prefetch('comments', queryset=TaskComment.objects.select_related('user').only('id', 'content', 'created_at', 'user_id')),
                Prefetch('attachments', queryset=TaskAttachment.objects.only('id', 'filename', 'file_size', 'uploaded_at')),
                'subtasks',
                'ai_suggestions'
            )
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def optimize_document_queryset(user_id: int = None) -> QuerySet:
        """
        Get optimized document queryset.
        
        Args:
            user_id: User ID to filter documents
        
        Returns:
            Optimized QuerySet
        """
        from core.models import Document
        
        queryset = Document.objects.select_related(
            'uploaded_by',
            'business_profile'
        ).prefetch_related(
            'versions',
            'analyses'
        )
        
        if user_id:
            queryset = queryset.filter(uploaded_by_id=user_id)
        
        return queryset.order_by('-uploaded_at')
    
    @staticmethod
    def optimize_conversation_queryset(user_id: int = None) -> QuerySet:
        """
        Get optimized conversation queryset.
        
        Args:
            user_id: User ID to filter conversations
        
        Returns:
            Optimized QuerySet
        """
        from core.models import Conversation, Message
        
        queryset = Conversation.objects.select_related(
            'user',
            'business_profile'
        ).prefetch_related(
            Prefetch('messages', queryset=Message.objects.select_related('user').only('id', 'content', 'role', 'created_at', 'user_id').order_by('created_at'))
        )
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by('-updated_at')


class AdvancedCacheManager:
    """
    Advanced caching strategies for AEIOU AI.
    """
    
    def __init__(self):
        self.default_timeout = getattr(settings, 'CACHE_DEFAULT_TIMEOUT', 300)
        self.cache_prefix = getattr(settings, 'CACHE_PREFIX', 'aeiou_ai')
    
    def get_cache_key(self, key_type: str, identifier: str, *args) -> str:
        """
        Generate structured cache key.
        
        Args:
            key_type: Type of cache key (user, task, etc.)
            identifier: Primary identifier
            args: Additional arguments
        
        Returns:
            Structured cache key
        """
        key_parts = [self.cache_prefix, key_type, str(identifier)]
        key_parts.extend(str(arg) for arg in args)
        return ':'.join(key_parts)
    
    def cache_user_tasks(self, user_id: int, tasks_data: Dict[str, Any], timeout: int = None) -> str:
        """
        Cache user tasks data.
        
        Args:
            user_id: User ID
            tasks_data: Tasks data to cache
            timeout: Cache timeout in seconds
        
        Returns:
            Cache key
        """
        cache_key = self.get_cache_key('user_tasks', user_id)
        timeout = timeout or self.default_timeout
        cache.set(cache_key, tasks_data, timeout)
        return cache_key
    
    def get_user_tasks(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached user tasks data.
        
        Args:
            user_id: User ID
        
        Returns:
            Cached tasks data or None
        """
        cache_key = self.get_cache_key('user_tasks', user_id)
        return cache.get(cache_key)
    
    def invalidate_user_cache(self, user_id: int) -> None:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID
        """
        patterns = [
            f"{self.cache_prefix}:user_tasks:{user_id}",
            f"{self.cache_prefix}:user_profile:{user_id}",
            f"{self.cache_prefix}:user_conversations:{user_id}",
            f"{self.cache_prefix}:user_documents:{user_id}",
        ]
        
        for pattern in patterns:
            cache.delete(pattern)
    
    def cache_task_detail(self, task_id: str, task_data: Dict[str, Any], timeout: int = None) -> str:
        """
        Cache task detail data.
        
        Args:
            task_id: Task ID
            task_data: Task data to cache
            timeout: Cache timeout in seconds
        
        Returns:
            Cache key
        """
        cache_key = self.get_cache_key('task_detail', task_id)
        timeout = timeout or self.default_timeout
        cache.set(cache_key, task_data, timeout)
        return cache_key
    
    def get_task_detail(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached task detail data.
        
        Args:
            task_id: Task ID
        
        Returns:
            Cached task data or None
        """
        cache_key = self.get_cache_key('task_detail', task_id)
        return cache.get(cache_key)
    
    def invalidate_task_cache(self, task_id: str, user_id: int = None) -> None:
        """
        Invalidate task cache entries.
        
        Args:
            task_id: Task ID
            user_id: User ID (optional, for user-specific cache)
        """
        cache.delete(self.get_cache_key('task_detail', task_id))
        
        if user_id:
            cache.delete(self.get_cache_key('user_tasks', user_id))
    
    def cache_query_result(self, query_hash: str, result: Any, timeout: int = None) -> str:
        """
        Cache database query result.
        
        Args:
            query_hash: Hash of the query
            result: Query result to cache
            timeout: Cache timeout in seconds
        
        Returns:
            Cache key
        """
        cache_key = self.get_cache_key('query_result', query_hash)
        timeout = timeout or self.default_timeout
        cache.set(cache_key, result, timeout)
        return cache_key
    
    def get_cached_query_result(self, query_hash: str) -> Optional[Any]:
        """
        Get cached query result.
        
        Args:
            query_hash: Hash of the query
        
        Returns:
            Cached result or None
        """
        cache_key = self.get_cache_key('query_result', query_hash)
        return cache.get(cache_key)
    
    def bulk_cache_invalidate(self, pattern: str) -> int:
        """
        Bulk invalidate cache entries matching pattern.
        
        Args:
            pattern: Cache pattern to match
        
        Returns:
            Number of keys invalidated
        """
        try:
            # This requires Redis with pattern matching support
            from django.core.cache import cache
            if hasattr(cache, 'delete_pattern'):
                return cache.delete_pattern(f"{self.cache_prefix}:{pattern}")
            else:
                # Fallback: iterate through known patterns
                patterns_to_delete = [
                    f"{self.cache_prefix}:user_tasks:*",
                    f"{self.cache_prefix}:task_detail:*",
                    f"{self.cache_prefix}:user_profile:*",
                    f"{self.cache_prefix}:query_result:*",
                ]
                
                count = 0
                for pattern in patterns_to_delete:
                    if pattern.startswith(f"{self.cache_prefix}:{pattern}:"):
                        # This is a simplified approach - in production, use Redis SCAN
                        count += 1
                
                return count
        except Exception as e:
            logger.error(f"Failed to bulk invalidate cache: {e}")
            return 0


class DatabasePerformanceMonitor:
    """
    Database performance monitoring and optimization.
    """
    
    def __init__(self):
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD', 0.5)
        self.query_log = []
    
    @contextmanager
    def monitor_query(self, query_name: str):
        """
        Context manager to monitor database query performance.
        
        Args:
            query_name: Name of the query for logging
        """
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        try:
            yield
        finally:
            end_time = time.time()
            query_time = end_time - start_time
            query_count = len(connection.queries) - initial_queries
            
            # Log slow queries
            if query_time > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {query_name}",
                    extra={
                        'query_name': query_name,
                        'query_time': query_time,
                        'query_count': query_count,
                        'threshold': self.slow_query_threshold
                    }
                )
            
            # Store for analytics
            self.query_log.append({
                'name': query_name,
                'time': query_time,
                'count': query_count,
                'timestamp': time.time()
            })
    
    def get_query_stats(self) -> Dict[str, Any]:
        """
        Get database query statistics.
        
        Returns:
            Query performance statistics
        """
        if not self.query_log:
            return {'message': 'No queries logged'}
        
        total_queries = sum(q['count'] for q in self.query_log)
        total_time = sum(q['time'] for q in self.query_log)
        avg_time = total_time / len(self.query_log)
        
        slow_queries = [q for q in self.query_log if q['time'] > self.slow_query_threshold]
        
        return {
            'total_queries': total_queries,
            'total_time': total_time,
            'average_time': avg_time,
            'slow_queries': len(slow_queries),
            'slow_query_percentage': (len(slow_queries) / len(self.query_log)) * 100,
            'queries_per_second': total_queries / total_time if total_time > 0 else 0
        }
    
    def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """
        Analyze slow queries for optimization opportunities.
        
        Returns:
            List of slow query analysis
        """
        slow_queries = [q for q in self.query_log if q['time'] > self.slow_query_threshold]
        
        analysis = []
        for query in slow_queries:
            analysis.append({
                'name': query['name'],
                'time': query['time'],
                'count': query['count'],
                'suggestions': self.get_optimization_suggestions(query)
            })
        
        return analysis
    
    def get_optimization_suggestions(self, query_data: Dict[str, Any]) -> List[str]:
        """
        Get optimization suggestions for a query.
        
        Args:
            query_data: Query performance data
        
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        if query_data['time'] > 2.0:
            suggestions.append("Consider adding database indexes")
            suggestions.append("Review query complexity")
        
        if query_data['count'] > 10:
            suggestions.append("Consider using select_related or prefetch_related")
            suggestions.append("Implement query result caching")
        
        if 'task' in query_data['name'].lower():
            suggestions.append("Optimize task queryset with proper filtering")
        
        if 'user' in query_data['name'].lower():
            suggestions.append("Cache user profile data")
        
        return suggestions


class OptimizedPaginator(Paginator):
    """
    Optimized paginator with caching support.
    """
    
    def __init__(self, queryset, per_page=20, cache_timeout=300, **kwargs):
        self.cache_timeout = cache_timeout
        self.cache_manager = AdvancedCacheManager()
        super().__init__(queryset, per_page, **kwargs)
    
    def get_page(self, number):
        """
        Get page with caching support.
        """
        cache_key = self.cache_manager.get_cache_key(
            'paginated_query', 
            hash(str(self.object_list.query)),
            str(number),
            str(self.per_page)
        )
        
        cached_page = self.cache_manager.get_cached_query_result(cache_key)
        if cached_page:
            return cached_page
        
        page = super().get_page(number)
        
        # Cache the page object (serialize key data)
        page_data = {
            'object_list': list(page.object_list.values()),
            'number': page.number,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
            'next_page_number': page.next_page_number() if page.has_next() else None,
            'previous_page_number': page.previous_page_number() if page.has_previous() else None,
        }
        
        self.cache_manager.cache_query_result(cache_key, page_data, self.cache_timeout)
        
        return page


# Global instances
query_optimizer = QueryOptimizer()
cache_manager = AdvancedCacheManager()
performance_monitor = DatabasePerformanceMonitor()


@contextmanager
def monitor_database_performance(query_name: str):
    """
    Convenience context manager for database performance monitoring.
    
    Args:
        query_name: Name of the query being monitored
    """
    with performance_monitor.monitor_query(query_name):
        yield


def get_optimized_task_list(user_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    Get optimized task list with caching.
    
    Args:
        user_id: User ID
        page: Page number
        page_size: Page size
    
    Returns:
        Optimized task list
    """
    cache_key = cache_manager.get_cache_key('user_tasks_page', user_id, page, page_size)
    cached_result = cache_manager.get_cached_query_result(cache_key)
    
    if cached_result:
        return cached_result
    
    with monitor_database_performance('get_optimized_task_list'):
        queryset = query_optimizer.optimize_task_queryset(user_id)
        paginator = OptimizedPaginator(queryset, page_size, cache_timeout=300)
        page_obj = paginator.get_page(page)
        
        result = {
            'tasks': page_obj.object_list,
            'page': page_obj.number,
            'pages': paginator.num_pages,
            'count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
        
        cache_manager.cache_query_result(cache_key, result, timeout=300)
    
    return result
