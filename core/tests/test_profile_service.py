"""
Unit tests for ProfileService.
"""
import pytest
from django.contrib.auth.models import User
from core.services.profile_service import ProfileService
from core.models import BusinessProfile


@pytest.mark.django_db
class TestProfileService:
    """Test cases for ProfileService."""
    
    def test_get_user_info(self):
        """Test getting user info."""
        user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')
        service = ProfileService(user)
        
        result = service.get_user_info()
        
        assert result['id'] == user.id
        assert result['username'] == 'testuser'
        assert result['email'] == 'test@example.com'
    
    def test_update_username_success(self):
        """Test successful username update."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = ProfileService(user)
        
        result = service.update_username('newusername')
        
        assert result['username'] == 'newusername'
        user.refresh_from_db()
        assert user.username == 'newusername'
    
    def test_update_username_too_short(self):
        """Test username update with too short username."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = ProfileService(user)
        
        with pytest.raises(ValueError, match="at least 3 characters"):
            service.update_username('ab')
    
    def test_update_username_duplicate(self):
        """Test username update with duplicate username."""
        User.objects.create_user(username='existing', password='pass123')
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = ProfileService(user)
        
        with pytest.raises(ValueError, match="already taken"):
            service.update_username('existing')
    
    def test_update_password_success(self):
        """Test successful password update."""
        user = User.objects.create_user(username='testuser', password='oldpass123')
        service = ProfileService(user)
        
        result = service.update_password('oldpass123', 'newpass123')
        
        assert result['message'] == 'Password updated successfully'
        user.refresh_from_db()
        assert user.check_password('newpass123')
    
    def test_update_password_wrong_current(self):
        """Test password update with wrong current password."""
        user = User.objects.create_user(username='testuser', password='oldpass123')
        service = ProfileService(user)
        
        with pytest.raises(ValueError, match="incorrect"):
            service.update_password('wrongpass', 'newpass123')
    
    def test_update_password_too_short(self):
        """Test password update with too short new password."""
        user = User.objects.create_user(username='testuser', password='oldpass123')
        service = ProfileService(user)
        
        with pytest.raises(ValueError, match="at least 8 characters"):
            service.update_password('oldpass123', 'short')
    
    def test_get_business_profile_none(self):
        """Test getting business profile when none exists."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = ProfileService(user)
        
        result = service.get_business_profile()
        
        assert result['id'] is None
        assert result['company_name'] == ''
    
    def test_get_business_profile_exists(self):
        """Test getting existing business profile."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        profile = BusinessProfile.objects.create(
            user=user,
            company_name='Test Company',
            industry='Tech'
        )
        service = ProfileService(user)
        
        result = service.get_business_profile()
        
        assert result['id'] == profile.id
        assert result['company_name'] == 'Test Company'
        assert result['industry'] == 'Tech'
    
    def test_update_business_profile_create(self):
        """Test creating business profile."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        service = ProfileService(user)
        
        data = {
            'company_name': 'New Company',
            'industry': 'Tech',
            'company_size': '1-10'
        }
        
        result = service.update_business_profile(data)
        
        assert result['company_name'] == 'New Company'
        assert BusinessProfile.objects.filter(user=user).exists()
    
    def test_update_business_profile_update(self):
        """Test updating existing business profile."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        BusinessProfile.objects.create(user=user, company_name='Old Name')
        service = ProfileService(user)
        
        data = {'company_name': 'New Name'}
        
        result = service.update_business_profile(data)
        
        assert result['company_name'] == 'New Name'
        profile = BusinessProfile.objects.get(user=user)
        assert profile.company_name == 'New Name'
