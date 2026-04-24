# Onboarding and task suggestion views
import logging
from datetime import datetime

from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Conversation, Message, Document, BusinessProfile, Task, TaskAISuggestion
from services.model_layer import add_user_memory, call_model

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_status(request):
    """Check what user has set up (profile, docs, chats, tasks)."""
    user = request.user

    profile_created = False
    try:
        profile = user.business_profile
        profile_created = bool(profile and profile.company_name)
    except Exception:
        pass

    first_document = Document.objects.filter(user=user).exists()
    first_chat = Conversation.objects.filter(user=user).exists()
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
def seed_demo_data(request):
    """Add sample data for new users (only if they have nothing yet)."""
    user = request.user

    has_conversations = Conversation.objects.filter(user=user).exists()
    has_documents = Document.objects.filter(user=user).exists()

    if has_conversations or has_documents:
        return Response({"seeded": False, "reason": "already_has_data"})

    try:
        profile = user.business_profile
    except Exception:
        profile = BusinessProfile.objects.create(user=user)

    # Create sample conversation
    conversation = Conversation.objects.create(
        user=user,
        title="Getting started with AEIOU AI",
    )

    Message.objects.create(
        conversation=conversation,
        role="user",
        content="What can you help me with?",
    )

    sample_response = """Welcome to **AEIOU AI** — your intelligent business assistant!

I can help you with:

**Documents** — Upload PDFs, DOCX, or TXT files and I'll analyze them, extract insights, and answer questions about their content

**Tasks** — Create, organize, and track your to-dos with priorities and due dates

**Business Chat** — Ask me anything about your business, documents, or general questions

**Analytics** — Get insights about your business data and performance metrics

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

    add_user_memory(
        user_id=user.id,
        memory="Demo data seeded for new user"
    )

    return Response({
        "seeded": True,
        "conversation_id": str(conversation.id),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def onboarding_complete(request):
    """User closed the onboarding - don't show again."""
    add_user_memory(
        user_id=request.user.id,
        memory="User completed onboarding",
        category="onboarding",
    )
    return Response({"completed": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def extract_tasks_from_text(request):
    """AI finds tasks in chat text."""
    text = request.data.get("text", "").strip()
    if not text:
        return Response({"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST)

    prompt = f"Extract tasks from: {text[:1000]}"
    result = call_model(prompt, max_tokens=500)

    return Response({
        "text": text,
        "suggestions": [
            {"title": line.strip(), "confidence": 0.8}
            for line in result.split("\n")
            if line.strip()
        ],
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_task_suggestion(request, suggestion_id):
    """Turn AI suggestion into real task."""
    try:
        suggestion = TaskAISuggestion.objects.get(id=suggestion_id, user=request.user)
    except TaskAISuggestion.DoesNotExist:
        return Response({"error": "Suggestion not found"}, status=status.HTTP_404_NOT_FOUND)

    task = Task.objects.create(
        user=request.user,
        created_by=request.user,
        title=suggestion.title,
        description=suggestion.description,
        priority=suggestion.priority or "medium",
    )
    suggestion.delete()

    return Response({"accepted": True, "task_id": str(task.id)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_task_suggestion(request, suggestion_id):
    """Dismiss AI suggestion."""
    try:
        suggestion = TaskAISuggestion.objects.get(id=suggestion_id, user=request.user)
        suggestion.delete()
    except TaskAISuggestion.DoesNotExist:
        pass

    return Response({"rejected": True})
