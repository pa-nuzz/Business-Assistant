"""
Model Abstraction Layer - Clean routing with proper fallbacks.
NVIDIA (powerful primary) → Groq (fast fallback) → OpenRouter (final fallback)
"""
import time
import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Any, List
import re
from django.conf import settings
from django.core.cache import cache

def _build_prompt(base: str, user_id: int) -> str:
    mem = get_user_memory(user_id)
    return f"{base}\n\n{mem}" if mem else base


from utils.text import extract_keywords as _extract_keywords

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
    text: Optional[str]
    model_used: str
    tool_calls: Optional[List[Dict]] = None
    usage: Optional[Dict] = None
    finish_reason: str = "stop"
    cached: bool = False
    latency_ms: float = 0.0
    
    def dict(self):
        return {
            "text": self.text,
            "model_used": self.model_used,
            "tool_calls": self.tool_calls,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "cached": self.cached,
            "latency_ms": self.latency_ms,
        }


# ─── Cache TTL ─────────────────────────────────────────────────────────────────
_CACHE_TTL = 300  # 5 minutes
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
    cache_key = f"user_mem_{user_id}"
    memories = cache.get(cache_key) or []
    if not memories:
        try:
            from core.models import UserMemory
            memories = [
                f"{m.category}: {m.value}"
                for m in UserMemory.objects.filter(user_id=user_id).order_by("-updated_at")[:10]
            ]
            if memories:
                cache.set(cache_key, memories[-_MAX_MEMORIES:], timeout=_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Failed to load persistent user memory: {e}")
    if not memories:
        return ""
    return "User context:\n" + "\n".join(f"- {m}" for m in memories[-5:])


def add_user_memory(user_id: int, memory: str = "", key: str = None, category: str = "fact", value: str = None):
    """
    Store memory for a user. Supports both simple list-based cache
    and structured persistent storage.
    """
    if key or value:
        from core.models import UserMemory
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
            UserMemory.objects.update_or_create(
                user=user,
                key=key or hashlib.md5(memory.encode()).hexdigest()[:16],
                defaults={
                    "value": value or memory,
                    "category": category
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store structured memory: {e}")

    # Always update the fast-access cache
    cache_key = f"user_mem_{user_id}"
    memories = cache.get(cache_key) or []
    mem_text = memory or value or ""
    if mem_text:
        memories.append(mem_text)
        memories = memories[-_MAX_MEMORIES:]
        cache.set(cache_key, memories, timeout=_CACHE_TTL)


def _cache_key(user_id: int, query: str, task: str) -> str:
    h = hashlib.md5(f"{task}:{query}".encode()).hexdigest()[:16]
    return f"model_layer_{user_id}_{h}"


def _from_cache(user_id: int, query: str, task: str) -> Optional[ModelResponse]:
    key = _cache_key(user_id, query, task)
    cached = cache.get(key)
    if cached:
        text, ts, model = cached
        if time.time() - ts < _CACHE_TTL:
            return ModelResponse(text=text, model_used=model, cached=True)
        cache.delete(key)
    return None


def _to_cache(user_id: int, query: str, task: str, text: str, model: str):
    cache.set(_cache_key(user_id, query, task), (text, time.time(), model), timeout=_CACHE_TTL)


def extract_and_store_memory(user_id: int, user_message: str, ai_response: str) -> bool:
    """
    Extract important facts from conversation and store as memory.
    Uses AI to identify what should be remembered.
    """
    try:
        # Skip short or trivial messages
        if len(user_message) < 10:
            return False
            
        # Skip common greetings and social chatter
        trivial_patterns = [
            r'^\s*(hi|hello|hey|bye|goodbye|thanks|thank you|ok|okay|cool|nice)\s*$',
            r'^\s*how are you\s*$',
        ]
        for pattern in trivial_patterns:
            if re.search(pattern, user_message.lower()):
                return False
        
        # Memory extraction prompt
        extraction_prompt = f"""Analyze this conversation and extract ONLY important facts that should be remembered for future context.

User: {user_message}
AI: {ai_response}

Extract facts ONLY if they contain:
- Personal/business preferences ("I prefer...", "We use...")
- Important decisions made
- Goals or objectives stated
- Key business info (company name, industry, size)
- Work habits or patterns
- Rejections or negative preferences ("I don't like...", "Never...")

Return EXACTLY in this format:
MEMORY: <the fact to remember>
OR
NONE

Be concise. One sentence max per memory."""

        result = call_model(
            user_id=user_id,
            user_message=extraction_prompt,
            base_system_prompt="You are a memory extraction system. Only extract genuinely important facts.",
            task_type=TaskType.ANALYSIS,
            priority=Priority.NORMAL,
            use_cache=False,
            store_memory=False
        )
        
        extracted = result.text.strip()
        
        if extracted.upper().startswith("MEMORY:"):
            memory_text = extracted[7:].strip().strip('"').strip("'")
            if memory_text and len(memory_text) > 5:
                add_user_memory(user_id, memory_text)
                logger.info(f"Memory stored for user {user_id}: {memory_text[:80]}...")
                return True
        
        return False
        
    except Exception as e:
        logger.warning(f"Memory extraction failed: {e}")
        return False


def get_enhanced_user_memory(user_id: int) -> Dict[str, Any]:
    """
    Get comprehensive user memory including raw memories and derived insights.
    """
    raw_memories = get_user_memory(user_id)
    
    # Get cached context too
    from agents.orchestrator import _get_cached_context
    context = _get_cached_context(user_id)
    
    return {
        "raw_memory": raw_memories,
        "conversation_count": context.get("conversation_count", 0),
        "last_topics": context.get("last_topics", []),
        "frequent_keywords": _extract_keywords(raw_memories) if raw_memories else []
    }


def _get_context_brief(user_id: int) -> str:
    """
    Synthesizes a rich context brief from workspace memory, 
    business profile, and conversation history.
    """
    from core.services.workspace_service import WorkspaceService
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(id=user_id)
        ws = WorkspaceService(user)
        # Default workspace_id is usually 'personal' or 'default'
        # Check if we have any workspace, otherwise use default
        ctx = ws.get_workspace_context("default")
        
        brief = ["--- WORKSPACE CONTEXT ---"]

        # 1. Business Context from workspace and canonical business profile
        bc = (ctx or {}).get("business_context", {})
        try:
            profile = user.business_profile
            profile_context = {
                "company_name": profile.company_name,
                "industry": profile.industry,
                "company_size": profile.company_size,
                "description": profile.description,
                "goals": profile.goals or [],
                "key_metrics": profile.key_metrics or {},
            }
            bc = {**profile_context, **bc}
        except Exception:
            pass

        if bc:
            brief.append(f"Profile: {bc.get('company_name', 'Business')} | Industry: {bc.get('industry', 'N/A')}")
            if bc.get('description'): brief.append(f"Mission: {bc['description'][:300]}")
            if bc.get("company_size"): brief.append(f"Company size: {bc['company_size']}")
            if bc.get("goals"): brief.append(f"Goals: {bc['goals'][:3]}")
            if bc.get("key_metrics"): brief.append(f"Metrics: {bc['key_metrics']}")
            
        # 2. Recent Memories from workspace and persistent user memory
        mems = (ctx or {}).get("recent_memories", [])
        if mems:
            brief.append("\nLearned Facts:")
            for m in mems[-5:]:
                brief.append(f"- {m.get('content', '')}")
        persistent_memory = get_user_memory(user_id)
        if persistent_memory:
            brief.append(f"\n{persistent_memory}")
                
        # 3. Conversation Summaries
        history = (ctx or {}).get("conversation_history", [])
        if history:
            brief.append("\nPrevious Interactions:")
            for s in history[-2:]:
                brief.append(f"- {s.get('summary', '')}")
                
        # 4. Open Tasks
        from core.models import Task
        open_tasks = Task.objects.filter(user=user).exclude(status__in=["done", "archived"]).order_by("due_date", "-priority")[:5]
        if open_tasks.exists():
            brief.append("\nCurrent Open Tasks:")
            for t in open_tasks:
                due = f" (Due: {t.due_date.strftime('%Y-%m-%d')})" if t.due_date else ""
                brief.append(f"- [{t.status}] {t.title} [Priority: {t.priority}]{due}")
                
        brief.append("--- END CONTEXT ---")
        return "\n".join(brief)
    except Exception as e:
        logger.warning(f"Failed to build context brief: {e}")
        return ""


def call_model(
    user_id: int,
    user_message: str,
    base_system_prompt: str = "You are a helpful AI assistant.",
    task_type: TaskType = TaskType.CHAT,
    priority: Priority = Priority.NORMAL,
    use_cache: bool = True,
    store_memory: bool = False,
    conversation_history: List[Dict] = None,
    tool_definitions: List[Dict] = None,
) -> ModelResponse:
    """
    Advanced Model Entry Point.
    Handles semantic context injection, provider fallbacks, and agentic tool use.
    """
    start = time.time()

    # 1. Synthesize Context
    context_brief = _get_context_brief(user_id)
    system_prompt = f"{base_system_prompt}\n\n{context_brief}".strip()
    
    # 2. Prepare Messages
    messages = conversation_history or []
    if not any(m["content"] == user_message for m in messages):
        messages.append({"role": "user", "content": user_message})

    # 3. Cache Check
    if use_cache:
        cached = _from_cache(user_id, user_message, task_type.value)
        if cached:
            return cached

    # 4. Try Providers (NVIDIA → Groq → OpenRouter).
    # Gemini chat is optional because some projects return quota=0 while embeddings work.
    last_error = None
    
    if settings.AI_CONFIG["gemini"].get("chat_enabled"):
        try:
            from services.gemini import call as gemini_call
            resp = gemini_call(messages, system_prompt, tool_definitions)
            if resp:
                model_res = ModelResponse(
                    text=resp.get("text"),
                    tool_calls=resp.get("tool_calls"),
                    model_used=resp.get("model", "gemini"),
                    finish_reason=resp.get("stop_reason", "stop"),
                    latency_ms=(time.time() - start) * 1000
                )
                if use_cache:
                    _to_cache(user_id, user_message, task_type.value, model_res.text or "", model_res.model_used)
                return model_res
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
            last_error = e

    # NVIDIA NIM (Powerful Hosted LLM Fallback)
    try:
        from services.nvidia import call as nvidia_call
        resp = nvidia_call(messages, system_prompt, tool_definitions)
        if resp:
            return ModelResponse(
                text=resp.get("text"),
                tool_calls=resp.get("tool_calls"),
                model_used=resp.get("model", "nvidia"),
                finish_reason=resp.get("stop_reason", "stop"),
                latency_ms=(time.time() - start) * 1000
            )
    except Exception as e:
        logger.warning(f"NVIDIA failed: {e}")
        last_error = e

    # Groq (Fast Fallback)
    try:
        from services.groq_service import call as groq_call
        resp = groq_call(messages, system_prompt, tool_definitions)
        if resp:
            model_res = ModelResponse(
                text=resp.get("text"),
                tool_calls=resp.get("tool_calls"),
                model_used=resp.get("model", "groq"),
                finish_reason=resp.get("stop_reason", "stop"),
                latency_ms=(time.time() - start) * 1000
            )
            return model_res
    except Exception as e:
        logger.warning(f"Groq failed: {e}")
        last_error = e

    # OpenRouter (Safety Net)
    try:
        from services.openrouter import call as or_call
        resp = or_call(messages, system_prompt, tool_definitions)
        if resp:
            return ModelResponse(
                text=resp.get("text"),
                tool_calls=resp.get("tool_calls"),
                model_used=resp.get("model", "openrouter"),
                latency_ms=(time.time() - start) * 1000
            )
    except Exception as e:
        logger.error(f"All providers failed: {e}")
        last_error = e

    raise Exception(f"All AI providers failed. Last error: {last_error}")


def call_model_stream(
    user_id: int,
    user_message: str,
    base_system_prompt: str = "You are a helpful AI assistant.",
    task_type: TaskType = TaskType.CHAT,
):
    """
    Streaming version. Consistently uses _get_context_brief for semantic memory.
    Tries Gemini first (streams), falls back to Groq stream, then OpenRouter stream.
    Yields string tokens.
    """
    # 1. Emit Thinking Steps based on task
    context_brief = _get_context_brief(user_id)
    system_prompt = f"{base_system_prompt}\n\n{context_brief}".strip()

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


def handle_tool_error(user_id: int, tool_name: str, error: str, original_call: Dict) -> Optional[ModelResponse]:
    """
    Self-healing tool mechanism. If a tool call fails, ask the AI to correct it.
    """
    logger.info(f"Self-healing triggered for {tool_name} due to: {error}")
    
    correction_prompt = f"""The previous tool call to '{tool_name}' failed with the following error:
Error: {error}
Original Arguments: {original_call.get('args') or original_call.get('function', {}).get('arguments')}

Please provide a corrected tool call with the right arguments. If you cannot fix it, explain why concisely."""

    try:
        return call_model(
            user_id=user_id,
            user_message=correction_prompt,
            base_system_prompt="You are a self-healing tool assistant. Correct the provided tool call based on the error.",
            task_type=TaskType.QUICK,
            priority=Priority.HIGH,
            use_cache=False
        )
    except Exception as e:
        logger.error(f"Self-healing failed: {e}")
        return None
