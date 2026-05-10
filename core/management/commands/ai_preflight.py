"""Check AI provider readiness before deployment."""
import json

from django.core.management.base import BaseCommand

from core.services.ai_health_service import get_ai_provider_health


class Command(BaseCommand):
    help = "Check configured AI providers without exposing secrets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--live",
            action="store_true",
            help="Make a small live call to each configured provider.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print machine-readable JSON.",
        )

    def handle(self, *args, **options):
        result = get_ai_provider_health(live=options["live"])

        if options["json"]:
            self.stdout.write(json.dumps(result, indent=2))
        else:
            self.stdout.write(f"AI preflight: {result['status']}")
            self.stdout.write(f"Ready providers: {result['ready_provider_count']}")
            for provider in result["providers"]:
                status = provider["status"]
                name = provider["name"]
                model = provider["model"] or "not set"
                detail = provider["detail"]
                self.stdout.write(f"- {name}: {status} ({model}) - {detail}")

        if result["ready_provider_count"] == 0:
            raise SystemExit(1)
