"""Query Optimizer - Database query optimization utilities."""
import logging
from typing import List, Optional, Type, Any
from django.db import models
from django.db.models import QuerySet, Prefetch

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Service for optimizing database queries."""

    @staticmethod
    def optimize_task_queryset(
        queryset: QuerySet,
        include_user: bool = True,
        include_workspace: bool = True,
        include_tags: bool = True
    ) -> QuerySet:
        """Optimize task queryset with select_related and prefetch_related."""
        select_related = []
        prefetch_related = []
        
        if include_user:
            select_related.append('user')
            select_related.append('assigned_to')
        
        if include_workspace:
            select_related.append('workspace')
        
        if include_tags and hasattr(queryset.model, 'tags'):
            prefetch_related.append('tags')
        
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        return queryset

    @staticmethod
    def optimize_document_queryset(
        queryset: QuerySet,
        include_user: bool = True,
        include_workspace: bool = True
    ) -> QuerySet:
        """Optimize document queryset."""
        select_related = []
        
        if include_user:
            select_related.append('user')
        
        if include_workspace:
            select_related.append('workspace')
        
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        return queryset

    @staticmethod
    def optimize_conversation_queryset(
        queryset: QuerySet,
        include_user: bool = True,
        include_messages: bool = False
    ) -> QuerySet:
        """Optimize conversation queryset."""
        select_related = []
        prefetch_related = []
        
        if include_user:
            select_related.append('user')
        
        if include_messages and hasattr(queryset.model, 'messages'):
            prefetch_related.append('messages')
        
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        return queryset

    @staticmethod
    def add_index_hints(queryset: QuerySet, fields: List[str]) -> QuerySet:
        """Add database index hints (PostgreSQL)."""
        # Note: Django doesn't support index hints directly
        # This is a placeholder for future database-specific optimizations
        return queryset

    @staticmethod
    def bulk_update_with_timestamp(
        model_class: Type[models.Model],
        objects: List[Any],
        fields: List[str],
        batch_size: int = 1000
    ) -> int:
        """Bulk update objects with automatic timestamp update."""
        if hasattr(model_class, 'updated_at'):
            fields = list(set(fields + ['updated_at']))
        
        count = model_class.objects.bulk_update(objects, fields, batch_size=batch_size)
        logger.info(f"Bulk updated {count} {model_class.__name__} objects")
        return count

    @staticmethod
    def chunked_queryset(
        queryset: QuerySet,
        chunk_size: int = 1000
    ):
        """Yield queryset in chunks to avoid loading all objects in memory."""
        offset = 0
        while True:
            chunk = list(queryset[offset:offset + chunk_size])
            if not chunk:
                break
            yield chunk
            offset += chunk_size

    @staticmethod
    def get_only_required_fields(
        queryset: QuerySet,
        fields: List[str]
    ) -> QuerySet:
        """Optimize by fetching only required fields."""
        return queryset.only(*fields)

    @staticmethod
    def defer_large_fields(
        queryset: QuerySet,
        fields: List[str]
    ) -> QuerySet:
        """Defer large fields to reduce memory usage."""
        return queryset.defer(*fields)


class NPlusOneDetector:
    """Detect and log potential N+1 query issues."""
    
    @staticmethod
    def check_queryset(queryset: QuerySet, accessed_relations: List[str]) -> List[str]:
        """Check if accessed relations are properly prefetched."""
        warnings = []
        
        # Get existing prefetches
        existing_prefetches = set()
        if hasattr(queryset, '_prefetch_related_lookups'):
            existing_prefetches = set(queryset._prefetch_related_lookups)
        
        # Get existing select_related
        existing_select_related = set()
        if hasattr(queryset, '_setup_query'):
            # Access select_related through the query object
            try:
                existing_select_related = set(queryset.query.select_related.keys())
            except AttributeError:
                pass
        
        for relation in accessed_relations:
            parts = relation.split('__')
            base_relation = parts[0]
            
            if base_relation not in existing_prefetches and base_relation not in existing_select_related:
                warnings.append(
                    f"Potential N+1: '{relation}' accessed but not prefetched. "
                    f"Consider adding .prefetch_related('{base_relation}') or .select_related('{base_relation}')"
                )
        
        for warning in warnings:
            logger.warning(warning)
        
        return warnings


def optimize_list_queryset(
    queryset: QuerySet,
    model_name: str = 'object'
) -> QuerySet:
    """Generic optimization for list view querysets."""
    # Get all ForeignKey fields
    fk_fields = [
        f.name for f in queryset.model._meta.get_fields()
        if isinstance(f, models.ForeignKey)
    ]
    
    # Get all ManyToMany fields
    m2m_fields = [
        f.name for f in queryset.model._meta.get_fields()
        if isinstance(f, models.ManyToManyField)
    ]
    
    # Auto-select related foreign keys
    if fk_fields:
        queryset = queryset.select_related(*fk_fields)
        logger.debug(f"Auto-select_related for {model_name}: {fk_fields}")
    
    # Auto-prefetch related many-to-many
    if m2m_fields:
        queryset = queryset.prefetch_related(*m2m_fields)
        logger.debug(f"Auto-prefetch_related for {model_name}: {m2m_fields}")
    
    return queryset
