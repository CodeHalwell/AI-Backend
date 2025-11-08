"""
Redis Caching Utility

Provides caching functionality using Redis.

Why Redis?
- In-memory: Very fast (microsecond latency)
- Persistence options available
- TTL support for auto-expiration
- Atomic operations
- Pub/Sub for real-time features

Use Cases:
- Cache API responses
- Store session data
- Rate limiting
- Real-time features
- Queue management

Performance Impact:
- Database queries: ~10-100ms
- Redis lookups: ~1ms
- 10-100x speedup for cached data
"""

from typing import Optional, Any
import json
from redis import asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import logger


class RedisCache:
    """
    Redis cache manager.
    
    Provides async Redis operations with automatic
    JSON serialization/deserialization.
    """
    
    def __init__(self):
        """Initialize Redis connection (lazy)."""
        self._redis: Optional[Redis] = None
    
    async def get_redis(self) -> Redis:
        """
        Get Redis connection.
        
        Creates connection on first use (lazy initialization).
        
        Returns:
            Redis connection instance
        """
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                )
                logger.info("Redis connection established")
            except Exception as e:
                logger.error("Failed to connect to Redis", error=str(e))
                raise
        
        return self._redis
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            redis = await self.get_redis()
            value = await redis.get(key)
            
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON-serialized)
            ttl: Time to live in seconds (default from settings)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis = await self.get_redis()
            
            # Serialize value
            if not isinstance(value, str):
                value = json.dumps(value)
            
            # Set with TTL
            ttl = ttl or settings.REDIS_CACHE_TTL
            await redis.setex(key, ttl, value)
            
            return True
            
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            redis = await self.get_redis()
            await redis.delete(key)
            return True
            
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        try:
            redis = await self.get_redis()
            return await redis.exists(key) > 0
            
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")


# Singleton instance
cache = RedisCache()


# Helper function for cache key generation
def make_cache_key(*args: str) -> str:
    """
    Generate cache key from components.
    
    Args:
        *args: Key components
        
    Returns:
        Cache key string
        
    Example:
        key = make_cache_key("user", user_id, "profile")
        # Returns: "user:123e4567:profile"
    """
    return ":".join(str(arg) for arg in args)


__all__ = ["cache", "make_cache_key", "RedisCache"]
