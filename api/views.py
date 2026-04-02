"""
API Views — Keep them thin. Business logic lives in agents/ and services/.
Views handle: auth, validation, HTTP, persistence of messages.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response

from core.models import Conversation, Message, Document, BusinessProfile
from agents import orchestrator
from services.tasks import process_document_task

logger = logging.getLogger(__name__)


# ─── Authentication ───────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Request password reset email.
    Request: {"email": "..."}
    Sends a real password reset email with a token link.
    """
    email = request.data.get("email", "").strip()
    
    if not email:
        return Response(
            {"error": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists or not (security best practice)
        return Response({
            "message": "If an account with that email exists, a password reset link has been sent."
        })
    
    # Generate password reset token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build reset URL
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
    
    # Send email
    try:
        send_mail(
            subject="Password Reset - AEIOU AI",
            message=f"""Hello {user.username},

You requested a password reset for your AEIOU AI account.

Click this link to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
AEIOU AI Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return Response(
            {"error": "Failed to send email. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        "message": "If an account with that email exists, a password reset link has been sent."
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_confirm(request):
    """
    Confirm password reset with token.
    Request: {"uid": "...", "token": "...", "new_password": "..."}
    """
    uid = request.data.get("uid", "")
    token = request.data.get("token", "")
    new_password = request.data.get("new_password", "")
    
    if not uid or not token or not new_password:
        return Response(
            {"error": "UID, token, and new password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {"error": "Password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Decode user ID
        user_pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_pk)
    except (User.DoesNotExist, ValueError, OverflowError):
        return Response(
            {"error": "Invalid reset link."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify token
    if not default_token_generator.check_token(user, token):
        return Response(
            {"error": "Reset link has expired or is invalid. Please request a new one."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    logger.info(f"Password reset successful for user {user.username}")
    
    return Response({
        "message": "Password reset successful. Please log in with your new password."
    })


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
@throttle_classes([ScopedRateThrottle])
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
    chat.throttle_scope = "chat"
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
    recent_messages = conversation.messages.order_by("created_at")[:20]
    
    # Check if user has a business profile and add system context
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

    # ── Run agent ──────────────────────────────────────────────────────────
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
        tool_calls=result.tools_used,
        model_used=result.model,
    )

    # Update conversation timestamp
    conversation.save(update_fields=["updated_at"])

    return Response({
        "reply": result.text,
        "conversation_id": str(conversation.id),
        "model_used": result.model,
        "tools_used": result.tools_used,
        "intent": result.intent,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
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
    chat_stream.throttle_scope = "chat"
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
    recent_messages = conversation.messages.order_by("created_at")[:20]
    
    # Check if user has a business profile and add system context
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

    # ── Streaming response generator ────────────────────────────────────────
    model_info = {"used": "unknown"}
    
    def event_stream():
        full_response = []
        
        # Run streaming agent
        for sse_data in orchestrator.run_stream(
            user_message=user_message,
            user_id=request.user.id,
            conversation_history=history,
            user_name=request.user.get_full_name() or request.user.username,
            conversation_id=str(conversation.id),
        ):
            yield sse_data
            
            # Collect the full response for DB storage
            if sse_data.startswith('data: ') and '[DONE]' not in sse_data:
                try:
                    import json
                    data = json.loads(sse_data[6:])  # Remove 'data: ' prefix
                    if "token" in data:
                        full_response.append(data["token"])
                    if "metadata" in data:
                        model_info["used"] = data["metadata"].get("model", "unknown")
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
            model_used=model_info["used"],
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
    """List all conversations for the user with pagination."""
    from django.core.paginator import Paginator
    
    page = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 20)), 100)
    
    convos = Conversation.objects.filter(user=request.user).order_by("-updated_at")
    paginator = Paginator(convos, page_size)
    page_obj = paginator.get_page(page)
    
    results = list(page_obj.object_list.values("id", "title", "created_at", "updated_at"))
    
    return Response({
        "results": results,
        "count": paginator.count,
        "page": page,
        "total_pages": paginator.num_pages,
    })


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_conversation(request, conversation_id):
    """
    Export a conversation with all messages.
    Returns clean JSON format for download/backup.
    """
    try:
        convo = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"error": "Not found."}, status=404)

    messages = convo.messages.order_by("created_at").values(
        "role", "content", "created_at", "model_used"
    )
    
    export_data = {
        "conversation_id": str(convo.id),
        "title": convo.title,
        "created_at": convo.created_at.isoformat(),
        "updated_at": convo.updated_at.isoformat(),
        "message_count": convo.messages.count(),
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "created_at": m["created_at"].isoformat() if m["created_at"] else None,
                "model_used": m["model_used"],
            }
            for m in messages
        ],
    }
    
    return Response(export_data)


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
@throttle_classes([ScopedRateThrottle])
def upload_document(request):
    """
    Upload a business document (PDF, DOCX, TXT).
    Processing is kicked off inline (use Celery for large files).

    Request: multipart/form-data with 'file' and optional 'title'
    """
    upload_document.throttle_scope = "upload"
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

    # Process document - try Celery first, fall back to sync if it fails
    try:
        # Try async Celery processing
        process_document_task.delay(str(doc.id))
    except Exception as e:
        # If Celery fails, process synchronously in background thread
        import threading
        logger.warning(f"Celery task failed, using threaded processing: {e}")
        def process_in_thread():
            from services.document import process_document
            process_document(str(doc.id))
        thread = threading.Thread(target=process_in_thread)
        thread.daemon = True
        thread.start()

    return Response({
        "id": str(doc.id),
        "title": doc.title,
        "status": "pending",
        "message": "Document uploaded. Processing in background.",
    }, status=202)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_list(request):
    """List user's documents with pagination."""
    from django.core.paginator import Paginator
    
    page = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 20)), 100)
    
    docs = Document.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(docs, page_size)
    page_obj = paginator.get_page(page)
    
    results = list(page_obj.object_list.values(
        "id", "title", "file_type", "status", "page_count", "created_at"
    ))
    
    return Response({
        "results": results,
        "count": paginator.count,
        "page": page,
        "total_pages": paginator.num_pages,
    })


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_summary(request, doc_id):
    """Get document summary."""
    from mcp.tools import get_document_summary
    result = get_document_summary(doc_id=doc_id, user_id=request.user.id)
    if "error" in result:
        return Response({"error": result["error"]}, status=404)
    return Response(result["result"])


# ─── User Profile Management ─────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_username(request):
    """Update user's username."""
    new_username = request.data.get("username", "").strip()
    
    if not new_username:
        return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_username) < 3:
        return Response({"error": "Username must be at least 3 characters."}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
        return Response({"error": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.username = new_username
    request.user.save()
    return Response({"message": "Username updated successfully.", "username": new_username})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_password(request):
    """Update user's password."""
    current_password = request.data.get("current_password", "")
    new_password = request.data.get("new_password", "")
    
    if not current_password or not new_password:
        return Response({"error": "Current password and new password are required."}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 8:
        return Response({"error": "New password must be at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)
    
    if not request.user.check_password(current_password):
        return Response({"error": "Current password is incorrect."}, status=status.HTTP_401_UNAUTHORIZED)
    
    request.user.set_password(new_password)
    request.user.save()
    return Response({"message": "Password updated successfully."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """Get current user info including username and avatar."""
    profile = getattr(request.user, 'business_profile', None)
    avatar_url = None
    if profile and profile.avatar:
        avatar_url = request.build_absolute_uri(profile.avatar.url)
    
    return Response({
        "username": request.user.username,
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "avatar": avatar_url,
    })

@api_view(["GET", "POST", "PUT"])
@permission_classes([IsAuthenticated])
def business_profile(request):
    """Get or create/update business profile with avatar support."""
    if request.method == "GET":
        try:
            profile = BusinessProfile.objects.get(user=request.user)
            avatar_url = None
            if profile.avatar:
                avatar_url = request.build_absolute_uri(profile.avatar.url)
            return Response({
                "company_name": profile.company_name,
                "industry": profile.industry,
                "company_size": profile.company_size,
                "description": profile.description,
                "goals": profile.goals,
                "key_metrics": profile.key_metrics,
                "avatar": avatar_url,
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
        
        # Handle avatar upload
        if "avatar" in request.FILES:
            profile.avatar = request.FILES["avatar"]
        
        profile.save()
        return Response({"message": "Profile updated successfully."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_analytics(request):
    """
    Returns structured analytics data for the dashboard.
    Pulls from BusinessProfile.key_metrics + conversation stats.
    """
    from mcp.tools import get_business_profile, get_conversation_insights, get_followup_items

    profile_data  = get_business_profile(user_id=request.user.id)
    insights_data = get_conversation_insights(user_id=request.user.id, limit=20)
    followup_data = get_followup_items(user_id=request.user.id)

    return Response({
        "profile":   profile_data.get("result", {}),
        "insights":  insights_data.get("result", {}),
        "followups": followup_data.get("result", {}),
    })


# ─── Health Check ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    from django.conf import settings
    providers = {
        "gemini": bool(settings.AI_CONFIG["gemini"]["api_key"]),
        "groq": bool(settings.AI_CONFIG["groq"]["api_key"]),
        "openrouter": bool(settings.AI_CONFIG["openrouter"]["api_key"]),
    }
    active = [k for k, v in providers.items() if v]
    return Response({
        "status": "ok",
        "service": "business-assistant-api",
        "ai_providers_configured": active,
        "ai_providers_missing": [k for k, v in providers.items() if not v],
    })


# ─── AI Task Extraction ───────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def extract_tasks_from_text(request):
    """
    Use AI to extract potential tasks from conversation text.
    Returns suggested tasks with confidence scores.
    """
    from services.model_layer import call_model, TaskType, Priority
    
    text = request.data.get("text", "").strip()
    conversation_id = request.data.get("conversation_id")
    
    if not text:
        return Response({"error": "Text is required"}, status=400)
    
    # AI prompt to extract tasks
    extraction_prompt = f"""Analyze the following text and extract any actionable tasks or to-do items mentioned.

Text: "{text}"

Extract tasks that:
1. Are actionable (have a clear action to take)
2. Have a deadline or timeframe mentioned (if any)
3. Have a priority level implied (if any)

Output as JSON array of tasks. If no clear tasks found, return empty array.

Format:
{{
  "tasks": [
    {{
      "title": "Clear, concise task title",
      "description": "Brief description of what needs to be done",
      "priority": "low|medium|high|urgent",
      "due_date_hint": "any deadline mentioned (e.g., 'tomorrow', 'next week', 'Friday')",
      "confidence": 0.0-1.0
    }}
  ],
  "has_actionable_tasks": true/false
}}

Rules:
- Only extract clear, specific tasks
- Confidence should reflect how certain the extraction is
- Due date hints should capture relative time references
- If text mentions something like "remind me to..." or "I need to..." that's a task signal"""

    try:
        result = call_model(
            user_id=request.user.id,
            user_message=extraction_prompt,
            base_system_prompt="You are a task extraction AI. Output valid JSON only.",
            task_type=TaskType.ANALYSIS,
            priority=Priority.NORMAL,
            use_cache=False,
        )
        
        # Parse AI response
        text_response = result.text.strip()
        if "```json" in text_response:
            text_response = text_response.split("```json")[1].split("```")[0].strip()
        elif "```" in text_response:
            text_response = text_response.split("```")[1].strip()
        
        parsed = json.loads(text_response)
        
        # Store suggestions in database for tracking
        from core.models import TaskAISuggestion
        
        tasks_found = []
        for task_data in parsed.get("tasks", []):
            if task_data.get("confidence", 0) > 0.6:  # Only store high confidence
                suggestion = TaskAISuggestion.objects.create(
                    user=request.user,
                    suggested_title=task_data["title"],
                    suggested_description=task_data.get("description", ""),
                    suggested_priority=task_data.get("priority", "medium"),
                    source_type="chat",
                    source_id=conversation_id or "",
                    source_content=text[:500],
                    confidence_score=task_data.get("confidence", 0.5),
                )
                tasks_found.append({
                    "id": str(suggestion.id),
                    "title": suggestion.suggested_title,
                    "description": suggestion.suggested_description,
                    "priority": suggestion.suggested_priority,
                    "confidence": float(suggestion.confidence_score),
                })
        
        return Response({
            "has_tasks": len(tasks_found) > 0,
            "tasks": tasks_found,
            "original_has_actionable": parsed.get("has_actionable_tasks", False),
        })
        
    except Exception as e:
        logger.warning(f"AI task extraction failed: {e}")
        # Return empty result gracefully instead of 500
        return Response({
            "has_tasks": False,
            "tasks": [],
            "original_has_actionable": False,
            "ai_unavailable": True,
        })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_task_suggestion(request, suggestion_id):
    """Accept an AI-suggested task and create it."""
    from core.models import TaskAISuggestion
    
    try:
        suggestion = TaskAISuggestion.objects.get(id=suggestion_id, user=request.user)
        
        if suggestion.was_accepted is not None:
            return Response({"error": "Suggestion already processed"}, status=400)
        
        # Create the task
        from core.models import Task, TaskTag, BusinessProfile
        
        try:
            business_profile = BusinessProfile.objects.get(user=request.user)
        except BusinessProfile.DoesNotExist:
            business_profile = BusinessProfile.objects.create(user=request.user)
        
        task = Task.objects.create(
            user=request.user,
            created_by=request.user,
            business_profile=business_profile,
            title=suggestion.suggested_title,
            description=suggestion.suggested_description,
            priority=suggestion.suggested_priority,
            status="todo",
        )
        
        # Mark suggestion as accepted
        suggestion.was_accepted = True
        suggestion.created_task = task
        suggestion.save()
        
        return Response({
            "message": "Task created successfully",
            "task_id": str(task.id),
            "title": task.title,
        })
        
    except TaskAISuggestion.DoesNotExist:
        return Response({"error": "Suggestion not found"}, status=404)
    except Exception as e:
        logger.exception("Failed to accept task suggestion")
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_task_suggestion(request, suggestion_id):
    """Reject an AI-suggested task."""
    from core.models import TaskAISuggestion
    
    try:
        suggestion = TaskAISuggestion.objects.get(id=suggestion_id, user=request.user)
        suggestion.was_accepted = False
        suggestion.save()
        return Response({"message": "Suggestion rejected"})
    except TaskAISuggestion.DoesNotExist:
        return Response({"error": "Suggestion not found"}, status=404)


# ===== TAGS API =====

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def tags_list_create(request):
    """List all user tags or create a new tag."""
    from core.models import TaskTag
    
    if request.method == "GET":
        # Get all unique tag names for the user's tasks
        user_tasks = Task.objects.filter(
            Q(user=request.user) | Q(assignee=request.user)
        )
        tags = TaskTag.objects.filter(task__in=user_tasks).values('tag').distinct()
        
        # Add usage counts
        result = []
        for tag in tags:
            count = TaskTag.objects.filter(
                tag=tag['tag'],
                task__in=user_tasks
            ).count()
            result.append({
                'tag': tag['tag'],
                'count': count
            })
        
        return Response(result)
    
    elif request.method == "POST":
        name = request.data.get('name', '').strip().lower()
        if not name:
            return Response({"error": "Tag name is required"}, status=400)
        
        # Tags are created when assigned to tasks
        return Response({"name": name, "message": "Tag ready for assignment"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tasks_by_tag(request, tag_name):
    """Get all tasks with a specific tag."""
    from core.models import TaskTag
    
    user_tasks = Task.objects.filter(
        Q(user=request.user) | Q(assignee=request.user)
    )
    
    task_ids = TaskTag.objects.filter(
        tag=tag_name.lower(),
        task__in=user_tasks
    ).values_list('task_id', flat=True)
    
    tasks = Task.objects.filter(id__in=task_ids)
    
    return Response({
        "tag": tag_name,
        "count": tasks.count(),
        "tasks": [{
            "id": str(t.id),
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else None,
        } for t in tasks]
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def task_add_tag(request, task_id):
    """Add a tag to a task."""
    from core.models import TaskTag
    
    task = Task.objects.filter(
        id=task_id
    ).filter(
        Q(user=request.user) | Q(assignee=request.user)
    ).first()
    
    if not task:
        return Response({"error": "Task not found"}, status=404)
    
    tag_name = request.data.get('tag', '').strip().lower()
    if not tag_name:
        return Response({"error": "Tag name is required"}, status=400)
    
    # Check if already exists
    if not TaskTag.objects.filter(task=task, tag=tag_name).exists():
        TaskTag.objects.create(task=task, tag=tag_name)
    
    return Response({
        "task_id": str(task.id),
        "tag": tag_name,
        "message": "Tag added"
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def task_remove_tag(request, task_id):
    """Remove a tag from a task."""
    from core.models import TaskTag
    
    task = Task.objects.filter(
        id=task_id
    ).filter(
        Q(user=request.user) | Q(assignee=request.user)
    ).first()
    
    if not task:
        return Response({"error": "Task not found"}, status=404)
    
    tag_name = request.data.get('tag', '').strip().lower()
    if not tag_name:
        return Response({"error": "Tag name is required"}, status=400)
    
    TaskTag.objects.filter(task=task, tag=tag_name).delete()
    
    return Response({
        "task_id": str(task.id),
        "tag": tag_name,
        "message": "Tag removed"
    })


# ─── Onboarding API ───────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_status(request):
    """
    Get onboarding status for the current user.
    
    Returns:
        {
            "completed": bool,
            "steps": {
                "profile_created": bool,
                "first_document": bool,
                "first_chat": bool,
                "first_task": bool,
            },
            "completion_pct": int
        }
    """
    from core.models import Task
    
    user = request.user
    
    # Check profile created (has company_name)
    profile_created = False
    try:
        profile = user.business_profile
        profile_created = bool(profile and profile.company_name)
    except Exception:
        pass
    
    # Check first document
    first_document = Document.objects.filter(user=user).exists()
    
    # Check first chat/conversation
    first_chat = Conversation.objects.filter(user=user).exists()
    
    # Check first task
    first_task = Task.objects.filter(
        Q(created_by=user) | Q(assignee=user) | Q(user=user)
    ).exists()
    
    steps = {
        "profile_created": profile_created,
        "first_document": first_document,
        "first_chat": first_chat,
        "first_task": first_task,
    }
    
    completed_count = sum(steps.values())
    completion_pct = int((completed_count / 4) * 100)
    completed = completed_count == 4
    
    return Response({
        "completed": completed,
        "steps": steps,
        "completion_pct": completion_pct,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def onboarding_complete(request):
    """
    Mark onboarding as dismissed/completed by user.
    Sets UserMemory with key="onboarded" to track this.
    """
    from services.model_layer import add_user_memory
    
    add_user_memory(
        user_id=request.user.id,
        memory="User dismissed onboarding"
    )
    
    return Response({
        "message": "Onboarding marked as complete",
        "dismissed": True,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def seed_demo_data(request):
    """
    Seed demo data for new users.
    Only runs if user has zero conversations AND zero documents.
    
    Creates:
        - 1 sample conversation with 2 messages
        - 3 sample tasks (todo, in_progress, done)
        - Sets UserMemory with key="onboarded"
    
    Returns: {"seeded": true} or {"seeded": false, "reason": "..."}
    """
    from core.models import Task
    from services.model_layer import add_user_memory
    
    user = request.user
    
    # Check if user already has data
    has_conversations = Conversation.objects.filter(user=user).exists()
    has_documents = Document.objects.filter(user=user).exists()
    
    if has_conversations or has_documents:
        return Response({
            "seeded": False,
            "reason": "already_has_data"
        })
    
    # Get or create business profile
    try:
        profile = user.business_profile
    except Exception:
        from core.models import BusinessProfile
        profile = BusinessProfile.objects.create(user=user)
    
    # Create sample conversation
    conversation = Conversation.objects.create(
        user=user,
        title="Getting started with AEIOU AI",
    )
    
    # Add sample messages
    Message.objects.create(
        conversation=conversation,
        role="user",
        content="What can you help me with?",
    )
    
    sample_response = """Welcome to **AEIOU AI** — your intelligent business assistant! 

I can help you with:

📄 **Documents** — Upload PDFs, DOCX, or TXT files and I'll analyze them, extract insights, and answer questions about their content

✅ **Tasks** — Create, organize, and track your to-dos with priorities and due dates

💬 **Business Chat** — Ask me anything about your business, documents, or general questions

📊 **Analytics** — Get insights about your business data and performance metrics

To get started, try:
• Upload a business document
• Create your first task
• Ask me about business strategies

What would you like to explore first?"""
    
    Message.objects.create(
        conversation=conversation,
        role="assistant",
        content=sample_response,
        model_used="onboarding",
    )
    
    # Create 3 sample tasks
    now = datetime.now()
    
    Task.objects.create(
        user=user,
        created_by=user,
        business_profile=profile,
        title="Review Q4 strategy",
        description="Analyze Q4 performance and plan for next quarter",
        priority="high",
        status="todo",
    )
    
    Task.objects.create(
        user=user,
        created_by=user,
        business_profile=profile,
        title="Prepare investor deck",
        description="Create presentation for upcoming investor meeting",
        priority="urgent",
        status="in_progress",
    )
    
    Task.objects.create(
        user=user,
        created_by=user,
        business_profile=profile,
        title="Set up business profile",
        description="Complete company information and key metrics",
        priority="medium",
        status="done",
        completed_at=now,
    )
    
    # Set user memory
    add_user_memory(
        user_id=user.id,
        memory="Demo data seeded for new user"
    )
    
    return Response({
        "seeded": True,
        "conversation_id": str(conversation.id),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    """
    Admin-only dashboard showing system-wide metrics.
    GET /api/v1/admin/dashboard/
    """
    # Only superusers can access admin dashboard
    if not request.user.is_superuser:
        return Response(
            {"error": "Admin access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    
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
@permission_classes([IsAuthenticated])
def admin_broadcast(request):
    """
    Admin-only broadcast message to all users.
    POST /api/v1/admin/broadcast/
    Request: {"message": "...", "type": "info|warning|maintenance"}
    """
    if not request.user.is_superuser:
        return Response(
            {"error": "Admin access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    
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
    }, timeout=3600)  # 1 hour
    
    return Response({
        "broadcast": True,
        "message": message,
        "type": msg_type,
        "recipients": "all",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_reindex_all(request):
    """
    Admin-only endpoint to trigger reindexing of all documents.
    POST /api/v1/admin/reindex-all/
    """
    if not request.user.is_superuser:
        return Response(
            {"error": "Admin access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from services.tasks import process_document_task
    
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reindex_document(request, doc_id):
    """
    Rechunk and reindex a document.
    Deletes old chunks, reprocesses document, creates new chunks.
    """
    from core.models import Document, DocumentChunk
    from services.document import extract_text, chunk_text, generate_summary
    from django.conf import settings
    
    try:
        doc = Document.objects.get(id=doc_id, user=request.user)
    except Document.DoesNotExist:
        return Response({"error": "Document not found"}, status=404)
    
    # Set status to processing
    doc.status = "processing"
    doc.save(update_fields=["status"])
    
    try:
        # 1. Delete old chunks
        old_chunk_count = DocumentChunk.objects.filter(document=doc).count()
        DocumentChunk.objects.filter(document=doc).delete()
        
        # 2. Re-extract text
        file_path = doc.file.path
        text, page_count = extract_text(file_path, doc.file_type)
        
        if not text.strip():
            raise ValueError("No text could be extracted from document")
        
        # 3. Re-chunk
        cfg = settings.DOCUMENT_CONFIG
        chunks_data = chunk_text(
            text,
            chunk_size=cfg["chunk_size_chars"],
            max_chunks=cfg["max_chunks_per_doc"],
        )
        
        # 4. Regenerate summary
        from services.document import generate_summary
        summary = generate_summary(text, doc.title)
        
        # 5. Save new chunks
        chunk_objects = [
            DocumentChunk(
                document=doc,
                chunk_index=c["chunk_index"],
                content=c["content"],
                keywords=c["keywords"],
            )
            for c in chunks_data
        ]
        DocumentChunk.objects.bulk_create(chunk_objects)
        
        # 6. Update document
        doc.summary = summary
        doc.page_count = page_count
        doc.status = "ready"
        doc.save(update_fields=["summary", "page_count", "status"])
        
        return Response({
            "reindexed": True,
            "document_id": str(doc.id),
            "old_chunks": old_chunk_count,
            "new_chunks": len(chunks_data),
            "pages": page_count,
        })
        
    except Exception as e:
        doc.status = "failed"
        doc.save(update_fields=["status"])
        logger.exception(f"Document reindexing failed for {doc_id}")
        return Response({
            "reindexed": False,
            "error": str(e)
        }, status=500)
