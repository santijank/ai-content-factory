"""
AI Content Factory - Shared Constants Package
============================================

This package contains all system-wide constants, configuration values,
and enumeration definitions used across the AI Content Factory system.

Constants included:
- Platform Constants: Platform-specific configurations and limits
- Quality Constants: Quality tier definitions and settings
- API Constants: API endpoints, versions, and configuration
- Content Constants: Content type specifications and formats
- System Constants: System-wide settings and defaults
- Error Constants: Error codes and messages
- Cache Constants: Cache keys and TTL values
- Rate Limit Constants: Rate limiting configurations

Usage:
    from shared.constants import PLATFORMS, QUALITY_TIERS, API_ENDPOINTS
    from shared.constants.platform_constants import YOUTUBE_CONFIG
    from shared.constants.quality_constants import PREMIUM_TIER
"""

# Import all constant modules
from .platform_constants import *
from .quality_constants import *
from .api_constants import *
from .content_constants import *
from .system_constants import *
from .error_constants import *
from .cache_constants import *

# Package version
__version__ = "1.0.0"

# Export all constants
__all__ = [
    # Platform constants
    'PLATFORMS',
    'PLATFORM_CONFIGS',
    'YOUTUBE_CONFIG',
    'TIKTOK_CONFIG', 
    'INSTAGRAM_CONFIG',
    'FACEBOOK_CONFIG',
    'TWITTER_CONFIG',
    'PLATFORM_LIMITS',
    'UPLOAD_SPECIFICATIONS',
    
    # Quality constants
    'QUALITY_TIERS',
    'BUDGET_TIER',
    'BALANCED_TIER',
    'PREMIUM_TIER',
    'AI_SERVICE_CONFIGS',
    'COST_CALCULATIONS',
    'QUALITY_METRICS',
    
    # API constants
    'API_ENDPOINTS',
    'API_VERSIONS',
    'HTTP_STATUS_CODES',
    'REQUEST_TIMEOUTS',
    'RETRY_POLICIES',
    'AUTHENTICATION_TYPES',
    
    # Content constants
    'CONTENT_TYPES',
    'SUPPORTED_FORMATS',
    'RESOLUTION_PRESETS',
    'ASPECT_RATIOS',
    'BITRATE_SETTINGS',
    'AUDIO_SETTINGS',
    'COMPRESSION_SETTINGS',
    
    # System constants
    'SYSTEM_CONFIG',
    'ENVIRONMENT_VARIABLES',
    'DEFAULT_SETTINGS',
    'FEATURE_FLAGS',
    'PERFORMANCE_LIMITS',
    'SECURITY_SETTINGS',
    
    # Error constants
    'ERROR_CODES',
    'ERROR_MESSAGES',
    'HTTP_ERRORS',
    'VALIDATION_ERRORS',
    'BUSINESS_ERRORS',
    
    # Cache constants
    'CACHE_KEYS',
    'CACHE_TTL',
    'CACHE_NAMESPACES',
    
    # Utility functions
    'get_constant',
    'validate_constants',
    'get_constants_info'
]

# System-wide constants registry
CONSTANTS_REGISTRY = {}

def register_constant(name: str, value, description: str = ""):
    """
    Register a constant in the global registry.
    
    Args:
        name: Constant name
        value: Constant value
        description: Optional description
    """
    CONSTANTS_REGISTRY[name] = {
        'value': value,
        'description': description,
        'type': type(value).__name__
    }

def get_constant(name: str, default=None):
    """
    Get constant value by name.
    
    Args:
        name: Constant name
        default: Default value if not found
        
    Returns:
        Constant value or default
    """
    constant_info = CONSTANTS_REGISTRY.get(name)
    if constant_info:
        return constant_info['value']
    return default

def validate_constants() -> list:
    """
    Validate all registered constants.
    
    Returns:
        List of validation issues
    """
    issues = []
    
    for name, info in CONSTANTS_REGISTRY.items():
        value = info['value']
        
        # Check for None values
        if value is None:
            issues.append(f"Constant '{name}' has None value")
        
        # Check for empty strings
        if isinstance(value, str) and not value.strip():
            issues.append(f"Constant '{name}' has empty string value")
        
        # Check for negative numbers where inappropriate
        if isinstance(value, (int, float)) and name.endswith(('_LIMIT', '_MAX', '_SIZE')):
            if value <= 0:
                issues.append(f"Constant '{name}' should be positive but is {value}")
    
    return issues

def get_constants_info() -> dict:
    """
    Get information about all registered constants.
    
    Returns:
        Dictionary with constants information
    """
    info = {
        'total_constants': len(CONSTANTS_REGISTRY),
        'constants_by_type': {},
        'constants': {}
    }
    
    # Group by type
    for name, const_info in CONSTANTS_REGISTRY.items():
        const_type = const_info['type']
        if const_type not in info['constants_by_type']:
            info['constants_by_type'][const_type] = 0
        info['constants_by_type'][const_type] += 1
        
        # Add to constants list
        info['constants'][name] = {
            'type': const_type,
            'description': const_info['description']
        }
    
    return info

# Common validation patterns
VALIDATION_PATTERNS = {
    'EMAIL': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'URL': r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$',
    'UUID': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    'PHONE': r'^\+?1?-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$',
    'YOUTUBE_VIDEO_ID': r'^[a-zA-Z0-9_-]{11}$',
    'TIKTOK_VIDEO_ID': r'^[0-9]{19}$'
}

# Common HTTP status codes
HTTP_STATUS = {
    # Success
    'OK': 200,
    'CREATED': 201,
    'ACCEPTED': 202,
    'NO_CONTENT': 204,
    
    # Client errors
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'METHOD_NOT_ALLOWED': 405,
    'CONFLICT': 409,
    'UNPROCESSABLE_ENTITY': 422,
    'TOO_MANY_REQUESTS': 429,
    
    # Server errors
    'INTERNAL_SERVER_ERROR': 500,
    'BAD_GATEWAY': 502,
    'SERVICE_UNAVAILABLE': 503,
    'GATEWAY_TIMEOUT': 504
}

# Common time constants (in seconds)
TIME_CONSTANTS = {
    'SECOND': 1,
    'MINUTE': 60,
    'HOUR': 3600,
    'DAY': 86400,
    'WEEK': 604800,
    'MONTH': 2592000,  # 30 days
    'YEAR': 31536000   # 365 days
}

# File size constants (in bytes)
FILE_SIZE_CONSTANTS = {
    'KB': 1024,
    'MB': 1024**2,
    'GB': 1024**3,
    'TB': 1024**4,
    
    # Common file size limits
    'MAX_THUMBNAIL_SIZE': 2 * 1024**2,    # 2 MB
    'MAX_IMAGE_SIZE': 10 * 1024**2,       # 10 MB
    'MAX_AUDIO_SIZE': 100 * 1024**2,      # 100 MB
    'MAX_VIDEO_SIZE': 4 * 1024**3,        # 4 GB
    'MAX_DOCUMENT_SIZE': 50 * 1024**2     # 50 MB
}

# Content quality presets
QUALITY_PRESETS = {
    'LOW': {
        'video_bitrate': 1000,
        'audio_bitrate': 128,
        'resolution': '720x480',
        'fps': 24
    },
    'MEDIUM': {
        'video_bitrate': 2500, 
        'audio_bitrate': 192,
        'resolution': '1280x720',
        'fps': 30
    },
    'HIGH': {
        'video_bitrate': 5000,
        'audio_bitrate': 320,
        'resolution': '1920x1080', 
        'fps': 30
    },
    'ULTRA': {
        'video_bitrate': 10000,
        'audio_bitrate': 320,
        'resolution': '3840x2160',
        'fps': 60
    }
}

# Language codes (ISO 639-1)
LANGUAGE_CODES = {
    'THAI': 'th',
    'ENGLISH': 'en',
    'CHINESE': 'zh',
    'JAPANESE': 'ja',
    'KOREAN': 'ko',
    'VIETNAMESE': 'vi',
    'INDONESIAN': 'id',
    'MALAY': 'ms',
    'FILIPINO': 'fil',
    'SPANISH': 'es',
    'FRENCH': 'fr',
    'GERMAN': 'de',
    'ITALIAN': 'it',
    'PORTUGUESE': 'pt',
    'RUSSIAN': 'ru',
    'ARABIC': 'ar',
    'HINDI': 'hi'
}

# Currency codes (ISO 4217)
CURRENCY_CODES = {
    'THAI_BAHT': 'THB',
    'US_DOLLAR': 'USD',
    'EURO': 'EUR',
    'JAPANESE_YEN': 'JPY',
    'CHINESE_YUAN': 'CNY',
    'KOREAN_WON': 'KRW',
    'SINGAPORE_DOLLAR': 'SGD',
    'MALAYSIAN_RINGGIT': 'MYR',
    'INDONESIAN_RUPIAH': 'IDR',
    'VIETNAMESE_DONG': 'VND'
}

# Register all constants
def _register_all_constants():
    """Register all constants in the global registry."""
    
    # Register validation patterns
    for name, pattern in VALIDATION_PATTERNS.items():
        register_constant(f"PATTERN_{name}", pattern, f"Validation pattern for {name}")
    
    # Register HTTP status codes
    for name, code in HTTP_STATUS.items():
        register_constant(f"HTTP_{name}", code, f"HTTP status code for {name}")
    
    # Register time constants
    for name, seconds in TIME_CONSTANTS.items():
        register_constant(f"TIME_{name}", seconds, f"Time constant for {name} in seconds")
    
    # Register file size constants  
    for name, size in FILE_SIZE_CONSTANTS.items():
        register_constant(f"SIZE_{name}", size, f"File size constant for {name}")
    
    # Register quality presets
    for name, preset in QUALITY_PRESETS.items():
        register_constant(f"QUALITY_{name}", preset, f"Quality preset for {name}")
    
    # Register language codes
    for name, code in LANGUAGE_CODES.items():
        register_constant(f"LANG_{name}", code, f"Language code for {name}")
    
    # Register currency codes
    for name, code in CURRENCY_CODES.items():
        register_constant(f"CURRENCY_{name}", code, f"Currency code for {name}")

# Auto-register constants on import
_register_all_constants()

# Environment-specific constants
def get_env_constants():
    """Get environment-specific constants."""
    import os
    
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        return {
            'DEBUG': False,
            'LOG_LEVEL': 'WARNING',
            'CACHE_TTL': 3600,
            'RATE_LIMIT': 1000,
            'MAX_WORKERS': 4
        }
    elif env == 'staging':
        return {
            'DEBUG': False,
            'LOG_LEVEL': 'INFO',
            'CACHE_TTL': 1800,
            'RATE_LIMIT': 500,
            'MAX_WORKERS': 2
        }
    else:  # development
        return {
            'DEBUG': True,
            'LOG_LEVEL': 'DEBUG',
            'CACHE_TTL': 300,
            'RATE_LIMIT': 100,
            'MAX_WORKERS': 1
        }

# System limits based on tier
def get_tier_limits(tier: str):
    """Get system limits based on quality tier."""
    
    limits = {
        'budget': {
            'max_concurrent_uploads': 2,
            'max_file_size': FILE_SIZE_CONSTANTS['GB'],  # 1 GB
            'max_video_length': TIME_CONSTANTS['HOUR'],  # 1 hour
            'rate_limit': 50,
            'cache_size': 100
        },
        'balanced': {
            'max_concurrent_uploads': 5,
            'max_file_size': 4 * FILE_SIZE_CONSTANTS['GB'],  # 4 GB
            'max_video_length': 4 * TIME_CONSTANTS['HOUR'],  # 4 hours
            'rate_limit': 200,
            'cache_size': 500
        },
        'premium': {
            'max_concurrent_uploads': 10,
            'max_file_size': 128 * FILE_SIZE_CONSTANTS['GB'],  # 128 GB
            'max_video_length': 12 * TIME_CONSTANTS['HOUR'],  # 12 hours
            'rate_limit': 1000,
            'cache_size': 2000
        }
    }
    
    return limits.get(tier.lower(), limits['balanced'])

# Utility function to get all constants as dict
def get_all_constants():
    """Get all constants as a dictionary."""
    return {name: info['value'] for name, info in CONSTANTS_REGISTRY.items()}