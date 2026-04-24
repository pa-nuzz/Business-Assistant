"""
Task Management API Views
Handles CRUD operations for tasks, comments, and activities.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response

from core.services.task_service import TaskService

logger = logging.getLogger(__name__)


# =============================================================================
# TASK CRUD ENDPOINTS
# =============================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def list_tasks(request):
    list_tasks.throttle_scope = "task"
    """Get tasks with filters + pagination."""
    service = TaskService(request.user)
    
    # Get filter parameters
    status_filter = request.query_params.get("status")
    priority_filter = request.query_params.get("priority")
    assignee_id = request.query_params.get("assignee")
    search_query = request.query_params.get("search")
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))
    order_by = request.query_params.get("order_by", "-created_at")
    
    try:
        result = service.list_tasks(
            status_filter=status_filter,
            priority_filter=priority_filter,
            assignee_id=assignee_id,
            search_query=search_query,
            page=page,
            page_size=page_size,
            order_by=order_by
        )
        return Response(result)
    except Exception as e:
        logger.exception("Failed to list tasks")
        return Response(
            {"error": "Failed to retrieve tasks"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def create_task(request):
    create_task.throttle_scope = "task_write"
    """Create a new task."""
    service = TaskService(request.user)
    
    try:
        result = service.create_task(request.data)
        return Response({
            "message": "Task created successfully",
            **result
        }, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Failed to create task")
        return Response(
            {"error": "Failed to create task"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def get_task(request, task_id):
    get_task.throttle_scope = "task"
    """Get single task details."""
    service = TaskService(request.user)
    
    try:
        result = service.get_task(task_id)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Failed to get task")
        return Response(
            {"error": "Failed to retrieve task"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def update_task(request, task_id):
    update_task.throttle_scope = "task_write"
    """Edit task fields."""
    service = TaskService(request.user)
    
    try:
        result = service.update_task(task_id, request.data)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Failed to update task")
        return Response(
            {"error": "Failed to update task"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def delete_task(request, task_id):
    delete_task.throttle_scope = "task_write"
    """Archive/delete task."""
    service = TaskService(request.user)
    
    try:
        service.delete_task(task_id)
        return Response({"message": "Task deleted successfully"})
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Failed to delete task")
        return Response(
            {"error": "Failed to delete task"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def complete_task(request, task_id):
    complete_task.throttle_scope = "task_write"
    """Mark a task as complete."""
    service = TaskService(request.user)
    
    try:
        data = request.data.copy()
        data["status"] = "done"
        result = service.update_task(task_id, data)
        return Response({
            "message": "Task completed! 🎉",
            **result
        })
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Failed to complete task")
        return Response(
            {"error": "Failed to complete task"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def reopen_task(request, task_id):
    reopen_task.throttle_scope = "task_write"
    """Reopen a completed task."""
    service = TaskService(request.user)
    
    try:
        data = request.data.copy()
        data["status"] = "todo"
        result = service.update_task(task_id, data)
        return Response({
            "message": "Task reopened",
            **result
        })
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Failed to reopen task")
        return Response(
            {"error": "Failed to reopen task"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# COMMENT ENDPOINTS
# =============================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def list_comments(request, task_id):
    list_comments.throttle_scope = "task"
    # Get task comments
    task = get_object_or_404(Task, id=task_id)
    comments = task.comments.select_related("user").order_by("-created_at")
    
    data = []
    for comment in comments:
        data.append({
            "id": str(comment.id),
            "content": comment.content,
            "user": {
                "id": comment.user.id,
                "username": comment.user.username,
            },
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
        })
    
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def create_comment(request, task_id):
    create_comment.throttle_scope = "task_write"
    """Add a comment to a task."""
    service = TaskService(request.user)
    
    try:
        result = service.add_comment(task_id, request.data.get("content", ""))
        return Response(result, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception("Failed to create comment")
        return Response(
            {"error": "Failed to create comment"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def delete_comment(request, task_id, comment_id):
    delete_comment.throttle_scope = "task_write"
    # Remove comment
    user = request.user
    comment = get_object_or_404(TaskComment, id=comment_id, task_id=task_id)
    
    if comment.user != user:
        return Response(
            {"error": "You can only delete your own comments"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    comment.delete()
    return Response({"message": "Comment deleted"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_activities(request, task_id):
    # Task history log
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    user = request.user
    if task.user != user and task.assignee != user and task.created_by != user:
        return Response(
            {"error": "You don't have permission to view this task"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    activities = task.activities.select_related("user").order_by("-created_at")
    
    data = []
    for activity in activities:
        data.append({
            "id": str(activity.id),
            "activity_type": activity.activity_type,
            "old_value": activity.old_value,
            "new_value": activity.new_value,
            "user": {
                "id": activity.user.id,
                "username": activity.user.username,
            },
            "created_at": activity.created_at.isoformat(),
        })
    
    return Response(data)


# =============================================================================
# DASHBOARD & STATS ENDPOINTS
# =============================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def task_dashboard(request):
    task_dashboard.throttle_scope = "task"
    # Dashboard: counts by status + upcoming
    user = request.user
    
    # Base queryset
    tasks = Task.objects.filter(
        Q(created_by=user) | Q(assignee=user) | Q(user=user)
    )
    
    # Status counts
    status_counts = tasks.values("status").annotate(count=Count("id"))
    status_data = {item["status"]: item["count"] for item in status_counts}
    
    # Priority counts
    priority_counts = tasks.exclude(status="done").exclude(status="archived").values("priority").annotate(count=Count("id"))
    priority_data = {item["priority"]: item["count"] for item in priority_counts}
    
    # Overdue tasks - use timezone-aware comparison
    from django.utils import timezone
    now = timezone.now()
    overdue_tasks = tasks.filter(
        due_date__lt=now,
        status__in=["todo", "in_progress", "review"]
    ).order_by("due_date")[:5]
    
    overdue_data = []
    for task in overdue_tasks:
        days_overdue = (now - task.due_date).days if task.due_date else 0
        overdue_data.append({
            "id": str(task.id),
            "title": task.title,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "priority": task.priority,
            "days_overdue": days_overdue
        })
    
    # Today's tasks
    today = now.date()
    today_tasks = tasks.filter(
        due_date__date=today,
        status__in=["todo", "in_progress"]
    ).order_by("priority")
    
    today_data = []
    for task in today_tasks:
        today_data.append({
            "id": str(task.id),
            "title": task.title,
            "priority": task.priority,
            "status": task.status,
        })
    
    # Upcoming tasks (next 7 days)
    upcoming = tasks.filter(
        due_date__date__gt=today,
        due_date__date__lte=today + timedelta(days=7),
        status__in=["todo", "in_progress"]
    ).order_by("due_date")[:10]
    
    upcoming_data = []
    for task in upcoming:
        upcoming_data.append({
            "id": str(task.id),
            "title": task.title,
            "due_date": task.due_date.isoformat(),
            "priority": task.priority,
        })
    
    return Response({
        "counts": {
            "total": tasks.count(),
            "by_status": status_data,
            "by_priority": priority_data,
        },
        "overdue": overdue_data,
        "today": today_data,
        "upcoming": upcoming_data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def task_stats(request):
    task_stats.throttle_scope = "task"
    # Stats: completion rate + trends
    user = request.user
    
    tasks = Task.objects.filter(
        Q(created_by=user) | Q(assignee=user) | Q(user=user)
    )
    
    # Completion rate
    total = tasks.count()
    completed = tasks.filter(status="done").count()
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    # This week stats
    week_ago = datetime.now() - timedelta(days=7)
    
    created_this_week = tasks.filter(created_at__gte=week_ago).count()
    completed_this_week = tasks.filter(completed_at__gte=week_ago).count()
    
    # Average completion time
    completed_tasks = tasks.filter(status="done", completed_at__isnull=False, created_at__isnull=False)
    avg_completion_hours = 0
    if completed_tasks.exists():
        total_hours = 0
        count = 0
        for task in completed_tasks[:50]:  # Sample last 50
            if task.completed_at and task.created_at:
                diff = (task.completed_at - task.created_at.replace(tzinfo=task.completed_at.tzinfo)).total_seconds() / 3600
                total_hours += diff
                count += 1
        avg_completion_hours = total_hours / count if count > 0 else 0
    
    return Response({
        "completion_rate": round(completion_rate, 1),
        "total_tasks": total,
        "completed_tasks": completed,
        "created_this_week": created_this_week,
        "completed_this_week": completed_this_week,
        "avg_completion_hours": round(avg_completion_hours, 1),
    })
