"""
Unit tests for AuthService.
"""
import pytest
from django.contrib.auth.models import User
from core.services.auth_service import AuthService
from core.models import EmailVerification, PasswordResetCode
from unittest.mock import patch


@pytest.mark.django_db
class TestAuthService:
    """Test cases for AuthService."""
    
    def test_register_success(self):
        """Test successful user registration."""
        with patch('core.services.auth_service.send_verification_email') as mock_email:
            mock_email.return_value = True
            
            result = AuthService.register('testuser', 'testpass123', 'test@example.com')
            
            assert User.objects.filter(username='testuser').exists()
            assert result['username'] == 'testuser'
            assert result['email'] == 'test@example.com'
            assert result['verification_required'] is True
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        User.objects.create_user(username='testuser', password='pass123', email='existing@example.com')
        
        with pytest.raises(ValueError, match="already taken"):
            AuthService.register('testuser', 'testpass123', 'new@example.com')
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        User.objects.create_user(username='existing', password='pass123', email='test@example.com')
        
        with pytest.raises(ValueError, match="already exists"):
            AuthService.register('newuser', 'testpass123', 'test@example.com')
    
    def test_register_short_password(self):
        """Test registration with short password."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            AuthService.register('testuser', 'short', 'test@example.com')
    
    def test_verify_email_success(self):
        """Test successful email verification."""
        user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com', is_active=False)
        verification = EmailVerification.objects.create(user=user)
        verification.set_code('123456')
        verification.save()
        
        with patch('core.services.auth_service.send_welcome_email'):
            result = AuthService.verify_email('testuser', '123456')
        
        assert result['verified'] is True
        assert 'access' in result
        assert 'refresh' in result
    
    def test_verify_email_invalid_code(self):
        """Test email verification with invalid code."""
        user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        verification = EmailVerification.objects.create(user=user)
        verification.set_code('123456')
        verification.save()
        
        with pytest.raises(ValueError, match="Invalid code"):
            AuthService.verify_email('testuser', '000000')
    
    def test_login_success(self):
        """Test successful login."""
        user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        
        result = AuthService.login('testuser', 'testpass123')
        
        assert 'access' in result
        assert 'refresh' in result
        assert result['user']['username'] == 'testuser'
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        
        with pytest.raises(ValueError, match="Invalid username or password"):
            AuthService.login('testuser', 'wrongpass')
    
    def test_request_password_reset(self):
        """Test password reset request."""
        user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        
        with patch('core.services.auth_service.send_password_reset_email') as mock_email:
            mock_email.return_value = True
            
            result = AuthService.request_password_reset('test@example.com')
            
            assert result['email_sent'] is True
            assert PasswordResetCode.objects.filter(user=user).exists()
    
    def test_reset_password_success(self):
        """Test successful password reset."""
        user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        reset_code = PasswordResetCode.objects.create(user=user)
        reset_code.set_code('123456')
        reset_code.save()
        
        result = AuthService.reset_password('test@example.com', '123456', 'newpass123')
        
        assert result['success'] is True
        user.refresh_from_db()
        assert user.check_password('newpass123')
