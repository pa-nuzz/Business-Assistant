from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Workspace, WorkspaceMember, WorkspaceInvitation
from core.services.permission_service import PermissionService
from django.utils import timezone
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


# Workspace Invitation Endpoints
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_invitation(request, workspace_id):
    """Create a workspace invitation."""
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Personal workspaces are private scopes and must never gain members
    if workspace.is_personal:
        return Response(
            {'error': 'Cannot invite members to a Personal workspace'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check permission
    if not PermissionService.has_workspace_permission(
        request.user, workspace_id, 'manage_members'
    ):
        return Response(
            {'error': "You don't have permission to invite members"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    email = request.data.get('email')
    role = request.data.get('role', 'member')
    
    if not email:
        return Response(
            {'error': 'email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    valid_roles = ['admin', 'member', 'viewer']
    if role not in ['admin', 'member', 'viewer']:
        return Response(
            {'error': f"Invalid role. Must be one of: {valid_roles}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check if user exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found. Please ask them to sign up first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already a member
        if WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=user
        ).exists():
            return Response(
                {'error': 'User is already a member of this workspace'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if invitation already exists
        existing = WorkspaceInvitation.objects.filter(
            workspace_id=workspace_id,
            email=email,
            status='pending'
        ).first()
        
        if existing:
            if existing.is_valid():
                return Response(
                    {'error': 'A pending invitation already exists for this email'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Expire the old one
                existing.status = 'expired'
                existing.save(update_fields=['status', 'updated_at'])
        
        # Check inviter can assign this role
        inviter_role = PermissionService.get_user_role_in_workspace(
            request.user, workspace_id
        )
        hierarchy = {'owner': 4, 'admin': 3, 'member': 2, 'viewer': 1}
        if hierarchy.get(inviter_role, 0) <= hierarchy.get(role, 0):
            raise PermissionError(f"Cannot invite users with role {role}")
        
        # Create invitation
        invitation = WorkspaceInvitation.objects.create(
            workspace=workspace,
            email=email,
            role=role,
            invited_by=request.user,
            invited_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        
        logger.info(f"{request.user.username} invited {email} to workspace {workspace_id} as {role}")
        
        return Response({
            'id': str(invitation.id),
            'email': invitation.email,
            'role': invitation.role,
            'token': invitation.token,
            'expires_at': invitation.expires_at.isoformat(),
            'status': invitation.status,
            'invite_url': f"/invite/{invitation.token}",
        }, status=status.HTTP_201_CREATED)
        
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
        logger.exception(f"Failed to create invitation for workspace {workspace_id}")
        return Response(
            {'error': 'Failed to create invitation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_invitations(request, workspace_id):
    """List all invitations for a workspace."""
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    if not PermissionService.has_workspace_permission(
        request.user, workspace_id, 'manage_members'
    ):
        return Response(
            {'error': "You don't have permission to view invitations"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    invitations = WorkspaceInvitation.objects.filter(
        workspace_id=workspace_id
    ).order_by('-created_at')
    
    data = []
    for inv in invitations:
        data.append({
            'id': str(inv.id),
            'email': inv.email,
            'role': inv.role,
            'status': inv.status,
            'invited_by': inv.invited_by.username if inv.invited_by else None,
            'invited_at': inv.invited_at.isoformat(),
            'expires_at': inv.expires_at.isoformat(),
            'accepted_at': inv.accepted_at.isoformat() if inv.accepted_at else None,
            'accepted_by': inv.accepted_by.username if inv.accepted_by else None,
        })
    
    return Response({'invitations': data})


@api_view(["POST"])
@permission_classes([AllowAny])
def accept_invitation(request, token):
    """Accept a workspace invitation."""
    invitation = get_object_or_404(WorkspaceInvitation, token=token)
    
    if not invitation.is_valid():
        return Response(
            {'error': 'This invitation has expired or is no longer valid'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # For unauthenticated users, we'd need them to sign up/login first
    # For now, require authentication
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required', 'login_url': f'/login?next=/invite/{token}'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if the invitation email matches the user
    if request.user.email != invitation.email:
        return Response(
            {'error': 'This invitation is for a different email address'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        member = invitation.accept(request.user)
        return Response({
            'message': 'Invitation accepted successfully',
            'workspace_id': str(invitation.workspace.id),
            'workspace_name': invitation.workspace.name,
            'role': member.role,
        })
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception("Failed to accept invitation")
        return Response(
            {'error': 'Failed to accept invitation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_invitation(request, workspace_id, invitation_id):
    """Revoke a pending invitation."""
    workspace = get_object_or_404(Workspace, id=workspace_id)
    invitation = get_object_or_404(WorkspaceInvitation, id=invitation_id, workspace=workspace)
    
    if not PermissionService.has_workspace_permission(
        request.user, workspace_id, 'manage_members'
    ):
        return Response(
            {'error': "You don't have permission to revoke invitations"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        invitation.revoke(request.user)
        return Response({'message': 'Invitation revoked successfully'})
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except PermissionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.exception("Failed to revoke invitation")
        return Response(
            {'error': 'Failed to revoke invitation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
