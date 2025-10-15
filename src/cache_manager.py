"""
Cache Manager for Production
Implements Redis-based caching for repeated requests and results.
"""

import json
import hashlib
import time
from typing import Optional, Dict, Any, Union
import asyncio
from dataclasses import dataclass

try:
    from .logging_system import get_logger
except ImportError:
    from logging_system import get_logger


@dataclass
class CacheConfig:
    """Cache configuration."""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    max_cache_size_mb: int = 100
    enable_compression: bool = True
    cache_prefix: str = "agno:"


class CacheManager:
    """Redis-based cache manager for production use."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.logger = get_logger()
        self.redis_client = None
        self._connection_lock = asyncio.Lock()
        
    async def _get_redis_client(self):
        """Get Redis client with lazy initialization."""
        if self.redis_client is None:
            async with self._connection_lock:
                if self.redis_client is None:
                    try:
                        import redis.asyncio as redis
                        self.redis_client = redis.from_url(
                            self.config.redis_url,
                            decode_responses=True,
                            socket_connect_timeout=5,
                            socket_timeout=5
                        )
                        # Test connection
                        await self.redis_client.ping()
                        self.logger.info("Redis cache connected successfully")
                    except Exception as e:
                        self.logger.warning(f"Redis connection failed: {str(e)}. Caching disabled.")
                        self.redis_client = None
        return self.redis_client
    
    def _generate_cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key from query and parameters."""
        # Create a hash of the query and parameters
        cache_data = {
            "query": query,
            "params": sorted(kwargs.items()) if kwargs else {}
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        return f"{self.config.cache_prefix}{cache_hash}"
    
    async def get_cached_result(self, query: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a query.
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            Cached result or None if not found
        """
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return None
            
            cache_key = self._generate_cache_key(query, **kwargs)
            cached_data = await redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                self.logger.debug(f"Cache hit for query: {query[:50]}...")
                return result
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error getting cached result: {str(e)}")
            return None
    
    async def cache_result(
        self, 
        query: str, 
        result: Dict[str, Any], 
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Cache a result.
        
        Args:
            query: Search query
            result: Result to cache
            ttl: Time to live in seconds
            **kwargs: Additional parameters
            
        Returns:
            True if cached successfully
        """
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return False
            
            cache_key = self._generate_cache_key(query, **kwargs)
            ttl = ttl or self.config.default_ttl
            
            # Add cache metadata
            cache_data = {
                "result": result,
                "cached_at": time.time(),
                "query": query,
                "params": kwargs
            }
            
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            
            self.logger.debug(f"Cached result for query: {query[:50]}... (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.warning(f"Error caching result: {str(e)}")
            return False
    
    async def invalidate_cache(self, query_pattern: str = None) -> int:
        """
        Invalidate cache entries.
        
        Args:
            query_pattern: Pattern to match (None for all)
            
        Returns:
            Number of keys deleted
        """
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return 0
            
            if query_pattern:
                pattern = f"{self.config.cache_prefix}*{query_pattern}*"
            else:
                pattern = f"{self.config.cache_prefix}*"
            
            keys = await redis_client.keys(pattern)
            if keys:
                deleted = await redis_client.delete(*keys)
                self.logger.info(f"Invalidated {deleted} cache entries")
                return deleted
            
            return 0
            
        except Exception as e:
            self.logger.warning(f"Error invalidating cache: {str(e)}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return {"status": "disabled", "reason": "Redis not available"}
            
            # Get Redis info
            info = await redis_client.info()
            
            # Count cache keys
            cache_keys = await redis_client.keys(f"{self.config.cache_prefix}*")
            
            return {
                "status": "active",
                "total_keys": len(cache_keys),
                "memory_usage": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return 0
            
            # Redis automatically handles TTL, but we can check for any issues
            info = await redis_client.info("memory")
            expired_keys = info.get("expired_keys", 0)
            
            self.logger.debug(f"Redis cleaned up {expired_keys} expired keys")
            return expired_keys
            
        except Exception as e:
            self.logger.warning(f"Error during cache cleanup: {str(e)}")
            return 0


class MemoryCacheManager:
    """In-memory cache fallback when Redis is not available."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = {}
        self.access_times = {}
        self.logger = get_logger()
    
    def _generate_cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key."""
        cache_data = {
            "query": query,
            "params": sorted(kwargs.items()) if kwargs else {}
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _cleanup_old_entries(self):
        """Remove old entries to maintain size limit."""
        if len(self.cache) <= self.max_size:
            return
        
        # Remove oldest entries
        sorted_entries = sorted(
            self.access_times.items(),
            key=lambda x: x[1]
        )
        
        entries_to_remove = len(self.cache) - self.max_size
        for key, _ in sorted_entries[:entries_to_remove]:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def get_cached_result(self, query: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get cached result."""
        cache_key = self._generate_cache_key(query, **kwargs)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check if expired
            if time.time() - entry["cached_at"] > entry["ttl"]:
                del self.cache[cache_key]
                self.access_times.pop(cache_key, None)
                return None
            
            # Update access time
            self.access_times[cache_key] = time.time()
            return entry["result"]
        
        return None
    
    def cache_result(
        self, 
        query: str, 
        result: Dict[str, Any], 
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """Cache a result."""
        try:
            cache_key = self._generate_cache_key(query, **kwargs)
            ttl = ttl or self.default_ttl
            
            self.cache[cache_key] = {
                "result": result,
                "cached_at": time.time(),
                "ttl": ttl
            }
            self.access_times[cache_key] = time.time()
            
            self._cleanup_old_entries()
            return True
            
        except Exception as e:
            self.logger.warning(f"Error caching result in memory: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "status": "active",
            "type": "memory",
            "total_keys": len(self.cache),
            "max_size": self.max_size,
            "usage_percent": (len(self.cache) / self.max_size) * 100
        }
