"""
Rate Limiter Module
จำกัด API calls สำหรับ services ต่างๆ ในระบบ AI Content Factory
"""

import asyncio
import time
import threading
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RateLimitStrategy(Enum):
    """กลยุทธ์การจำกัด rate"""
    TOKEN_BUCKET = "token_bucket"      # Token bucket algorithm
    SLIDING_WINDOW = "sliding_window"  # Sliding window counter
    FIXED_WINDOW = "fixed_window"      # Fixed window counter

@dataclass
class RateLimitConfig:
    """Configuration สำหรับ rate limiting"""
    max_requests: int           # จำนวน requests สูงสุด
    time_window: int           # ช่วงเวลา (วินาที)
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    burst_limit: Optional[int] = None  # จำนวน requests ที่ยอมให้ burst
    backoff_factor: float = 1.5        # Factor สำหรับ exponential backoff

class TokenBucket:
    """
    Token Bucket Rate Limiter Implementation
    """
    
    def __init__(self, max_tokens: int, refill_rate: float):
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        พยายาม consume tokens
        Returns True ถ้าสำเร็จ, False ถ้า tokens ไม่พอ
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """เติม tokens ตาม refill rate"""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def wait_time(self, tokens: int = 1) -> float:
        """คำนวณเวลาที่ต้องรอเพื่อให้มี tokens พอ"""
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - self.tokens
            return tokens_needed / self.refill_rate

class SlidingWindowLimiter:
    """
    Sliding Window Rate Limiter Implementation
    """
    
    def __init__(self, max_requests: int, window_size: int):
        self.max_requests = max_requests
        self.window_size = window_size  # seconds
        self.requests = deque()
        self.lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """ตรวจสอบว่า request นี้ allowed หรือไม่"""
        with self.lock:
            now = time.time()
            
            # ลบ requests ที่เก่าเกินไปออก
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()
            
            # ตรวจสอบว่าเกิน limit หรือไม่
            if len(self.requests) >= self.max_requests:
                return False
            
            # เพิ่ม request ปัจจุบัน
            self.requests.append(now)
            return True
    
    def wait_time(self) -> float:
        """คำนวณเวลาที่ต้องรอ"""
        with self.lock:
            now = time.time()
            
            # ลบ requests เก่าออก
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()
            
            if len(self.requests) < self.max_requests:
                return 0.0
            
            # เวลาที่ต้องรอ = เวลาที่ request เก่าสุดจะหมดอายุ
            oldest_request = self.requests[0]
            return (oldest_request + self.window_size) - now

class FixedWindowLimiter:
    """
    Fixed Window Rate Limiter Implementation
    """
    
    def __init__(self, max_requests: int, window_size: int):
        self.max_requests = max_requests
        self.window_size = window_size
        self.current_window = 0
        self.requests_count = 0
        self.lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """ตรวจสอบว่า request นี้ allowed หรือไม่"""
        with self.lock:
            current_time = int(time.time())
            window_start = (current_time // self.window_size) * self.window_size
            
            # ถ้าเป็น window ใหม่ ให้ reset counter
            if window_start != self.current_window:
                self.current_window = window_start
                self.requests_count = 0
            
            # ตรวจสอบ limit
            if self.requests_count >= self.max_requests:
                return False
            
            self.requests_count += 1
            return True
    
    def wait_time(self) -> float:
        """คำนวณเวลาที่ต้องรอ"""
        with self.lock:
            current_time = int(time.time())
            window_start = (current_time // self.window_size) * self.window_size
            
            if window_start != self.current_window:
                return 0.0  # Window ใหม่แล้ว
            
            if self.requests_count < self.max_requests:
                return 0.0
            
            # รอจนกว่า window ถัดไปจะเริ่ม
            next_window = window_start + self.window_size
            return next_window - current_time

class RateLimiter:
    """
    Main Rate Limiter Class
    จัดการ rate limiting สำหรับ services ต่างๆ
    """
    
    def __init__(self):
        self.limiters: Dict[str, Union[TokenBucket, SlidingWindowLimiter, FixedWindowLimiter]] = {}
        self.configs: Dict[str, RateLimitConfig] = {}
        self.stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "last_blocked": 0
        })
        self.lock = threading.Lock()
    
    def configure_service(self, service_name: str, config: RateLimitConfig):
        """กำหนดค่า rate limiting สำหรับ service"""
        with self.lock:
            self.configs[service_name] = config
            
            if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                # Token bucket: refill rate = max_requests / time_window
                refill_rate = config.max_requests / config.time_window
                self.limiters[service_name] = TokenBucket(config.max_requests, refill_rate)
                
            elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                self.limiters[service_name] = SlidingWindowLimiter(
                    config.max_requests, config.time_window
                )
                
            elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
                self.limiters[service_name] = FixedWindowLimiter(
                    config.max_requests, config.time_window
                )
    
    def is_allowed(self, service_name: str, tokens: int = 1) -> bool:
        """ตรวจสอบว่า request นี้ allowed หรือไม่"""
        if service_name not in self.limiters:
            # ถ้าไม่ได้กำหนด rate limit ให้ allow ทุก request
            return True
        
        limiter = self.limiters[service_name]
        self.stats[service_name]["total_requests"] += 1
        
        # ตรวจสอบ rate limit
        if isinstance(limiter, TokenBucket):
            allowed = limiter.consume(tokens)
        else:
            allowed = limiter.is_allowed()
        
        # Update statistics
        if allowed:
            self.stats[service_name]["allowed_requests"] += 1
        else:
            self.stats[service_name]["blocked_requests"] += 1
            self.stats[service_name]["last_blocked"] = int(time.time())
        
        return allowed
    
    def wait_time(self, service_name: str, tokens: int = 1) -> float:
        """คำนวณเวลาที่ต้องรอสำหรับ request ต่อไป"""
        if service_name not in self.limiters:
            return 0.0
        
        limiter = self.limiters[service_name]
        
        if isinstance(limiter, TokenBucket):
            return limiter.wait_time(tokens)
        else:
            return limiter.wait_time()
    
    async def wait_for_capacity(self, service_name: str, tokens: int = 1, timeout: float = 60.0):
        """รอจนกว่าจะมี capacity สำหรับ request"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_allowed(service_name, tokens):
                return True
            
            wait_time = self.wait_time(service_name, tokens)
            if wait_time > 0:
                sleep_time = min(wait_time, timeout - (time.time() - start_time))
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(0.1)  # Short sleep to prevent busy waiting
        
        return False  # Timeout
    
    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """ดู statistics ของ service"""
        if service_name not in self.stats:
            return {"error": "Service not found"}
        
        stats = dict(self.stats[service_name])
        
        # เพิ่มข้อมูลเพิ่มเติม
        if service_name in self.limiters:
            stats["wait_time"] = self.wait_time(service_name)
            
            if isinstance(self.limiters[service_name], TokenBucket):
                bucket = self.limiters[service_name]
                with bucket.lock:
                    bucket._refill()
                    stats["available_tokens"] = int(bucket.tokens)
                    stats["max_tokens"] = bucket.max_tokens
        
        return stats
    
    def get_all_stats(self) -> Dict[str, Any]:
        """ดู statistics ของทุก services"""
        return {
            service: self.get_service_stats(service)
            for service in self.stats.keys()
        }
    
    def reset_stats(self, service_name: Optional[str] = None):
        """Reset statistics"""
        if service_name:
            if service_name in self.stats:
                self.stats[service_name] = {
                    "total_requests": 0,
                    "allowed_requests": 0,
                    "blocked_requests": 0,
                    "last_blocked": 0
                }
        else:
            self.stats.clear()

# Decorator Functions
def rate_limit(service_name: str, 
              tokens: int = 1, 
              rate_limiter: RateLimiter = None,
              timeout: float = 60.0):
    """
    Decorator สำหรับ apply rate limiting automatically
    """
    if rate_limiter is None:
        rate_limiter = global_rate_limiter
    
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                success = await rate_limiter.wait_for_capacity(service_name, tokens, timeout)
                if not success:
                    raise Exception(f"Rate limit timeout for service: {service_name}")
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                if not rate_limiter.is_allowed(service_name, tokens):
                    wait_time = rate_limiter.wait_time(service_name, tokens)
                    if wait_time > timeout:
                        raise Exception(f"Rate limit exceeded for service: {service_name}")
                    time.sleep(wait_time)
                    
                    # Try again after waiting
                    if not rate_limiter.is_allowed(service_name, tokens):
                        raise Exception(f"Still rate limited after waiting: {service_name}")
                
                return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator

# Global Rate Limiter Instance
global_rate_limiter = RateLimiter()

# Predefined Configurations for Common Services
AI_SERVICE_CONFIGS = {
    "groq_free": RateLimitConfig(
        max_requests=14400,    # 14.4k requests per day
        time_window=86400,     # 24 hours
        strategy=RateLimitStrategy.TOKEN_BUCKET
    ),
    "openai_gpt4": RateLimitConfig(
        max_requests=500,      # 500 requests per day (free tier)
        time_window=86400,
        strategy=RateLimitStrategy.TOKEN_BUCKET
    ),
    "claude_api": RateLimitConfig(
        max_requests=1000,     # 1000 requests per day
        time_window=86400,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ),
    "youtube_api": RateLimitConfig(
        max_requests=10000,    # 10k units per day
        time_window=86400,
        strategy=RateLimitStrategy.FIXED_WINDOW
    ),
    "elevenlabs_free": RateLimitConfig(
        max_requests=10000,    # 10k characters per month
        time_window=2592000,   # 30 days
        strategy=RateLimitStrategy.TOKEN_BUCKET
    ),
    "leonardo_ai": RateLimitConfig(
        max_requests=150,      # 150 images per day (free tier)
        time_window=86400,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )
}

def setup_default_limits():
    """ตั้งค่า default rate limits สำหรับ services ทั่วไป"""
    for service, config in AI_SERVICE_CONFIGS.items():
        global_rate_limiter.configure_service(service, config)

# Convenience Functions
def configure_service(service_name: str, config: RateLimitConfig):
    """Convenience function สำหรับ configure service"""
    global_rate_limiter.configure_service(service_name, config)

def is_allowed(service_name: str, tokens: int = 1) -> bool:
    """Convenience function สำหรับตรวจสอบ rate limit"""
    return global_rate_limiter.is_allowed(service_name, tokens)

def wait_time(service_name: str, tokens: int = 1) -> float:
    """Convenience function สำหรับดู wait time"""
    return global_rate_limiter.wait_time(service_name, tokens)

async def wait_for_capacity(service_name: str, tokens: int = 1, timeout: float = 60.0) -> bool:
    """Convenience function สำหรับรอ capacity"""
    return await global_rate_limiter.wait_for_capacity(service_name, tokens, timeout)

# Initialize default configurations
setup_default_limits()

# Example Usage
if __name__ == "__main__":
    import asyncio
    
    # Test rate limiter
    limiter = RateLimiter()
    
    # Configure a test service (5 requests per 10 seconds)
    config = RateLimitConfig(
        max_requests=5,
        time_window=10,
        strategy=RateLimitStrategy.TOKEN_BUCKET
    )
    limiter.configure_service("test_service", config)
    
    # Test requests
    for i in range(10):
        allowed = limiter.is_allowed("test_service")
        print(f"Request {i+1}: {'Allowed' if allowed else 'Blocked'}")
        
        if not allowed:
            wait = limiter.wait_time("test_service")
            print(f"  Wait time: {wait:.2f} seconds")
    
    print("\nService stats:", limiter.get_service_stats("test_service"))