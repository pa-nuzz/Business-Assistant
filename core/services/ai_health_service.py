"""AI provider readiness checks that never expose secrets."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from django.conf import settings


@dataclass
class ProviderHealth:
    name: str
    configured: bool
    enabled: bool
    model: str
    timeout: int
    status: str
    detail: str
    latency_ms: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "configured": self.configured,
            "enabled": self.enabled,
            "model": self.model,
            "timeout": self.timeout,
            "status": self.status,
            "detail": self.detail,
            "latency_ms": self.latency_ms,
        }


def _provider_config(name: str) -> dict[str, Any]:
    return settings.AI_CONFIG.get(name, {})


def get_ai_provider_health(live: bool = False) -> dict[str, Any]:
    """
    Return AI provider status without returning API keys.

    By default this is a safe preflight/config check. Pass live=True from a
    management command when you intentionally want to spend a tiny provider call.
    """
    providers = [
        _check_provider("nvidia", live=live),
        _check_provider("groq", live=live),
        _check_provider("openrouter", live=live),
        _check_provider("gemini", live=live),
    ]
    ready = [p for p in providers if p.enabled and p.configured and p.status in {"ready", "ok"}]
    return {
        "status": "ok" if ready else "degraded",
        "ready_provider_count": len(ready),
        "providers": [p.as_dict() for p in providers],
        "recommended_order": ["nvidia", "groq", "openrouter"],
        "notes": [
            "Gemini chat is intentionally disabled unless GEMINI_CHAT_ENABLED=True.",
            "Dashboard analytics use cached/local summaries and do not require live LLM calls.",
        ],
    }


def _check_provider(name: str, live: bool = False) -> ProviderHealth:
    cfg = _provider_config(name)
    configured = bool(cfg.get("api_key") or cfg.get("api_keys"))
    enabled = configured and (name != "gemini" or bool(cfg.get("chat_enabled")))
    model = str(cfg.get("model") or "")
    timeout = int(cfg.get("timeout") or 0)

    if not configured:
        return ProviderHealth(
            name=name,
            configured=False,
            enabled=False,
            model=model,
            timeout=timeout,
            status="missing_key",
            detail=f"{name.upper()} API key is not configured.",
        )
    if name == "gemini" and not cfg.get("chat_enabled"):
        return ProviderHealth(
            name=name,
            configured=True,
            enabled=False,
            model=model,
            timeout=timeout,
            status="disabled",
            detail="Gemini chat disabled by GEMINI_CHAT_ENABLED=False.",
        )
    if not live:
        return ProviderHealth(
            name=name,
            configured=True,
            enabled=True,
            model=model,
            timeout=timeout,
            status="ready",
            detail="Configured. Run manage.py ai_preflight --live to verify the remote endpoint.",
        )

    started = time.monotonic()
    try:
        _live_probe(name)
        return ProviderHealth(
            name=name,
            configured=True,
            enabled=True,
            model=model,
            timeout=timeout,
            status="ok",
            detail="Live provider probe succeeded.",
            latency_ms=int((time.monotonic() - started) * 1000),
        )
    except Exception as exc:
        return ProviderHealth(
            name=name,
            configured=True,
            enabled=True,
            model=model,
            timeout=timeout,
            status="failed",
            detail=str(exc)[:220],
            latency_ms=int((time.monotonic() - started) * 1000),
        )


def _live_probe(name: str) -> None:
    messages = [{"role": "user", "content": "Reply with OK only."}]
    system_prompt = "You are a health check. Reply with OK only."

    if name == "nvidia":
        from services.nvidia import call

        call(messages, system_prompt, [], timeout=8)
    elif name == "groq":
        from services.groq_service import call

        call(messages, system_prompt, [], timeout=8)
    elif name == "openrouter":
        from services.openrouter import call

        call(messages, system_prompt, [], timeout=8)
    elif name == "gemini":
        from services.gemini import call

        call(messages, system_prompt, [])
    else:
        raise ValueError(f"Unknown provider: {name}")
