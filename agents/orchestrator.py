"""
Enhanced Orchestrator — True Agent Architecture with Multi-Step Reasoning

Intelligent business assistant that:
1. Plans multi-step reasoning chains
2. Remembers context across conversations
3. Auto-extracts business insights
4. Self-corrects when tools fail
5. Provides actionable recommendations
"""

from dataclasses import dataclass, field
from typing import Literal, Dict, List, Optional, Any
import logging
import json
import re
from datetime import datetime

from services.model_layer import (
    call_model, call_model_stream, 
    TaskType, Priority, 
    add_user_memory, get_user_memory,
    intent_to_task_type
)
from mcp.tools import TOOL_DEFINITIONS, execute_tool
from django.core.cache import cache

logger = logging.getLogger(__name__)

QueryIntent = Literal["chat", "search", "document", "analytics", "memory", "action", "task"]

@dataclass
class ExecutionPlan:
    intent: QueryIntent
    tool_calls: List[Dict]
    reasoning_chain: List[str] = field(default_factory=list)
    context_summary: str = ""
    expected_outcome: str = ""

@dataclass
class OrchestratorResult:
    text: str
    model: str
    tools_used: List[str]
    intent: QueryIntent
    reasoning_chain: List[str]
    confidence: float = 0.0
    cached: bool = False
    memory_stored: bool = False

def _get_cached_context(user_id: int) -> Dict:
    """Get or initialize user context from Redis cache."""
    cache_key = f"user_ctx_{user_id}"
    context = cache.get(cache_key)
    if context is None:
        context = {
            "last_topics": [],
            "frequent_queries": [],
            "business_insights": [],
            "conversation_count": 0,
            "last_active": None
        }
        cache.set(cache_key, context, timeout=300)
    return context

def _update_context(user_id: int, query: str, intent: str, tools_used: List[str]):
    """Update user context with new interaction."""
    cache_key = f"user_ctx_{user_id}"
    ctx = _get_cached_context(user_id)
    ctx["conversation_count"] += 1
    ctx["last_active"] = datetime.now().isoformat()
    
    # Track topics
    if intent not in ctx["last_topics"]:
        ctx["last_topics"].insert(0, intent)
        ctx["last_topics"] = ctx["last_topics"][:5]  # Keep last 5
    
    # Track frequent query patterns
    keywords = _extract_keywords(query)
    ctx["frequent_queries"].insert(0, {"query": query, "keywords": keywords, "intent": intent})
    ctx["frequent_queries"] = ctx["frequent_queries"][:10]
    
    # Save back to cache
    cache.set(cache_key, ctx, timeout=300)

def _extract_keywords(text: str) -> List[str]:
    """Extract business-relevant keywords from text."""
    business_terms = {
        "revenue", "sales", "profit", "growth", "customer", "client",
        "marketing", "strategy", "budget", "forecast", "kpi", "metrics",
        "document", "contract", "invoice", "report", "analysis",
        "competitor", "market", "product", "service", "team", "hiring"
    }
    words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
    return list(words & business_terms)

def classify_intent_advanced(user_message: str, user_id: int) -> QueryIntent:
    """
    Advanced intent classification with context awareness.
    Uses both keyword matching and context from previous interactions.
    """
    msg = user_message.lower().strip()
    ctx = _get_cached_context(user_id)
    
    # Direct intent signals
    signals = {
        "document": ["document", "pdf", "file", "upload", "summary of", "in my docs", 
                     "contract", "report", "spreadsheet", "cv", "resume", "what does my", 
                     "read my", "analyze my"],
        "analytics": ["revenue", "metrics", "kpi", "dashboard", "how much", "how many",
                      "growth", "performance", "sales", "profit", "numbers", "statistics",
                      "calculate", "compare", "trend"],
        "search": ["search", "find out", "latest", "current", "news", "competitor",
                   "market", "trend", "research", "what is", "who is", "where is",
                   "lookup", "information about"],
        "memory": ["remember", "you know that", "i told you", "last time", "my preference",
                   "as i mentioned", "earlier", "previously", "what did i say"],
        "task": ["create task", "add task", "new task", "make a task", "to-do", "todo",
                 "task for", "remind me to", "schedule", "plan to", "need to", "should I",
                 "mark complete", "finish task", "done with", "task done", "my tasks",
                 "what tasks", "show tasks", "list tasks", "prioritize", "organize tasks",
                 "task priority", "assign task", "due date", "deadline"],
        "action": ["create", "update", "delete", "save", "schedule", "remind me",
                   "add to", "remove from", "set up", "configure"]
    }
    
    # Check for direct signals
    for intent, keywords in signals.items():
        if any(kw in msg for kw in keywords):
            return intent if intent != "action" else "action"
    
    # Context-based inference
    if ctx["last_topics"]:
        last_topic = ctx["last_topics"][0]
        followup_indicators = ["and", "also", "what about", "how about", "can you", 
                              "tell me more", "explain"]
        if any(ind in msg for ind in followup_indicators):
            return last_topic
    
    return "chat"

def build_intelligent_plan(intent: QueryIntent, user_message: str, user_id: int,
                           conversation_history: List[Dict]) -> ExecutionPlan:
    """Build an execution plan using rule-based logic (no AI call)."""
    
    tool_calls = []
    reasoning_chain = []
    
    if intent == "document":
        tool_calls = [
            {"name": "list_documents", "args": {"user_id": user_id}, "reason": "Check available documents"},
            {"name": "search_documents", "args": {"query": user_message, "user_id": user_id}, "reason": "Search in documents"}
        ]
        reasoning_chain = ["User asked about documents", "List available docs and search within them"]
    
    elif intent == "analytics":
        tool_calls = [
            {"name": "get_business_profile", "args": {"user_id": user_id}, "reason": "Get business context"},
            {"name": "get_revenue_data", "args": {"user_id": user_id}, "reason": "Get financial data"},
            {"name": "get_conversation_insights", "args": {"user_id": user_id, "limit": 20}, "reason": "Get conversation patterns"}
        ]
        reasoning_chain = ["User asked for analytics/metrics", "Fetch business profile, revenue, and conversation insights"]
    
    elif intent == "search":
        tool_calls = [
            {"name": "brave_search", "args": {"query": user_message, "num_results": 5}, "reason": "Search web for current info"}
        ]
        reasoning_chain = ["User requested web search", "Execute brave search with the query"]
    
    elif intent == "task":
        # Check if this is a task creation request vs just querying tasks
        creation_signals = ["create", "add", "new", "make", "remind", "schedule", "plan to", "need to", "should"]
        is_creating = any(sig in user_message.lower() for sig in creation_signals)
        
        if is_creating:
            # Auto-extract and create tasks from the message
            tool_calls = [
                {"name": "suggest_tasks_from_context", "args": {"text": user_message, "user_id": user_id, "source_type": "chat"}, "reason": "Extract actionable tasks from user message"},
                {"name": "list_tasks", "args": {"user_id": user_id, "limit": 5, "status": "todo"}, "reason": "Show updated task list"}
            ]
            reasoning_chain = ["User wants to create a task", "Extract tasks from their message", "Show updated task list"]
        else:
            # Just querying existing tasks
            tool_calls = [
                {"name": "list_tasks", "args": {"user_id": user_id, "limit": 10}, "reason": "Check recent tasks"},
                {"name": "get_task_insights", "args": {"user_id": user_id}, "reason": "Get task productivity insights"}
            ]
            reasoning_chain = ["User asked about tasks", "List tasks and get productivity insights"]
    
    elif intent == "memory":
        tool_calls = [
            {"name": "get_user_memory", "args": {"user_id": user_id}, "reason": "Retrieve user memory/context"},
            {"name": "get_followup_items", "args": {"user_id": user_id}, "reason": "Check for follow-up items"}
        ]
        reasoning_chain = ["User referenced previous context", "Fetch user memory and follow-ups"]
    
    elif intent == "chat":
        tool_calls = [
            {"name": "get_business_profile", "args": {"user_id": user_id}, "reason": "Get business context for personalization"},
            {"name": "get_user_memory", "args": {"user_id": user_id}, "reason": "Get user context for continuity"}
        ]
        reasoning_chain = ["General chat question", "Load business profile and user memory for context"]
    
    else:
        # Fallback for any other intent
        tool_calls = [
            {"name": "get_business_profile", "args": {"user_id": user_id}, "reason": "Get basic context"}
        ]
        reasoning_chain = ["Unclear intent, using minimal context"]
    
    return ExecutionPlan(
        intent=intent,
        tool_calls=tool_calls,
        reasoning_chain=reasoning_chain,
        context_summary=f"Rule-based plan for intent: {intent}",
        expected_outcome="Relevant data for response synthesis"
    )

def execute_intelligent_plan(plan: ExecutionPlan, user_id: int) -> List[Dict]:
    """Execute plan with self-correction and result enrichment."""
    from utils.security import enforce_user_id
    results = []
    
    for tc in plan.tool_calls:
        tool_name = tc["name"]
        tool_args = tc.get("args", {})
        reason = tc.get("reason", "No reason provided")
        
        # Sanitize tool args to enforce correct user_id
        tool_args = enforce_user_id(tool_name, tool_args, user_id)
        
        max_retries = 2
        result = None
        error = None
        
        for attempt in range(max_retries):
            try:
                result = execute_tool(tool_name, tool_args)
                if "error" not in result:
                    break
                error = result.get("error")
            except Exception as e:
                error = str(e)
                logger.warning(f"Tool {tool_name} attempt {attempt + 1} failed: {e}")
        
        if result and "error" not in result:
            formatted = _format_tool_result(tool_name, result)
        else:
            formatted = f"[{tool_name} failed: {error or 'Unknown error'}]"
        
        results.append({
            "tool": tool_name, 
            "result": formatted,
            "reason": reason,
            "success": "error" not in (result or {})
        })
        
        logger.info(f"Tool executed: {tool_name}")
    
    return results

def _format_tool_result(tool_name: str, result: Dict) -> str:
    """Format tool result with smart context injection."""
    data = result.get("result", result)
    
    if tool_name == "search_documents":
        if isinstance(data, str) and "No relevant" in data:
            return f"[{tool_name}] No matching documents found."
        return f"[{tool_name}] Found in your documents:\n{json.dumps(data, indent=2, default=str)}"
    
    elif tool_name == "get_business_profile":
        return f"[{tool_name}] Business context:\n{json.dumps(data, indent=2, default=str)}"
    
    elif tool_name == "brave_search":
        return f"[{tool_name}] Web search results:\n{json.dumps(data, indent=2, default=str)}"
    
    else:
        return f"[{tool_name} result]\n{json.dumps(data, indent=2, default=str)}"

def synthesize_response(user_message: str, plan: ExecutionPlan, tool_results: List[Dict], 
                       user_id: int, user_name: Optional[str]) -> str:
    """Synthesize a comprehensive, intelligent response."""
    from agents.prompts import get_system_prompt
    
    system_prompt = get_system_prompt(user_name)
    
    # --- Extract user context from already-fetched tool_results ---
    user_context_parts = []
    
    # Get business profile from tool_results
    profile_result = next((r for r in tool_results if r.get("tool") == "get_business_profile"), None)
    if profile_result and profile_result.get("success", False):
        user_context_parts.append(f"[Business Profile]\n{profile_result['result']}")
    
    # Get user memory from tool_results
    memory_result = next((r for r in tool_results if r.get("tool") == "get_user_memory"), None)
    if memory_result and memory_result.get("success", False):
        user_context_parts.append(f"[User Memory]\n{memory_result['result']}")
    
    # Get documents list from tool_results (for document intent)
    if plan.intent == "document":
        docs_result = next((r for r in tool_results if r.get("tool") == "list_documents"), None)
        if docs_result and docs_result.get("success", False):
            user_context_parts.append(f"[Available Documents]\n{docs_result['result']}")
    
    user_context_block = "\n\n".join(user_context_parts) if user_context_parts else ""
    
    successful_results = [r for r in tool_results if r.get("success", True)]
    failed_results = [r for r in tool_results if not r.get("success", True)]
    
    context_parts = [r["result"] for r in successful_results]
    context_block = "\n\n".join(context_parts) if context_parts else ""
    
    failure_note = ""
    if failed_results:
        failure_note = f"\n\nNote: Some data sources were unavailable ({len(failed_results)} tools failed)."
    
    # Build synthesis prompt with user context at the top
    user_context_section = f"""
User Context (the user's background and what they have):
{user_context_block}

""" if user_context_block else ""
    
    synthesis_prompt = f"""The user asked: "{user_message}"

{user_context_section}Here's what I found from tools:
{context_block}
{failure_note}

Instructions for AEIOU AI:
1. Respond conversationally, like a helpful colleague
2. Reference specific data points naturally in your response (document titles, numbers, company name)
3. Be concise - 2-4 sentences max for simple questions
4. Don't use numbered lists or structured formats unless asked
5. If the user just created a task or document, acknowledge it
6. Answer their specific question directly
7. No generic "action steps" or "best practices" advice
8. USE the User Context above - reference their company name, documents, and history
9. CRITICAL - DO NOT HALLUCINATE:
   - If a tool result is empty or missing, say "I don't have that information" or "I don't see any [tasks/documents/data] for you yet"
   - Never make up numbers, dates, or facts that aren't in the tool results
   - Never reference documents or tasks that don't appear in the tool results
   - If you need to search for something not found, say "I couldn't find that - would you like me to search differently?"
10. If the data shows "No [items] found", clearly state that rather than being vague

Just give a natural, helpful response:"""

    try:
        result = call_model(
            user_id=user_id,
            user_message=synthesis_prompt,
            base_system_prompt=system_prompt,
            task_type=TaskType.ANALYSIS,
            priority=Priority.HIGH,
            use_cache=True,
            store_memory=True,
        )
        return result.text or "I couldn't process that request."
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return "I'm having trouble processing your request. Please try again."

def run_intelligent(user_message: str, user_id: int, conversation_history: List[Dict], 
                   user_name: str = None) -> OrchestratorResult:
    """Main entry point for intelligent orchestration."""
    _update_context(user_id, user_message, "", [])
    
    intent = classify_intent_advanced(user_message, user_id)
    _update_context(user_id, user_message, intent, [])
    
    plan = build_intelligent_plan(intent, user_message, user_id, conversation_history)
    
    tool_results = execute_intelligent_plan(plan, user_id)
    tools_used = [r["tool"] for r in tool_results if r.get("success", False)]
    
    response_text = synthesize_response(
        user_message, plan, tool_results, user_id, user_name
    )
    
    memory_stored = False
    if intent in ["analytics", "document", "action", "task"]:
        add_user_memory(
            user_id,
            f"User asked about {intent}: {user_message[:100]}... Response used tools: {', '.join(tools_used)}"
        )
        memory_stored = True
    
    return OrchestratorResult(
        text=response_text,
        model="intelligent_orchestrator",
        tools_used=tools_used,
        intent=intent,
        reasoning_chain=plan.reasoning_chain,
        confidence=len(tools_used) / max(len(plan.tool_calls), 1),
        memory_stored=memory_stored
    )

def run_stream_intelligent(user_message: str, user_id: int, conversation_history: List[Dict], 
                          user_name: str = None, conversation_id: str = None):
    """Streaming version of intelligent orchestration."""
    import json as _json
    
    _update_context(user_id, user_message, "", [])
    intent = classify_intent_advanced(user_message, user_id)
    plan = build_intelligent_plan(intent, user_message, user_id, conversation_history)
    
    meta = {
        "metadata": {
            "intent": intent,
            "reasoning_chain": plan.reasoning_chain,
            "expected_outcome": plan.expected_outcome,
            "conversation_id": conversation_id
        }
    }
    yield f"data: {_json.dumps(meta)}\n\n"
    
    tool_results = execute_intelligent_plan(plan, user_id)
    tools_used = [r["tool"] for r in tool_results if r.get("success", False)]
    
    tools_meta = {"tools_used": tools_used}
    yield f"data: {_json.dumps(tools_meta)}\n\n"
    
    context_parts = [r["result"] for r in tool_results]
    context_block = "\n\n".join(context_parts)
    
    synthesis_message = f"""Original question: {user_message}

Reasoning: {chr(10).join(plan.reasoning_chain)}

Data: {context_block}

Provide a helpful, actionable response:"""

    try:
        for token in call_model_stream(
            user_id=user_id,
            user_message=synthesis_message,
            base_system_prompt="You are an intelligent business assistant. Be specific and actionable.",
            task_type=TaskType.ANALYSIS,
        ):
            yield f"data: {_json.dumps({'token': token})}\n\n"
    except Exception as e:
        logger.exception("Streaming synthesis failed")
        yield f"data: {_json.dumps({'error': str(e)})}\n\n"
    
    yield "data: [DONE]\n\n"

# Backwards compatibility
run = run_intelligent
run_stream = run_stream_intelligent
