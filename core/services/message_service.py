"""
Message service for managing messages.
Extracted from views to enable testing and reusability.
"""
import logging
from typing import Dict, List
from django.contrib.auth.models import User
from core.models import Message, Conversation

logger = logging.getLogger(__name__)


class MessageService:
    """Service for handling message operations."""
    
    def __init__(self, user: User):
        self.user = user
    
    def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List] = None,
        tool_results: Optional[Dict] = None,
        model_used: Optional[str] = None
    ) -> Message:
        """
        Create a new message in a conversation.
        
        Args:
            conversation_id: UUID of the conversation
            role: Message role (user, assistant, tool)
            content: Message content
            tool_calls: Optional tool calls made
            tool_results: Optional tool results
            model_used: Optional AI model used
            
        Returns:
            Created Message instance
            
        Raises:
            ValueError: If conversation not found or invalid role
        """
        valid_roles = ["user", "assistant", "tool"]
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                user=self.user
            )
        except Conversation.DoesNotExist:
            raise ValueError("Conversation not found")
        
        message = Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results,
            model_used=model_used,
        )
        
        # Update conversation timestamp
        conversation.save(update_fields=["updated_at"])
        
        return message
    
    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages from a conversation.
        
        Args:
            conversation_id: UUID of the conversation
            limit: Optional limit on number of messages
            
        Returns:
            List of Message instances
            
        Raises:
            ValueError: If conversation not found
        """
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                user=self.user
            )
        except Conversation.DoesNotExist:
            raise ValueError("Conversation not found")
        
        queryset = conversation.messages.order_by("created_at")
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    def get_messages_as_dict(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get messages from a conversation as dictionaries.
        
        Args:
            conversation_id: UUID of the conversation
            limit: Optional limit on number of messages
            
        Returns:
            List of message dictionaries
        """
        messages = self.get_messages(conversation_id, limit)
        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
                "tool_calls": m.tool_calls,
                "tool_results": m.tool_results,
                "model_used": m.model_used,
            }
            for m in messages
        ]
