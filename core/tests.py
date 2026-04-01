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
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_profile(self):
        """Test getting user profile - returns 404 if not created yet"""
        url = '/api/v1/profile/'
        response = self.client.get(url)
        # Should return 404 if profile doesn't exist, or 200 if it does
        self.assertIn(response.status_code, [200, 404])
    
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
