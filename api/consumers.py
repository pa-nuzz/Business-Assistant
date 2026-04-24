"""
Chat WebSocket Consumer for real-time streaming chat.
"""
import asyncio
import json
import logging
import time
from collections import defaultdict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

# Rate limiting configuration
_user_message_times = defaultdict(list)
RATE_LIMIT = 20       # messages
RATE_WINDOW = 60      # seconds


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat with streaming responses.
    
    Connect to: ws://host/ws/chat/
    Send: {"message": "Hello", "conversation_id": "uuid" (optional)}
    Receive: {"type": "token", "data": "Hello"}
                 {"type": "metadata", "data": {...}}
                 {"type": "done"}
                 {"type": "error", "data": "..."}
                 {"type": "ping"}
    """

    async def connect(self):
        """Accept connection only for authenticated users."""
        self.user = self.scope.get("user", AnonymousUser())
        
        if self.user.is_anonymous:
            await self.close(code=4001)  # Unauthorized
            return
            
        await self.accept()
        self.conversation_id = None
        
        # Start keepalive ping task
        self.keepalive_task = asyncio.ensure_future(self.send_ping())

    async def send_ping(self):
        """Send periodic ping to keep connection alive and detect dead clients."""
        while True:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                await self.send(text_data=json.dumps({"type": "ping"}))
            except Exception:
                # Connection is dead, exit the loop
                break

    async def disconnect(self, close_code):
        """Handle disconnection - clean up rate limiting data."""
        # Remove user's rate limiting data on disconnect
        user_id = getattr(self, 'user', None)
        if user_id and hasattr(user_id, 'id') and user_id.id in _user_message_times:
            del _user_message_times[user_id.id]

    async def receive(self, text_data):
        """Handle incoming messages with rate limiting."""
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
            
            # Rate limiting check
            user_id = self.user.id
            now = time.time()
            times = _user_message_times[user_id]
            
            # Remove timestamps outside the window
            _user_message_times[user_id] = [t for t in times if now - t < RATE_WINDOW]
            
            if len(_user_message_times[user_id]) >= RATE_LIMIT:
                await self.send_error("Too many messages. Please wait a moment.")
                return
            
            _user_message_times[user_id].append(now)
            
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
            if response_text.strip():
                await self.save_message(conversation, "assistant", response_text)
                # Update conversation timestamp
                await self.update_conversation_timestamp(conversation)
            
            # Send done signal
            await self.send(json.dumps({"type": "done"}))
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in WebSocket receive: {e}")
            await self.send_error(f"Error processing message: {str(e)}")

    async def send_error(self, message):
        # Send error to websocket client
        await self.send(json.dumps({
            "type": "error",
            "data": message
        }))

    @database_sync_to_async
    def get_or_create_conversation(self, conversation_id, message):
        # Find existing chat or start new one
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

    @database_sync_to_async
    def update_conversation_timestamp(self, conversation):
        # Bump chat to top of sidebar
        from django.utils import timezone
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
