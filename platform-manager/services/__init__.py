"""
AI Content Factory - Platform Manager Services Package
====================================================

This package contains all service classes for platform integration,
upload management, and content distribution across multiple social media platforms.

Services included:
- PlatformManager: Central platform management service
- EnhancedPlatformManager: Advanced platform management with analytics
- YouTubeUploader: YouTube-specific upload and management
- TikTokUploader: TikTok-specific upload and management  
- InstagramUploader: Instagram-specific upload and management
- FacebookUploader: Facebook-specific upload and management
- TwitterUploader: Twitter-specific upload and management
- UploadScheduler: Upload scheduling and queue management
- PerformanceTracker: Performance analytics and reporting
- ContentOptimizer: Platform-specific content optimization

Architecture:
    Service Registry Pattern - Dynamic service registration and discovery
    Strategy Pattern - Platform-specific upload strategies
    Observer Pattern - Upload progress and status notifications
    Factory Pattern - Platform uploader creation

Usage:
    from platform_manager.services import PlatformManager, get_uploader
    
    manager = PlatformManager()
    uploader = manager.get_uploader('youtube')
    result = await uploader.upload(content_data, metadata)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

# Import service modules
from .platform_manager import PlatformManager
from .enhanced_platform_manager import EnhancedPlatformManager
from .uploaders.youtube_uploader import YouTubeUploader
from .uploaders.tiktok_uploader import TikTokUploader
from .uploaders.instagram_uploader import InstagramUploader
from .uploaders.facebook_uploader import FacebookUploader
from .uploaders.twitter_uploader import TwitterUploader
from .upload_scheduler import UploadScheduler
from .performance_tracker import PerformanceTracker
from .content_optimizer import ContentOptimizer
from .batch_processor import BatchProcessor
from .analytics_service import AnalyticsService

# Import shared models
from shared.models.platform_model import PlatformTypeEnum, UploadStatusEnum
from shared.constants.platform_constants import PLATFORMS

# Package version
__version__ = "1.0.0"

# Service registry
SERVICE_REGISTRY: Dict[str, Type] = {}
UPLOADER_REGISTRY: Dict[PlatformTypeEnum, Type] = {}

# Export all services
__all__ = [
    # Core services
    'PlatformManager',
    'EnhancedPlatformManager',
    'UploadScheduler',
    'PerformanceTracker',
    'ContentOptimizer',
    'BatchProcessor',
    'AnalyticsService',
    
    # Platform uploaders
    'YouTubeUploader',
    'TikTokUploader',
    'InstagramUploader', 
    'FacebookUploader',
    'TwitterUploader',
    
    # Base classes
    'BaseUploader',
    'BaseService',
    'UploadResult',
    'ServiceConfig',
    
    # Registry functions
    'register_service',
    'register_uploader',
    'get_service',
    'get_uploader',
    'get_platform_manager',
    'list_services',
    'list_uploaders',
    
    # Utility functions
    'initialize_services',
    'cleanup_services',
    'health_check_services'
]

class ServiceStatusEnum(str, Enum):
    """Service status enumeration."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class UploadResult:
    """Upload operation result."""
    success: bool
    platform: PlatformTypeEnum
    platform_id: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    upload_time: float = 0.0
    file_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'platform': self.platform.value if isinstance(self.platform, PlatformTypeEnum) else self.platform,
            'platform_id': self.platform_id,
            'platform_url': self.platform_url,
            'error_message': self.error_message,
            'metadata': self.metadata,
            'upload_time': self.upload_time,
            'file_size': self.file_size
        }

@dataclass
class ServiceConfig:
    """Service configuration."""
    name: str
    enabled: bool = True
    max_concurrent: int = 5
    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: int = 60
    rate_limit: int = 100
    settings: Dict[str, Any] = field(default_factory=dict)

class BaseService(ABC):
    """Base class for all platform services."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.status = ServiceStatusEnum.INACTIVE
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._stats = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_failed': 0,
            'avg_response_time': 0.0
        }
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup resources."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            'status': self.status.value,
            'config': {
                'name': self.config.name,
                'enabled': self.config.enabled,
                'max_concurrent': self.config.max_concurrent
            },
            'stats': self._stats.copy()
        }
    
    def update_stats(self, success: bool, response_time: float):
        """Update service statistics."""
        self._stats['requests_total'] += 1
        if success:
            self._stats['requests_success'] += 1
        else:
            self._stats['requests_failed'] += 1
        
        # Update average response time
        current_avg = self._stats['avg_response_time']
        total_requests = self._stats['requests_total']
        self._stats['avg_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )

class BaseUploader(BaseService):
    """Base class for all platform uploaders."""
    
    def __init__(self, config: ServiceConfig, platform: PlatformTypeEnum):
        super().__init__(config)
        self.platform = platform
    
    @abstractmethod
    async def upload(self, file_path: str, metadata: Dict[str, Any]) -> UploadResult:
        """Upload content to platform."""
        pass
    
    @abstractmethod
    async def delete(self, platform_id: str) -> bool:
        """Delete content from platform."""
        pass
    
    @abstractmethod
    async def update_metadata(self, platform_id: str, metadata: Dict[str, Any]) -> bool:
        """Update content metadata on platform."""
        pass
    
    @abstractmethod
    async def get_upload_status(self, platform_id: str) -> UploadStatusEnum:
        """Get upload status from platform."""
        pass
    
    async def validate_file(self, file_path: str) -> bool:
        """Validate file for platform requirements."""
        # Default implementation
        import os
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    
    async def optimize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize metadata for platform."""
        # Default implementation - override in specific uploaders
        return metadata

# Service registration functions
def register_service(name: str, service_class: Type[BaseService]):
    """Register a service class."""
    SERVICE_REGISTRY[name] = service_class
    logging.getLogger(__name__).info(f"Registered service: {name}")

def register_uploader(platform: PlatformTypeEnum, uploader_class: Type[BaseUploader]):
    """Register an uploader class for a platform."""
    UPLOADER_REGISTRY[platform] = uploader_class
    logging.getLogger(__name__).info(f"Registered uploader for platform: {platform.value}")

def get_service(name: str, config: ServiceConfig = None) -> Optional[BaseService]:
    """Get service instance by name."""
    service_class = SERVICE_REGISTRY.get(name)
    if service_class:
        if config is None:
            config = ServiceConfig(name=name)
        return service_class(config)
    return None

def get_uploader(platform: PlatformTypeEnum, config: ServiceConfig = None) -> Optional[BaseUploader]:
    """Get uploader instance for platform."""
    uploader_class = UPLOADER_REGISTRY.get(platform)
    if uploader_class:
        if config is None:
            config = ServiceConfig(name=f"{platform.value}_uploader")
        return uploader_class(config, platform)
    return None

def get_platform_manager(enhanced: bool = True) -> PlatformManager:
    """Get platform manager instance."""
    if enhanced:
        return EnhancedPlatformManager()
    return PlatformManager()

def list_services() -> List[str]:
    """List all registered services."""
    return list(SERVICE_REGISTRY.keys())

def list_uploaders() -> List[str]:
    """List all registered uploaders."""
    return [platform.value for platform in UPLOADER_REGISTRY.keys()]

# Global service instances
_service_instances: Dict[str, BaseService] = {}
_platform_manager: Optional[PlatformManager] = None

async def initialize_services(configs: Dict[str, ServiceConfig] = None) -> bool:
    """
    Initialize all services.
    
    Args:
        configs: Dictionary of service configurations
        
    Returns:
        True if all services initialized successfully
    """
    global _service_instances, _platform_manager
    
    logger = logging.getLogger(__name__)
    logger.info("Initializing platform services...")
    
    success_count = 0
    total_count = 0
    
    # Initialize platform manager
    try:
        _platform_manager = get_platform_manager()
        if await _platform_manager.initialize():
            logger.info("Platform manager initialized successfully")
            success_count += 1
        else:
            logger.error("Failed to initialize platform manager")
        total_count += 1
    except Exception as e:
        logger.error(f"Error initializing platform manager: {e}")
        total_count += 1
    
    # Initialize other services
    for service_name in SERVICE_REGISTRY.keys():
        if service_name in ['platform_manager', 'enhanced_platform_manager']:
            continue  # Already handled above
            
        try:
            config = configs.get(service_name) if configs else None
            service = get_service(service_name, config)
            
            if service and await service.initialize():
                _service_instances[service_name] = service
                logger.info(f"Service '{service_name}' initialized successfully")
                success_count += 1
            else:
                logger.error(f"Failed to initialize service '{service_name}'")
                
        except Exception as e:
            logger.error(f"Error initializing service '{service_name}': {e}")
        
        total_count += 1
    
    success_rate = success_count / total_count if total_count > 0 else 0
    logger.info(f"Services initialization completed: {success_count}/{total_count} ({success_rate:.1%})")
    
    return success_rate >= 0.8  # Consider successful if 80%+ services initialized

async def cleanup_services():
    """Cleanup all service instances."""
    global _service_instances, _platform_manager
    
    logger = logging.getLogger(__name__)
    logger.info("Cleaning up platform services...")
    
    # Cleanup service instances
    for service_name, service in _service_instances.items():
        try:
            await service.cleanup()
            logger.info(f"Service '{service_name}' cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up service '{service_name}': {e}")
    
    # Cleanup platform manager
    if _platform_manager:
        try:
            await _platform_manager.cleanup()
            logger.info("Platform manager cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up platform manager: {e}")
    
    # Clear instances
    _service_instances.clear()
    _platform_manager = None
    
    logger.info("Services cleanup completed")

async def health_check_services() -> Dict[str, Any]:
    """
    Perform health check on all services.
    
    Returns:
        Dictionary with health check results
    """
    global _service_instances, _platform_manager
    
    results = {
        'overall_status': 'healthy',
        'services': {},
        'summary': {
            'total': 0,
            'healthy': 0,
            'unhealthy': 0,
            'unknown': 0
        }
    }
    
    # Check platform manager
    if _platform_manager:
        try:
            pm_health = await _platform_manager.health_check()
            results['services']['platform_manager'] = pm_health
            
            if pm_health.get('status') == 'healthy':
                results['summary']['healthy'] += 1
            else:
                results['summary']['unhealthy'] += 1
                results['overall_status'] = 'degraded'
        except Exception as e:
            results['services']['platform_manager'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            results['summary']['unhealthy'] += 1
            results['overall_status'] = 'degraded'
        
        results['summary']['total'] += 1
    
    # Check other services
    for service_name, service in _service_instances.items():
        try:
            service_health = await service.health_check()
            results['services'][service_name] = service_health
            
            status = service_health.get('status', 'unknown')
            if status == 'healthy':
                results['summary']['healthy'] += 1
            elif status == 'unhealthy':
                results['summary']['unhealthy'] += 1
                results['overall_status'] = 'degraded'
            else:
                results['summary']['unknown'] += 1
                
        except Exception as e:
            results['services'][service_name] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            results['summary']['unhealthy'] += 1
            results['overall_status'] = 'degraded'
        
        results['summary']['total'] += 1
    
    # Determine overall status
    if results['summary']['unhealthy'] > results['summary']['healthy']:
        results['overall_status'] = 'unhealthy'
    elif results['summary']['unhealthy'] > 0:
        results['overall_status'] = 'degraded'
    
    return results

# Register default services and uploaders on import
def _register_default_services():
    """Register default services and uploaders."""
    
    # Register core services
    register_service('platform_manager', PlatformManager)
    register_service('enhanced_platform_manager', EnhancedPlatformManager)
    register_service('upload_scheduler', UploadScheduler)
    register_service('performance_tracker', PerformanceTracker)
    register_service('content_optimizer', ContentOptimizer)
    register_service('batch_processor', BatchProcessor)
    register_service('analytics_service', AnalyticsService)
    
    # Register platform uploaders
    register_uploader(PlatformTypeEnum.YOUTUBE, YouTubeUploader)
    register_uploader(PlatformTypeEnum.TIKTOK, TikTokUploader)
    register_uploader(PlatformTypeEnum.INSTAGRAM, InstagramUploader)
    register_uploader(PlatformTypeEnum.FACEBOOK, FacebookUploader)
    register_uploader(PlatformTypeEnum.TWITTER, TwitterUploader)

# Context manager for service lifecycle
class ServiceContext:
    """Context manager for automatic service initialization and cleanup."""
    
    def __init__(self, configs: Dict[str, ServiceConfig] = None):
        self.configs = configs
        
    async def __aenter__(self):
        await initialize_services(self.configs)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await cleanup_services()

# Utility function for batch uploads
async def batch_upload(
    files: List[str],
    platforms: List[PlatformTypeEnum],
    metadata: Dict[str, Any],
    max_concurrent: int = 3
) -> List[UploadResult]:
    """
    Upload files to multiple platforms concurrently.
    
    Args:
        files: List of file paths
        platforms: List of target platforms
        metadata: Upload metadata
        max_concurrent: Maximum concurrent uploads
        
    Returns:
        List of upload results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []
    
    async def upload_single(file_path: str, platform: PlatformTypeEnum) -> UploadResult:
        async with semaphore:
            uploader = get_uploader(platform)
            if uploader:
                return await uploader.upload(file_path, metadata)
            return UploadResult(success=False, platform=platform, error_message=f"No uploader found for {platform.value}")
    
    # Create upload tasks
    tasks = []
    for file_path in files:
        for platform in platforms:
            task = upload_single(file_path, platform)
            tasks.append(task)
    
    # Execute uploads
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    final_results = []
    for result in results:
        if isinstance(result, Exception):
            final_results.append(UploadResult(
                success=False,
                platform=PlatformTypeEnum.YOUTUBE,  # Default platform
                error_message=str(result)
            ))
        else:
            final_results.append(result)
    
    return final_results

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor service performance."""
    async def wrapper(self, *args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = await func(self, *args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time
            
            if hasattr(self, 'update_stats'):
                self.update_stats(success, response_time)
        
        return result
    return wrapper

# Rate limiting decorator
def rate_limit(max_calls: int = 100, window: int = 3600):
    """Decorator to add rate limiting to service methods."""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Simple rate limiting implementation
            # In production, use Redis or similar
            if hasattr(self, 'config') and hasattr(self.config, 'rate_limit'):
                if self.config.rate_limit > 0:
                    # Rate limiting logic would go here
                    pass
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator

# Error handling decorator
def handle_errors(retry_attempts: int = 3, retry_delay: int = 60):
    """Decorator to add error handling and retry logic."""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(retry_attempts):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < retry_attempts - 1:
                        if hasattr(self, 'logger'):
                            self.logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {retry_delay}s")
                        await asyncio.sleep(retry_delay)
                    else:
                        if hasattr(self, 'logger'):
                            self.logger.error(f"All {retry_attempts} attempts failed: {e}")
            
            raise last_exception
        return wrapper
    return decorator

# Service discovery utilities
class ServiceDiscovery:
    """Service discovery and registration helper."""
    
    def __init__(self):
        self._services = {}
        self._health_checks = {}
    
    def register(self, name: str, service_instance: BaseService, health_check_interval: int = 30):
        """Register a service instance."""
        self._services[name] = service_instance
        self._health_checks[name] = {
            'interval': health_check_interval,
            'last_check': 0,
            'status': 'unknown'
        }
    
    def unregister(self, name: str):
        """Unregister a service."""
        self._services.pop(name, None)
        self._health_checks.pop(name, None)
    
    def discover(self, name: str) -> Optional[BaseService]:
        """Discover a service by name."""
        return self._services.get(name)
    
    def list_services(self) -> List[str]:
        """List all registered services."""
        return list(self._services.keys())
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all registered services."""
        results = {}
        
        for name, service in self._services.items():
            try:
                health = await service.health_check()
                results[name] = health
                self._health_checks[name]['status'] = health.get('status', 'unknown')
            except Exception as e:
                results[name] = {'status': 'unhealthy', 'error': str(e)}
                self._health_checks[name]['status'] = 'unhealthy'
        
        return results

# Global service discovery instance
_service_discovery = ServiceDiscovery()

def get_service_discovery() -> ServiceDiscovery:
    """Get global service discovery instance."""
    return _service_discovery

# Configuration validation
def validate_service_config(config: ServiceConfig) -> List[str]:
    """
    Validate service configuration.
    
    Args:
        config: Service configuration to validate
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if not config.name or not config.name.strip():
        errors.append("Service name cannot be empty")
    
    if config.max_concurrent <= 0:
        errors.append("max_concurrent must be positive")
    
    if config.timeout <= 0:
        errors.append("timeout must be positive")
    
    if config.retry_attempts < 0:
        errors.append("retry_attempts cannot be negative")
    
    if config.retry_delay < 0:
        errors.append("retry_delay cannot be negative")
    
    if config.rate_limit < 0:
        errors.append("rate_limit cannot be negative")
    
    return errors

# Service metrics collection
class ServiceMetrics:
    """Service metrics collection and reporting."""
    
    def __init__(self):
        self._metrics = {}
    
    def record_metric(self, service_name: str, metric_name: str, value: float):
        """Record a metric value."""
        if service_name not in self._metrics:
            self._metrics[service_name] = {}
        
        if metric_name not in self._metrics[service_name]:
            self._metrics[service_name][metric_name] = []
        
        self._metrics[service_name][metric_name].append({
            'value': value,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        # Keep only last 1000 metrics per service/metric
        if len(self._metrics[service_name][metric_name]) > 1000:
            self._metrics[service_name][metric_name] = self._metrics[service_name][metric_name][-1000:]
    
    def get_metrics(self, service_name: str = None) -> Dict[str, Any]:
        """Get metrics for a service or all services."""
        if service_name:
            return self._metrics.get(service_name, {})
        return self._metrics.copy()
    
    def get_summary(self, service_name: str) -> Dict[str, Any]:
        """Get summary statistics for a service."""
        if service_name not in self._metrics:
            return {}
        
        summary = {}
        for metric_name, values in self._metrics[service_name].items():
            if not values:
                continue
                
            numeric_values = [v['value'] for v in values if isinstance(v['value'], (int, float))]
            if numeric_values:
                summary[metric_name] = {
                    'count': len(numeric_values),
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'avg': sum(numeric_values) / len(numeric_values),
                    'latest': numeric_values[-1]
                }
        
        return summary

# Global metrics instance
_service_metrics = ServiceMetrics()

def get_service_metrics() -> ServiceMetrics:
    """Get global service metrics instance."""
    return _service_metrics

# Auto-register default services on import
_register_default_services()

# Version info
__author__ = "AI Content Factory Team"
__email__ = "dev@aicontentfactory.com"
__status__ = "Production"