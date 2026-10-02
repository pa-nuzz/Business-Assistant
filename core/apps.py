"""App configuration for core."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Import signals so Personal workspace auto-creation is registered.
        import core.signals  # noqa: F401
