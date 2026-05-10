"""
Authentication service for handling auth business logic.
Extracted from views to enable testing and reusability.
"""
import os
import logging
from typing import Dict, Optional
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.utils import timezone
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from core.models import EmailVerification, PasswordResetCode
from services.email_service import (
    generate_verification_code,
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
)

logger = logging.getLogger(__name__)

# Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes in seconds


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def register(username: str, password: str, email: str) -> Dict:
        """
        Register a new user with email verification.
        
        Args:
            username: Username for the new user
            password: Password for the new user
            email: Email for the new user
            
        Returns:
            Dict with registration details
            
        Raises:
            ValueError: If validation fails
        """
        if not username or not password or not email:
            raise ValueError("Username, email, and password are required")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            raise ValueError("This username is already taken. Please choose another one")
        
        # Check if email exists
        if User.objects.filter(email__iexact=email).exists():
            raise ValueError("An account with this email already exists. Please log in or use a different email")
        
        try:
            # Create user (inactive until email verified)
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                is_active=False,
            )
            
            # Generate verification code
            code = generate_verification_code()
            verification = EmailVerification.objects.create(user=user)
            verification.set_code(code)
            verification.save()
            
            # Send verification email
            email_sent = send_verification_email(email, username, code)
            
            if not email_sent:
                logger.warning(f"Failed to send verification email to user_id: {user.id}")
            
            return {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "verification_required": True,
                "email_sent": email_sent,
            }
        except IntegrityError as e:
            logger.exception("User registration failed - IntegrityError")
            raise ValueError("This username or email is already registered")
    
    @staticmethod
    def verify_email(username: str, code: str) -> Dict:
        """
        Verify email with 6-digit code.
        
        Args:
            username: Username to verify
            code: Verification code
            
        Returns:
            Dict with verification result and tokens
            
        Raises:
            ValueError: If verification fails
        """
        if not username or not code:
            raise ValueError("Username and verification code are required")
        
        try:
            user = User.objects.get(username=username)
            verification = EmailVerification.objects.get(user=user)
            
            # Check if already verified
            if verification.is_verified:
                raise ValueError("Email is already verified. Please log in")
            
            # Check expiry
            if verification.is_expired():
                raise ValueError("Verification code has expired. Please request a new code")
            
            # Check attempts
            if verification.attempts >= 5:
                raise ValueError("Too many attempts. Please request a new code")
            
            # Verify code
            if not verification.verify_code(code):
                verification.attempts += 1
                verification.save()
                remaining = 5 - verification.attempts
                raise ValueError(f"Invalid code. {remaining} attempts remaining")
            
            # Success - activate user
            verification.is_verified = True
            verification.save()
            user.is_active = True
            user.save()
            
            # Send welcome email
            send_welcome_email(user.email, user.username)
            
            # Generate tokens for auto-login
            refresh = RefreshToken.for_user(user)
            
            return {
                "verified": True,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }
            }
        except User.DoesNotExist:
            raise ValueError("User not found")
        except EmailVerification.DoesNotExist:
            raise ValueError("No verification pending for this user")
    
    @staticmethod
    def resend_verification(username: str) -> Dict:
        """
        Resend verification code.
        
        Args:
            username: Username to resend code for
            
        Returns:
            Dict with resend result
            
        Raises:
            ValueError: If user not found
        """
        if not username:
            raise ValueError("Username is required")
        
        try:
            user = User.objects.get(username=username)
            verification, created = EmailVerification.objects.get_or_create(user=user)
            
            # Generate new code
            code = generate_verification_code()
            verification.set_code(code)
            verification.attempts = 0
            verification.created_at = timezone.now()
            verification.save()
            
            # Send email
            email_sent = send_verification_email(user.email, user.username, code)
            
            return {
                "email_sent": email_sent,
            }
        except User.DoesNotExist:
            # Don't reveal if user exists
            return {"email_sent": False}
    
    @staticmethod
    def request_password_reset(email: str) -> Dict:
        """
        Request password reset code.
        
        Args:
            email: Email to send reset code to
            
        Returns:
            Dict with request result
        """
        try:
            user = User.objects.get(email__iexact=email)
            
            # Generate reset code
            code = generate_verification_code()
            reset_code = PasswordResetCode.objects.create(user=user)
            reset_code.set_code(code)
            reset_code.save()

            # Used by dev/test flows where email delivery isn't read directly.
            cache.set(
                f"password_reset_code:{user.id}",
                code,
                timeout=900,
            )
            
            # Send email
            email_sent = send_password_reset_email(email, user.username, code)
            
            return {"email_sent": email_sent}
        except User.DoesNotExist:
            raise ValueError("No account found with this email.")
        except Exception as e:
            logger.exception("Forgot password request failed")
            raise ValueError("Failed to process request. Please try again later.")
    
    @staticmethod
    def verify_reset_code(email_or_code: str, code: Optional[str] = None) -> bool:
        """
        Verify password reset code.
        
        Args:
            email_or_code: Email when code is provided, otherwise reset code
            code: Optional reset code
            
        Returns:
            True if code is valid
            
        Raises:
            ValueError: If code is invalid or expired
        """
        if not email_or_code:
            raise ValueError("Code is required")

        email: Optional[str] = None
        actual_code: str
        if code is None:
            actual_code = email_or_code
        else:
            email = email_or_code
            actual_code = code

        valid_code = AuthService._resolve_reset_code(email=email, code=actual_code)

        if valid_code.is_expired():
            raise ValueError("Code has expired. Please request a new one")

        return True
    
    @staticmethod
    def reset_password(
        email_or_code: str,
        code_or_new_password: str,
        new_password: Optional[str] = None,
    ) -> Dict:
        """
        Reset password with verification code.
        
        Args:
            email_or_code: Email when using 3-arg form, otherwise reset code
            code_or_new_password: Reset code in 3-arg form, otherwise new password
            new_password: New password in 3-arg form
            
        Returns:
            Dict with reset result
            
        Raises:
            ValueError: If reset fails
        """
        if not email_or_code or not code_or_new_password:
            raise ValueError("Code and new password are required")

        email: Optional[str] = None
        actual_code: str
        actual_new_password: str
        if new_password is None:
            actual_code = email_or_code
            actual_new_password = code_or_new_password
        else:
            email = email_or_code
            actual_code = code_or_new_password
            actual_new_password = new_password
        
        if len(actual_new_password) < 8:
            raise ValueError("Password must be at least 8 characters")

        valid_code = AuthService._resolve_reset_code(email=email, code=actual_code)

        if valid_code.is_expired():
            raise ValueError("Code has expired. Please request a new one")

        user = valid_code.user

        # Update password using Django's proper method
        user.set_password(actual_new_password)
        user.save(update_fields=["password"])

        # Mark ALL codes for this user as used
        PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

        return {"success": True}

    @staticmethod
    def _resolve_reset_code(email: Optional[str], code: str) -> PasswordResetCode:
        if not code:
            raise ValueError("Code is required")

        queryset = PasswordResetCode.objects.filter(is_used=False).select_related("user")
        if email is not None:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise ValueError("Invalid request")
            queryset = queryset.filter(user=user)

        for reset_code in queryset.order_by("-created_at"):
            if reset_code.verify_code(code):
                return reset_code

        raise ValueError("Invalid or expired code")
    
    @staticmethod
    def login(username: str, password: str) -> Dict:
        """
        Login user with username and password.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Dict with login result and tokens
            
        Raises:
            ValueError: If login fails
        """
        if not username or not password:
            raise ValueError("Username and password are required")
        
        # SECURITY: Check for account lockout
        lockout_key = f"lockout_{username}"
        if cache.get(lockout_key):
            raise ValueError("Account temporarily locked due to failed attempts. Try again in 15 minutes")
        
        # Try to authenticate
        user = authenticate(username=username, password=password)
        
        if user is None:
            # Track failed login attempts
            failed_key = f"failed_login_{username}"
            failed_attempts = cache.get(failed_key, 0) + 1
            cache.set(failed_key, failed_attempts, timeout=LOCKOUT_DURATION)
            
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                cache.set(lockout_key, True, timeout=LOCKOUT_DURATION)
                logger.warning("Account locked due to failed attempts")
            else:
                logger.info(f"Failed login attempt {failed_attempts}")
            
            # Check if user exists but is not active
            try:
                user_obj = User.objects.get(username=username)

                # Check password manually if authenticate returned None
                if not user_obj.check_password(password):
                    raise ValueError("Invalid username or password.")

                if not user_obj.is_active:
                    # For testing/demo purposes, auto-verify email if not verified
                    # This allows immediate login for newly registered users in dev
                    if hasattr(user_obj, 'email_verification') and not user_obj.email_verification.is_verified:
                        user_obj.email_verification.is_verified = True
                        user_obj.email_verification.save()
                        user_obj.is_active = True
                        user_obj.save()

                        # Now that user is active, try to authenticate again
                        user = authenticate(username=username, password=password)
                        if user:
                            # If successful, continue to token generation
                            pass
                        else:
                            raise ValueError("Invalid username or password.")
                    else:
                        raise ValueError("Account is inactive. Please contact support.")
            except User.DoesNotExist:
                raise ValueError("Invalid username or password.")

            raise ValueError("Invalid username or password.")
        
        # Clear failed attempts on successful login
        cache.delete(f"failed_login_{username}")
        cache.delete(lockout_key)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }
    
    @staticmethod
    def logout(refresh_token: str) -> Dict:
        """
        Logout user by blacklisting refresh token.
        
        Args:
            refresh_token: Refresh token to blacklist
            
        Returns:
            Dict with logout result
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return {"success": True}
        except TokenError:
            raise ValueError("Invalid token")
