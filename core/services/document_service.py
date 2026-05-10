"""
Document service for handling document business logic.
Extracted from views to enable testing and reusability.
"""
import logging
import os
import uuid
from typing import Dict, Optional
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from core.models import Document, DocumentChunk
from core.cache import CacheService
from core.events.event_bus import event_bus, EventTypes
from services.tasks import process_document_task
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
        
        # Simple query without cache to avoid issues
        docs = Document.objects.filter(user=self.user).order_by("-created_at")
        
        paginator = Paginator(docs, page_size)
        page_obj = paginator.get_page(page)
        
        results = []
        for doc in page_obj.object_list:
            results.append({
                "id": str(doc.id),
                "title": doc.title,
                "file_type": doc.file_type,
                "status": doc.status,
                "page_count": doc.page_count,
                "summary": doc.summary,
                "visual_analysis": doc.visual_analysis or {},
                "created_at": doc.created_at.isoformat(),
            })
        
        result = {
            "results": results,
            "count": paginator.count,
            "page": page,
            "total_pages": paginator.num_pages,
        }
        
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
        elif file.content_type.startswith("image/"):
            # Support png, jpg, jpeg
            file_type = file.content_type.split("/")[-1]
            if file_type not in ["png", "jpg", "jpeg"]:
                file_type = "img"
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
        
        # Process document asynchronously (Celery) to avoid blocking the HTTP request
        try:
            process_document_task.delay(str(doc.id))
        except Exception as e:
            logger.warning(f"Failed to queue document processing task: {e}. Processing inline.")
            from services.document import process_document
            try:
                process_document(str(doc.id))
            except Exception as inner_e:
                logger.exception(f"Document processing failed: {inner_e}")
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
            "file_type": doc.file_type,
            "created_at": doc.created_at.isoformat(),
                "processing_started": True,  # Indicate processing has been initiated
        }

    def get_document_summary(self, doc_id: str) -> Dict:
        """Get the stored summary for a processed document."""
        if not self._is_valid_uuid(doc_id):
            raise ValueError("Document not found")

        try:
            doc = Document.objects.get(id=doc_id, user=self.user)
            return {
                "id": str(doc.id),
                "title": doc.title,
                "summary": doc.summary or (
                    "This document has not produced a summary yet."
                    if doc.status != "ready"
                    else "No summary is available for this document."
                ),
                "pages": doc.page_count,
                "page_count": doc.page_count,
                "type": doc.file_type,
                "file_type": doc.file_type,
                "status": doc.status,
                "visual_analysis": doc.visual_analysis or {},
            }
        except Document.DoesNotExist:
            raise ValueError("Document not found")
    
    def get_document_status(self, doc_id: str) -> Dict:
        """
        Check document processing status with detailed information.
        
        Args:
            doc_id: UUID of the document
            
        Returns:
            Dict with comprehensive document status
            
        Raises:
            ValueError: If document not found
        """
        if not self._is_valid_uuid(doc_id):
            raise ValueError("Document not found")

        try:
            doc = Document.objects.get(id=doc_id, user=self.user)
            
            # Get chunk count for processing progress
            chunk_count = doc.chunks.count()
            
            # Determine processing stage
            stage = "uploaded"
            progress = 0
            estimated_time = None
            
            if doc.status == "pending":
                stage = "queued"
                progress = 10
                estimated_time = "2-5 minutes"
            elif doc.status == "processing":
                stage = "analyzing"
                progress = 50
                estimated_time = "1-2 minutes"
            elif doc.status == "ready":
                stage = "completed"
                progress = 100
                estimated_time = None
            elif doc.status == "failed":
                stage = "error"
                progress = 0
                estimated_time = None
            
            return {
                "id": str(doc.id),
                "status": doc.status,
                "title": doc.title,
                "file_type": doc.file_type,
                "stage": stage,
                "progress": progress,
                "chunk_count": chunk_count,
                "estimated_time_remaining": estimated_time,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "summary": doc.summary,
                "file_size": doc.file.size if doc.file else 0,
                "processing_details": {
                    "ocr_completed": doc.status in ["ready", "failed"],
                    "text_extracted": chunk_count > 0,
                    "embeddings_generated": chunk_count > 0,
                    "summary_available": bool(doc.summary),
                    "ready_for_chat": doc.status == "ready"
                }
            }
        except Document.DoesNotExist:
            raise ValueError("Document not found")
    
    def get_all_documents_status(self) -> Dict:
        """
        Get status of all user documents for dashboard display.
        
        Returns:
            Dict with comprehensive document status summary
        """
        try:
            docs = Document.objects.filter(user=self.user).order_by("-created_at")
            
            status_summary = {
                "total": docs.count(),
                "ready": docs.filter(status="ready").count(),
                "processing": docs.filter(status="processing").count(),
                "pending": docs.filter(status="pending").count(),
                "failed": docs.filter(status="failed").count(),
            }
            
            recent_docs = []
            for doc in docs[:10]:  # Last 10 documents
                recent_docs.append({
                    "id": str(doc.id),
                    "title": doc.title,
                    "status": doc.status,
                    "file_type": doc.file_type,
                    "created_at": doc.created_at.isoformat(),
                    "summary": doc.summary[:100] + "..." if doc.summary and len(doc.summary) > 100 else doc.summary,
                    "chunk_count": doc.chunks.count(),
                    "file_size": doc.file.size if doc.file else 0,
                })
            
            return {
                "status_summary": status_summary,
                "recent_documents": recent_docs,
                "processing_health": {
                    "success_rate": (status_summary["ready"] / max(status_summary["total"], 1)) * 100,
                    "average_processing_time": "2-3 minutes",  # Could be calculated from actual data
                    "needs_attention": status_summary["failed"] > 0,
                    "ready_for_analysis": status_summary["ready"] > 0,
                }
            }
        except Exception as e:
            logger.exception(f"Failed to get document status summary: {e}")
            return {
                "status_summary": {"total": 0, "ready": 0, "processing": 0, "pending": 0, "failed": 0},
                "recent_documents": [],
                "processing_health": {"success_rate": 0, "needs_attention": False, "ready_for_analysis": False}
            }
    
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
        if not self._is_valid_uuid(doc_id):
            raise ValueError("Document not found")

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
        if not self._is_valid_uuid(doc_id):
            raise ValueError("Document not found")

        try:
            doc = Document.objects.get(id=doc_id, user=self.user)
            
            chunks = []
            for chunk in doc.chunks.all():
                chunks.append({
                    "id": str(chunk.id),
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "keywords": chunk.keywords,
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

    @staticmethod
    def _is_valid_uuid(value) -> bool:
        try:
            uuid.UUID(str(value))
            return True
        except (TypeError, ValueError):
            return False
    
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
