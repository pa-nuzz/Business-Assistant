# Document management views
import logging

from django.conf import settings
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

logger = logging.getLogger(__name__)


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

    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    if file.content_type not in allowed_types:
        return Response(
            {"error": "Invalid file type. Use PDF, DOCX, or TXT."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if file.content_type == "application/pdf":
        file_type = "pdf"
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        file_type = "docx"
    else:
        file_type = "txt"

    doc = Document.objects.create(
        user=request.user,
        title=request.data.get("title", file.name),
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
    deleted, _ = Document.objects.filter(id=doc_id, user=request.user).delete()
    if not deleted:
        return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response({"deleted": True})


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

        # Re-extract text
        file_path = doc.file.path
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

    except Exception as e:
        doc.status = "failed"
        doc.save(update_fields=["status"])
        logger.exception(f"Document reindexing failed for {doc_id}")
        return Response(
            {"reindexed": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
