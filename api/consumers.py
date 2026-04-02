"""
Chat WebSocket Consumer for real-time streaming chat.
"""
import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat with streaming responses.
    
    Connect to: ws://host/ws/chat/
    Send: {"message": "Hello", "conversation_id": "uuid" (optional)}
    Receive: {"type": "token", "data": "Hello"}
                 {"type": "metadata", "data": {...}}
                 {"type": "done"}
                 {"type": "error", "data": "..."}
    """

    async def connect(self):
        """Accept connection only for authenticated users."""
        self.user = self.scope.get("user", AnonymousUser())
        
        if self.user.is_anonymous:
            await self.close(code=4001)  # Unauthorized
            return
            
        await self.accept()
        self.conversation_id = None

    async def disconnect(self, close_code):
        """Handle disconnection."""
        pass

    async def receive(self, text_data):
        """Handle incoming messages."""
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            conversation_id = data.get("conversation_id")
            
            if not message:
                await self.send_error("Message cannot be empty")
                return
                
            if len(message) > 4000:
                await self.send_error("Message too long (max 4000 chars)")
                return
            
            # Get or create conversation
            conversation = await self.get_or_create_conversation(conversation_id, message)
            self.conversation_id = str(conversation.id)
            
            # Save user message
            await self.save_message(conversation, "user", message)
            
            # Build conversation history
            history = await self.build_history(conversation)
            
            # Send metadata
            await self.send(json.dumps({
                "type": "metadata",
                "data": {
                    "conversation_id": self.conversation_id,
                    "model": "streaming_orchestrator",
                }
            }))
            
            # Stream the response
            full_response = []
            from agents import orchestrator
            
            for sse_data in orchestrator.run_stream(
                user_message=message,
                user_id=self.user.id,
                conversation_history=history,
                user_name=self.user.get_full_name() or self.user.username,
                conversation_id=self.conversation_id,
            ):
                # Parse SSE data
                if sse_data.startswith('data: '):
                    try:
                        payload = json.loads(sse_data[6:])  # Remove 'data: ' prefix
                        
                        if "token" in payload:
                            token = payload["token"]
                            full_response.append(token)
                            await self.send(json.dumps({
                                "type": "token",
                                "data": token
                            }))
                        elif "metadata" in payload:
                            await self.send(json.dumps({
                                "type": "metadata",
                                "data": payload["metadata"]
                            }))
                        elif "error" in payload:
                            await self.send(json.dumps({
                                "type": "error",
                                "data": payload["error"]
                            }))
                    except json.JSONDecodeError:
                        pass
                elif "[DONE]" in sse_data:
                    break
            
            # Save assistant message
            response_text = "".join(full_response)
            await self.save_message(conversation, "assistant", response_text)
            
            # Send done signal
            await self.send(json.dumps({"type": "done"}))
            
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")

    async def send_error(self, message):
        """Send error message to client."""
        await self.send(json.dumps({
            "type": "error",
            "data": message
        }))

    @database_sync_to_async
    def get_or_create_conversation(self, conversation_id, message):
        """Get existing or create new conversation."""
        from core.models import Conversation
        
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    user=self.user
                )
                return conversation
            except Conversation.DoesNotExist:
                pass
        
        return Conversation.objects.create(
            user=self.user,
            title=message[:80],
        )

    @database_sync_to_async
    def build_history(self, conversation):
        """Build conversation history for the model."""
        from core.models import BusinessProfile
        
        recent_messages = conversation.messages.order_by("created_at")[:20]
        
        # Check if user has a business profile
        system_message = None
        try:
            profile = BusinessProfile.objects.get(user=self.user)
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

    @database_sync_to_async
    def save_message(self, conversation, role, content):
        """Save message to database."""
        from core.models import Message
        
        return Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
        )
