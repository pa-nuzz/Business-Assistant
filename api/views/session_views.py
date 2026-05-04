"""Session management views for user security."""
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.sessions.models import Session
from django.utils import timezone


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def list_sessions(request):
    """List all active sessions for the current user."""
    # Get all sessions for this user
    sessions = []
    for session in Session.objects.filter(expire_date__gt=timezone.now()):
        session_data = session.get_decoded()
        if str(request.user.id) == str(session_data.get('_auth_user_id')):
            sessions.append({
                "session_key": session.session_key[:8] + "...",
                "expire_date": session.expire_date.isoformat(),
                "is_current": session.session_key == request.session.session_key,
            })
    
    return Response({"sessions": sessions})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def revoke_session(request):
    """Revoke a specific session."""
    session_key = request.data.get("session_key", "").replace("...", "")
    
    # Find and delete the session
    for session in Session.objects.filter(expire_date__gt=timezone.now()):
        if session.session_key.startswith(session_key):
            session_data = session.get_decoded()
            if str(request.user.id) == str(session_data.get('_auth_user_id')):
                session.delete()
                return Response({"ok": True, "message": "Session revoked"})
    
    return Response({"error": "Session not found"}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def revoke_all_other_sessions(request):
    """Revoke all sessions except the current one."""
    current_session_key = request.session.session_key
    revoked_count = 0
    
    for session in Session.objects.filter(expire_date__gt=timezone.now()):
        if session.session_key != current_session_key:
            session_data = session.get_decoded()
            if str(request.user.id) == str(session_data.get('_auth_user_id')):
                session.delete()
                revoked_count += 1
    
    return Response({"ok": True, "revoked_count": revoked_count})
