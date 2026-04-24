"""
Profile service for handling user and business profile business logic.
Extracted from views to enable testing and reusability.
"""
import logging
from typing import Dict, Optional
from django.contrib.auth.models import User
from django.db import transaction

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
        
        Args:
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            Dict with success message
            
        Raises:
            ValueError: If validation fails
        """
        if not self.user.check_password(current_password):
            raise ValueError("Current password is incorrect")
        
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters")
        
        self.user.set_password(new_password)
        self.user.save(update_fields=["password"])
        
        # Invalidate cache
        CacheService.invalidate_user_cache(self.user.id)
        
        # Publish event
        event_bus.publish(
            EventTypes.USER_PASSWORD_RESET,
            {
                "user_id": self.user.id,
            },
            source="ProfileService"
        )
        
        return {"message": "Password updated successfully"}
    
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
