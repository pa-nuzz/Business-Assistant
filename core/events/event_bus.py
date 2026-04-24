"""
Event bus for decoupled communication between components.
Enables event-driven architecture for async processing.
"""
import logging
from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Base event class."""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    correlation_id: str = None


class EventBus:
    """
    Simple in-memory event bus for decoupled communication.
    In production, this would be replaced with Redis/Celery for distributed events.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Callback function to remove
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed from event: {event_type}")
    
    def publish(self, event_type: str, data: Dict[str, Any], source: str = "system") -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event to publish
            data: Event data
            source: Source of the event
        """
        event = Event(
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify subscribers
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.exception(f"Event handler failed for {event_type}: {e}")
        
        logger.info(f"Published event: {event_type} from {source}")
    
    def get_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]


# Global event bus instance
event_bus = EventBus()


# Event type constants
class EventTypes:
    """Standard event types for the application."""
    
    # User events
    USER_REGISTERED = "user.registered"
    USER_VERIFIED = "user.verified"
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    USER_PASSWORD_RESET = "user.password_reset"
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    TASK_ASSIGNED = "task.assigned"
    
    # Document events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_DELETED = "document.deleted"
    
    # Chat events
    MESSAGE_SENT = "message.sent"
    CONVERSATION_CREATED = "conversation.created"
    
    # Notification events
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_READ = "notification.read"


# Event handlers
def log_event_handler(event: Event) -> None:
    """Default handler that logs all events."""
    logger.info(
        f"Event: {event.event_type} | Source: {event.source} | "
        f"Data: {json.dumps(event.data, default=str)[:200]}"
    )


# Subscribe default handler to all events
for event_type in dir(EventTypes):
    if not event_type.startswith('_'):
        event_bus.subscribe(getattr(EventTypes, event_type), log_event_handler)
