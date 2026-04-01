"""
API Views — Keep them thin. Business logic lives in agents/ and services/.
Views handle: auth, validation, HTTP, persistence of messages.
"""
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
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
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
    recent_messages = conversation.messages.order_by("-created_at")[:25]
    
    # Build history list with last 5 messages first, then remaining reversed
    last_5 = list(reversed(recent_messages[:5]))
    remaining = list(reversed(recent_messages[5:20]))
    
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
    
    # Add last 5 messages first (most recent at the end for the model)
    for m in last_5:
        history.append({"role": m.role, "content": m.content})
    
    # Then add remaining older messages
    for m in remaining:
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
    recent_messages = conversation.messages.order_by("-created_at")[:25]
    
    # Build history list with last 5 messages first, then remaining reversed
    last_5 = list(reversed(recent_messages[:5]))
    remaining = list(reversed(recent_messages[5:20]))
    
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
    
    # Add last 5 messages first (most recent at the end for the model)
    for m in last_5:
        history.append({"role": m.role, "content": m.content})
    
    # Then add remaining older messages
    for m in remaining:
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

    # Process synchronously for development (use Celery in production)
    try:
        from services.document import process_document
        success = process_document(str(doc.id))
        if success:
            doc.refresh_from_db()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Document processing failed: {e}")
        doc.status = "failed"
        doc.save()

    return Response({
        "id": str(doc.id),
        "title": doc.title,
        "status": doc.status,
        "message": "Document uploaded and processed." if doc.status == "ready" else "Document uploaded but processing failed.",
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
        tags = TaskTag.objects.filter(task__in=user_tasks).values('name').distinct()
        
        # Add usage counts
        result = []
        for tag in tags:
            count = TaskTag.objects.filter(
                name=tag['name'],
                task__in=user_tasks
            ).count()
            result.append({
                'name': tag['name'],
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
        name=tag_name.lower(),
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
    if not TaskTag.objects.filter(task=task, name=tag_name).exists():
        TaskTag.objects.create(task=task, name=tag_name)
    
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
    
    TaskTag.objects.filter(task=task, name=tag_name).delete()
    
    return Response({
        "task_id": str(task.id),
        "tag": tag_name,
        "message": "Tag removed"
    })
