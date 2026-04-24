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
    if not user_message:
        return Response({"error": "Message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

    user_message = sanitize_plain_text(user_message, max_length=4000)
    if len(user_message) > 4000:
        return Response({"error": "Message too long (max 4000 chars)."}, status=status.HTTP_400_BAD_REQUEST)

    conversation_id = request.data.get("conversation_id")

    # Get or create conversation
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
    else:
        conversation = Conversation.objects.create(
            user=request.user,
            title=user_message[:80],
        )

    # Build conversation history with user context
    recent_messages = conversation.messages.order_by("created_at")[:20]

    system_message = None
    try:
        profile = request.user.business_profile
        if profile and profile.company_name:
            system_content = f"User's business: {profile.company_name}"
            if profile.industry:
                system_content += f" in the {profile.industry} industry"
            system_message = {"role": "system", "content": system_content}
    except Exception:
        pass

    history = []
    if system_message:
        history.append(system_message)
    for m in recent_messages:
        history.append({"role": m.role, "content": m.content})

    # Run agent
    try:
        result = orchestrator.run(
            user_message=user_message,
            user_id=request.user.id,
            conversation_history=history,
            user_name=request.user.get_full_name() or request.user.username,
        )
    except Exception as e:
        logger.exception("Agent run failed")
        return Response(
            {"error": "Something went wrong processing your request. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Save messages to DB
    Message.objects.create(
        conversation=conversation,
        role="user",
        content=user_message,
    )
    Message.objects.create(
        conversation=conversation,
        role="assistant",
        content=result.get("reply", ""),
        tool_calls=result.get("tools_used", []),
        model_used=result.get("model", "unknown"),
    )

    conversation.save(update_fields=["updated_at"])

    return Response({
        "reply": result.get("reply", ""),
        "conversation_id": str(conversation.id),
        "model_used": result.get("model", "unknown"),
        "tools_used": result.get("tools_used", []),
        "intent": result.get("intent", "chat"),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def chat_stream(request):
    """Stream chat responses live. Uses SSE format."""
    chat_stream.throttle_scope = "chat"
    user_message = request.data.get("message", "").strip()
    if not user_message:
        return Response({"error": "Message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

    user_message = sanitize_plain_text(user_message, max_length=4000)
    if len(user_message) > 4000:
        return Response({"error": "Message too long (max 4000 chars)."}, status=status.HTTP_400_BAD_REQUEST)

    conversation_id = request.data.get("conversation_id")

    # Get or create conversation
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
    else:
        conversation = Conversation.objects.create(
            user=request.user,
            title=user_message[:80],
        )

    # Build conversation history
    recent_messages = conversation.messages.order_by("created_at")[:20]

    system_message = None
    try:
        profile = request.user.business_profile
        if profile and profile.company_name:
            system_content = f"User's business: {profile.company_name}"
            if profile.industry:
                system_content += f" in the {profile.industry} industry"
            system_message = {"role": "system", "content": system_content}
    except Exception:
        pass

    history = []
    if system_message:
        history.append(system_message)
    for m in recent_messages:
        history.append({"role": m.role, "content": m.content})

    # Streaming response generator
    model_info = {"used": "unknown"}

    def event_stream():
        full_response = []

        for sse_data in orchestrator.run_stream(
            user_message=user_message,
            user_id=request.user.id,
            conversation_history=history,
            user_name=request.user.get_full_name() or request.user.username,
            conversation_id=str(conversation.id),
        ):
            yield sse_data

            if sse_data.startswith('data: ') and '[DONE]' not in sse_data:
                try:
                    data = json.loads(sse_data[6:])
                    if "token" in data:
                        full_response.append(data["token"])
                    if "metadata" in data:
                        model_info["used"] = data["metadata"].get("model", "unknown")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"SSE parse error: {e}")

        # Save messages after streaming completes
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message,
        )
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="".join(full_response),
            model_used=model_info["used"],
        )
        conversation.save(update_fields=["updated_at"])

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def conversation_list(request):
    """Get user's chats with pagination."""
    page = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 20)), 100)

    convos = Conversation.objects.filter(user=request.user).annotate(
        message_count=Count("messages")
    ).order_by("-updated_at")

    from django.core.paginator import Paginator
    paginator = Paginator(convos, page_size)
    page_obj = paginator.get_page(page)

    results = []
    for convo in page_obj.object_list:
        results.append({
            "id": str(convo.id),
            "title": convo.title or "Untitled conversation",
            "created_at": convo.created_at,
            "updated_at": convo.updated_at,
            "message_count": convo.message_count,
        })

    return Response({
        "results": results,
        "count": paginator.count,
        "page": page,
        "total_pages": paginator.num_pages,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """Get single chat with all messages."""
    try:
        convo = Conversation.objects.prefetch_related(
            Prefetch('messages', queryset=Message.objects.order_by('created_at'))
        ).get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    messages_data = [
        {"role": m.role, "content": m.content, "created_at": m.created_at,
         "tool_calls": m.tool_calls, "model_used": m.model_used}
        for m in convo.messages.all()
    ]

    return Response({
        "id": str(convo.id),
        "title": convo.title,
        "created_at": convo.created_at,
        "updated_at": convo.updated_at,
        "messages": messages_data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_conversation(request, conversation_id):
    """Export chat as JSON for backup."""
    try:
        convo = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    messages = convo.messages.order_by("created_at").values(
        "role", "content", "created_at"
    )
    return Response({
        "id": str(convo.id),
        "title": convo.title,
        "exported_at": datetime.now().isoformat(),
        "messages": list(messages),
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """Delete chat and its messages."""
    deleted, _ = Conversation.objects.filter(id=conversation_id, user=request.user).delete()
    if not deleted:
        return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})
