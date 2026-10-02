# Workspace refactor: add workspace FKs and restructure WorkspaceContext.
#
# Replays cleanly on a fresh database:
#   1. Copy the legacy workspace_id CharField data into legacy_workspace_id
#   2. Drop the legacy column (PostgreSQL drops its indexes/constraints)
#   3. Add the new workspace OneToOneField (creates the workspace_id uuid column)
#
# Note: schema operations are reversible; the legacy-data copy (RunSQL) is
# one-way — the legacy column is dropped after its values are preserved in
# legacy_workspace_id (consumed by the 0027 data migration, then dropped
# by 0028).
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0025_remove_legacy_models"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Remove the old indexes on the legacy workspace_id CharField
        migrations.RemoveIndex(
            model_name="workspacecontext",
            name="workspace_ctx_user_idx",
        ),
        migrations.RemoveIndex(
            model_name="workspacecontext",
            name="workspace_ctx_id_idx",
        ),

        # 2. Remove the (user, workspace_id) unique constraint
        migrations.AlterUniqueTogether(
            name="workspacecontext",
            unique_together=set(),
        ),

        # 3. Add legacy_workspace_id to hold the old string values
        migrations.AddField(
            model_name="workspacecontext",
            name="legacy_workspace_id",
            field=models.CharField(
                blank=True, db_index=True, max_length=100, null=True
            ),
        ),

        # 4. Preserve old data before dropping the legacy column (one-way)
        migrations.RunSQL(
            sql="""
                UPDATE core_workspacecontext
                SET legacy_workspace_id = workspace_id
                WHERE workspace_id IS NOT NULL AND legacy_workspace_id IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 5. Drop the legacy workspace_id CharField
        migrations.RemoveField(
            model_name="workspacecontext",
            name="workspace_id",
        ),

        # 6. Add the shared workspace OneToOneField (now free to use the
        #    workspace_id column name)
        migrations.AddField(
            model_name="workspacecontext",
            name="workspace",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="context",
                to="core.workspace",
            ),
        ),

        # 7. Relax legacy provenance fields (removed entirely in 0028)
        migrations.AlterField(
            model_name="workspacecontext",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="workspace_contexts",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="workspacecontext",
            name="workspace_name",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),

        # 8. Index the new workspace link
        migrations.AddIndex(
            model_name="workspacecontext",
            index=models.Index(fields=["workspace"], name="workspace_ctx_ws_idx"),
        ),

        # 9. Add nullable workspace FK to the core resources
        migrations.AddField(
            model_name="conversation",
            name="workspace",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="conversations",
                to="core.workspace",
            ),
        ),
        migrations.AddField(
            model_name="document",
            name="workspace",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="documents",
                to="core.workspace",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="workspace",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks",
                to="core.workspace",
            ),
        ),
    ]