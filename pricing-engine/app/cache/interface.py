"""
Cache interface for AWS metadata.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheInterface(ABC):
    """Abstract cache interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        pass


def generate_cache_key(
    account_id: str,
    region: str,
    service: str,
    resource_type: str,
    resource_id: str = ""
) -> str:
    """
    Generate deterministic cache key.
    
    Format: {account_id}:{region}:{service}:{resource_type}:{resource_id}
    
    Args:
        account_id: AWS account ID
        region: AWS region
        service: AWS service (ec2, rds, etc.)
        resource_type: Resource type
        resource_id: Optional resource ID
        
    Returns:
        Cache key
    """
    parts = [account_id, region, service, resource_type]
    if resource_id:
        parts.append(resource_id)
    return ":".join(parts)
