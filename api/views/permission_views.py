"""API views for workspace permissions and member management."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Workspace, WorkspaceMember
from core.services.permission_service import PermissionService
import logging

logger = logging.getLogger(__name__)


# Workspace Management
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_workspaces(request):
    """List all workspaces where user is a member."""
    try:
        workspaces = PermissionService.get_user_workspaces(request.user)
        return Response({'workspaces': workspaces})
    except Exception as e:
        logger.exception("Failed to list workspaces")
        return Response(
            {'error': 'Failed to retrieve workspaces'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_workspace(request):
    """Create a new workspace."""
    name = request.data.get('name')
    description = request.data.get('description', '')
    is_public = request.data.get('is_public', False)
    
    if not name:
        return Response(
            {'error': 'name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        workspace = Workspace.objects.create(
            name=name,
            description=description,
            owner=request.user,
            is_public=is_public
        )
        
        # Create owner membership
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=request.user,
            role='owner'
        )
        
        return Response({
            'id': str(workspace.id),
            'name': workspace.name,
            'description': workspace.description,
            'role': 'owner',
            'created_at': workspace.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception("Failed to create workspace")
        return Response(
            {'error': 'Failed to create workspace'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_workspace(request, workspace_id):
    """Get workspace details."""
    try:
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        # Check membership
        member = WorkspaceMember.objects.filter(
            workspace=workspace,
            user=request.user
        ).first()
        
        if not member and not workspace.is_public:
            return Response(
                {'error': 'You are not a member of this workspace'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'id': str(workspace.id),
            'name': workspace.name,
            'description': workspace.description,
            'owner': workspace.owner.username,
            'is_public': workspace.is_public,
            'my_role': member.role if member else None,
            'member_count': workspace.get_member_count(),
            'created_at': workspace.created_at.isoformat(),
        })
    except Exception as e:
        logger.exception(f"Failed to get workspace {workspace_id}")
        return Response(
            {'error': 'Failed to retrieve workspace'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_workspace(request, workspace_id):
    """Update workspace settings."""
    try:
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        # Check permission
        if not PermissionService.has_workspace_permission(
            request.user, workspace_id, 'manage_settings'
        ):
            return Response(
                {'error': "You don't have permission to update this workspace"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update fields
        if 'name' in request.data:
            workspace.name = request.data['name']
        if 'description' in request.data:
            workspace.description = request.data['description']
        if 'is_public' in request.data:
            workspace.is_public = request.data['is_public']
        if 'default_member_role' in request.data:
            workspace.default_member_role = request.data['default_member_role']
        
        workspace.save()
        
        return Response({
            'id': str(workspace.id),
            'name': workspace.name,
            'description': workspace.description,
            'is_public': workspace.is_public,
        })
    except Exception as e:
        logger.exception(f"Failed to update workspace {workspace_id}")
        return Response(
            {'error': 'Failed to update workspace'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_workspace(request, workspace_id):
    """Delete a workspace (owner only)."""
    try:
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        # Only owner can delete
        member = WorkspaceMember.objects.get(
            workspace=workspace,
            user=request.user
        )
        
        if member.role != 'owner':
            return Response(
                {'error': 'Only the owner can delete a workspace'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        workspace.delete()
        return Response({'message': 'Workspace deleted successfully'})
    except WorkspaceMember.DoesNotExist:
        return Response(
            {'error': 'You are not a member of this workspace'},
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.exception(f"Failed to delete workspace {workspace_id}")
        return Response(
            {'error': 'Failed to delete workspace'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Member Management
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_members(request, workspace_id):
    """List all members of a workspace."""
    try:
        members = PermissionService.get_workspace_members(workspace_id, request.user)
        return Response({'members': members})
    except PermissionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.exception(f"Failed to list members for workspace {workspace_id}")
        return Response(
            {'error': 'Failed to retrieve members'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invite_member(request, workspace_id):
    """Invite a new member to the workspace."""
    email = request.data.get('email')
    role = request.data.get('role', 'member')
    
    if not email:
        return Response(
            {'error': 'email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        member = PermissionService.invite_member(
            workspace_id=workspace_id,
            email=email,
            role=role,
            invited_by=request.user
        )
        return Response(member, status=status.HTTP_201_CREATED)
    except PermissionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception(f"Failed to invite member to workspace {workspace_id}")
        return Response(
            {'error': 'Failed to invite member'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_member_role(request, workspace_id, member_id):
    """Update a member's role."""
    new_role = request.data.get('role')
    
    if not new_role:
        return Response(
            {'error': 'role is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        member = PermissionService.update_member_role(
            workspace_id=workspace_id,
            member_id=member_id,
            new_role=new_role,
            updated_by=request.user
        )
        return Response(member)
    except PermissionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.exception(f"Failed to update member role {member_id}")
        return Response(
            {'error': 'Failed to update member role'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_member(request, workspace_id, member_id):
    """Remove a member from the workspace."""
    try:
        success = PermissionService.remove_member(
            workspace_id=workspace_id,
            member_id=member_id,
            removed_by=request.user
        )
        if success:
            return Response({'message': 'Member removed successfully'})
        else:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except PermissionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.exception(f"Failed to remove member {member_id}")
        return Response(
            {'error': 'Failed to remove member'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Permission Checks
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_permission(request, workspace_id):
    """Check if user has a specific permission."""
    permission = request.query_params.get('permission')
    
    if not permission:
        return Response(
            {'error': 'permission query parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    has_perm = PermissionService.has_workspace_permission(
        request.user, workspace_id, permission
    )
    
    return Response({
        'has_permission': has_perm,
        'permission': permission,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def check_resource_permission(request):
    """Check if user can perform an action on a resource."""
    resource_type = request.data.get('resource_type')
    resource_id = request.data.get('resource_id')
    action = request.data.get('action')
    
    if not all([resource_type, resource_id, action]):
        return Response(
            {'error': 'resource_type, resource_id, and action are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    can_manage = PermissionService.can_manage_resource(
        request.user, resource_type, resource_id, action
    )
    
    return Response({
        'can_manage': can_manage,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'action': action,
    })


# Resource Permissions
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def grant_permission(request):
    """Grant a permission on a resource to a user."""
    resource_type = request.data.get('resource_type')
    resource_id = request.data.get('resource_id')
    user_id = request.data.get('user_id')
    permission = request.data.get('permission')
    
    if not all([resource_type, resource_id, user_id, permission]):
        return Response(
            {'error': 'resource_type, resource_id, user_id, and permission are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        PermissionService.grant_resource_permission(
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            permission=permission,
            granted_by=request.user
        )
        return Response({'message': 'Permission granted successfully'})
    except PermissionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.exception("Failed to grant permission")
        return Response(
            {'error': 'Failed to grant permission'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_permission(request):
    """Revoke a permission on a resource from a user."""
    resource_type = request.data.get('resource_type')
    resource_id = request.data.get('resource_id')
    user_id = request.data.get('user_id')
    permission = request.data.get('permission')
    
    if not all([resource_type, resource_id, user_id, permission]):
        return Response(
            {'error': 'resource_type, resource_id, user_id, and permission are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        success = PermissionService.revoke_resource_permission(
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            permission=permission,
            revoked_by=request.user
        )
        if success:
            return Response({'message': 'Permission revoked successfully'})
        else:
            return Response(
                {'error': 'Permission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    except PermissionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.exception("Failed to revoke permission")
        return Response(
            {'error': 'Failed to revoke permission'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
