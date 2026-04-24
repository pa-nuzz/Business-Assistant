"""
Integration tests for the entire application flow.
Tests end-to-end scenarios across multiple services.
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Task, Document, BusinessProfile, Conversation, Message
from core.services.task_service import TaskService
from core.services.document_service import DocumentService
from core.services.profile_service import ProfileService
from core.services.auth_service import AuthService


@pytest.mark.django_db
class TestIntegrationAuthFlow:
    """Integration test for complete authentication flow."""
    
    def test_complete_auth_flow(self):
        """Test registration, verification, login, logout flow."""
        # Register
        result = AuthService.register(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        assert result['username'] == 'testuser'
        
        user = User.objects.get(username='testuser')
        assert not user.is_active
        
        # Verify email (simulate)
        verification_code = user.email_verification.verification_code
        AuthService.verify_email(verification_code)
        
        user.refresh_from_db()
        assert user.is_active
        
        # Login
        login_result = AuthService.login('testuser', 'testpass123')
        assert 'access_token' in login_result
        assert 'refresh_token' in login_result
        
        # Logout
        AuthService.logout(login_result['refresh_token'])
    
    def test_password_reset_flow(self):
        """Test forgot password, verify code, reset password flow."""
        user = User.objects.create_user(
            username='testuser',
            password='oldpass123',
            email='test@example.com'
        )
        user.is_active = True
        user.save()
        
        # Request reset
        AuthService.request_password_reset('test@example.com')
        
        # Get reset code
        user.refresh_from_db()
        reset_code = user.password_reset_code.verification_code
        
        # Verify reset code
        AuthService.verify_reset_code(reset_code)
        
        # Reset password
        AuthService.reset_password(reset_code, 'newpass123')
        
        user.refresh_from_db()
        assert user.check_password('newpass123')


@pytest.mark.django_db
class TestIntegrationTaskFlow:
    """Integration test for complete task management flow."""
    
    def test_complete_task_lifecycle(self):
        """Test create, update, complete, delete task flow."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        user.is_active = True
        user.save()
        
        service = TaskService(user)
        
        # Create task
        task_data = {
            'title': 'Integration Test Task',
            'description': 'Test description',
            'status': 'todo',
            'priority': 'high'
        }
        result = service.create_task(task_data)
        task_id = result['id']
        
        # Get task
        task = service.get_task(task_id)
        assert task['title'] == 'Integration Test Task'
        
        # Update task
        service.update_task(task_id, {'status': 'in_progress'})
        task = service.get_task(task_id)
        assert task['status'] == 'in_progress'
        
        # Add comment
        comment = service.add_comment(task_id, 'Test comment')
        assert comment['content'] == 'Test comment'
        
        # Complete task
        service.update_task(task_id, {'status': 'done'})
        task = service.get_task(task_id)
        assert task['status'] == 'done'
        
        # Delete task
        service.delete_task(task_id)
        assert not Task.objects.filter(id=task_id).exists()
    
    def test_task_with_tags_and_attachments(self):
        """Test task creation with tags and document attachments."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        user.is_active = True
        user.save()
        
        service = TaskService(user)
        
        # Create document
        from core.models import Document
        doc = Document.objects.create(
            user=user,
            title='Test Document',
            file_type='txt',
            status='ready'
        )
        
        # Create task with tags and document
        task_data = {
            'title': 'Task with attachments',
            'tags': ['urgent', 'important'],
            'document_ids': [str(doc.id)]
        }
        result = service.create_task(task_data)
        
        task = Task.objects.get(id=result['id'])
        assert task.tags.count() == 2
        assert task.attachments.count() == 1


@pytest.mark.django_db
class TestIntegrationDocumentFlow:
    """Integration test for document processing flow."""
    
    def test_document_upload_and_retrieval(self):
        """Test document upload, processing, and retrieval."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        user.is_active = True
        user.save()
        
        service = DocumentService(user)
        
        # Create document (simulated upload)
        from core.models import Document
        doc = Document.objects.create(
            user=user,
            title='Test Document',
            file_type='txt',
            status='ready',
            summary='Test summary'
        )
        
        # List documents
        result = service.list_documents()
        assert len(result['results']) == 1
        
        # Get document status
        status_result = service.get_document_status(str(doc.id))
        assert status_result['status'] == 'ready'
        
        # Get document details
        details = service.get_document(str(doc.id))
        assert details['summary'] == 'Test summary'
        
        # Delete document
        service.delete_document(str(doc.id))
        assert not Document.objects.filter(id=doc.id).exists()


@pytest.mark.django_db
class TestIntegrationProfileFlow:
    """Integration test for profile management flow."""
    
    def test_complete_profile_setup(self):
        """Test user info, business profile, and updates."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        user.is_active = True
        user.save()
        
        service = ProfileService(user)
        
        # Get user info
        info = service.get_user_info()
        assert info['username'] == 'testuser'
        
        # Update username
        service.update_username('newusername')
        user.refresh_from_db()
        assert user.username == 'newusername'
        
        # Update password
        service.update_password('testpass123', 'newpass123')
        user.refresh_from_db()
        assert user.check_password('newpass123')
        
        # Create business profile
        profile_data = {
            'company_name': 'Test Company',
            'industry': 'Technology',
            'company_size': '1-10'
        }
        result = service.update_business_profile(profile_data)
        assert result['company_name'] == 'Test Company'
        
        # Verify profile exists
        profile = service.get_business_profile()
        assert profile['company_name'] == 'Test Company'


@pytest.mark.django_db
class TestIntegrationAPIEndpoints:
    """Integration test for API endpoint flows."""
    
    def test_complete_api_workflow(self):
        """Test complete workflow through API endpoints."""
        client = APIClient()
        
        # Register
        register_data = {
            'username': 'apiuser',
            'password': 'apipass123',
            'email': 'api@example.com'
        }
        response = client.post('/api/v1/auth/register/', register_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify and activate user
        user = User.objects.get(username='apiuser')
        user.is_active = True
        user.save()
        
        # Login
        login_data = {'username': 'apiuser', 'password': 'apipass123'}
        response = client.post('/api/v1/auth/login/', login_data)
        assert response.status_code == status.HTTP_200_OK
        
        token = response.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Get user info
        response = client.get('/api/v1/user/info/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'apiuser'
        
        # Create task
        task_data = {'title': 'API Task', 'status': 'todo'}
        response = client.post('/api/v1/tasks/create/', task_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        task_id = response.data['id']
        
        # List tasks
        response = client.get('/api/v1/tasks/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        
        # Update task
        response = client.post(f'/api/v1/tasks/{task_id}/update/', {'status': 'done'})
        assert response.status_code == status.HTTP_200_OK
        
        # Logout
        response = client.post('/api/v1/auth/logout/', {'refresh_token': token})
        assert response.status_code == status.HTTP_200_OK
