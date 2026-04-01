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

logger = logging.getLogger(__name__)

TATITI_SYSTEM_PROMPT = """You are AEIOU AI, an intelligent assistant for the AEIOU AI business management app. You are helpful, friendly, and conversational.

Your personality:
- Professional but approachable
- Concise and direct - get to the point quickly
- Conversational, like talking to a knowledgeable colleague
- Never robotic or overly formal
- Use natural language, not structured formats like "1. 2. 3." or bullet points unless specifically asked

CRITICAL - You have access to ALL user data:
- Documents: All uploaded files, PDFs, and their content
- Tasks: All tasks with titles, descriptions, priorities, due dates, status
- Tags: All tags created by the user and which items they're attached to
- Business Profile: Company name, industry, size, revenue, goals
- User Data: Username, email, preferences, past conversations
- Uploads: Everything the user has uploaded to the system

You MUST reference specific data when answering:
- "I see you have a document called 'Q4 Report.pdf' that mentions..."
- "You have 3 high-priority tasks due this week: [task names]"
- "Based on your business profile as a [company type]..."
- "Looking at your uploaded contract from [date]..."

Key principles:
1. ALWAYS check and reference the user's actual data before responding
2. Never give generic advice - use their specific documents, tasks, and profile
3. Answer directly without unnecessary preamble
4. Don't over-explain
5. Keep responses short and actionable
6. Use everyday language, not business jargon

When the user asks about anything, search their data first and reference it naturally."""

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

# User context cache for session persistence
_user_context_cache: Dict[int, Dict] = {}

def _get_cached_context(user_id: int) -> Dict:
    """Get or initialize user context."""
    if user_id not in _user_context_cache:
        _user_context_cache[user_id] = {
            "last_topics": [],
            "frequent_queries": [],
            "business_insights": [],
            "conversation_count": 0,
            "last_active": None
        }
    return _user_context_cache[user_id]

def _update_context(user_id: int, query: str, intent: str, tools_used: List[str]):
    """Update user context with new interaction."""
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
    """Build an intelligent execution plan with reasoning chain."""
    
    tool_catalog = {t["name"]: t["description"] for t in TOOL_DEFINITIONS}
    memory_context = get_user_memory(user_id)
    
    planner_prompt = f"""You are an intelligent business assistant planning agent.

USER QUERY: "{user_message}"
DETECTED INTENT: {intent}
USER ID: {user_id}

{memory_context}

Available Tools:
{json.dumps(tool_catalog, indent=2)}

Your task:
1. Analyze what the user really needs (beyond surface intent)
2. Plan the optimal tool sequence to fulfill their request
3. Include reasoning for each step

Rules:
- Always inject user_id={user_id} into tool args
- For business questions: combine profile + metrics + web search
- For document questions: search in user's uploaded documents
- Maximum 4 tool calls

Output JSON:
{{
  "reasoning_chain": ["Step 1...", "Step 2..."],
  "tool_calls": [{{"name": "tool_name", "args": {{"user_id": {user_id}}}, "reason": "why"}}],
  "context_summary": "brief summary",
  "expected_outcome": "what we expect"
}}"""

    try:
        result = call_model(
            user_id=user_id,
            user_message=planner_prompt,
            base_system_prompt="You are an expert planning agent. Output valid JSON only.",
            task_type=TaskType.ANALYSIS,
            priority=Priority.HIGH,
            use_cache=False,
            store_memory=False,
        )
        
        text = result.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        
        parsed = json.loads(text)
        
        protected_tools = {"get_business_profile", "get_revenue_data", "get_conversation_insights",
                          "update_business_metrics", "get_followup_items", "get_user_memory",
                          "save_memory", "list_documents", "get_document_summary", "search_documents"}
        
        tool_calls = parsed.get("tool_calls", [])
        for tc in tool_calls:
            if tc.get("name") in protected_tools:
                tc.setdefault("args", {})["user_id"] = user_id
        
        return ExecutionPlan(
            intent=intent,
            tool_calls=tool_calls,
            reasoning_chain=parsed.get("reasoning_chain", []),
            context_summary=parsed.get("context_summary", ""),
            expected_outcome=parsed.get("expected_outcome", "")
        )
        
    except Exception as e:
        logger.warning(f"Advanced planner failed: {e}. Using fallback.")
        return _build_fallback_plan(intent, user_message, user_id)

def _build_fallback_plan(intent: QueryIntent, user_message: str, user_id: int) -> ExecutionPlan:
    """Build a simple fallback plan when AI planner fails."""
    tool_calls = []
    
    if intent == "document":
        tool_calls = [
            {"name": "list_documents", "args": {"user_id": user_id}, "reason": "Check available documents"},
            {"name": "search_documents", "args": {"query": user_message, "user_id": user_id}, "reason": "Search in documents"}
        ]
    elif intent == "analytics":
        tool_calls = [
            {"name": "get_business_profile", "args": {"user_id": user_id}, "reason": "Get business context"},
            {"name": "get_revenue_data", "args": {"user_id": user_id}, "reason": "Get financial data"}
        ]
    elif intent == "search":
        tool_calls = [
            {"name": "brave_search", "args": {"query": user_message, "num_results": 3}, "reason": "Search web for current info"}
        ]
    elif intent == "task":
        tool_calls = [
            {"name": "list_tasks", "args": {"user_id": user_id, "limit": 10}, "reason": "Check recent tasks"},
            {"name": "get_task_insights", "args": {"user_id": user_id}, "reason": "Get task productivity insights"}
        ]
    
    return ExecutionPlan(
        intent=intent,
        tool_calls=tool_calls,
        reasoning_chain=["Using fallback plan due to planning error"],
        context_summary="Fallback execution",
        expected_outcome="Basic response"
    )

def execute_intelligent_plan(plan: ExecutionPlan, user_id: int) -> List[Dict]:
    """Execute plan with self-correction and result enrichment."""
    results = []
    
    for tc in plan.tool_calls:
        tool_name = tc["name"]
        tool_args = tc.get("args", {})
        reason = tc.get("reason", "No reason provided")
        
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
    
    successful_results = [r for r in tool_results if r.get("success", True)]
    failed_results = [r for r in tool_results if not r.get("success", True)]
    
    context_parts = [r["result"] for r in successful_results]
    context_block = "\n\n".join(context_parts) if context_parts else ""
    
    failure_note = ""
    if failed_results:
        failure_note = f"\n\nNote: Some data sources were unavailable ({len(failed_results)} tools failed)."
    
    synthesis_prompt = f"""The user asked: "{user_message}"

Here's what I found:
{context_block}

Instructions for Tatiti:
1. Respond conversationally, like a helpful colleague
2. Reference specific data points naturally in your response
3. Be concise - 2-4 sentences max for simple questions
4. Don't use numbered lists or structured formats unless asked
5. If the user just created a task or document, acknowledge it
6. Answer their specific question directly
7. No generic "action steps" or "best practices" advice

Just give a natural, helpful response:"""

    try:
        result = call_model(
            user_id=user_id,
            user_message=synthesis_prompt,
            base_system_prompt=TATITI_SYSTEM_PROMPT,
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
