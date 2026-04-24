"""
Task Management API Views
Handles CRUD operations for tasks, comments, and activities.
"""
import logging
from datetime import datetime, timedelta
from django.db.models import Q, Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from core.models import (
    Task, TaskTag, TaskComment, TaskActivity, 
    TaskAttachment, TaskAISuggestion, BusinessProfile
)
from utils.sanitization import sanitize_plain_text, sanitize_rich_text
from utils.task_permissions import can_modify_task, can_delete_task

logger = logging.getLogger(__name__)


# =============================================================================
# TASK CRUD ENDPOINTS
# =============================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def list_tasks(request):
    list_tasks.throttle_scope = "task"
    # Get tasks with filters + pagination
    user = request.user
    
    # Get filter parameters
    status_filter = request.query_params.get("status")
    priority_filter = request.query_params.get("priority")
    assignee_id = request.query_params.get("assignee")
    search_query = request.query_params.get("search")
    
    # Pagination
    from django.core.paginator import Paginator
    page = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 20)), 100)
    
    # Base queryset - tasks created by user OR assigned to user
    # Using select_related for foreign keys and prefetch_related for many-to-many
    tasks = Task.objects.filter(
        Q(created_by=user) | Q(assignee=user) | Q(user=user)
    ).select_related(
        "assignee", "created_by", "business_profile"
    ).prefetch_related(
        "tags", "subtasks", "comments"
    )
    
    # Apply filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if assignee_id:
        tasks = tasks.filter(assignee_id=assignee_id)
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Ordering
    order_by = request.query_params.get("order_by", "-created_at")
    tasks = tasks.order_by(order_by)
    
    # Paginate
    paginator = Paginator(tasks, page_size)
    page_obj = paginator.get_page(page)
    
    # Serialize
    data = []
    for task in page_obj.object_list:
        data.append({
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_by": task.created_by.username,
            "assignee": task.assignee.username if task.assignee else None,
            "assignee_id": task.assignee_id,
            "tags": [tag.tag for tag in task.tags.all()],
            "is_subtask": task.is_subtask,
            "subtask_count": task.subtasks.count(),
            "comment_count": task.comments.count(),
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        })
    
    return Response({
        "results": data,
        "count": paginator.count,
        "page": page,
        "total_pages": paginator.num_pages,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def create_task(request):
    create_task.throttle_scope = "task_write"
    # Make a new task
    user = request.user
    data = request.data
    
    # Sanitize inputs
    title = sanitize_plain_text(data.get("title", ""), max_length=255)
    description = sanitize_rich_text(data.get("description", ""), max_length=5000)

    if not title:
        return Response(
            {"error": "Task title is required and must be valid text."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Replace raw data references with sanitized values
    data = request.data.copy()
    data["title"] = title
    data["description"] = description
    
    # Validate required fields
    title = data.get("title", "").strip()
    if not title:
        return Response(
            {"error": "Task title is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create business profile
    try:
        business_profile = user.business_profile
    except BusinessProfile.DoesNotExist:
        business_profile = BusinessProfile.objects.create(user=user)
    
    # Create task
    task = Task.objects.create(
        user=user,
        created_by=user,
        business_profile=business_profile,
        title=title,
        description=data.get("description", ""),
        status=data.get("status", "todo"),
        priority=data.get("priority", "medium"),
        due_date=data.get("due_date"),
        assignee_id=data.get("assignee_id") if data.get("assignee_id") is not None else user.id,
        estimated_hours=data.get("estimated_hours"),
        is_subtask=data.get("is_subtask", False),
        parent_task_id=data.get("parent_task_id"),
    )
    
    # Add tags
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    for tag in tags:
        TaskTag.objects.create(task=task, tag=tag.lower())
    
    # Link documents
    document_ids = data.get("document_ids", [])
    for doc_id in document_ids:
        TaskAttachment.objects.create(task=task, document_id=doc_id)
    
    # Log activity
    TaskActivity.objects.create(
        task=task,
        user=user,
        activity_type="created",
        new_value=f"Task created: {title}"
    )
    
    return Response({
        "id": str(task.id),
        "title": task.title,
        "status": task.status,
        "message": "Task created successfully"
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def get_task(request, task_id):
    get_task.throttle_scope = "task"
    # Get single task details
    user = request.user
    
    task = get_object_or_404(
        Task.objects.select_related("assignee", "created_by", "conversation")
        .prefetch_related("tags", "attachments", "subtasks"),
        id=task_id
    )
    
    # Check permissions
    if task.user != user and task.assignee != user and task.created_by != user:
        return Response(
            {"error": "You don't have permission to view this task"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get subtasks
    subtasks_data = []
    for subtask in task.subtasks.all():
        subtasks_data.append({
            "id": str(subtask.id),
            "title": subtask.title,
            "status": subtask.status,
            "completed": subtask.status == "done"
        })
    
    # Get attachments
    attachments_data = []
    for attachment in task.attachments.all():
        attachments_data.append({
            "id": str(attachment.document.id),
            "title": attachment.document.title,
            "file_type": attachment.document.file_type,
        })
    
    data = {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_by": {
            "id": task.created_by.id,
            "username": task.created_by.username,
        },
        "assignee": {
            "id": task.assignee.id,
            "username": task.assignee.username,
        } if task.assignee else None,
        "tags": [tag.tag for tag in task.tags.all()],
        "estimated_hours": str(task.estimated_hours) if task.estimated_hours else None,
        "actual_hours": str(task.actual_hours) if task.actual_hours else None,
        "completion_notes": task.completion_notes,
        "is_subtask": task.is_subtask,
        "parent_task_id": str(task.parent_task_id) if task.parent_task_id else None,
        "subtasks": subtasks_data,
        "attachments": attachments_data,
        "conversation_id": str(task.conversation_id) if task.conversation else None,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
    
    return Response(data)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def update_task(request, task_id):
    update_task.throttle_scope = "task_write"
    # Edit task fields
    user = request.user
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions using shared utility
    if not can_modify_task(task, user):
        return Response(
            {"error": "You don't have permission to update this task"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    data = request.data
    
    # Sanitize text inputs
    if "title" in data:
        data["title"] = sanitize_plain_text(data["title"], max_length=255)
    if "description" in data:
        data["description"] = sanitize_rich_text(data["description"], max_length=5000)
    if "completion_notes" in data:
        data["completion_notes"] = sanitize_rich_text(data["completion_notes"], max_length=2000)
    
    # Track changes for activity log
    changes = []
    
    # Update fields
    if "title" in data:
        old_title = task.title
        task.title = data["title"]
        changes.append(("title", old_title, data["title"]))
    
    if "description" in data:
        task.description = data["description"]
        changes.append(("description", "updated", "updated"))
    
    if "status" in data and data["status"] != task.status:
        old_status = task.status
        task.status = data["status"]
        changes.append(("status", old_status, data["status"]))
        
        # Update completed_at if status changed to done
        if data["status"] == "done" and old_status != "done":
            task.completed_at = datetime.now()
        elif data["status"] != "done":
            task.completed_at = None
    
    if "priority" in data and data["priority"] != task.priority:
        old_priority = task.priority
        task.priority = data["priority"]
        changes.append(("priority", old_priority, data["priority"]))
    
    if "due_date" in data:
        task.due_date = data["due_date"]
        changes.append(("due_date", "updated", data["due_date"]))
    
    if "assignee_id" in data:
        old_assignee = task.assignee.username if task.assignee else "Unassigned"
        task.assignee_id = data["assignee_id"]
        new_assignee = User.objects.get(id=data["assignee_id"]).username
        changes.append(("assignee", old_assignee, new_assignee))
    
    if "estimated_hours" in data:
        task.estimated_hours = data["estimated_hours"]
    
    if "actual_hours" in data:
        task.actual_hours = data["actual_hours"]
    
    if "completion_notes" in data:
        task.completion_notes = data["completion_notes"]
    
    task.save()
    
    # Update tags if provided
    if "tags" in data:
        task.tags.all().delete()
        tags = data["tags"]
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tags:
            TaskTag.objects.create(task=task, tag=tag.lower())
    
    # Log activities
    for field, old_val, new_val in changes:
        activity_type = f"{field}_changed" if field in ["status", "priority"] else "updated"
        TaskActivity.objects.create(
            task=task,
            user=user,
            activity_type=activity_type,
            old_value=str(old_val),
            new_value=str(new_val)
        )
    
    return Response({
        "id": str(task.id),
        "message": "Task updated successfully",
        "changes": [c[0] for c in changes]
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def delete_task(request, task_id):
    delete_task.throttle_scope = "task_write"
    # Archive/delete task
    user = request.user
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if task.created_by != user:
        return Response(
            {"error": "Only the task creator can delete this task"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Soft delete - archive instead of hard delete
    task.status = "archived"
    task.archived_at = datetime.now()
    task.save()
    
    TaskActivity.objects.create(
        task=task,
        user=user,
        activity_type="archived",
        new_value="Task archived"
    )
    
    return Response({"message": "Task archived successfully"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def complete_task(request, task_id):
    complete_task.throttle_scope = "task_write"
    """Mark a task as complete."""
    user = request.user
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if task.created_by != user and task.assignee != user:
        return Response(
            {"error": "You don't have permission to complete this task"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    data = request.data
    
    task.status = "done"
    task.completed_at = datetime.now()
    if data.get("completion_notes"):
        task.completion_notes = data["completion_notes"]
    if data.get("actual_hours"):
        task.actual_hours = data["actual_hours"]
    
    task.save()
    
    TaskActivity.objects.create(
        task=task,
        user=user,
        activity_type="completed",
        new_value="Task marked as complete"
    )
    
    return Response({
        "message": "Task completed! 🎉",
        "completed_at": task.completed_at.isoformat()
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def reopen_task(request, task_id):
    reopen_task.throttle_scope = "task_write"
    """Reopen a completed task."""
    user = request.user
    task = get_object_or_404(Task, id=task_id)
    
    if task.status != "done":
        return Response(
            {"error": "Task is not completed"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    task.status = "todo"
    task.completed_at = None
    task.save()
    
    TaskActivity.objects.create(
        task=task,
        user=user,
        activity_type="status_changed",
        old_value="done",
        new_value="todo"
    )
    
    return Response({"message": "Task reopened"})


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
    user = request.user
    task = get_object_or_404(Task, id=task_id)
    
    # Sanitize comment content to prevent XSS
    content = sanitize_rich_text(request.data.get("content", ""), max_length=2000)
    if not content:
        return Response(
            {"error": "Comment content is required and cannot be empty after sanitization"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    comment = TaskComment.objects.create(
        task=task,
        user=user,
        content=content
    )
    
    TaskActivity.objects.create(
        task=task,
        user=user,
        activity_type="commented",
        new_value=f"Comment added: {content[:100]}..."
    )
    
    return Response({
        "id": str(comment.id),
        "content": comment.content,
        "user": {"id": user.id, "username": user.username},
        "created_at": comment.created_at.isoformat(),
    }, status=status.HTTP_201_CREATED)


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
