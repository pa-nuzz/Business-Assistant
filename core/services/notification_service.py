"""Notification Service - Real-time alerts via WebSocket."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from core.models import Notification, NotificationPreference, Task, TaskComment, Document
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and managing notifications with WebSocket delivery."""

    @staticmethod
    def create_notification(
        user: User,
        notification_type: str,
        title: str,
        message: str,
        task: Task = None,
        document: Document = None,
        comment: TaskComment = None,
        actor: User = None
    ) -> Notification:
        """Create a notification and send via WebSocket."""
        
        # Check user preferences
        try:
            prefs = user.notification_preferences
            if not getattr(prefs, f'{notification_type}_in_app', True):
                logger.info(f"Skipping in-app notification for {user.username} - disabled in prefs")
                return None
        except NotificationPreference.DoesNotExist:
            pass  # No prefs set, default to sending
        
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            task=task,
            document=document,
            comment=comment,
            actor=actor
        )
        
        # Send via WebSocket
        NotificationService.send_websocket_notification(notification)
        
        logger.info(f"Created {notification_type} notification for {user.username}")
        return notification

    @staticmethod
    def send_websocket_notification(notification: Notification):
        """Send notification to user via WebSocket."""
        channel_layer = get_channel_layer()
        
        notification_data = {
            'type': 'notification',
            'id': str(notification.id),
            'notification_type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'task_id': str(notification.task.id) if notification.task else None,
            'document_id': str(notification.document.id) if notification.document else None,
            'actor': notification.actor.username if notification.actor else None,
        }
        
        try:
            async_to_sync(channel_layer.group_send)(
                f'user_{notification.user.id}_notifications',
                {
                    'type': 'send_notification',
                    'notification': notification_data
                }
            )
            
            # Mark as delivered
            notification.websocket_delivered = True
            notification.websocket_delivered_at = datetime.now()
            notification.save(update_fields=['websocket_delivered', 'websocket_delivered_at'])
            
        except Exception as e:
            logger.exception(f"Failed to send WebSocket notification: {e}")

    @staticmethod
    def notify_task_assigned(task: Task, assigned_by: User = None):
        """Notify user when assigned to a task."""
        if task.assigned_to and task.assigned_to != assigned_by:
            NotificationService.create_notification(
                user=task.assigned_to,
                notification_type='task_assigned',
                title=f'Assigned to: {task.title}',
                message=f'You have been assigned to the task "{task.title}"',
                task=task,
                actor=assigned_by
            )

    @staticmethod
    def notify_task_mentioned(comment: TaskComment, mentioned_users: List[str]):
        """Notify users when mentioned in a comment."""
        for username in mentioned_users:
            try:
                user = User.objects.get(username=username)
                NotificationService.create_notification(
                    user=user,
                    notification_type='task_mentioned',
                    title=f'Mentioned in: {comment.task.title}',
                    message=f'{comment.user.username} mentioned you in a comment',
                    task=comment.task,
                    comment=comment,
                    actor=comment.user
                )
            except User.DoesNotExist:
                continue

    @staticmethod
    def notify_comment_reply(parent_comment: TaskComment, reply: TaskComment):
        """Notify user when someone replies to their comment."""
        if parent_comment.user != reply.user:
            NotificationService.create_notification(
                user=parent_comment.user,
                notification_type='comment_reply',
                title=f'Reply to your comment on: {reply.task.title}',
                message=f'{reply.user.username} replied to your comment',
                task=reply.task,
                comment=reply,
                actor=reply.user
            )

    @staticmethod
    def notify_task_completed(task: Task, completed_by: User):
        """Notify task creator when task is completed."""
        if task.user != completed_by:
            NotificationService.create_notification(
                user=task.user,
                notification_type='task_completed',
                title=f'Task completed: {task.title}',
                message=f'{completed_by.username} completed the task',
                task=task,
                actor=completed_by
            )

    @staticmethod
    def check_due_date_notifications():
        """Check for tasks approaching due date and send notifications."""
        from django.utils import timezone
        
        # Get users with notification preferences
        users_with_prefs = NotificationPreference.objects.filter(
            due_date_approaching_in_app=True
        ).select_related('user')
        
        for pref in users_with_prefs:
            warning_hours = pref.due_date_warning_hours
            warning_time = timezone.now() + timedelta(hours=warning_hours)
            
            # Find tasks due within warning period
            tasks = Task.objects.filter(
                user=pref.user,
                due_date__lte=warning_time,
                due_date__gt=timezone.now(),
                status__in=['todo', 'in_progress']
            )
            
            for task in tasks:
                # Check if we already notified about this task
                already_notified = Notification.objects.filter(
                    user=pref.user,
                    task=task,
                    notification_type='due_date_approaching',
                    created_at__gte=timezone.now() - timedelta(hours=24)
                ).exists()
                
                if not already_notified:
                    NotificationService.create_notification(
                        user=pref.user,
                        notification_type='due_date_approaching',
                        title=f'Due soon: {task.title}',
                        message=f'This task is due in less than {warning_hours} hours',
                        task=task
                    )

    @staticmethod
    def get_unread_count(user: User) -> int:
        """Get count of unread notifications for user."""
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def get_notifications(
        user: User,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notifications for user."""
        notifications = Notification.objects.filter(user=user)
        
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        notifications = notifications.order_by('-created_at')[:limit]
        
        return [
            {
                'id': str(n.id),
                'type': n.notification_type,
                'title': n.title,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
                'task_id': str(n.task.id) if n.task else None,
                'document_id': str(n.document.id) if n.document else None,
                'actor': n.actor.username if n.actor else None,
            }
            for n in notifications
        ]

    @staticmethod
    def mark_all_read(user: User) -> int:
        """Mark all notifications as read for user."""
        count = Notification.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=datetime.now()
        )
        return count

    @staticmethod
    def update_preferences(user: User, **kwargs) -> NotificationPreference:
        """Update notification preferences for user."""
        prefs, created = NotificationPreference.objects.get_or_create(user=user)
        
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        prefs.save()
        return prefs


class NotificationConsumer:
    """WebSocket consumer for real-time notifications."""
    
    @staticmethod
    async def connect(user_id: int):
        """Connect user to their notification channel."""
        channel_layer = get_channel_layer()
        await channel_layer.group_add(
            f'user_{user_id}_notifications',
            channel_layer
        )
    
    @staticmethod
    async def disconnect(user_id: int):
        """Disconnect user from their notification channel."""
        channel_layer = get_channel_layer()
        await channel_layer.group_discard(
            f'user_{user_id}_notifications',
            channel_layer
        )
