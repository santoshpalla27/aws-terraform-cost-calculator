"""Caching layer for AWS metadata."""

import time
import logging
from typing import Any, Optional, Dict
from cachetools import TTLCache
from threading import Lock

logger = logging.getLogger(__name__)


class MetadataCache:
    """Thread-safe cache for AWS metadata with TTL support."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize cache.
        
        Args:
            max_size: Maximum number of cache entries
        """
        self.caches: Dict[str, TTLCache] = {}
        self.locks: Dict[str, Lock] = {}
        self.max_size = max_size
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0
        }
        self.stats_lock = Lock()
    
    def _get_cache(self, cache_type: str, ttl: int) -> TTLCache:
        """Get or create cache for a specific type.
        
        Args:
            cache_type: Type of cache (ami, instance_type, etc.)
            ttl: Time to live in seconds
            
        Returns:
            TTL cache instance
        """
        if cache_type not in self.caches:
            self.caches[cache_type] = TTLCache(maxsize=self.max_size, ttl=ttl)
            self.locks[cache_type] = Lock()
        
        return self.caches[cache_type]
    
    def get(self, cache_type: str, key: str, ttl: int) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            ttl: Time to live
            
        Returns:
            Cached value or None
        """
        cache = self._get_cache(cache_type, ttl)
        lock = self.locks[cache_type]
        
        with lock:
            value = cache.get(key)
            
            with self.stats_lock:
                if value is not None:
                    self.stats["hits"] += 1
                    logger.debug(f"Cache hit: {cache_type}:{key}")
                else:
                    self.stats["misses"] += 1
                    logger.debug(f"Cache miss: {cache_type}:{key}")
            
            return value
    
    def set(self, cache_type: str, key: str, value: Any, ttl: int) -> None:
        """Set value in cache.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            value: Value to cache
            ttl: Time to live
        """
        cache = self._get_cache(cache_type, ttl)
        lock = self.locks[cache_type]
        
        with lock:
            cache[key] = value
            
            with self.stats_lock:
                self.stats["sets"] += 1
            
            logger.debug(f"Cache set: {cache_type}:{key}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dictionary of cache stats
        """
        with self.stats_lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self.stats,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2)
            }
    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """Clear cache.
        
        Args:
            cache_type: Type of cache to clear, or None for all
        """
        if cache_type:
            if cache_type in self.caches:
                with self.locks[cache_type]:
                    self.caches[cache_type].clear()
                logger.info(f"Cleared cache: {cache_type}")
        else:
            for ct in list(self.caches.keys()):
                with self.locks[ct]:
                    self.caches[ct].clear()
            logger.info("Cleared all caches")


# Global cache instance
_cache: Optional[MetadataCache] = None


def get_cache() -> MetadataCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        from .config import settings
        _cache = MetadataCache(max_size=settings.cache_max_size)
    return _cache
