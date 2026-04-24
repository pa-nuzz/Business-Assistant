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
    from django.core.paginator import Paginator
    
    page = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 20)), 100)
    
    unread = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).values("id", "message", "priority", "created_at", "action_url")
    
    paginator = Paginator(unread, page_size)
    page_obj = paginator.get_page(page)
    
    return Response({
        "results": list(page_obj.object_list),
        "count": paginator.count,
        "page": page,
        "total_pages": paginator.num_pages,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([])  # Exempt from throttling
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
    return Response({"ok": True})
