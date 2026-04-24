# Misc views - tags and utility endpoints
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Task, TaskTag


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def tags_list_create(request):
    """List or create tags."""
    if request.method == "GET":
        from django.core.paginator import Paginator
        
        page = int(request.GET.get("page", 1))
        page_size = min(int(request.GET.get("page_size", 50)), 100)
        
        tags = TaskTag.objects.filter(user=request.user).values("name", "color").distinct()
        
        paginator = Paginator(tags, page_size)
        page_obj = paginator.get_page(page)
        
        return Response({
            "results": list(page_obj.object_list),
            "count": paginator.count,
            "page": page,
            "total_pages": paginator.num_pages,
        })

    # POST - create new tag
    name = request.data.get("name", "").strip().lower()
    if not name:
        return Response({"error": "Tag name required"}, status=status.HTTP_400_BAD_REQUEST)

    TaskTag.objects.get_or_create(
        user=request.user,
        name=name,
        defaults={"color": "#6366F1"}
    )
    return Response({"created": True, "name": name})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tasks_by_tag(request, tag_name):
    """Filter tasks by tag."""
    from django.db.models import Q
    from django.core.paginator import Paginator

    page = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 20)), 100)

    user_tasks = Task.objects.filter(
        Q(created_by=request.user) | Q(assignee=request.user) | Q(user=request.user)
    )
    tagged_tasks = user_tasks.filter(tags__name=tag_name.lower())

    paginator = Paginator(tagged_tasks, page_size)
    page_obj = paginator.get_page(page)

    return Response({
        "tag": tag_name,
        "results": [{"id": str(t.id), "title": t.title, "status": t.status} for t in page_obj.object_list],
        "count": paginator.count,
        "page": page,
        "total_pages": paginator.num_pages,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def task_add_tag(request, task_id):
    """Tag a task."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    tag_name = request.data.get("tag", "").strip().lower()

    if not tag_name:
        return Response({"error": "Tag name required"}, status=status.HTTP_400_BAD_REQUEST)

    tag, _ = TaskTag.objects.get_or_create(
        user=request.user,
        name=tag_name,
        defaults={"color": "#6366F1"}
    )
    task.tags.add(tag)

    return Response({"added": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def task_remove_tag(request, task_id):
    """Remove tag from task."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    tag_name = request.data.get("tag", "").strip().lower()

    try:
        tag = TaskTag.objects.get(user=request.user, name=tag_name)
        task.tags.remove(tag)
    except TaskTag.DoesNotExist:
        pass

    return Response({"removed": True})
