"""Workspace context and AI memory management service.

WorkspaceContext is shared per-workspace (OneToOne with Workspace).
Every operation validates the requesting user's membership/role first.
"""
from typing import Optional, Dict, List, Any
from django.contrib.auth.models import User
from core.models import Workspace, WorkspaceMember, WorkspaceContext
import logging

logger = logging.getLogger(__name__)


class WorkspaceAccessError(Exception):
    """Raised when a user attempts to access a workspace they are not a member of."""

    def __init__(self, message: str, status_code: int = 403):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class WorkspaceService:
    """Service for managing shared workspace context and AI memory.

    Security invariant: every method that touches workspace-scoped data
    first validates that the requesting user is an active member of that
    workspace. workspace_id alone never grants access.
    """

    def __init__(self, user: User):
        self.user = user

    # ------------------------------------------------------------------
    # Membership / permission helpers
    # ------------------------------------------------------------------

    def _validate_membership(self, workspace_id: str) -> Workspace:
        """Validate the user is a member of the workspace. Returns the Workspace.

        Raises WorkspaceAccessError with 404 if the workspace doesn't exist
        and 403 if the user is not a member.
        """
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except (Workspace.DoesNotExist, ValueError, TypeError):
            raise WorkspaceAccessError("Workspace not found", status_code=404)

        if not WorkspaceMember.objects.filter(
            workspace=workspace, user=self.user
        ).exists():
            raise WorkspaceAccessError("You are not a member of this workspace", status_code=403)

        return workspace

    def _validate_permission(self, workspace_id: str, permission: str) -> Workspace:
        """Validate membership AND a specific permission. Returns the Workspace."""
        workspace = self._validate_membership(workspace_id)

        if not WorkspaceMember.objects.filter(
            workspace=workspace, user=self.user
        ).first().has_permission(permission):
            raise WorkspaceAccessError(
                f"You don't have permission to perform this action", status_code=403
            )

        return workspace

    # ------------------------------------------------------------------
    # Context management (shared per workspace)
    # ------------------------------------------------------------------

    def get_or_create_context(self, workspace: Workspace) -> WorkspaceContext:
        """Get or create the shared context for a workspace."""
        context, created = WorkspaceContext.objects.get_or_create(
            workspace=workspace,
            defaults={
                "business_context": {},
                "ai_memory": [],
                "conversation_summaries": [],
                "preferences": {},
            }
        )
        return context

    def get_workspace_context(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get workspace context for AI prompt injection (read access required)."""
        workspace = self._validate_membership(workspace_id)

        try:
            context = WorkspaceContext.objects.get(workspace=workspace, is_active=True)
            return context.get_context_for_prompt()
        except WorkspaceContext.DoesNotExist:
            return None

    def update_business_context(self, workspace_id: str, **kwargs) -> WorkspaceContext:
        """Update business context for a workspace (update permission required)."""
        workspace = self._validate_permission(workspace_id, "update")
        context = self.get_or_create_context(workspace)
        context.update_business_context(**kwargs)
        return context

    # ------------------------------------------------------------------
    # Shared AI memory
    # ------------------------------------------------------------------

    def add_memory(
        self,
        workspace_id: str,
        memory_type: str,
        content: str,
        source_conversation_id: str = None,
    ) -> Dict:
        """Add a new shared memory entry to the workspace (update permission)."""
        workspace = self._validate_permission(workspace_id, "update")
        context = self.get_or_create_context(workspace)
        return context.add_memory(memory_type, content, source_conversation_id)

    def get_memories(
        self,
        workspace_id: str,
        memory_type: str = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Get shared memories for a workspace (read access)."""
        workspace = self._validate_membership(workspace_id)

        try:
            context = WorkspaceContext.objects.get(workspace=workspace, is_active=True)
            memories = context.ai_memory
        except WorkspaceContext.DoesNotExist:
            return []

        if memory_type:
            memories = [m for m in memories if m.get("type") == memory_type]

        # Return most recent first, limited to specified count
        return memories[-limit:][::-1]

    def delete_memory(self, workspace_id: str, memory_index: int) -> bool:
        """Delete a specific shared memory entry by index (update permission).

        Note: index-based deletion is fragile under concurrent edits; a
        UUID-keyed memory store is planned as a later layer.
        """
        workspace = self._validate_permission(workspace_id, "update")

        try:
            context = WorkspaceContext.objects.get(workspace=workspace)
        except WorkspaceContext.DoesNotExist:
            return False

        if 0 <= memory_index < len(context.ai_memory):
            context.ai_memory.pop(memory_index)
            context.save(update_fields=["ai_memory"])
            return True
        return False

    # ------------------------------------------------------------------
    # Conversation summaries (shared long-term context)
    # ------------------------------------------------------------------

    def add_conversation_summary(
        self,
        workspace_id: str,
        conversation_id: str,
        summary: str,
        topics: List[str] = None,
    ) -> Dict:
        """Add a conversation summary to the workspace's shared context (update permission)."""
        workspace = self._validate_permission(workspace_id, "update")
        context = self.get_or_create_context(workspace)
        return context.add_conversation_summary(conversation_id, summary, topics)

    # ------------------------------------------------------------------
    # Preferences (shared workspace settings)
    # ------------------------------------------------------------------

    def update_preferences(self, workspace_id: str, **preferences) -> WorkspaceContext:
        """Update shared workspace preferences (update permission)."""
        workspace = self._validate_permission(workspace_id, "update")
        context = self.get_or_create_context(workspace)
        context.preferences.update(preferences)
        context.save(update_fields=["preferences"])
        return context

    # ------------------------------------------------------------------
    # Workspace listing / archival
    # ------------------------------------------------------------------

    def list_workspaces(self) -> List[Dict]:
        """List all workspaces where the user is a member (from memberships)."""
        memberships = WorkspaceMember.objects.filter(
            user=self.user
        ).select_related("workspace").order_by("-workspace__updated_at")

        results = []
        for m in memberships:
            results.append({
                "workspace_id": str(m.workspace.id),
                "workspace_name": m.workspace.name,
                "description": m.workspace.description,
                "role": m.role,
                "created_at": m.workspace.created_at.isoformat(),
                "updated_at": m.workspace.updated_at.isoformat(),
                "memory_count": WorkspaceContext.objects.filter(
                    workspace=m.workspace
                ).values_list("ai_memory", flat=True).first() and len(
                    WorkspaceContext.objects.filter(
                        workspace=m.workspace
                    ).values_list("ai_memory", flat=True).first()
                ) or 0,
            })
        return results

    def archive_workspace(self, workspace_id: str) -> bool:
        """Deactivate a workspace context (manage_settings = owner only)."""
        workspace = self._validate_permission(workspace_id, "manage_settings")

        try:
            context = WorkspaceContext.objects.get(workspace=workspace)
            context.is_active = False
            context.save(update_fields=["is_active"])
            return True
        except WorkspaceContext.DoesNotExist:
            return False
