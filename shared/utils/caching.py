#!/usr/bin/env python3
"""
AI Content Factory - Advanced Caching Utilities
==============================================

This module provides comprehensive caching capabilities with Redis backend,
multi-level caching, cache warming, and intelligent invalidation strategies.

Path: ai-content-factory/shared/utils/caching.py
"""

import asyncio
import json
import pickle
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from functools import wraps
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as aioredis
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels for multi-tier caching strategy"""
    MEMORY = "memory"
    REDIS = "redis" 
    DATABASE = "database"


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"                    # Time-based expiration
    LRU = "lru"                    # Least Recently Used
    LFU = "lfu"                    # Least Frequently Used
    WRITE_THROUGH = "write_through" # Update cache on write
    WRITE_BEHIND = "write_behind"   # Async write to cache


@dataclass
class CacheConfig:
    """Cache configuration settings"""
    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 3600  # 1 hour
    max_memory_items: int = 1000
    key_prefix: str = "ai_content_factory"
    compression_threshold: int = 1024  # Compress data larger than 1KB
    serialization_method: str = "json"  # json, pickle, msgpack
    enable_metrics: bool = True
    max_key_length: int = 250


class CacheMetrics:
    """Cache performance metrics collector"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.total_time = 0.0
        self.start_time = time.time()
    
    def hit(self, execution_time: float = 0):
        self.hits += 1
        self.total_time += execution_time
    
    def miss(self, execution_time: float = 0):
        self.misses += 1
        self.total_time += execution_time
    
    def set(self, execution_time: float = 0):
        self.sets += 1
        self.total_time += execution_time
    
    def delete(self, execution_time: float = 0):
        self.deletes += 1
        self.total_time += execution_time
    
    def error(self):
        self.errors += 1
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0
    
    @property
    def average_time(self) -> float:
        total_ops = self.hits + self.misses + self.sets + self.deletes
        return (self.total_time / total_ops) if total_ops > 0 else 0
    
    def get_stats(self) -> Dict[str, Any]:
        uptime = time.time() - self.start_time
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": self.hit_rate,
            "average_time_ms": self.average_time * 1000,
            "uptime_seconds": uptime,
            "operations_per_second": (self.hits + self.misses + self.sets + self.deletes) / uptime if uptime > 0 else 0
        }


class AdvancedCache:
    """
    Advanced multi-level caching system with Redis backend
    
    Features:
    - Multi-level caching (memory + Redis)
    - Intelligent serialization
    - Cache warming and preloading
    - Metrics and monitoring
    - Batch operations
    - Namespace support
    - TTL management
    """
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis_client: Optional[aioredis.Redis] = None
        self.redis_sync_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Tuple[Any, float, int]] = {}  # value, expiry, access_count
        self.metrics = CacheMetrics() if self.config.enable_metrics else None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize Redis connections"""
        try:
            self.redis_client = aioredis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=False,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            self.redis_sync_client = redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=False,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Cache system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            raise
    
    def _generate_key(self, key: str, namespace: str = None) -> str:
        """Generate cache key with prefix and namespace"""
        parts = [self.config.key_prefix]
        if namespace:
            parts.append(namespace)
        parts.append(key)
        
        cache_key = ":".join(parts)
        
        # Handle long keys
        if len(cache_key) > self.config.max_key_length:
            cache_key = f"{cache_key[:200]}:{hashlib.md5(cache_key.encode()).hexdigest()}"
        
        return cache_key
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data based on configuration"""
        try:
            if self.config.serialization_method == "json":
                serialized = json.dumps(data, default=str).encode('utf-8')
            elif self.config.serialization_method == "pickle":
                serialized = pickle.dumps(data)
            else:
                # Fallback to pickle
                serialized = pickle.dumps(data)
            
            # Compress if data is large
            if len(serialized) > self.config.compression_threshold:
                import gzip
                serialized = gzip.compress(serialized)
                return b"compressed:" + serialized
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data"""
        try:
            # Check if compressed
            if data.startswith(b"compressed:"):
                import gzip
                data = gzip.decompress(data[11:])
            
            if self.config.serialization_method == "json":
                return json.loads(data.decode('utf-8'))
            elif self.config.serialization_method == "pickle":
                return pickle.loads(data)
            else:
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise
    
    async def get(self, key: str, namespace: str = None, default: Any = None) -> Any:
        """Get value from cache with multi-level fallback"""
        start_time = time.time()
        cache_key = self._generate_key(key, namespace)
        
        try:
            # Level 1: Memory cache
            if cache_key in self.memory_cache:
                value, expiry, access_count = self.memory_cache[cache_key]
                if expiry == 0 or time.time() < expiry:
                    # Update access count for LFU
                    self.memory_cache[cache_key] = (value, expiry, access_count + 1)
                    if self.metrics:
                        self.metrics.hit(time.time() - start_time)
                    return value
                else:
                    # Expired, remove from memory
                    del self.memory_cache[cache_key]
            
            # Level 2: Redis cache
            if self.redis_client:
                data = await self.redis_client.get(cache_key)
                if data is not None:
                    value = self._deserialize_data(data)
                    # Store in memory cache for faster access
                    await self._store_in_memory(cache_key, value, self.config.default_ttl)
                    if self.metrics:
                        self.metrics.hit(time.time() - start_time)
                    return value
            
            # Cache miss
            if self.metrics:
                self.metrics.miss(time.time() - start_time)
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            if self.metrics:
                self.metrics.error()
            return default
    
    async def set(self, key: str, value: Any, ttl: int = None, namespace: str = None) -> bool:
        """Set value in cache with multi-level storage"""
        start_time = time.time()
        cache_key = self._generate_key(key, namespace)
        ttl = ttl or self.config.default_ttl
        
        try:
            # Store in Redis
            if self.redis_client:
                serialized_data = self._serialize_data(value)
                await self.redis_client.setex(cache_key, ttl, serialized_data)
            
            # Store in memory cache
            await self._store_in_memory(cache_key, value, ttl)
            
            if self.metrics:
                self.metrics.set(time.time() - start_time)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            if self.metrics:
                self.metrics.error()
            return False
    
    async def _store_in_memory(self, cache_key: str, value: Any, ttl: int):
        """Store value in memory cache with size management"""
        async with self._lock:
            expiry = time.time() + ttl if ttl > 0 else 0
            self.memory_cache[cache_key] = (value, expiry, 1)
            
            # Memory cache size management
            if len(self.memory_cache) > self.config.max_memory_items:
                # Remove expired items first
                current_time = time.time()
                expired_keys = [
                    k for k, (_, exp, _) in self.memory_cache.items() 
                    if exp > 0 and current_time > exp
                ]
                for k in expired_keys:
                    del self.memory_cache[k]
                
                # If still over limit, remove LRU items
                if len(self.memory_cache) > self.config.max_memory_items:
                    # Sort by access count (LFU) and remove least frequently used
                    sorted_items = sorted(
                        self.memory_cache.items(), 
                        key=lambda x: x[1][2]  # access_count
                    )
                    items_to_remove = len(self.memory_cache) - self.config.max_memory_items + 100
                    for k, _ in sorted_items[:items_to_remove]:
                        del self.memory_cache[k]
    
    async def delete(self, key: str, namespace: str = None) -> bool:
        """Delete key from all cache levels"""
        start_time = time.time()
        cache_key = self._generate_key(key, namespace)
        
        try:
            # Delete from Redis
            deleted_count = 0
            if self.redis_client:
                deleted_count = await self.redis_client.delete(cache_key)
            
            # Delete from memory
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
                deleted_count += 1
            
            if self.metrics:
                self.metrics.delete(time.time() - start_time)
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            if self.metrics:
                self.metrics.error()
            return False
    
    async def exists(self, key: str, namespace: str = None) -> bool:
        """Check if key exists in cache"""
        cache_key = self._generate_key(key, namespace)
        
        try:
            # Check memory first
            if cache_key in self.memory_cache:
                _, expiry, _ = self.memory_cache[cache_key]
                if expiry == 0 or time.time() < expiry:
                    return True
                else:
                    del self.memory_cache[cache_key]
            
            # Check Redis
            if self.redis_client:
                return bool(await self.redis_client.exists(cache_key))
            
            return False
            
        except Exception as e:
            logger.error(f"Cache exists error for key {cache_key}: {e}")
            return False
    
    async def get_many(self, keys: List[str], namespace: str = None) -> Dict[str, Any]:
        """Get multiple values from cache"""
        cache_keys = [self._generate_key(key, namespace) for key in keys]
        results = {}
        
        try:
            # Get from Redis in batch
            if self.redis_client and cache_keys:
                values = await self.redis_client.mget(cache_keys)
                for i, value in enumerate(values):
                    if value is not None:
                        try:
                            results[keys[i]] = self._deserialize_data(value)
                        except Exception as e:
                            logger.error(f"Deserialization error for key {keys[i]}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(self, mapping: Dict[str, Any], ttl: int = None, namespace: str = None) -> bool:
        """Set multiple values in cache"""
        ttl = ttl or self.config.default_ttl
        
        try:
            if self.redis_client:
                pipeline = self.redis_client.pipeline()
                for key, value in mapping.items():
                    cache_key = self._generate_key(key, namespace)
                    serialized_data = self._serialize_data(value)
                    pipeline.setex(cache_key, ttl, serialized_data)
                
                await pipeline.execute()
            
            # Store in memory cache
            for key, value in mapping.items():
                cache_key = self._generate_key(key, namespace)
                await self._store_in_memory(cache_key, value, ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        try:
            pattern = self._generate_key("*", namespace)
            cleared_count = 0
            
            if self.redis_client:
                # Use SCAN for better performance
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self.redis_client.delete(*keys)
                        cleared_count += len(keys)
                    if cursor == 0:
                        break
            
            # Clear from memory cache
            memory_keys_to_remove = [
                k for k in self.memory_cache.keys() 
                if k.startswith(self._generate_key("", namespace))
            ]
            for k in memory_keys_to_remove:
                del self.memory_cache[k]
                cleared_count += 1
            
            logger.info(f"Cleared {cleared_count} keys from namespace '{namespace}'")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Clear namespace error: {e}")
            return 0
    
    async def warm_cache(self, warm_func: Callable, keys: List[str], namespace: str = None, ttl: int = None):
        """Warm cache with data from a function"""
        logger.info(f"Starting cache warming for {len(keys)} keys")
        
        try:
            # Batch warm the cache
            batch_size = 50
            for i in range(0, len(keys), batch_size):
                batch_keys = keys[i:i + batch_size]
                
                # Check which keys need warming
                existing_keys = []
                for key in batch_keys:
                    if await self.exists(key, namespace):
                        existing_keys.append(key)
                
                keys_to_warm = [k for k in batch_keys if k not in existing_keys]
                
                if keys_to_warm:
                    # Get data from warm function
                    if asyncio.iscoroutinefunction(warm_func):
                        warm_data = await warm_func(keys_to_warm)
                    else:
                        warm_data = warm_func(keys_to_warm)
                    
                    # Set in cache
                    if isinstance(warm_data, dict):
                        await self.set_many(warm_data, ttl, namespace)
                    
                logger.info(f"Warmed {len(keys_to_warm)} keys in batch {i // batch_size + 1}")
            
            logger.info("Cache warming completed successfully")
            
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_max_size": self.config.max_memory_items,
            "redis_connected": self.redis_client is not None
        }
        
        if self.metrics:
            stats.update(self.metrics.get_stats())
        
        # Redis stats
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info("memory")
                stats.update({
                    "redis_memory_used": redis_info.get("used_memory_human", "N/A"),
                    "redis_memory_peak": redis_info.get("used_memory_peak_human", "N/A"),
                    "redis_keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "redis_keyspace_misses": redis_info.get("keyspace_misses", 0)
                })
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
        
        return stats
    
    async def close(self):
        """Close connections and cleanup"""
        if self.redis_client:
            await self.redis_client.close()
        if self.redis_sync_client:
            self.redis_sync_client.close()
        self.memory_cache.clear()
        logger.info("Cache connections closed")


# Decorator for caching function results
def cached(ttl: int = 3600, namespace: str = None, key_func: Callable = None, cache_instance: AdvancedCache = None):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        namespace: Cache namespace
        key_func: Function to generate cache key from args
        cache_instance: Cache instance to use
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = cache_instance or get_default_cache()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache.set(cache_key, result, ttl, namespace)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async cache operations
            # This is a simplified version
            result = func(*args, **kwargs)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global cache instance
_default_cache: Optional[AdvancedCache] = None


async def initialize_cache(config: CacheConfig = None) -> AdvancedCache:
    """Initialize global cache instance"""
    global _default_cache
    _default_cache = AdvancedCache(config)
    await _default_cache.initialize()
    return _default_cache


def get_default_cache() -> AdvancedCache:
    """Get the default cache instance"""
    if _default_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _default_cache


# Cache warming helpers
async def warm_trending_cache(cache: AdvancedCache):
    """Warm cache with trending data"""
    async def get_trending_data(keys):
        # This would be implemented to fetch actual trending data
        return {key: f"trending_data_{key}" for key in keys}
    
    trending_keys = [f"trending_{i}" for i in range(100)]
    await cache.warm_cache(get_trending_data, trending_keys, "trends", ttl=3600)


async def warm_user_cache(cache: AdvancedCache, user_ids: List[str]):
    """Warm cache with user data"""
    async def get_user_data(user_ids):
        # This would be implemented to fetch actual user data
        return {user_id: f"user_data_{user_id}" for user_id in user_ids}
    
    await cache.warm_cache(get_user_data, user_ids, "users", ttl=7200)


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize cache
        config = CacheConfig(
            redis_url="redis://localhost:6379/0",
            default_ttl=3600,
            enable_metrics=True
        )
        cache = await initialize_cache(config)
        
        # Test basic operations
        await cache.set("test_key", {"data": "test_value"}, ttl=300)
        result = await cache.get("test_key")
        print(f"Cached result: {result}")
        
        # Test batch operations
        await cache.set_many({
            "key1": "value1",
            "key2": "value2", 
            "key3": "value3"
        })
        
        batch_result = await cache.get_many(["key1", "key2", "key3"])
        print(f"Batch result: {batch_result}")
        
        # Get stats
        stats = await cache.get_stats()
        print(f"Cache stats: {json.dumps(stats, indent=2)}")
        
        # Clean up
        await cache.close()
    
    # Run example
    asyncio.run(main())