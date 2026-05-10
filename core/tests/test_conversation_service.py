"""
Unit tests for ConversationService.
"""
import pytest
from django.contrib.auth.models import User
from core.models import Conversation, Message
from core.services.conversation_service import ConversationService


@pytest.mark.django_db
class TestConversationService:
    """Test cases for ConversationService."""
    
    def test_list_conversations_empty(self):
        """Test listing conversations when user has none."""
        user = User.objects.create_user(username='testuser', password='testpass')
        service = ConversationService(user)
        
        result = service.list_conversations()
        
        assert result['count'] == 0
        assert result['results'] == []
    
    def test_list_conversations_with_data(self):
        """Test listing conversations with existing conversations."""
        user = User.objects.create_user(username='testuser', password='testpass')
        Conversation.objects.create(user=user, title='Test 1')
        Conversation.objects.create(user=user, title='Test 2')
        
        service = ConversationService(user)
        result = service.list_conversations()
        
        assert result['count'] == 2
        assert len(result['results']) == 2
    
    def test_list_conversations_pagination(self):
        """Test pagination of conversations."""
        user = User.objects.create_user(username='testuser', password='testpass')
        for i in range(5):
            Conversation.objects.create(user=user, title=f'Test {i}')
        
        service = ConversationService(user)
        result = service.list_conversations(page=1, page_size=2)
        
        assert result['count'] == 5
        assert len(result['results']) == 2
        assert result['total_pages'] == 3
    
    def test_get_conversation_success(self):
        """Test getting a specific conversation."""
        user = User.objects.create_user(username='testuser', password='testpass')
        conversation = Conversation.objects.create(user=user, title='Test')
        Message.objects.create(conversation=conversation, role='user', content='Hello')
        
        service = ConversationService(user)
        result = service.get_conversation(str(conversation.id))
        
        assert result['id'] == str(conversation.id)
        assert result['title'] == 'Test'
        assert len(result['messages']) == 1
    
    def test_get_conversation_not_found(self):
        """Test getting non-existent conversation raises ValueError."""
        user = User.objects.create_user(username='testuser', password='testpass')
        service = ConversationService(user)
        
        with pytest.raises(ValueError, match="Conversation not found"):
            service.get_conversation('invalid-uuid')
    
    def test_delete_conversation_success(self):
        """Test deleting a conversation."""
        user = User.objects.create_user(username='testuser', password='testpass')
        conversation = Conversation.objects.create(user=user, title='Test')
        
        service = ConversationService(user)
        result = service.delete_conversation(str(conversation.id))
        
        assert result is True
        assert Conversation.objects.filter(id=conversation.id).count() == 0
    
    def test_delete_conversation_not_found(self):
        """Test deleting non-existent conversation returns False."""
        user = User.objects.create_user(username='testuser', password='testpass')
        service = ConversationService(user)
        
        result = service.delete_conversation('invalid-uuid')
        
        assert result is False
    
    def test_soft_delete_conversation(self):
        """Test soft deleting a conversation."""
        user = User.objects.create_user(username='testuser', password='testpass')
        conversation = Conversation.objects.create(user=user, title='Test')
        
        service = ConversationService(user)
        result = service.soft_delete_conversation(str(conversation.id))
        
        assert result is True
        conversation.refresh_from_db()
        assert conversation.deleted_at is not None
    
    def test_export_conversation(self):
        """Test exporting a conversation."""
        user = User.objects.create_user(username='testuser', password='testpass')
        conversation = Conversation.objects.create(user=user, title='Test')
        Message.objects.create(conversation=conversation, role='user', content='Hello')
        
        service = ConversationService(user)
        result = service.export_conversation(str(conversation.id))
        
        assert result['id'] == str(conversation.id)
        assert result['title'] == 'Test'
        assert 'exported_at' in result
        assert len(result['messages']) == 1
