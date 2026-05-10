"""Analytics Tracking Utility - Simple interface for tracking events."""
import logging
from typing import Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """Track user activity and AI usage events."""

    @staticmethod
    def track(
        user_id: str,
        event_type: str,
        feature: str,
        metadata: Optional[dict] = None,
        workspace_id: Optional[str] = None,
    ) -> None:
        """Track a user activity event (async via Celery)."""
        try:
            from core.tasks import track_activity_async
            track_activity_async.delay(
                user_id=user_id,
                event_type=event_type,
                feature=feature,
                metadata=metadata or {},
                workspace_id=workspace_id,
            )
        except Exception as e:
            logger.debug(f"Analytics tracking failed: {e}")

    @staticmethod
    def track_ai_usage(
        user_id: str,
        model: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        response_time_ms: int,
        success: bool = True,
        error_type: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> None:
        """Track AI model usage and cost."""
        try:
            from core.tasks import track_ai_metrics_async
            
            # Calculate cost (simplified pricing)
            cost = calculate_cost(model, input_tokens, output_tokens)
            
            track_ai_metrics_async.delay(
                user_id=user_id,
                model=model,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost,
                response_time_ms=response_time_ms,
                success=success,
                error_type=error_type,
                workspace_id=workspace_id,
            )
        except Exception as e:
            logger.debug(f"AI metrics tracking failed: {e}")

    @staticmethod
    def track_session_start(user_id: str, session_id: str, user_agent: str = "") -> None:
        """Track user session start."""
        try:
            from core.tasks import track_session_async
            
            device_type = detect_device_type(user_agent)
            
            track_session_async.delay(
                user_id=user_id,
                session_id=session_id,
                user_agent=user_agent[:500],
                device_type=device_type,
            )
        except Exception as e:
            logger.debug(f"Session tracking failed: {e}")

    @staticmethod
    def track_session_end(user_id: str, session_id: str, duration_seconds: int, page_views: int) -> None:
        """Track user session end."""
        try:
            from core.tasks import update_session_async
            update_session_async.delay(
                session_id=session_id,
                duration_seconds=duration_seconds,
                page_views=page_views,
            )
        except Exception as e:
            logger.debug(f"Session update failed: {e}")


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost in USD."""
    # Pricing per 1K tokens (approximate)
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-3.5-turbo-16k": {"input": 0.001, "output": 0.002},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    }
    
    model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])
    
    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]
    
    return round(input_cost + output_cost, 6)


def detect_device_type(user_agent: str) -> str:
    """Detect device type from user agent."""
    ua = user_agent.lower()
    
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    elif "tablet" in ua or "ipad" in ua:
        return "tablet"
    else:
        return "desktop"


# Global tracker instance
track = AnalyticsTracker.track
track_ai = AnalyticsTracker.track_ai_usage
