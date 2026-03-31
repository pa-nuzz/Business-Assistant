"""
Model Abstraction Layer - Intelligent AI Routing
Routes tasks to optimal models with caching, memory, and fallback logic.
"""
import json
import hashlib
import time
from typing import Optional, Dict, Any, List
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum

from services.groq_service import call as call_groq, call as call_groq_stream
from services.gemini import call_gemini, call_gemini_stream
from services.openrouter import call_openrouter, call_openrouter_stream
from utils.logger import logger


class TaskType(Enum):
    CHAT = "chat"           # Fast, casual conversation
    ANALYSIS = "analysis"   # Deep reasoning, complex tasks  
    CREATIVE = "creative"   # Writing, brainstorming
    CODE = "code"           # Programming help
    QUICK = "quick"         # Simple Q&A, classification


class Priority(Enum):
    HIGH = "high"      # Use best model regardless of cost
    NORMAL = "normal"  # Balance quality/cost
    LOW = "low"        # Use cheapest/fastest


def intent_to_task_type(intent: str) -> TaskType:
    """Map intent string to task type for model selection."""
    mapping = {
        "chat": TaskType.CHAT,
        "search": TaskType.QUICK,
        "document": TaskType.ANALYSIS,
        "analytics": TaskType.ANALYSIS,
        "memory": TaskType.CHAT,
    }
    return mapping.get(intent, TaskType.CHAT)


@dataclass
class ModelResponse:
    text: str
    model_used: str
    cached: bool = False
    tokens_used: int = 0
    latency_ms: float = 0.0


# Response cache: (user_id, query_hash) -> (response, timestamp, model)
_response_cache: Dict[str, tuple] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes

# User memory store: user_id -> List[memory strings]
_user_memory: Dict[int, List[str]] = {}
_MAX_MEMORY_ITEMS = 20


def _get_cache_key(user_id: int, query: str, task_type: str) -> str:
    """Generate cache key from user + query hash."""
    query_hash = hashlib.md5(f"{task_type}:{query}".encode()).hexdigest()[:16]
    return f"{user_id}:{query_hash}"


def _get_from_cache(user_id: int, query: str, task_type: str) -> Optional[ModelResponse]:
    """Try to get cached response."""
    key = _get_cache_key(user_id, query, task_type)
    if key in _response_cache:
        response, timestamp, model = _response_cache[key]
        if time.time() - timestamp < _CACHE_TTL_SECONDS:
            logger.info(f"Cache hit for user {user_id}")
            return ModelResponse(text=response, model_used=model, cached=True)
        else:
            del _response_cache[key]
    return None


def _save_to_cache(user_id: int, query: str, task_type: str, response: str, model: str):
    """Save response to cache."""
    key = _get_cache_key(user_id, query, task_type)
    _response_cache[key] = (response, time.time(), model)


def get_user_memory(user_id: int) -> str:
    """Get formatted memory context for user."""
    memories = _user_memory.get(user_id, [])
    if not memories:
        return ""
    return "\n".join([f"- {m}" for m in memories[-5:]])  # Last 5 memories


def add_user_memory(user_id: int, memory: str):
    """Add a memory item for user."""
    if user_id not in _user_memory:
        _user_memory[user_id] = []
    _user_memory[user_id].append(memory)
    # Keep only recent memories
    _user_memory[user_id] = _user_memory[user_id][-_MAX_MEMORY_ITEMS:]
    logger.info(f"Added memory for user {user_id}: {memory[:50]}...")


def _build_system_prompt(base_prompt: str, user_id: int, task_type: TaskType) -> str:
    """Build system prompt with user memory and context."""
    memory_context = get_user_memory(user_id)
    
    parts = [base_prompt]
    
    if memory_context:
        parts.append(f"\n\nUser context from previous conversations:\n{memory_context}")
    
    if task_type == TaskType.ANALYSIS:
        parts.append("\n\nThink step by step. Provide thorough, well-reasoned responses.")
    elif task_type == TaskType.CREATIVE:
        parts.append("\n\nBe creative and engaging. Use vivid language.")
    elif task_type == TaskType.CODE:
        parts.append("\n\nProvide clean, well-commented code with explanations.")
    
    return "\n".join(parts)


def _select_model(task_type: TaskType, priority: Priority) -> tuple:
    """
    Select optimal model based on task type and priority.
    Returns: (primary_model, fallback_models)
    """
    # GROQ is primary - fast, cheap, reliable
    # Gemini is secondary - smarter for complex tasks
    # OpenRouter is tertiary - backup
    
    if priority == Priority.HIGH:
        # Use best available
        if task_type in (TaskType.ANALYSIS, TaskType.CREATIVE):
            return ("gemini", ["groq", "openrouter"])
        return ("groq", ["gemini", "openrouter"])
    
    elif priority == Priority.LOW:
        # Use cheapest/fastest
        return ("groq", ["openrouter"])
    
    else:  # NORMAL
        if task_type == TaskType.QUICK:
            return ("groq", ["openrouter"])
        elif task_type in (TaskType.CHAT, TaskType.CODE):
            return ("groq", ["gemini"])
        else:  # ANALYSIS, CREATIVE
            return ("gemini", ["groq", "openrouter"])


def _call_model(model: str, system_prompt: str, user_message: str, stream: bool = False):
    """Call specific model with unified interface."""
    start_time = time.time()
    
    try:
        if model == "groq":
            if stream:
                return call_groq_stream(system_prompt, user_message)
            # call() requires messages, system_prompt, tool_definitions
            messages = [{"role": "user", "content": user_message}]
            result = call_groq(messages, system_prompt, [])
            return result.get("text", ""), "groq"
        
        elif model == "gemini":
            if stream:
                return call_gemini_stream(system_prompt, user_message)
            return call_gemini(system_prompt, user_message), "gemini"
        
        elif model == "openrouter":
            if stream:
                return call_openrouter_stream(system_prompt, user_message)
            return call_openrouter(system_prompt, user_message), "openrouter"
        
        else:
            raise ValueError(f"Unknown model: {model}")
    
    except Exception as e:
        logger.error(f"Model {model} failed: {e}")
        latency = (time.time() - start_time) * 1000
        raise


def call_model(
    user_id: int,
    user_message: str,
    base_system_prompt: str = "You are a helpful AI assistant.",
    task_type: TaskType = TaskType.CHAT,
    priority: Priority = Priority.NORMAL,
    use_cache: bool = True,
    stream: bool = False,
    store_memory: bool = True
) -> ModelResponse:
    """
    Main entry point - intelligent model routing with caching and fallbacks.
    
    Args:
        user_id: User ID for personalization
        user_message: The user's query
        base_system_prompt: Base instructions for the AI
        task_type: Type of task for model selection
        priority: Priority level for quality/cost tradeoff
        use_cache: Whether to check/use cache
        stream: Whether to stream response
        store_memory: Whether to extract and store memories
    
    Returns:
        ModelResponse with text, model used, cache status, etc.
    """
    start_time = time.time()
    
    # Check cache first
    if use_cache and not stream:
        cached = _get_from_cache(user_id, user_message, task_type.value)
        if cached:
            return cached
    
    # Build enhanced prompt with user memory
    system_prompt = _build_system_prompt(base_system_prompt, user_id, task_type)
    
    # Select models to try
    primary, fallbacks = _select_model(task_type, priority)
    models_to_try = [primary] + fallbacks
    
    # Try models in order
    last_error = None
    for model in models_to_try:
        try:
            logger.info(f"Trying model {model} for user {user_id}, task={task_type.value}")
            
            if stream and model == models_to_try[0]:
                # For streaming, only try primary (fallbacks don't stream well)
                return _call_model(model, system_prompt, user_message, stream=True)
            
            response_text, model_used = _call_model(model, system_prompt, user_message, stream=False)
            
            latency = (time.time() - start_time) * 1000
            
            # Cache successful response
            if use_cache:
                _save_to_cache(user_id, user_message, task_type.value, response_text, model_used)
            
            # Extract memory if enabled (simple approach: store key facts)
            if store_memory and len(user_message) > 20:
                # Simple heuristic: store user preferences/statements about themselves
                if "I am" in user_message or "I work" in user_message or "my" in user_message.lower():
                    add_user_memory(user_id, f"User said: {user_message[:100]}")
            
            return ModelResponse(
                text=response_text,
                model_used=model_used,
                cached=False,
                tokens_used=len(response_text.split()),  # Rough estimate
                latency_ms=latency
            )
            
        except Exception as e:
            logger.warning(f"Model {model} failed: {e}")
            last_error = e
            continue  # Try next fallback
    
    # All models failed
    logger.error(f"All models failed for user {user_id}: {last_error}")
    raise Exception(f"All AI providers failed. Last error: {last_error}")


def call_model_stream(
    user_id: int,
    user_message: str,
    base_system_prompt: str = "You are a helpful AI assistant.",
    task_type: TaskType = TaskType.CHAT,
    priority: Priority = Priority.NORMAL
):
    """
    Streaming version - returns generator of tokens.
    Uses Groq for speed, with fallback to non-streaming if needed.
    """
    system_prompt = _build_system_prompt(base_system_prompt, user_id, task_type)
    
    # For streaming, always use Groq (fastest)
    # If it fails, we'll handle in the view
    return call_groq_stream(system_prompt, user_message)


# Convenience wrappers
def quick_chat(user_id: int, message: str, context: str = "") -> str:
    """Fast chat response (Groq)."""
    result = call_model(
        user_id=user_id,
        user_message=message,
        base_system_prompt=context or "You are a helpful assistant.",
        task_type=TaskType.QUICK,
        priority=Priority.LOW
    )
    return result.text


def deep_analysis(user_id: int, message: str, context: str = "") -> str:
    """Deep analysis response (Gemini/Groq)."""
    result = call_model(
        user_id=user_id,
        user_message=message,
        base_system_prompt=context or "You are an expert analyst. Think step by step.",
        task_type=TaskType.ANALYSIS,
        priority=Priority.HIGH
    )
    return result.text
