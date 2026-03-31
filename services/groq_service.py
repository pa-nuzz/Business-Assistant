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

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=groq_messages,
        tools=tools,
        tool_choice="auto" if tools else None,
        temperature=0.3,
        max_tokens=2048,
        timeout=timeout,
    )

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
