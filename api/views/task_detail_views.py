"""API views for task detail panel - comments, subtasks, time tracking."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Task
from core.services.task_detail_service import TaskDetailService
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_task_details(request, task_id):
    """Get full task details including comments, subtasks, time tracking."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    service = TaskDetailService(request.user)
    
    try:
        details = service.get_task_details(task_id)
        return Response(details)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception(f"Failed to get task details for {task_id}")
        return Response(
            {'error': 'Failed to retrieve task details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Comments
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_comment(request, task_id):
    """Add a comment to a task."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    content = request.data.get('content')
    mentions = request.data.get('mentions', [])
    
    if not content:
        return Response(
            {'error': 'content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    service = TaskDetailService(request.user)
    
    try:
        comment = service.add_comment(task_id, content, mentions)
        return Response(comment, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception(f"Failed to add comment to task {task_id}")
        return Response(
            {'error': 'Failed to add comment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def edit_comment(request, comment_id):
    """Edit an existing comment."""
    content = request.data.get('content')
    
    if not content:
        return Response(
            {'error': 'content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    service = TaskDetailService(request.user)
    
    try:
        success = service.edit_comment(comment_id, content)
        if success:
            return Response({'message': 'Comment updated'})
        else:
            return Response(
                {'error': 'Comment not found or not authorized'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        logger.exception(f"Failed to edit comment {comment_id}")
        return Response(
            {'error': 'Failed to edit comment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reply_to_comment(request, task_id, comment_id):
    """Reply to a comment."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    content = request.data.get('content')
    
    if not content:
        return Response(
            {'error': 'content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    service = TaskDetailService(request.user)
    
    try:
        reply = service.reply_to_comment(task_id, comment_id, content)
        return Response(reply, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception(f"Failed to reply to comment {comment_id}")
        return Response(
            {'error': 'Failed to add reply'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Subtasks
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_subtask(request, task_id):
    """Add a subtask."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    title = request.data.get('title')
    description = request.data.get('description', '')
    assignee_id = request.data.get('assignee_id')
    
    if not title:
        return Response(
            {'error': 'title is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    service = TaskDetailService(request.user)
    
    try:
        subtask = service.add_subtask(task_id, title, description, assignee_id)
        return Response(subtask, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception(f"Failed to add subtask to task {task_id}")
        return Response(
            {'error': 'Failed to add subtask'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_subtask(request, subtask_id):
    """Update a subtask."""
    status_val = request.data.get('status')
    title = request.data.get('title')
    
    service = TaskDetailService(request.user)
    
    try:
        success = service.update_subtask(subtask_id, status=status_val, title=title)
        if success:
            return Response({'message': 'Subtask updated'})
        else:
            return Response(
                {'error': 'Subtask not found or not authorized'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        logger.exception(f"Failed to update subtask {subtask_id}")
        return Response(
            {'error': 'Failed to update subtask'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_subtask(request, subtask_id):
    """Delete a subtask."""
    service = TaskDetailService(request.user)
    
    try:
        success = service.delete_subtask(subtask_id)
        if success:
            return Response({'message': 'Subtask deleted'})
        else:
            return Response(
                {'error': 'Subtask not found or not authorized'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        logger.exception(f"Failed to delete subtask {subtask_id}")
        return Response(
            {'error': 'Failed to delete subtask'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Time Tracking
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_timer(request, task_id):
    """Start a timer for a task."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    description = request.data.get('description', '')
    
    service = TaskDetailService(request.user)
    
    try:
        result = service.start_timer(task_id, description)
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception(f"Failed to start timer for task {task_id}")
        return Response(
            {'error': 'Failed to start timer'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stop_timer(request, entry_id):
    """Stop a running timer."""
    service = TaskDetailService(request.user)
    
    try:
        result = service.stop_timer(entry_id)
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)
    except Exception as e:
        logger.exception(f"Failed to stop timer {entry_id}")
        return Response(
            {'error': 'Failed to stop timer'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_manual_time(request, task_id):
    """Add manual time entry."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    duration = request.data.get('duration_minutes')
    description = request.data.get('description', '')
    date = request.data.get('date')
    
    if not duration:
        return Response(
            {'error': 'duration_minutes is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    service = TaskDetailService(request.user)
    
    try:
        entry = service.add_manual_time(task_id, int(duration), description, date)
        return Response(entry, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception(f"Failed to add manual time for task {task_id}")
        return Response(
            {'error': 'Failed to add time entry'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_time_entry(request, entry_id):
    """Delete a time entry."""
    service = TaskDetailService(request.user)
    
    try:
        success = service.delete_time_entry(entry_id)
        if success:
            return Response({'message': 'Time entry deleted'})
        else:
            return Response(
                {'error': 'Time entry not found or not authorized'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        logger.exception(f"Failed to delete time entry {entry_id}")
        return Response(
            {'error': 'Failed to delete time entry'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_active_timer(request):
    """Get currently running timer."""
    service = TaskDetailService(request.user)
    
    try:
        timer = service.get_active_timer()
        if timer:
            return Response(timer)
        else:
            return Response({'active': False})
    except Exception as e:
        logger.exception("Failed to get active timer")
        return Response(
            {'error': 'Failed to get timer'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
