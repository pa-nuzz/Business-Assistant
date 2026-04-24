"""
Authentication views with email verification and password reset.
"""
import logging
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle

from core.services.auth_service import AuthService
from utils.audit import log_audit_action

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def register(request):
    register.throttle_scope = "auth_register"
    """
    Register a new user with email verification.
    Request: {"username": "...", "password": "...", "email": "..."}
    """
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    email = request.data.get("email", "").strip()

    try:
        result = AuthService.register(username, password, email)
        return Response({
            "message": "Registration successful! Please check your email for a verification code.",
            **result
        }, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("User registration failed")
        return Response(
            {"error": "Registration failed. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def verify_email(request):
    verify_email.throttle_scope = "auth_verify"
    """
    Verify email with 6-digit code.
    Request: {"username": "...", "code": "..."}
    """
    username = request.data.get("username", "").strip()
    code = request.data.get("code", "").strip()

    try:
        result = AuthService.verify_email(username, code)
        return Response({
            "message": "Email verified successfully! Welcome to AEIOU AI.",
            **result
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Email verification failed")
        return Response(
            {"error": "Verification failed. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def resend_verification(request):
    resend_verification.throttle_scope = "auth_verify"
    """
    Resend verification code.
    Request: {"username": "..."}
    """
    username = request.data.get("username", "").strip()

    try:
        result = AuthService.resend_verification(username)
        return Response({
            "message": "Verification code resent. Please check your email.",
            **result
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Resend verification failed")
        return Response(
            {"error": "Failed to resend verification code. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def forgot_password(request):
    forgot_password.throttle_scope = "auth_password"
    """
    Request password reset code.
    Request: {"email": "..."}
    """
    email = request.data.get("email", "").strip()

    try:
        result = AuthService.request_password_reset(email)
        return Response({
            "message": "If an account exists with this email, a password reset code has been sent.",
            **result
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Forgot password failed")
        return Response(
            {"error": "Failed to process request."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def verify_reset_code(request):
    verify_reset_code.throttle_scope = "auth_verify"
    """
    Verify password reset code (without resetting yet).
    Request: {"email": "...", "code": "..."}
    """
    email = request.data.get("email", "").strip()
    code = request.data.get("code", "").strip()

    try:
        AuthService.verify_reset_code(email, code)
        return Response({
            "valid": True,
            "message": "Code verified. You can now reset your password.",
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def reset_password(request):
    reset_password.throttle_scope = "auth_password"
    """
    Reset password with verification code.
    Request: {"email": "...", "code": "...", "new_password": "..."}
    """
    email = request.data.get("email", "").strip()
    code = request.data.get("code", "").strip()
    new_password = request.data.get("new_password", "")

    try:
        result = AuthService.reset_password(email, code, new_password)
        return Response({
            "message": "Password reset successfully! Please log in with your new password.",
            **result
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Password reset failed")
        return Response(
            {"error": "Failed to reset password. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def login(request):
    login.throttle_scope = "auth_login"
    """
    Login with username and password.
    Returns JWT tokens on success.
    """
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    try:
        result = AuthService.login(username, password)
        
        # Build response
        response = Response({
            "access": result["access"],
            "user": result["user"]
        }, status=status.HTTP_200_OK)

        # Set refresh token in httpOnly cookie (7 days)
        response.set_cookie(
            key="refresh_token",
            value=result["refresh"],
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,  # 7 days
        )

        # Log successful login
        from django.contrib.auth.models import User
        user = User.objects.get(username=username)
        log_audit_action(user, 'login', 'user', user.id, {'ip': request.META.get('REMOTE_ADDR')})

        return response
    except ValueError as e:
        if "locked" in str(e).lower():
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        if "verify" in str(e).lower():
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout - clear refresh token cookie and blacklist the token.
    Client should also clear access token from memory.
    """
    try:
        # Get the refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            AuthService.logout(refresh_token)
        
        # Log the logout
        log_audit_action(request.user, 'logout', 'user', request.user.id, {'ip': request.META.get('REMOTE_ADDR')})
    except ValueError:
        # Token was already invalid/expired
        pass
    
    response = Response({"message": "Logged out successfully."})
    response.delete_cookie("refresh_token")
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def token_refresh(request):
    """
    Refresh access token using httpOnly cookie.
    Returns new access token (15 min) and rotates refresh token.
    """
    refresh_token = request.COOKIES.get("refresh_token")

    if not refresh_token:
        return Response(
            {"error": "Refresh token not found. Please login again."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        from rest_framework_simplejwt.tokens import RefreshToken as RefreshTokenClass
        refresh = RefreshTokenClass(refresh_token)

        # Rotate refresh token for security
        new_refresh = RefreshTokenClass.for_user(refresh.user)
        access_token = str(new_refresh.access_token)

        response = Response({
            "access": access_token,
        })

        # Set new refresh token in httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=str(new_refresh),
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,  # 7 days
        )

        return response

    except TokenError:
        logger.warning("Token refresh failed: Invalid token")
        return Response(
            {"error": "Invalid refresh token. Please login again."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        logger.exception("Token refresh failed")
        return Response(
            {"error": "Token refresh failed. Please login again."},
            status=status.HTTP_401_UNAUTHORIZED
        )
