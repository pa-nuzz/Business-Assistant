"""
Tool decision engine.
Decides WHICH tools to call, in WHAT order, and WHETHER to cache results.
Replaces hardcoded tool lists per intent in the orchestrator.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any


class DecisionType(Enum):
    NO_TOOLS = "no_tools"
    SINGLE = "single"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
    reason: str
    depends_on: Optional[str] = None
    cache_ttl: int = 0
    on_empty_fallback: Optional[str] = None


@dataclass
class ToolDecision:
    decision_type: DecisionType
    tool_calls: List[ToolCall]
    reasoning: str


SOCIAL_PATTERNS = [
    r'\b(hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening)\b',
    r'\b(thanks|thank\s+you|appreciate\s+it|cheers)\b',
    r'\b(bye|goodbye|see\s+you|talk\s+later|ttyl)\b',
    r'^\s*ok\s*$',
    r'^\s*okay\s*$',
    r'^\s*sure\s*$',
    r'^\s*sounds\s+good\s*$',
]


class ToolDecisionEngine:

    def __init__(self, user_id: int):
        self.user_id = user_id

    def decide(
        self,
        intent: str,
        user_message: str,
        entities: list,
        context: dict
    ) -> ToolDecision:

        uid = self.user_id

        # --- No-tool cases ---
        if self._is_social(user_message):
            return ToolDecision(
                decision_type=DecisionType.NO_TOOLS,
                tool_calls=[],
                reasoning="Social or conversational message — no data needed."
            )

        if intent == "chat" and not entities:
            return ToolDecision(
                decision_type=DecisionType.NO_TOOLS,
                tool_calls=[],
                reasoning="General chat with no entity references — answer from context."
            )

        # --- Entity-specific single tool ---
        if entities:
            entity = entities[0]
            if entity.needs_clarification:
                return ToolDecision(
                    decision_type=DecisionType.NO_TOOLS,
                    tool_calls=[],
                    reasoning=f"Ambiguous entity reference. Ask: 'Did you mean {entity.name}?'"
                )
            if entity.type == "document":
                return ToolDecision(
                    decision_type=DecisionType.SINGLE,
                    tool_calls=[ToolCall(
                        name="get_document_summary",
                        args={"doc_id": entity.id, "user_id": uid},
                        reason=f"Fetch specific document: {entity.name}",
                        cache_ttl=600
                    )],
                    reasoning=f"User is asking about a specific document: {entity.name}"
                )
            if entity.type == "task":
                return ToolDecision(
                    decision_type=DecisionType.SINGLE,
                    tool_calls=[ToolCall(
                        name="get_task_details",
                        args={"task_id": entity.id, "user_id": uid},
                        reason=f"Fetch specific task: {entity.name}",
                        cache_ttl=0
                    )],
                    reasoning=f"User is asking about a specific task: {entity.name}"
                )

        # --- Analytics ---
        if intent == "analytics":
            return ToolDecision(
                decision_type=DecisionType.SEQUENTIAL,
                tool_calls=[
                    ToolCall(
                        name="get_business_profile",
                        args={"user_id": uid},
                        reason="Load business context first",
                        cache_ttl=600
                    ),
                    ToolCall(
                        name="get_revenue_data",
                        args={"user_id": uid, "period": "monthly"},
                        reason="Load revenue data",
                        depends_on="get_business_profile",
                        cache_ttl=120
                    ),
                ],
                reasoning="Analytics query: fetch profile then revenue in order."
            )

        # --- Search with fallback ---
        if intent == "search":
            return ToolDecision(
                decision_type=DecisionType.CONDITIONAL,
                tool_calls=[
                    ToolCall(
                        name="search_documents",
                        args={"query": user_message, "user_id": uid},
                        reason="Search internal documents first",
                        on_empty_fallback="brave_search"
                    )
                ],
                reasoning="Search internal docs first, fall back to web search if empty."
            )

        # --- Document listing ---
        if intent == "document" and not entities:
            return ToolDecision(
                decision_type=DecisionType.PARALLEL,
                tool_calls=[
                    ToolCall(
                        name="list_documents",
                        args={"user_id": uid},
                        reason="Fetch all documents",
                        cache_ttl=180
                    ),
                    ToolCall(
                        name="get_user_memory",
                        args={"user_id": uid, "category": "context"},
                        reason="Load user context",
                        cache_ttl=60
                    ),
                ],
                reasoning="Parallel: documents + user context."
            )

        # --- Default: minimal profile context ---
        return ToolDecision(
            decision_type=DecisionType.SINGLE,
            tool_calls=[
                ToolCall(
                    name="get_business_profile",
                    args={"user_id": uid},
                    reason="Load base context for unknown intent",
                    cache_ttl=600
                )
            ],
            reasoning=f"Unknown intent '{intent}' — load business profile as base context."
        )

    def _is_social(self, message: str) -> bool:
        return any(re.search(p, message, re.IGNORECASE) for p in SOCIAL_PATTERNS)
