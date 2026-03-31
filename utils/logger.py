"""
Logging utilities. Wraps structlog for consistent, searchable log output.
In production on Render, logs are sent to the dashboard automatically.
"""
import logging
import structlog


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
