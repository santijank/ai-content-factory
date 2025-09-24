"""
Advanced Caching System for AI Content Factory
รองรับ in-memory cache, Redis cache และ intelligent cache strategies
"""

import asyncio
import hashlib
import json
import pickle
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading


class CacheStrategy(Enum):
    """กลยุทธ์การ cache"""
    LRU = "lru"  # Least Recently Used
    TTL = "ttl"  # Time To Live
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out


@dataclass
class CacheItem:
    """Item ใน cache"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """ตรวจสอบว่า item หมดอายุหรือไม่"""
        if self.ttl_seconds is None:
            return False
        
        expired_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expired_time
    
    def touch(self):
        """อัปเดต access time และ count"""
        self.accessed_at = datetime.now()
        self.access_count += 1
    
    def size_bytes(self) -> int:
        """คำนวณขนาดของ item"""
        try:
            return len(pickle.dumps(self.value))
        except:
            return len(str(self.value).encode('utf-8'))


class CacheBackend(ABC):
    """Abstract base class สำหรับ cache backend"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """ดึงข้อมูลจาก cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """เก็บข้อมูลลง cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """ลบข้อมูลจาก cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """เคลียร์ cache ทั้งหมด"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """ตรวจสอบว่ามี key หรือไม่"""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """ดึงรายการ keys"""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache implementation"""
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: Optional[int] = None,
                 strategy: CacheStrategy = CacheStrategy.LRU):
        
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self._cache: Dict[str, CacheItem] = {}
        self._lock = threading.RLock()
        
        # เริ่ม background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """เริ่ม task สำหรับ cleanup expired items"""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(60)  # รันทุก 1 นาที
                await self._cleanup_expired()
        
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # No event loop running
            pass
    
    async def _cleanup_expired(self):
        """ลบ items ที่หมดอายุ"""
        with self._lock:
            expired_keys = []
            for key, item in self._cache.items():
                if item.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """ดึงข้อมูลจาก cache"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            
            # ตรวจสอบ expiry
            if item.is_expired():
                del self._cache[key]
                return None
            
            # อัปเดต access info
            item.touch()
            
            return item.value
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """เก็บข้อมูลลง cache"""
        with self._lock:
            # ใช้ default TTL ถ้าไม่ได้กำหนด
            if ttl_seconds is None:
                ttl_seconds = self.default_ttl
            
            # ลบ item เก่าถ้ามี
            if key in self._cache:
                del self._cache[key]
            
            # ตรวจสอบ size limit
            if len(self._cache) >= self.max_size:
                await self._evict_items()
            
            # สร้าง cache item ใหม่
            item = CacheItem(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds
            )
            
            self._cache[key] = item
            return True
    
    async def delete(self, key: str) -> bool:
        """ลบข้อมูลจาก cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> bool:
        """เคลียร์ cache ทั้งหมด"""
        with self._lock:
            self._cache.clear()
            return True
    
    async def exists(self, key: str) -> bool:
        """ตรวจสอบว่ามี key หรือไม่"""
        with self._lock:
            if key not in self._cache:
                return False
            
            item = self._cache[key]
            if item.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """ดึงรายการ keys"""
        import fnmatch
        
        with self._lock:
            # cleanup expired items first
            await self._cleanup_expired()
            
            if pattern == "*":
                return list(self._cache.keys())
            
            return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]
    
    async def _evict_items(self):
        """ลบ items ตาม strategy"""
        if len(self._cache) == 0:
            return
        
        # คำนวณจำนวนที่ต้องลบ (25% ของ max_size)
        evict_count = max(1, self.max_size // 4)
        
        if self.strategy == CacheStrategy.LRU:
            # ลบ items ที่ access นานที่สุด
            items = sorted(self._cache.items(), key=lambda x: x[1].accessed_at)
            
        elif self.strategy == CacheStrategy.LFU:
            # ลบ items ที่ access น้อยที่สุด
            items = sorted(self._cache.items(), key=lambda x: x[1].access_count)
            
        elif self.strategy == CacheStrategy.FIFO:
            # ลบ items ที่เก่าที่สุด
            items = sorted(self._cache.items(), key=lambda x: x[1].created_at)
            
        else:  # Default LRU
            items = sorted(self._cache.items(), key=lambda x: x[1].accessed_at)
        
        # ลบ items
        for i in range(min(evict_count, len(items))):
            key = items[i][0]
            del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """ดึงสถิติของ cache"""
        with self._lock:
            total_size_bytes = sum(item.size_bytes() for item in self._cache.values())
            
            return {
                'total_items': len(self._cache),
                'max_size': self.max_size,
                'utilization_percent': (len(self._cache) / self.max_size) * 100,
                'total_size_bytes': total_size_bytes,
                'strategy': self.strategy.value,
                'default_ttl': self.default_ttl
            }


class RedisCache(CacheBackend):
    """Redis cache implementation"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 prefix: str = "ai_factory:"):
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self._redis = None
    
    async def _get_redis(self):
        """ดึง Redis connection"""
        if self._redis is None:
            try:
                import aioredis
                self._redis = await aioredis.from_url(
                    f"redis://{self.host}:{self.port}",
                    db=self.db,
                    password=self.password,
                    decode_responses=False
                )
            except ImportError:
                raise ImportError("aioredis is required for Redis cache. Install with: pip install aioredis")
        
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """สร้าง key พร้อม prefix"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """ดึงข้อมูลจาก Redis"""
        redis = await self._get_redis()
        
        try:
            data = await redis.get(self._make_key(key))
            if data is None:
                return None
            
            return pickle.loads(data)
            
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """เก็บข้อมูลลง Redis"""
        redis = await self._get_redis()
        
        try:
            serialized_value = pickle.dumps(value)
            
            if ttl_seconds:
                await redis.setex(self._make_key(key), ttl_seconds, serialized_value)
            else:
                await redis.set(self._make_key(key), serialized_value)
            
            return True
            
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """ลบข้อมูลจาก Redis"""
        redis = await self._get_redis()
        
        try:
            result = await redis.delete(self._make_key(key))
            return result > 0
            
        except Exception:
            return False
    
    async def clear(self) -> bool:
        """เคลียร์ keys ที่มี prefix"""
        redis = await self._get_redis()
        
        try:
            keys = await redis.keys(f"{self.prefix}*")
            if keys:
                await redis.delete(*keys)
            return True
            
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """ตรวจสอบว่ามี key หรือไม่"""
        redis = await self._get_redis()
        
        try:
            result = await redis.exists(self._make_key(key))
            return result > 0
            
        except Exception:
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """ดึงรายการ keys"""
        redis = await self._get_redis()
        
        try:
            keys = await redis.keys(f"{self.prefix}{pattern}")
            # ลบ prefix ออก
            return [key.decode('utf-8')[len(self.prefix):] for key in keys]
            
        except Exception:
            return []


class SmartCache:
    """Smart cache ที่รวม multiple backends และ intelligent caching"""
    
    def __init__(self, 
                 memory_cache: Optional[MemoryCache] = None,
                 redis_cache: Optional[RedisCache] = None,
                 enable_stats: bool = True):
        
        self.memory_cache = memory_cache or MemoryCache()
        self.redis_cache = redis_cache
        self.enable_stats = enable_stats
        
        if enable_stats:
            self.stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0,
                'memory_hits': 0,
                'redis_hits': 0
            }
    
    async def get(self, key: str) -> Optional[Any]:
        """ดึงข้อมูลจาก cache (memory first, then Redis)"""
        
        # ลอง memory cache ก่อน
        value = await self.memory_cache.get(key)
        if value is not None:
            if self.enable_stats:
                self.stats['hits'] += 1
                self.stats['memory_hits'] += 1
            return value
        
        # ลอง Redis cache
        if self.redis_cache:
            value = await self.redis_cache.get(key)
            if value is not None:
                # เก็บลง memory cache ด้วย
                await self.memory_cache.set(key, value)
                
                if self.enable_stats:
                    self.stats['hits'] += 1
                    self.stats['redis_hits'] += 1
                
                return value
        
        if self.enable_stats:
            self.stats['misses'] += 1
        
        return None
    
    async def set(self, key: str, 
                 value: Any, 
                 ttl_seconds: Optional[int] = None,
                 memory_only: bool = False) -> bool:
        """เก็บข้อมูลลง cache"""
        
        success = True
        
        # เก็บลง memory cache
        memory_success = await self.memory_cache.set(key, value, ttl_seconds)
        success = success and memory_success
        
        # เก็บลง Redis cache ด้วย (ถ้าไม่ใช่ memory_only)
        if not memory_only and self.redis_cache:
            redis_success = await self.redis_cache.set(key, value, ttl_seconds)
            success = success and redis_success
        
        if self.enable_stats:
            self.stats['sets'] += 1
        
        return success
    
    async def delete(self, key: str) -> bool:
        """ลบข้อมูลจาก cache ทั้งหมด"""
        
        success = True
        
        # ลบจาก memory cache
        memory_success = await self.memory_cache.delete(key)
        
        # ลบจาก Redis cache
        if self.redis_cache:
            redis_success = await self.redis_cache.delete(key)
            success = memory_success or redis_success
        else:
            success = memory_success
        
        if self.enable_stats:
            self.stats['deletes'] += 1
        
        return success
    
    async def clear(self) -> bool:
        """เคลียร์ cache ทั้งหมด"""
        success = True
        
        success = success and await self.memory_cache.clear()
        
        if self.redis_cache:
            success = success and await self.redis_cache.clear()
        
        return success
    
    async def exists(self, key: str) -> bool:
        """ตรวจสอบว่ามี key หรือไม่"""
        
        # ตรวจสอบ memory cache ก่อน
        if await self.memory_cache.exists(key):
            return True
        
        # ตรวจสอบ Redis cache
        if self.redis_cache:
            return await self.redis_cache.exists(key)
        
        return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """ดึงสถิติของ cache"""
        stats = {}
        
        if self.enable_stats:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            stats.update({
                'total_requests': total_requests,
                'hit_rate_percent': round(hit_rate, 2),
                'cache_stats': self.stats.copy()
            })
        
        # เพิ่มสถิติ memory cache
        stats['memory_cache'] = self.memory_cache.get_stats()
        
        return stats


# Decorators สำหรับ caching functions
def cached(cache: SmartCache, 
          ttl_seconds: Optional[int] = None,
          key_generator: Optional[Callable] = None):
    """Decorator สำหรับ cache function results"""
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # สร้าง cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{_generate_key_from_args(args, kwargs)}"
            
            # ลองดึงจาก cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # เรียก function และ cache ผลลัพธ์
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            # สำหรับ sync functions
            import asyncio
            
            # สร้าง cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{_generate_key_from_args(args, kwargs)}"
            
            # ลองดึงจาก cache
            try:
                loop = asyncio.get_event_loop()
                cached_result = loop.run_until_complete(cache.get(cache_key))
                if cached_result is not None:
                    return cached_result
            except RuntimeError:
                # No event loop
                pass
            
            # เรียก function และ cache ผลลัพธ์
            result = func(*args, **kwargs)
            
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(cache.set(cache_key, result, ttl_seconds))
            except RuntimeError:
                # No event loop
                pass
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _generate_key_from_args(args, kwargs) -> str:
    """สร้าง cache key จาก function arguments"""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


# Specialized caches สำหรับ AI Content Factory
class TrendCache(SmartCache):
    """Cache เฉพาะสำหรับ trend data"""
    
    def __init__(self):
        memory_cache = MemoryCache(
            max_size=500,
            default_ttl=300,  # 5 minutes
            strategy=CacheStrategy.TTL
        )
        
        super().__init__(memory_cache=memory_cache)
    
    async def cache_trend_data(self, source: str, data: List[Dict]) -> bool:
        """Cache trend data จาก source"""
        key = f"trends:{source}:{int(time.time() // 300)}"  # 5-minute buckets
        return await self.set(key, data, ttl_seconds=300)
    
    async def get_cached_trends(self, source: str) -> Optional[List[Dict]]:
        """ดึง cached trend data"""
        key = f"trends:{source}:{int(time.time() // 300)}"
        return await self.get(key)


class AIResponseCache(SmartCache):
    """Cache เฉพาะสำหรับ AI responses"""
    
    def __init__(self):
        memory_cache = MemoryCache(
            max_size=200,
            default_ttl=1800,  # 30 minutes
            strategy=CacheStrategy.LRU
        )
        
        super().__init__(memory_cache=memory_cache)
    
    async def cache_ai_response(self, 
                               model: str, 
                               prompt_hash: str, 
                               response: Dict) -> bool:
        """Cache AI response"""
        key = f"ai_response:{model}:{prompt_hash}"
        return await self.set(key, response, ttl_seconds=1800)
    
    async def get_cached_response(self, model: str, prompt: str) -> Optional[Dict]:
        """ดึง cached AI response"""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        key = f"ai_response:{model}:{prompt_hash}"
        return await self.get(key)


# Example usage และ testing
if __name__ == "__main__":
    async def test_cache():
        # ทดสอบ MemoryCache
        print("🧪 Testing MemoryCache...")
        cache = MemoryCache(max_size=3, strategy=CacheStrategy.LRU)
        
        await cache.set("key1", "value1", ttl_seconds=60)
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        await cache.set("key4", "value4")  # Should evict key1
        
        print(f"key1 exists: {await cache.exists('key1')}")  # Should be False
        print(f"key2 value: {await cache.get('key2')}")  # Should be value2
        
        print(f"Cache stats: {cache.get_stats()}")
        
        # ทดสอบ SmartCache
        print("\n🧪 Testing SmartCache...")
        smart_cache = SmartCache()
        
        await smart_cache.set("test_key", {"data": "test"})
        result = await smart_cache.get("test_key")
        print(f"Smart cache result: {result}")
        
        print(f"Smart cache stats: {smart_cache.get_cache_stats()}")
        
        # ทดสอบ Decorator
        print("\n🧪 Testing Cache Decorator...")
        
        @cached(smart_cache, ttl_seconds=60)
        async def expensive_function(x: int, y: int) -> int:
            print(f"Computing {x} + {y}...")
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x + y
        
        # First call - should compute
        result1 = await expensive_function(5, 3)
        print(f"First call result: {result1}")
        
        # Second call - should use cache
        result2 = await expensive_function(5, 3)
        print(f"Second call result: {result2}")
        
        print("✅ Cache tests completed")
    
    # รันการทดสอบ
    asyncio.run(test_cache())