"""API views for semantic search."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.services.semantic_service import SemanticSearchService
import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def semantic_search(request):
    """Perform semantic search on document chunks."""
    query = request.data.get("query")
    document_ids = request.data.get("document_ids")
    top_k = request.data.get("top_k", 10)
    threshold = request.data.get("threshold", 0.7)
    
    if not query:
        return Response(
            {"error": "query is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        results = SemanticSearchService.search_by_text(
            query=query,
            user_id=request.user.id,
            document_ids=document_ids,
            top_k=int(top_k),
            threshold=float(threshold)
        )
        return Response(results)
    except Exception as e:
        logger.exception("Semantic search failed")
        return Response(
            {"error": "Search failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def conversational_retrieval(request):
    """Semantic search with conversation context."""
    query = request.data.get("query")
    conversation_history = request.data.get("conversation_history", [])
    top_k = request.data.get("top_k", 10)
    
    if not query:
        return Response(
            {"error": "query is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        results = SemanticSearchService.conversational_search(
            query=query,
            conversation_history=conversation_history,
            user_id=request.user.id,
            top_k=int(top_k)
        )
        return Response(results)
    except Exception as e:
        logger.exception("Conversational retrieval failed")
        return Response(
            {"error": "Retrieval failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_embeddings(request):
    """Generate embeddings for document chunks (placeholder)."""
    chunk_ids = request.data.get("chunk_ids")
    embedding_model = request.data.get("embedding_model", "text-embedding-3-small")
    
    try:
        results = SemanticSearchService.generate_embeddings(
            chunk_ids=chunk_ids,
            embedding_model=embedding_model
        )
        return Response(results)
    except Exception as e:
        logger.exception("Embedding generation failed")
        return Response(
            {"error": "Embedding generation failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
