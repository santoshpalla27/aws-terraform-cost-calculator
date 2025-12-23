"""
Correlation ID middleware.
Adds a unique correlation ID to each request for tracing.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logger import set_correlation_id


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to requests."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        
        # Set in context for logging
        set_correlation_id(correlation_id)
        
        # CRITICAL: Attach to request.state for downstream access
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response
