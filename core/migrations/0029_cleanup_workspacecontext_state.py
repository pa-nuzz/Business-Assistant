# No-op migration (superseded).
#
# Originally removed the legacy workspacecontext state (indexes, unique
# constraint, workspace_id CharField) as a state-only operation. Those
# removals are now performed correctly as real operations in
# 0026_workspace_refactor, so this migration must do nothing when
# replayed on a fresh database.
#
# The file is kept (rather than deleted) because it is already recorded as
# applied in existing development databases.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_remove_workspacecontext_legacy_fields"),
    ]

    operations = []