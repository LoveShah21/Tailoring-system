"""
Audit App - Middleware

Controlled audit logging middleware.
Only logs business-critical actions, not blanket logging.
"""

import json
from django.utils.deprecation import MiddlewareMixin


class AuditMiddleware(MiddlewareMixin):
    """
    Business-critical action logging middleware.
    
    Logs:
    - Authenticated users only
    - POST, PUT, PATCH, DELETE methods only
    - Excludes: static files, admin media, health checks
    
    Captures:
    - IP address
    - User agent
    - Request path
    - User ID
    """
    
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/health/',
        '/robots.txt',
    ]
    
    AUDITED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def should_audit(self, request):
        """Determine if request should be audited."""
        # Skip unauthenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Skip safe methods (GET, HEAD, OPTIONS)
        if request.method not in self.AUDITED_METHODS:
            return False
        
        # Skip excluded paths
        for path in self.EXCLUDED_PATHS:
            if request.path.startswith(path):
                return False
        
        return True
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip[:45]  # Truncate for IPv4/IPv6 compatibility
    
    def process_request(self, request):
        """Store request info for later logging."""
        if self.should_audit(request):
            request._audit_data = {
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'path': request.path[:255],
                'method': request.method,
            }
    
    def process_response(self, request, response):
        """
        Note: Actual audit logging is done in services layer via AuditService,
        not in middleware. This middleware only prepares request metadata.
        """
        return response
