"""
Audit logging service for security and compliance.
Provides centralized audit trail for all critical operations.
"""
import logging
from typing import Dict, Optional, Any
from django.contrib.auth.models import User
from core.models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogService:
    """Service for creating and managing audit log entries."""
    
    @staticmethod
    def log(
        event_type: str,
        user: Optional[User] = None,
        severity: str = "info",
        description: str = "",
        resource_type: str = "",
        resource_id: str = "",
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        request=None,
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            event_type: Type of event from AuditLog.EVENT_TYPES
            user: User who performed the action
            severity: Severity level (info, warning, critical)
            description: Human-readable description
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            metadata: Additional JSON metadata
            request: Django request object for extracting context
            
        Returns:
            Created AuditLog instance
        """
        try:
            # Extract request context if available
            ip_address = None
            user_agent = ""
            request_id = ""
            
            if request:
                # Get IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0].strip()
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
                
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                request_id = request.META.get('HTTP_X_REQUEST_ID', '')
            
            # Create the audit log entry
            audit_log = AuditLog.objects.create(
                user=user,
                event_type=event_type,
                severity=severity,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else "",
                old_values=old_values,
                new_values=new_values,
                metadata=metadata or {},
            )
            
            logger.info(f"Audit log created: {event_type} by {user.username if user else 'system'}")
            return audit_log
            
        except Exception as e:
            logger.exception(f"Failed to create audit log: {e}")
            # Don't raise - audit logging should not break functionality
            return None
    
    @staticmethod
    def log_auth_event(
        event_type: str,
        user: Optional[User] = None,
        success: bool = True,
        description: str = "",
        request=None,
        metadata: Optional[Dict] = None,
    ) -> AuditLog:
        """Log authentication-related events."""
        severity = "info" if success else "warning"
        if event_type in ["login_failed"] and user is None:
            severity = "warning"
        
        return AuditLogService.log(
            event_type=event_type,
            user=user,
            severity=severity,
            description=description or f"{event_type} {'successful' if success else 'failed'}",
            metadata=metadata,
            request=request,
        )
    
    @staticmethod
    def log_document_event(
        event_type: str,
        user: User,
        document_id: str,
        document_title: str = "",
        request=None,
        metadata: Optional[Dict] = None,
    ) -> AuditLog:
        """Log document-related events."""
        return AuditLogService.log(
            event_type=event_type,
            user=user,
            severity="info",
            description=f"Document '{document_title}' {event_type.replace('document_', '')}",
            resource_type="document",
            resource_id=document_id,
            metadata=metadata,
            request=request,
        )
    
    @staticmethod
    def log_task_event(
        event_type: str,
        user: User,
        task_id: str,
        task_title: str = "",
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        request=None,
    ) -> AuditLog:
        """Log task-related events."""
        severity = "warning" if event_type == "task_delete" else "info"
        
        return AuditLogService.log(
            event_type=event_type,
            user=user,
            severity=severity,
            description=f"Task '{task_title}' {event_type.replace('task_', '')}",
            resource_type="task",
            resource_id=task_id,
            old_values=old_values,
            new_values=new_values,
            request=request,
        )
    
    @staticmethod
    def log_ai_event(
        event_type: str,
        user: User,
        conversation_id: str = "",
        request=None,
        metadata: Optional[Dict] = None,
    ) -> AuditLog:
        """Log AI-related events."""
        return AuditLogService.log(
            event_type=event_type,
            user=user,
            severity="info",
            description=f"AI {event_type.replace('ai_', '')}",
            resource_type="conversation",
            resource_id=conversation_id,
            metadata=metadata,
            request=request,
        )
    
    @staticmethod
    def log_permission_event(
        event_type: str,
        user: User,
        target_user_id: str = "",
        permission: str = "",
        request=None,
    ) -> AuditLog:
        """Log permission-related events."""
        return AuditLogService.log(
            event_type=event_type,
            user=user,
            severity="warning",  # Permission changes are always notable
            description=f"Permission '{permission}' {event_type.replace('permission_', '')} for user {target_user_id}",
            resource_type="permission",
            resource_id=target_user_id,
            request=request,
        )
    
    @staticmethod
    def get_recent_events(
        user: Optional[User] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ):
        """Get recent audit log events with optional filtering."""
        queryset = AuditLog.objects.all()
        
        if user:
            queryset = queryset.filter(user=user)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset[:limit]
