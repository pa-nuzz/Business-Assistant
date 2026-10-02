"""
Task Management API Views
Handles CRUD operations for tasks, comments, and activities.
Modularized for AEIOU AI v1 API.
"""
import logging
from datetime import datetime, timedelta
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response

from core.models import Task, TaskComment, TaskActivity
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
    workspace_id = request.query_params.get("workspace_id")
    
    try:
        result = service.list_tasks(
            status_filter=status_filter,
            priority_filter=priority_filter,
            assignee_id=assignee_id,
            search_query=search_query,
            page=page,
            page_size=page_size,
            order_by=order_by,
            workspace_id=workspace_id
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
        # Pass workspace_id from request data
        data = request.data.copy()
        result = service.create_task(data)
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
    from core.services.task_detail_service import TaskDetailService
    service = TaskDetailService(request.user)
    
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


# =============================================================================
# TASK COLLABORATOR ENDPOINTS
# =============================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def list_collaborators(request, task_id):
    """List all collaborators on a task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions - user must be task owner, assignee, or collaborator
    user = request.user
    if task.user != user and task.assignee != user and not task.collaborators.filter(id=user.id).exists():
        return Response(
            {"error": "You don't have permission to view this task"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    collaborators = task.collaborators.select_related('user').all()
    
    data = []
    for collab in collaborators:
        data.append({
            "id": collab.id,
            "username": collab.username,
            "email": collab.email,
            "first_name": collab.first_name,
            "last_name": collab.last_name,
        })
    
    # Also include assignee if not already in collaborators
    if task.assignee and not task.collaborators.filter(id=task.assignee.id).exists():
        data.insert(0, {
            "id": task.assignee.id,
            "username": task.assignee.username,
            "email": task.assignee.email,
            "first_name": task.assignee.first_name,
            "last_name": task.assignee.last_name,
            "is_assignee": True,
        })
    
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def add_collaborator(request, task_id):
    """Add a collaborator to a task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Only task owner or assignee can add collaborators
    user = request.user
    if task.user != user and task.assignee != user:
        return Response(
            {"error": "Only task owner or assignee can add collaborators"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user_id = request.data.get("user_id")
    if not user_id:
        return Response(
            {"error": "user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        collaborator = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Can't add owner or assignee as collaborator
    if collaborator == task.user:
        return Response(
            {"error": "Task owner is already the owner"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if task.assignee and collaborator == task.assignee:
        return Response(
            {"error": "Assignee is already assigned to this task"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Add collaborator
    task.collaborators.add(collaborator)
    
    # Log activity
    from core.models import TaskActivity
    TaskActivity.objects.create(
        task=task,
        user=request.user,
        activity_type="assigned",
        old_value="",
        new_value=f"Added collaborator: {collaborator.username}"
    )
    
    return Response({
        "message": "Collaborator added successfully",
        "collaborator": {
            "id": collaborator.id,
            "username": collaborator.username,
            "email": collaborator.email,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def remove_collaborator(request, task_id, user_id):
    """Remove a collaborator from a task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Only task owner can remove collaborators
    if task.user != request.user:
        return Response(
            {"error": "Only task owner can remove collaborators"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        collaborator = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if collaborator == task.user:
        return Response(
            {"error": "Cannot remove task owner"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if task.assignee and collaborator == task.assignee:
        return Response(
            {"error": "Cannot remove assignee (use unassign instead)"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    task.collaborators.remove(collaborator)
    
    # Log activity
    from core.models import TaskActivity
    TaskActivity.objects.create(
        task=task,
        user=request.user,
        activity_type="assigned",
        old_value=f"Collaborator: {collaborator.username}",
        new_value="Removed collaborator"
    )
    
    return Response({"message": "Collaborator removed successfully"})


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
