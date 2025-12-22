"""
Rate limiting middleware.
Implements per-client rate limiting with configurable limits.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class InMemoryRateLimiter:
    """Simple in-memory rate limiter (Redis-ready architecture)."""
    
    def __init__(self, requests: int, window: int):
        """
        Initialize rate limiter.
        
        Args:
            requests: Number of requests allowed per window
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self.clients: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for client.
        
        Args:
            client_id: Client identifier (IP or user ID)
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window
        
        # Clean old requests
        self.clients[client_id] = [
            req_time for req_time in self.clients[client_id]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.clients[client_id]) >= self.requests:
            oldest_request = min(self.clients[client_id])
            retry_after = int(oldest_request + self.window - now) + 1
            return False, retry_after
        
        # Add current request
        self.clients[client_id].append(now)
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting."""
    
    def __init__(self, app, limiter: InMemoryRateLimiter):
        super().__init__(app)
        self.limiter = limiter
        self.enabled = settings.rate_limit_enabled
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip health endpoints
        if request.url.path.startswith('/health'):
            return await call_next(request)
        
        # Get client identifier (IP address or user ID from auth)
        client_id = request.client.host if request.client else "unknown"
        
        # Check if user is authenticated and use user ID instead
        if hasattr(request.state, 'user_id'):
            client_id = request.state.user_id
        
        # Check rate limit
        is_allowed, retry_after = self.limiter.is_allowed(client_id)
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for client {client_id}",
                extra={'client_id': client_id, 'retry_after': retry_after}
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "retry_after": retry_after
                    }
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        return await call_next(request)
