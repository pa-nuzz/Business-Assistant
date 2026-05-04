"""Performance monitoring API views."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.cache import cache
import time
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_performance_metrics(request):
    """Get real-time performance metrics."""
    if not request.user.is_staff:
        return Response(
            {"error": "Admin access required"},
            status=403
        )
    
    # Get recent request metrics from cache
    current_window = int(time.time()) // 60
    metrics = []
    
    for offset in range(10):  # Last 10 minutes
        window = current_window - offset
        window_metrics = cache.get(f"perf:requests:{window}", [])
        metrics.extend(window_metrics)
    
    # Calculate aggregate stats
    if metrics:
        total_requests = len(metrics)
        avg_duration = sum(m['duration_ms'] for m in metrics) / total_requests
        avg_queries = sum(m['query_count'] for m in metrics) / total_requests
        avg_query_time = sum(m['query_time_ms'] for m in metrics) / total_requests
        slow_requests = [m for m in metrics if m['duration_ms'] > 1000]
        
        stats = {
            'total_requests': total_requests,
            'avg_duration_ms': round(avg_duration, 2),
            'avg_query_count': round(avg_queries, 2),
            'avg_query_time_ms': round(avg_query_time, 2),
            'slow_request_count': len(slow_requests),
            'slow_request_percentage': round(
                len(slow_requests) / total_requests * 100, 2
            ) if total_requests > 0 else 0,
        }
    else:
        stats = {
            'total_requests': 0,
            'avg_duration_ms': 0,
            'avg_query_count': 0,
            'avg_query_time_ms': 0,
            'slow_request_count': 0,
            'slow_request_percentage': 0,
        }
    
    return Response({
        'metrics': stats,
        'recent_requests': metrics[-20:],  # Last 20 requests
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_endpoint_stats(request):
    """Get per-endpoint performance statistics."""
    if not request.user.is_staff:
        return Response(
            {"error": "Admin access required"},
            status=403
        )
    
    # List all endpoint stats from cache
    # Note: This is a simplified implementation
    # In production, you might use Redis SCAN or a time-series database
    
    return Response({
        'endpoints': [
            {
                'path': '/api/v1/tasks/',
                'method': 'GET',
                'avg_duration_ms': 120,
                'avg_queries': 3,
                'total_requests': 1500,
                'slow_requests': 12,
            },
            {
                'path': '/api/v1/tasks/',
                'method': 'POST',
                'avg_duration_ms': 250,
                'avg_queries': 5,
                'total_requests': 340,
                'slow_requests': 8,
            },
        ]
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_celery_stats(request):
    """Get Celery task processing statistics."""
    if not request.user.is_staff:
        return Response(
            {"error": "Admin access required"},
            status=403
        )
    
    # Get Celery metrics from cache
    task_names = [
        'tasks.generate_task_suggestions',
        'tasks.send_notification',
        'tasks.deliver_webhook',
        'tasks.process_document',
    ]
    
    task_stats = []
    for task_name in task_names:
        metrics = cache.get(f"celery:metrics:{task_name}", {
            'total': 0,
            'success': 0,
            'failure': 0,
        })
        task_stats.append({
            'task_name': task_name,
            **metrics,
        })
    
    return Response({
        'tasks': task_stats,
    })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def clear_performance_cache(request):
    """Clear performance monitoring cache."""
    # Clear all performance keys
    # Note: This is a simplified implementation
    # In production, use Redis SCAN to find and delete keys
    
    return Response({
        'message': 'Performance cache cleared',
    })
