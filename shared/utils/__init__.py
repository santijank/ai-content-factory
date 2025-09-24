"""
AI Content Factory - Shared Utilities Package
============================================

This package contains common utility functions and classes shared across
all services in the AI Content Factory system.

Utilities included:
- Logger: Centralized logging with structured output
- Cache: Redis-based caching with TTL support  
- RateLimiter: API rate limiting and throttling
- ErrorHandler: Exception handling and error reporting
- ConfigManager: Configuration management
- FileManager: File operations and management
- DateUtils: Date/time utilities
- StringUtils: String processing utilities
- ValidationUtils: Data validation utilities
- CryptoUtils: Encryption and security utilities

Usage:
    from shared.utils import logger, cache, rate_limiter
    
    logger.info("Starting process")
    cache.set("key", "value", ttl=3600)
    rate_limiter.check_limit("api_call", max_calls=100)
"""

import os
import sys
from typing import Any, Dict, List, Optional

# Import all utility modules
from .logger import get_logger, setup_logging, LogConfig
from .cache import CacheManager, RedisCache, MemoryCache
from .rate_limiter import RateLimiter, TokenBucket, SlidingWindow
from .error_handler import ErrorHandler, ErrorReporter, handle_errors
from .config_manager import ConfigManager, load_config, get_config
from .file_manager import FileManager, S3Manager, LocalFileManager
from .date_utils import DateUtils, format_datetime, parse_datetime
from .string_utils import StringUtils, sanitize_string, generate_slug
from .validation_utils import ValidationUtils, validate_email, validate_phone
from .crypto_utils import CryptoUtils, hash_password, encrypt_data

# Package version
__version__ = "1.0.0"

# Default configurations
DEFAULT_CONFIG = {
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': ['console', 'file']
    },
    'cache': {
        'backend': 'redis',
        'ttl': 3600,
        'max_size': 1000
    },
    'rate_limiting': {
        'default_limit': 100,
        'window_size': 3600,
        'algorithm': 'sliding_window'
    }
}

# Global instances (lazy-loaded)
_logger = None
_cache = None
_rate_limiter = None
_error_handler = None
_config_manager = None
_file_manager = None

# Export all utility classes and functions
__all__ = [
    # Core utilities
    'get_logger',
    'get_cache', 
    'get_rate_limiter',
    'get_error_handler',
    'get_config_manager',
    'get_file_manager',
    
    # Logger utilities
    'setup_logging',
    'LogConfig',
    
    # Cache utilities  
    'CacheManager',
    'RedisCache',
    'MemoryCache',
    
    # Rate limiting utilities
    'RateLimiter',
    'TokenBucket', 
    'SlidingWindow',
    
    # Error handling utilities
    'ErrorHandler',
    'ErrorReporter',
    'handle_errors',
    
    # Configuration utilities
    'ConfigManager',
    'load_config',
    'get_config',
    
    # File management utilities
    'FileManager',
    'S3Manager',
    'LocalFileManager',
    
    # Date utilities
    'DateUtils',
    'format_datetime',
    'parse_datetime',
    
    # String utilities
    'StringUtils',
    'sanitize_string',
    'generate_slug',
    
    # Validation utilities  
    'ValidationUtils',
    'validate_email',
    'validate_phone',
    
    # Crypto utilities
    'CryptoUtils', 
    'hash_password',
    'encrypt_data',
    
    # Package utilities
    'initialize_utils',
    'get_system_info',
    'cleanup_utils'
]

def get_logger(name: str = None):
    """
    Get centralized logger instance.
    
    Args:
        name: Logger name (defaults to calling module)
        
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger

def get_cache():
    """
    Get cache manager instance.
    
    Returns:
        CacheManager instance
    """
    global _cache
    if _cache is None:
        cache_config = DEFAULT_CONFIG['cache']
        if cache_config['backend'] == 'redis':
            _cache = RedisCache()
        else:
            _cache = MemoryCache()
    return _cache

def get_rate_limiter():
    """
    Get rate limiter instance.
    
    Returns:
        RateLimiter instance  
    """
    global _rate_limiter
    if _rate_limiter is None:
        config = DEFAULT_CONFIG['rate_limiting']
        _rate_limiter = RateLimiter(
            default_limit=config['default_limit'],
            window_size=config['window_size']
        )
    return _rate_limiter

def get_error_handler():
    """
    Get error handler instance.
    
    Returns:
        ErrorHandler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(
            logger=get_logger('error_handler')
        )
    return _error_handler

def get_config_manager():
    """
    Get configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_file_manager():
    """
    Get file manager instance.
    
    Returns:
        FileManager instance
    """
    global _file_manager
    if _file_manager is None:
        # Choose based on environment
        if os.getenv('AWS_ACCESS_KEY_ID'):
            _file_manager = S3Manager()
        else:
            _file_manager = LocalFileManager()
    return _file_manager

def initialize_utils(config: Dict[str, Any] = None):
    """
    Initialize all utility instances with custom configuration.
    
    Args:
        config: Custom configuration dictionary
    """
    global _logger, _cache, _rate_limiter, _error_handler, _config_manager, _file_manager
    
    # Merge with default config
    if config:
        merged_config = {**DEFAULT_CONFIG, **config}
    else:
        merged_config = DEFAULT_CONFIG
    
    # Initialize logger
    log_config = LogConfig(**merged_config['logging'])
    _logger = setup_logging(log_config)
    
    # Initialize cache
    cache_config = merged_config['cache']
    if cache_config['backend'] == 'redis':
        _cache = RedisCache(
            ttl=cache_config['ttl'],
            max_size=cache_config['max_size']
        )
    else:
        _cache = MemoryCache(
            ttl=cache_config['ttl'], 
            max_size=cache_config['max_size']
        )
    
    # Initialize rate limiter
    rl_config = merged_config['rate_limiting']
    _rate_limiter = RateLimiter(
        default_limit=rl_config['default_limit'],
        window_size=rl_config['window_size']
    )
    
    # Initialize error handler
    _error_handler = ErrorHandler(logger=_logger)
    
    # Initialize config manager
    _config_manager = ConfigManager(config=merged_config)
    
    # Initialize file manager
    _file_manager = get_file_manager()
    
    _logger.info("All utilities initialized successfully")

def get_system_info() -> Dict[str, Any]:
    """
    Get system information and utility status.
    
    Returns:
        Dictionary with system information
    """
    info = {
        'python_version': sys.version,
        'platform': sys.platform,
        'utilities': {
            'logger': _logger is not None,
            'cache': _cache is not None, 
            'rate_limiter': _rate_limiter is not None,
            'error_handler': _error_handler is not None,
            'config_manager': _config_manager is not None,
            'file_manager': _file_manager is not None
        },
        'environment': {
            'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
            'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true',
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
        }
    }
    
    # Add cache info if available
    if _cache:
        try:
            cache_info = _cache.get_info()
            info['cache_info'] = cache_info
        except Exception:
            info['cache_info'] = {'status': 'unavailable'}
    
    # Add rate limiter info if available
    if _rate_limiter:
        try:
            rl_info = _rate_limiter.get_stats()
            info['rate_limiter_info'] = rl_info
        except Exception:
            info['rate_limiter_info'] = {'status': 'unavailable'}
    
    return info

def cleanup_utils():
    """
    Cleanup and close all utility instances.
    
    Should be called on application shutdown.
    """
    global _logger, _cache, _rate_limiter, _error_handler, _config_manager, _file_manager
    
    try:
        if _cache:
            _cache.close()
        
        if _rate_limiter:
            _rate_limiter.cleanup()
        
        if _error_handler:
            _error_handler.flush()
        
        if _file_manager:
            _file_manager.cleanup()
        
        if _logger:
            _logger.info("Utilities cleanup completed")
            
    except Exception as e:
        print(f"Error during utilities cleanup: {e}")
    
    # Reset global instances
    _logger = None
    _cache = None
    _rate_limiter = None
    _error_handler = None
    _config_manager = None
    _file_manager = None

# Context manager for automatic cleanup
class UtilityContext:
    """Context manager for automatic utility initialization and cleanup."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config
    
    def __enter__(self):
        initialize_utils(self.config)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup_utils()

# Decorator for automatic error handling
def with_error_handling(func):
    """
    Decorator that adds automatic error handling to functions.
    
    Usage:
        @with_error_handling
        def my_function():
            # Function code here
            pass
    """
    def wrapper(*args, **kwargs):
        error_handler = get_error_handler()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler.handle_error(e, context={
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            })
            raise
    
    return wrapper

# Decorator for automatic caching
def with_cache(ttl: int = 3600, key_prefix: str = None):
    """
    Decorator that adds automatic caching to functions.
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Optional key prefix
    
    Usage:
        @with_cache(ttl=1800, key_prefix="user_data")
        def get_user_data(user_id):
            # Function code here
            return data
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            key_parts = [func.__name__]
            if key_prefix:
                key_parts.insert(0, key_prefix)
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator

# Decorator for rate limiting
def with_rate_limit(limit: int = 100, window: int = 3600, key_func=None):
    """
    Decorator that adds rate limiting to functions.
    
    Args:
        limit: Maximum calls per window
        window: Time window in seconds
        key_func: Function to generate rate limit key
    
    Usage:
        @with_rate_limit(limit=10, window=60)
        def api_call(user_id):
            # Function code here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            rate_limiter = get_rate_limiter()
            
            # Generate rate limit key
            if key_func:
                rl_key = key_func(*args, **kwargs)
            else:
                rl_key = f"{func.__name__}:{args[0] if args else 'global'}"
            
            # Check rate limit
            if not rate_limiter.check_limit(rl_key, limit, window):
                raise Exception(f"Rate limit exceeded for {rl_key}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Health check function
def health_check() -> Dict[str, Any]:
    """
    Perform health check on all utilities.
    
    Returns:
        Dictionary with health status
    """
    health = {
        'status': 'healthy',
        'timestamp': format_datetime(),
        'utilities': {}
    }
    
    # Check logger
    try:
        logger = get_logger()
        logger.debug("Health check")
        health['utilities']['logger'] = {'status': 'healthy'}
    except Exception as e:
        health['utilities']['logger'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'degraded'
    
    # Check cache
    try:
        cache = get_cache()
        cache.set('health_check', 'ok', ttl=60)
        cached_value = cache.get('health_check')
        if cached_value == 'ok':
            health['utilities']['cache'] = {'status': 'healthy'}
        else:
            health['utilities']['cache'] = {'status': 'unhealthy', 'error': 'cache test failed'}
            health['status'] = 'degraded'
    except Exception as e:
        health['utilities']['cache'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'degraded'
    
    # Check rate limiter
    try:
        rate_limiter = get_rate_limiter()
        can_proceed = rate_limiter.check_limit('health_check', 10, 60)
        health['utilities']['rate_limiter'] = {
            'status': 'healthy',
            'can_proceed': can_proceed
        }
    except Exception as e:
        health['utilities']['rate_limiter'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'degraded'
    
    return health

# Initialize default utilities on import (optional)
if os.getenv('AUTO_INIT_UTILS', 'false').lower() == 'true':
    initialize_utils()