"""Rate limiting middleware."""

import time
from typing import Dict, Tuple
from collections import defaultdict
import threading

from fastapi import Request, HTTPException, status

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=settings.rate_limit_requests,
                refill_rate=settings.rate_limit_requests / settings.rate_limit_period
            )
        )
        self.cleanup_interval = 3600  # Clean up old buckets every hour
        self.last_cleanup = time.time()
        logger.info(
            "Initialized rate limiter",
            requests=settings.rate_limit_requests,
            period=settings.rate_limit_period
        )
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed.
        
        Args:
            key: Identifier for rate limiting (e.g., IP address)
            
        Returns:
            True if allowed, False otherwise
        """
        # Periodic cleanup
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
        
        bucket = self.buckets[key]
        return bucket.consume()
    
    def _cleanup(self):
        """Clean up old buckets to prevent memory leak."""
        # Remove buckets that are full (haven't been used recently)
        keys_to_remove = [
            key for key, bucket in self.buckets.items()
            if bucket.tokens >= bucket.capacity
        ]
        
        for key in keys_to_remove:
            del self.buckets[key]
        
        self.last_cleanup = time.time()
        logger.info("Cleaned up rate limiter buckets", removed=len(keys_to_remove))


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limit_middleware(request: Request):
    """Rate limiting dependency for routes.
    
    Args:
        request: FastAPI request
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    if not settings.rate_limit_enabled:
        return
    
    # Use client IP as key
    client_ip = request.client.host if request.client else "unknown"
    
    limiter = get_rate_limiter()
    if not limiter.is_allowed(client_ip):
        logger.warning("Rate limit exceeded", client_ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
