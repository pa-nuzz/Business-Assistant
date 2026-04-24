"""
Document service for handling document business logic.
Extracted from views to enable testing and reusability.
"""
import logging
import os
from typing import Dict, Optional
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from core.models import Document, DocumentChunk
from core.cache import CacheService
from core.events.event_bus import event_bus, EventTypes
from services.document import process_document
from utils.sanitization import validate_file_upload, sanitize_filename_strict

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for handling document operations."""
    
    def __init__(self, user):
        self.user = user
    
    def list_documents(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        Get user's documents with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            Dict with results, count, page, total_pages
        """
        page_size = min(page_size, 100)
        
        # Try cache first
        cache_key = f"documents:{self.user.id}:{page}:{page_size}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached
        
        docs = Document.objects.filter(user=self.user).select_related(
            'user'
        ).prefetch_related(
            'chunks'
        ).order_by("-created_at")
        
        paginator = Paginator(docs, page_size)
        page_obj = paginator.get_page(page)
        
        results = []
        for doc in page_obj.object_list:
            results.append({
                "id": str(doc.id),
                "title": doc.title,
                "file_type": doc.file_type,
                "status": doc.status,
                "created_at": doc.created_at,
            })
        
        result = {
            "results": results,
            "count": paginator.count,
            "page": page,
            "total_pages": paginator.num_pages,
        }
        
        # Cache for 2 minutes
        CacheService.set(cache_key, result, timeout=120)
        
        return result
    
    def upload_document(self, file, title: Optional[str] = None) -> Dict:
        """
        Upload and process a document.
        
        Args:
            file: Uploaded file object
            title: Optional title for the document
            
        Returns:
            Dict with document details
            
        Raises:
            ValueError: If validation fails
        """
        if not file:
            raise ValueError("No file provided")
        
        # Validate file upload
        try:
            validate_file_upload(file)
        except ValidationError as e:
            raise ValueError(str(e))
        
        # Determine file type
        if file.content_type == "application/pdf":
            file_type = "pdf"
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            file_type = "docx"
        elif file.content_type == "text/markdown":
            file_type = "md"
        else:
            file_type = "txt"
        
        # Sanitize filename
        safe_filename = sanitize_filename_strict(file.name)
        file.name = safe_filename
        
        doc = Document.objects.create(
            user=self.user,
            title=title or safe_filename,
            file=file,
            file_type=file_type,
            status="pending",
        )
        
        # Process document
        try:
            process_document(str(doc.id))
        except Exception as e:
            logger.exception(f"Document processing failed: {e}")
            doc.status = "failed"
            doc.save(update_fields=["status"])
        
        # Invalidate cache
        CacheService.invalidate_user_cache(self.user.id)
        
        # Publish event
        event_bus.publish(
            EventTypes.DOCUMENT_UPLOADED,
            {
                "document_id": str(doc.id),
                "title": doc.title,
                "user_id": self.user.id,
            },
            source="DocumentService"
        )
        
        return {
            "id": str(doc.id),
            "title": doc.title,
            "status": doc.status,
        }
    
    def get_document_status(self, doc_id: str) -> Dict:
        """
        Check document processing status.
        
        Args:
            doc_id: UUID of the document
            
        Returns:
            Dict with document status
            
        Raises:
            ValueError: If document not found
        """
        try:
            doc = Document.objects.get(id=doc_id, user=self.user)
            return {
                "id": str(doc.id),
                "status": doc.status,
                "title": doc.title,
            }
        except Document.DoesNotExist:
            raise ValueError("Document not found")
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and its chunks.
        
        Args:
            doc_id: UUID of the document
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If document not found
        """
        try:
            doc = Document.objects.get(id=doc_id, user=self.user)
            doc.delete()
            
            # Invalidate cache
            CacheService.invalidate_user_cache(self.user.id)
            CacheService.invalidate_document_cache(doc_id)
            
            # Publish event
            event_bus.publish(
                EventTypes.DOCUMENT_DELETED,
                {
                    "document_id": str(doc.id),
                    "user_id": self.user.id,
                },
                source="DocumentService"
            )
            
            return True
        except Document.DoesNotExist:
            raise ValueError("Document not found")
    
    def get_document(self, doc_id: str) -> Dict:
        """
        Get document details with chunks.
        
        Args:
            doc_id: UUID of the document
            
        Returns:
            Dict with document details and chunks
            
        Raises:
            ValueError: If document not found
        """
        try:
            doc = Document.objects.get(id=doc_id, user=self.user)
            
            chunks = []
            for chunk in doc.chunks.all():
                chunks.append({
                    "id": str(chunk.id),
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                })
            
            return {
                "id": str(doc.id),
                "title": doc.title,
                "file_type": doc.file_type,
                "status": doc.status,
                "summary": doc.summary,
                "created_at": doc.created_at,
                "chunks": chunks,
            }
        except Document.DoesNotExist:
            raise ValueError("Document not found")
    
    def get_safe_file_path(self, doc) -> str:
        """
        Ensure file path is within allowed storage directory.
        Prevents path traversal attacks.
        
        Args:
            doc: Document instance
            
        Returns:
            Safe file path
            
        Raises:
            ValueError: If path traversal detected
        """
        base_path = os.path.normpath(settings.MEDIA_ROOT)
        file_path = os.path.normpath(doc.file.path)
        
        # Ensure the resolved path is within MEDIA_ROOT
        if not file_path.startswith(base_path):
            raise ValueError("Invalid file path - path traversal detected")
        
        return file_path
