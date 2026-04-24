"""
Unit tests for ChatService.
"""
import pytest
from django.contrib.auth.models import User
from core.models import Conversation, Message
from core.services.chat_service import ChatService
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestChatService:
    """Test cases for ChatService."""
    
    def test_send_message_creates_new_conversation(self):
        """Test that sending a message without conversation_id creates a new conversation."""
        user = User.objects.create_user(username='testuser', password='testpass')
        service = ChatService(user)
        
        with patch('core.services.chat_service.orchestrator.run') as mock_run:
            mock_run.return_value = {
                'reply': 'Test response',
                'model': 'test-model',
                'tools_used': [],
                'intent': 'chat'
            }
            
            result = service.send_message('Hello')
            
            assert Conversation.objects.filter(user=user).count() == 1
            assert result['conversation_id'] is not None
            assert result['reply'] == 'Test response'
    
    def test_send_message_uses_existing_conversation(self):
        """Test that sending a message with conversation_id uses existing conversation."""
        user = User.objects.create_user(username='testuser', password='testpass')
        conversation = Conversation.objects.create(user=user, title='Test')
        
        service = ChatService(user)
        
        with patch('core.services.chat_service.orchestrator.run') as mock_run:
            mock_run.return_value = {
                'reply': 'Test response',
                'model': 'test-model',
                'tools_used': [],
                'intent': 'chat'
            }
            
            result = service.send_message('Hello', str(conversation.id))
            
            assert Conversation.objects.filter(user=user).count() == 1
            assert result['conversation_id'] == str(conversation.id)
    
    def test_send_message_empty_error(self):
        """Test that empty message raises ValueError."""
        user = User.objects.create_user(username='testuser', password='testpass')
        service = ChatService(user)
        
        with pytest.raises(ValueError, match="Message cannot be empty"):
            service.send_message('')
    
    def test_send_message_too_long_error(self):
        """Test that message too long raises ValueError."""
        user = User.objects.create_user(username='testuser', password='testpass')
        service = ChatService(user)
        
        long_message = 'a' * 4001
        with pytest.raises(ValueError, match="Message too long"):
            service.send_message(long_message)
    
    def test_send_message_invalid_conversation(self):
        """Test that invalid conversation_id raises ValueError."""
        user = User.objects.create_user(username='testuser', password='testpass')
        service = ChatService(user)
        
        with pytest.raises(ValueError, match="Conversation not found"):
            service.send_message('Hello', 'invalid-uuid')
    
    def test_send_message_saves_messages(self):
        """Test that messages are saved to database."""
        user = User.objects.create_user(username='testuser', password='testpass')
        service = ChatService(user)
        
        with patch('core.services.chat_service.orchestrator.run') as mock_run:
            mock_run.return_value = {
                'reply': 'Test response',
                'model': 'test-model',
                'tools_used': [],
                'intent': 'chat'
            }
            
            service.send_message('Hello')
            
            conversation = Conversation.objects.get(user=user)
            assert Message.objects.filter(conversation=conversation).count() == 2
    
    def test_build_conversation_history(self):
        """Test that conversation history is built correctly."""
        user = User.objects.create_user(username='testuser', password='testpass')
        conversation = Conversation.objects.create(user=user, title='Test')
        
        Message.objects.create(conversation=conversation, role='user', content='Hello')
        Message.objects.create(conversation=conversation, role='assistant', content='Hi there')
        
        service = ChatService(user)
        history = service._build_conversation_history(conversation)
        
        assert len(history) == 2
        assert history[0]['role'] == 'user'
        assert history[1]['role'] == 'assistant'
