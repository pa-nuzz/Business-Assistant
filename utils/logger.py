"""
Logging utilities. Wraps structlog for consistent, searchable log output.
In production on Render, logs are sent to the dashboard automatically.
"""
import logging
import structlog

# Default logger for direct import
logger = structlog.get_logger("business_assistant")


def get_logger(name: str):
    """Get a structured logger for a module."""
    return structlog.get_logger(name)


def log_agent_run(
    user_id: int,
    model: str,
    tools_used: list,
    iterations: int,
    success: bool,
    latency_ms: float = None,
):
    """Standard log entry for every agent run. Useful for monitoring."""
    logger = get_logger("agent.metrics")
    logger.info(
        "agent_run",
        user_id=user_id,
        model=model,
        tools_used=tools_used,
        tool_count=len(tools_used),
        iterations=iterations,
        success=success,
        latency_ms=latency_ms,
    )


def log_model_fallback(from_model: str, to_model: str, reason: str):
    """Log when model fallback occurs."""
    logger = get_logger("agent.router")
    logger.warning(
        "model_fallback",
        from_model=from_model,
        to_model=to_model,
        reason=reason,
    )


def log_tool_call(tool_name: str, user_id: int, success: bool, error: str = None):
    """Log individual tool calls."""
    logger = get_logger("mcp.tools")
    level = "info" if success else "warning"
    getattr(logger, level)(
        "tool_call",
        tool=tool_name,
        user_id=user_id,
        success=success,
        error=error,
    )


def log_api_request(
    user_id: int,
    endpoint: str,
    method: str,
    status_code: int,
    latency_ms: float = None,
    error: str = None,
):
    """Log API request with structured data."""
    logger = get_logger("api.request")
    level = "info" if status_code < 400 else "warning" if status_code < 500 else "error"
    getattr(logger, level)(
        "api_request",
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        latency_ms=latency_ms,
        error=error,
    )


def log_security_event(
    event_type: str,
    user_id: int = None,
    ip_address: str = None,
    details: dict = None,
):
    """Log security-related events."""
    logger = get_logger("security.event")
    logger.warning(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        details=details or {},
    )


def log_db_query(
    model_name: str,
    operation: str,
    duration_ms: float,
    row_count: int = None,
    slow_threshold_ms: float = 100.0,
):
    """Log database queries for performance monitoring."""
    logger = get_logger("db.query")
    is_slow = duration_ms > slow_threshold_ms
    level = "warning" if is_slow else "debug"
    getattr(logger, level)(
        "db_query",
        model_name=model_name,
        operation=operation,
        duration_ms=duration_ms,
        row_count=row_count,
        is_slow=is_slow,
    )
