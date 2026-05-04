# User profile and business profile views
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.services.profile_service import ProfileService

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """Get user profile + avatar."""
    service = ProfileService(request.user)
    result = service.get_user_info()
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_username(request):
    """Change username."""
    service = ProfileService(request.user)
    new_username = request.data.get("username", "")

    try:
        result = service.update_username(new_username)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Failed to update username")
        return Response(
            {"error": "Failed to update username"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_password(request):
    """Change password (needs current password)."""
    service = ProfileService(request.user)
    current_password = request.data.get("current_password", "")
    new_password = request.data.get("new_password", "")

    try:
        result = service.update_password(current_password, new_password)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Failed to update password")
        return Response(
            {"error": "Failed to update password"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET", "POST", "PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def business_profile(request):
    """Get/update business info with logo."""
    service = ProfileService(request.user)
    
    if request.method == "GET":
        try:
            result = service.get_business_profile()
            return Response(result)
        except Exception as e:
            logger.exception("Failed to get business profile")
            return Response(
                {"error": "Failed to retrieve business profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST or PUT - create/update
    try:
        avatar_file = request.FILES.get("avatar") if "avatar" in request.FILES else None
        result = service.update_business_profile(request.data, avatar_file)
        return Response(result)
    except Exception as e:
        logger.exception("Failed to update business profile")
        return Response(
            {"error": "Failed to update business profile"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_sessions(request):
    """List all active sessions for the current user."""
    service = ProfileService(request.user)
    try:
        result = service.get_active_sessions()
        # Mark the current session (from the current access token)
        current_jti = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                token_str = auth_header[7:]
                token = AccessToken(token_str)
                current_jti = token.get('jti')
            except Exception:
                pass
        
        # Mark current session
        if current_jti:
            for session in result.get('sessions', []):
                if session['id'] == current_jti:
                    session['is_current'] = True
                    break
        
        return Response(result)
    except Exception as e:
        logger.exception("Failed to list sessions")
        return Response(
            {"error": "Failed to retrieve sessions"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_session(request):
    """Revoke a specific session."""
    service = ProfileService(request.user)
    session_id = request.data.get("session_id")
    
    if not session_id:
        return Response(
            {"error": "session_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = service.revoke_session(session_id)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception(f"Failed to revoke session {session_id}")
        return Response(
            {"error": "Failed to terminate session"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_all_other_sessions(request):
    """Revoke all sessions except the current one."""
    service = ProfileService(request.user)
    try:
        # Get current token JTI from Authorization header
        current_jti = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                token_str = auth_header[7:]
                token = AccessToken(token_str)
                current_jti = token.get('jti')
            except Exception:
                pass
        
        result = service.revoke_all_other_sessions(current_jti)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Failed to revoke other sessions")
        return Response(
            {"error": "Failed to terminate other sessions"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
