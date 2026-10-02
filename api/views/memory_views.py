"""Memory Management API Views."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import UserMemory
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_memories(request):
    """List user's memories with optional category filter."""
    category = request.query_params.get('category')
    
    memories = UserMemory.objects.filter(user=request.user)
    if category:
        memories = memories.filter(category=category)
    
    memories = memories.order_by('-updated_at')
    
    results = []
    for memory in memories:
        results.append({
            'id': str(memory.id),
            'key': memory.key,
            'value': memory.value,
            'category': memory.category,
            'source_conversation': str(memory.source_conversation) if memory.source_conversation else None,
            'has_embedding': memory.has_embedding(),
            'embedding_model': memory.embedding_model,
            'embedding_generated_at': memory.embedding_generated_at.isoformat() if memory.embedding_generated_at else None,
            'created_at': memory.created_at.isoformat(),
            'updated_at': memory.updated_at.isoformat(),
        })
    
    return Response({'memories': results, 'count': len(results)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_memory(request):
    """Create or update a user memory."""
    key = request.data.get('key', '').strip()
    value = request.data.get('value', '').strip()
    category = request.data.get('category', 'fact')
    
    if not key or not value:
        return Response(
            {'error': 'Key and value are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from core.models import UserMemory
    memory, created = UserMemory.objects.update_or_create(
        user=request.user,
        key=key,
        defaults={
            'value': value,
            'category': category,
        }
    )
    
    # Trigger embedding generation asynchronously
    if created or memory.value != value:
        from services.tasks import generate_memory_embeddings_task
        generate_memory_embeddings_task.delay(memory_ids=[str(memory.id)])
    
    return Response({
        'id': str(memory.id),
        'key': memory.key,
        'value': memory.value,
        'category': memory.category,
        'created': created,
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_memory(request, memory_id):
    """Get a specific memory by ID."""
    memory = get_object_or_404(UserMemory, id=memory_id, user=request.user)
    
    return Response({
        'id': str(memory.id),
        'key': memory.key,
        'value': memory.value,
        'category': memory.category,
        'source_conversation': str(memory.source_conversation) if memory.source_conversation else None,
        'has_embedding': memory.has_embedding(),
        'embedding_model': memory.embedding_model,
        'embedding_generated_at': memory.embedding_generated_at.isoformat() if memory.embedding_generated_at else None,
        'created_at': memory.created_at.isoformat(),
        'updated_at': memory.updated_at.isoformat(),
    })


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_memory(request, memory_id):
    """Update a specific memory."""
    memory = get_object_or_404(UserMemory, id=memory_id, user=request.user)
    
    value = request.data.get('value')
    category = request.data.get('category')
    
    if value is not None:
        memory.value = value.strip()
    if category is not None:
        memory.category = category
    
    memory.save(update_fields=['value', 'category', 'updated_at'] if value is not None and category is not None else 
                ['value', 'updated_at'] if value is not None else 
                ['category', 'updated_at'])
    
    # Trigger embedding regeneration if value changed
    if value is not None:
        from services.tasks import generate_memory_embeddings_task
        generate_memory_embeddings_task.delay(memory_ids=[str(memory.id)])
    
    return Response({
        'id': str(memory.id),
        'key': memory.key,
        'value': memory.value,
        'category': memory.category,
        'updated_at': memory.updated_at.isoformat(),
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_memory(request, memory_id):
    """Delete a specific memory."""
    memory = get_object_or_404(UserMemory, id=memory_id, user=request.user)
    key = memory.key
    memory.delete()
    
    return Response({
        'deleted': True,
        'key': key,
        'message': f"Memory '{key}' deleted successfully"
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def regenerate_embeddings(request):
    """Trigger embedding regeneration for all user memories or specific ones."""
    memory_ids = request.data.get('memory_ids')
    
    from services.tasks import generate_memory_embeddings_task
    task = generate_memory_embeddings_task.delay(memory_ids=memory_ids)
    
    return Response({
        'task_id': task.id,
        'status': 'started',
        'memory_ids': memory_ids,
    })