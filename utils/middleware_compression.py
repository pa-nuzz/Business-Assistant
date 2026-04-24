"""
Response compression middleware for API responses.
"""
import gzip
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class CompressionMiddleware:
    """
    Middleware to compress API responses using gzip.
    Only compresses responses larger than 500 bytes.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.min_size = 500  # Minimum size in bytes to compress
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only compress in production and for API responses
        if not settings.DEBUG and self.should_compress(request, response):
            response = self.compress_response(response)
        
        return response
    
    def should_compress(self, request, response):
        """Check if response should be compressed."""
        # Don't compress if already compressed
        if response.get('Content-Encoding') == 'gzip':
            return False
        
        # Don't compress if client doesn't accept gzip
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if 'gzip' not in accept_encoding.lower():
            return False
        
        # Only compress JSON responses
        content_type = response.get('Content-Type', '')
        if 'application/json' not in content_type:
            return False
        
        # Don't compress if response is too small
        if hasattr(response, 'content') and len(response.content) < self.min_size:
            return False
        
        return True
    
    def compress_response(self, response):
        """Compress response content using gzip."""
        if not hasattr(response, 'content'):
            return response
        
        try:
            compressed_content = gzip.compress(response.content, compresslevel=6)
            
            # Update response
            response.content = compressed_content
            response['Content-Encoding'] = 'gzip'
            response['Content-Length'] = str(len(compressed_content))
            
            # Remove Vary header if present to avoid issues
            response.pop('Vary', None)
            
            logger.debug(f"Compressed response: {len(response.content)} -> {len(compressed_content)} bytes")
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
        
        return response
