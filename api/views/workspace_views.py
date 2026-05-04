"""API views for workspace context and AI memory management."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from core.services.workspace_service import WorkspaceService
from core.models import WorkspaceContext
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_workspaces(request):
    """List all workspaces for the authenticated user."""
    service = WorkspaceService(request.user)
    try:
        workspaces = service.list_workspaces()
        return Response({"workspaces": workspaces})
    except Exception as e:
        logger.exception("Failed to list workspaces")
        return Response(
            {"error": "Failed to retrieve workspaces"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_workspace_context(request, workspace_id):
    """Get context for a specific workspace."""
    service = WorkspaceService(request.user)
    try:
        context = service.get_workspace_context(workspace_id)
        if context is None:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(context)
    except Exception as e:
        logger.exception(f"Failed to get workspace context for {workspace_id}")
        return Response(
            {"error": "Failed to retrieve workspace context"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_business_context(request, workspace_id):
    """Update business context for a workspace."""
    service = WorkspaceService(request.user)
    
    if not request.data:
        return Response(
            {"error": "No data provided"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        context = service.update_business_context(workspace_id, **request.data)
        return Response({
            "message": "Business context updated",
            "workspace_id": context.workspace_id,
            "business_context": context.business_context
        })
    except Exception as e:
        logger.exception(f"Failed to update business context for {workspace_id}")
        return Response(
            {"error": "Failed to update business context"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_memory(request, workspace_id):
    """Add a memory entry to a workspace."""
    service = WorkspaceService(request.user)
    
    memory_type = request.data.get("type")
    content = request.data.get("content")
    source_conversation_id = request.data.get("source_conversation_id")
    
    if not memory_type or not content:
        return Response(
            {"error": "type and content are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        memory = service.add_memory(
            workspace_id, 
            memory_type, 
            content, 
            source_conversation_id
        )
        return Response({
            "message": "Memory added",
            "memory": memory
        })
    except Exception as e:
        logger.exception(f"Failed to add memory for {workspace_id}")
        return Response(
            {"error": "Failed to add memory"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_memories(request, workspace_id):
    """Get memories for a workspace, optionally filtered by type."""
    service = WorkspaceService(request.user)
    
    memory_type = request.query_params.get("type")
    limit = int(request.query_params.get("limit", 10))
    
    try:
        memories = service.get_memories(workspace_id, memory_type, limit)
        return Response({
            "memories": memories,
            "count": len(memories)
        })
    except Exception as e:
        logger.exception(f"Failed to get memories for {workspace_id}")
        return Response(
            {"error": "Failed to retrieve memories"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_memory(request, workspace_id, memory_index):
    """Delete a specific memory entry."""
    service = WorkspaceService(request.user)
    
    try:
        success = service.delete_memory(workspace_id, int(memory_index))
        if success:
            return Response({"message": "Memory deleted"})
        return Response(
            {"error": "Memory not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError:
        return Response(
            {"error": "Invalid memory index"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception(f"Failed to delete memory for {workspace_id}")
        return Response(
            {"error": "Failed to delete memory"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_conversation_summary(request, workspace_id):
    """Add a conversation summary for long-term context."""
    service = WorkspaceService(request.user)
    
    conversation_id = request.data.get("conversation_id")
    summary = request.data.get("summary")
    topics = request.data.get("topics", [])
    
    if not conversation_id or not summary:
        return Response(
            {"error": "conversation_id and summary are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        summary_entry = service.add_conversation_summary(
            workspace_id,
            conversation_id,
            summary,
            topics
        )
        return Response({
            "message": "Conversation summary added",
            "summary": summary_entry
        })
    except Exception as e:
        logger.exception(f"Failed to add conversation summary for {workspace_id}")
        return Response(
            {"error": "Failed to add conversation summary"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_preferences(request, workspace_id):
    """Update workspace preferences."""
    service = WorkspaceService(request.user)
    
    if not request.data:
        return Response(
            {"error": "No preferences provided"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        context = service.update_preferences(workspace_id, **request.data)
        return Response({
            "message": "Preferences updated",
            "preferences": context.preferences
        })
    except Exception as e:
        logger.exception(f"Failed to update preferences for {workspace_id}")
        return Response(
            {"error": "Failed to update preferences"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def archive_workspace(request, workspace_id):
    """Archive (soft delete) a workspace."""
    service = WorkspaceService(request.user)
    
    try:
        success = service.archive_workspace(workspace_id)
        if success:
            return Response({"message": "Workspace archived"})
        return Response(
            {"error": "Workspace not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.exception(f"Failed to archive workspace {workspace_id}")
        return Response(
            {"error": "Failed to archive workspace"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
