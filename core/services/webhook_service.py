"""Webhook Service - Event subscriptions with delivery retry and HMAC signing."""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
from django.conf import settings
from celery import shared_task
from core.models import Webhook, WebhookDelivery, Task, Document, Conversation

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for managing webhook subscriptions and deliveries."""

    @staticmethod
    def create_webhook(
        user,
        name: str,
        url: str,
        events: List[str],
        workspace=None,
        headers: Dict[str, str] = None,
        secret: str = None
    ) -> Webhook:
        """Create a new webhook subscription."""
        # Validate events
        valid_events = [e[0] for e in Webhook.EVENT_TYPES]
        invalid = [e for e in events if e not in valid_events]
        if invalid:
            raise ValueError(f"Invalid events: {invalid}. Valid: {valid_events}")
        
        # Generate secret if not provided
        if not secret:
            secret = hashlib.sha256(
                f"{user.id}:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:32]
        
        webhook = Webhook.objects.create(
            user=user,
            workspace=workspace,
            name=name,
            url=url,
            events=events,
            secret=secret,
            headers=headers or {}
        )
        
        logger.info(f"Created webhook '{name}' for user {user.username}")
        return webhook

    @staticmethod
    def delete_webhook(webhook_id: str, user) -> bool:
        """Delete a webhook subscription."""
        try:
            webhook = Webhook.objects.get(id=webhook_id, user=user)
            webhook.delete()
            logger.info(f"Deleted webhook {webhook_id}")
            return True
        except Webhook.DoesNotExist:
            return False

    @staticmethod
    def trigger_event(event_type: str, payload: Dict[str, Any], workspace=None):
        """Trigger an event to all subscribed webhooks."""
        # Find matching webhooks
        webhooks = Webhook.objects.filter(
            events__contains=[event_type],
            is_active=True
        )
        
        if workspace:
            webhooks = webhooks.filter(workspace=workspace)
        
        for webhook in webhooks:
            # Create delivery record
            delivery = WebhookDelivery.objects.create(
                webhook=webhook,
                event_type=event_type,
                payload=payload,
                status=WebhookDelivery.PENDING
            )
            
            # Queue for delivery
            deliver_webhook.delay(delivery.id)
        
        logger.debug(f"Triggered {event_type} to {webhooks.count()} webhooks")

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_signature(payload: str, secret: str, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = WebhookService.generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)


@shared_task(bind=True, max_retries=3)
def deliver_webhook(self, delivery_id: str):
    """Deliver webhook with retry logic."""
    try:
        delivery = WebhookDelivery.objects.select_related('webhook').get(id=delivery_id)
        webhook = delivery.webhook
        
        # Prepare payload
        payload = {
            'event': delivery.event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': delivery.payload,
        }
        payload_json = json.dumps(payload, default=str)
        
        # Generate signature
        signature = WebhookService.generate_signature(payload_json, webhook.secret)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Event': delivery.event_type,
            'X-Webhook-ID': str(delivery.id),
            'User-Agent': 'AEIOU-Webhook/1.0',
        }
        headers.update(webhook.headers)
        
        # Update delivery attempt
        delivery.attempt_number = self.request.retries + 1
        delivery.status = WebhookDelivery.RETRYING
        delivery.save()
        
        # Send request
        started_at = datetime.utcnow()
        try:
            response = requests.post(
                webhook.url,
                data=payload_json,
                headers=headers,
                timeout=webhook.timeout_seconds,
                allow_redirects=False
            )
            
            delivery.status_code = response.status_code
            delivery.response_body = response.text[:10000]  # Limit response size
            
            if response.status_code >= 200 and response.status_code < 300:
                delivery.status = WebhookDelivery.SUCCESS
                webhook.last_delivered_at = datetime.now()
                webhook.last_status_code = response.status_code
                webhook.failure_count = 0
            else:
                delivery.status = WebhookDelivery.FAILED
                delivery.error_message = f"HTTP {response.status_code}"
                webhook.failure_count += 1
                
        except requests.exceptions.Timeout:
            delivery.status = WebhookDelivery.FAILED
            delivery.error_message = "Request timeout"
            webhook.failure_count += 1
            
        except requests.exceptions.RequestException as e:
            delivery.status = WebhookDelivery.FAILED
            delivery.error_message = str(e)[:500]
            webhook.failure_count += 1
        
        # Calculate duration
        delivery.completed_at = datetime.utcnow()
        duration = (delivery.completed_at - started_at).total_seconds() * 1000
        delivery.duration_ms = int(duration)
        
        delivery.save()
        webhook.save()
        
        # Retry if failed and retries remaining
        if delivery.status == WebhookDelivery.FAILED:
            if self.request.retries < webhook.retry_count:
                retry_in = 2 ** self.request.retries * 60  # Exponential backoff
                logger.warning(f"Webhook {webhook.id} failed, retrying in {retry_in}s")
                raise self.retry(countdown=retry_in)
            else:
                logger.error(f"Webhook {webhook.id} failed after {webhook.retry_count} attempts")
        
    except WebhookDelivery.DoesNotExist:
        logger.error(f"Delivery {delivery_id} not found")
    except Exception as e:
        logger.exception(f"Failed to deliver webhook {delivery_id}")


def notify_task_created(task: Task):
    """Notify webhooks about task creation."""
    WebhookService.trigger_event('task.created', {
        'id': str(task.id),
        'title': task.title,
        'status': task.status,
        'priority': task.priority,
        'assigned_to': task.assigned_to.username if task.assigned_to else None,
        'created_by': task.user.username,
        'created_at': task.created_at.isoformat(),
    }, task.workspace)


def notify_task_updated(task: Task, changes: Dict[str, Any]):
    """Notify webhooks about task update."""
    WebhookService.trigger_event('task.updated', {
        'id': str(task.id),
        'title': task.title,
        'changes': changes,
        'updated_at': task.updated_at.isoformat(),
    }, task.workspace)


def notify_task_deleted(task_id: str, workspace=None):
    """Notify webhooks about task deletion."""
    WebhookService.trigger_event('task.deleted', {
        'id': task_id,
        'deleted_at': datetime.utcnow().isoformat(),
    }, workspace)


def notify_task_completed(task: Task):
    """Notify webhooks about task completion."""
    WebhookService.trigger_event('task.completed', {
        'id': str(task.id),
        'title': task.title,
        'completed_at': datetime.utcnow().isoformat(),
        'completed_by': task.user.username,
    }, task.workspace)


def notify_document_created(doc: Document):
    """Notify webhooks about document creation."""
    WebhookService.trigger_event('document.created', {
        'id': str(doc.id),
        'title': doc.title,
        'file_type': doc.file_type,
        'size_bytes': doc.file_size if hasattr(doc, 'file_size') else None,
        'created_by': doc.user.username,
        'created_at': doc.created_at.isoformat(),
    }, doc.workspace)
