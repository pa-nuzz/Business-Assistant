"""API views for document versioning."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Document
from core.services.document_version_service import DocumentVersionService
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_document_versions(request, document_id):
    """List all versions for a document."""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    service = DocumentVersionService(request.user)
    
    try:
        versions = service.get_versions(document)
        stats = service.get_version_stats(document)
        
        return Response({
            'document_id': str(document.id),
            'versions': versions,
            'stats': stats
        })
    except Exception as e:
        logger.exception(f"Failed to list versions for {document_id}")
        return Response(
            {'error': 'Failed to list versions'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_version_diff(request, document_id, version_number):
    """Get the diff for a specific version."""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    service = DocumentVersionService(request.user)
    
    try:
        result = service.get_version_diff(document, int(version_number))
        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result)
    except Exception as e:
        logger.exception(f"Failed to get diff for {document_id} v{version_number}")
        return Response(
            {'error': 'Failed to get diff'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def compare_versions(request, document_id):
    """Compare two versions of a document."""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    service = DocumentVersionService(request.user)
    
    version_1 = request.data.get('version_1')
    version_2 = request.data.get('version_2')
    
    if not version_1 or not version_2:
        return Response(
            {'error': 'Both version_1 and version_2 are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = service.compare_versions(document, int(version_1), int(version_2))
        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result)
    except Exception as e:
        logger.exception(f"Failed to compare versions for {document_id}")
        return Response(
            {'error': 'Failed to compare versions'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_version(request, document_id):
    """Manually create a new version for a document."""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    service = DocumentVersionService(request.user)
    
    change_summary = request.data.get('change_summary', 'Manual version creation')
    change_type = request.data.get('change_type', 'minor')
    
    try:
        version = service.create_version(
            document=document,
            change_summary=change_summary,
            change_type=change_type
        )
        
        return Response({
            'message': 'Version created',
            'version': {
                'id': str(version.id),
                'version_number': version.version_number,
                'change_summary': version.change_summary,
                'created_at': version.created_at.isoformat(),
            }
        })
    except Exception as e:
        logger.exception(f"Failed to create version for {document_id}")
        return Response(
            {'error': 'Failed to create version'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
