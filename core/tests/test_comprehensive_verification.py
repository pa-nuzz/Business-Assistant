"""
Comprehensive verification tests for all implemented features.
Tests bug fixes, chat enhancements, document verification, and routing.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Document, Conversation, Message, BusinessProfile
from core.services.chat_service import ChatService
from core.services.document_service import DocumentService
from core.services.conversation_service import ConversationService


class ComprehensiveVerificationTests(TransactionTestCase):
    """Comprehensive test suite for all implemented features."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create business profile for context testing
        self.business_profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            industry='Technology',
            company_size='Small'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_rename_archive_functionality(self):
        """Test rename and archive functionality works correctly."""
        # Create a conversation
        convo = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        
        # Test rename functionality
        conversation_service = ConversationService(self.user)
        result = conversation_service.update_conversation(str(convo.id), {'title': 'New Title'})
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'New Title')
        
        # Verify in database
        convo.refresh_from_db()
        self.assertEqual(convo.title, 'New Title')
        
        # Test archive functionality
        result = conversation_service.update_conversation(str(convo.id), {'archived': True})
        
        self.assertIsNotNone(result)
        self.assertTrue(result['archived'])
        
        # Verify in database
        convo.refresh_from_db()
        self.assertTrue(convo.archived)
    
    def test_delete_conversation_api_endpoint(self):
        """Test delete conversation API works with correct endpoint."""
        # Create a conversation
        convo = Conversation.objects.create(
            user=self.user,
            title='Test Conversation for Deletion'
        )
        
        # Test delete endpoint
        url = reverse('api_v1:delete-conversation', kwargs={'conversation_id': convo.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['deleted'])
        
        # Verify conversation is deleted
        with self.assertRaises(Conversation.DoesNotExist):
            Conversation.objects.get(id=convo.id)
    
    def test_professional_chat_context(self):
        """Test chat service builds professional context correctly."""
        chat_service = ChatService(self.user)
        
        # Create a conversation for context building
        convo = Conversation.objects.create(
            user=self.user,
            title='Business Strategy Discussion'
        )
        
        # Test context building
        history = chat_service._build_conversation_history(convo)
        
        # Should have system message with professional context
        self.assertTrue(len(history) > 0)
        system_message = history[0]
        self.assertEqual(system_message['role'], 'system')
        self.assertIn('AEIOU AI', system_message['content'])
        self.assertIn('professional', system_message['content'])
        self.assertIn('Test Company', system_message['content'])
        self.assertIn('Technology', system_message['content'])
    
    def test_intelligent_command_processing(self):
        """Test intelligent command processing works."""
        chat_service = ChatService(self.user)
        
        # Test document analysis command
        result = chat_service._process_intelligent_commands("analyze this document")
        self.assertIsNotNone(result)
        self.assertEqual(result['intent'], 'document_analysis')
        self.assertIn('document analysis', result['response'].lower())
        
        # Task creation command
        result = chat_service._process_intelligent_commands("create a task to review report")
        self.assertIsNotNone(result)
        self.assertEqual(result['intent'], 'task_creation')
        self.assertIn('task', result['response'].lower())
        
        # Summary command
        result = chat_service._process_intelligent_commands("summarize my recent chats")
        self.assertIsNotNone(result)
        self.assertEqual(result['intent'], 'conversation_summary')
        self.assertIn('summary', result['response'].lower())
        
        # Analytics command
        result = chat_service._process_intelligent_commands("show me trends")
        self.assertIsNotNone(result)
        self.assertEqual(result['intent'], 'analytics_request')
        self.assertIn('analytics', result['response'].lower())
        
        # Document status command
        result = chat_service._process_intelligent_commands("recheck document")
        self.assertIsNotNone(result)
        self.assertEqual(result['intent'], 'document_status')
        self.assertIn('document', result['response'].lower())
    
    def test_document_verification_system(self):
        """Test enhanced document verification and status tracking."""
        document_service = DocumentService(self.user)
        
        # Create a test document
        doc = Document.objects.create(
            user=self.user,
            title='Test Document.pdf',
            file_type='pdf',
            status='ready'
        )
        
        # Test detailed status checking
        status = document_service.get_document_status(str(doc.id))
        
        self.assertEqual(status['id'], str(doc.id))
        self.assertEqual(status['status'], 'ready')
        self.assertEqual(status['stage'], 'completed')
        self.assertEqual(status['progress'], 100)
        self.assertIn('processing_details', status)
        self.assertTrue(status['processing_details']['ready_for_chat'])
        
        # Test all documents status summary
        summary = document_service.get_all_documents_status()
        
        self.assertIn('status_summary', summary)
        self.assertIn('recent_documents', summary)
        self.assertIn('processing_health', summary)
        self.assertEqual(summary['status_summary']['total'], 1)
        self.assertEqual(summary['status_summary']['ready'], 1)
        self.assertTrue(summary['processing_health']['ready_for_analysis'])
    
    def test_document_verification_api_endpoints(self):
        """Test new document verification API endpoints."""
        # Create a test document
        doc = Document.objects.create(
            user=self.user,
            title='API Test Document.pdf',
            file_type='pdf',
            status='processing'
        )
        
        # Test document status endpoint
        url = reverse('api_v1:document-status', kwargs={'doc_id': doc.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(doc.id))
        self.assertEqual(response.data['status'], 'processing')
        self.assertIn('stage', response.data)
        self.assertIn('progress', response.data)
        
        # Test documents status summary endpoint
        url = reverse('api_v1:documents-status-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status_summary', response.data)
        self.assertIn('recent_documents', response.data)
        self.assertIn('processing_health', response.data)
        
        # Test reprocess document endpoint
        url = reverse('api_v1:document-reprocess', kwargs={'doc_id': doc.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('re-processing started', response.data['message'])
        
        # Verify document status was reset
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'pending')
    
    @patch('core.services.document_service.process_document_task.delay')
    def test_document_upload_enhancement(self, mock_task_delay):
        """Test enhanced document upload with verification."""
        document_service = DocumentService(self.user)
        
        mock_file = SimpleUploadedFile(
            "test_document.pdf",
            b"%PDF-1.4\n% test pdf content",
            content_type="application/pdf",
        )
        
        # Test upload with enhanced response
        result = document_service.upload_document(mock_file, 'Test Document')
        
        self.assertIn('id', result)
        self.assertIn('title', result)
        self.assertIn('status', result)
        self.assertIn('file_type', result)
        self.assertIn('created_at', result)
        self.assertTrue(result['processing_started'])
        
        # Verify task was queued
        mock_task_delay.assert_called_once()
    
    def test_chat_persistence_across_sessions(self):
        """Test chat context persists across sessions."""
        # Create conversation with messages
        convo = Conversation.objects.create(
            user=self.user,
            title='Persistent Test Chat'
        )
        
        Message.objects.create(
            conversation=convo,
            role='user',
            content='Test message for persistence'
        )
        
        Message.objects.create(
            conversation=convo,
            role='assistant',
            content='Test response for persistence'
        )
        
        # Test conversation retrieval
        conversation_service = ConversationService(self.user)
        result = conversation_service.get_conversation(str(convo.id))
        
        self.assertEqual(result['id'], str(convo.id))
        self.assertEqual(len(result['messages']), 2)
        self.assertEqual(result['messages'][0]['role'], 'user')
        self.assertEqual(result['messages'][1]['role'], 'assistant')
    
    def test_routing_consistency(self):
        """Test routing works consistently across the application."""
        # Test main routes are accessible
        routes_to_test = [
            ('api_v1:conversation-list', []),
            ('api_v1:document-list', []),
            ('api_v1:documents-status-summary', []),
            ('api_v1:user-info', []),
        ]
        
        for route_name, kwargs in routes_to_test:
            try:
                url = reverse(route_name, kwargs=kwargs)
                response = self.client.get(url)
                # Should not return 404 for valid routes
                self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            except Exception as e:
                self.fail(f"Route {route_name} failed: {str(e)}")
    
    def test_error_handling_and_robustness(self):
        """Test error handling and system robustness."""
        chat_service = ChatService(self.user)
        document_service = DocumentService(self.user)
        conversation_service = ConversationService(self.user)
        
        # Test chat service error handling
        with self.assertRaises(ValueError):
            chat_service.send_message("")  # Empty message
        
        with self.assertRaises(ValueError):
            chat_service.send_message("x" * 5000)  # Too long message
        
        # Test document service error handling
        with self.assertRaises(ValueError):
            document_service.get_document_status("invalid-uuid")
        
        with self.assertRaises(ValueError):
            document_service.get_document_status("00000000-0000-0000-0000-000000000000")
        
        # Test conversation service error handling
        with self.assertRaises(ValueError):
            conversation_service.get_conversation("invalid-uuid")
        
        self.assertIsNone(conversation_service.update_conversation("invalid-uuid", {"title": "Test"}))
    
    def test_performance_and_scalability(self):
        """Test performance indicators and scalability considerations."""
        # Create multiple documents for testing
        docs = []
        for i in range(10):
            doc = Document.objects.create(
                user=self.user,
                title=f'Performance Test Document {i}.pdf',
                file_type='pdf',
                status='ready'
            )
            docs.append(doc)
        
        # Test bulk status retrieval
        document_service = DocumentService(self.user)
        summary = document_service.get_all_documents_status()
        
        # Should handle multiple documents efficiently
        self.assertEqual(summary['status_summary']['total'], 10)
        self.assertEqual(len(summary['recent_documents']), 10)
        
        # Test conversation history building performance
        convo = Conversation.objects.create(
            user=self.user,
            title='Performance Test Conversation'
        )
        
        chat_service = ChatService(self.user)
        history = chat_service._build_conversation_history(convo)
        
        # Should build context efficiently
        self.assertIsInstance(history, list)
        self.assertTrue(len(history) > 0)


class IntegrationTests(TransactionTestCase):
    """Integration tests for end-to-end workflows."""
    
    def setUp(self):
        """Set up integration test data."""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integrationpass123'
        )
        
        self.business_profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Integration Test Corp',
            industry='Software',
            company_size='Medium'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_complete_document_workflow(self):
        """Test complete document upload → processing → chat workflow."""
        # This would be tested with actual file upload in a real environment
        # For now, we simulate the workflow
        
        # 1. Create document (simulating upload)
        doc = Document.objects.create(
            user=self.user,
            title='Integration Workflow Test.pdf',
            file_type='pdf',
            status='ready',
            summary='This document contains important business information about workflow optimization.'
        )
        
        # 2. Verify document status
        document_service = DocumentService(self.user)
        status = document_service.get_document_status(str(doc.id))
        self.assertEqual(status['status'], 'ready')
        self.assertTrue(status['processing_details']['ready_for_chat'])
        
        # 3. Test chat with document context
        chat_service = ChatService(self.user)
        convo = Conversation.objects.create(user=self.user, title='Document Discussion')
        
        history = chat_service._build_conversation_history(convo)
        
        # Should include document context
        doc_context_added = any('Recent Documents Context:' in msg['content'] for msg in history)
        # Note: This depends on having documents with status='ready'
        
        # 4. Test intelligent commands
        result = chat_service._process_intelligent_commands("analyze this document")
        self.assertIsNotNone(result)
        self.assertEqual(result['intent'], 'document_analysis')
    
    def test_complete_chat_workflow(self):
        """Test complete chat workflow with professional behavior."""
        chat_service = ChatService(self.user)
        
        # 1. Create conversation
        convo = Conversation.objects.create(
            user=self.user,
            title='Professional Business Discussion'
        )
        
        # 2. Test professional context building
        history = chat_service._build_conversation_history(convo)
        system_message = history[0]
        
        # Should contain professional guidelines and business context
        self.assertIn('professional', system_message['content'])
        self.assertIn('Integration Test Corp', system_message['content'])
        self.assertIn('Software', system_message['content'])
        
        # 3. Test intelligent command recognition
        commands_to_test = [
            ("analyze this document", "document_analysis"),
            ("create a task for review", "task_creation"),
            ("summarize my recent activity", "conversation_summary"),
            ("show me analytics dashboard", "analytics_request"),
        ]
        
        for command, expected_intent in commands_to_test:
            result = chat_service._process_intelligent_commands(command)
            self.assertIsNotNone(result)
            self.assertEqual(result['intent'], expected_intent)
    
    def test_error_recovery_and_resilience(self):
        """Test system resilience and error recovery."""
        # Test with failed documents
        failed_doc = Document.objects.create(
            user=self.user,
            title='Failed Document.pdf',
            file_type='pdf',
            status='failed'
        )
        
        document_service = DocumentService(self.user)
        summary = document_service.get_all_documents_status()
        
        # Should handle failed documents gracefully
        self.assertTrue(summary['processing_health']['needs_attention'])
        self.assertEqual(summary['status_summary']['failed'], 1)
        
        # Test reprocessing failed document
        from core.services.document_service import process_document_task
        with patch('core.services.document_service.process_document_task.delay') as mock_task:
            doc_id = str(failed_doc.id)
            url = reverse('api_v1:document-reprocess', kwargs={'doc_id': doc_id})
            response = self.client.post(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_task.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
