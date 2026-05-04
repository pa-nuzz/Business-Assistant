"""Task Detail Service - Manages task details, comments, subtasks, and time tracking."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db import transaction
from core.models import Task, TaskComment, TaskSubtask, TimeEntry, Document, Conversation
import logging

logger = logging.getLogger(__name__)


class TaskDetailService:
    """Service for managing task details including comments, subtasks, time tracking."""

    def __init__(self, user: User):
        self.user = user

    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get full task details with all related data."""
        try:
            task = Task.objects.select_related('user').get(id=task_id)
        except Task.DoesNotExist:
            raise ValueError("Task not found")

        # Get comments with replies
        comments = self._get_comments(task)

        # Get subtasks
        subtasks = self._get_subtasks(task)

        # Get time tracking
        time_entries = self._get_time_entries(task)

        # Get linked resources
        linked_docs = self._get_linked_documents(task)
        linked_chats = self._get_linked_conversations(task)

        return {
            'id': str(task.id),
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'assignee': task.assigned_to.username if task.assigned_to else None,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'comments': comments,
            'subtasks': subtasks,
            'time_entries': time_entries,
            'linked_documents': linked_docs,
            'linked_conversations': linked_chats,
            'total_time_logged': sum(e['duration_minutes'] for e in time_entries),
            'subtasks_completed': sum(1 for s in subtasks if s['status'] == 'done'),
            'subtasks_total': len(subtasks),
        }

    def _get_comments(self, task: Task) -> List[Dict[str, Any]]:
        """Get comments for a task, including replies."""
        comments = TaskComment.objects.filter(task=task, parent_comment=None).select_related('user').order_by('-created_at')
        
        result = []
        for comment in comments:
            replies = TaskComment.objects.filter(parent_comment=comment).select_related('user').order_by('created_at')
            
            result.append({
                'id': str(comment.id),
                'content': comment.content,
                'author': comment.user.username,
                'created_at': comment.created_at.isoformat(),
                'is_edited': comment.is_edited,
                'mentions': comment.mentions,
                'replies': [
                    {
                        'id': str(reply.id),
                        'content': reply.content,
                        'author': reply.user.username,
                        'created_at': reply.created_at.isoformat(),
                        'is_edited': reply.is_edited,
                    }
                    for reply in replies
                ]
            })
        
        return result

    def _get_subtasks(self, task: Task) -> List[Dict[str, Any]]:
        """Get subtasks for a task."""
        subtasks = TaskSubtask.objects.filter(parent_task=task).select_related('assignee').order_by('created_at')
        
        return [
            {
                'id': str(subtask.id),
                'title': subtask.title,
                'description': subtask.description,
                'status': subtask.status,
                'assignee': subtask.assignee.username if subtask.assignee else None,
                'due_date': subtask.due_date.isoformat() if subtask.due_date else None,
                'created_at': subtask.created_at.isoformat(),
                'completed_at': subtask.completed_at.isoformat() if subtask.completed_at else None,
            }
            for subtask in subtasks
        ]

    def _get_time_entries(self, task: Task) -> List[Dict[str, Any]]:
        """Get time entries for a task."""
        entries = TimeEntry.objects.filter(task=task).select_related('user').order_by('-start_time')
        
        return [
            {
                'id': str(entry.id),
                'user': entry.user.username,
                'start_time': entry.start_time.isoformat(),
                'end_time': entry.end_time.isoformat() if entry.end_time else None,
                'duration_minutes': entry.duration_minutes or 0,
                'description': entry.description,
                'is_manual': entry.is_manual,
            }
            for entry in entries
        ]

    def _get_linked_documents(self, task: Task) -> List[Dict[str, Any]]:
        """Get documents linked to a task."""
        # Assuming Task has a linked_documents ManyToMany field
        if hasattr(task, 'linked_documents'):
            return [
                {
                    'id': str(doc.id),
                    'title': doc.title,
                    'file_type': doc.file_type,
                    'created_at': doc.created_at.isoformat(),
                }
                for doc in task.linked_documents.all()
            ]
        return []

    def _get_linked_conversations(self, task: Task) -> List[Dict[str, Any]]:
        """Get conversations linked to a task."""
        if hasattr(task, 'linked_conversations'):
            return [
                {
                    'id': str(conv.id),
                    'title': conv.title,
                    'created_at': conv.created_at.isoformat(),
                }
                for conv in task.linked_conversations.all()
            ]
        return []

    # Comment management
    def add_comment(self, task_id: str, content: str, mentions: List[str] = None) -> Dict[str, Any]:
        """Add a comment to a task."""
        task = Task.objects.get(id=task_id)
        
        comment = TaskComment.objects.create(
            task=task,
            user=self.user,
            content=content,
            mentions=mentions or []
        )

        return {
            'id': str(comment.id),
            'content': comment.content,
            'author': comment.user.username,
            'created_at': comment.created_at.isoformat(),
        }

    def edit_comment(self, comment_id: str, content: str) -> bool:
        """Edit an existing comment."""
        try:
            comment = TaskComment.objects.get(id=comment_id, user=self.user)
            comment.content = content
            comment.is_edited = True
            comment.edited_at = datetime.now()
            comment.save()
            return True
        except TaskComment.DoesNotExist:
            return False

    def reply_to_comment(self, task_id: str, parent_comment_id: str, content: str) -> Dict[str, Any]:
        """Reply to an existing comment."""
        task = Task.objects.get(id=task_id)
        parent = TaskComment.objects.get(id=parent_comment_id, task=task)
        
        reply = TaskComment.objects.create(
            task=task,
            user=self.user,
            content=content,
            parent_comment=parent
        )
        
        return {
            'id': str(reply.id),
            'content': reply.content,
            'author': reply.user.username,
            'created_at': reply.created_at.isoformat(),
        }

    # Subtask management
    def add_subtask(self, task_id: str, title: str, description: str = "", assignee_id: int = None) -> Dict[str, Any]:
        """Add a subtask to a task."""
        task = Task.objects.get(id=task_id)
        
        subtask = TaskSubtask.objects.create(
            parent_task=task,
            title=title,
            description=description,
            assignee_id=assignee_id
        )
        
        return {
            'id': str(subtask.id),
            'title': subtask.title,
            'description': subtask.description,
            'status': subtask.status,
            'created_at': subtask.created_at.isoformat(),
        }

    def update_subtask(self, subtask_id: str, status: str = None, title: str = None) -> bool:
        """Update a subtask's status or title."""
        try:
            subtask = TaskSubtask.objects.get(id=subtask_id, parent_task__user=self.user)
            
            if status:
                subtask.status = status
                if status == 'done' and not subtask.completed_at:
                    subtask.completed_at = datetime.now()
                elif status != 'done':
                    subtask.completed_at = None
            
            if title:
                subtask.title = title
            
            subtask.save()
            return True
        except TaskSubtask.DoesNotExist:
            return False

    def delete_subtask(self, subtask_id: str) -> bool:
        """Delete a subtask."""
        try:
            subtask = TaskSubtask.objects.get(id=subtask_id, parent_task__user=self.user)
            subtask.delete()
            return True
        except TaskSubtask.DoesNotExist:
            return False

    # Time tracking
    def start_timer(self, task_id: str, description: str = "") -> Dict[str, Any]:
        """Start a timer for a task."""
        task = Task.objects.get(id=task_id)
        
        # Check if there's already an active timer
        active = TimeEntry.objects.filter(
            task=task,
            user=self.user,
            end_time__isnull=True
        ).first()
        
        if active:
            return {
                'error': 'Timer already running',
                'active_timer': {
                    'id': str(active.id),
                    'start_time': active.start_time.isoformat(),
                    'description': active.description,
                }
            }
        
        entry = TimeEntry.objects.create(
            task=task,
            user=self.user,
            start_time=datetime.now(),
            description=description
        )
        
        return {
            'id': str(entry.id),
            'start_time': entry.start_time.isoformat(),
            'description': entry.description,
        }

    def stop_timer(self, entry_id: str) -> Dict[str, Any]:
        """Stop a running timer."""
        try:
            entry = TimeEntry.objects.get(id=entry_id, user=self.user, end_time__isnull=True)
            entry.end_time = datetime.now()
            entry.duration_minutes = int((entry.end_time - entry.start_time).total_seconds() / 60)
            entry.save()
            
            return {
                'id': str(entry.id),
                'start_time': entry.start_time.isoformat(),
                'end_time': entry.end_time.isoformat(),
                'duration_minutes': entry.duration_minutes,
                'description': entry.description,
            }
        except TimeEntry.DoesNotExist:
            return {'error': 'No active timer found'}

    def add_manual_time(self, task_id: str, duration_minutes: int, description: str = "", date: str = None) -> Dict[str, Any]:
        """Add manual time entry."""
        task = Task.objects.get(id=task_id)
        
        entry_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.now()
        start_time = entry_date
        end_time = entry_date + timedelta(minutes=duration_minutes)
        
        entry = TimeEntry.objects.create(
            task=task,
            user=self.user,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            description=description,
            is_manual=True
        )
        
        return {
            'id': str(entry.id),
            'duration_minutes': entry.duration_minutes,
            'description': entry.description,
            'is_manual': True,
        }

    def delete_time_entry(self, entry_id: str) -> bool:
        """Delete a time entry."""
        try:
            entry = TimeEntry.objects.get(id=entry_id, user=self.user)
            entry.delete()
            return True
        except TimeEntry.DoesNotExist:
            return False

    def get_active_timer(self) -> Optional[Dict[str, Any]]:
        """Get currently running timer for user."""
        active = TimeEntry.objects.filter(
            user=self.user,
            end_time__isnull=True
        ).select_related('task').first()
        
        if not active:
            return None
        
        return {
            'id': str(active.id),
            'task_id': str(active.task.id),
            'task_title': active.task.title,
            'start_time': active.start_time.isoformat(),
            'description': active.description,
            'elapsed_minutes': int((datetime.now() - active.start_time).total_seconds() / 60),
        }

    # Resource linking
    def link_document(self, task_id: str, document_id: str) -> bool:
        """Link a document to a task."""
        try:
            task = Task.objects.get(id=task_id, user=self.user)
            document = Document.objects.get(id=document_id, user=self.user)
            
            if hasattr(task, 'linked_documents'):
                task.linked_documents.add(document)
            return True
        except (Task.DoesNotExist, Document.DoesNotExist):
            return False

    def link_conversation(self, task_id: str, conversation_id: str) -> bool:
        """Link a conversation to a task."""
        try:
            task = Task.objects.get(id=task_id, user=self.user)
            conversation = Conversation.objects.get(id=conversation_id, user=self.user)
            
            if hasattr(task, 'linked_conversations'):
                task.linked_conversations.add(conversation)
            return True
        except (Task.DoesNotExist, Conversation.DoesNotExist):
            return False
