"""Permission Service - Role-based access control for workspaces and resources."""
from typing import Optional, List, Dict, Any
from django.contrib.auth.models import User
from core.models import (
    Workspace, WorkspaceMember, ResourcePermission,
    Task, Document, Conversation
)
import logging

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for checking and managing permissions."""

    @staticmethod
    def get_user_role_in_workspace(user: User, workspace_id: str) -> Optional[str]:
        """Get user's role in a workspace."""
        try:
            member = WorkspaceMember.objects.get(
                workspace_id=workspace_id,
                user=user
            )
            return member.role
        except WorkspaceMember.DoesNotExist:
            return None

    @staticmethod
    def has_workspace_permission(
        user: User,
        workspace_id: str,
        permission: str
    ) -> bool:
        """Check if user has a specific permission in a workspace."""
        try:
            member = WorkspaceMember.objects.get(
                workspace_id=workspace_id,
                user=user
            )
            return member.has_permission(permission)
        except WorkspaceMember.DoesNotExist:
            return False

    @staticmethod
    def can_manage_resource(
        user: User,
        resource_type: str,
        resource_id: str,
        action: str
    ) -> bool:
        """Check if user can perform an action on a resource."""
        # Get the resource
        resource = PermissionService._get_resource(resource_type, resource_id)
        if not resource:
            return False

        # Resource owner always has full access
        if hasattr(resource, 'user') and resource.user == user:
            return True

        # Check if user is assigned to the task
        if resource_type == 'task' and hasattr(resource, 'assigned_to'):
            if resource.assigned_to == user:
                return action in ['read', 'update', 'delete_own']

        # Check workspace permissions
        if hasattr(resource, 'workspace') and resource.workspace:
            if PermissionService.has_workspace_permission(
                user, str(resource.workspace.id), action
            ):
                return True

        # Check specific resource permissions
        try:
            perm = ResourcePermission.objects.get(
                resource_type=resource_type,
                resource_id=resource_id,
                user=user,
                permission=action
            )
            return True
        except ResourcePermission.DoesNotExist:
            pass

        return False

    @staticmethod
    def _get_resource(resource_type: str, resource_id: str):
        """Get resource by type and ID."""
        try:
            if resource_type == 'task':
                return Task.objects.get(id=resource_id)
            elif resource_type == 'document':
                return Document.objects.get(id=resource_id)
            elif resource_type == 'conversation':
                return Conversation.objects.get(id=resource_id)
        except Exception:
            return None
        return None

    @staticmethod
    def can_manage_member(
        user: User,
        workspace_id: str,
        target_user_id: int
    ) -> bool:
        """Check if user can manage another member in the workspace."""
        try:
            manager = WorkspaceMember.objects.get(
                workspace_id=workspace_id,
                user=user
            )
            target = WorkspaceMember.objects.get(
                workspace_id=workspace_id,
                user_id=target_user_id
            )
            return manager.can_manage_member(target.role)
        except WorkspaceMember.DoesNotExist:
            return False

    @staticmethod
    def invite_member(
        workspace_id: str,
        email: str,
        role: str,
        invited_by: User
    ) -> Dict[str, Any]:
        """Invite a user to a workspace."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Check if inviter has permission
        if not PermissionService.has_workspace_permission(
            invited_by, workspace_id, 'manage_members'
        ):
            raise PermissionError("You don't have permission to invite members")

        # Validate role
        valid_roles = ['admin', 'member', 'viewer']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")

        # Check inviter can assign this role
        inviter_role = PermissionService.get_user_role_in_workspace(
            invited_by, workspace_id
        )
        hierarchy = {'owner': 4, 'admin': 3, 'member': 2, 'viewer': 1}
        if hierarchy.get(inviter_role, 0) <= hierarchy.get(role, 0):
            raise PermissionError(f"Cannot invite users with role {role}")

        # Get or create user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create pending user or send invite email
            # For now, return error
            raise ValueError("User not found. Please ask them to sign up first.")

        # Check if already member
        if WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=user
        ).exists():
            raise ValueError("User is already a member of this workspace")

        # Create membership
        member = WorkspaceMember.objects.create(
            workspace_id=workspace_id,
            user=user,
            role=role,
            invited_by=invited_by,
            invited_at=datetime.now()
        )

        logger.info(f"{invited_by.username} invited {user.username} to workspace {workspace_id} as {role}")

        return {
            'id': str(member.id),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'role': member.role,
            'invited_at': member.invited_at.isoformat(),
        }

    @staticmethod
    def remove_member(
        workspace_id: str,
        member_id: str,
        removed_by: User
    ) -> bool:
        """Remove a member from a workspace."""
        try:
            member = WorkspaceMember.objects.get(
                id=member_id,
                workspace_id=workspace_id
            )

            # Cannot remove owner
            if member.role == 'owner':
                raise PermissionError("Cannot remove workspace owner")

            # Check if remover can manage this member
            remover = WorkspaceMember.objects.get(
                workspace_id=workspace_id,
                user=removed_by
            )

            if not remover.can_manage_member(member.role):
                raise PermissionError("You don't have permission to remove this member")

            member.delete()
            logger.info(f"{removed_by.username} removed {member.user.username} from workspace {workspace_id}")
            return True

        except WorkspaceMember.DoesNotExist:
            return False

    @staticmethod
    def update_member_role(
        workspace_id: str,
        member_id: str,
        new_role: str,
        updated_by: User
    ) -> Dict[str, Any]:
        """Update a member's role."""
        try:
            member = WorkspaceMember.objects.get(
                id=member_id,
                workspace_id=workspace_id
            )

            # Cannot change owner's role
            if member.role == 'owner':
                raise PermissionError("Cannot change owner's role")

            # Check if updater has permission
            updater = WorkspaceMember.objects.get(
                workspace_id=workspace_id,
                user=updated_by
            )

            # Only owner can assign admin role
            if new_role == 'admin' and updater.role != 'owner':
                raise PermissionError("Only owner can assign admin role")

            # Check updater can manage both current and new role
            if not updater.can_manage_member(member.role):
                raise PermissionError("You don't have permission to manage this member")

            if not updater.can_manage_member(new_role):
                raise PermissionError(f"Cannot assign role {new_role}")

            old_role = member.role
            member.role = new_role
            member.save()

            logger.info(f"{updated_by.username} changed {member.user.username} from {old_role} to {new_role}")

            return {
                'id': str(member.id),
                'user': {
                    'id': member.user.id,
                    'username': member.user.username,
                    'email': member.user.email,
                },
                'role': member.role,
            }

        except WorkspaceMember.DoesNotExist:
            raise ValueError("Member not found")

    @staticmethod
    def get_workspace_members(workspace_id: str, user: User) -> List[Dict[str, Any]]:
        """Get all members of a workspace."""
        # Check if user is a member
        if not WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=user
        ).exists():
            raise PermissionError("You are not a member of this workspace")

        members = WorkspaceMember.objects.filter(
            workspace_id=workspace_id
        ).select_related('user', 'invited_by').order_by('-role', 'joined_at')

        return [
            {
                'id': str(m.id),
                'user': {
                    'id': m.user.id,
                    'username': m.user.username,
                    'email': m.user.email,
                    'first_name': m.user.first_name,
                    'last_name': m.user.last_name,
                },
                'role': m.role,
                'joined_at': m.joined_at.isoformat(),
                'invited_by': m.invited_by.username if m.invited_by else None,
            }
            for m in members
        ]

    @staticmethod
    def grant_resource_permission(
        resource_type: str,
        resource_id: str,
        user_id: int,
        permission: str,
        granted_by: User
    ) -> bool:
        """Grant a specific permission on a resource to a user."""
        # Check granter has manage permissions on resource
        if not PermissionService.can_manage_resource(
            granted_by, resource_type, resource_id, 'share'
        ):
            raise PermissionError("You don't have permission to share this resource")

        # Create permission
        ResourcePermission.objects.get_or_create(
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            permission=permission,
            defaults={'granted_by': granted_by}
        )

        logger.info(f"{granted_by.username} granted {permission} on {resource_type}:{resource_id} to user {user_id}")
        return True

    @staticmethod
    def revoke_resource_permission(
        resource_type: str,
        resource_id: str,
        user_id: int,
        permission: str,
        revoked_by: User
    ) -> bool:
        """Revoke a permission on a resource."""
        # Check revoker has manage permissions
        if not PermissionService.can_manage_resource(
            revoked_by, resource_type, resource_id, 'share'
        ):
            raise PermissionError("You don't have permission to manage this resource")

        try:
            perm = ResourcePermission.objects.get(
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                permission=permission
            )
            perm.delete()
            logger.info(f"{revoked_by.username} revoked {permission} on {resource_type}:{resource_id} from user {user_id}")
            return True
        except ResourcePermission.DoesNotExist:
            return False

    @staticmethod
    def get_user_workspaces(user: User) -> List[Dict[str, Any]]:
        """Get all workspaces where user is a member."""
        memberships = WorkspaceMember.objects.filter(
            user=user
        ).select_related('workspace')

        return [
            {
                'id': str(m.workspace.id),
                'name': m.workspace.name,
                'description': m.workspace.description,
                'role': m.role,
                'is_owner': m.role == 'owner',
                'member_count': m.workspace.get_member_count(),
                'created_at': m.workspace.created_at.isoformat(),
            }
            for m in memberships
        ]


from datetime import datetime
