"""Production deployment preflight checks."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from core.services.ai_health_service import get_ai_provider_health


PLACEHOLDERS = (
    "REPLACE_WITH",
    "your_",
    "your-",
    "example.com",
    "your-domain.com",
    "secure_password",
    "redis_password",
    "your-secret-key-here",
)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    severity: str = "error"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "severity": self.severity,
            "detail": self.detail,
        }


class Command(BaseCommand):
    help = "Run production-readiness checks for Oracle Cloud deployment."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Treat warnings as failures.",
        )

    def handle(self, *args, **options):
        results = [
            *self._settings_checks(),
            self._database_check(),
            self._cache_check(),
            self._ai_provider_check(),
        ]

        failures = [r for r in results if not r.ok and (r.severity == "error" or options["strict"])]
        payload = {
            "status": "failed" if failures else "ok",
            "failed_count": len(failures),
            "checks": [r.as_dict() for r in results],
        }

        if options["json"]:
            self.stdout.write(json.dumps(payload, indent=2))
        else:
            self.stdout.write(f"Deploy preflight: {payload['status']}")
            for result in results:
                marker = "OK" if result.ok else result.severity.upper()
                self.stdout.write(f"- [{marker}] {result.name}: {result.detail}")

        if failures:
            raise CommandError("Deployment preflight failed. Fix the errors above before deploying.")

    def _settings_checks(self) -> list[CheckResult]:
        checks: list[CheckResult] = []
        env = os.environ

        checks.append(CheckResult(
            "debug",
            not settings.DEBUG,
            "DEBUG is disabled." if not settings.DEBUG else "DEBUG must be False in production.",
        ))

        secret_key = getattr(settings, "SECRET_KEY", "")
        checks.append(CheckResult(
            "secret_key",
            bool(secret_key) and len(secret_key) >= 40 and not _has_placeholder(secret_key),
            "SECRET_KEY looks production-grade." if secret_key else "SECRET_KEY is missing.",
        ))

        allowed_hosts = list(getattr(settings, "ALLOWED_HOSTS", []))
        checks.append(CheckResult(
            "allowed_hosts",
            bool(allowed_hosts) and "*" not in allowed_hosts and not _only_local_hosts(allowed_hosts),
            f"ALLOWED_HOSTS configured: {', '.join(allowed_hosts)}",
        ))

        frontend_url = env.get("FRONTEND_URL", "")
        checks.append(CheckResult(
            "frontend_url",
            frontend_url.startswith("https://") and not _has_placeholder(frontend_url),
            f"FRONTEND_URL={frontend_url or 'missing'}",
        ))

        cors_origins = list(getattr(settings, "CORS_ALLOWED_ORIGINS", []))
        checks.append(CheckResult(
            "cors",
            bool(cors_origins) and all(o.startswith("https://") and not _has_placeholder(o) for o in cors_origins),
            f"CORS_ALLOWED_ORIGINS={', '.join(cors_origins) if cors_origins else 'missing'}",
        ))

        csrf_origins = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", []))
        checks.append(CheckResult(
            "csrf",
            bool(csrf_origins) and all(o.startswith("https://") and not _has_placeholder(o) for o in csrf_origins),
            f"CSRF_TRUSTED_ORIGINS={', '.join(csrf_origins) if csrf_origins else 'missing'}",
        ))

        checks.append(CheckResult(
            "secure_cookies",
            bool(settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE),
            "Secure session and CSRF cookies are enabled.",
        ))

        checks.append(CheckResult(
            "https",
            bool(settings.SECURE_SSL_REDIRECT and settings.SECURE_HSTS_SECONDS >= 31536000),
            "HTTPS redirect and one-year HSTS are enabled.",
        ))

        for name in ("DATABASE_URL", "REDIS_URL", "DB_PASSWORD", "REDIS_PASSWORD"):
            value = env.get(name, "")
            checks.append(CheckResult(
                f"env_{name.lower()}",
                bool(value) and not _has_placeholder(value),
                f"{name} is set." if value else f"{name} is missing.",
            ))

        return checks

    def _database_check(self) -> CheckResult:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return CheckResult("database", True, "Database connection succeeded.")
        except Exception as exc:
            return CheckResult("database", False, f"Database connection failed: {exc}")

    def _cache_check(self) -> CheckResult:
        try:
            cache.set("deploy_preflight", "ok", timeout=30)
            ok = cache.get("deploy_preflight") == "ok"
            return CheckResult(
                "cache",
                ok,
                "Cache read/write succeeded." if ok else "Cache write did not round-trip.",
            )
        except Exception as exc:
            return CheckResult("cache", False, f"Cache connection failed: {exc}")

    def _ai_provider_check(self) -> CheckResult:
        health = get_ai_provider_health(live=False)
        count = int(health.get("ready_provider_count", 0))
        return CheckResult(
            "ai_providers",
            count > 0,
            f"{count} AI provider(s) configured and ready.",
        )


def _has_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(token.lower() in lowered for token in PLACEHOLDERS)


def _only_local_hosts(hosts: list[str]) -> bool:
    local = {"localhost", "127.0.0.1", "0.0.0.0", "backend"}
    return all(host in local for host in hosts)
