"""API views for webhook management."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Webhook, WebhookDelivery
from core.services.webhook_service import WebhookService
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_webhooks(request):
    """List user's webhooks."""
    webhooks = Webhook.objects.filter(user=request.user).order_by('-created_at')
    
    return Response({
        'webhooks': [
            {
                'id': str(w.id),
                'name': w.name,
                'url': w.url,
                'events': w.events,
                'is_active': w.is_active,
                'last_delivered_at': w.last_delivered_at.isoformat() if w.last_delivered_at else None,
                'last_status_code': w.last_status_code,
                'failure_count': w.failure_count,
                'created_at': w.created_at.isoformat(),
            }
            for w in webhooks
        ]
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_webhook(request):
    """Create a new webhook subscription."""
    name = request.data.get('name')
    url = request.data.get('url')
    events = request.data.get('events', [])
    workspace_id = request.data.get('workspace_id')
    headers = request.data.get('headers', {})
    
    if not name or not url or not events:
        return Response(
            {'error': 'name, url, and events are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return Response(
            {'error': 'URL must start with http:// or https://'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        workspace = None
        if workspace_id:
            from core.models import Workspace, WorkspaceMember
            workspace = get_object_or_404(Workspace, id=workspace_id)
            # Check membership
            if not WorkspaceMember.objects.filter(
                workspace=workspace,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You are not a member of this workspace'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        webhook = WebhookService.create_webhook(
            user=request.user,
            name=name,
            url=url,
            events=events,
            workspace=workspace,
            headers=headers
        )
        
        return Response({
            'id': str(webhook.id),
            'name': webhook.name,
            'url': webhook.url,
            'events': webhook.events,
            'secret': webhook.secret,  # Only shown on creation
            'is_active': webhook.is_active,
            'created_at': webhook.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception("Failed to create webhook")
        return Response(
            {'error': 'Failed to create webhook'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_webhook(request, webhook_id):
    """Get webhook details."""
    webhook = get_object_or_404(Webhook, id=webhook_id, user=request.user)
    
    return Response({
        'id': str(webhook.id),
        'name': webhook.name,
        'url': webhook.url,
        'events': webhook.events,
        'headers': webhook.headers,
        'is_active': webhook.is_active,
        'retry_count': webhook.retry_count,
        'timeout_seconds': webhook.timeout_seconds,
        'last_delivered_at': webhook.last_delivered_at.isoformat() if webhook.last_delivered_at else None,
        'last_status_code': webhook.last_status_code,
        'failure_count': webhook.failure_count,
        'created_at': webhook.created_at.isoformat(),
    })


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_webhook(request, webhook_id):
    """Update webhook settings."""
    webhook = get_object_or_404(Webhook, id=webhook_id, user=request.user)
    
    if 'name' in request.data:
        webhook.name = request.data['name']
    if 'url' in request.data:
        webhook.url = request.data['url']
    if 'events' in request.data:
        webhook.events = request.data['events']
    if 'headers' in request.data:
        webhook.headers = request.data['headers']
    if 'is_active' in request.data:
        webhook.is_active = request.data['is_active']
    if 'retry_count' in request.data:
        webhook.retry_count = request.data['retry_count']
    if 'timeout_seconds' in request.data:
        webhook.timeout_seconds = request.data['timeout_seconds']
    
    webhook.save()
    
    return Response({
        'id': str(webhook.id),
        'name': webhook.name,
        'url': webhook.url,
        'events': webhook.events,
        'is_active': webhook.is_active,
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_webhook(request, webhook_id):
    """Delete a webhook."""
    success = WebhookService.delete_webhook(webhook_id, request.user)
    if success:
        return Response({'message': 'Webhook deleted successfully'})
    else:
        return Response(
            {'error': 'Webhook not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_webhook(request, webhook_id):
    """Send a test event to webhook."""
    webhook = get_object_or_404(Webhook, id=webhook_id, user=request.user)
    
    # Create test delivery
    from core.services.webhook_service import deliver_webhook
    
    delivery = WebhookDelivery.objects.create(
        webhook=webhook,
        event_type='test.event',
        payload={
            'message': 'This is a test event from AEIOU AI',
            'timestamp': datetime.utcnow().isoformat(),
        },
        status=WebhookDelivery.PENDING
    )
    
    # Trigger immediate delivery
    deliver_webhook.delay(delivery.id)
    
    return Response({
        'message': 'Test event sent',
        'delivery_id': str(delivery.id),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_deliveries(request, webhook_id):
    """List delivery attempts for a webhook."""
    webhook = get_object_or_404(Webhook, id=webhook_id, user=request.user)
    
    limit = int(request.query_params.get('limit', 50))
    offset = int(request.query_params.get('offset', 0))
    
    deliveries = WebhookDelivery.objects.filter(
        webhook=webhook
    ).order_by('-started_at')[offset:offset + limit]
    
    return Response({
        'deliveries': [
            {
                'id': str(d.id),
                'event_type': d.event_type,
                'status': d.status,
                'status_code': d.status_code,
                'attempt_number': d.attempt_number,
                'duration_ms': d.duration_ms,
                'error_message': d.error_message,
                'started_at': d.started_at.isoformat(),
                'completed_at': d.completed_at.isoformat() if d.completed_at else None,
            }
            for d in deliveries
        ],
        'total': WebhookDelivery.objects.filter(webhook=webhook).count()
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def regenerate_secret(request, webhook_id):
    """Regenerate webhook secret."""
    webhook = get_object_or_404(Webhook, id=webhook_id, user=request.user)
    
    import hashlib
    from datetime import datetime
    
    webhook.secret = hashlib.sha256(
        f"{request.user.id}:{datetime.now().isoformat()}".encode()
    ).hexdigest()[:32]
    webhook.save()
    
    return Response({
        'id': str(webhook.id),
        'secret': webhook.secret,
        'message': 'Secret regenerated. Update your integration immediately.',
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_available_events(request):
    """List available webhook event types."""
    return Response({
        'events': [
            {'value': e[0], 'label': e[1]}
            for e in Webhook.EVENT_TYPES
        ]
    })


from datetime import datetime
