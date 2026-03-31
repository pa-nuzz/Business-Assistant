"""
Model Router — Gemini → Groq → OpenRouter fallback chain.

Design principles:
- Try Gemini first (best quality, generous free tier)
- On timeout or API error, fall to Groq (fast, free)
- On Groq failure, fall to OpenRouter (has free models)
- Log every fallback so you know when to fix things
- Never silently fail — always raise if all three fail
"""
import logging
from typing import Optional
from django.conf import settings

from services import gemini, groq_service, openrouter

logger = logging.getLogger(__name__)


class ModelUnavailableError(Exception):
    """Raised when all model providers fail."""
    pass


def call_with_fallback(
    messages: list[dict],
    system_prompt: str,
    tool_definitions: list,
) -> dict:
    """
    Tries each model in order. Returns the first successful response.

    Response format:
    {
        "text": str | None,
        "tool_calls": list | None,
        "model": "gemini/..." | "groq/..." | "openrouter/...",
        "stop_reason": "tool_use" | "end_turn"
    }
    """
    cfg = settings.AI_CONFIG

    # ── 1. Try Gemini ──────────────────────────────────────────────────────────
    if cfg["gemini"]["api_key"]:
        try:
            result = gemini.call(
                messages=messages,
                system_prompt=system_prompt,
                tool_definitions=tool_definitions,
                timeout=cfg["gemini"]["timeout"],
            )
            logger.info(f"Model used: {result['model']}")
            return result
        except TimeoutError:
            logger.warning("Gemini timed out → falling back to Groq")
        except Exception as e:
            logger.warning(f"Gemini failed ({type(e).__name__}: {e}) → falling back to Groq")
    else:
        logger.debug("Gemini skipped (no API key)")

    # ── 2. Try Groq ────────────────────────────────────────────────────────────
    if cfg["groq"]["api_key"]:
        try:
            result = groq_service.call(
                messages=messages,
                system_prompt=system_prompt,
                tool_definitions=tool_definitions,
                timeout=cfg["groq"]["timeout"],
            )
            logger.info(f"Model used: {result['model']} (fallback)")
            return result
        except TimeoutError:
            logger.warning("Groq timed out → falling back to OpenRouter")
        except Exception as e:
            logger.warning(f"Groq failed ({type(e).__name__}: {e}) → falling back to OpenRouter")
    else:
        logger.debug("Groq skipped (no API key)")

    # ── 3. Try OpenRouter ──────────────────────────────────────────────────────
    if cfg["openrouter"]["api_key"]:
        try:
            result = openrouter.call(
                messages=messages,
                system_prompt=system_prompt,
                tool_definitions=tool_definitions,
                timeout=cfg["openrouter"]["timeout"],
            )
            logger.info(f"Model used: {result['model']} (final fallback)")
            return result
        except Exception as e:
            logger.error(f"OpenRouter also failed: {e}")

    raise ModelUnavailableError(
        "All AI providers failed. Check your API keys and network connectivity."
    )


def call_with_fallback_stream(
    messages: list[dict],
    system_prompt: str,
    tool_definitions: list,
):
    """
    Streaming version: Yields tokens from Gemini as they arrive.
    Falls back to non-streaming for Groq/OpenRouter (yields full response as single token).
    
    Yields: dict with "token", "done", or "error" keys
    """
    cfg = settings.AI_CONFIG

    # ── 1. Try Gemini with streaming ──────────────────────────────────────────
    if cfg["gemini"]["api_key"]:
        try:
            from services import gemini
            yield from gemini.call_stream(
                messages=messages,
                system_prompt=system_prompt,
                tool_definitions=tool_definitions,
                timeout=cfg["gemini"]["timeout"],
            )
            return
        except Exception as e:
            logger.warning(f"Gemini streaming failed ({type(e).__name__}: {e}) → falling back to non-streaming")

    # ── 2. Fall back to non-streaming (yield full response as single token) ───
    try:
        result = call_with_fallback(
            messages=messages,
            system_prompt=system_prompt,
            tool_definitions=tool_definitions,
        )
        if result.get("text"):
            yield {"token": result["text"]}
        yield {"done": True, "model": result.get("model", "unknown")}
    except Exception as e:
        yield {"error": str(e)}
