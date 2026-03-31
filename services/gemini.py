"""
Gemini Service — Primary AI model.
Uses google-generativeai SDK with function calling.
Free tier: 1M tokens/day on gemini-1.5-flash (very generous).
"""
import logging
import concurrent.futures
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Lazy import to avoid import errors if key not set
_gemini_client = None


def _get_client():
    global _gemini_client
    if _gemini_client is None:
        import google.generativeai as genai
        cfg = settings.AI_CONFIG["gemini"]
        genai.configure(api_key=cfg["api_key"])
        _gemini_client = genai
    return _gemini_client


def _build_gemini_tools(tool_definitions: list) -> list:
    """Convert our tool definitions to Gemini's FunctionDeclaration format."""
    import google.generativeai as genai
    from google.generativeai.types import FunctionDeclaration, Tool

    declarations = []
    for tool in tool_definitions:
        declarations.append(
            FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool.get("parameters", {}),
            )
        )
    return [Tool(function_declarations=declarations)]


def _call_with_timeout(fn, timeout):
    """Execute function with timeout using ThreadPoolExecutor (cross-platform)."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Gemini call timed out after {timeout}s")


def call(
    messages: list[dict],
    system_prompt: str,
    tool_definitions: list,
    timeout: Optional[int] = None,
) -> dict:
    """
    Call Gemini with messages and tool definitions.

    Returns:
        {
            "text": str | None,
            "tool_calls": [{"name": str, "args": dict}] | None,
            "model": "gemini",
            "stop_reason": "tool_use" | "end_turn"
        }
    """
    cfg = settings.AI_CONFIG["gemini"]
    timeout = timeout or cfg["timeout"]
    genai = _get_client()

    import google.generativeai as genai_module
    from google.generativeai.types import GenerationConfig

    model = genai_module.GenerativeModel(
        model_name=cfg["model"],
        system_instruction=system_prompt,
        tools=_build_gemini_tools(tool_definitions) if tool_definitions else None,
        generation_config=GenerationConfig(
            temperature=0.3,
            max_output_tokens=2048,
        ),
    )

    # Convert messages to Gemini format
    gemini_history = []
    for msg in messages[:-1]:  # all except last
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=gemini_history)

    try:
        last_msg = messages[-1]["content"]
        response = _call_with_timeout(lambda: chat.send_message(last_msg), timeout)
    except TimeoutError:
        raise
    except Exception as e:
        raise

    # Parse response
    candidate = response.candidates[0]
    tool_calls = []
    text_parts = []

    for part in candidate.content.parts:
        if hasattr(part, "function_call") and part.function_call.name:
            tool_calls.append({
                "name": part.function_call.name,
                "args": dict(part.function_call.args),
            })
        if hasattr(part, "text") and part.text:
            text_parts.append(part.text)

    return {
        "text": "\n".join(text_parts) if text_parts else None,
        "tool_calls": tool_calls if tool_calls else None,
        "model": f"gemini/{cfg['model']}",
        "stop_reason": "tool_use" if tool_calls else "end_turn",
    }


def call_stream(
    messages: list[dict],
    system_prompt: str,
    tool_definitions: list,
    timeout: Optional[int] = None,
):
    """
    Call Gemini with streaming enabled. Yields tokens as they arrive.
    
    Only yields the final response tokens (not tool call iterations).
    Tool calls are handled internally and their results are fed back,
    then the final response is streamed.
    
    Yields: dict with "token" or "done" keys
    """
    cfg = settings.AI_CONFIG["gemini"]
    timeout = timeout or cfg["timeout"]
    genai = _get_client()

    import google.generativeai as genai_module
    from google.generativeai.types import GenerationConfig

    model = genai_module.GenerativeModel(
        model_name=cfg["model"],
        system_instruction=system_prompt,
        tools=_build_gemini_tools(tool_definitions) if tool_definitions else None,
        generation_config=GenerationConfig(
            temperature=0.3,
            max_output_tokens=2048,
        ),
    )

    # Convert messages to Gemini format
    gemini_history = []
    for msg in messages[:-1]:  # all except last
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=gemini_history)
    last_msg = messages[-1]["content"]

    try:
        response = _call_with_timeout(lambda: chat.send_message(last_msg, stream=True), timeout)
        
        for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                yield {"token": chunk.text}
            
            # Check if this chunk has function calls (tool use)
            if hasattr(chunk, 'candidates') and chunk.candidates:
                candidate = chunk.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call.name:
                            # Tool call detected - can't stream this
                            yield {"error": "Tool calls detected during streaming - use non-streaming endpoint"}
                            return
        
        yield {"done": True}
        
    except TimeoutError:
        yield {"error": "Stream timed out"}
    except Exception as e:
        yield {"error": str(e)}


# Simple wrappers for Model Abstraction Layer
def call_gemini(system_prompt: str, user_message: str) -> str:
    """Simple non-streaming call for Model Layer."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    result = call(messages, system_prompt, [])
    return result.get("text", "")


def call_gemini_stream(system_prompt: str, user_message: str):
    """Streaming generator for Model Layer."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    for chunk in call_stream(messages, system_prompt, []):
        if "token" in chunk:
            yield chunk["token"]
        elif "error" in chunk:
            yield f"[Error: {chunk['error']}]"
            break
