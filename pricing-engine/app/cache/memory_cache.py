"""
In-memory cache fallback implementation.
"""
import time
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict
from app.cache.interface import CacheInterface
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryCache(CacheInterface):
    """In-memory cache with LRU eviction."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        if key not in self._cache:
            self._miss_count += 1
            logger.debug(f"Cache miss: {key}")
            return None
        
        value, expiry = self._cache[key]
        
        # Check if expired
        if time.time() > expiry:
            del self._cache[key]
            self._miss_count += 1
            logger.debug(f"Cache miss (expired): {key}")
            return None
        
        # Move to end (LRU)
        self._cache.move_to_end(key)
        self._hit_count += 1
        logger.debug(f"Cache hit: {key}")
        return value
    
    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in memory cache with TTL."""
        expiry = time.time() + ttl
        
        # Remove oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._cache.popitem(last=False)
        
        self._cache[key] = (value, expiry)
        self._cache.move_to_end(key)
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    async def delete(self, key: str) -> None:
        """Delete key from memory cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache delete: {key}")
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        if key not in self._cache:
            return False
        
        _, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return False
        
        return True
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._hit_count + self._miss_count
        if total == 0:
            return 0.0
        return self._hit_count / total
    
    def reset_stats(self) -> None:
        """Reset hit/miss statistics."""
        self._hit_count = 0
        self._miss_count = 0
    
    def evict_expired(self) -> int:
        """
        Evict all expired entries.
        
        Returns:
            Number of entries evicted
        """
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if now > expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Evicted {len(expired_keys)} expired entries")
        
        return len(expired_keys)
