"""
Caching System
Redis-based caching for performance optimization
"""

import json
import pickle
import logging
from typing import Any, Optional, Dict, Union, List
from datetime import datetime, timedelta
import hashlib
import asyncio

try:
    import redis.asyncio as redis
except ImportError:
    import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Async Redis cache manager with intelligent caching strategies"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}  # Fallback in-memory cache
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "last_reset": datetime.now()
        }
        
    async def init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory cache: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_data = f"{prefix}:" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    self.cache_stats["hits"] += 1
                    return json.loads(value)
            else:
                # Fallback to memory cache
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    if entry["expires"] > datetime.now():
                        self.cache_stats["hits"] += 1
                        return entry["value"]
                    else:
                        del self.memory_cache[key]
            
            self.cache_stats["misses"] += 1
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["errors"] += 1
            return default
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            if self.redis_client:
                await self.redis_client.setex(key, ttl, json.dumps(value, default=str))
                return True
            else:
                # Fallback to memory cache
                self.memory_cache[key] = {
                    "value": value,
                    "expires": datetime.now() + timedelta(seconds=ttl)
                }
                return True
                
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            count = 0
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    count = await self.redis_client.delete(*keys)
            else:
                # Memory cache pattern matching
                matching_keys = [k for k in self.memory_cache.keys() if pattern in k]
                for key in matching_keys:
                    del self.memory_cache[key]
                count = len(matching_keys)
            
            logger.info(f"Cleared {count} cache entries matching pattern: {pattern}")
            return count
            
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    # AI Response Caching
    async def cache_ai_response(self, prompt: str, model: str, response: Dict[str, Any], ttl: int = 7200):
        """Cache AI model response"""
        key = self._generate_key("ai_response", prompt=prompt, model=model)
        await self.set(key, {
            "response": response,
            "cached_at": datetime.now().isoformat(),
            "model": model
        }, ttl)
    
    async def get_cached_ai_response(self, prompt: str, model: str) -> Optional[Dict[str, Any]]:
        """Get cached AI response"""
        key = self._generate_key("ai_response", prompt=prompt, model=model)
        return await self.get(key)
    
    # Test Results Caching
    async def cache_test_results(self, test_id: str, results: Dict[str, Any], ttl: int = 3600):
        """Cache test execution results"""
        key = self._generate_key("test_results", test_id=test_id)
        await self.set(key, results, ttl)
    
    async def get_cached_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get cached test results"""
        key = self._generate_key("test_results", test_id=test_id)
        return await self.get(key)
    
    # Analytics Caching
    async def cache_analytics_data(self, query_type: str, params: Dict[str, Any], data: Any, ttl: int = 1800):
        """Cache analytics query results"""
        key = self._generate_key("analytics", query_type=query_type, **params)
        await self.set(key, data, ttl)
    
    async def get_cached_analytics(self, query_type: str, params: Dict[str, Any]) -> Any:
        """Get cached analytics data"""
        key = self._generate_key("analytics", query_type=query_type, **params)
        return await self.get(key)
    
    # User Session Caching
    async def cache_user_session(self, user_id: int, session_data: Dict[str, Any], ttl: int = 1800):
        """Cache user session data"""
        key = self._generate_key("user_session", user_id=user_id)
        await self.set(key, session_data, ttl)
    
    async def get_cached_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user session"""
        key = self._generate_key("user_session", user_id=user_id)
        return await self.get(key)
    
    # Configuration Caching  
    async def cache_config(self, config_type: str, config_data: Dict[str, Any], ttl: int = 3600):
        """Cache configuration data"""
        key = self._generate_key("config", type=config_type)
        await self.set(key, config_data, ttl)
    
    async def get_cached_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Get cached configuration"""
        key = self._generate_key("config", type=config_type)
        return await self.get(key)
    
    # Cache Statistics and Management
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "errors": self.cache_stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "uptime": str(datetime.now() - self.cache_stats["last_reset"]),
            "redis_connected": self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats["redis_info"] = {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            except Exception as e:
                logger.error(f"Redis info error: {e}")
        else:
            stats["memory_cache_size"] = len(self.memory_cache)
        
        return stats
    
    async def reset_stats(self):
        """Reset cache statistics"""
        self.cache_stats = {
            "hits": 0,
            "misses": 0, 
            "errors": 0,
            "last_reset": datetime.now()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Cache system health check"""
        try:
            # Test cache operations
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.now().isoformat()}
            
            await self.set(test_key, test_value, 60)
            retrieved = await self.get(test_key)
            await self.delete(test_key)
            
            if retrieved == test_value:
                status = "healthy"
            else:
                status = "degraded"
            
            return {
                "status": status,
                "redis_connected": self.redis_client is not None,
                "test_passed": retrieved == test_value,
                "stats": await self.get_stats()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "redis_connected": False,
                "test_passed": False
            }
    
    async def cleanup_expired(self):
        """Clean up expired entries from memory cache"""
        if not self.redis_client:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry["expires"] <= now
            ]
            for key in expired_keys:
                del self.memory_cache[key]
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

# Global cache manager instance
cache_manager = CacheManager()

# Decorator for caching function results
def cached(ttl: int = 3600, key_prefix: str = "func"):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = f"{key_prefix}:{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()[:16]
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result
            
        return wrapper
    return decorator