"""
Task service for handling task business logic.
Extracted from views to enable testing and reusability.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q

from core.models import (
    Task, TaskTag, TaskComment, TaskActivity, 
    TaskAttachment, TaskAISuggestion, BusinessProfile
)
from core.cache import CacheService
from core.events.event_bus import event_bus, EventTypes
from utils.sanitization import sanitize_plain_text, sanitize_rich_text
from utils.task_permissions import can_modify_task, can_delete_task

logger = logging.getLogger(__name__)


class TaskService:
    """Service for handling task operations."""
    
    def __init__(self, user: User):
        self.user = user
    
    def list_tasks(
        self,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        assignee_id: Optional[str] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "-created_at"
    ) -> Dict:
        """
        Get tasks with filters and pagination.
        
        Args:
            status_filter: Filter by status
            priority_filter: Filter by priority
            assignee_id: Filter by assignee
            search_query: Search in title and description
            page: Page number
            page_size: Items per page
            order_by: Ordering field
            
        Returns:
            Dict with results, count, page, total_pages
        """
        page_size = min(page_size, 100)
        
        # Try cache first
        cache_key = f"tasks:{self.user.id}:{page}:{status_filter}:{priority_filter}:{assignee_id}:{search_query}:{order_by}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached
        
        # Base queryset - tasks created by user OR assigned to user
        tasks = Task.objects.filter(
            Q(created_by=self.user) | Q(assignee=self.user) | Q(user=self.user)
        ).select_related(
            "assignee", "created_by", "business_profile", "user"
        ).prefetch_related(
            "tags", "subtasks", "comments", "attachments"
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
        
        result = {
            "results": data,
            "count": paginator.count,
            "page": page,
            "total_pages": paginator.num_pages,
        }
        
        # Cache for 1 minute
        CacheService.set(cache_key, result, timeout=60)
        
        return result
    
    def create_task(self, data: Dict) -> Dict:
        """
        Create a new task.
        
        Args:
            data: Task data including title, description, etc.
            
        Returns:
            Dict with created task details
            
        Raises:
            ValueError: If validation fails
        """
        # Sanitize inputs
        title = sanitize_plain_text(data.get("title", ""), max_length=255)
        description = sanitize_rich_text(data.get("description", ""), max_length=5000)
        
        if not title:
            raise ValueError("Task title is required and must be valid text")
        
        # Replace raw data references with sanitized values
        data = data.copy()
        data["title"] = title
        data["description"] = description
        
        # Validate required fields
        title = data.get("title", "").strip()
        if not title:
            raise ValueError("Task title is required")
        
        # Get or create business profile
        try:
            business_profile = self.user.business_profile
        except BusinessProfile.DoesNotExist:
            business_profile = BusinessProfile.objects.create(user=self.user)
        
        # Create task
        task = Task.objects.create(
            user=self.user,
            created_by=self.user,
            business_profile=business_profile,
            title=title,
            description=data.get("description", ""),
            status=data.get("status", "todo"),
            priority=data.get("priority", "medium"),
            due_date=data.get("due_date"),
            assignee_id=data.get("assignee_id") if data.get("assignee_id") is not None else self.user.id,
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
            user=self.user,
            activity_type="created",
            new_value=f"Task created: {title}"
        )
        
        # Invalidate cache
        CacheService.invalidate_user_cache(self.user.id)
        
        # Publish event
        event_bus.publish(
            EventTypes.TASK_CREATED,
            {
                "task_id": str(task.id),
                "title": task.title,
                "user_id": self.user.id,
            },
            source="TaskService"
        )
        
        return {
            "id": str(task.id),
            "title": task.title,
            "status": task.status,
        }
    
    def get_task(self, task_id: str) -> Dict:
        """
        Get single task details.
        
        Args:
            task_id: UUID of the task
            
        Returns:
            Dict with task details
            
        Raises:
            ValueError: If task not found or no permission
        """
        from django.shortcuts import get_object_or_404
        
        task = get_object_or_404(
            Task.objects.select_related("assignee", "created_by", "conversation")
            .prefetch_related("tags", "attachments", "subtasks"),
            id=task_id
        )
        
        # Check permissions
        if task.user != self.user and task.assignee != self.user and task.created_by != self.user:
            raise ValueError("You don't have permission to view this task")
        
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
        
        return {
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
    
    def update_task(self, task_id: str, data: Dict) -> Dict:
        """
        Update task fields.
        
        Args:
            task_id: UUID of the task
            data: Updated task data
            
        Returns:
            Dict with updated task details
            
        Raises:
            ValueError: If task not found or no permission
        """
        from django.shortcuts import get_object_or_404
        
        task = get_object_or_404(Task, id=task_id)
        
        # Check permissions
        if not can_modify_task(task, self.user):
            raise ValueError("You don't have permission to update this task")
        
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
            TaskActivity.objects.create(
                task=task,
                user=self.user,
                activity_type="updated",
                field_name=field,
                old_value=str(old_val),
                new_value=str(new_val)
            )
        
        # Invalidate cache
        CacheService.invalidate_user_cache(self.user.id)
        
        # Publish event
        event_bus.publish(
            EventTypes.TASK_UPDATED,
            {
                "task_id": str(task.id),
                "user_id": self.user.id,
                "changes": [c[0] for c in changes],
            },
            source="TaskService"
        )
        
        return {
            "id": str(task.id),
            "title": task.title,
            "status": task.status,
        }
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: UUID of the task
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If task not found or no permission
        """
        from django.shortcuts import get_object_or_404
        
        task = get_object_or_404(Task, id=task_id)
        
        # Check permissions
        if not can_delete_task(task, self.user):
            raise ValueError("You don't have permission to delete this task")
        
        task.delete()
        
        # Invalidate cache
        CacheService.invalidate_user_cache(self.user.id)
        
        # Publish event
        event_bus.publish(
            EventTypes.TASK_DELETED,
            {
                "task_id": str(task.id),
                "user_id": self.user.id,
            },
            source="TaskService"
        )
        
        return True
    
    def add_comment(self, task_id: str, content: str) -> Dict:
        """
        Add a comment to a task.
        
        Args:
            task_id: UUID of the task
            content: Comment content
            
        Returns:
            Dict with comment details
            
        Raises:
            ValueError: If task not found or no permission
        """
        from django.shortcuts import get_object_or_404
        
        task = get_object_or_404(Task, id=task_id)
        
        # Check permissions
        if task.user != self.user and task.assignee != self.user and task.created_by != self.user:
            raise ValueError("You don't have permission to comment on this task")
        
        # Sanitize content
        content = sanitize_rich_text(content, max_length=2000)
        
        comment = TaskComment.objects.create(
            task=task,
            user=self.user,
            content=content
        )
        
        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=self.user,
            activity_type="commented",
            new_value=f"Comment added: {content[:50]}..."
        )
        
        return {
            "id": str(comment.id),
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "user": {
                "id": comment.user.id,
                "username": comment.user.username,
            }
        }
