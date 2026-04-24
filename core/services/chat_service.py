"""
Chat service for handling chat business logic.
Extracted from views to enable testing and reusability.
"""
import logging
from typing import Dict, List, Optional, Generator
from django.contrib.auth.models import User
from core.models import Conversation, Message
from agents import orchestrator
from utils.sanitization import sanitize_plain_text

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat operations."""
    
    def __init__(self, user: User):
        self.user = user
    
    def send_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict:
        """
        Send a message and get AI response.
        
        Args:
            message: User message content
            conversation_id: Optional conversation ID to continue
            stream: Whether to stream the response
            
        Returns:
            Dict with reply, conversation_id, model_used, tools_used, intent
        """
        # Validate and sanitize message
        message = message.strip()
        if not message:
            raise ValueError("Message cannot be empty")
        
        message = sanitize_plain_text(message, max_length=4000)
        if len(message) > 4000:
            raise ValueError("Message too long (max 4000 chars)")
        
        # Get or create conversation
        conversation = self._get_or_create_conversation(conversation_id, message)
        
        # Build conversation history
        history = self._build_conversation_history(conversation)
        
        # Run agent
        try:
            result = orchestrator.run(
                user_message=message,
                user_id=self.user.id,
                conversation_history=history,
                user_name=self.user.get_full_name() or self.user.username,
            )
        except Exception as e:
            logger.exception("Agent run failed")
            raise RuntimeError("Failed to process message") from e
        
        # Save messages to DB
        self._save_messages(conversation, message, result)
        
        return {
            "reply": result.get("reply", ""),
            "conversation_id": str(conversation.id),
            "model_used": result.get("model", "unknown"),
            "tools_used": result.get("tools_used", []),
            "intent": result.get("intent", "chat"),
        }
    
    def send_message_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Send a message and stream AI response.
        
        Args:
            message: User message content
            conversation_id: Optional conversation ID to continue
            
        Yields:
            SSE formatted strings
        """
        # Validate and sanitize message
        message = message.strip()
        if not message:
            raise ValueError("Message cannot be empty")
        
        message = sanitize_plain_text(message, max_length=4000)
        if len(message) > 4000:
            raise ValueError("Message too long (max 4000 chars)")
        
        # Get or create conversation
        conversation = self._get_or_create_conversation(conversation_id, message)
        
        # Build conversation history
        history = self._build_conversation_history(conversation)
        
        # Save user message immediately
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=message,
        )
        conversation.save(update_fields=["updated_at"])
        
        # Stream response
        full_response = []
        model_info = {"used": "unknown"}
        stream_error = None
        
        try:
            for sse_data in orchestrator.run_stream(
                user_message=message,
                user_id=self.user.id,
                conversation_history=history,
                user_name=self.user.get_full_name() or self.user.username,
                conversation_id=str(conversation.id),
            ):
                yield sse_data
                
                # Collect response for saving
                if sse_data.startswith('data: ') and '[DONE]' not in sse_data:
                    try:
                        import json
                        data = json.loads(sse_data[6:])
                        if "token" in data:
                            full_response.append(data["token"])
                        if "metadata" in data:
                            model_info["used"] = data["metadata"].get("model", "unknown")
                        if "error" in data:
                            stream_error = data["error"]
                            logger.warning(f"Stream error received: {stream_error}")
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"SSE parse error: {e}")
                        
        except Exception as e:
            logger.exception("Streaming failed")
            stream_error = str(e)
            yield f'data: {{"error": "{str(e)}"}}\n\n'
        
        # Save assistant message after streaming completes (even if error)
        response_text = "".join(full_response)
        if response_text.strip() or stream_error:
            final_content = response_text if response_text.strip() else f"I encountered an error: {stream_error}"
            Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=final_content,
                model_used=model_info["used"],
                tool_calls={"stream_error": stream_error} if stream_error else None,
            )
            conversation.save(update_fields=["updated_at"])
    
    def _get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        message: str
    ) -> Conversation:
        """Get existing conversation or create new one."""
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id, user=self.user)
            except Conversation.DoesNotExist:
                raise ValueError("Conversation not found")
        
        return Conversation.objects.create(
            user=self.user,
            title=message[:80],
        )
    
    def _build_conversation_history(self, conversation: Conversation) -> List[Dict]:
        """Build conversation history with user context."""
        recent_messages = conversation.messages.order_by("created_at")[:20]
        
        system_message = None
        try:
            profile = self.user.business_profile
            if profile and profile.company_name:
                system_content = f"User's business: {profile.company_name}"
                if profile.industry:
                    system_content += f" in the {profile.industry} industry"
                system_message = {"role": "system", "content": system_content}
        except Exception:
            pass
        
        history = []
        if system_message:
            history.append(system_message)
        for m in recent_messages:
            history.append({"role": m.role, "content": m.content})
        
        return history
    
    def _save_messages(self, conversation: Conversation, user_message: str, result: Dict):
        """Save user and assistant messages to database."""
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message,
        )
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=result.get("reply", ""),
            tool_calls=result.get("tools_used", []),
            model_used=result.get("model", "unknown"),
        )
        conversation.save(update_fields=["updated_at"])
