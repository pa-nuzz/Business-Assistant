"""NVIDIA NIM hosted LLM fallback.

The hosted NIM LLM endpoint is OpenAI-compatible, so this mirrors the
OpenRouter/Groq request shape while using NVIDIA's model catalog.
"""
import json
import logging
from typing import Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def call(
    messages: list[dict],
    system_prompt: str,
    tool_definitions: list,
    timeout: Optional[int] = None,
) -> dict:
    cfg = settings.AI_CONFIG["nvidia"]
    if not cfg["api_key"]:
        raise ValueError("NVIDIA_API_KEY is not configured")

    timeout = timeout or cfg["timeout"]
    nvidia_messages = [{"role": "system", "content": system_prompt}] + messages

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

    payload = {
        "model": cfg["model"],
        "messages": nvidia_messages,
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(
            f"{cfg['base_url']}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    choice = data["choices"][0]
    message = choice["message"]

    tool_calls = None
    if message.get("tool_calls"):
        tool_calls = [
            {
                "name": tc["function"]["name"],
                "args": json.loads(tc["function"]["arguments"]),
                "id": tc["id"],
            }
            for tc in message["tool_calls"]
        ]

    return {
        "text": message.get("content"),
        "tool_calls": tool_calls,
        "model": f"nvidia/{cfg['model']}",
        "stop_reason": "tool_use" if tool_calls else "end_turn",
    }


def call_nvidia(system_prompt: str, user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]
    result = call(messages, system_prompt, [])
    return result.get("text", "") or ""
