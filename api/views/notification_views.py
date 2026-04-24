# Notification views
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Notification


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([])  # Exempt from throttling for polling
def get_notifications(request):
    """Get unread notifications for the current user."""
    unread = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).values("id", "message", "priority", "created_at", "action_url")[:20]
    return Response({"notifications": list(unread), "count": len(unread)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([])  # Exempt from throttling
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
    return Response({"ok": True})
