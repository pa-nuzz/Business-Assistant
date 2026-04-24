"""
Unit tests for DocumentService.
"""
import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from core.services.document_service import DocumentService
from core.models import Document
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestDocumentService:
    """Test cases for DocumentService."""
    
    def test_list_documents_empty(self):
        """Test listing documents when user has no documents."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        result = service.list_documents()
        
        assert result['results'] == []
        assert result['count'] == 0
        assert result['page'] == 1
    
    def test_list_documents_with_data(self):
        """Test listing documents with existing documents."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        Document.objects.create(
            user=user,
            title='Test Doc',
            file_type='txt',
            status='ready'
        )
        
        result = service.list_documents()
        
        assert len(result['results']) == 1
        assert result['count'] == 1
        assert result['results'][0]['title'] == 'Test Doc'
    
    @patch('core.services.document_service.process_document')
    def test_upload_document_success(self, mock_process):
        """Test successful document upload."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        mock_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        
        result = service.upload_document(mock_file, 'Test Title')
        
        assert 'id' in result
        assert result['title'] == 'Test Title'
        assert Document.objects.filter(user=user).exists()
    
    def test_upload_document_no_file(self):
        """Test document upload without file."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        with pytest.raises(ValueError, match="No file provided"):
            service.upload_document(None)
    
    def test_get_document_status_success(self):
        """Test getting document status."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        doc = Document.objects.create(
            user=user,
            title='Test Doc',
            file_type='txt',
            status='ready'
        )
        
        result = service.get_document_status(str(doc.id))
        
        assert result['id'] == str(doc.id)
        assert result['status'] == 'ready'
    
    def test_get_document_status_not_found(self):
        """Test getting status for non-existent document."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        with pytest.raises(ValueError, match="not found"):
            service.get_document_status('00000000-0000-0000-0000-000000000000')
    
    def test_delete_document_success(self):
        """Test deleting a document."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        doc = Document.objects.create(
            user=user,
            title='To Delete',
            file_type='txt',
            status='ready'
        )
        
        result = service.delete_document(str(doc.id))
        
        assert result is True
        assert not Document.objects.filter(id=doc.id).exists()
    
    def test_delete_document_not_found(self):
        """Test deleting non-existent document."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        with pytest.raises(ValueError, match="not found"):
            service.delete_document('00000000-0000-0000-0000-000000000000')
    
    def test_get_document_success(self):
        """Test getting document details."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = DocumentService(user)
        
        doc = Document.objects.create(
            user=user,
            title='Test Doc',
            file_type='txt',
            status='ready',
            summary='Test summary'
        )
        
        result = service.get_document(str(doc.id))
        
        assert result['id'] == str(doc.id)
        assert result['title'] == 'Test Doc'
        assert result['summary'] == 'Test summary'
