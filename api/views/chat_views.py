# Chat and conversation views
import json
import logging
from datetime import datetime

from django.db.models import Count, Prefetch
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from core.models import Conversation, Message
from core.services.chat_service import ChatService
from core.services.conversation_service import ConversationService
from agents import orchestrator
from utils.sanitization import sanitize_plain_text

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Quick status check for load balancers."""
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def chat(request):
    """Main chat endpoint with Aiden."""
    chat.throttle_scope = "chat"
    user_message = request.data.get("message", "").strip()
    conversation_id = request.data.get("conversation_id")

    try:
        chat_service = ChatService(request.user)
        result = chat_service.send_message(user_message, conversation_id)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as e:
        logger.exception("Chat processing failed")
        return Response(
            {"error": "Something went wrong processing your request. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def chat_stream(request):
    """Stream chat responses live. Uses SSE format."""
    chat_stream.throttle_scope = "chat"
    user_message = request.data.get("message", "").strip()
    conversation_id = request.data.get("conversation_id")

    try:
        chat_service = ChatService(request.user)
        
        def event_stream():
            for sse_data in chat_service.send_message_stream(user_message, conversation_id):
                yield sse_data
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as e:
        logger.exception("Chat streaming failed")
        return Response(
            {"error": "Something went wrong processing your request. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def conversation_list(request):
    """Get user's chats with pagination."""
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    try:
        conversation_service = ConversationService(request.user)
        result = conversation_service.list_conversations(page, page_size)
        return Response(result)
    except Exception as e:
        logger.exception("Failed to list conversations")
        return Response(
            {"error": "Failed to retrieve conversations"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """Get single chat with all messages."""
    try:
        conversation_service = ConversationService(request.user)
        result = conversation_service.get_conversation(conversation_id)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Failed to get conversation")
        return Response(
            {"error": "Failed to retrieve conversation"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_conversation(request, conversation_id):
    """Export chat as JSON for backup."""
    try:
        conversation_service = ConversationService(request.user)
        result = conversation_service.export_conversation(conversation_id)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Failed to export conversation")
        return Response(
            {"error": "Failed to export conversation"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """Delete chat and its messages."""
    try:
        conversation_service = ConversationService(request.user)
        deleted = conversation_service.delete_conversation(conversation_id)
        if not deleted:
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"deleted": True})
    except Exception as e:
        logger.exception("Failed to delete conversation")
        return Response(
            {"error": "Failed to delete conversation"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
