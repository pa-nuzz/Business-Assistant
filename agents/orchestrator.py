"""
Orchestrator — replaces the flat agent loop.

Uses Model Abstraction Layer for intelligent AI routing with caching, memory, and fallbacks.
"""

from dataclasses import dataclass
from typing import Literal
import logging
import json
from services.model_layer import (
    call_model, call_model_stream, 
    TaskType, Priority, 
    add_user_memory,
    intent_to_task_type
)
from mcp.tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

QueryIntent = Literal["chat", "search", "document", "analytics", "memory"]

@dataclass
class ExecutionPlan:
    intent: QueryIntent
    tool_calls: list[dict]
    needs_streaming: bool
    context_summary: str

@dataclass
class OrchestratorResult:
    text: str
    model: str
    tools_used: list[str]
    intent: QueryIntent
    iterations: int
    cached: bool = False


def classify_intent(user_message: str) -> QueryIntent:
    """Fast heuristic intent classification."""
    msg = user_message.lower().strip()

    search_signals = ["search", "find out", "latest", "current", "news",
                      "competitor", "market", "trend", "research", "what is"]
    doc_signals    = ["document", "pdf", "file", "upload", "summary of",
                      "in my docs", "contract", "report", "spreadsheet"]
    analytics_signals = ["revenue", "metrics", "kpi", "dashboard", "how much",
                          "how many", "growth", "performance", "sales", "profit"]
    memory_signals = ["remember", "you know that", "i told you", "last time",
                      "my preference", "as i mentioned"]

    if any(s in msg for s in doc_signals):    return "document"
    if any(s in msg for s in analytics_signals): return "analytics"
    if any(s in msg for s in search_signals):  return "search"
    if any(s in msg for s in memory_signals):  return "memory"
    return "chat"


def build_plan(intent: QueryIntent, user_message: str, user_id: int,
               conversation_history: list[dict], system_prompt: str) -> ExecutionPlan:
    """Build execution plan using Model Abstraction Layer."""
    planner_prompt = f"""
You are a planning agent. Given a user query, output a JSON execution plan.

User query: {user_message}
Detected intent: {intent}
User ID (inject into every tool that needs it): {user_id}

Respond ONLY with valid JSON:
{{
  "tool_calls": [{{"name": "<tool_name>", "args": {{"key": "value"}}, "reason": "<why>"}}],
  "context_summary": "<one sentence about what this query needs>"
}}

Available tools: {json.dumps([t["name"] for t in TOOL_DEFINITIONS])}

Rules:
- Always include user_id={user_id} in args for any tool that accepts user_id
- For analytics: always call get_business_profile + get_revenue_data
- For document: call list_documents first, then search_documents
- Maximum 4 tool calls per plan
"""

    try:
        result = call_model(
            user_id=user_id,
            user_message=planner_prompt,
            base_system_prompt="You are a JSON-only planning agent. Output valid JSON only.",
            task_type=TaskType.QUICK,
            priority=Priority.NORMAL,
            use_cache=False,
            store_memory=False,
        )
        
        text = result.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        
        tool_calls = parsed.get("tool_calls", [])
        for tc in tool_calls:
            if "user_id" in tc.get("args", {}):
                tc["args"]["user_id"] = user_id

        return ExecutionPlan(
            intent=intent,
            tool_calls=tool_calls,
            needs_streaming=True,
            context_summary=parsed.get("context_summary", ""),
        )
    except Exception as e:
        logger.warning(f"Planner failed ({e}), using empty plan")
        return ExecutionPlan(intent=intent, tool_calls=[], needs_streaming=True, context_summary="")


def execute_plan(plan: ExecutionPlan, user_id: int) -> list[dict]:
    """Execute tool calls in the plan."""
    results = []
    for tc in plan.tool_calls:
        tool_name = tc["name"]
        tool_args = tc.get("args", {})
        
        PROTECTED = {"get_business_profile", "get_revenue_data", "get_conversation_insights",
                    "update_business_metrics", "get_followup_items", "get_user_memory",
                    "save_memory", "list_documents", "get_document_summary", "search_documents"}
        if tool_name in PROTECTED:
            tool_args["user_id"] = user_id

        result = execute_tool(tool_name, tool_args)
        formatted = f"[{tool_name} result]\n{json.dumps(result.get('result', ''), indent=2, default=str)}" if "error" not in result else f"[{tool_name} error: {result['error']}]"
        results.append({"tool": tool_name, "result": formatted})
        logger.info(f"Tool executed: {tool_name}")

    return results


def run(user_message: str, user_id: int, conversation_history: list[dict], user_name: str = None):
    """Non-streaming entry point."""
    from agents.prompts import get_system_prompt
    system_prompt = get_system_prompt(user_name)

    intent = classify_intent(user_message)
    task_type = intent_to_task_type(intent)
    
    # Store personal info
    if any(x in user_message.lower() for x in ["i am", "i work", "my company", "my business"]):
        add_user_memory(user_id, f"User: {user_message[:150]}")
    
    plan = build_plan(intent, user_message, user_id, conversation_history, system_prompt)
    tool_results = execute_plan(plan, user_id)
    
    context_block = "\n\n".join(r["result"] for r in tool_results) if tool_results else ""
    synthesis_message = f"{user_message}\n\n[Context]\n{context_block}\n\nAnswer directly." if context_block else user_message

    try:
        priority = Priority.HIGH if intent in ["analytics", "document"] else Priority.NORMAL
        
        result = call_model(
            user_id=user_id,
            user_message=synthesis_message,
            base_system_prompt=system_prompt,
            task_type=task_type,
            priority=priority,
            use_cache=True,
            store_memory=False,
        )
        
        return OrchestratorResult(
            text=result.text or "No response.",
            model=result.model_used,
            tools_used=[r["tool"] for r in tool_results],
            intent=intent,
            iterations=2 if tool_results else 1,
            cached=result.cached,
        )
    except Exception as e:
        logger.exception("Synthesis failed")
        return OrchestratorResult(
            text=f"AI services temporarily unavailable. Please try again. ({e})",
            model="error",
            tools_used=[],
            intent=intent,
            iterations=1,
            cached=False,
        )


def run_stream(user_message: str, user_id: int, conversation_history: list[dict], user_name: str = None):
    """Streaming entry point."""
    import json as _json
    from agents.prompts import get_system_prompt
    system_prompt = get_system_prompt(user_name)

    intent = classify_intent(user_message)
    task_type = intent_to_task_type(intent)
    
    if any(x in user_message.lower() for x in ["i am", "i work", "my company", "my business"]):
        add_user_memory(user_id, f"User: {user_message[:150]}")
    
    plan = build_plan(intent, user_message, user_id, conversation_history, system_prompt)
    tool_results = execute_plan(plan, user_id)
    
    meta = {"metadata": {"intent": intent, "tools_used": [r["tool"] for r in tool_results], "plan_summary": plan.context_summary}}
    yield f"data: {_json.dumps(meta)}\n\n"

    context_block = "\n\n".join(r["result"] for r in tool_results) if tool_results else ""
    synthesis_message = f"{user_message}\n\n[Context]\n{context_block}\n\nAnswer directly." if context_block else user_message

    try:
        for token in call_model_stream(
            user_id=user_id,
            user_message=synthesis_message,
            base_system_prompt=system_prompt,
            task_type=task_type,
        ):
            yield f"data: {_json.dumps({'token': token})}\n\n"
    except Exception as e:
        logger.exception("Streaming failed")
        yield f"data: {_json.dumps({'error': str(e)})}\n\n"

    yield "data: [DONE]\n\n"
