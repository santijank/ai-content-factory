#!/usr/bin/env python3
"""
AI Content Factory - Async Helpers and Utilities
==============================================

This module provides advanced async utilities including:
- Async context managers
- Concurrent execution helpers
- Retry mechanisms
- Rate limiting
- Queue management
- Background task management

Path: ai-content-factory/shared/utils/async_helpers.py
"""

import asyncio
import time
import logging
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable, TypeVar, Generic
from functools import wraps
from dataclasses import dataclass
from enum import Enum
from contextlib import asynccontextmanager
import aiohttp
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy(Enum):
    """Retry strategies for failed operations"""
    EXPONENTIAL_BACKOFF = "exponential"
    LINEAR_BACKOFF = "linear"
    FIXED_INTERVAL = "fixed"
    FIBONACCI = "fibonacci"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RetryConfig:
    """Configuration for retry operations"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    exceptions: tuple = (Exception,)
    on_retry: Optional[Callable] = None


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    calls_per_second: float = 10.0
    burst_size: int = 20
    time_window: float = 1.0


@dataclass
class TaskResult(Generic[T]):
    """Result wrapper for async tasks"""
    success: bool
    result: Optional[T] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    retries: int = 0


class AsyncRateLimiter:
    """Token bucket rate limiter for async operations"""
    
    def __init__(self, config: RateLimitConfig):
        self.calls_per_second = config.calls_per_second
        self.burst_size = config.burst_size
        self.time_window = config.time_window
        
        self.tokens = self.burst_size
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket"""
        async with self._lock:
            now = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.calls_per_second
            )
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def wait_for_tokens(self, tokens: int = 1):
        """Wait until tokens are available"""
        while not await self.acquire(tokens):
            # Calculate wait time
            wait_time = tokens / self.calls_per_second
            await asyncio.sleep(min(wait_time, 0.1))


class AsyncRetrier:
    """Advanced retry mechanism with multiple strategies"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay based on retry strategy"""
        if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.backoff_factor ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.FIXED_INTERVAL:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            fib = [1, 1]
            for i in range(2, attempt + 2):
                fib.append(fib[i-1] + fib[i-2])
            delay = self.config.base_delay * fib[attempt]
        else:
            delay = self.config.base_delay
        
        return min(delay, self.config.max_delay)
    
    async def execute(self, coro: Awaitable[T]) -> TaskResult[T]:
        """Execute coroutine with retry logic"""
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                result = await coro
                return TaskResult(
                    success=True,
                    result=result,
                    execution_time=time.time() - start_time,
                    retries=attempt
                )
            
            except self.config.exceptions as e:
                last_exception = e
                
                if self.config.on_retry:
                    try:
                        if asyncio.iscoroutinefunction(self.config.on_retry):
                            await self.config.on_retry(attempt, e)
                        else:
                            self.config.on_retry(attempt, e)
                    except Exception as retry_error:
                        logger.error(f"Error in retry callback: {retry_error}")
                
                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_attempts} attempts failed. Last error: {e}")
        
        return TaskResult(
            success=False,
            error=last_exception,
            execution_time=time.time() - start_time,
            retries=self.config.max_attempts - 1
        )


class AsyncTaskQueue:
    """Priority-based async task queue with concurrency control"""
    
    def __init__(self, max_concurrency: int = 10, max_queue_size: int = 1000):
        self.max_concurrency = max_concurrency
        self.max_queue_size = max_queue_size
        self._queue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._active_tasks = set()
        self._shutdown = False
        self._workers = []
        self._stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'active_tasks': 0
        }
    
    async def start_workers(self):
        """Start worker coroutines"""
        for i in range(self.max_concurrency):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
        logger.info(f"Started {self.max_concurrency} task queue workers")
    
    async def _worker(self, worker_id: str):
        """Worker coroutine to process tasks"""
        while not self._shutdown:
            try:
                priority, task_id, coro, future = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
                
                self._stats['active_tasks'] += 1
                start_time = time.time()
                
                try:
                    result = await coro
                    future.set_result(result)
                    self._stats['completed_tasks'] += 1
                    logger.debug(f"Worker {worker_id} completed task {task_id}")
                
                except Exception as e:
                    future.set_exception(e)
                    self._stats['failed_tasks'] += 1
                    logger.error(f"Worker {worker_id} failed task {task_id}: {e}")
                
                finally:
                    self._stats['active_tasks'] -= 1
                    execution_time = time.time() - start_time
                    logger.debug(f"Task {task_id} executed in {execution_time:.3f}s")
                    self._queue.task_done()
            
            except asyncio.TimeoutError:
                # No tasks available, continue
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
    
    async def submit(self, coro: Awaitable[T], priority: TaskPriority = TaskPriority.NORMAL, task_id: str = None) -> T:
        """Submit a task to the queue"""
        if self._shutdown:
            raise RuntimeError("Task queue is shutdown")
        
        task_id = task_id or f"task-{self._stats['total_tasks']}"
        future = asyncio.Future()
        
        try:
            # Lower number = higher priority
            priority_value = 5 - priority.value
            await self._queue.put((priority_value, task_id, coro, future))
            self._stats['total_tasks'] += 1
            
            return await future
        
        except asyncio.QueueFull:
            raise RuntimeError("Task queue is full")
    
    async def shutdown(self, timeout: float = 30.0):
        """Shutdown the task queue"""
        self._shutdown = True
        
        # Wait for active tasks to complete
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for tasks to complete")
        
        # Cancel workers
        for worker in self._workers:
            worker.cancel()
        
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        logger.info("Task queue shutdown completed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            **self._stats,
            'queue_size': self._queue.qsize(),
            'max_concurrency': self.max_concurrency,
            'max_queue_size': self.max_queue_size,
            'is_shutdown': self._shutdown
        }


class AsyncBatchProcessor:
    """Batch processor for efficient async operations"""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch = []
        self._last_flush = time.time()
        self._lock = asyncio.Lock()
        self._flush_task = None
        self._shutdown = False
    
    async def start(self):
        """Start the batch processor"""
        self._flush_task = asyncio.create_task(self._flush_timer())
    
    async def add_item(self, item: Any, processor: Callable[[List[Any]], Awaitable]):
        """Add item to batch for processing"""
        async with self._lock:
            if self._shutdown:
                return
            
            self._batch.append((item, processor))
            
            if len(self._batch) >= self.batch_size:
                await self._flush_batch()
    
    async def _flush_batch(self):
        """Process current batch"""
        if not self._batch:
            return
        
        # Group items by processor
        processors = {}
        for item, processor in self._batch:
            if processor not in processors:
                processors[processor] = []
            processors[processor].append(item)
        
        # Process each group
        tasks = []
        for processor, items in processors.items():
            tasks.append(processor(items))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self._batch.clear()
        self._last_flush = time.time()
    
    async def _flush_timer(self):
        """Periodic flush timer"""
        while not self._shutdown:
            await asyncio.sleep(1.0)
            
            if time.time() - self._last_flush >= self.flush_interval:
                async with self._lock:
                    await self._flush_batch()
    
    async def shutdown(self):
        """Shutdown the batch processor"""
        self._shutdown = True
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        async with self._lock:
            await self._flush_batch()


class AsyncContextManager:
    """Generic async context manager for resource management"""
    
    def __init__(self, setup_func: Callable[[], Awaitable], cleanup_func: Callable[[Any], Awaitable]):
        self.setup_func = setup_func
        self.cleanup_func = cleanup_func
        self.resource = None
    
    async def __aenter__(self):
        self.resource = await self.setup_func()
        return self.resource
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.resource is not None:
            await self.cleanup_func(self.resource)


@asynccontextmanager
async def async_timeout(seconds: float):
    """Context manager for async timeout"""
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {seconds} seconds")
        raise


class AsyncCircuitBreaker:
    """Circuit breaker pattern for async operations"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0, expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, coro: Awaitable[T]) -> T:
        """Execute coroutine with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await coro
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# Decorators and utility functions

def async_retry(config: RetryConfig = None):
    """Decorator for adding retry logic to async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retrier = AsyncRetrier(config)
            result = await retrier.execute(func(*args, **kwargs))
            if result.success:
                return result.result
            else:
                raise result.error
        return wrapper
    return decorator


def async_rate_limit(config: RateLimitConfig):
    """Decorator for rate limiting async functions"""
    rate_limiter = AsyncRateLimiter(config)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await rate_limiter.wait_for_tokens()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def async_timeout_decorator(seconds: float):
    """Decorator for adding timeout to async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with async_timeout(seconds):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


async def gather_with_concurrency(coros: List[Awaitable[T]], limit: int = 10) -> List[T]:
    """Execute coroutines with concurrency limit"""
    semaphore = asyncio.Semaphore(limit)
    
    async def sem_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*[sem_coro(coro) for coro in coros])


async def gather_with_progress(coros: List[Awaitable[T]], progress_callback: Callable[[int, int], None] = None) -> List[T]:
    """Execute coroutines with progress tracking"""
    results = []
    total = len(coros)
    
    for i, coro in enumerate(asyncio.as_completed(coros)):
        result = await coro
        results.append(result)
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    return results


async def run_with_timeout_and_retry(coro: Awaitable[T], timeout: float = 30.0, retry_config: RetryConfig = None) -> T:
    """Run coroutine with both timeout and retry"""
    retry_config = retry_config or RetryConfig()
    retrier = AsyncRetrier(retry_config)
    
    async def timeout_coro():
        async with async_timeout(timeout):
            return await coro
    
    result = await retrier.execute(timeout_coro())
    if result.success:
        return result.result
    else:
        raise result.error


class AsyncResourcePool:
    """Generic async resource pool"""
    
    def __init__(self, create_resource: Callable[[], Awaitable[T]], max_size: int = 10, min_size: int = 1):
        self.create_resource = create_resource
        self.max_size = max_size
        self.min_size = min_size
        self._pool = asyncio.Queue(maxsize=max_size)
        self._current_size = 0
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the pool with minimum resources"""
        for _ in range(self.min_size):
            resource = await self.create_resource()
            await self._pool.put(resource)
            self._current_size += 1
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a resource from the pool"""
        resource = None
        try:
            # Try to get from pool or create new one
            try:
                resource = self._pool.get_nowait()
            except asyncio.QueueEmpty:
                if self._current_size < self.max_size:
                    async with self._lock:
                        if self._current_size < self.max_size:
                            resource = await self.create_resource()
                            self._current_size += 1
                
                if resource is None:
                    resource = await self._pool.get()
            
            yield resource
        
        finally:
            if resource is not None:
                try:
                    self._pool.put_nowait(resource)
                except asyncio.QueueFull:
                    # Pool is full, discard the resource
                    self._current_size -= 1


# Background task management
class BackgroundTaskManager:
    """Manager for background async tasks"""
    
    def __init__(self):
        self._tasks = set()
        self._shutdown = False
    
    def create_task(self, coro: Awaitable, name: str = None) -> asyncio.Task:
        """Create and track a background task"""
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
    
    def create_periodic_task(self, coro_func: Callable[[], Awaitable], interval: float, name: str = None) -> asyncio.Task:
        """Create a periodic background task"""
        async def periodic_runner():
            while not self._shutdown:
                try:
                    await coro_func()
                except Exception as e:
                    logger.error(f"Error in periodic task {name}: {e}")
                
                try:
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
        
        return self.create_task(periodic_runner(), name)
    
    async def shutdown(self, timeout: float = 30.0):
        """Shutdown all background tasks"""
        self._shutdown = True
        
        if not self._tasks:
            return
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Some tasks didn't complete within {timeout}s timeout")
    
    def get_active_tasks(self) -> List[asyncio.Task]:
        """Get list of active tasks"""
        return [task for task in self._tasks if not task.done()]


# HTTP client helpers
class AsyncHTTPClient:
    """Async HTTP client with advanced features"""
    
    def __init__(self, timeout: float = 30.0, max_retries: int = 3, rate_limit_config: RateLimitConfig = None):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.rate_limiter = AsyncRateLimiter(rate_limit_config) if rate_limit_config else None
        self._session = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with rate limiting and retries"""
        if self.rate_limiter:
            await self.rate_limiter.wait_for_tokens()
        
        retry_config = RetryConfig(
            max_attempts=self.max_retries,
            exceptions=(aiohttp.ClientError, asyncio.TimeoutError)
        )
        retrier = AsyncRetrier(retry_config)
        
        async def make_request():
            return await self._session.request(method, url, **kwargs)
        
        result = await retrier.execute(make_request())
        if result.success:
            return result.result
        else:
            raise result.error


# Utility functions for common async patterns
async def async_map(func: Callable[[T], Awaitable[Any]], items: List[T], concurrency: int = 10) -> List[Any]:
    """Async version of map with concurrency control"""
    coros = [func(item) for item in items]
    return await gather_with_concurrency(coros, concurrency)


async def async_filter(predicate: Callable[[T], Awaitable[bool]], items: List[T]) -> List[T]:
    """Async version of filter"""
    results = await asyncio.gather(*[predicate(item) for item in items])
    return [item for item, keep in zip(items, results) if keep]


async def debounce_async(func: Callable[..., Awaitable[T]], delay: float = 1.0):
    """Debounce async function calls"""
    last_called = 0
    task = None
    
    async def debounced(*args, **kwargs):
        nonlocal last_called, task
        
        last_called = time.time()
        
        if task:
            task.cancel()
        
        async def delayed_call():
            await asyncio.sleep(delay)
            if time.time() - last_called >= delay:
                return await func(*args, **kwargs)
        
        task = asyncio.create_task(delayed_call())
        return await task
    
    return debounced


# Example usage and tests
if __name__ == "__main__":
    async def example_usage():
        logger.info("Testing async helpers...")
        
        # Test retry mechanism
        @async_retry(RetryConfig(max_attempts=3, base_delay=0.1))
        async def flaky_function():
            import random
            if random.random() < 0.7:
                raise Exception("Random failure")
            return "Success!"
        
        try:
            result = await flaky_function()
            logger.info(f"Retry test result: {result}")
        except Exception as e:
            logger.error(f"Retry test failed: {e}")
        
        # Test rate limiting
        rate_config = RateLimitConfig(calls_per_second=5.0, burst_size=10)
        
        @async_rate_limit(rate_config)
        async def rate_limited_function(x):
            return f"Processed {x}"
        
        start_time = time.time()
        tasks = [rate_limited_function(i) for i in range(15)]
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        logger.info(f"Rate limiting test: {len(results)} calls in {execution_time:.2f}s")
        
        # Test task queue
        task_queue = AsyncTaskQueue(max_concurrency=3)
        await task_queue.start_workers()
        
        async def queue_task(x):
            await asyncio.sleep(0.1)
            return x * 2
        
        queue_tasks = [
            task_queue.submit(queue_task(i), TaskPriority.NORMAL) 
            for i in range(10)
        ]
        queue_results = await asyncio.gather(*queue_tasks)
        
        logger.info(f"Task queue results: {queue_results}")
        logger.info(f"Task queue stats: {task_queue.get_stats()}")
        
        await task_queue.shutdown()
        logger.info("Async helpers test completed")
    
    # Run the example
    asyncio.run(example_usage())