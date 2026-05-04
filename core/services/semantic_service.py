"""Semantic search service using vector embeddings."""
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from core.models import DocumentChunk
import logging

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Service for semantic search using vector embeddings."""

    @staticmethod
    def search_by_text(
        query: str,
        user_id: int,
        document_ids: List[str] = None,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for document chunks by text query.
        
        This is a placeholder implementation that uses keyword matching.
        In production, this would:
        1. Generate embeddings for the query using an embedding model
        2. Perform vector similarity search using pgvector
        
        For now, we fall back to keyword search on content and keywords.
        """
        logger.info(f"Semantic search query: '{query}' for user {user_id}")
        
        # Get all chunks for user's documents
        chunks = DocumentChunk.objects.filter(
            document__user_id=user_id
        ).select_related('document')
        
        if document_ids:
            chunks = chunks.filter(document_id__in=document_ids)
        
        # Fallback: keyword-based search
        results = []
        query_terms = query.lower().split()
        
        for chunk in chunks:
            # Calculate simple keyword relevance score
            score = 0
            content_lower = chunk.content.lower()
            keywords_lower = [k.lower() for k in chunk.keywords]
            
            for term in query_terms:
                # Content match
                if term in content_lower:
                    score += 0.5
                # Keyword match
                if term in keywords_lower:
                    score += 1.0
            
            # Normalize by number of terms
            if query_terms:
                score /= len(query_terms)
            
            if score > threshold / 2:  # Lower threshold for keyword matching
                results.append({
                    'chunk_id': str(chunk.id),
                    'document_id': str(chunk.document_id),
                    'document_title': chunk.document.title,
                    'content': chunk.content[:500],
                    'page_number': chunk.page_number,
                    'score': round(score, 3),
                    'keywords': chunk.keywords,
                    'has_embedding': chunk.has_embedding(),
                    'search_method': 'keyword_fallback'
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'query': query,
            'results': results[:top_k],
            'total_chunks_searched': chunks.count(),
            'search_method': 'keyword_fallback',
            'note': 'Vector embeddings not yet enabled. Using keyword search as fallback.'
        }

    @staticmethod
    def search_by_embedding(
        query_embedding: List[float],
        user_id: int,
        document_ids: List[str] = None,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for similar document chunks using vector embedding.
        
        This is the proper semantic search implementation.
        In production with pgvector:
        - Use cosine similarity: SELECT * ORDER BY embedding <=> query_embedding
        - Filter by user_id and optional document_ids
        """
        logger.info(f"Vector search for user {user_id}")
        
        # Get chunks with embeddings
        chunks = DocumentChunk.objects.filter(
            document__user_id=user_id,
            embedding__isnull=False
        ).exclude(embedding=[]).select_related('document')
        
        if document_ids:
            chunks = chunks.filter(document_id__in=document_ids)
        
        # Calculate cosine similarity for each chunk (inefficient for large datasets)
        # In production, use pgvector's <=> operator
        results = []
        
        for chunk in chunks:
            similarity = chunk.cosine_similarity(query_embedding)
            
            if similarity >= threshold:
                results.append({
                    'chunk_id': str(chunk.id),
                    'document_id': str(chunk.document_id),
                    'document_title': chunk.document.title,
                    'content': chunk.content[:500],
                    'page_number': chunk.page_number,
                    'score': round(similarity, 3),
                    'keywords': chunk.keywords,
                    'has_embedding': True,
                    'search_method': 'cosine_similarity'
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'query_embedding_shape': len(query_embedding),
            'results': results[:top_k],
            'total_chunks_searched': chunks.count(),
            'search_method': 'cosine_similarity',
            'note': 'Using Python cosine similarity. Enable pgvector for production scale.'
        }

    @staticmethod
    def generate_embeddings(
        chunk_ids: List[str] = None,
        embedding_model: str = "text-embedding-3-small"
    ) -> Dict[str, Any]:
        """
        Generate embeddings for document chunks.
        
        This is a placeholder. In production:
        1. Call OpenAI/text-embedding-3-small API
        2. Store results in chunk.embedding field
        """
        logger.info(f"Generating embeddings for model: {embedding_model}")
        
        # Get chunks without embeddings
        chunks = DocumentChunk.objects.filter(embedding=[])
        if chunk_ids:
            chunks = chunks.filter(id__in=chunk_ids)
        
        total_chunks = chunks.count()
        
        # Placeholder: return metadata
        return {
            'total_chunks_pending': total_chunks,
            'embedding_model': embedding_model,
            'status': 'not_implemented',
            'note': 'Embedding generation not yet implemented. Use OpenAI API for text-embedding-3-small.'
        }

    @staticmethod
    def conversational_search(
        query: str,
        conversation_history: List[Dict],
        user_id: int,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Semantic search with conversation context.
        
        Enhances the query with conversation history for better context understanding.
        """
        # Build context-aware query
        context_parts = [query]
        
        # Add recent conversation context
        for msg in conversation_history[-3:]:  # Last 3 messages
            if msg.get('role') == 'assistant':
                # Include relevant assistant responses as context
                if 'summary' in msg.get('content', '').lower() or 'extracted' in msg.get('content', '').lower():
                    context_parts.append(msg['content'])
        
        enhanced_query = " ".join(context_parts)
        
        # Perform search
        results = SemanticSearchService.search_by_text(
            query=enhanced_query,
            user_id=user_id,
            top_k=top_k
        )
        
        results['original_query'] = query
        results['enhanced_query'] = enhanced_query
        results['conversation_context_used'] = len(conversation_history) > 0
        
        return results
