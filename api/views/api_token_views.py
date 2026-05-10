"""API views for API token management (for Zapier/Make integrations)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import APIToken
import hashlib
import secrets
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_api_tokens(request):
    """List user's API tokens."""
    tokens = APIToken.objects.filter(user=request.user).order_by('-created_at')
    
    return Response({
        'tokens': [
            {
                'id': str(t.id),
                'name': t.name,
                'scopes': t.scopes,
                'is_active': t.is_active,
                'last_used_at': t.last_used_at.isoformat() if t.last_used_at else None,
                'request_count': t.request_count,
                'created_at': t.created_at.isoformat(),
                'expires_at': t.expires_at.isoformat() if t.expires_at else None,
                'is_expired': t.expires_at and t.expires_at < datetime.now() if t.expires_at else False,
            }
            for t in tokens
        ]
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_api_token(request):
    """Create a new API token."""
    name = request.data.get('name')
    scopes = request.data.get('scopes', ['tasks:read', 'documents:read'])
    expires_days = request.data.get('expires_days', 365)
    
    if not name:
        return Response(
            {'error': 'name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate token (only shown once)
    raw_token = f"aeiou_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Calculate expiry
    expires_at = datetime.now() + timedelta(days=expires_days) if expires_days else None
    
    token = APIToken.objects.create(
        user=request.user,
        name=name,
        token_hash=token_hash,
        scopes=scopes,
        expires_at=expires_at
    )
    
    logger.info(f"Created API token '{name}' for user {request.user.username}")
    
    return Response({
        'id': str(token.id),
        'name': token.name,
        'token': raw_token,  # Only shown once!
        'scopes': token.scopes,
        'expires_at': token.expires_at.isoformat() if token.expires_at else None,
        'created_at': token.created_at.isoformat(),
        'warning': 'This token will only be shown once. Store it securely.',
    }, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def revoke_api_token(request, token_id):
    """Revoke an API token."""
    try:
        token = APIToken.objects.get(id=token_id, user=request.user)
        token.is_active = False
        token.save()
        return Response({'message': 'Token revoked successfully'})
    except APIToken.DoesNotExist:
        return Response(
            {'error': 'Token not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# Zapier/Make Integration Endpoints

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def zapier_triggers(request):
    """List available Zapier triggers."""
    return Response({
        'triggers': [
            {
                'key': 'task_created',
                'label': 'New Task Created',
                'description': 'Triggers when a new task is created',
                'event_type': 'task.created',
            },
            {
                'key': 'task_completed',
                'label': 'Task Completed',
                'description': 'Triggers when a task is marked as done',
                'event_type': 'task.completed',
            },
            {
                'key': 'document_created',
                'label': 'New Document Added',
                'description': 'Triggers when a new document is uploaded',
                'event_type': 'document.created',
            },
            {
                'key': 'comment_created',
                'label': 'New Comment',
                'description': 'Triggers when a comment is added to a task',
                'event_type': 'comment.created',
            },
        ]
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def zapier_actions(request):
    """List available Zapier actions."""
    return Response({
        'actions': [
            {
                'key': 'create_task',
                'label': 'Create Task',
                'description': 'Creates a new task in your workspace',
                'endpoint': '/api/v1/tasks/',
                'method': 'POST',
                'fields': [
                    {'key': 'title', 'label': 'Title', 'type': 'string', 'required': True},
                    {'key': 'description', 'label': 'Description', 'type': 'text', 'required': False},
                    {'key': 'status', 'label': 'Status', 'type': 'string', 'choices': ['todo', 'in_progress', 'done'], 'default': 'todo'},
                    {'key': 'priority', 'label': 'Priority', 'type': 'string', 'choices': ['low', 'medium', 'high'], 'default': 'medium'},
                    {'key': 'due_date', 'label': 'Due Date', 'type': 'date', 'required': False},
                    {'key': 'tags', 'label': 'Tags', 'type': 'array', 'required': False},
                ]
            },
            {
                'key': 'update_task',
                'label': 'Update Task',
                'description': 'Updates an existing task',
                'endpoint': '/api/v1/tasks/{id}/',
                'method': 'PUT',
                'fields': [
                    {'key': 'id', 'label': 'Task ID', 'type': 'string', 'required': True},
                    {'key': 'title', 'label': 'Title', 'type': 'string', 'required': False},
                    {'key': 'status', 'label': 'Status', 'type': 'string', 'choices': ['todo', 'in_progress', 'done'], 'required': False},
                ]
            },
            {
                'key': 'create_document',
                'label': 'Upload Document',
                'description': 'Uploads a document from URL or file',
                'endpoint': '/api/v1/documents/',
                'method': 'POST',
                'fields': [
                    {'key': 'title', 'label': 'Title', 'type': 'string', 'required': True},
                    {'key': 'file_url', 'label': 'File URL', 'type': 'string', 'required': True},
                ]
            },
            {
                'key': 'add_comment',
                'label': 'Add Comment to Task',
                'description': 'Adds a comment to a task',
                'endpoint': '/api/v1/tasks/{task_id}/comments/add/',
                'method': 'POST',
                'fields': [
                    {'key': 'task_id', 'label': 'Task ID', 'type': 'string', 'required': True},
                    {'key': 'content', 'label': 'Comment', 'type': 'text', 'required': True},
                ]
            },
        ]
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def zapier_sample_data(request, trigger_key):
    """Return sample data for Zapier trigger testing."""
    samples = {
        'task_created': {
            'id': 'sample-task-id',
            'title': 'Sample Task from Zapier',
            'description': 'This is a sample task created by Zapier',
            'status': 'todo',
            'priority': 'medium',
            'due_date': '2024-12-31',
            'tags': ['zapier', 'sample'],
            'assigned_to': 'user@example.com',
            'created_by': 'zapier@example.com',
            'created_at': datetime.now().isoformat(),
        },
        'task_completed': {
            'id': 'sample-task-id',
            'title': 'Completed Task',
            'status': 'done',
            'completed_at': datetime.now().isoformat(),
            'completed_by': 'user@example.com',
        },
        'document_created': {
            'id': 'sample-doc-id',
            'title': 'Sample Document',
            'file_type': 'pdf',
            'size_bytes': 1024000,
            'created_by': 'zapier@example.com',
            'created_at': datetime.now().isoformat(),
        },
    }
    
    return Response(samples.get(trigger_key, {}))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def integration_status(request):
    """Get integration status and available integrations."""
    return Response({
        'integrations': [
            {
                'name': 'Zapier',
                'status': 'available',
                'description': 'Connect AEIOU AI with 5000+ apps via Zapier',
                'setup_url': '/integrations/zapier/setup/',
                'requires_webhook': True,
            },
            {
                'name': 'Make (Integromat)',
                'status': 'available',
                'description': 'Build custom automations with Make',
                'setup_url': '/integrations/make/setup/',
                'requires_webhook': True,
            },
            {
                'name': 'Slack',
                'status': 'coming_soon',
                'description': 'Get notifications and interact via Slack',
            },
            {
                'name': 'GitHub',
                'status': 'coming_soon',
                'description': 'Link tasks to GitHub issues and PRs',
            },
        ],
        'webhook_count': request.user.webhooks.filter(is_active=True).count(),
        'api_token_count': request.user.api_tokens.filter(is_active=True).count(),
    })
