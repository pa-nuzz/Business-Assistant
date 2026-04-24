# Document management views
import logging
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes, throttle_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from core.models import Document, DocumentChunk
from services.document import process_document, extract_text, chunk_text, generate_summary
from services.tasks import process_document_task
from utils.sanitization import validate_file_upload, sanitize_filename_strict
from utils.audit import log_audit_action

logger = logging.getLogger(__name__)


def get_safe_file_path(doc):
    """
    Ensure file path is within allowed storage directory.
    Prevents path traversal attacks.
    """
    base_path = os.path.normpath(settings.MEDIA_ROOT)
    file_path = os.path.normpath(doc.file.path)
    
    # Ensure the resolved path is within MEDIA_ROOT
    if not file_path.startswith(base_path):
        raise ValueError("Invalid file path - path traversal detected")
    
    return file_path


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_list(request):
    """Get user's uploaded docs with pagination."""
    page = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 20)), 100)

    docs = Document.objects.filter(user=request.user).order_by("-created_at")

    from django.core.paginator import Paginator
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

    return Response({
        "results": results,
        "count": paginator.count,
        "page": page,
        "total_pages": paginator.num_pages,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
@throttle_classes([ScopedRateThrottle])
def upload_document(request):
    """Upload PDF/DOCX/TXT. Processing starts immediately."""
    upload_document.throttle_scope = "upload"
    file = request.FILES.get("file")
    if not file:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    # SECURITY: Validate file upload (Phase 3.3)
    try:
        validate_file_upload(file)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Determine file type
    if file.content_type == "application/pdf":
        file_type = "pdf"
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        file_type = "docx"
    elif file.content_type == "text/markdown":
        file_type = "md"
    else:
        file_type = "txt"

    # SECURITY: Sanitize filename
    safe_filename = sanitize_filename_strict(file.name)
    file.name = safe_filename

    doc = Document.objects.create(
        user=request.user,
        title=request.data.get("title", safe_filename),
        file=file,
        file_type=file_type,
        status="pending",
    )

    # Process document (sync for now, async via Celery in production)
    try:
        process_document(str(doc.id))
    except Exception as e:
        logger.exception(f"Document processing failed: {e}")
        doc.status = "error"
        doc.save(update_fields=["status"])

    return Response({
        "id": str(doc.id),
        "title": doc.title,
        "status": doc.status,
        "message": "Document uploaded and processing started.",
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_status(request, doc_id):
    """Check if doc is still processing."""
    try:
        doc = Document.objects.get(id=doc_id, user=request.user)
        return Response({
            "id": str(doc.id),
            "status": doc.status,
            "title": doc.title,
        })
    except Document.DoesNotExist:
        return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_document(request, doc_id):
    """Delete doc and its chunks."""
    try:
        doc = Document.objects.get(id=doc_id, user=request.user)
        doc_title = doc.title
        doc.delete()
        
        # Log the deletion
        log_audit_action(
            request.user,
            'delete',
            'document',
            str(doc_id),
            details={'title': doc_title},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({"deleted": True})
    except Document.DoesNotExist:
        return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_summary(request, doc_id):
    """Get AI-generated summary."""
    try:
        doc = Document.objects.get(id=doc_id, user=request.user)
        return Response({
            "id": str(doc.id),
            "title": doc.title,
            "summary": doc.summary or "Summary not available yet.",
            "status": doc.status,
        })
    except Document.DoesNotExist:
        return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_download(request, doc_id):
    """Return a signed URL for document download (60 seconds)."""
    try:
        doc = Document.objects.get(id=doc_id, user=request.user)
    except Document.DoesNotExist:
        return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

    # Generate signed URL (placeholder for S3 implementation)
    # TODO: Implement S3 presigned URL when S3 storage is configured
    from django.core.files.storage import default_storage
    try:
        url = default_storage.url(doc.file.name)
        return Response({
            "download_url": url,
            "expires_in": 60,
            "filename": doc.title,
        })
    except Exception as e:
        logger.exception(f"Failed to generate download URL for {doc_id}")
        return Response(
            {"error": "Failed to generate download URL"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reindex_document(request, doc_id):
    """Rechunk and reindex a document."""
    try:
        doc = Document.objects.get(id=doc_id, user=request.user)
    except Document.DoesNotExist:
        return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

    doc.status = "processing"
    doc.save(update_fields=["status"])

    try:
        # Delete old chunks
        old_chunk_count = DocumentChunk.objects.filter(document=doc).count()
        DocumentChunk.objects.filter(document=doc).delete()

        # Re-extract text with path traversal prevention
        file_path = get_safe_file_path(doc)
        text, page_count = extract_text(file_path, doc.file_type)

        if not text.strip():
            raise ValueError("No text could be extracted from document")

        # Re-chunk
        cfg = settings.DOCUMENT_CONFIG
        chunks_data = chunk_text(
            text,
            chunk_size=cfg["chunk_size_chars"],
            max_chunks=cfg["max_chunks_per_doc"],
        )

        # Regenerate summary
        summary = generate_summary(text, doc.title)

        # Save new chunks
        chunk_objects = [
            DocumentChunk(
                document=doc,
                chunk_index=c["chunk_index"],
                content=c["content"],
                keywords=c["keywords"],
            )
            for c in chunks_data
        ]
        DocumentChunk.objects.bulk_create(chunk_objects)

        # Update document
        doc.summary = summary
        doc.page_count = page_count
        doc.status = "ready"
        doc.save(update_fields=["summary", "page_count", "status"])

        return Response({
            "reindexed": True,
            "document_id": str(doc.id),
            "old_chunks": old_chunk_count,
            "new_chunks": len(chunks_data),
            "pages": page_count,
        })

    except ValueError as e:
        doc.status = "failed"
        doc.save(update_fields=["status"])
        logger.error(f"Path traversal attempt or invalid file: {e}")
        return Response(
            {"reindexed": False, "error": "Invalid document file"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        doc.status = "failed"
        doc.save(update_fields=["status"])
        logger.exception(f"Document reindexing failed for {doc_id}")
        return Response(
            {"reindexed": False, "error": "Document processing failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
