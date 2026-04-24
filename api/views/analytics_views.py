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
        analytics.throttle_scope = "analytics"
        service = AnalyticsService(request.user)
        data = service.get_dashboard_analytics()
        return Response(data)
    except Exception as e:
        logger.exception(f"Analytics generation failed: {e}")
        return Response(
            {"error": "Failed to generate analytics. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
