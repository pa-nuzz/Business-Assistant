"""Celery tasks for analytics tracking and async processing."""
from celery import shared_task
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task
def track_activity_async(
    user_id: str,
    event_type: str,
    feature: str,
    metadata: dict,
    workspace_id: str = None,
):
    """Async task to track user activity."""
    try:
        from core.models_analytics import UserActivity
        
        UserActivity.objects.create(
            user_id=user_id,
            workspace_id=workspace_id,
            event_type=event_type,
            feature=feature,
            metadata=metadata,
        )
    except Exception as e:
        logger.error(f"Failed to track activity: {e}")


@shared_task
def track_ai_metrics_async(
    user_id: str,
    model: str,
    operation: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    cost_usd: float,
    response_time_ms: int,
    success: bool = True,
    error_type: str = None,
    workspace_id: str = None,
):
    """Async task to track AI usage metrics."""
    try:
        from core.models_analytics import AIMetrics
        
        AIMetrics.objects.create(
            user_id=user_id,
            workspace_id=workspace_id,
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            success=success,
            error_type=error_type,
        )
    except Exception as e:
        logger.error(f"Failed to track AI metrics: {e}")


@shared_task
def track_session_async(
    user_id: str,
    session_id: str,
    user_agent: str,
    device_type: str,
):
    """Async task to track session start."""
    try:
        from core.models_analytics import SessionAnalytics
        
        SessionAnalytics.objects.create(
            user_id=user_id,
            session_id=session_id,
            user_agent=user_agent,
            device_type=device_type,
        )
    except Exception as e:
        logger.error(f"Failed to track session: {e}")


@shared_task
def update_session_async(
    session_id: str,
    duration_seconds: int,
    page_views: int,
):
    """Async task to update session on end."""
    try:
        from core.models_analytics import SessionAnalytics
        
        session = SessionAnalytics.objects.filter(session_id=session_id).first()
        if session:
            session.duration_seconds = duration_seconds
            session.page_views = page_views
            session.save()
    except Exception as e:
        logger.error(f"Failed to update session: {e}")


@shared_task
def generate_analytics_export(export_id: str):
    """Generate analytics export file (CSV/JSON)."""
    try:
        from core.models_analytics import AnalyticsExport, UserActivity
        import csv
        import json
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        
        export = AnalyticsExport.objects.get(id=export_id)
        export.status = 'processing'
        export.save()
        
        # Get data
        activities = UserActivity.objects.filter(
            user=export.user,
            created_at__gte=export.date_from,
            created_at__lte=export.date_to,
        )
        
        if export.workspace:
            activities = activities.filter(workspace=export.workspace)
        
        # Anonymize if requested
        data = []
        for activity in activities:
            item = {
                'event_type': activity.event_type,
                'feature': activity.feature,
                'timestamp': activity.created_at.isoformat(),
                'metadata': activity.metadata,
            }
            if not export.anonymized:
                item['user_id'] = str(activity.user_id)
            data.append(item)
        
        # Generate file
        if export.export_type == 'csv':
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
            writer.writeheader()
            writer.writerows(data)
            content = ContentFile(output.getvalue().encode())
        else:
            content = ContentFile(json.dumps(data, indent=2).encode())
        
        # Save to storage
        filename = f"exports/analytics_{export_id}.{export.export_type}"
        path = default_storage.save(filename, content)
        
        export.file_url = default_storage.url(path)
        export.status = 'completed'
        export.save()
        
    except Exception as e:
        logger.error(f"Export generation failed: {e}")
        if 'export' in locals():
            export.status = 'failed'
            export.error_message = str(e)
            export.save()


@shared_task
def generate_daily_retention_snapshot():
    """Generate daily retention snapshot."""
    try:
        from core.models_analytics import RetentionSnapshot, UserActivity
        from core.models import User, Workspace
        from django.db.models import Count
        
        today = datetime.now().date()
        
        # Calculate metrics
        total_users = User.objects.count()
        active_users = (
            UserActivity.objects.filter(
                created_at__date=today
            )
            .values('user')
            .distinct()
            .count()
        )
        
        new_users = User.objects.filter(
            date_joined__date=today
        ).count()
        
        returning_users = active_users - new_users
        
        total_workspaces = Workspace.objects.count()
        active_workspaces = (
            UserActivity.objects.filter(
                created_at__date=today,
                workspace__isnull=False
            )
            .values('workspace')
            .distinct()
            .count()
        )
        
        # Calculate retention (simplified)
        day_1_retention = 0
        day_7_retention = 0
        day_30_retention = 0
        
        RetentionSnapshot.objects.create(
            date=today,
            total_users=total_users,
            active_users=active_users,
            new_users=new_users,
            returning_users=returning_users,
            day_1_retention=day_1_retention,
            day_7_retention=day_7_retention,
            day_30_retention=day_30_retention,
            total_workspaces=total_workspaces,
            active_workspaces=active_workspaces,
        )
        
    except Exception as e:
        logger.error(f"Daily snapshot failed: {e}")
