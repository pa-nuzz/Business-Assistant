# OpenRouter — backup AI provider. Uses any model including free ones.
import json
import logging
import httpx
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def call(
    messages: list[dict],
    system_prompt: str,
    tool_definitions: list,
    timeout: Optional[int] = None,
) -> dict:
    # Regular HTTP call to OpenRouter. Returns text + tool calls.
    cfg = settings.AI_CONFIG["openrouter"]
    timeout = timeout or cfg["timeout"]

    or_messages = [{"role": "system", "content": system_prompt}] + messages

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
        "messages": or_messages,
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
                "HTTP-Referer": "https://localhost:3000",  # required by OpenRouter
                "X-Title": "Business Assistant",
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
        "model": f"openrouter/{cfg['model']}",
        "stop_reason": "tool_use" if tool_calls else "end_turn",
    }


def call_openrouter(system_prompt: str, user_message: str) -> str:
    # Simple wrapper - no tools, just text
    messages = [{"role": "user", "content": user_message}]
    result = call(messages, system_prompt, [])
    return result.get("text", "")


def call_openrouter_stream(system_prompt: str, user_message: str):
    # Stream tokens from OpenRouter
    cfg = settings.AI_CONFIG["openrouter"]
    timeout = cfg["timeout"]
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2048,
        "stream": True,
    }
    
    with httpx.Client(timeout=timeout) as client:
        with client.stream(
            "POST",
            f"{cfg['base_url']}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "HTTP-Referer": "https://localhost:3000",
                "X-Title": "Business Assistant",
                "Content-Type": "application/json",
            },
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk["choices"][0]["delta"].get("content"):
                            yield chunk["choices"][0]["delta"]["content"]
                    except:
                        pass
