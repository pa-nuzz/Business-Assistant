# Document management views
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes, throttle_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from core.services.document_service import DocumentService
from utils.audit import log_audit_action

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_list(request):
    """Get user's uploaded docs with pagination."""
    service = DocumentService(request.user)
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    try:
        result = service.list_documents(page, page_size)
        return Response(result)
    except Exception as e:
        logger.exception("Failed to list documents")
        return Response(
            {"error": "Failed to retrieve documents"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
@throttle_classes([ScopedRateThrottle])
def upload_document(request):
    """Upload PDF/DOCX/TXT. Processing starts immediately."""
    upload_document.throttle_scope = "upload"
    service = DocumentService(request.user)
    file = request.FILES.get("file")
    title = request.data.get("title")

    try:
        result = service.upload_document(file, title)
        return Response({
            "message": "Document uploaded and processing started.",
            **result
        }, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Failed to upload document")
        return Response(
            {"error": "Failed to upload document"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_status(request, doc_id):
    """Check if doc is still processing."""
    service = DocumentService(request.user)

    try:
        result = service.get_document_status(doc_id)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Failed to get document status")
        return Response(
            {"error": "Failed to retrieve document status"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_document(request, doc_id):
    """Delete doc and its chunks."""
    service = DocumentService(request.user)

    try:
        service.delete_document(doc_id)
        return Response({"message": "Document deleted successfully"})
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Failed to delete document")
        return Response(
            {"error": "Failed to delete document"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_download(request, doc_id):
    """Return a signed URL for document download (60 seconds)."""
    service = DocumentService(request.user)

    try:
        doc = service.get_document(doc_id)
        # Generate signed URL logic would go here
        return Response({"message": "Download URL generation not implemented"})
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("Failed to generate download URL")
        return Response(
            {"error": "Failed to generate download URL"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
