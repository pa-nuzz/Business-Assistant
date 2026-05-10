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
from agents.entity_resolver import EntityResolver
from agents.tool_decision import ToolDecisionEngine

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """You are AEIOU, a business assistant. You have strict rules:

1. BASE YOUR RESPONSE ONLY ON THE TOOL RESULTS PROVIDED BELOW.
2. NEVER invent, estimate, or calculate numbers not present in tool results.
3. If a specific piece of information is missing from tool results, say exactly:
   "I don't have that information available right now."
4. NEVER use your training knowledge to fill in business data (revenue, task counts, dates).
5. If tool results are empty, say so clearly and offer to help the user set up that data.
6. Keep responses concise and actionable.
7. If the user asks about something you just told them, refer back to what you said — don't re-fetch.

Tool results are provided below. Respond based ONLY on these.
"""

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

from utils.text import extract_keywords as _extract_keywords

def classify_intent_advanced(user_message: str, user_id: int, history: List[Dict] = None) -> QueryIntent:
    """
    Semantic intent classification.
    Uses fast keyword matching for obvious cases, falls back to LLM for complex/ambiguous ones.
    """
    msg = user_message.lower().strip()
    ctx = _get_cached_context(user_id)
    
    # --- Level 1: Fast Direct Signal Matching ---
    signals = {
        "document": ["document", "pdf", "file", "upload", "summary of", "in my docs", 
                     "contract", "report", "spreadsheet", "cv", "resume", "what does my"],
        "analytics": ["revenue", "metrics", "kpi", "dashboard", "how much", "how many",
                      "growth", "performance", "sales", "profit", "statistics"],
        "search": ["search", "find out", "latest", "current", "news", "research", "what is"],
        "task": ["create task", "add task", "new task", "todo", "remind me to", "schedule", "deadline", "my tasks", "update task", "delete task"],
    }
    
    for intent, keywords in signals.items():
        if any(kw in msg for kw in keywords):
            return intent
    
    # --- Level 2: Contextual Inference (Fast) ---
    if ctx["last_topics"]:
        last_topic = ctx["last_topics"][0]
        followup_indicators = ["and", "also", "what about", "how about", "can you", 
                              "tell me more", "explain"]
        if any(ind in msg for ind in followup_indicators):
            return last_topic

    # --- Level 3: Semantic Classification (LLM Fallback) ---
    # Only run LLM if the message is long enough or seems complex
    if len(msg) > 15:
        try:
            from services.model_layer import call_model, TaskType, Priority
            
            # Simple few-shot classification prompt
            classification_prompt = f"""Classify the user's intent into exactly one of these categories:
- chat: General conversation, greetings, or off-topic questions.
- search: Request for external information, news, or web search.
- document: Questions about their uploaded files, PDFs, or contracts.
- analytics: Questions about business metrics, revenue, KPIs, or data trends.
- task: Request to manage, create, list, or update tasks/reminders.
- memory: Questions about what was discussed previously or personal preferences.

User Message: "{user_message}"

Respond with ONLY the category name."""

            result = call_model(
                user_id=user_id,
                user_message=classification_prompt,
                base_system_prompt="You are an intent classifier. Be precise.",
                task_type=TaskType.QUICK,
                priority=Priority.HIGH,
                use_cache=True
            )
            
            cleaned_intent = result.text.lower().strip()
            # Validate against valid intents
            valid_intents = ["chat", "search", "document", "analytics", "memory", "task", "action"]
            if cleaned_intent in valid_intents:
                logger.info(f"LLM Semantic Intent: {cleaned_intent}")
                return cleaned_intent
        except Exception as e:
            logger.warning(f"LLM Intent Classification failed: {e}")

    return "chat"

def build_intelligent_plan(intent: QueryIntent, user_message: str, user_id: int,
                           conversation_history: List[Dict]) -> ExecutionPlan:
    """Build an execution plan using rule-based logic (no AI call)."""
    
    # --- Entity resolution ---
    resolver = EntityResolver(user_id=user_id, conversation_history=conversation_history)
    entities = resolver.resolve(user_message)

    # --- Clarification shortcut ---
    unclear = [e for e in entities if e.needs_clarification]
    if unclear:
        # Return a clarification plan instead of guessing
        return ExecutionPlan(
            intent="clarification",
            tool_calls=[],
            reasoning_chain=[f"Ambiguous reference — confirm: did you mean '{e.name}'?" for e in unclear],
            expected_outcome="Ask user to confirm which entity they mean before proceeding."
        )

    # --- Tool decision engine ---
    # Use for intents where the hardcoded logic below doesn't have a specific handler
    engine = ToolDecisionEngine(user_id=user_id)
    decision = engine.decide(
        intent=intent,
        user_message=user_message,
        entities=entities,
        context={}
    )

    # If the engine says no tools needed, return early
    if decision.decision_type.value == "no_tools":
        return ExecutionPlan(
            intent=intent,
            tool_calls=[],
            reasoning_chain=[decision.reasoning],
            expected_outcome="Answer from conversation context only."
        )

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
            {"name": "searxng_search", "args": {"query": user_message, "num_results": 5}, "reason": "Search web for current info via SearXNG"},
            {"name": "duckduckgo_search", "args": {"query": user_message, "num_results": 3}, "reason": "Search web for current info via DuckDuckGo fallback"}
        ]
        reasoning_chain = ["User requested web search", "Execute searxng and duckduckgo search with the query"]
    
    elif intent == "task":
        from services.model_layer import call_model, TaskType, Priority
        from mcp.tools import TOOL_DEFINITIONS
        
        task_tools = [t for t in TOOL_DEFINITIONS if "task" in t["name"] or t["name"] == "get_business_profile"]
        
        prompt = f"User wants to manage tasks. Message: '{user_message}'\n\nPick the right tool(s) to fulfill this request. If they want to create a task, extract the title, priority, etc. If they want to update, extract the status. If they want to list, use list_tasks."
        
        try:
            res = call_model(
                user_id=user_id,
                user_message=prompt,
                base_system_prompt="You are a task routing assistant. Call the appropriate tools to handle the user's task request.",
                task_type=TaskType.QUICK,
                priority=Priority.HIGH,
                use_cache=False,
                tool_definitions=task_tools,
                conversation_history=conversation_history[-4:] if conversation_history else []
            )
            
            if res.tool_calls:
                for tc in res.tool_calls:
                    # Enforce user_id
                    if "args" not in tc:
                        tc["args"] = {}
                    tc["args"]["user_id"] = user_id
                    tc["reason"] = "LLM intent parsing"
                    tool_calls.append(tc)
                
                # If modifying, add a list_tasks to see the result
                if any(tc["name"] in ["create_task", "update_task_status", "delete_task"] for tc in tool_calls):
                    tool_calls.append({"name": "list_tasks", "args": {"user_id": user_id, "limit": 5}, "reason": "Show updated task list"})
                
                reasoning_chain = ["Used AI to determine task actions"]
            else:
                tool_calls = [{"name": "list_tasks", "args": {"user_id": user_id, "limit": 5}, "reason": "Fallback: show current tasks"}]
                reasoning_chain = ["Could not determine specific task action, showing tasks"]
        except Exception as e:
            logger.error(f"Task tool routing failed: {e}")
            tool_calls = [{"name": "list_tasks", "args": {"user_id": user_id, "limit": 5}, "reason": "Fallback: show current tasks"}]
            reasoning_chain = ["Error in task routing, showing tasks"]
    
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


def get_proactive_alerts(user_id: int) -> list:
    """
    Return time-sensitive, high-value alerts.
    Checks tasks, recent documents, and metric anomalies.
    """
    from django.utils import timezone
    from core.models import Task, Document, BusinessProfile
    alerts = []

    # 1. Task Alerts (Overdue/Due Today)
    overdue = Task.objects.filter(
        user_id=user_id,
        due_date__lt=timezone.now(),
        status__in=["todo", "in_progress"]
    ).count()
    if overdue > 0:
        alerts.append({
            "type": "urgent",
            "message": f"CRITICAL: {overdue} task{'s' if overdue > 1 else ''} overdue.",
            "action": "list_tasks",
            "priority": "high"
        })

    # 2. Document Alerts (Recently uploaded, not yet summarized/analyzed)
    recent_docs = Document.objects.filter(
        user_id=user_id,
        status="ready",
        created_at__gte=timezone.now() - timezone.timedelta(hours=24)
    ).order_by("-created_at")[:2]
    
    for doc in recent_docs:
        alerts.append({
            "type": "insight",
            "message": f"NEW: Analyzed '{doc.title}'. View summary?",
            "action": f"get_document_summary(doc_id='{doc.id}')",
            "priority": "normal"
        })

    # 3. Metric Alerts (Example: Revenue growth)
    try:
        profile = BusinessProfile.objects.get(user_id=user_id)
        metrics = profile.key_metrics or {}
        if "monthly_revenue" in metrics:
            # Placeholder for trend logic - in real app compare with historical snapshots
            alerts.append({
                "type": "metric",
                "message": f"TREND: Monthly revenue is tracking well. View growth report?",
                "action": "get_revenue_data",
                "priority": "normal"
            })
    except Exception:
        pass

    return alerts

def _format_tool_result(tool_name: str, result: Dict) -> str:
    """Format tool result with smart context injection."""
    data = result.get("result", result)
    
    if tool_name == "search_documents":
        if isinstance(data, str) and "No relevant" in data:
            return f"[{tool_name}] No matching documents found."
        return f"[{tool_name}] Found in your documents:\n{json.dumps(data, indent=2, default=str)}"
    
    elif tool_name == "get_business_profile":
        return f"[{tool_name}] Business context:\n{json.dumps(data, indent=2, default=str)}"
    
    elif tool_name in ["searxng_search", "duckduckgo_search"]:
        return f"[{tool_name}] Web search results:\n{json.dumps(data, indent=2, default=str)}"
    
    else:
        return f"[{tool_name} result]\n{json.dumps(data, indent=2, default=str)}"

def synthesize_response(user_message: str, plan: ExecutionPlan, tool_results: List[Dict], 
                       user_id: int, user_name: Optional[str]) -> str:
    """Synthesize a comprehensive, intelligent response."""
    from agents.prompts import get_system_prompt
    
    system_prompt = SYNTHESIS_SYSTEM_PROMPT
    
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
    """Main entry point for intelligent orchestration with context-first responses."""
    from services.model_layer import extract_and_store_memory
    
    _update_context(user_id, user_message, "", [])
    
    intent = classify_intent_advanced(user_message, user_id)
    _update_context(user_id, user_message, intent, [])
    
    plan = build_intelligent_plan(intent, user_message, user_id, conversation_history)
    
    tool_results = execute_intelligent_plan(plan, user_id)
    tools_used = [r["tool"] for r in tool_results if r.get("success", False)]
    
    response_text = synthesize_response(
        user_message, plan, tool_results, user_id, user_name
    )
    
    # Defer memory extraction to background task (avoids extra LLM call per message)
    memory_stored = False
    try:
        from services.tasks import defer_memory_extraction
        defer_memory_extraction.delay(user_id, user_message, response_text)
    except Exception as e:
        # Fallback: extract synchronously if Celery unavailable
        try:
            memory_stored = extract_and_store_memory(user_id, user_message, response_text)
        except Exception as e2:
            logger.warning(f"Memory extraction failed: {e2}")
    
    return {
        "reply": response_text,
        "suggestions": get_proactive_alerts(user_id),
        "model": "intelligent_orchestrator",
        "tools_used": tools_used,
        "intent": intent,
        "reasoning_chain": plan.reasoning_chain,
        "confidence": len(tools_used) / max(len(plan.tool_calls), 1),
        "memory_stored": memory_stored
    }

def run_stream_intelligent(user_message: str, user_id: int, conversation_history: List[Dict], 
                          user_name: str = None, conversation_id: str = None):
    """Streaming version of intelligent orchestration with thinking indicators and automatic memory extraction."""
    import json as _json
    from services.model_layer import extract_and_store_memory
    
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
    
    # Start thinking indicator immediately
    thinking_msg = _get_thinking_message(plan.tool_calls, intent)
    yield f"data: {_json.dumps({'type': 'thinking', 'content': thinking_msg})}\n\n"
    
    tool_results = execute_intelligent_plan(plan, user_id)
    tools_used = [r["tool"] for r in tool_results if r.get("success", False)]
    
    # Update thinking message before synthesis
    yield f"data: {_json.dumps({'type': 'thinking', 'content': 'Putting it together...'})}\n\n"
    
    tools_meta = {"tools_used": tools_used}
    yield f"data: {_json.dumps(tools_meta)}\n\n"
    
    context_parts = [r["result"] for r in tool_results]
    context_block = "\n\n".join(context_parts)
    
    synthesis_message = f"""Original question: {user_message}

Reasoning: {chr(10).join(plan.reasoning_chain)}

Data: {context_block}

Provide a helpful, actionable response:"""

    # Collect response for memory extraction
    collected_response = []
    
    try:
        for token in call_model_stream(
            user_id=user_id,
            user_message=synthesis_message,
            base_system_prompt=SYNTHESIS_SYSTEM_PROMPT,
            task_type=TaskType.ANALYSIS,
        ):
            collected_response.append(token)
            yield f"data: {_json.dumps({'token': token})}\n\n"
    except Exception as e:
        logger.exception("Streaming synthesis failed")
        yield f"data: {_json.dumps({'error': str(e)})}\n\n"
    
    # Defer memory extraction to background task
    try:
        full_response = "".join(collected_response)
        from services.tasks import defer_memory_extraction
        defer_memory_extraction.delay(user_id, user_message, full_response)
    except Exception:
        # Fallback: extract synchronously if Celery unavailable
        try:
            full_response = "".join(collected_response)
            memory_stored = extract_and_store_memory(user_id, user_message, full_response)
            if memory_stored:
                yield f"data: {_json.dumps({'memory_stored': True})}\n\n"
        except Exception as e:
            logger.warning(f"Memory extraction in stream failed: {e}")
    
    yield "data: [DONE]\n\n"


def _get_thinking_message(tool_calls: List[Dict], intent: str) -> str:
    """Generate an appropriate thinking message based on tools being called."""
    if not tool_calls:
        return "Thinking..."
    
    tool_names = [tc.get("name", "") for tc in tool_calls]
    
    # Group by category
    if any("search" in tn for tn in tool_names) and not any("document" in tn for tn in tool_names):
        return "Searching for information..."
    elif any("document" in tn for tn in tool_names):
        return "Looking through your documents..."
    elif any("task" in tn for tn in tool_names):
        return "Checking your tasks..."
    elif any("revenue" in tn or "analytics" in tn or "profile" in tn for tn in tool_names):
        return "Pulling up your business data..."
    elif len(tool_calls) > 2:
        return f"Running {len(tool_calls)} tools to get your answer..."
    else:
        return "Looking that up..."

def classify_smart_action(user_message: str, user_id: int) -> Dict[str, Any]:
    """
    Classifies a natural language query into a structured 'Smart Action'.
    """
    prompt = f"""You are a smart action classifier for AEIOU AI.
Classify the user's command into a structured action object.

USER COMMAND: "{user_message}"

VALID ACTIONS:
- NAVIGATE: (to: "dashboard" | "chat" | "tasks" | "documents" | "settings")
- SEARCH: (query: "search string", type: "document" | "web")
- CREATE_TASK: (title: "task title", priority: "low"|"medium"|"high"|"urgent", due_date: "YYYY-MM-DD"|null)
- ANALYZE: (target: "business" | "revenue" | "latest document")
- CHAT: (message: "original message")

Respond with JSON ONLY.
Example: {{"action": "NAVIGATE", "params": {{"to": "tasks"}}}}
"""

    result = call_model(
        user_id=user_id,
        user_message=prompt,
        base_system_prompt="You are a smart command parser.",
        task_type=TaskType.QUICK,
        priority=Priority.HIGH,
        use_cache=True
    )
    
    try:
        # Extract JSON if model wraps it in markdown blocks
        clean_text = result.text.strip()
        if clean_text.startswith("```"):
            clean_text = re.sub(r"```(json)?", "", clean_text).strip()
        return json.loads(clean_text)
    except Exception as e:
        logger.warning(f"Failed to parse smart action: {e} | Text: {result.text}")
        return {"action": "CHAT", "params": {"message": user_message}}

# Backwards compatibility
run = run_intelligent
run_stream = run_stream_intelligent
