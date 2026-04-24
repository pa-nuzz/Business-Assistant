"""
Custom middleware for security and input validation.
"""
import json
import logging
from django.http import JsonResponse
from django.conf import settings

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
        
        # Content Security Policy (adjust as needed)
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' http://localhost:8000 https:;"
            )
        
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
