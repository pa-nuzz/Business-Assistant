"""
API Views — Keep them thin. Business logic lives in agents/ and services/.
Views handle: auth, validation, HTTP, persistence of messages.
"""
import logging
import uuid
from django.conf import settings
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from core.models import Conversation, Message, Document, BusinessProfile
from agents import agent
from services.tasks import process_document_task

logger = logging.getLogger(__name__)


# ─── Authentication ───────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user.
    Request: {"username": "...", "password": "...", "email": "..." (optional)}
    """
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    email = request.data.get("email", "").strip()

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 8:
        return Response(
            {"error": "Password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )
        return Response({
            "message": "User created successfully.",
            "user_id": user.id,
            "username": user.username,
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception("User registration failed")
        return Response(
            {"error": "Failed to create user. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ─── Chat Endpoint ────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    Main chat endpoint.

    Request body:
        {
            "message": "What's my revenue trend?",
            "conversation_id": "uuid" (optional — omit to start new)
        }

    Response:
        {
            "reply": "...",
            "conversation_id": "uuid",
            "model_used": "gemini/...",
            "tools_used": ["get_business_profile", ...]
        }
    """
    user_message = request.data.get("message", "").strip()
    if not user_message:
        return Response({"error": "Message cannot be empty."}, status=400)

    if len(user_message) > 4000:
        return Response({"error": "Message too long (max 4000 chars)."}, status=400)

    conversation_id = request.data.get("conversation_id")

    # ── Get or create conversation ─────────────────────────────────────────
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=404)
    else:
        conversation = Conversation.objects.create(
            user=request.user,
            title=user_message[:80],  # use first 80 chars as title
        )

    # ── Build conversation history (last 20 messages to manage context) ────
    recent_messages = conversation.messages.order_by("-created_at")[:20]
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(recent_messages)
    ]

    # ── Run agent ──────────────────────────────────────────────────────────
    try:
        result = agent.run(
            user_message=user_message,
            user_id=request.user.id,
            conversation_history=history,
            user_name=request.user.get_full_name() or request.user.username,
        )
    except Exception as e:
        logger.exception("Agent run failed")
        return Response(
            {"error": "Something went wrong processing your request. Please try again."},
            status=500,
        )

    # ── Save messages to DB ────────────────────────────────────────────────
    Message.objects.create(
        conversation=conversation,
        role="user",
        content=user_message,
    )
    Message.objects.create(
        conversation=conversation,
        role="assistant",
        content=result.text,
        tool_calls=result.tool_calls_made,
        model_used=result.model,
    )

    # Update conversation timestamp
    conversation.save(update_fields=["updated_at"])

    return Response({
        "reply": result.text,
        "conversation_id": str(conversation.id),
        "model_used": result.model,
        "tools_used": result.tool_calls_made,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_stream(request):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    
    Runs the agent loop for tool calls, then streams the final response tokens.
    
    Request body:
        {
            "message": "What's my revenue trend?",
            "conversation_id": "uuid" (optional)
        }
    
    Response: SSE stream with format:
        data: {"metadata": {"model": "...", "tools_used": [...]}}\n\n
        data: {"token": "Hello"}\n\n
        data: {"token": " world"}\n\n
        data: [DONE]\n\n
    """
    user_message = request.data.get("message", "").strip()
    if not user_message:
        return Response({"error": "Message cannot be empty."}, status=400)

    if len(user_message) > 4000:
        return Response({"error": "Message too long (max 4000 chars)."}, status=400)

    conversation_id = request.data.get("conversation_id")

    # ── Get or create conversation ─────────────────────────────────────────
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=404)
    else:
        conversation = Conversation.objects.create(
            user=request.user,
            title=user_message[:80],
        )

    # ── Build conversation history ───────────────────────────────────────────
    recent_messages = conversation.messages.order_by("-created_at")[:20]
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(recent_messages)
    ]

    # ── Streaming response generator ────────────────────────────────────────
    def event_stream():
        full_response = []
        
        # Run streaming agent
        for sse_data in agent.run_stream(
            user_message=user_message,
            user_id=request.user.id,
            conversation_history=history,
            user_name=request.user.get_full_name() or request.user.username,
        ):
            yield sse_data
            
            # Collect the full response for DB storage
            if sse_data.startswith('data: ') and '[DONE]' not in sse_data:
                try:
                    import json
                    data = json.loads(sse_data[6:])  # Remove 'data: ' prefix
                    if "token" in data:
                        full_response.append(data["token"])
                except:
                    pass
        
        # ── Save messages to DB after streaming completes ───────────────────
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message,
        )
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="".join(full_response),
            model_used="gemini",  # Will be updated from metadata if available
        )
        conversation.save(update_fields=["updated_at"])
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering if present
    return response


# ─── Conversation History ─────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    """List all conversations for the user."""
    convos = Conversation.objects.filter(user=request.user).values(
        "id", "title", "created_at", "updated_at"
    )[:50]
    return Response(list(convos))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """Get all messages in a conversation."""
    try:
        convo = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"error": "Not found."}, status=404)

    messages = convo.messages.values("role", "content", "model_used", "created_at")
    return Response({
        "id": str(convo.id),
        "title": convo.title,
        "messages": list(messages),
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """Delete a conversation and all its messages."""
    deleted, _ = Conversation.objects.filter(id=conversation_id, user=request.user).delete()
    if not deleted:
        return Response({"error": "Not found."}, status=404)
    return Response({"deleted": True})


# ─── Document Upload ──────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Upload a business document (PDF, DOCX, TXT).
    Processing is kicked off inline (use Celery for large files).

    Request: multipart/form-data with 'file' and optional 'title'
    """
    file = request.FILES.get("file")
    if not file:
        return Response({"error": "No file provided."}, status=400)

    # Validate size
    max_mb = settings.DOCUMENT_CONFIG["max_upload_size_mb"]
    if file.size > max_mb * 1024 * 1024:
        return Response({"error": f"File too large. Max {max_mb}MB."}, status=400)

    # Validate type
    ext = file.name.rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "docx", "txt"):
        return Response({"error": "Only PDF, DOCX, and TXT files are supported."}, status=400)

    title = request.data.get("title") or file.name.rsplit(".", 1)[0]

    doc = Document.objects.create(
        user=request.user,
        title=title,
        file=file,
        file_type=ext,
        status="pending",
    )

    # Process asynchronously via Celery
    process_document_task.delay(str(doc.id))

    return Response({
        "id": str(doc.id),
        "title": doc.title,
        "status": "pending",
        "message": "Document uploaded and processing started. Poll /api/v1/documents/<id>/status/ for updates.",
    }, status=202)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_list(request):
    """List user's documents."""
    docs = Document.objects.filter(user=request.user).values(
        "id", "title", "file_type", "status", "page_count", "created_at"
    )
    return Response(list(docs))


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_document(request, doc_id):
    """Delete a document and all its chunks."""
    deleted, _ = Document.objects.filter(id=doc_id, user=request.user).delete()
    if not deleted:
        return Response({"error": "Not found."}, status=404)
    return Response({"deleted": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_status(request, doc_id):
    """Get document processing status."""
    try:
        doc = Document.objects.get(id=doc_id, user=request.user)
        return Response({
            "id": str(doc.id),
            "title": doc.title,
            "status": doc.status,
            "pages": doc.page_count,
            "has_summary": bool(doc.summary),
            "created_at": doc.created_at,
        })
    except Document.DoesNotExist:
        return Response({"error": "Not found."}, status=404)


# ─── Business Profile ─────────────────────────────────────────────────────────

@api_view(["GET", "POST", "PUT"])
@permission_classes([IsAuthenticated])
def business_profile(request):
    """Get or create/update business profile."""
    if request.method == "GET":
        try:
            profile = BusinessProfile.objects.get(user=request.user)
            return Response({
                "company_name": profile.company_name,
                "industry": profile.industry,
                "company_size": profile.company_size,
                "description": profile.description,
                "goals": profile.goals,
                "key_metrics": profile.key_metrics,
            })
        except BusinessProfile.DoesNotExist:
            return Response({"error": "No business profile found."}, status=404)

    elif request.method in ("POST", "PUT"):
        profile, _ = BusinessProfile.objects.get_or_create(user=request.user)
        data = request.data
        profile.company_name = data.get("company_name", profile.company_name)
        profile.industry = data.get("industry", profile.industry)
        profile.company_size = data.get("company_size", profile.company_size)
        profile.description = data.get("description", profile.description)
        profile.goals = data.get("goals", profile.goals)
        profile.key_metrics = data.get("key_metrics", profile.key_metrics)
        profile.save()
        return Response({"message": "Profile updated successfully."})


# ─── Health Check ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Render/Railway pings this to check if the service is up."""
    return Response({"status": "ok", "service": "business-assistant-api"})
