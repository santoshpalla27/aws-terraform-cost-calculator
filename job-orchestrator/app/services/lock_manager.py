"""
Distributed lock manager using Redis.
Ensures one active orchestrator per job.
"""
import redis.asyncio as redis
from typing import Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LockManager:
    """Distributed lock manager using Redis."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.worker_id = settings.worker_id
    
    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Connected to Redis")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def acquire_lock(self, job_id: str, ttl: Optional[int] = None) -> bool:
        """
        Acquire distributed lock for a job.
        
        Args:
            job_id: Job identifier
            ttl: Lock TTL in seconds (default from config)
            
        Returns:
            True if lock acquired, False otherwise
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        lock_key = f"job:lock:{job_id}"
        lock_ttl = ttl or settings.lock_ttl
        
        # Try to acquire lock (SET if not exists)
        acquired = await self.redis_client.set(
            lock_key,
            self.worker_id,
            nx=True,  # Only set if not exists
            ex=lock_ttl  # Expiration time
        )
        
        if acquired:
            logger.info(
                f"Acquired lock for job {job_id}",
                extra={'job_id': job_id, 'worker_id': self.worker_id, 'ttl': lock_ttl}
            )
        else:
            current_owner = await self.redis_client.get(lock_key)
            logger.warning(
                f"Failed to acquire lock for job {job_id} (owned by {current_owner})",
                extra={'job_id': job_id, 'current_owner': current_owner}
            )
        
        return bool(acquired)
    
    async def release_lock(self, job_id: str) -> None:
        """
        Release distributed lock for a job.
        
        Args:
            job_id: Job identifier
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        lock_key = f"job:lock:{job_id}"
        
        # Only release if we own the lock
        current_owner = await self.redis_client.get(lock_key)
        if current_owner == self.worker_id:
            await self.redis_client.delete(lock_key)
            logger.info(
                f"Released lock for job {job_id}",
                extra={'job_id': job_id, 'worker_id': self.worker_id}
            )
        else:
            logger.warning(
                f"Cannot release lock for job {job_id} (not owner)",
                extra={'job_id': job_id, 'owner': current_owner, 'worker_id': self.worker_id}
            )
    
    async def extend_lock(self, job_id: str, ttl: Optional[int] = None) -> bool:
        """
        Extend lock TTL.
        
        Args:
            job_id: Job identifier
            ttl: New TTL in seconds
            
        Returns:
            True if extended, False otherwise
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        lock_key = f"job:lock:{job_id}"
        lock_ttl = ttl or settings.lock_ttl
        
        # Only extend if we own the lock
        current_owner = await self.redis_client.get(lock_key)
        if current_owner == self.worker_id:
            await self.redis_client.expire(lock_key, lock_ttl)
            logger.debug(
                f"Extended lock for job {job_id}",
                extra={'job_id': job_id, 'ttl': lock_ttl}
            )
            return True
        
        return False
    
    async def is_locked(self, job_id: str) -> bool:
        """Check if job is locked."""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        lock_key = f"job:lock:{job_id}"
        return await self.redis_client.exists(lock_key) > 0


# Global lock manager instance
lock_manager = LockManager()
