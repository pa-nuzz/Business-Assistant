# User profile and business profile views
import logging

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import BusinessProfile, Conversation, Message

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """Get user profile + avatar."""
    profile = getattr(request.user, 'business_profile', None)
    avatar_url = None
    if profile and profile.avatar:
        avatar_url = profile.avatar.url

    return Response({
        "id": request.user.id,
        "username": request.user.username,
        "email": request.user.email,
        "avatar_url": avatar_url,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_username(request):
    """Change username."""
    new_username = request.data.get("username", "").strip()

    if not new_username:
        return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_username) < 3:
        return Response(
            {"error": "Username must be at least 3 characters."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
        return Response({"error": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)

    request.user.username = new_username
    request.user.save(update_fields=["username"])

    return Response({"username": new_username})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_password(request):
    """Change password (needs current password)."""
    current_password = request.data.get("current_password", "")
    new_password = request.data.get("new_password", "")

    if not request.user.check_password(current_password):
        return Response(
            {"error": "Current password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 8:
        return Response(
            {"error": "New password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST
        )

    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])

    return Response({"message": "Password updated successfully."})


@api_view(["GET", "POST", "PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def business_profile(request):
    """Get/update business info with logo."""
    if request.method == "GET":
        try:
            profile = BusinessProfile.objects.get(user=request.user)
            return Response({
                "id": profile.id,
                "company_name": profile.company_name,
                "industry": profile.industry,
                "company_size": profile.company_size,
                "website": profile.website,
                "description": profile.description,
                "goals": profile.goals or [],
                "key_metrics": profile.key_metrics or {},
                "avatar_url": profile.avatar.url if profile.avatar else None,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
            })
        except BusinessProfile.DoesNotExist:
            return Response({
                "id": None,
                "company_name": "",
                "industry": "",
                "company_size": "",
                "website": "",
                "description": "",
                "goals": [],
                "key_metrics": {},
                "avatar_url": None,
            })

    # POST or PUT - create/update with transaction safety
    try:
        with transaction.atomic():
            profile, created = BusinessProfile.objects.get_or_create(user=request.user)
            data = request.data

            if "company_name" in data:
                profile.company_name = data["company_name"]
            if "industry" in data:
                profile.industry = data["industry"]
            if "company_size" in data:
                profile.company_size = data["company_size"]
            if "website" in data:
                profile.website = data["website"]
            if "description" in data:
                profile.description = data["description"]
            if "key_metrics" in data:
                profile.key_metrics = data["key_metrics"] if isinstance(data["key_metrics"], dict) else {}
            if "goals" in data:
                profile.goals = data["goals"] if isinstance(data["goals"], list) else []

            # Handle avatar upload
            if "avatar" in request.FILES:
                if profile.avatar:
                    try:
                        profile.avatar.delete(save=False)
                    except Exception as e:
                        logger.warning(f"Failed to delete old avatar: {e}")
                profile.avatar = request.FILES["avatar"]

            # Handle avatar removal
            if data.get("remove_avatar") == "true":
                if profile.avatar:
                    try:
                        profile.avatar.delete(save=False)
                    except Exception as e:
                        logger.warning(f"Failed to delete avatar: {e}")
                    profile.avatar = None

            profile.save()

            return Response({
                "id": profile.id,
                "company_name": profile.company_name,
                "industry": profile.industry,
                "company_size": profile.company_size,
                "website": profile.website,
                "description": profile.description,
                "goals": profile.goals,
                "key_metrics": profile.key_metrics,
                "avatar_url": profile.avatar.url if profile.avatar else None,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "message": "Profile saved successfully." if not created else "Profile created successfully.",
            })
    except Exception as e:
        logger.exception("Failed to save business profile")
        return Response(
            {"error": "Failed to save profile. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_analytics(request):
    """Dashboard numbers: metrics, chat stats, followups."""
    try:
        profile = BusinessProfile.objects.get(user=request.user)
        metrics = profile.key_metrics or {}
    except BusinessProfile.DoesNotExist:
        metrics = {}

    convo_count = Conversation.objects.filter(user=request.user).count()
    msg_count = Message.objects.filter(conversation__user=request.user).count()

    return Response({
        "metrics": metrics,
        "conversation_count": convo_count,
        "message_count": msg_count,
    })
