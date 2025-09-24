"""
Utilities Package for AI Content Factory
Contains helper functions, configuration management, and common utilities

This package includes:
- Configuration management
- Video assembly utilities
- File handling utilities
- Logging utilities
- Cache utilities
- Error handling utilities
- Rate limiting utilities
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
from pathlib import Path

# Import utility modules (with error handling for missing modules)
try:
    from .config_manager import ConfigManager, get_config, set_config, load_config_file
except ImportError:
    ConfigManager = None
    get_config = None
    set_config = None
    load_config_file = None

try:
    from .video_assembler import VideoAssembler, assemble_video, create_video_from_assets
except ImportError:
    VideoAssembler = None
    assemble_video = None
    create_video_from_assets = None

# Logging configuration
def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    format_string: str = None
) -> logging.Logger:
    """
    Setup logging configuration for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Optional custom format string
        
    Returns:
        Configured logger instance
    """
    if not format_string:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logger
    logger = logging.getLogger("ai_content_factory")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# File utilities
def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Create a safe filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Safe filename
    """
    import re
    
    # Remove or replace invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    # Truncate if too long
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        max_name_length = max_length - len(ext)
        safe_name = name[:max_name_length] + ext
    
    return safe_name

def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
    """
    return Path(file_path).stat().st_size

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Filename
        
    Returns:
        File extension (including dot)
    """
    return Path(filename).suffix.lower()

# JSON utilities
def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Safely load JSON file with error handling
    
    Args:
        file_path: Path to JSON file
        default: Default value if loading fails
        
    Returns:
        Loaded data or default value
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        return default

def safe_json_save(data: Any, file_path: Union[str, Path]) -> bool:
    """
    Safely save data to JSON file
    
    Args:
        data: Data to save
        file_path: Path to save to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        path_obj = Path(file_path)
        ensure_directory(path_obj.parent)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

# Time utilities
def get_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    Get formatted timestamp
    
    Args:
        format_str: Timestamp format
        
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_str)

def parse_timestamp(timestamp_str: str, format_str: str = "%Y%m%d_%H%M%S") -> datetime:
    """
    Parse timestamp string to datetime
    
    Args:
        timestamp_str: Timestamp string
        format_str: Expected format
        
    Returns:
        Datetime object
    """
    return datetime.strptime(timestamp_str, format_str)

def time_since(start_time: datetime) -> str:
    """
    Get human-readable time since given datetime
    
    Args:
        start_time: Start datetime
        
    Returns:
        Human-readable time difference
    """
    diff = datetime.now() - start_time
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "Just now"

# Cache utilities
class SimpleCache:
    """
    Simple in-memory cache with TTL support
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.now() > entry['expires']:
            del self._cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        self._cache[key] = {
            'value': value,
            'expires': datetime.now() + timedelta(seconds=ttl)
        }
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries
        
        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry['expires']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)

# Rate limiting utilities
class RateLimiter:
    """
    Simple rate limiter for API calls
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: List[datetime] = []
    
    def can_proceed(self) -> bool:
        """
        Check if request can proceed
        
        Returns:
            True if under rate limit, False otherwise
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Remove old requests
        self._requests = [req_time for req_time in self._requests if req_time > cutoff]
        
        return len(self._requests) < self.max_requests
    
    def record_request(self) -> None:
        """Record a new request"""
        self._requests.append(datetime.now())
    
    def wait_time(self) -> float:
        """
        Get seconds to wait before next request
        
        Returns:
            Seconds to wait (0 if can proceed immediately)
        """
        if self.can_proceed():
            return 0.0
        
        # Find oldest request in current window
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        valid_requests = [req_time for req_time in self._requests if req_time > cutoff]
        if not valid_requests:
            return 0.0
        
        oldest_request = min(valid_requests)
        next_available = oldest_request + timedelta(seconds=self.window_seconds)
        
        return max(0.0, (next_available - now).total_seconds())

# Error handling utilities
class ContentFactoryError(Exception):
    """Base exception for Content Factory errors"""
    pass

class ConfigurationError(ContentFactoryError):
    """Configuration related errors"""
    pass

class ServiceError(ContentFactoryError):
    """Service related errors"""
    pass

class ValidationError(ContentFactoryError):
    """Validation related errors"""
    pass

def handle_async_exception(func):
    """
    Decorator for handling async function exceptions
    
    Args:
        func: Async function to wrap
        
    Returns:
        Wrapped function
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger("ai_content_factory")
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
    
    return wrapper

# Global instances
_global_cache = SimpleCache()
_global_rate_limiter = RateLimiter()

# Utility functions using global instances
def cache_get(key: str) -> Any:
    """Get value from global cache"""
    return _global_cache.get(key)

def cache_set(key: str, value: Any, ttl: int = None) -> None:
    """Set value in global cache"""
    _global_cache.set(key, value, ttl)

def cache_delete(key: str) -> bool:
    """Delete key from global cache"""
    return _global_cache.delete(key)

def cache_clear() -> None:
    """Clear global cache"""
    _global_cache.clear()

def rate_limit_check() -> bool:
    """Check global rate limit"""
    return _global_rate_limiter.can_proceed()

def rate_limit_record() -> None:
    """Record request in global rate limiter"""
    _global_rate_limiter.record_request()

# Package information
__version__ = "1.0.0"
__author__ = "AI Content Factory Team"
__description__ = "Utility functions and helpers for AI Content Factory"

# Package exports
__all__ = [
    # Configuration management
    "ConfigManager",
    "get_config",
    "set_config", 
    "load_config_file",
    
    # Video assembly
    "VideoAssembler",
    "assemble_video",
    "create_video_from_assets",
    
    # Logging
    "setup_logging",
    
    # File utilities
    "ensure_directory",
    "safe_filename",
    "get_file_size",
    "get_file_extension",
    
    # JSON utilities
    "safe_json_load",
    "safe_json_save",
    
    # Time utilities
    "get_timestamp",
    "parse_timestamp",
    "time_since",
    
    # Cache utilities
    "SimpleCache",
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_clear",
    
    # Rate limiting
    "RateLimiter",
    "rate_limit_check",
    "rate_limit_record",
    
    # Error handling
    "ContentFactoryError",
    "ConfigurationError",
    "ServiceError",
    "ValidationError",
    "handle_async_exception"
]

# Initialize logging on import
try:
    _logger = setup_logging()
    _logger.info("AI Content Factory Utils package initialized")
except Exception:
    # Fallback to basic logging if setup fails
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("ai_content_factory").info("Utils package initialized with basic logging")