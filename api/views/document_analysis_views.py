"""API views for document analysis and auto-extraction."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Document, DocumentChunk
from core.services.document_analysis_service import DocumentAnalysisService, DocumentProcessingPipeline
from core.services.semantic_service import SemanticSearchService
from services.gemini import get_embeddings
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def document_qa(request, document_id):
    """
    Ask a question about a specific document.
    
    Request body:
        question: The question to ask about the document
        top_k: Number of chunks to retrieve (default: 5)
    """
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    question = request.data.get('question', '').strip()
    if not question:
        return Response(
            {'error': 'Question is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    top_k = int(request.data.get('top_k', 5))
    
    try:
        # Generate query embedding
        from services.gemini import get_embeddings
        query_embeddings = get_embeddings([question])
        if not query_embeddings or not query_embeddings[0]:
            return Response(
                {'error': 'Failed to generate query embedding'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        query_embedding = query_embeddings[0]
        
        # Search document chunks
        from pgvector.django import CosineDistance
        chunks = DocumentChunk.objects.filter(
            document=document,
            embedding__isnull=False
        ).annotate(
            distance=CosineDistance('embedding', query_embedding)
        ).order_by('distance')[:int(request.data.get('top_k', 5))]
        
        # Build context from chunks
        context_parts = []
        sources = []
        for i, chunk in enumerate(chunks):
            similarity = 1.0 - chunk.distance
            context_parts.append(f"[Source {i+1} (page {chunk.page_number}, relevance: {similarity:.2f})]:\n{chunk.content}")
            sources.append({
                "chunk_id": str(chunk.id),
                "page": chunk.page_number,
                "relevance": round(similarity, 3),
                "snippet": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            })
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using LLM
        from services.model_layer import call_model, TaskType, Priority
        
        qa_prompt = f"""Answer the user's question based ONLY on the provided document context.

Document: {document.title}
Question: {question}

Context from document:
{context}

Instructions:
- Answer directly and conversationally
- Only use information from the provided context
- If the context doesn't contain the answer, say "I couldn't find that information in this document"
- Cite sources using [1], [2], etc. corresponding to the sources above
- Be concise but complete

Answer:"""

        result = call_model(
            user_id=request.user.id,
            user_message=qa_prompt,
            base_system_prompt="You are a document Q&A assistant. Answer questions using only the provided document context. Cite sources with [1], [2], etc.",
            task_type="analysis",
            priority="high",
            use_cache=False,
        )
        
        return Response({
            'question': question,
            'answer': result.text.strip() if result.text else "No answer generated",
            'document_id': str(document.id),
            'document_title': document.title,
            'sources': sources,
        })
        
    except Exception as e:
        logger.exception(f"Document Q&A failed for {document_id}")
        return Response(
            {'error': 'Q&A failed', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
