"""
Audit logging utilities for security-sensitive actions.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Create audit logger
audit_logger = logging.getLogger('audit')


def log_audit_action(
    user,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> None:
    """
    Log a security-sensitive action for audit trail.
    
    Args:
        user: The user performing the action
        action: Type of action (login, logout, create, update, delete, etc.)
        resource_type: Type of resource being accessed (user, document, task, etc.)
        resource_id: ID of the resource
        details: Additional details about the action
        ip_address: IP address of the requester
    """
    try:
        audit_logger.info({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': getattr(user, 'id', None),
            'username': getattr(user, 'username', 'anonymous'),
            'action': action,
            'resource_type': resource_type,
            'resource_id': str(resource_id),
            'ip_address': ip_address,
            'details': details or {},
        })
    except Exception as e:
        # Fail silently - don't break the application if audit logging fails
        logging.getLogger(__name__).error(f"Failed to write audit log: {e}")


def log_document_access(user, document, action: str = 'view', ip_address: Optional[str] = None) -> None:
    """Log document access for audit trail."""
    log_audit_action(
        user=user,
        action=action,
        resource_type='document',
        resource_id=str(document.id),
        details={'title': document.title},
        ip_address=ip_address
    )


def log_task_action(user, task, action: str, ip_address: Optional[str] = None) -> None:
    """Log task-related actions."""
    log_audit_action(
        user=user,
        action=action,
        resource_type='task',
        resource_id=str(task.id),
        details={'title': task.title, 'status': task.status},
        ip_address=ip_address
    )


def log_auth_action(user, action: str, success: bool = True, ip_address: Optional[str] = None, details: Optional[Dict] = None) -> None:
    """Log authentication-related actions."""
    log_audit_action(
        user=user,
        action=f"{'successful_' if success else 'failed_'}{action}",
        resource_type='auth',
        resource_id=str(getattr(user, 'id', 'unknown')),
        details={**(details or {}), 'success': success},
        ip_address=ip_address
    )
