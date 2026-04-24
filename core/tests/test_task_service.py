"""
Unit tests for TaskService.
"""
import pytest
from django.contrib.auth.models import User
from core.services.task_service import TaskService
from core.models import Task, TaskTag, BusinessProfile


@pytest.mark.django_db
class TestTaskService:
    """Test cases for TaskService."""
    
    def test_list_tasks_empty(self):
        """Test listing tasks when user has no tasks."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = TaskService(user)
        
        result = service.list_tasks()
        
        assert result['results'] == []
        assert result['count'] == 0
        assert result['page'] == 1
    
    def test_create_task_success(self):
        """Test successful task creation."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = TaskService(user)
        
        data = {
            'title': 'Test Task',
            'description': 'Test description',
            'status': 'todo',
            'priority': 'high'
        }
        
        result = service.create_task(data)
        
        assert 'id' in result
        assert result['title'] == 'Test Task'
        assert result['status'] == 'todo'
        assert Task.objects.filter(user=user).exists()
    
    def test_create_task_with_tags(self):
        """Test task creation with tags."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = TaskService(user)
        
        data = {
            'title': 'Test Task',
            'tags': ['urgent', 'important']
        }
        
        result = service.create_task(data)
        
        task = Task.objects.get(id=result['id'])
        assert task.tags.count() == 2
    
    def test_create_task_invalid_title(self):
        """Test task creation with invalid title."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = TaskService(user)
        
        with pytest.raises(ValueError, match="required"):
            service.create_task({'title': ''})
    
    def test_get_task_success(self):
        """Test getting a task."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = TaskService(user)
        
        task = Task.objects.create(
            user=user,
            created_by=user,
            title='Test Task',
            status='todo'
        )
        
        result = service.get_task(str(task.id))
        
        assert result['id'] == str(task.id)
        assert result['title'] == 'Test Task'
    
    def test_get_task_no_permission(self):
        """Test getting a task without permission."""
        user1 = User.objects.create_user(username='user1', password='pass123')
        user2 = User.objects.create_user(username='user2', password='pass123')
        service = TaskService(user2)
        
        task = Task.objects.create(
            user=user1,
            created_by=user1,
            title='Private Task',
            status='todo'
        )
        
        with pytest.raises(ValueError, match="permission"):
            service.get_task(str(task.id))
    
    def test_update_task_success(self):
        """Test updating a task."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = TaskService(user)
        
        task = Task.objects.create(
            user=user,
            created_by=user,
            title='Original Title',
            status='todo'
        )
        
        result = service.update_task(str(task.id), {'title': 'Updated Title'})
        
        assert result['title'] == 'Updated Title'
        task.refresh_from_db()
        assert task.title == 'Updated Title'
    
    def test_delete_task_success(self):
        """Test deleting a task."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = TaskService(user)
        
        task = Task.objects.create(
            user=user,
            created_by=user,
            title='To Delete',
            status='todo'
        )
        
        result = service.delete_task(str(task.id))
        
        assert result is True
        assert not Task.objects.filter(id=task.id).exists()
    
    def test_add_comment_success(self):
        """Test adding a comment to a task."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = TaskService(user)
        
        task = Task.objects.create(
            user=user,
            created_by=user,
            title='Test Task',
            status='todo'
        )
        
        result = service.add_comment(str(task.id), 'This is a comment')
        
        assert 'id' in result
        assert result['content'] == 'This is a comment'
