# Data migration: Create Personal Workspaces and migrate data
from django.db import migrations
from django.utils import timezone


def create_personal_workspaces(apps, schema_editor):
    """Create Personal Workspace for each user and owner WorkspaceMember."""
    User = apps.get_model('auth', 'User')
    Workspace = apps.get_model('core', 'Workspace')
    WorkspaceMember = apps.get_model('core', 'WorkspaceMember')
    
    for user in User.objects.all():
        # Skip if already has a personal workspace
        if Workspace.objects.filter(owner=user, name="Personal").exists():
            continue
            
        workspace = Workspace.objects.create(
            name="Personal",
            owner=user,
            description="Personal workspace",
            is_public=False,
            allow_invite_links=False,
            default_member_role='member',
        )
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=user,
            role='owner',
            invited_by=user,
            invited_at=timezone.now(),
        )


def backfill_resources_to_personal(apps, schema_editor):
    """Backfill Tasks, Documents, Conversations to user's Personal Workspace."""
    Task = apps.get_model('core', 'Task')
    Document = apps.get_model('core', 'Document')
    Conversation = apps.get_model('core', 'Conversation')
    Workspace = apps.get_model('core', 'Workspace')
    
    for workspace in Workspace.objects.filter(name="Personal"):
        user = workspace.owner
        Task.objects.filter(user=user, workspace__isnull=True).update(workspace=workspace)
        Document.objects.filter(user=user, workspace__isnull=True).update(workspace=workspace)
        Conversation.objects.filter(user=user, workspace__isnull=True).update(workspace=workspace)


def migrate_workspace_contexts(apps, schema_editor):
    """Migrate per-user WorkspaceContext 'default' to shared Personal Workspace context.

    Private user data is preserved in the user's Personal scope only — it is
    never copied into collaborative workspaces. After migration, the legacy
    per-user rows are deleted so the table contains only workspace-linked
    shared contexts (0028 enforces NOT NULL workspace).
    """
    WorkspaceContext = apps.get_model('core', 'WorkspaceContext')
    Workspace = apps.get_model('core', 'Workspace')
    
    # For each user's "default" context, create/update shared context for
    # that user's Personal Workspace (their private scope)
    for old_ctx in WorkspaceContext.objects.filter(legacy_workspace_id="default"):
        personal_ws = Workspace.objects.filter(owner=old_ctx.user, name="Personal").first()
        if personal_ws:
            WorkspaceContext.objects.update_or_create(
                workspace=personal_ws,
                defaults={
                    "business_context": old_ctx.business_context,
                    "ai_memory": old_ctx.ai_memory,
                    "conversation_summaries": old_ctx.conversation_summaries,
                    "preferences": old_ctx.preferences,
                    "is_active": old_ctx.is_active,
                    "last_accessed": old_ctx.last_accessed,
                    "created_at": old_ctx.created_at,
                    "user": old_ctx.user,
                    "legacy_workspace_id": old_ctx.legacy_workspace_id,
                    "workspace_name": old_ctx.workspace_name,
                }
            )
    
    # For existing collaborative workspaces, create an EMPTY shared
    # WorkspaceContext — no private data is ever copied here.
    from django.db import connection
    for ws in Workspace.objects.exclude(name="Personal"):
        if not hasattr(ws, 'context') or ws.context is None:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO core_workspacecontext 
                    (id, workspace_id, business_context, ai_memory, conversation_summaries, preferences, is_active, last_accessed, created_at)
                    VALUES (gen_random_uuid(), %s, '{}', '[]', '[]', '{}', true, now(), now())
                    ON CONFLICT (workspace_id) DO NOTHING
                    """,
                    [str(ws.id)]
                )

    # Delete the legacy per-user rows now that their data is preserved in
    # each user's Personal workspace context.
    WorkspaceContext.objects.filter(
        workspace__isnull=True, legacy_workspace_id__isnull=False
    ).exclude(legacy_workspace_id="").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0026_workspace_refactor"),
    ]

    operations = [
        migrations.RunPython(create_personal_workspaces, migrations.RunPython.noop),
        migrations.RunPython(backfill_resources_to_personal, migrations.RunPython.noop),
        migrations.RunPython(migrate_workspace_contexts, migrations.RunPython.noop),
    ]