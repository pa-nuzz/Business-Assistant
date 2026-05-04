"""Workspace context and AI memory management service."""
from typing import Optional, Dict, List, Any
from django.contrib.auth.models import User
from core.models import WorkspaceContext, ConversationMemory, Conversation
import logging

logger = logging.getLogger(__name__)


class WorkspaceService:
    """Service for managing workspace context and AI memory."""

    def __init__(self, user: User):
        self.user = user

    def get_or_create_context(
        self, 
        workspace_id: str, 
        workspace_name: str = ""
    ) -> WorkspaceContext:
        """Get or create a workspace context for the user."""
        context, created = WorkspaceContext.objects.get_or_create(
            user=self.user,
            workspace_id=workspace_id,
            defaults={
                "workspace_name": workspace_name or f"Workspace {workspace_id}",
                "business_context": {},
                "ai_memory": [],
                "conversation_summaries": [],
                "preferences": {},
            }
        )
        
        if not created and workspace_name and workspace_name != context.workspace_name:
            context.workspace_name = workspace_name
            context.save(update_fields=["workspace_name"])
        
        return context

    def get_workspace_context(
        self, 
        workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get workspace context for AI prompt injection."""
        try:
            context = WorkspaceContext.objects.get(
                user=self.user, 
                workspace_id=workspace_id,
                is_active=True
            )
            return context.get_context_for_prompt()
        except WorkspaceContext.DoesNotExist:
            return None

    def update_business_context(
        self, 
        workspace_id: str, 
        **kwargs
    ) -> WorkspaceContext:
        """Update business context for a workspace."""
        context = self.get_or_create_context(workspace_id)
        context.update_business_context(**kwargs)
        return context

    def add_memory(
        self,
        workspace_id: str,
        memory_type: str,
        content: str,
        source_conversation_id: str = None
    ) -> Dict:
        """Add a new memory entry to the workspace."""
        context = self.get_or_create_context(workspace_id)
        memory = context.add_memory(memory_type, content, source_conversation_id)
        return memory

    def get_memories(
        self,
        workspace_id: str,
        memory_type: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get memories for a workspace, optionally filtered by type."""
        try:
            context = WorkspaceContext.objects.get(
                user=self.user,
                workspace_id=workspace_id,
                is_active=True
            )
            memories = context.ai_memory
            
            if memory_type:
                memories = [m for m in memories if m.get("type") == memory_type]
            
            # Return most recent first, limited to specified count
            return memories[-limit:][::-1]
        except WorkspaceContext.DoesNotExist:
            return []

    def add_conversation_summary(
        self,
        workspace_id: str,
        conversation_id: str,
        summary: str,
        topics: List[str] = None
    ) -> Dict:
        """Add a conversation summary for long-term context."""
        context = self.get_or_create_context(workspace_id)
        return context.add_conversation_summary(conversation_id, summary, topics)

    def update_preferences(
        self,
        workspace_id: str,
        **preferences
    ) -> WorkspaceContext:
        """Update workspace preferences."""
        context = self.get_or_create_context(workspace_id)
        context.preferences.update(preferences)
        context.save(update_fields=["preferences"])
        return context

    def list_workspaces(self) -> List[Dict]:
        """List all active workspaces for the user."""
        contexts = WorkspaceContext.objects.filter(
            user=self.user,
            is_active=True
        ).order_by("-last_accessed")
        
        return [
            {
                "workspace_id": ctx.workspace_id,
                "workspace_name": ctx.workspace_name,
                "created_at": ctx.created_at.isoformat(),
                "last_accessed": ctx.last_accessed.isoformat(),
                "memory_count": len(ctx.ai_memory),
                "preferences": ctx.preferences,
            }
            for ctx in contexts
        ]

    def archive_workspace(self, workspace_id: str) -> bool:
        """Archive a workspace (soft delete)."""
        try:
            context = WorkspaceContext.objects.get(
                user=self.user,
                workspace_id=workspace_id
            )
            context.is_active = False
            context.save(update_fields=["is_active"])
            return True
        except WorkspaceContext.DoesNotExist:
            return False

    def delete_memory(self, workspace_id: str, memory_index: int) -> bool:
        """Delete a specific memory entry by index."""
        try:
            context = WorkspaceContext.objects.get(
                user=self.user,
                workspace_id=workspace_id
            )
            if 0 <= memory_index < len(context.ai_memory):
                context.ai_memory.pop(memory_index)
                context.save(update_fields=["ai_memory"])
                return True
            return False
        except WorkspaceContext.DoesNotExist:
            return False


class ConversationMemoryService:
    """Service for managing per-conversation memory."""

    def __init__(self, conversation: Conversation):
        self.conversation = conversation

    def get_or_create_memory(self) -> ConversationMemory:
        """Get or create memory for this conversation."""
        memory, created = ConversationMemory.objects.get_or_create(
            conversation=self.conversation,
            defaults={
                "extracted_facts": [],
                "user_intents": [],
                "running_summary": "",
                "topics": [],
            }
        )
        return memory

    def add_fact(self, fact: str, confidence: float = 1.0) -> Dict:
        """Add an extracted fact about the conversation."""
        memory = self.get_or_create_memory()
        memory.add_fact(fact, confidence)
        return {"fact": fact, "confidence": confidence}

    def update_summary(self, summary: str) -> str:
        """Update the running conversation summary."""
        memory = self.get_or_create_memory()
        memory.update_summary(summary)
        return summary

    def add_user_intent(self, intent: str, confidence: float = 1.0) -> List[Dict]:
        """Add a detected user intent."""
        memory = self.get_or_create_memory()
        memory.user_intents.append({
            "intent": intent,
            "confidence": confidence,
            "timestamp": __import__('django.utils.timezone').now().isoformat(),
        })
        memory.save(update_fields=["user_intents"])
        return memory.user_intents

    def add_topic(self, topic: str) -> List[str]:
        """Add a topic discussed in the conversation."""
        memory = self.get_or_create_memory()
        if topic not in memory.topics:
            memory.topics.append(topic)
            memory.save(update_fields=["topics"])
        return memory.topics

    def get_memory_context(self) -> Dict:
        """Get all memory context for this conversation."""
        memory = self.get_or_create_memory()
        return {
            "extracted_facts": memory.extracted_facts,
            "user_intents": memory.user_intents,
            "running_summary": memory.running_summary,
            "topics": memory.topics,
        }

    def clear_memory(self) -> bool:
        """Clear all memory for this conversation."""
        try:
            memory = ConversationMemory.objects.get(conversation=self.conversation)
            memory.delete()
            return True
        except ConversationMemory.DoesNotExist:
            return False
