"""
Conversation service for managing conversations.
Extracted from views to enable testing and reusability.
"""
import logging
from typing import Dict, List, Optional
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch
from core.models import Conversation, Message

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for handling conversation operations."""
    
    def __init__(self, user: User):
        self.user = user
    
    def list_conversations(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        Get user's conversations with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page (max 100)
            
        Returns:
            Dict with results, count, page, total_pages
        """
        page_size = min(page_size, 100)
        
        convos = Conversation.objects.filter(user=self.user).select_related(
            'user'
        ).prefetch_related(
            'messages'
        ).annotate(
            message_count=Count("messages")
        ).order_by("-updated_at")
        
        paginator = Paginator(convos, page_size)
        page_obj = paginator.get_page(page)
        
        results = []
        for convo in page_obj.object_list:
            results.append({
                "id": str(convo.id),
                "title": convo.title or "Untitled conversation",
                "created_at": convo.created_at,
                "updated_at": convo.updated_at,
                "message_count": convo.message_count,
            })
        
        return {
            "results": results,
            "count": paginator.count,
            "page": page,
            "total_pages": paginator.num_pages,
        }
    
    def get_conversation(self, conversation_id: str) -> Dict:
        """
        Get single conversation with all messages.
        
        Args:
            conversation_id: UUID of the conversation
            
        Returns:
            Dict with conversation details and messages
            
        Raises:
            ValueError: If conversation not found
        """
        try:
            convo = Conversation.objects.prefetch_related(
                Prefetch('messages', queryset=Message.objects.order_by('created_at'))
            ).get(id=conversation_id, user=self.user)
        except Conversation.DoesNotExist:
            raise ValueError("Conversation not found")
        
        messages_data = [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
                "tool_calls": m.tool_calls,
                "model_used": m.model_used
            }
            for m in convo.messages.all()
        ]
        
        return {
            "id": str(convo.id),
            "title": convo.title,
            "created_at": convo.created_at,
            "updated_at": convo.updated_at,
            "messages": messages_data,
        }
    
    def export_conversation(self, conversation_id: str) -> Dict:
        """
        Export conversation as JSON for backup.
        
        Args:
            conversation_id: UUID of the conversation
            
        Returns:
            Dict with conversation data for export
            
        Raises:
            ValueError: If conversation not found
        """
        from datetime import datetime
        
        try:
            convo = Conversation.objects.get(id=conversation_id, user=self.user)
        except Conversation.DoesNotExist:
            raise ValueError("Conversation not found")
        
        messages = convo.messages.order_by("created_at").values(
            "role", "content", "created_at"
        )
        
        return {
            "id": str(convo.id),
            "title": convo.title,
            "exported_at": datetime.now().isoformat(),
            "messages": list(messages),
        }
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and its messages.
        
        Args:
            conversation_id: UUID of the conversation
            
        Returns:
            True if deleted, False if not found
        """
        deleted, _ = Conversation.objects.filter(
            id=conversation_id,
            user=self.user
        ).delete()
        return deleted > 0
    
    def soft_delete_conversation(self, conversation_id: str) -> bool:
        """
        Soft delete a conversation (mark as deleted).
        
        Args:
            conversation_id: UUID of the conversation
            
        Returns:
            True if deleted, False if not found
        """
        try:
            convo = Conversation.objects.get(id=conversation_id, user=self.user)
            convo.soft_delete(user=self.user)
            return True
        except Conversation.DoesNotExist:
            return False
