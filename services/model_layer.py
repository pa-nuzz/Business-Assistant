"""
Model Abstraction Layer - Clean routing with proper fallbacks.
Gemini (primary, best quality) → Groq (fast fallback) → OpenRouter (final fallback)
"""
import time
import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TaskType(Enum):
    CHAT = "chat"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    CODE = "code"
    QUICK = "quick"


class Priority(Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class ModelResponse:
    text: str
    model_used: str
    cached: bool = False
    latency_ms: float = 0.0


# ─── Simple in-memory cache ───────────────────────────────────────────────────
_cache: Dict[str, tuple] = {}
_CACHE_TTL = 300  # 5 minutes

# ─── User memory (in-memory, per session) ────────────────────────────────────
_user_memory: Dict[int, list] = {}
_MAX_MEMORIES = 15


def intent_to_task_type(intent: str) -> TaskType:
    mapping = {
        "chat": TaskType.CHAT,
        "search": TaskType.QUICK,
        "document": TaskType.ANALYSIS,
        "analytics": TaskType.ANALYSIS,
        "memory": TaskType.CHAT,
    }
    return mapping.get(intent, TaskType.CHAT)


def get_user_memory(user_id: int) -> str:
    memories = _user_memory.get(user_id, [])
    if not memories:
        return ""
    return "User context:\n" + "\n".join(f"- {m}" for m in memories[-5:])


def add_user_memory(user_id: int, memory: str):
    if user_id not in _user_memory:
        _user_memory[user_id] = []
    _user_memory[user_id].append(memory)
    _user_memory[user_id] = _user_memory[user_id][-_MAX_MEMORIES:]


def _cache_key(user_id: int, query: str, task: str) -> str:
    h = hashlib.md5(f"{task}:{query}".encode()).hexdigest()[:16]
    return f"{user_id}:{h}"


def _from_cache(user_id: int, query: str, task: str) -> Optional[ModelResponse]:
    key = _cache_key(user_id, query, task)
    if key in _cache:
        text, ts, model = _cache[key]
        if time.time() - ts < _CACHE_TTL:
            return ModelResponse(text=text, model_used=model, cached=True)
        del _cache[key]
    return None


def _to_cache(user_id: int, query: str, task: str, text: str, model: str):
    _cache[_cache_key(user_id, query, task)] = (text, time.time(), model)


def _build_prompt(base: str, user_id: int) -> str:
    mem = get_user_memory(user_id)
    return f"{base}\n\n{mem}" if mem else base


def call_model(
    user_id: int,
    user_message: str,
    base_system_prompt: str = "You are a helpful AI assistant.",
    task_type: TaskType = TaskType.CHAT,
    priority: Priority = Priority.NORMAL,
    use_cache: bool = True,
    store_memory: bool = False,
) -> ModelResponse:
    """
    Call AI with automatic fallback chain:
    Gemini → Groq → OpenRouter
    """
    start = time.time()

    if use_cache:
        cached = _from_cache(user_id, user_message, task_type.value)
        if cached:
            return cached

    system_prompt = _build_prompt(base_system_prompt, user_id)
    
    # Store explicit memory only when told to
    if store_memory and any(
        phrase in user_message.lower()
        for phrase in ["i am ", "i work at", "my company is", "my business is"]
    ):
        add_user_memory(user_id, user_message[:120])

    last_error = None

    # Try Gemini first
    try:
        from services.gemini import call_gemini
        text = call_gemini(system_prompt, user_message)
        if text:
            if use_cache:
                _to_cache(user_id, user_message, task_type.value, text, "gemini")
            return ModelResponse(
                text=text,
                model_used="gemini",
                latency_ms=(time.time() - start) * 1000
            )
    except Exception as e:
        logger.warning(f"Gemini failed, trying Groq: {e}")
        last_error = e

    # Try Groq second
    try:
        from services.groq_service import call_simple
        text = call_simple(system_prompt, user_message)
        if text:
            if use_cache:
                _to_cache(user_id, user_message, task_type.value, text, "groq")
            return ModelResponse(
                text=text,
                model_used="groq",
                latency_ms=(time.time() - start) * 1000
            )
    except Exception as e:
        logger.warning(f"Groq failed, trying OpenRouter: {e}")
        last_error = e

    # Try OpenRouter last
    try:
        from services.openrouter import call_openrouter
        text = call_openrouter(system_prompt, user_message)
        if text:
            return ModelResponse(
                text=text,
                model_used="openrouter",
                latency_ms=(time.time() - start) * 1000
            )
    except Exception as e:
        logger.error(f"All models failed: {e}")
        last_error = e

    raise Exception(f"All AI providers failed. Last error: {last_error}")


def call_model_stream(
    user_id: int,
    user_message: str,
    base_system_prompt: str = "You are a helpful AI assistant.",
    task_type: TaskType = TaskType.CHAT,
):
    """
    Streaming version. Tries Gemini first (streams), falls back to 
    Groq stream, then OpenRouter stream.
    Yields string tokens.
    """
    system_prompt = _build_prompt(base_system_prompt, user_id)

    # Try Gemini streaming first
    try:
        from services.gemini import call_gemini_stream
        yielded_anything = False
        for token in call_gemini_stream(system_prompt, user_message):
            yield token
            yielded_anything = True
        if yielded_anything:
            return
    except Exception as e:
        logger.warning(f"Gemini streaming failed, trying Groq: {e}")

    # Try Groq streaming
    try:
        from services.groq_service import call_stream as groq_stream
        messages = [{"role": "user", "content": user_message}]
        for token in groq_stream(messages, system_prompt, []):
            yield token
        return
    except Exception as e:
        logger.warning(f"Groq streaming failed, trying OpenRouter: {e}")

    # Try OpenRouter streaming
    try:
        from services.openrouter import call_openrouter_stream
        for token in call_openrouter_stream(system_prompt, user_message):
            yield token
        return
    except Exception as e:
        logger.error(f"All streaming providers failed: {e}")
        yield f"[Error: AI providers temporarily unavailable. Please try again.]"
