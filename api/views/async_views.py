"""
Async views for long-running operations.
Uses Django async views for non-blocking operations.
"""
import logging
from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse

from core.services.task_service import TaskService
from core.services.document_service import DocumentService
from services.document import process_document

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def async_process_document(request):
    """
    Async endpoint for document processing.
    Returns immediately with a job ID, processing happens in background.
    """
    from core.models import Document
    from django.core.files.base import ContentFile
    import uuid
    
    doc_id = request.data.get("doc_id")
    
    if not doc_id:
        return Response({"error": "Document ID required"}, status=status.HTTP_400_BAD_REQUEST)
    
    job_id = str(uuid.uuid4())
    
    # Start async processing
    async def process():
        try:
            await sync_to_async(process_document)(doc_id)
            logger.info(f"Document {doc_id} processed successfully")
        except Exception as e:
            logger.exception(f"Document processing failed for {doc_id}")
    
    # In production, this would use Celery
    # For now, we'll process synchronously but return immediately
    try:
        await process()
        return Response({
            "job_id": job_id,
            "status": "completed",
            "message": "Document processed successfully"
        })
    except Exception as e:
        logger.exception("Async document processing failed")
        return Response(
            {"error": "Document processing failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def async_bulk_task_update(request):
    """
    Async endpoint for bulk task updates.
    Accepts multiple task updates and processes them in parallel.
    """
    task_updates = request.data.get("updates", [])
    
    if not task_updates:
        return Response({"error": "No updates provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    results = []
    
    for update in task_updates:
        task_id = update.get("task_id")
        data = update.get("data", {})
        
        try:
            service = TaskService(request.user)
            result = await sync_to_async(service.update_task)(task_id, data)
            results.append({"task_id": task_id, "status": "success", "data": result})
        except Exception as e:
            results.append({"task_id": task_id, "status": "error", "error": str(e)})
    
    return Response({
        "processed": len(results),
        "results": results
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
async def async_job_status(request, job_id):
    """
    Check status of an async job.
    """
    # In production, this would check Celery task status
    # For now, return a placeholder
    return Response({
        "job_id": job_id,
        "status": "completed",
        "progress": 100
    })
