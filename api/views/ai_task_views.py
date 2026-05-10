"""API views for AI-Generated Tasks."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Conversation, Document
from core.services.ai_task_service import AITaskGenerationService
import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_tasks_from_chat(request, conversation_id):
    """
    Generate task suggestions from a chat message.
    
    Query params:
        auto_create: If 'true', automatically create tasks (default: false)
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    message_content = request.data.get('message_content', '')
    auto_create = request.query_params.get('auto_create', 'false').lower() == 'true'
    
    if not message_content:
        return Response(
            {'error': 'message_content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    service = AITaskGenerationService(request.user)
    
    try:
        result = service.generate_tasks_from_chat(
            conversation=conversation,
            message_content=message_content,
            auto_create=auto_create
        )
        return Response(result)
    except Exception as e:
        logger.exception(f"AI task generation from chat failed for {conversation_id}")
        return Response(
            {'error': 'Task generation failed', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_tasks_from_document(request, document_id):
    """
    Generate task suggestions from a document.
    
    Query params:
        auto_create: If 'true', automatically create tasks (default: false)
    """
    document = get_object_or_404(Document, id=document_id, user=request.user)
    auto_create = request.query_params.get('auto_create', 'false').lower() == 'true'
    
    service = AITaskGenerationService(request.user)
    
    try:
        result = service.generate_tasks_from_document(
            document=document,
            auto_create=auto_create
        )
        return Response(result)
    except Exception as e:
        logger.exception(f"AI task generation from document failed for {document_id}")
        return Response(
            {'error': 'Task generation failed', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_pending_ai_tasks(request):
    """Get all pending AI-generated tasks awaiting review."""
    service = AITaskGenerationService(request.user)
    
    try:
        tasks = service.get_pending_ai_tasks()
        return Response({
            'count': len(tasks),
            'tasks': tasks
        })
    except Exception as e:
        logger.exception("Failed to get pending AI tasks")
        return Response(
            {'error': 'Failed to retrieve tasks'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_ai_task(request, task_id):
    """Accept an AI-generated task (mark as reviewed)."""
    service = AITaskGenerationService(request.user)
    
    try:
        success = service.accept_ai_task(task_id)
        if success:
            return Response({'message': 'Task accepted', 'task_id': task_id})
        else:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        logger.exception(f"Failed to accept AI task {task_id}")
        return Response(
            {'error': 'Failed to accept task'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_ai_task(request, task_id):
    """Reject and delete an AI-generated task."""
    service = AITaskGenerationService(request.user)
    
    try:
        success = service.reject_ai_task(task_id)
        if success:
            return Response({'message': 'Task rejected and removed', 'task_id': task_id})
        else:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        logger.exception(f"Failed to reject AI task {task_id}")
        return Response(
            {'error': 'Failed to reject task'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
