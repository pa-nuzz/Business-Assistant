"""API views for workspace context and AI memory management.

Security: every workspace-scoped endpoint validates that the authenticated
user is an active member of the requested workspace before touching data.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.services.workspace_service import WorkspaceService, WorkspaceAccessError
import logging

logger = logging.getLogger(__name__)


def _access_error_response(e: WorkspaceAccessError) -> Response:
    """Build an error response from a WorkspaceAccessError."""
    return Response({"error": e.message}, status=e.status_code)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_workspaces(request):
    """List all workspaces for the authenticated user (memberships)."""
    service = WorkspaceService(request.user)
    try:
        workspaces = service.list_workspaces()
        return Response({"workspaces": workspaces})
    except Exception:
        logger.exception("Failed to list workspaces")
        return Response(
            {"error": "Failed to retrieve workspaces"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_workspace_context(request, workspace_id):
    """Get shared context for a workspace (membership required)."""
    service = WorkspaceService(request.user)
    try:
        context = service.get_workspace_context(workspace_id)
        if context is None:
            return Response(
                {"error": "Workspace context not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(context)
    except WorkspaceAccessError as e:
        return _access_error_response(e)
    except Exception:
        logger.exception(f"Failed to get workspace context for {workspace_id}")
        return Response(
            {"error": "Failed to retrieve workspace context"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_business_context(request, workspace_id):
    """Update shared business context for a workspace (update permission required)."""
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
            "workspace_id": str(context.workspace.id),
            "business_context": context.business_context
        })
    except WorkspaceAccessError as e:
        return _access_error_response(e)
    except Exception:
        logger.exception(f"Failed to update business context for {workspace_id}")
        return Response(
            {"error": "Failed to update business context"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_memory(request, workspace_id):
    """Add a shared memory entry to a workspace (update permission required)."""
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
    except WorkspaceAccessError as e:
        return _access_error_response(e)
    except Exception:
        logger.exception(f"Failed to add memory for {workspace_id}")
        return Response(
            {"error": "Failed to add memory"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_memories(request, workspace_id):
    """Get shared memories for a workspace (membership required)."""
    service = WorkspaceService(request.user)

    memory_type = request.query_params.get("type")
    limit = int(request.query_params.get("limit", 10))

    try:
        memories = service.get_memories(workspace_id, memory_type, limit)
        return Response({
            "memories": memories,
            "count": len(memories)
        })
    except WorkspaceAccessError as e:
        return _access_error_response(e)
    except Exception:
        logger.exception(f"Failed to get memories for {workspace_id}")
        return Response(
            {"error": "Failed to retrieve memories"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_memory(request, workspace_id, memory_index):
    """Delete a specific shared memory entry (update permission required)."""
    service = WorkspaceService(request.user)

    try:
        success = service.delete_memory(workspace_id, int(memory_index))
        if success:
            return Response({"message": "Memory deleted"})
        return Response(
            {"error": "Memory not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except WorkspaceAccessError as e:
        return _access_error_response(e)
    except ValueError:
        return Response(
            {"error": "Invalid memory index"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception:
        logger.exception(f"Failed to delete memory for {workspace_id}")
        return Response(
            {"error": "Failed to delete memory"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_conversation_summary(request, workspace_id):
    """Add a conversation summary to a workspace's shared context (update permission)."""
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
    except WorkspaceAccessError as e:
        return _access_error_response(e)
    except Exception:
        logger.exception(f"Failed to add conversation summary for {workspace_id}")
        return Response(
            {"error": "Failed to add conversation summary"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_preferences(request, workspace_id):
    """Update shared workspace preferences (update permission required)."""
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
    except WorkspaceAccessError as e:
        return _access_error_response(e)
    except Exception:
        logger.exception(f"Failed to update preferences for {workspace_id}")
        return Response(
            {"error": "Failed to update preferences"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def archive_workspace(request, workspace_id):
    """Deactivate a workspace context (owner only: manage_settings permission)."""
    service = WorkspaceService(request.user)

    try:
        success = service.archive_workspace(workspace_id)
        if success:
            return Response({"message": "Workspace archived"})
        return Response(
            {"error": "Workspace context not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except WorkspaceAccessError as e:
        return _access_error_response(e)
    except Exception:
        logger.exception(f"Failed to archive workspace {workspace_id}")
        return Response(
            {"error": "Failed to archive workspace"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
