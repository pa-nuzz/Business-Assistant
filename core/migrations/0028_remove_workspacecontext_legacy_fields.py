# Remove legacy fields from WorkspaceContext and enforce NOT NULL workspace
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0027_workspace_data_migration"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Safety check: ensure no rows have NULL workspace before enforcing NOT NULL.
        # All rows were verified to have workspace set by the 0027 data migration.
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM core_workspacecontext WHERE workspace_id IS NULL) THEN
                    RAISE EXCEPTION 'Cannot make workspace NOT NULL: rows with NULL workspace exist. Run data migration 0027 first.';
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Remove legacy fields
        migrations.RemoveField(
            model_name="workspacecontext",
            name="user",
        ),
        migrations.RemoveField(
            model_name="workspacecontext",
            name="legacy_workspace_id",
        ),
        migrations.RemoveField(
            model_name="workspacecontext",
            name="workspace_name",
        ),

        # Enforce NOT NULL on workspace (all rows have workspace set)
        migrations.AlterField(
            model_name="workspacecontext",
            name="workspace",
            field=models.OneToOneField(
                blank=False,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="context",
                to="core.workspace",
            ),
        ),
    ]