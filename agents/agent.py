"""
Agent Loop — The core of the system.

Flow:
  user_message
    → build context (messages + system prompt)
    → call model (with tools)
    → if model wants tools → execute → feed result back → call model again
    → repeat until model gives final text answer (or max iterations)
    → return final response + metadata

This is an agentic loop, not a single call. The model decides when to stop.
Max iterations guard against runaway tool chains.
"""
import logging
from typing import Optional
from django.conf import settings

from agents import prompts
from agents.router import call_with_fallback, call_with_fallback_stream, ModelUnavailableError
from mcp.tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)


class AgentResponse:
    """Clean response object from agent."""
    def __init__(self, text: str, model: str, tool_calls_made: list, iterations: int):
        self.text = text
        self.model = model
        self.tool_calls_made = tool_calls_made  # list of tool names used
        self.iterations = iterations


def run(
    user_message: str,
    user_id: int,
    conversation_history: list[dict],
    user_name: Optional[str] = None,
) -> AgentResponse:
    """
    Run the agent loop for a single user turn.

    Args:
        user_message: The new message from the user
        user_id: Authenticated user's ID (injected into tool args automatically)
        conversation_history: Previous messages in [{role, content}] format
        user_name: Optional user display name for personalization

    Returns:
        AgentResponse with final text + metadata
    """
    max_iterations = settings.AI_CONFIG["max_tool_iterations"]
    system_prompt = prompts.get_system_prompt(user_name)

    # Build the working message list
    # We inject user_id into the system context so tools can use it
    system_with_context = (
        f"{system_prompt}\n\n"
        f"## Session Context\n"
        f"Current user_id: {user_id}\n"
        f"Always pass user_id={user_id} to tools that require it."
    )

    # Append the new user message to history
    messages = conversation_history + [{"role": "user", "content": user_message}]

    tool_calls_made = []
    model_used = None
    iterations = 0

    # ─── Agent Loop ───────────────────────────────────────────────────────────
    while iterations < max_iterations:
        iterations += 1
        logger.debug(f"Agent iteration {iterations}/{max_iterations}")

        try:
            response = call_with_fallback(
                messages=messages,
                system_prompt=system_with_context,
                tool_definitions=TOOL_DEFINITIONS,
            )
        except ModelUnavailableError as e:
            return AgentResponse(
                text=f"I'm temporarily unable to process your request. Please try again in a moment. ({str(e)})",
                model="none",
                tool_calls_made=tool_calls_made,
                iterations=iterations,
            )

        model_used = response["model"]

        # ── Model gave a final text answer — we're done ─────────────────────
        if response["stop_reason"] == "end_turn" or not response.get("tool_calls"):
            final_text = response.get("text") or "I wasn't able to generate a response. Please try rephrasing."
            logger.info(
                f"Agent done in {iterations} iterations | model={model_used} | "
                f"tools_used={tool_calls_made}"
            )
            return AgentResponse(
                text=final_text,
                model=model_used,
                tool_calls_made=tool_calls_made,
                iterations=iterations,
            )

        # ── Model wants to use tools ─────────────────────────────────────────
        tool_calls = response["tool_calls"]
        logger.debug(f"Tool calls requested: {[tc['name'] for tc in tool_calls]}")

        # Add assistant's tool-calling message to history
        messages.append({
            "role": "assistant",
            "content": response.get("text") or "",
            "_tool_calls": tool_calls,  # for our own tracking
        })

        # Execute each tool and collect results
        tool_results_text = []
        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc.get("args", {})

            # Security: inject user_id from session, not from model
            # This prevents the model from accessing other users' data
            if "user_id" in TOOL_DEFINITIONS_REQUIRING_AUTH and tool_name in TOOL_DEFINITIONS_REQUIRING_AUTH:
                tool_args["user_id"] = user_id

            result = execute_tool(tool_name, tool_args)
            tool_calls_made.append(tool_name)

            result_str = _format_tool_result(tool_name, result)
            tool_results_text.append(result_str)

        # Feed tool results back to model as a user-turn message
        combined_results = "\n\n".join(tool_results_text)
        messages.append({
            "role": "user",
            "content": f"[Tool Results]\n{combined_results}\n\nNow provide your final response based on these results.",
        })

    # ── Hit max iterations without a final answer ─────────────────────────────
    logger.warning(f"Agent hit max iterations ({max_iterations}) without finishing")
    return AgentResponse(
        text="I ran into a complex situation and couldn't complete the analysis. Please try a more specific question.",
        model=model_used or "unknown",
        tool_calls_made=tool_calls_made,
        iterations=iterations,
    )


def run_stream(
    user_message: str,
    user_id: int,
    conversation_history: list[dict],
    user_name: Optional[str] = None,
):
    """
    Run the agent loop for tool calls, then stream the final response.
    
    This runs the normal agent loop first to handle any tool calls.
    Once tool calls are complete, it streams the final response tokens.
    
    Yields: SSE-formatted strings "data: {...}\n\n"
    """
    import json
    from agents.router import call_with_fallback_stream
    
    max_iterations = settings.AI_CONFIG["max_tool_iterations"]
    system_prompt = prompts.get_system_prompt(user_name)
    
    system_with_context = (
        f"{system_prompt}\n\n"
        f"## Session Context\n"
        f"Current user_id: {user_id}\n"
        f"Always pass user_id={user_id} to tools that require it."
    )
    
    messages = conversation_history + [{"role": "user", "content": user_message}]
    
    tool_calls_made = []
    model_used = None
    iterations = 0
    
    # ─── Phase 1: Handle Tool Calls (non-streaming) ─────────────────────────────
    while iterations < max_iterations:
        iterations += 1
        logger.debug(f"Agent stream iteration {iterations}/{max_iterations}")
        
        try:
            response = call_with_fallback(
                messages=messages,
                system_prompt=system_with_context,
                tool_definitions=TOOL_DEFINITIONS,
            )
        except ModelUnavailableError as e:
            yield f'data: {{"error": "Model unavailable: {str(e)}"}}\n\n'
            yield 'data: [DONE]\n\n'
            return
        
        model_used = response["model"]
        
        # No tool calls - ready to stream final response
        if response["stop_reason"] == "end_turn" or not response.get("tool_calls"):
            final_messages = messages
            break
        
        # Handle tool calls
        tool_calls = response["tool_calls"]
        logger.debug(f"Tool calls requested: {[tc['name'] for tc in tool_calls]}")
        
        messages.append({
            "role": "assistant",
            "content": response.get("text") or "",
            "_tool_calls": tool_calls,
        })
        
        tool_results_text = []
        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc.get("args", {})
            
            if "user_id" in TOOL_DEFINITIONS_REQUIRING_AUTH and tool_name in TOOL_DEFINITIONS_REQUIRING_AUTH:
                tool_args["user_id"] = user_id
            
            result = execute_tool(tool_name, tool_args)
            tool_calls_made.append(tool_name)
            
            result_str = _format_tool_result(tool_name, result)
            tool_results_text.append(result_str)
        
        combined_results = "\n\n".join(tool_results_text)
        messages.append({
            "role": "user",
            "content": f"[Tool Results]\n{combined_results}\n\nNow provide your final response based on these results.",
        })
    else:
        # Max iterations hit
        yield f'data: {{"error": "Max iterations reached without final response"}}\n\n'
        yield 'data: [DONE]\n\n'
        return
    
    # ─── Phase 2: Stream Final Response ────────────────────────────────────────
    logger.info(f"Streaming final response | model={model_used} | tools_used={tool_calls_made}")
    
    # Send metadata first
    metadata = {
        "model": model_used,
        "tools_used": tool_calls_made,
        "iterations": iterations,
    }
    yield f'data: {json.dumps({"metadata": metadata})}\n\n'
    
    # Stream tokens
    try:
        for chunk in call_with_fallback_stream(
            messages=final_messages,
            system_prompt=system_with_context,
            tool_definitions=[],  # No tools for final streaming call
        ):
            if "token" in chunk:
                yield f'data: {json.dumps({"token": chunk["token"]})}\n\n'
            elif "error" in chunk:
                yield f'data: {json.dumps({"error": chunk["error"]})}\n\n'
                yield 'data: [DONE]\n\n'
                return
            elif "done" in chunk:
                break
    except Exception as e:
        logger.exception("Streaming failed")
        yield f'data: {json.dumps({"error": str(e)})}\n\n'
    
    yield 'data: [DONE]\n\n'


def _format_tool_result(tool_name: str, result: dict) -> str:
    """Format a tool result for injection back into the model context."""
    if "error" in result:
        return f"Tool `{tool_name}` returned an error: {result['error']}"
    return f"Tool `{tool_name}` result:\n{result.get('result', 'No data returned')}"


# Tools that require user_id to be enforced from session (not from model args)
# This is a security measure — model cannot override the user_id
TOOL_DEFINITIONS_REQUIRING_AUTH = {
    "get_business_profile",
    "get_revenue_data",
    "get_conversation_insights",
    "update_business_metrics",
    "get_followup_items",
    "get_user_memory",
    "save_memory",
    "list_documents",
    "get_document_summary",
    "search_documents",
}
