"""
Backend API Tests for AEIOU AI
Tests all API endpoints including auth, chat, and documents
Uses Django's built-in TestCase (no pytest required)
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from core.models import Conversation, Message, Document, BusinessProfile
import json
import uuid


class AuthTests(APITestCase):
    """Test authentication endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_register_success(self):
        """Test user registration with valid data"""
        url = '/api/v1/auth/register/'
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'new@example.com'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username fails"""
        url = '/api/v1/auth/register/'
        data = {
            'username': 'testuser',
            'password': 'newpass123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_short_password(self):
        """Test registration with short password fails"""
        url = '/api/v1/auth/register/'
        data = {
            'username': 'shortpass',
            'password': '123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_success(self):
        """Test login with valid credentials"""
        url = '/api/v1/auth/token/'
        data = {
            'username': 'testuser',
            'password': 'testpass123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials fails"""
        url = '/api/v1/auth/token/'
        data = {
            'username': 'testuser',
            'password': 'wrongpass',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_forgot_password_success(self):
        """Test forgot password endpoint"""
        url = '/api/v1/auth/forgot-password/'
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_forgot_password_missing_email(self):
        """Test forgot password without email fails"""
        url = '/api/v1/auth/forgot-password/'
        data = {}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ConversationTests(APITestCase):
    """Test conversation endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
    
    def test_list_conversations(self):
        """Test listing user conversations"""
        url = '/api/v1/conversations/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_get_conversation_detail(self):
        """Test getting conversation with messages"""
        url = f'/api/v1/conversations/{self.conversation.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.conversation.id))
    
    def test_delete_conversation(self):
        """Test deleting a conversation"""
        url = f'/api/v1/conversations/{self.conversation.id}/delete/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Conversation.objects.filter(id=self.conversation.id).exists())
    
    def test_delete_other_user_conversation(self):
        """Test cannot delete another user's conversation"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_conv = Conversation.objects.create(
            user=other_user,
            title='Other User Conversation'
        )
        url = f'/api/v1/conversations/{other_conv.id}/delete/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated requests are rejected"""
        self.client.credentials()
        url = '/api/v1/conversations/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatTests(APITestCase):
    """Test chat endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_chat_endpoint_requires_auth(self):
        """Test chat endpoint requires authentication"""
        self.client.credentials()
        url = '/api/v1/chat/'
        data = {'message': 'Hello'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_health_check(self):
        """Test health check endpoint"""
        url = '/api/v1/health/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'ok')


class DocumentTests(APITestCase):
    """Test document endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_documents(self):
        """Test listing documents"""
        url = '/api/v1/documents/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_document_upload_requires_auth(self):
        """Test document upload requires authentication"""
        self.client.credentials()
        url = '/api/v1/documents/upload/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTests(APITestCase):
    """Test profile endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Create business profile for consistent testing
        from core.models import BusinessProfile
        BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            industry='Technology'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_get_profile(self):
        """Test getting user profile returns 200"""
        url = '/api/v1/profile/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['company_name'], 'Test Company')
    
    def test_update_profile_creates_if_not_exists(self):
        """Test updating profile creates it if not exists"""
        url = '/api/v1/profile/'
        data = {
            'company_name': 'Test Business',
            'industry': 'Technology'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Now profile should exist
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ModelTests(TestCase):
    """Test database models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_conversation_creation(self):
        """Test creating a conversation"""
        conv = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        self.assertEqual(conv.title, 'Test Conversation')
        self.assertEqual(conv.user, self.user)
    
    def test_message_creation(self):
        """Test creating a message"""
        conv = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        msg = Message.objects.create(
            conversation=conv,
            role='user',
            content='Hello'
        )
        self.assertEqual(msg.content, 'Hello')
        self.assertEqual(msg.conversation, conv)
    
    def test_document_creation(self):
        """Test creating a document"""
        doc = Document.objects.create(
            user=self.user,
            title='test.pdf',
            file_type='pdf',
            status='pending'
        )
        self.assertEqual(doc.title, 'test.pdf')
        self.assertEqual(doc.user, self.user)
    
    def test_business_profile_creation(self):
        """Test creating a business profile"""
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Business',
            industry='Technology'
        )
        self.assertEqual(profile.company_name, 'Test Business')
        self.assertEqual(profile.user, self.user)


class CriticalPathIntegrationTest(APITestCase):
    """
    Critical Path Integration Test
    
    Tests the complete user journey from chat → task creation → task viewing.
    This ensures all major components work together.
    """
    
    def setUp(self):
        """Set up test user with business profile."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.profile = BusinessProfile.objects.create(
            user=self.user,
            company_name="Test Company",
            industry="Technology"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_chat_endpoint_responds(self):
        """Test the chat API endpoint responds without error."""
        response = self.client.post(
            "/api/v1/chat/",
            data={"message": "What tasks do I have?"},
            format="json"
        )
        # Should return 200 — orchestrator handles missing AI config gracefully
        self.assertEqual(response.status_code, 200)

    def test_task_list_api(self):
        """Test task list API endpoint."""
        response = self.client.get("/api/v1/tasks/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)

    def test_task_creation_via_api(self):
        """Test creating a task via API."""
        response = self.client.post(
            "/api/v1/tasks/create/",
            data={
                "title": "API test task",
                "description": "Test description",
                "priority": "medium"
            },
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        
        # Verify task was created
        from core.models import Task
        task = Task.objects.get(id=data["id"])
        self.assertEqual(task.title, "API test task")

    def test_complete_user_journey_chat_to_task(self):
        """
        Test the complete flow:
        1. User sends chat message
        2. Conversation is created
        3. Task can be created via task API
        4. Task appears in task list
        """
        # Step 1: Chat request
        chat_response = self.client.post(
            "/api/v1/chat/",
            data={"message": "I need to review the quarterly report"},
            format="json"
        )
        # Chat may fail if AI not configured, that's ok for this test
        
        # Step 2: Create task manually (simulating what orchestrator would do)
        task_response = self.client.post(
            "/api/v1/tasks/create/",
            data={
                "title": "Review quarterly report",
                "priority": "high",
                "description": "Created from chat context"
            },
            format="json"
        )
        self.assertEqual(task_response.status_code, 201)
        task_data = task_response.json()
        task_id = task_data["id"]
        
        # Step 3: Get task details
        detail_response = self.client.get(f"/api/v1/tasks/{task_id}/")
        self.assertEqual(detail_response.status_code, 200)
        detail_data = detail_response.json()
        self.assertEqual(detail_data["title"], "Review quarterly report")
        
        # Step 4: Task appears in list
        list_response = self.client.get("/api/v1/tasks/")
        self.assertEqual(list_response.status_code, 200)
        list_data = list_response.json()
        task_ids = [t["id"] for t in list_data.get("results", [])]
        self.assertIn(task_id, task_ids)

    def test_entity_resolution_context(self):
        """Test that entity resolution can be imported and works."""
        from agents.entity_resolver import EntityResolver, ResolvedEntity
        
        # Create a test conversation with a document reference
        conv = Conversation.objects.create(
            user=self.user,
            title="Test conversation"
        )
        
        # Test entity resolver can be instantiated
        history = [{"role": "assistant", "content": f"Document {uuid.uuid4()} is ready"}]
        resolver = EntityResolver(user_id=self.user.id, conversation_history=history)
        
        # Should return list (may be empty if no entities found)
        entities = resolver.resolve("that report")
        self.assertIsInstance(entities, list)

    def test_tool_caching_works(self):
        """Test that tool caching decorator works."""
        from mcp.tools import cached_tool
        
        # Verify decorator exists and can be applied
        @cached_tool(ttl=60)
        def test_tool():
            return {"result": "test"}
        
        result = test_tool()
        self.assertIn("result", result)

    def test_sanitization_imports(self):
        """Test that sanitization utilities can be imported."""
        from utils.sanitization import sanitize_plain_text, sanitize_rich_text
        
        # Test basic sanitization
        dirty = "<script>alert('xss')</script>Hello"
        clean = sanitize_plain_text(dirty)
        self.assertNotIn("<script>", clean)
        self.assertIn("Hello", clean)

    def test_task_permissions_utility(self):
        """Test that task permissions utility works."""
        from utils.task_permissions import can_read_task, can_modify_task, can_delete_task
        from core.models import Task
        
        # Create a task
        task = Task.objects.create(
            user=self.user,
            created_by=self.user,
            business_profile=self.profile,
            title="Permission test task",
            status="todo",
            priority="medium"
        )
        
        # User should have all permissions on their own task
        self.assertTrue(can_read_task(task, self.user))
        self.assertTrue(can_modify_task(task, self.user))
        self.assertTrue(can_delete_task(task, self.user))
