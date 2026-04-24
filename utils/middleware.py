"""
Custom middleware for security and input validation.
"""
import json
import logging
import uuid
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class InputValidationMiddleware:
    """
    Middleware to validate and sanitize input data.
    Prevents common injection attacks and validates content types.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip validation for GET requests and file uploads
        if request.method == 'GET' or 'multipart/form-data' in request.content_type:
            return self.get_response(request)

        # Validate JSON content type for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.content_type or ''
            
            # Check for suspicious content types
            if 'application/json' in content_type:
                try:
                    if request.body:
                        body = request.body.decode('utf-8')
                        # Prevent JSON injection by validating structure
                        json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"Invalid JSON in request: {e}")
                    return JsonResponse(
                        {"error": "Invalid JSON format"},
                        status=400
                    )

        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add additional security headers to all responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (strict production, relaxed in development)
        if settings.DEBUG:
            # Development: allow localhost and inline scripts for debugging
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* https://localhost:*; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https: http://localhost:* https://localhost:*; "
                "connect-src 'self' http://localhost:* https://localhost:* ws://localhost:* wss://localhost:*; "
                "frame-ancestors 'self'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            # Production: strict CSP based on settings
            csp = (
                f"default-src {getattr(settings, 'CSP_DEFAULT_SRC', ('\'self\'',))}; "
                f"script-src {getattr(settings, 'CSP_SCRIPT_SRC', ('\'self\'', 'https://cdn.jsdelivr.net'))}; "
                f"style-src {getattr(settings, 'CSP_STYLE_SRC', ('\'self\'', 'https://fonts.googleapis.com', '\'unsafe-inline\''))}; "
                f"font-src {getattr(settings, 'CSP_FONT_SRC', ('\'self\'', 'https://fonts.gstatic.com'))}; "
                f"img-src {getattr(settings, 'CSP_IMG_SRC', ('\'self\'', 'data:', 'https://*.r2.cloudflarestorage.com', 'https://*.amazonaws.com'))}; "
                f"connect-src {getattr(settings, 'CSP_CONNECT_SRC', ('\'self\'', 'https://*.render.com'))}; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        
        response['Content-Security-Policy'] = csp
        
        return response


class RateLimitLoggingMiddleware:
    """
    Middleware to log potential rate limit violations for analysis.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log 429 responses (rate limited)
        if response.status_code == 429:
            logger.warning(
                f"Rate limit exceeded - User: {request.user.id if request.user.is_authenticated else 'anonymous'}, "
                f"Path: {request.path}, "
                f"Method: {request.method}"
            )
        
        return response


class IPRateLimitMiddleware:
    """
    IP-based rate limiting middleware to prevent abuse and brute force attacks.
    Limits requests per IP address regardless of authentication status.
    """
    
    # Rate limits per endpoint (requests per minute)
    RATE_LIMITS = {
        'auth': 10,  # Auth endpoints
        'default': 60,  # General endpoints
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def get_client_ip(self, request):
        """Extract client IP from request, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def get_rate_limit_key(self, request):
        """Generate cache key for rate limiting."""
        ip = self.get_client_ip(request)
        path = request.path
        
        # Determine rate limit category
        if '/auth/' in path:
            category = 'auth'
        else:
            category = 'default'
        
        return f"rate_limit_{category}_{ip}"
    
    def __call__(self, request):
        # Skip rate limiting for health checks and static files
        if request.path in ['/health/', '/health', '/static/', '/media/']:
            return self.get_response(request)
        
        ip = self.get_client_ip(request)
        key = self.get_rate_limit_key(request)
        
        # Get current count
        current_count = cache.get(key, 0)
        
        # Determine limit
        if '/auth/' in request.path:
            limit = self.RATE_LIMITS['auth']
        else:
            limit = self.RATE_LIMITS['default']
        
        # Check if limit exceeded
        if current_count >= limit:
            logger.warning(
                f"IP rate limit exceeded - IP: {ip}, "
                f"Path: {request.path}, "
                f"Count: {current_count}, "
                f"Limit: {limit}"
            )
            return JsonResponse(
                {"error": "Too many requests. Please try again later."},
                status=429
            )
        
        # Increment counter
        cache.set(key, current_count + 1, timeout=60)  # 1 minute window
        
        response = self.get_response(request)
        
        # Add rate limit headers
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(limit - (current_count + 1))
        response['X-RateLimit-Reset'] = str(60)
        
        return response


class RequestIDMiddleware:
    """
    Middleware to add unique request ID to each request for tracing and debugging.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Generate or retrieve request ID
        request_id = request.META.get('HTTP_X_REQUEST_ID') or str(uuid.uuid4())
        request.id = request_id
        
        response = self.get_response(request)
        
        # Add request ID to response headers
        response['X-Request-ID'] = request_id
        
        return response


class DeviceFingerprintMiddleware:
    """
    Middleware to generate and track device fingerprints for session security.
    Helps detect session hijacking and suspicious login patterns.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def get_fingerprint(self, request):
        """Generate a device fingerprint from request headers."""
        # Collect fingerprint components
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        # Create a simple hash of these components
        import hashlib
        fingerprint_data = f"{user_agent}|{accept_language}|{accept_encoding}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    def __call__(self, request):
        # Generate device fingerprint
        fingerprint = self.get_fingerprint(request)
        request.device_fingerprint = fingerprint
        
        response = self.get_response(request)
        
        # Add fingerprint to response headers (for debugging, not for security)
        if settings.DEBUG:
            response['X-Device-Fingerprint'] = fingerprint
        
        return response


class SlowQueryLoggingMiddleware:
    """
    Middleware to log slow database queries (>100ms) for performance monitoring.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_query_threshold = 0.1  # 100ms in seconds
    
    def __call__(self, request):
        from django.db import connection
        from django.conf import settings
        
        # Enable query logging for this request
        connection.queries_log.clear()
        
        response = self.get_response(request)
        
        # Check for slow queries
        if settings.DEBUG and connection.queries:
            for query in connection.queries:
                query_time = float(query.get('time', 0))
                if query_time > self.slow_query_threshold:
                    logger.warning(
                        f"Slow query detected - Time: {query_time:.3f}s, "
                        f"SQL: {query['sql'][:200]}..., "
                        f"Path: {request.path}"
                    )
        
        return response
