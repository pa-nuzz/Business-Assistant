"""
Analytics API Views
"""
import logging
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from core.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def get_analytics(request):
    """
    Get comprehensive dashboard analytics for the current user.
    
    Returns:
        profile: Business profile data
        summary: Usage statistics (conversations, messages, documents, tasks)
        insights: Top topics, focus areas, engagement metrics, productivity score
        activity_trends: Daily message counts for last 30 days
        followups: Pending follow-ups and reminders
        recent_activity: Recent messages and task activities
    """
    try:
        get_analytics.throttle_scope = "analytics"
        service = AnalyticsService(request.user)
        data = service.get_dashboard_analytics()
        return Response(data)
    except Exception as e:
        logger.exception(f"Analytics generation failed: {e}")
        return Response(
            {"error": "Failed to generate analytics. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_engagement(request):
    """Get user engagement metrics."""
    try:
        days = int(request.GET.get('days', 30))
        service = AnalyticsService(request.user)
        data = service.get_user_engagement(days)
        return Response(data)
    except Exception as e:
        logger.exception(f"Engagement metrics failed: {e}")
        return Response(
            {"error": "Failed to get engagement metrics"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_ai_usage(request):
    """Get AI usage and cost metrics."""
    try:
        days = int(request.GET.get('days', 30))
        service = AnalyticsService(request.user)
        data = service.get_ai_usage_stats(days)
        return Response(data)
    except Exception as e:
        logger.exception(f"AI usage metrics failed: {e}")
        return Response(
            {"error": "Failed to get AI usage metrics"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_workspace_analytics(request, workspace_id: str):
    """Get workspace-level analytics (requires workspace access)."""
    from core.services.admin_analytics_service import AdminAnalyticsService
    
    try:
        # Verify workspace access
        from core.models import WorkspaceMember
        if not WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=request.user
        ).exists() and not request.user.is_staff:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.GET.get('days', 30))
        service = AdminAnalyticsService(request.user)
        data = service.get_workspace_analytics(workspace_id, days)
        return Response(data)
    except Exception as e:
        logger.exception(f"Workspace analytics failed: {e}")
        return Response(
            {"error": "Failed to get workspace analytics"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_admin_dashboard(request):
    """Get admin dashboard (requires staff status)."""
    from core.services.admin_analytics_service import AdminAnalyticsService
    
    if not request.user.is_staff:
        return Response(
            {"error": "Admin access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        days = int(request.GET.get('days', 30))
        service = AdminAnalyticsService(request.user)
        data = service.get_admin_dashboard(days)
        return Response(data)
    except Exception as e:
        logger.exception(f"Admin dashboard failed: {e}")
        return Response(
            {"error": "Failed to get admin dashboard"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_retention_report(request):
    """Get user retention report (admin only)."""
    from core.services.admin_analytics_service import AdminAnalyticsService
    
    if not request.user.is_staff:
        return Response(
            {"error": "Admin access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        cohort_days = int(request.GET.get('cohort_days', 30))
        service = AdminAnalyticsService(request.user)
        data = service.get_retention_report(cohort_days)
        return Response(data)
    except Exception as e:
        logger.exception(f"Retention report failed: {e}")
        return Response(
            {"error": "Failed to get retention report"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_analytics_export(request):
    """Request analytics data export."""
    from core.models_analytics import AnalyticsExport
    from core.tasks import generate_analytics_export
    
    try:
        export = AnalyticsExport.objects.create(
            user=request.user,
            workspace_id=request.data.get('workspace_id'),
            export_type=request.data.get('export_type', 'json'),
            data_scope=request.data.get('data_scope', 'user'),
            date_from=request.data.get('date_from'),
            date_to=request.data.get('date_to'),
            is_scheduled=request.data.get('is_scheduled', False),
            schedule_frequency=request.data.get('schedule_frequency'),
            anonymized=request.data.get('anonymized', True),
        )
        
        # Trigger async generation
        generate_analytics_export.delay(str(export.id))
        
        return Response({
            'export_id': str(export.id),
            'status': 'pending',
            'message': 'Export is being generated. Check back later.'
        })
    except Exception as e:
        logger.exception(f"Export request failed: {e}")
        return Response(
            {"error": "Failed to create export"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_export_status(request, export_id: str):
    """Check export generation status."""
    from core.models_analytics import AnalyticsExport
    
    try:
        export = AnalyticsExport.objects.get(
            id=export_id,
            user=request.user
        )
        
        return Response({
            'export_id': str(export.id),
            'status': export.status,
            'file_url': export.file_url,
            'error_message': export.error_message,
            'created_at': export.created_at.isoformat(),
        })
    except AnalyticsExport.DoesNotExist:
        return Response(
            {"error": "Export not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.exception(f"Export status check failed: {e}")
        return Response(
            {"error": "Failed to check export status"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_analytics_data(request):
    """Delete user's analytics data (GDPR compliance)."""
    from core.models_analytics import UserActivity, AIMetrics, SessionAnalytics
    
    try:
        user_id = request.user.id
        
        # Delete all user analytics data
        UserActivity.objects.filter(user_id=user_id).delete()
        AIMetrics.objects.filter(user_id=user_id).delete()
        SessionAnalytics.objects.filter(user_id=user_id).delete()
        
        return Response({
            'message': 'Your analytics data has been deleted.'
        })
    except Exception as e:
        logger.exception(f"Analytics deletion failed: {e}")
        return Response(
            {"error": "Failed to delete analytics data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
