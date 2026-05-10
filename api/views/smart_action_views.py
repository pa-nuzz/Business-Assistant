from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from agents.orchestrator import classify_smart_action
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_action_view(request):
    """
    Endpoint for natural language commands from the global command palette.
    """
    query = request.data.get('query', '').strip()
    if not query:
        return Response({"error": "No query provided"}, status=400)
    
    try:
        action = classify_smart_action(query, request.user.id)
        return Response(action)
    except Exception as e:
        logger.error(f"Smart action classification failed: {e}")
        return Response({"action": "CHAT", "params": {"message": query}})
