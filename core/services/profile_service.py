"""
Profile service for handling user and business profile business logic.
Extracted from views to enable testing and reusability.
"""
import logging
from typing import Dict, Optional
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from core.models import BusinessProfile
from core.cache import CacheService
from core.events.event_bus import event_bus, EventTypes

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for handling profile operations."""
    
    def __init__(self, user: User):
        self.user = user
    
    def get_user_info(self) -> Dict:
        """
        Get user profile with avatar.
        
        Returns:
            Dict with user info
        """
        # Try cache first
        cache_key = f"user_info:{self.user.id}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached
        
        profile = getattr(self.user, 'business_profile', None)
        avatar_url = None
        if profile and profile.avatar:
            avatar_url = profile.avatar.url
        
        result = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "avatar_url": avatar_url,
        }
        
        # Cache for 5 minutes
        CacheService.set(cache_key, result, timeout=300)
        
        return result
    
    def update_username(self, new_username: str) -> Dict:
        """
        Change username.
        
        Args:
            new_username: New username
            
        Returns:
            Dict with updated username
            
        Raises:
            ValueError: If validation fails
        """
        new_username = new_username.strip()
        
        if not new_username:
            raise ValueError("Username is required")
        
        if len(new_username) < 3:
            raise ValueError("Username must be at least 3 characters")
        
        if User.objects.filter(username=new_username).exclude(id=self.user.id).exists():
            raise ValueError("Username already taken")
        
        self.user.username = new_username
        self.user.save(update_fields=["username"])
        
        # Invalidate cache
        CacheService.invalidate_user_cache(self.user.id)
        
        return {"username": new_username}
    
    def update_password(self, current_password: str, new_password: str) -> Dict:
        """
        Change password (requires current password).
        Invalidates all active sessions for security.
        
        Args:
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            Dict with success message and sessions invalidated count
            
        Raises:
            ValueError: If validation fails
        """
        if not self.user.check_password(current_password):
            raise ValueError("Current password is incorrect")
        
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters")
        
        self.user.set_password(new_password)
        self.user.save(update_fields=["password"])
        
        # Invalidate all refresh tokens (sessions) for this user
        sessions_invalidated = self._invalidate_all_sessions()
        
        # Invalidate cache
        CacheService.invalidate_user_cache(self.user.id)
        
        # Publish event
        event_bus.publish(
            EventTypes.USER_PASSWORD_RESET,
            {
                "user_id": self.user.id,
                "sessions_invalidated": sessions_invalidated,
            },
            source="ProfileService"
        )
        
        return {
            "message": "Password updated successfully",
            "sessions_invalidated": sessions_invalidated,
            "requires_relogin": True,
        }
    
    def _invalidate_all_sessions(self) -> int:
        """
        Blacklist all outstanding refresh tokens for the user.
        
        Returns:
            Number of sessions invalidated
        """
        try:
            # Get all outstanding tokens for this user
            outstanding_tokens = OutstandingToken.objects.filter(user=self.user)
            
            # Blacklist each token
            invalidated_count = 0
            for token in outstanding_tokens:
                BlacklistedToken.objects.get_or_create(token=token)
                invalidated_count += 1
            
            if invalidated_count > 0:
                logger.info(f"Invalidated {invalidated_count} sessions for user {self.user.id}")
            
            return invalidated_count
        except Exception as e:
            logger.exception(f"Failed to invalidate sessions for user {self.user.id}: {e}")
            return 0
    
    def get_active_sessions(self) -> Dict:
        """
        Get list of active user sessions with device/browser info.
        
        Returns:
            Dict with list of active sessions
        """
        try:
            # Get all outstanding tokens for this user that haven't expired
            from django.utils import timezone
            outstanding_tokens = OutstandingToken.objects.filter(
                user=self.user,
                expires_at__gt=timezone.now()
            ).order_by('-created_at')
            
            sessions = []
            for token in outstanding_tokens:
                # Check if token is blacklisted (revoked)
                is_blacklisted = BlacklistedToken.objects.filter(token=token).exists()
                
                # Extract jti (token id) as session identifier
                sessions.append({
                    "id": str(token.jti) if token.jti else str(token.id),
                    "created_at": token.created_at.isoformat() if token.created_at else None,
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    "is_current": False,  # Will be marked by API view
                    "is_active": not is_blacklisted,
                    "device_info": "Unknown device",  # Would parse from user agent in middleware
                    "ip_address": None,  # Would store in token extra claims
                })
            
            return {
                "sessions": sessions,
                "total_count": len(sessions),
                "active_count": sum(1 for s in sessions if s["is_active"]),
            }
        except Exception as e:
            logger.exception(f"Failed to get sessions for user {self.user.id}: {e}")
            return {"sessions": [], "total_count": 0, "active_count": 0}
    
    def revoke_session(self, session_id: str) -> Dict:
        """
        Revoke a specific session by blacklisting its token.
        
        Args:
            session_id: The jti or id of the token to revoke
            
        Returns:
            Dict with success status
            
        Raises:
            ValueError: If session not found or already revoked
        """
        try:
            # Try to find by jti first, then by id
            token = OutstandingToken.objects.filter(
                user=self.user,
                jti=session_id
            ).first()
            
            if not token:
                try:
                    token = OutstandingToken.objects.get(
                        user=self.user,
                        id=int(session_id)
                    )
                except (ValueError, OutstandingToken.DoesNotExist):
                    raise ValueError("Session not found")
            
            # Check if already blacklisted
            if BlacklistedToken.objects.filter(token=token).exists():
                raise ValueError("Session already revoked")
            
            # Blacklist the token
            BlacklistedToken.objects.create(token=token)
            logger.info(f"Revoked session {session_id} for user {self.user.id}")
            
            return {"success": True, "message": "Session terminated successfully"}
            
        except ValueError:
            raise
        except Exception as e:
            logger.exception(f"Failed to revoke session {session_id}: {e}")
            raise ValueError("Failed to terminate session")
    
    def revoke_all_other_sessions(self, current_token_jti: str = None) -> Dict:
        """
        Revoke all sessions except the current one.
        
        Args:
            current_token_jti: JTI of the current session to preserve
            
        Returns:
            Dict with count of revoked sessions
        """
        try:
            from django.utils import timezone
            
            # Get all active tokens for this user
            outstanding_tokens = OutstandingToken.objects.filter(
                user=self.user,
                expires_at__gt=timezone.now()
            )
            
            # Filter out the current session and already blacklisted
            tokens_to_revoke = outstanding_tokens.exclude(
                jti=current_token_jti
            ).exclude(
                blacklistedtoken__isnull=False
            )
            
            revoked_count = 0
            for token in tokens_to_revoke:
                BlacklistedToken.objects.get_or_create(token=token)
                revoked_count += 1
            
            if revoked_count > 0:
                logger.info(f"Revoked {revoked_count} other sessions for user {self.user.id}")
            
            return {
                "success": True,
                "revoked_count": revoked_count,
                "message": f"{revoked_count} other session(s) terminated"
            }
            
        except Exception as e:
            logger.exception(f"Failed to revoke other sessions: {e}")
            raise ValueError("Failed to terminate other sessions")
    
    def get_business_profile(self) -> Dict:
        """
        Get business profile info.
        
        Returns:
            Dict with business profile data
        """
        try:
            profile = BusinessProfile.objects.get(user=self.user)
            return {
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
            }
        except BusinessProfile.DoesNotExist:
            return {
                "id": None,
                "company_name": "",
                "industry": "",
                "company_size": "",
                "website": "",
                "description": "",
                "goals": [],
                "key_metrics": {},
                "avatar_url": None,
            }
    
    def update_business_profile(self, data: Dict, avatar_file=None) -> Dict:
        """
        Update business profile with transaction safety.
        
        Args:
            data: Business profile data
            avatar_file: Optional avatar file
            
        Returns:
            Dict with updated profile
            
        Raises:
            ValueError: If validation fails
        """
        with transaction.atomic():
            profile, created = BusinessProfile.objects.get_or_create(user=self.user)
            
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
            if avatar_file:
                if profile.avatar:
                    try:
                        profile.avatar.delete(save=False)
                    except Exception as e:
                        logger.warning(f"Failed to delete old avatar: {e}")
                profile.avatar = avatar_file
            
            # Handle avatar removal
            if data.get("remove_avatar") == "true":
                if profile.avatar:
                    try:
                        profile.avatar.delete(save=False)
                        profile.avatar = None
                    except Exception as e:
                        logger.warning(f"Failed to delete avatar: {e}")
            
            profile.save()
            
            # Invalidate cache
            CacheService.invalidate_user_cache(self.user.id)
            
            return {
                "id": profile.id,
                "company_name": profile.company_name,
                "industry": profile.industry,
                "company_size": profile.company_size,
                "website": profile.website,
                "description": profile.description,
                "goals": profile.goals or [],
                "key_metrics": profile.key_metrics or {},
                "avatar_url": profile.avatar.url if profile.avatar else None,
            }
    
    def delete_account(self, password: str) -> bool:
        """
        Delete user account (requires password verification).
        Uses soft delete for data preservation.
        
        Args:
            password: Current password for verification
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If password is incorrect
        """
        if not self.user.check_password(password):
            raise ValueError("Incorrect password")
        
        # Soft delete conversations (not hard delete)
        from core.models import Conversation
        for convo in Conversation.objects.filter(user=self.user):
            convo.soft_delete(user=self.user)
        
        # Deactivate user instead of hard delete
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        
        # Invalidate all user cache
        CacheService.invalidate_user_cache(self.user.id)
        
        return True
