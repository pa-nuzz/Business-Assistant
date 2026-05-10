"""
Groq Service — Fallback AI model.
Groq is blazingly fast (LPU inference) and has a free tier.
Uses OpenAI-compatible API, so tool calling works the same way.
Free tier: check https://console.groq.com for current limits.
"""
import json
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

_groq_client = None


def _get_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        cfg = settings.AI_CONFIG["groq"]
        _groq_client = Groq(api_key=cfg["api_key"])
    return _groq_client


def call(
    messages: list[dict],
    system_prompt: str,
    tool_definitions: list,
    timeout: Optional[int] = None,
) -> dict:
    """
    Call Groq. Uses OpenAI-compatible format — clean and simple.
    Groq supports function calling natively.
    """
    cfg = settings.AI_CONFIG["groq"]
    timeout = timeout or cfg["timeout"]
    client = _get_client()

    # Build messages list with system prompt
    groq_messages = [{"role": "system", "content": system_prompt}] + messages

    # Convert tool definitions to OpenAI format
    tools = None
    if tool_definitions:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("parameters", {}),
                },
            }
            for t in tool_definitions
        ]

    # Build API parameters
    api_params = {
        "model": cfg["model"],
        "messages": groq_messages,
        "temperature": 0.3,
        "max_tokens": 2048,
        "timeout": timeout,
    }
    
    # Only include tools if they exist
    if tools:
        api_params["tools"] = tools
        api_params["tool_choice"] = "auto"
    
    response = client.chat.completions.create(**api_params)

    choice = response.choices[0]
    message = choice.message

    # Parse tool calls
    tool_calls = None
    if message.tool_calls:
        tool_calls = [
            {
                "name": tc.function.name,
                "args": json.loads(tc.function.arguments),
                "id": tc.id,
            }
            for tc in message.tool_calls
        ]

    return {
        "text": message.content,
        "tool_calls": tool_calls,
        "model": f"groq/{cfg['model']}",
        "stop_reason": "tool_use" if tool_calls else "end_turn",
    }


def call_stream(
    messages: list[dict],
    system_prompt: str,
    tool_definitions: list,
    timeout: int = None,
):
    """Streaming call using Groq. Yields token strings."""
    from groq import Groq, Stream
    cfg = settings.AI_CONFIG["groq"]
    client = _get_client()
    
    groq_messages = [{"role": "system", "content": system_prompt}] + messages
    timeout = timeout or cfg["timeout"]
    
    try:
        response = client.chat.completions.create(
            model=cfg["model"],
            messages=groq_messages,
            temperature=0.3,
            max_tokens=2048,
            timeout=timeout,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except Exception as e:
        logger.error(f"Groq streaming failed: {e}")
        raise


def call_simple(system_prompt: str, user_message: str) -> str:
    """Simple single-turn call returning text string."""
    messages = [{"role": "user", "content": user_message}]
    result = call(messages, system_prompt, [])
    return result.get("text", "") or ""
