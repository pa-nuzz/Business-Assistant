"""
Enhanced Security Middleware for AEIOU AI.

Provides comprehensive security features including:
- Rate limiting
- Input validation
- Security headers
- Request logging
- IP blocking
- Session security
"""
import time
import json
import logging
from typing import Dict, Any, Optional
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .security import (
    detect_sql_injection, 
    log_security_event, 
    get_security_headers,
    RateLimiter
)

logger = logging.getLogger(__name__)

class SecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiter = RateLimiter()
        
        # Rate limiting configuration
        self.rate_limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests/hour
            'auth': {'requests': 20, 'window': 3600},       # 20 auth requests/hour
            'upload': {'requests': 10, 'window': 3600},      # 10 uploads/hour
            'api': {'requests': 1000, 'window': 3600},      # 1000 API requests/hour
        }
        
        # Blocked IPs (in production, use Redis or database)
        self.blocked_ips = set()
        
        super().__init__(get_response)
    
    def __call__(self, request):
        # Process request
        response = self.process_request(request)
        if response:
            return response
        
        # Get response
        response = self.get_response(request)
        
        # Process response
        response = self.process_response(request, response)
        
        return response
    
    def process_request(self, request):
        """Process incoming request for security checks."""
        
        # Get client information
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            log_security_event(
                'BLOCKED_IP_ACCESS',
                {'ip_address': client_ip, 'user_agent': user_agent}
            )
            return JsonResponse(
                {'error': 'Access denied'}, 
                status=403
            )
        
        # Validate request size
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB limit
            log_security_event(
                'LARGE_REQUEST',
                {'ip_address': client_ip, 'size': content_length}
            )
            return JsonResponse(
                {'error': 'Request too large'}, 
                status=413
            )
        
        # Rate limiting
        if not self.check_rate_limit(request, client_ip):
            log_security_event(
                'RATE_LIMIT_EXCEEDED',
                {'ip_address': client_ip, 'path': request.path}
            )
            return JsonResponse(
                {'error': 'Rate limit exceeded'}, 
                status=429
            )
        
        # SQL injection detection
        if self.detect_suspicious_input(request):
            log_security_event(
                'SUSPICIOUS_INPUT_DETECTED',
                {
                    'ip_address': client_ip,
                    'path': request.path,
                    'method': request.method,
                    'user_agent': user_agent
                }
            )
            # Block temporarily
            self.block_ip_temporarily(client_ip, duration=300)  # 5 minutes
            return JsonResponse(
                {'error': 'Invalid request'}, 
                status=400
            )
        
        # Validate headers
        if not self.validate_headers(request):
            log_security_event(
                'INVALID_HEADERS',
                {'ip_address': client_ip, 'headers': dict(request.headers)}
            )
            return JsonResponse(
                {'error': 'Invalid request headers'}, 
                status=400
            )
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response for security headers."""
        
        # Add security headers
        security_headers = get_security_headers()
        
        for header, value in security_headers.items():
            response[header] = value
        
        # Add custom security headers
        response['X-API-Version'] = '1.0.0'
        response['X-Response-Time'] = str(int(time.time() * 1000))
        
        # Log security events for certain status codes
        if hasattr(response, 'status_code') and response.status_code >= 400:
            self.log_security_response(request, response)
        
        return response
    
    def get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        
        # Check for proxy headers
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        return ip or 'unknown'
    
    def check_rate_limit(self, request, client_ip: str) -> bool:
        """Check if request exceeds rate limits."""
        
        # Get rate limit category
        category = self.get_rate_limit_category(request)
        rate_config = self.rate_limits.get(category, self.rate_limits['default'])
        
        # Create rate limit key
        if hasattr(request, 'user') and request.user.is_authenticated:
            key = f"user:{request.user.id}:{category}"
        else:
            key = f"ip:{client_ip}:{category}"
        
        # Check rate limit
        return self.rate_limiter.is_allowed(
            key, 
            rate_config['requests'], 
            rate_config['window']
        )
    
    def get_rate_limit_category(self, request) -> str:
        """Determine rate limit category based on request."""
        
        path = request.path.lower()
        
        if '/auth/' in path:
            return 'auth'
        elif '/upload' in path or '/documents/' in path:
            return 'upload'
        elif path.startswith('/api/'):
            return 'api'
        else:
            return 'default'
    
    def detect_suspicious_input(self, request) -> bool:
        """Detect suspicious input in request."""
        
        # Check query parameters
        for key, value in request.GET.items():
            if detect_sql_injection(str(value)):
                return True
        
        # Check POST data
        if hasattr(request, 'POST'):
            for key, value in request.POST.items():
                if detect_sql_injection(str(value)):
                    return True
        
        # Check JSON body
        if hasattr(request, 'body') and request.body:
            try:
                body_str = request.body.decode('utf-8')
                if detect_sql_injection(body_str):
                    return True
            except UnicodeDecodeError:
                pass
        
        # Check path for traversal attempts
        path = request.path
        if '../' in path or '..\\' in path:
            return True
        
        return False
    
    def validate_headers(self, request) -> bool:
        """Validate request headers for security issues."""
        
        # Check for suspicious headers
        suspicious_headers = [
            'X-Forwarded-Host',
            'X-Real-IP',
            'X-Originating-IP'
        ]
        
        for header in suspicious_headers:
            if header in request.META:
                value = request.META[header]
                # Check for header injection
                if '\n' in value or '\r' in value:
                    return False
        
        # Validate Content-Type
        content_type = request.META.get('CONTENT_TYPE', '')
        if content_type and not self.is_valid_content_type(content_type):
            return False
        
        return True
    
    def is_valid_content_type(self, content_type: str) -> bool:
        """Validate content type header."""
        
        allowed_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain'
        ]
        
        # Check if content type starts with allowed type
        for allowed in allowed_types:
            if content_type.startswith(allowed):
                return True
        
        return False
    
    def block_ip_temporarily(self, ip: str, duration: int = 300):
        """Block IP address temporarily."""
        
        self.blocked_ips.add(ip)
        
        # Schedule unblock (in production, use Celery or Redis with TTL)
        def unblock_ip():
            self.blocked_ips.discard(ip)
        
        # In production, use proper async scheduling
        import threading
        timer = threading.Timer(duration, unblock_ip)
        timer.start()
    
    def log_security_response(self, request, response):
        """Log security-related responses."""
        client_ip = self.get_client_ip(request)
        log_security_event(
            f'HTTP_{response.status_code}',
            {
                'ip_address': client_ip,
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )


class InputValidationMiddleware(MiddlewareMixin):
    """
    Middleware to validate and sanitize input data.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        """Validate and sanitize input data."""
        # Validate and sanitize query parameters
        self.validate_query_params(request)
        # Validate and sanitize POST data
        if hasattr(request, 'POST'):
            self.validate_post_data(request)
        # Validate JSON body
        if hasattr(request, 'body') and request.body:
            self.validate_json_body(request)
        return self.get_response(request)

    def validate_query_params(self, request):
        """Validate query parameters."""
        for key, value in request.GET.items():
            if detect_sql_injection(str(value)):
                raise ValueError(f"Invalid parameter: {key}")
            request.GET._mutable = True
            request.GET[key] = self.sanitize_input_value(value)
            request.GET._mutable = False

    def validate_post_data(self, request):
        """Validate POST data."""
        for key, value in request.POST.items():
            if detect_sql_injection(str(value)):
                raise ValueError(f"Invalid parameter: {key}")
            request.POST._mutable = True
            request.POST[key] = self.sanitize_input_value(value)
            request.POST._mutable = False

    def validate_json_body(self, request):
        """Validate JSON body."""
        if request.content_type and 'json' in request.content_type:
            try:
                data = json.loads(request.body.decode('utf-8'))
                self.validate_json_data(data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    def validate_json_data(self, data: Any, path: str = ""):
        """Recursively validate JSON data."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, str) and detect_sql_injection(value):
                    raise ValueError(f"Invalid field: {current_path}")
                if isinstance(value, (dict, list)):
                    self.validate_json_data(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                if isinstance(item, str) and detect_sql_injection(item):
                    raise ValueError(f"Invalid item: {current_path}")
                if isinstance(item, (dict, list)):
                    self.validate_json_data(item, current_path)

    def sanitize_input_value(self, value: Any) -> Any:
        """Sanitize input value."""
        if isinstance(value, str):
            value = value.replace('\x00', '')
            value = value.strip()
            if len(value) > 10000:
                value = value[:10000]
        return value


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware for session security.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        """Enforce session security."""
        if hasattr(request, 'session') and request.session:
            self.check_session_age(request)
            self.check_session_ip(request)
            self.check_session_user_agent(request)
        return self.get_response(request)

    def check_session_age(self, request):
        """Check if session has expired."""
        session_created = request.session.get('session_created')
        if session_created:
            session_age = time.time() - session_created
            max_age = getattr(settings, 'SESSION_COOKIE_AGE', 86400)
            if session_age > max_age:
                request.session.flush()
                log_security_event(
                    'SESSION_EXPIRED',
                    {'ip_address': self.get_client_ip(request)}
                )
        else:
            request.session['session_created'] = time.time()

    def check_session_ip(self, request):
        """Check if session IP has changed."""
        current_ip = self.get_client_ip(request)
        session_ip = request.session.get('session_ip')
        if session_ip and session_ip != current_ip:
            request.session.flush()
            log_security_event(
                'SESSION_IP_CHANGED',
                {
                    'ip_address': current_ip,
                    'original_ip': session_ip
                }
            )
        else:
            request.session['session_ip'] = current_ip

    def check_session_user_agent(self, request):
        """Check if session user agent has changed."""
        current_ua = request.META.get('HTTP_USER_AGENT', '')
        session_ua = request.session.get('session_user_agent')
        if session_ua and session_ua != current_ua:
            request.session.flush()
            log_security_event(
                'SESSION_UA_CHANGED',
                {
                    'ip_address': self.get_client_ip(request),
                    'original_ua': session_ua,
                    'current_ua': current_ua
                }
            )
        else:
            request.session['session_user_agent'] = current_ua

    def get_client_ip(self, request) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
