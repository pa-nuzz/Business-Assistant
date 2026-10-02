"""Signals for the core app.

Ensures every new user gets a Personal workspace (their private scope)
with an owner membership and an empty shared context, per the approved
workspace architecture:

- Personal workspace is created automatically when the user is created.
- Personal is a special workspace for architectural simplicity, but it is a
  distinct product/security scope: it must never gain additional members.
"""
import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="auth.User")
def create_personal_workspace(sender, instance, created, **kwargs):
    """Create the user's Personal workspace + owner membership + context on signup."""
    if not created:
        return

    from core.models import Workspace, WorkspaceMember, WorkspaceContext

    try:
        with transaction.atomic():
            # Idempotent: skip if a Personal workspace already exists
            if Workspace.objects.filter(owner=instance, is_personal=True).exists():
                return

            workspace = Workspace.objects.create(
                name="Personal",
                owner=instance,
                description="Personal workspace",
                is_personal=True,
                is_public=False,
                allow_invite_links=False,
                default_member_role="member",
            )
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=instance,
                role="owner",
                invited_by=instance,
            )
            WorkspaceContext.objects.create(
                workspace=workspace,
                business_context={},
                ai_memory=[],
                conversation_summaries=[],
                preferences={},
            )
            logger.info(f"Created Personal workspace {workspace.id} for user {instance.id}")

    except Exception:
        # Never block user creation because of workspace provisioning.
        logger.exception(f"Failed to create Personal workspace for user {instance.id}")
