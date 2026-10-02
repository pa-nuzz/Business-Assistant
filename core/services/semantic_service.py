"""Semantic search service using vector embeddings."""
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from core.models import DocumentChunk
import logging

try:
    from pgvector.django import CosineDistance
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

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
        
        Generates query embedding and performs vector similarity search using pgvector.
        Falls back to keyword search if embeddings unavailable.
        """
        logger.info(f"Semantic search query: '{query}' for user {user_id}")
        
        # Generate embedding for the query
        from services.gemini import get_embeddings
        query_embeddings = get_embeddings([query])
        
        if query_embeddings and query_embeddings[0]:
            query_embedding = query_embeddings[0]
            return SemanticSearchService.search_by_embedding(
                query_embedding=query_embedding,
                user_id=user_id,
                document_ids=document_ids,
                top_k=top_k,
                threshold=threshold
            )
        
        # Fallback: keyword-based search
        logger.warning("Embedding generation failed, falling back to keyword search")
        return SemanticSearchService._keyword_search_fallback(
            query=query,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
            threshold=threshold
        )

    @staticmethod
    def _keyword_search_fallback(
        query: str,
        user_id: int,
        document_ids: List[str] = None,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Fallback keyword-based search when embeddings unavailable."""
        logger.info(f"Keyword fallback search for query: '{query}'")
        
        chunks = DocumentChunk.objects.filter(
            document__user_id=user_id
        ).select_related('document')
        
        if document_ids:
            chunks = chunks.filter(document_id__in=document_ids)
        
        results = []
        query_terms = query.lower().split()
        
        for chunk in chunks:
            score = 0
            content_lower = chunk.content.lower()
            keywords_lower = [k.lower() for k in chunk.keywords]
            
            for term in query_terms:
                if term in content_lower:
                    score += 0.5
                if term in keywords_lower:
                    score += 1.0
            
            if query_terms:
                score /= len(query_terms)
            
            if score > threshold / 2:
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
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'query': query,
            'results': results[:top_k],
            'total_chunks_searched': chunks.count(),
            'search_method': 'keyword_fallback',
            'note': 'Vector embeddings unavailable. Using keyword search as fallback.'
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
        
        Uses pgvector's HNSW index with cosine distance for efficient similarity search.
        """
        logger.info(f"Vector search for user {user_id}")
        
        # Get chunks with embeddings
        chunks = DocumentChunk.objects.filter(
            document__user_id=user_id,
            embedding__isnull=False
        ).select_related('document')
        
        if document_ids:
            chunks = chunks.filter(document_id__in=document_ids)
        
        # Use pgvector's CosineDistance for efficient vector search with HNSW index
        if PGVECTOR_AVAILABLE:
            chunks = chunks.annotate(
                distance=CosineDistance('embedding', query_embedding)
            ).order_by('distance')[:top_k]
            
            results = []
            for chunk in chunks:
                # Convert distance to similarity score (1 - distance)
                similarity = max(0.0, 1.0 - getattr(chunk, 'distance', 1.0))
                
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
                        'search_method': 'pgvector_hnsw_cosine'
                    })
            
            return {
                'query_embedding_shape': len(query_embedding),
                'results': results,
                'total_chunks_searched': chunks.count(),
                'search_method': 'pgvector_hnsw_cosine',
                'note': 'Using pgvector HNSW index with cosine distance.'
            }
        else:
            # Fallback to Python cosine similarity
            logger.warning("pgvector not available, falling back to Python cosine similarity")
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
                        'search_method': 'cosine_similarity_fallback'
                    })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'query_embedding_shape': len(query_embedding),
                'results': results[:top_k],
                'total_chunks_searched': chunks.count(),
                'search_method': 'cosine_similarity_fallback',
                'note': 'pgvector not available. Using Python cosine similarity fallback.'
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
        chunks = DocumentChunk.objects.filter(embedding__isnull=True)
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


class SemanticMemoryService:
    """Service for semantic search on UserMemory facts."""
    
    @staticmethod
    def search_by_text(
        query: str,
        user_id: int,
        category: str = None,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for user memories by text query.
        
        Generates query embedding and performs vector similarity search on UserMemory.
        Falls back to keyword search if embeddings unavailable.
        """
        logger.info(f"Semantic memory search query: '{query}' for user {user_id}")
        
        # Generate embedding for the query
        from services.gemini import get_embeddings
        query_embeddings = get_embeddings([query])
        
        if query_embeddings and query_embeddings[0]:
            query_embedding = query_embeddings[0]
            return SemanticMemoryService.search_by_embedding(
                query_embedding=query_embedding,
                user_id=user_id,
                category=category,
                top_k=top_k,
                threshold=threshold
            )
        
        # Fallback: keyword-based search
        logger.warning("Embedding generation failed, falling back to keyword search")
        return SemanticMemoryService._keyword_search_fallback(
            query=query,
            user_id=user_id,
            category=category,
            top_k=top_k,
            threshold=threshold
        )
    
    @staticmethod
    def _keyword_search_fallback(
        query: str,
        user_id: int,
        category: str = None,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Fallback keyword-based search when embeddings unavailable."""
        logger.info(f"Keyword fallback memory search for query: '{query}'")
        
        from core.models import UserMemory
        
        memories = UserMemory.objects.filter(user_id=user_id)
        if category:
            memories = memories.filter(category=category)
        
        results = []
        query_terms = query.lower().split()
        
        for memory in memories:
            score = 0
            content_lower = memory.value.lower()
            key_lower = memory.key.lower()
            
            for term in query_terms:
                if term in content_lower:
                    score += 0.5
                if term in key_lower:
                    score += 1.0
            
            if query_terms:
                score /= len(query_terms)
            
            if score > threshold / 2:
                results.append({
                    'memory_id': str(memory.id),
                    'key': memory.key,
                    'value': memory.value[:500],
                    'category': memory.category,
                    'created_at': memory.created_at.isoformat(),
                    'score': round(score, 3),
                    'search_method': 'keyword_fallback'
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'query': query,
            'results': results[:top_k],
            'total_memories_searched': memories.count(),
            'search_method': 'keyword_fallback',
            'note': 'Vector embeddings unavailable. Using keyword search as fallback.'
        }
    
    @staticmethod
    def search_by_embedding(
        query_embedding: List[float],
        user_id: int,
        category: str = None,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for similar user memories using vector embedding.
        
        Uses pgvector's HNSW index with cosine distance for efficient similarity search.
        """
        logger.info(f"Vector memory search for user {user_id}")
        
        from core.models import UserMemory
        from pgvector.django import CosineDistance
        
        # Get memories with embeddings
        memories = UserMemory.objects.filter(
            user_id=user_id,
            embedding__isnull=False
        )
        
        if category:
            memories = memories.filter(category=category)
        
        # Use pgvector's CosineDistance for efficient vector search
        if PGVECTOR_AVAILABLE:
            memories = memories.annotate(
                distance=CosineDistance('embedding', query_embedding)
            ).order_by('distance')[:10]
            
            results = []
            for memory in memories:
                # Convert distance to similarity score (1 - distance)
                similarity = max(0.0, 1.0 - getattr(memory, 'distance', 1.0))
                
                if similarity >= threshold:
                    results.append({
                        'memory_id': str(memory.id),
                        'key': memory.key,
                        'value': memory.value[:500],
                        'category': memory.category,
                        'created_at': memory.created_at.isoformat(),
                        'score': round(similarity, 3),
                        'search_method': 'pgvector_hnsw_cosine'
                    })
            
            return {
                'query_embedding_shape': len(query_embedding),
                'results': results,
                'total_memories_searched': memories.count(),
                'search_method': 'pgvector_hnsw_cosine',
                'note': 'Using pgvector with cosine distance.'
            }
        else:
            # Fallback to Python cosine similarity
            logger.warning("pgvector not available, falling back to Python cosine similarity")
            results = []
            
            from core.models import UserMemory
            memories = UserMemory.objects.filter(
                user_id=user_id,
                embedding__isnull=False
            )
            if category:
                memories = memories.filter(category=category)
            
            results = []
            
            for memory in memories:
                similarity = memory.cosine_similarity(query_embedding)
                
                if similarity >= threshold:
                    results.append({
                        'memory_id': str(memory.id),
                        'key': memory.key,
                        'value': memory.value[:500],
                        'category': memory.category,
                        'created_at': memory.created_at.isoformat(),
                        'score': round(similarity, 3),
                        'search_method': 'cosine_similarity_fallback'
                    })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'query_embedding_shape': len(query_embedding),
                'results': results[:10],
                'total_memories_searched': memories.count(),
                'search_method': 'cosine_similarity_fallback',
                'note': 'pgvector not available. Using Python cosine similarity fallback.'
            }
    
    @staticmethod
    def generate_embeddings(
        memory_ids: List[str] = None,
        embedding_model: str = "gemini-embedding-001"
    ) -> Dict[str, Any]:
        """
        Generate embeddings for UserMemory facts.
        """
        from core.models import UserMemory
        from services.gemini import get_embeddings
        from django.utils import timezone
        
        logger.info(f"Generating memory embeddings for model: {embedding_model}")
        
        # Get memories without embeddings
        memories = UserMemory.objects.filter(embedding__isnull=True)
        if memory_ids:
            memories = memories.filter(id__in=memory_ids)
        
        total_memories = memories.count()
        if total_memories == 0:
            return {
                'total_memories_pending': 0,
                'embedding_model': embedding_model,
                'status': 'complete',
                'note': 'No memories need embeddings.'
            }
        
        # Process in batches
        batch_size = 20
        processed = 0
        
        for i in range(0, total_memories, batch_size):
            batch = list(memories[i:i+batch_size])
            texts = [m.value for m in batch]
            
            try:
                batch_embeddings = get_embeddings(texts)
                if batch_embeddings:
                    for memory, embedding in zip(batch, batch_embeddings):
                        if embedding:
                            memory.embedding = embedding
                            memory.embedding_model = "gemini-embedding-001"
                            memory.embedding_generated_at = timezone.now()
                            memory.save(update_fields=['embedding', 'embedding_model', 'embedding_generated_at'])
                            processed += 1
            except Exception as e:
                logger.warning(f"Failed to generate embeddings for batch: {e}")
        
        return {
            'total_memories_pending': total_memories,
            'embedding_model': "gemini-embedding-001",
            'processed': processed,
            'status': 'completed' if processed == total_memories else 'partial',
            'note': f'Processed {processed}/{total_memories} memories.'
        }
