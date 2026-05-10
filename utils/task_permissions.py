"""
Shared task permission checks.
Use these instead of duplicating logic in MCP tools and API views.
"""


def can_read_task(task, user) -> bool:
    """User can read the task if they own, created, or are assigned to it."""
    return (
        task.user_id == user.id
        or task.created_by_id == user.id
        or (task.assignee_id is not None and task.assignee_id == user.id)
    )


def can_modify_task(task, user) -> bool:
    """User can modify the task if they created it or are assigned."""
    return (
        task.created_by_id == user.id
        or (task.assignee_id is not None and task.assignee_id == user.id)
    )


def can_delete_task(task, user) -> bool:
    """Only the creator can delete a task."""
    return task.created_by_id == user.id
