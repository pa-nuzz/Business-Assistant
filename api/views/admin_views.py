# Admin-only views
import logging
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from core.models import Conversation, Message, Document
from services.tasks import process_document_task

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    """Admin-only: system-wide stats."""
    # IsAdminUser ensures user is authenticated and is_staff

    from django.contrib.auth.models import User
    from core.models import Task

    now = datetime.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # User stats
    total_users = User.objects.count()
    active_today = User.objects.filter(last_login__gte=day_ago).count()
    active_this_week = User.objects.filter(last_login__gte=week_ago).count()
    new_this_week = User.objects.filter(date_joined__gte=week_ago).count()

    # Conversation stats
    total_conversations = Conversation.objects.count()
    conversations_today = Conversation.objects.filter(created_at__gte=day_ago).count()
    messages_today = Message.objects.filter(created_at__gte=day_ago).count()

    # Document stats
    total_documents = Document.objects.count()
    documents_pending = Document.objects.filter(status="pending").count()
    documents_ready = Document.objects.filter(status="ready").count()
    documents_failed = Document.objects.filter(status="failed").count()

    # Task stats
    total_tasks = Task.objects.count()
    tasks_completed = Task.objects.filter(status="done").count()
    tasks_in_progress = Task.objects.filter(status="in_progress").count()
    tasks_todo = Task.objects.filter(status="todo").count()

    return Response({
        "users": {
            "total": total_users,
            "active_today": active_today,
            "active_this_week": active_this_week,
            "new_this_week": new_this_week,
        },
        "conversations": {
            "total": total_conversations,
            "created_today": conversations_today,
            "messages_today": messages_today,
        },
        "documents": {
            "total": total_documents,
            "pending": documents_pending,
            "ready": documents_ready,
            "failed": documents_failed,
        },
        "tasks": {
            "total": total_tasks,
            "completed": tasks_completed,
            "in_progress": tasks_in_progress,
            "todo": tasks_todo,
        },
        "generated_at": now.isoformat(),
    })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_broadcast(request):
    """
    Admin-only broadcast message to all users.
    POST /api/v1/admin/broadcast/
    Request: {"message": "...", "type": "info|warning|maintenance"}
    """
    # IsAdminUser ensures user is authenticated and is_staff

    message = request.data.get("message", "").strip()
    msg_type = request.data.get("type", "info")

    if not message:
        return Response(
            {"error": "Message is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Store broadcast in cache for WebSocket consumers to pick up
    from django.core.cache import cache
    broadcast_key = f"admin_broadcast_{int(datetime.now().timestamp())}"
    cache.set(broadcast_key, {
        "message": message,
        "type": msg_type,
        "sent_at": datetime.now().isoformat(),
        "sent_by": request.user.username,
    }, timeout=3600)

    return Response({
        "broadcast": True,
        "message": message,
        "type": msg_type,
        "recipients": "all",
    })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_reindex_all(request):
    """
    Admin-only endpoint to trigger reindexing of all documents.
    POST /api/v1/admin/reindex-all/
    """
    # IsAdminUser ensures user is authenticated and is_staff

    # Get all documents that are ready or failed
    documents = Document.objects.filter(status__in=["ready", "failed"])
    doc_ids = list(documents.values_list("id", flat=True))

    # Queue reindex tasks
    count = 0
    for doc_id in doc_ids:
        process_document_task.delay(str(doc_id))
        count += 1

    return Response({
        "queued": True,
        "document_count": count,
        "message": f"Reindexing queued for {count} documents",
    })
