"""
Authentication views with email verification and password reset.
"""
import logging
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import EmailVerification, PasswordResetCode
from services.email_service import (
    generate_verification_code,
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
)

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

    if not username or not password or not email:
        return Response(
            {"error": "Username, email, and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 8:
        return Response(
            {"error": "Password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if username exists
    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "This username is already taken. Please choose another one."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email exists
    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "An account with this email already exists. Please log in or use a different email."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Create user (inactive until email verified)
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_active=False,  # Will activate after email verification
        )

        # Generate verification code
        code = generate_verification_code()
        EmailVerification.objects.create(user=user, code=code)

        # Send verification email
        email_sent = send_verification_email(email, username, code)

        if not email_sent:
            # If email fails, still return success but warn
            logger.warning(f"Failed to send verification email to {email}")

        return Response({
            "message": "Registration successful! Please check your email for a verification code.",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "verification_required": True,
            "email_sent": email_sent,
        }, status=status.HTTP_201_CREATED)

    except IntegrityError as e:
        logger.exception("User registration failed - IntegrityError")
        return Response(
            {"error": "This username or email is already registered."},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception("User registration failed")
        return Response(
            {"error": f"Registration failed: {str(e)}"},
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

    if not username or not code:
        return Response(
            {"error": "Username and verification code are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(username=username)
        verification = EmailVerification.objects.get(user=user)

        # Check if already verified
        if verification.is_verified:
            return Response(
                {"error": "Email is already verified. Please log in."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check expiry
        if verification.is_expired():
            return Response(
                {"error": "Verification code has expired. Please request a new code."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check attempts
        if verification.attempts >= 5:
            return Response(
                {"error": "Too many attempts. Please request a new code."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify code
        if verification.code != code:
            verification.attempts += 1
            verification.save()
            remaining = 5 - verification.attempts
            return Response(
                {"error": f"Invalid code. {remaining} attempts remaining."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Success - activate user
        verification.is_verified = True
        verification.save()
        user.is_active = True
        user.save()

        # Send welcome email
        send_welcome_email(user.email, user.username)

        # Generate tokens for auto-login
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Email verified successfully! Welcome to AEIOU AI.",
            "verified": True,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except EmailVerification.DoesNotExist:
        return Response(
            {"error": "No verification pending for this user."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.exception("Email verification failed")
        return Response(
            {"error": f"Verification failed: {str(e)}"},
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

    if not username:
        return Response(
            {"error": "Username is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(username=username)
        verification, created = EmailVerification.objects.get_or_create(user=user)

        # Generate new code
        code = generate_verification_code()
        verification.code = code
        verification.attempts = 0
        verification.created_at = timezone.now()
        verification.save()

        # Send email
        email_sent = send_verification_email(user.email, user.username, code)

        return Response({
            "message": "Verification code resent. Please check your email.",
            "email_sent": email_sent,
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        # Don't reveal if user exists
        return Response({
            "message": "If an account exists, a verification code has been sent.",
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Resend verification failed")
        return Response(
            {"error": "Failed to resend code."},
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

    if not email:
        return Response(
            {"error": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)

        # Clean up old reset codes for this user before creating new one
        PasswordResetCode.objects.filter(
            user=user,
            created_at__lt=timezone.now() - timezone.timedelta(minutes=15)
        ).delete()
        PasswordResetCode.objects.filter(user=user, is_used=True).delete()

        # Generate reset code
        code = generate_verification_code()
        PasswordResetCode.objects.create(user=user, code=code)

        # Send email
        email_sent = send_password_reset_email(email, user.username, code)

        if not email_sent:
            logger.warning(f"Failed to send password reset email to {email}")

        return Response({
            "message": "If an account exists with this email, a password reset code has been sent.",
            "email_sent": email_sent,
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        # Don't reveal if email exists
        return Response({
            "message": "If an account exists with this email, a password reset code has been sent.",
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

    if not email or not code:
        return Response(
            {"error": "Email and code are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        reset_code = PasswordResetCode.objects.filter(
            user=user,
            code=code,
            is_used=False
        ).first()

        if not reset_code:
            return Response(
                {"error": "Invalid code."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reset_code.is_expired():
            return Response(
                {"error": "Code has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "valid": True,
            "message": "Code verified. You can now reset your password.",
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response(
            {"error": "Invalid code."},
            status=status.HTTP_400_BAD_REQUEST
        )


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

    logger.info(f"Password reset attempt for email: {email}")

    if not email or not code or not new_password:
        return Response(
            {"error": "Email, code, and new password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 8:
        return Response(
            {"error": "Password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        logger.info(f"Found user: {user.username}")
        
        # Get the most recent unused code for this user
        reset_code = PasswordResetCode.objects.filter(
            user=user,
            code=code,
            is_used=False
        ).order_by('-created_at').first()

        if not reset_code:
            logger.warning(f"No valid reset code found for user: {user.username}")
            return Response(
                {"error": "Invalid or expired code. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reset_code.is_expired():
            logger.warning(f"Reset code expired for user: {user.username}")
            return Response(
                {"error": "Code has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update password using Django's proper method
        user.set_password(new_password)
        user.save()
        logger.info(f"Password updated successfully for user: {user.username}")

        # Mark ALL codes for this user as used (not just the one used)
        PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

        return Response({
            "message": "Password reset successfully! Please log in with your new password.",
            "success": True
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.warning(f"Password reset attempted for non-existent email: {email}")
        return Response(
            {"error": "Invalid request."},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception(f"Password reset failed for email: {email}")
        return Response(
            {"error": f"Failed to reset password: {str(e)}"},
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

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Try to authenticate
    user = authenticate(username=username, password=password)

    if user is None:
        # Check if user exists but is not active
        try:
            user_obj = User.objects.get(username=username)
            if not user_obj.is_active:
                # Check if email verification is pending
                if hasattr(user_obj, 'email_verification') and not user_obj.email_verification.is_verified:
                    return Response(
                        {"error": "Please verify your email before logging in. Check your inbox for the verification code."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        except User.DoesNotExist:
            pass

        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Check if email is verified
    if hasattr(user, 'email_verification') and not user.email_verification.is_verified:
        return Response(
            {"error": "Please verify your email before logging in. Check your inbox for the verification code."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    # Generate tokens
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # Build response
    response = Response({
        "access": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }, status=status.HTTP_200_OK)

    # Set refresh token in httpOnly cookie (7 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="Lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def logout(request):
    """
    Logout - clear refresh token cookie.
    Client should also clear access token from memory.
    """
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

    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        return Response(
            {"error": "Invalid refresh token. Please login again."},
            status=status.HTTP_401_UNAUTHORIZED
        )
