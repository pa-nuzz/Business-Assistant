"""
MCP Tool Registry.

All tools follow the same contract:
  - Input: typed kwargs (validated by the agent before calling)
  - Output: dict with "result" key (or "error" key on failure)

This is the single source of truth for tool definitions.
The agent reads TOOL_DEFINITIONS to tell the model what's available,
then calls execute_tool() when the model requests a tool.
"""
import logging
from typing import Any
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# ─── Tool Definitions (sent to the LLM) ──────────────────────────────────────
# These follow the function-calling schema format used by Gemini/OpenAI-compatible APIs.

TOOL_DEFINITIONS = [
    {
        "name": "get_business_profile",
        "description": (
            "Retrieves the user's business profile including company name, industry, "
            "size, description, goals, and key metrics. Call this at the start of any "
            "conversation to understand the business context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The authenticated user's ID."
                }
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_revenue_data",
        "description": (
            "Retrieves revenue data from the user's business profile key_metrics. "
            "Provides trend analysis if historical data exists. Use this for revenue "
            "reporting and financial analysis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"],
                    "default": "monthly",
                    "description": "Time period for revenue aggregation."
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_conversation_insights",
        "description": (
            "Analyzes recent conversations to identify recurring topics and patterns. "
            "Returns most frequently asked questions and conversation themes. "
            "Use this to understand user interests and pain points."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Number of recent conversations to analyze."
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "update_business_metrics",
        "description": (
            "Safely updates a specific business metric in the user's profile. "
            "Use this when the user shares updated metrics like revenue, customer count, "
            "conversion rates, or any other KPI they want to track."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "metric_key": {
                    "type": "string",
                    "description": "Metric name, e.g., 'monthly_revenue', 'customer_count'"
                },
                "metric_value": {
                    "type": ["number", "string"],
                    "description": "The metric value (number or string)."
                },
            },
            "required": ["user_id", "metric_key", "metric_value"],
        },
    },
    {
        "name": "get_followup_items",
        "description": (
            "Retrieves all follow-up items stored in user memory. "
            "Returns actionable checklist of pending tasks or commitments. "
            "Use this to remind users of items they asked you to track."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_user_memory",
        "description": (
            "Retrieves stored memory facts about the user — preferences, past decisions, "
            "important context. Use this to personalize responses. "
            "Optionally filter by category: preference, decision, context, fact, followup."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "category": {
                    "type": "string",
                    "enum": ["preference", "decision", "context", "fact", "followup", "all"],
                    "description": "Filter memories by category. Use 'all' to fetch everything."
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "save_memory",
        "description": (
            "Saves an important fact, preference, or decision to the user's memory. "
            "Call this when the user shares something important that should be remembered "
            "for future conversations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "key": {"type": "string", "description": "Short identifier, e.g. 'preferred_currency'"},
                "value": {"type": "string", "description": "The value to remember."},
                "category": {
                    "type": "string",
                    "enum": ["preference", "decision", "context", "fact", "followup"],
                },
            },
            "required": ["user_id", "key", "value", "category"],
        },
    },
    {
        "name": "list_documents",
        "description": "Lists all documents the user has uploaded, with their titles and processing status.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_document_summary",
        "description": (
            "Returns the AI-generated summary of a specific document. "
            "Use this for a quick overview before deciding if you need deeper details."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "UUID of the document."},
                "user_id": {"type": "integer", "description": "Must match the document owner."},
            },
            "required": ["doc_id", "user_id"],
        },
    },
    {
        "name": "search_documents",
        "description": (
            "Keyword-based search across document titles and content chunks. "
            "Splits query into keywords and finds matches in both titles and content. "
            "Use this for specific questions about document content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for."},
                "user_id": {"type": "integer"},
                "doc_id": {
                    "type": "string",
                    "description": "Optional: limit search to one specific document UUID."
                },
            },
            "required": ["query", "user_id"],
        },
    },
    {
        "name": "brave_search",
        "description": (
            "Searches the web for real-time information — market data, competitors, "
            "news, industry trends. Use when user needs current external information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "num_results": {
                    "type": "integer",
                    "description": "Number of results (1-5). Default: 3.",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
]


# ─── Tool Implementations ─────────────────────────────────────────────────────

def get_business_profile(user_id: int) -> dict:
    """Fetch user's business profile from DB."""
    try:
        from core.models import BusinessProfile
        profile = BusinessProfile.objects.select_related("user").get(user_id=user_id)
        return {
            "result": {
                "company_name": profile.company_name,
                "industry": profile.industry,
                "company_size": profile.company_size,
                "description": profile.description,
                "goals": profile.goals,
                "key_metrics": profile.key_metrics,
            }
        }
    except Exception as e:
        return {"error": f"No business profile found for user {user_id}. Ask user to set one up."}


def get_user_memory(user_id: int, category: str = "all") -> dict:
    """Fetch stored memories for a user."""
    try:
        from core.models import UserMemory
        qs = UserMemory.objects.filter(user_id=user_id)
        if category != "all":
            qs = qs.filter(category=category)
        memories = [
            {"key": m.key, "value": m.value, "category": m.category}
            for m in qs.order_by("-updated_at")[:30]  # cap at 30 items
        ]
        return {"result": memories if memories else "No memories stored yet."}
    except Exception as e:
        logger.exception("get_user_memory error")
        return {"error": str(e)}


def save_memory(user_id: int, key: str, value: str, category: str) -> dict:
    """Upsert a memory fact."""
    try:
        from core.models import UserMemory
        from utils.sanitization import sanitize_plain_text, sanitize_rich_text
        
        # Sanitize inputs
        key = sanitize_plain_text(key, max_length=200)
        value = sanitize_rich_text(value, max_length=10000)
        category = sanitize_plain_text(category, max_length=50)
        
        obj, created = UserMemory.objects.update_or_create(
            user_id=user_id,
            key=key,
            defaults={"value": value, "category": category},
        )
        action = "created" if created else "updated"
        return {"result": f"Memory '{key}' {action} successfully."}
    except Exception as e:
        logger.exception("save_memory error")
        return {"error": str(e)}


def get_revenue_data(user_id: int, period: str = "monthly") -> dict:
    """
    Retrieve revenue data from user's business profile.
    Returns trend analysis if multiple data points exist.
    """
    try:
        from core.models import BusinessProfile
        profile = BusinessProfile.objects.select_related("user").get(user_id=user_id)
        
        key_metrics = profile.key_metrics or {}
        
        # Look for revenue-related keys
        revenue_keys = [
            "monthly_revenue", "revenue", "annual_revenue", "mrr", "arr",
            "weekly_revenue", "daily_revenue", "quarterly_revenue"
        ]
        
        revenue_data = {}
        for key in revenue_keys:
            if key in key_metrics:
                revenue_data[key] = key_metrics[key]
        
        # If no explicit revenue found, return all key_metrics for manual inspection
        if not revenue_data:
            revenue_data = key_metrics
        
        # Simple trend analysis (placeholder for when you add historical data)
        trend = "No historical trend data available. Consider storing revenue history."
        
        return {
            "result": {
                "period": period,
                "revenue_metrics": revenue_data,
                "trend_analysis": trend,
                "profile_company": profile.company_name,
            }
        }
    except BusinessProfile.DoesNotExist:
        return {"error": f"No business profile found for user {user_id}."}
    except Exception as e:
        logger.exception("get_revenue_data error")
        return {"error": str(e)}


def get_conversation_insights(user_id: int, limit: int = 10) -> dict:
    """
    Analyze recent conversations for recurring topics.
    Returns most frequently asked question categories using keyword frequency.
    """
    try:
        from core.models import Conversation, Message
        from collections import Counter
        
        # Get recent conversations
        recent_conversations = Conversation.objects.filter(
            user_id=user_id
        ).order_by("-updated_at")[:limit]
        
        if not recent_conversations:
            return {"result": "No conversations found for analysis."}
        
        # Get all user messages from these conversations
        convo_ids = [c.id for c in recent_conversations]
        user_messages = Message.objects.filter(
            conversation_id__in=convo_ids,
            role="user"
        ).values_list("content", flat=True)
        
        # Simple keyword frequency analysis
        STOPWORDS = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "was", "are", "were", "be", "been", "have", "has",
            "had", "do", "does", "did", "will", "would", "can", "could", "should",
            "this", "that", "these", "those", "it", "its", "by", "from", "as",
            "not", "no", "so", "if", "then", "than", "when", "which", "who",
            "what", "how", "why", "where", "my", "me", "i", "you", "your",
        }
        
        # Business-relevant keywords to track
        BUSINESS_KEYWORDS = {
            "revenue", "sales", "customer", "client", "profit", "cost", "expense",
            "marketing", "growth", "strategy", "competitor", "market", "product",
            "service", "price", "pricing", "budget", "forecast", "report",
            "analytics", "metrics", "kpi", "goal", "target", "team", "employee",
            "hiring", "funding", "investor", "pitch", "deck", "document", "file",
            "contract", "invoice", "tax", "legal", "compliance", "tech", "software",
            "website", "app", "dashboard", "automation", "ai", "data",
        }
        
        all_text = " ".join(user_messages).lower()
        words = [w.strip(".,!?;:'\"()") for w in all_text.split() if len(w) > 2]
        
        # Count business-relevant keywords
        keyword_counts = Counter()
        for word in words:
            if word in BUSINESS_KEYWORDS and word not in STOPWORDS:
                keyword_counts[word] += 1
        
        # Get top topics
        top_topics = keyword_counts.most_common(10)
        
        # Simple question pattern detection
        question_starters = ["how", "what", "when", "where", "why", "can", "should", "is", "are"]
        question_count = sum(1 for msg in user_messages if any(msg.lower().startswith(s) for s in question_starters))
        
        return {
            "result": {
                "conversations_analyzed": len(recent_conversations),
                "total_messages": len(user_messages),
                "questions_asked": question_count,
                "top_topics": [{"topic": t[0], "frequency": t[1]} for t in top_topics] if top_topics else "No recurring topics identified",
                "suggested_focus_areas": [t[0] for t in top_topics[:5]] if top_topics else [],
            }
        }
    except Exception as e:
        logger.exception("get_conversation_insights error")
        return {"error": str(e)}


def update_business_metrics(user_id: int, metric_key: str, metric_value) -> dict:
    """
    Safely updates a specific metric in BusinessProfile.key_metrics.
    Validates that metric_value is a number or string.
    """
    try:
        from core.models import BusinessProfile
        
        # Validate metric_value type
        if not isinstance(metric_value, (int, float, str)):
            return {
                "error": f"Invalid metric_value type: {type(metric_value).__name__}. Must be number or string."
            }
        
        # Get or create profile
        profile, created = BusinessProfile.objects.get_or_create(
            user_id=user_id,
            defaults={"key_metrics": {}}
        )
        
        # Update the metric
        if profile.key_metrics is None:
            profile.key_metrics = {}
        
        profile.key_metrics[metric_key] = metric_value
        profile.save(update_fields=["key_metrics"])
        
        return {
            "result": {
                "message": f"Metric '{metric_key}' updated successfully.",
                "updated_metrics": profile.key_metrics,
            }
        }
    except Exception as e:
        logger.exception("update_business_metrics error")
        return {"error": str(e)}


def get_followup_items(user_id: int) -> dict:
    """
    Fetches all UserMemory records with category='followup'.
    Returns them formatted as an actionable checklist.
    """
    try:
        from core.models import UserMemory
        
        followups = UserMemory.objects.filter(
            user_id=user_id,
            category="followup"
        ).order_by("-updated_at")
        
        if not followups:
            return {"result": "No follow-up items found. You're all caught up!"}
        
        items = []
        for i, item in enumerate(followups, 1):
            items.append({
                "number": i,
                "key": item.key,
                "description": item.value,
                "created": item.created_at.strftime("%Y-%m-%d"),
            })
        
        return {
            "result": {
                "total_items": len(items),
                "checklist": items,
                "summary": f"You have {len(items)} follow-up item(s) pending."
            }
        }
    except Exception as e:
        logger.exception("get_followup_items error")
        return {"error": str(e)}


def list_documents(user_id: int) -> dict:
    """List user's uploaded documents."""
    try:
        from core.models import Document
        docs = Document.objects.filter(user_id=user_id).values(
            "id", "title", "file_type", "status", "page_count", "created_at"
        )
        result = [
            {
                "id": str(d["id"]),
                "title": d["title"],
                "type": d["file_type"],
                "status": d["status"],
                "pages": d["page_count"],
            }
            for d in docs
        ]
        return {"result": result if result else "No documents uploaded yet."}
    except Exception as e:
        return {"error": str(e)}


def get_document_summary(doc_id: str, user_id: int) -> dict:
    """Get the pre-generated summary of a document."""
    try:
        from core.models import Document
        doc = Document.objects.get(id=doc_id, user_id=user_id, status="ready")
        if not doc.summary:
            return {"error": "Document is still processing or has no summary yet."}
        return {
            "result": {
                "title": doc.title,
                "summary": doc.summary,
                "pages": doc.page_count,
                "type": doc.file_type,
            }
        }
    except Document.DoesNotExist:
        return {"error": f"Document {doc_id} not found or not ready."}
    except Exception as e:
        return {"error": str(e)}


def search_documents(query: str, user_id: int, doc_id: str = None) -> dict:
    """
    Keyword-based search across document titles and content chunks.
    Splits query into keywords and finds matches in both titles and content.
    """
    try:
        from core.models import DocumentChunk, Document
        keywords = [w.lower().strip() for w in query.split() if len(w) > 2]

        # First, search document titles
        title_matches = []
        docs_qs = Document.objects.filter(user_id=user_id, status="ready")
        if doc_id:
            docs_qs = docs_qs.filter(id=doc_id)
        
        for doc in docs_qs:
            doc_title_lower = doc.title.lower()
            # Check if any keyword matches the title (exact or partial)
            title_score = sum(2 for kw in keywords if kw in doc_title_lower)
            # Also check for common document name patterns
            if any(term in doc_title_lower for term in ['cv', 'resume', 'curriculum', 'portfolio']):
                title_score += 3
            if title_score > 0:
                title_matches.append({
                    "score": title_score,
                    "doc_title": doc.title,
                    "doc_id": str(doc.id),
                    "content": f"Document title: {doc.title}. This is a {doc.file_type} file with {doc.page_count or 'unknown'} pages.",
                    "page": 1,
                    "match_type": "title"
                })

        # Then search content chunks
        qs = DocumentChunk.objects.filter(document__user_id=user_id, document__status="ready")
        if doc_id:
            qs = qs.filter(document_id=doc_id)

        # Score chunks by keyword overlap
        content_results = []
        for chunk in qs.select_related("document")[:200]:
            content_lower = chunk.content.lower()
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                content_results.append({
                    "score": score,
                    "doc_title": chunk.document.title,
                    "doc_id": str(chunk.document.id),
                    "content": chunk.content[:800],
                    "page": chunk.page_number,
                    "match_type": "content"
                })

        # Combine and sort results - title matches get priority
        all_results = title_matches + content_results
        all_results.sort(key=lambda x: x["score"], reverse=True)
        top = all_results[:5]

        if not top:
            return {"result": "No relevant content found in documents for this query."}
        return {"result": top}
    except Exception as e:
        logger.exception("search_documents error")
        return {"error": str(e)}


def brave_search(query: str, num_results: int = 3) -> dict:
    """
    Web search via Brave Search API.
    Falls back to DuckDuckGo HTML scrape if no API key configured.
    """
    import httpx
    from django.conf import settings

    api_key = settings.BRAVE_SEARCH_API_KEY

    if api_key:
        # Brave Search API (2000 free queries/month)
        try:
            with httpx.Client(timeout=8) as client:
                resp = client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": num_results, "text_decorations": False},
                    headers={"Accept": "application/json", "X-Subscription-Token": api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                results = [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "snippet": r.get("description", ""),
                    }
                    for r in data.get("web", {}).get("results", [])[:num_results]
                ]
                return {"result": results}
        except Exception as e:
            logger.warning(f"Brave search failed: {e}, trying DuckDuckGo fallback")

    # DuckDuckGo fallback (no API key needed)
    try:
        with httpx.Client(timeout=8, follow_redirects=True) as client:
            resp = client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
            data = resp.json()
            results = []
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", "")[:300],
                })
            for topic in data.get("RelatedTopics", [])[:num_results - 1]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:80],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")[:300],
                    })
            return {"result": results if results else "No results found."}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


# ─── Task Management Tools ──────────────────────────────────────────────────

def create_task(user_id: int, title: str, description: str = "", 
                priority: str = "medium", due_date: str = None,
                assignee_id: int = None, tags: list = None) -> dict:
    """
    Create a new task for the user.
    
    Args:
        user_id: The user creating the task
        title: Task title (required)
        description: Task description (optional)
        priority: low, medium, high, or urgent (default: medium)
        due_date: ISO format date string (optional)
        assignee_id: User ID to assign task to (optional, defaults to creator)
        tags: List of tag strings (optional)
    """
    try:
        from core.models import Task, TaskTag, BusinessProfile
        from django.contrib.auth.models import User
        from utils.sanitization import sanitize_plain_text, sanitize_rich_text
        
        # Sanitize inputs
        title = sanitize_plain_text(title, max_length=255)
        description = sanitize_rich_text(description, max_length=5000)
        
        # Validate required fields
        if not title:
            return {"error": "Task title is required"}
        
        # Get or create business profile
        try:
            business_profile = BusinessProfile.objects.get(user_id=user_id)
        except BusinessProfile.DoesNotExist:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            business_profile = BusinessProfile.objects.create(user=user)
        
        # Set assignee (default to creator if not specified)
        if assignee_id is None:
            assignee_id = user_id
        
        # Parse due_date if provided
        parsed_due_date = None
        if due_date:
            from datetime import datetime
            try:
                parsed_due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Create task
        task = Task.objects.create(
            user_id=user_id,
            created_by_id=user_id,
            business_profile=business_profile,
            title=title,
            description=description,
            priority=priority,
            due_date=parsed_due_date,
            assignee_id=assignee_id,
        )
        
        # Add tags (sanitized)
        if tags:
            for tag in tags:
                clean_tag = sanitize_plain_text(tag, max_length=100)
                if clean_tag:
                    TaskTag.objects.create(task=task, tag=clean_tag.lower())
        
        return {
            "result": {
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "message": "Task created successfully"
            }
        }
    except Exception as e:
        logger.exception("create_task error")
        return {"error": str(e)}


def list_tasks(user_id: int, status: str = None, priority: str = None,
               assignee_id: int = None, limit: int = 50) -> dict:
    """
    List tasks for a user with optional filters.
    
    Args:
        user_id: The user requesting tasks
        status: Filter by status (optional)
        priority: Filter by priority (optional)
        assignee_id: Filter by assignee (optional)
        limit: Maximum number of results (default: 50)
    """
    try:
        from core.models import Task
        from django.db.models import Q
        
        # Get tasks created by user OR assigned to user
        tasks = Task.objects.filter(
            Q(created_by_id=user_id) | Q(assignee_id=user_id) | Q(user_id=user_id)
        ).exclude(status="archived")
        
        # Apply filters
        if status:
            tasks = tasks.filter(status=status)
        if priority:
            tasks = tasks.filter(priority=priority)
        if assignee_id:
            tasks = tasks.filter(assignee_id=assignee_id)
        
        tasks = tasks.order_by("-created_at")[:limit]
        
        results = []
        for task in tasks:
            results.append({
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "assignee": task.assignee.username if task.assignee else None,
                "tags": [tag.tag for tag in task.tags.all()],
            })
        
        return {"result": results}
    except Exception as e:
        logger.exception("list_tasks error")
        return {"error": str(e)}


def update_task_status(task_id: str, user_id: int, status: str) -> dict:
    """
    Update task status.
    
    Args:
        task_id: UUID of the task
        user_id: User making the update
        status: New status (todo, in_progress, review, done, archived)
    """
    try:
        from core.models import Task, TaskActivity
        from datetime import datetime
        
        task = Task.objects.get(id=task_id)
        
        # Check permissions
        if task.created_by_id != user_id and task.assignee_id != user_id:
            return {"error": "Permission denied"}
        
        old_status = task.status
        task.status = status
        
        # Update completed_at if marking as done
        if status == "done" and old_status != "done":
            task.completed_at = datetime.now()
        elif status != "done":
            task.completed_at = None
        
        task.save()
        
        # Log activity
        TaskActivity.objects.create(
            task=task,
            user_id=user_id,
            activity_type="status_changed",
            old_value=old_status,
            new_value=status
        )
        
        return {
            "result": {
                "id": str(task.id),
                "status": task.status,
                "message": f"Task status updated to {status}"
            }
        }
    except Task.DoesNotExist:
        return {"error": "Task not found"}
    except Exception as e:
        logger.exception("update_task_status error")
        return {"error": str(e)}


def get_task_details(task_id: str, user_id: int) -> dict:
    """
    Get detailed information about a specific task.
    
    Args:
        task_id: UUID of the task
        user_id: User requesting the details
    """
    try:
        from core.models import Task
        from django.db.models import Q
        
        task = Task.objects.get(
            Q(id=task_id),
            Q(created_by_id=user_id) | Q(assignee_id=user_id) | Q(user_id=user_id)
        )
        
        # Get subtasks
        subtasks = []
        for subtask in task.subtasks.all():
            subtasks.append({
                "id": str(subtask.id),
                "title": subtask.title,
                "status": subtask.status,
            })
        
        # Get comments
        comments = []
        for comment in task.comments.order_by("-created_at")[:10]:
            comments.append({
                "id": str(comment.id),
                "content": comment.content,
                "user": comment.user.username,
                "created_at": comment.created_at.isoformat(),
            })
        
        return {
            "result": {
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_by": task.created_by.username,
                "assignee": task.assignee.username if task.assignee else None,
                "tags": [tag.tag for tag in task.tags.all()],
                "subtasks": subtasks,
                "comments": comments,
                "created_at": task.created_at.isoformat(),
            }
        }
    except Task.DoesNotExist:
        return {"error": "Task not found"}
    except Exception as e:
        logger.exception("get_task_details error")
        return {"error": str(e)}


def get_task_insights(user_id: int) -> dict:
    """
    Get productivity insights for the user.
    
    Args:
        user_id: The user to get insights for
    """
    try:
        from core.models import Task
        from django.db.models import Q, Count
        from datetime import datetime, timedelta
        
        # Base queryset
        tasks = Task.objects.filter(
            Q(created_by_id=user_id) | Q(assignee_id=user_id)
        )
        
        # Status counts
        status_counts = tasks.values("status").annotate(count=Count("id"))
        status_data = {item["status"]: item["count"] for item in status_counts}
        
        # Completion rate
        total = tasks.count()
        completed = tasks.filter(status="done").count()
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # This week stats
        week_ago = datetime.now() - timedelta(days=7)
        created_this_week = tasks.filter(created_at__gte=week_ago).count()
        completed_this_week = tasks.filter(completed_at__gte=week_ago).count()
        
        # Overdue tasks
        overdue = tasks.filter(
            due_date__lt=datetime.now(),
            status__in=["todo", "in_progress", "review"]
        ).count()
        
        return {
            "result": {
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round(completion_rate, 1),
                "created_this_week": created_this_week,
                "completed_this_week": completed_this_week,
                "overdue_tasks": overdue,
                "by_status": status_data,
            }
        }
    except Exception as e:
        logger.exception("get_task_insights error")
        return {"error": str(e)}


def suggest_tasks_from_context(user_id: int, context: str, source_type: str = "chat") -> dict:
    """
    AI suggests tasks based on conversation or document content.
    
    Args:
        user_id: The user to suggest tasks for
        context: The text content to analyze for task suggestions
        source_type: The source of the context (chat, document, etc.)
    """
    try:
        from services.model_layer import call_model, TaskType, Priority
        
        if not context or len(context.strip()) < 20:
            return {"result": {"suggestions": [], "message": "Context too short for task extraction"}}
        
        # Use AI to extract potential tasks
        extraction_prompt = f"""Analyze the following text and extract any actionable tasks or to-do items.

Text: "{context[:1000]}"

Extract tasks that:
1. Are clearly actionable (not vague goals)
2. Have specific outcomes
3. Would make sense as a standalone task

Return JSON:
{{
  "suggestions": [
    {{
      "title": "Concise task title",
      "description": "Brief description",
      "priority": "low|medium|high",
      "reasoning": "Why this should be a task"
    }}
  ]
}}

If no actionable tasks found, return empty suggestions array."""

        result = call_model(
            user_id=user_id,
            user_message=extraction_prompt,
            base_system_prompt="You are a task extraction assistant. Output valid JSON only.",
            task_type=TaskType.ANALYSIS,
            priority=Priority.NORMAL,
            use_cache=False,
        )
        
        # Parse response
        text = result.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
        
        parsed = json.loads(text)
        suggestions = parsed.get("suggestions", [])
        
        return {
            "result": {
                "suggestions": suggestions,
                "count": len(suggestions),
                "source": source_type,
            }
        }
        
    except Exception as e:
        logger.exception("suggest_tasks_from_context error")
        return {"error": str(e)}


def delete_task(user_id: int, task_id: str) -> dict:
    """
    Delete a task permanently.
    
    Args:
        user_id: The user who owns the task
        task_id: UUID of the task to delete
    """
    try:
        from core.models import Task, TaskActivity
        
        task = Task.objects.get(id=task_id, user_id=user_id)
        title = task.title
        
        # Log the deletion for audit trail
        TaskActivity.objects.create(
            task=task,
            user_id=user_id,
            activity_type="archived",
            old_value="active",
            new_value="deleted"
        )
        
        task.delete()
        
        return {
            "result": {
                "deleted": True,
                "task_title": title,
                "message": f"Task '{title}' deleted successfully"
            }
        }
    except Task.DoesNotExist:
        return {"error": "Task not found"}
    except Exception as e:
        logger.exception("delete_task error")
        return {"error": str(e)}


# ─── Tool Dispatcher ──────────────────────────────────────────────────────────

TOOL_MAP: dict[str, callable] = {
    "get_business_profile": get_business_profile,
    "get_revenue_data": get_revenue_data,
    "get_conversation_insights": get_conversation_insights,
    "update_business_metrics": update_business_metrics,
    "get_followup_items": get_followup_items,
    "get_user_memory": get_user_memory,
    "save_memory": save_memory,
    "list_documents": list_documents,
    "get_document_summary": get_document_summary,
    "search_documents": search_documents,
    "brave_search": brave_search,
    # Task management tools
    "create_task": create_task,
    "list_tasks": list_tasks,
    "update_task_status": update_task_status,
    "get_task_details": get_task_details,
    "get_task_insights": get_task_insights,
    "suggest_tasks_from_context": suggest_tasks_from_context,
    "delete_task": delete_task,
}


def execute_tool(tool_name: str, tool_args: dict) -> dict:
    """
    Single entry point for all tool calls.
    Returns a dict — always has "result" or "error" key.
    """
    fn = TOOL_MAP.get(tool_name)
    if not fn:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        logger.info(f"Executing tool: {tool_name} | args: {tool_args}")
        result = fn(**tool_args)
        logger.info(f"Tool result: {tool_name} → ok")
        return result
    except TypeError as e:
        return {"error": f"Invalid arguments for {tool_name}: {str(e)}"}
    except Exception as e:
        logger.exception(f"Tool {tool_name} crashed")
        return {"error": f"Tool error: {str(e)}"}
