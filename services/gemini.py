# Gemini - main AI. Free tier gives 1M tokens/day which is plenty.
import logging
import concurrent.futures
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Don't import until we actually need it - avoids crashes if API key missing
_gemini_client = None


def _get_client():
    global _gemini_client
    if _gemini_client is None:
        import google.generativeai as genai
        _gemini_client = genai
    return _gemini_client


def _get_api_keys() -> list[str]:
    cfg = settings.AI_CONFIG["gemini"]
    keys = []
    if cfg.get("api_keys"):
        keys.extend(k.strip() for k in cfg["api_keys"].split(","))
    keys.extend([
        cfg.get("api_key", ""),
        cfg.get("api_key1", ""),
        cfg.get("api_key2", ""),
        cfg.get("api_key3", ""),
        cfg.get("api_key4", ""),
        cfg.get("api_keys1", ""),
        cfg.get("api_keys2", ""),
        cfg.get("api_keys3", ""),
        cfg.get("api_keys4", ""),
    ])
    return list(dict.fromkeys(k for k in keys if k))


def _configure_key(genai, api_key: str) -> None:
    genai.configure(api_key=api_key)


def _build_gemini_tools(tool_definitions: list) -> list:
    # Gemini has its own format for tools - convert here
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
    # Kill the call if it hangs - Gemini can be slow sometimes
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
    # Main call to Gemini. Returns text + any tool calls the model wants to make
    cfg = settings.AI_CONFIG["gemini"]
    timeout = timeout or cfg["timeout"]
    genai = _get_client()

    import google.generativeai as genai_module
    from google.generativeai.types import GenerationConfig
    api_keys = _get_api_keys()
    if not api_keys:
        raise ValueError("GEMINI_API_KEY is not configured")

    last_error = None
    for api_key in api_keys:
        try:
            _configure_key(genai, api_key)
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
            response = _call_with_timeout(lambda: chat.send_message(last_msg), timeout)
            break
        except TimeoutError:
            raise
        except Exception as e:
            last_error = e
    else:
        raise last_error

    # Pull out text + any tool calls from the response
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
    # Stream tokens as they come in. Note: tool calls break streaming.
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
    messages = [{"role": "user", "content": user_message}]
    result = call(messages, system_prompt, [])
    return result.get("text", "") or ""


def call_gemini_stream(system_prompt: str, user_message: str):
    """Streaming generator for Model Layer. Yields token strings."""
    messages = [{"role": "user", "content": user_message}]
    for chunk in call_stream(messages, system_prompt, []):
        if "token" in chunk:
            yield chunk["token"]
        elif "error" in chunk:
            logger.error(f"Gemini stream error: {chunk['error']}")
            break

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Get vector embeddings for a list of texts using Gemini's embedding model.
    """
    genai = _get_client()
    cfg = settings.AI_CONFIG["gemini"]
    api_keys = _get_api_keys()
    if not api_keys:
        logger.error("Gemini embedding failed: GEMINI_API_KEY is not configured")
        return []

    last_error = None
    for api_key in api_keys:
        _configure_key(genai, api_key)
        try:
            result = genai.embed_content(
                model=cfg["embedding_model"],
                content=texts,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            last_error = e
    try:
        raise last_error
    except Exception as e:
        logger.error(f"Gemini embedding failed: {e}")
    return []

def call_vision(
    image_data: bytes,
    mime_type: str,
    prompt: str,
    system_prompt: str = "You are a business intelligence assistant specialized in visual analysis. Analyze charts, diagrams, and document visuals for strategic insights."
) -> str:
    """
    Analyze an image or document visual using Gemini 1.5 Flash Vision.
    """
    genai = _get_client()
    import google.generativeai as genai_module
    from google.generativeai.types import GenerationConfig

    model = genai_module.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
        generation_config=GenerationConfig(
            temperature=0.2,
            max_output_tokens=1024,
        ),
    )

    try:
        response = _call_with_timeout(
            lambda: model.generate_content([
                {"mime_type": mime_type, "data": image_data},
                prompt
            ]),
            timeout=30
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Vision call failed: {e}")
        return f"Visual analysis unavailable: {str(e)}"
