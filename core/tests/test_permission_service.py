import pytest
from django.contrib.auth.models import User
from core.models import Workspace, WorkspaceMember, Task, ResourcePermission, BusinessProfile
from core.services.permission_service import PermissionService


@pytest.fixture
def owner(db):
    return User.objects.create_user(username="owner", password="password")


@pytest.fixture
def member(db):
    return User.objects.create_user(username="member", password="password")


@pytest.fixture
def workspace(db, owner):
    ws = Workspace.objects.create(name="Test Workspace", owner=owner)
    WorkspaceMember.objects.create(workspace=ws, user=owner, role="owner")
    return ws


@pytest.fixture
def business_profile(db, owner):
    return BusinessProfile.objects.create(user=owner, company_name="Test Company")


@pytest.fixture
def task(db, workspace, owner, business_profile):
    return Task.objects.create(title="Test Task", user=owner, created_by=owner, business_profile=business_profile)


@pytest.mark.django_db
class TestPermissionService:
    def test_get_user_role_in_workspace(self, workspace, owner, member):
        WorkspaceMember.objects.create(workspace=workspace, user=member, role="member")
        
        role1 = PermissionService.get_user_role_in_workspace(owner, str(workspace.id))
        role2 = PermissionService.get_user_role_in_workspace(member, str(workspace.id))
        
        assert role1 == "owner"
        assert role2 == "member"

    def test_has_workspace_permission_owner(self, workspace, owner):
        assert PermissionService.has_workspace_permission(owner, str(workspace.id), "manage_members")

    def test_can_manage_resource_as_owner(self, task, owner):
        assert PermissionService.can_manage_resource(owner, "task", str(task.id), "read")
        assert PermissionService.can_manage_resource(owner, "task", str(task.id), "delete")

    def test_can_manage_resource_assigned(self, task, member):
        task.assignee = member
        task.save()
        
        assert PermissionService.can_manage_resource(member, "task", str(task.id), "update")
        assert not PermissionService.can_manage_resource(member, "task", str(task.id), "delete")

    def test_grant_resource_permission(self, task, owner, member):
        PermissionService.grant_resource_permission(
            resource_type="task",
            resource_id=str(task.id),
            user_id=member.id,
            permission="read",
            granted_by=owner
        )
        
        # Verify it was added to DB
        assert ResourcePermission.objects.filter(
            resource_type="task",
            resource_id=str(task.id),
            user=member,
            permission="read"
        ).exists()
        
        # Verify it checks out
        assert PermissionService.can_manage_resource(member, "task", str(task.id), "read")
