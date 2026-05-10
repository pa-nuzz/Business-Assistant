import pytest
from django.contrib.auth.models import User
from core.models import AuditLog
from core.services.audit_service import AuditLogService
from unittest.mock import Mock


@pytest.fixture
def test_user(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.mark.django_db
class TestAuditLogService:
    def test_log_creation(self, test_user):
        audit_log = AuditLogService.log(
            event_type="test_event",
            user=test_user,
            severity="info",
            description="Test description",
        )
        assert audit_log is not None
        assert audit_log.event_type == "test_event"
        assert audit_log.user == test_user
        assert audit_log.description == "Test description"
        
        # Verify it was saved to the db
        db_log = AuditLog.objects.get(id=audit_log.id)
        assert db_log.event_type == "test_event"

    def test_log_auth_event_success(self, test_user):
        log = AuditLogService.log_auth_event(
            event_type="login",
            user=test_user,
            success=True,
            description="Login success"
        )
        assert log.severity == "info"
        assert log.event_type == "login"

    def test_log_auth_event_failure(self):
        log = AuditLogService.log_auth_event(
            event_type="login_failed",
            user=None,
            success=False,
            description="Invalid credentials"
        )
        assert log.severity == "warning"
        assert log.event_type == "login_failed"
        assert log.user is None

    def test_request_context_extraction(self, test_user):
        mock_request = Mock()
        mock_request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1',
            'HTTP_USER_AGENT': 'Mozilla/5.0',
            'HTTP_X_REQUEST_ID': 'req-12345'
        }
        
        log = AuditLogService.log(
            event_type="api_call",
            user=test_user,
            request=mock_request
        )
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Mozilla/5.0"
        assert log.request_id == "req-12345"
