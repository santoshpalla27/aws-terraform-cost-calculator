"""
Redis-backed cache implementation.
"""
import json
import redis.asyncio as redis
from typing import Any, Optional
from app.cache.interface import CacheInterface
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RedisCache(CacheInterface):
    """Redis-backed cache with TTL support."""
    
    def __init__(self, redis_url: str):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self._hit_count = 0
        self._miss_count = 0
    
    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Redis cache disconnected")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.client:
            logger.warning("Redis client not connected")
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                self._hit_count += 1
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                self._miss_count += 1
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self._miss_count += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in Redis cache with TTL."""
        if not self.client:
            logger.warning("Redis client not connected")
            return
        
        try:
            serialized = json.dumps(value)
            await self.client.setex(key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete key from Redis cache."""
        if not self.client:
            return
        
        try:
            await self.client.delete(key)
            logger.debug(f"Cache delete: {key}")
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        if not self.client:
            return
        
        try:
            await self.client.flushdb()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        if not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
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
