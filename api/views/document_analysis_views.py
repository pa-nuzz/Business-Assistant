"""API views for document analysis and auto-extraction."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Document
from core.services.document_analysis_service import DocumentAnalysisService, DocumentProcessingPipeline
import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_document(request, document_id):
    """Analyze a document and extract insights."""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    service = DocumentAnalysisService(request.user)
    
    try:
        analysis = service.analyze_document(document)
        return Response({
            'document_id': str(document.id),
            'analysis': analysis,
            'status': 'success'
        })
    except Exception as e:
        logger.exception(f"Document analysis failed for {document_id}")
        return Response(
            {'error': 'Analysis failed', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auto_extract_tasks(request, document_id):
    """
    Run auto-extraction on a document to suggest or create tasks.
    
    Query params:
        auto_create: If 'true', automatically create tasks (default: false)
    """
    document = get_object_or_404(Document, id=document_id, user=request.user)
    auto_create = request.query_params.get('auto_create', 'false').lower() == 'true'
    
    pipeline = DocumentProcessingPipeline(request.user)
    
    try:
        results = pipeline.process_document(document, auto_create_tasks=auto_create)
        return Response(results)
    except Exception as e:
        logger.exception(f"Auto-extraction failed for {document_id}")
        return Response(
            {'error': 'Auto-extraction failed', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document_insights(request, document_id):
    """Get all insights for a document including analysis and entities."""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    service = DocumentAnalysisService(request.user)
    
    try:
        analysis = service.analyze_document(document)
        entities = service.extract_entities(document)
        
        return Response({
            'document_id': str(document.id),
            'document_title': document.title,
            'summary': analysis.get('summary', ''),
            'key_topics': analysis.get('key_topics', []),
            'suggested_tasks': analysis.get('suggested_tasks', []),
            'extracted_entities': entities,
            'analysis_status': analysis.get('status', 'unknown')
        })
    except Exception as e:
        logger.exception(f"Failed to get insights for {document_id}")
        return Response(
            {'error': 'Failed to get insights', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
