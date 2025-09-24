#!/usr/bin/env python3
"""
Health Monitoring Module for AI Content Factory
โมดูลติดตามสุขภาพของระบบและ services ต่างๆ

This module provides comprehensive health monitoring capabilities:
- Service health monitoring with configurable intervals
- System resource monitoring (CPU, Memory, Disk, Network)
- Database and Redis health checks
- HTTP endpoint monitoring
- Metrics collection and trend analysis
- Threshold-based alerting
"""

__version__ = "1.0.0"
__description__ = "Health monitoring and metrics collection"

# Import main classes and functions
try:
    from .service_health import (
        ServiceHealthMonitor,
        ServiceMetrics,
        HealthThreshold
    )
    
    # Import from root health_check if available
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    try:
        from health_check import (
            SystemHealthChecker,
            HealthStatus,
            HealthCheckResult
        )
    except ImportError:
        # If root health_check is not available, define placeholders
        SystemHealthChecker = None
        HealthStatus = None
        HealthCheckResult = None
    
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Health monitoring components not fully available: {e}")
    
    # Define placeholder classes to prevent import errors
    class ServiceHealthMonitor:
        pass
    class ServiceMetrics:
        pass
    class HealthThreshold:
        pass

# Module exports
__all__ = [
    'ServiceHealthMonitor',
    'ServiceMetrics', 
    'HealthThreshold',
    'SystemHealthChecker',
    'HealthStatus',
    'HealthCheckResult',
    'create_health_monitor',
    'get_system_health',
    'monitor_service',
    'check_database_health',
    'check_redis_health',
    'get_health_trends'
]

# Health check types and categories
HEALTH_CHECK_TYPES = {
    'database': {
        'description': 'Database connectivity and performance',
        'category': 'infrastructure',
        'critical': True
    },
    'redis': {
        'description': 'Redis cache connectivity and performance', 
        'category': 'infrastructure',
        'critical': True
    },
    'http_service': {
        'description': 'HTTP service endpoint health',
        'category': 'application',
        'critical': True
    },
    'system_resources': {
        'description': 'System CPU, memory, and disk usage',
        'category': 'system',
        'critical': False
    },
    'external_api': {
        'description': 'External API connectivity',
        'category': 'external',
        'critical': False
    }
}

# Default health thresholds
DEFAULT_THRESHOLDS = {
    'response_time': {
        'warning': 1000,    # ms
        'critical': 5000    # ms
    },
    'error_rate': {
        'warning': 5.0,     # %
        'critical': 15.0    # %
    },
    'cpu_usage': {
        'warning': 80.0,    # %
        'critical': 95.0    # %
    },
    'memory_usage': {
        'warning': 80.0,    # %
        'critical': 95.0    # %
    },
    'disk_usage': {
        'warning': 80.0,    # %
        'critical': 95.0    # %
    }
}

def create_health_monitor(config=None):
    """Create and configure a health monitor instance"""
    try:
        monitor = ServiceHealthMonitor(config)
        return monitor
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create health monitor: {e}")
        return None

def get_system_health():
    """Get current system health status"""
    try:
        if SystemHealthChecker:
            checker = SystemHealthChecker()
            results = checker.run_all_checks(parallel=True)
            overall_status, message = checker.get_overall_status()
            
            return {
                'overall_status': overall_status.value if hasattr(overall_status, 'value') else str(overall_status),
                'message': message,
                'services': {name: result.status.value if hasattr(result.status, 'value') else str(result.status) 
                           for name, result in results.items()},
                'timestamp': results[list(results.keys())[0]].timestamp.isoformat() if results else None
            }
        else:
            return {
                'overall_status': 'unknown',
                'message': 'System health checker not available',
                'services': {},
                'timestamp': None
            }
    except Exception as e:
        return {
            'overall_status': 'error',
            'message': f'Health check failed: {str(e)}',
            'services': {},
            'timestamp': None
        }

def monitor_service(service_name, service_config, duration_minutes=5):
    """Monitor a specific service for a given duration"""
    try:
        monitor = create_health_monitor()
        if not monitor:
            return None
        
        import time
        import threading
        
        results = []
        monitoring = True
        
        def collect_metrics():
            while monitoring:
                try:
                    metrics = monitor.check_service_health(service_name)
                    results.append(metrics)
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Service monitoring error: {e}")
                    break
        
        # Start monitoring thread
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
        
        # Wait for specified duration
        time.sleep(duration_minutes * 60)
        monitoring = False
        thread.join(timeout=5)
        
        # Calculate summary statistics
        if results:
            response_times = [r.response_time_ms for r in results]
            error_rates = [r.error_rate for r in results]
            
            return {
                'service_name': service_name,
                'duration_minutes': duration_minutes,
                'total_checks': len(results),
                'avg_response_time': sum(response_times) / len(response_times),
                'max_response_time': max(response_times),
                'avg_error_rate': sum(error_rates) / len(error_rates),
                'max_error_rate': max(error_rates),
                'availability': (len([r for r in results if r.status == 'healthy']) / len(results)) * 100
            }
        
        return None
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Service monitoring failed: {e}")
        return None

def check_database_health(db_config=None):
    """Quick database health check"""
    try:
        if SystemHealthChecker:
            checker = SystemHealthChecker(config={'database': db_config} if db_config else None)
            result = checker.check_database_health()
            return {
                'status': result.status.value if hasattr(result.status, 'value') else str(result.status),
                'response_time_ms': result.response_time_ms,
                'message': result.message,
                'details': result.details
            }
        else:
            return {
                'status': 'unknown',
                'response_time_ms': 0,
                'message': 'Database health checker not available',
                'details': {}
            }
    except Exception as e:
        return {
            'status': 'error',
            'response_time_ms': 0,
            'message': f'Database health check failed: {str(e)}',
            'details': {'error': str(e)}
        }

def check_redis_health(redis_config=None):
    """Quick Redis health check"""
    try:
        if SystemHealthChecker:
            checker = SystemHealthChecker(config={'redis': redis_config} if redis_config else None)
            result = checker.check_redis_health()
            return {
                'status': result.status.value if hasattr(result.status, 'value') else str(result.status),
                'response_time_ms': result.response_time_ms,
                'message': result.message,
                'details': result.details
            }
        else:
            return {
                'status': 'unknown',
                'response_time_ms': 0,
                'message': 'Redis health checker not available',
                'details': {}
            }
    except Exception as e:
        return {
            'status': 'error',
            'response_time_ms': 0,
            'message': f'Redis health check failed: {str(e)}',
            'details': {'error': str(e)}
        }

def get_health_trends(service_name, hours=24):
    """Get health trends for a service over specified hours"""
    try:
        monitor = create_health_monitor()
        if not monitor:
            return None
        
        # Try to get trends from the monitor
        if hasattr(monitor, 'get_service_trend'):
            return monitor.get_service_trend(service_name, hours)
        else:
            return {
                'error': 'Trend analysis not available',
                'service_name': service_name,
                'hours': hours
            }
            
    except Exception as e:
        return {
            'error': f'Failed to get health trends: {str(e)}',
            'service_name': service_name,
            'hours': hours
        }

# Health status utilities
def is_healthy(status):
    """Check if a status indicates healthy state"""
    healthy_states = ['healthy', 'ok', 'up', 'running']
    return str(status).lower() in healthy_states

def is_critical(status):
    """Check if a status indicates critical state"""
    critical_states = ['critical', 'down', 'error', 'failed']
    return str(status).lower() in critical_states

def is_warning(status):
    """Check if a status indicates warning state"""
    warning_states = ['warning', 'degraded', 'slow']
    return str(status).lower() in warning_states

def get_status_priority(status):
    """Get numeric priority for status (higher = more severe)"""
    priorities = {
        'healthy': 0,
        'ok': 0,
        'up': 0,
        'running': 0,
        'warning': 1,
        'degraded': 1,
        'slow': 1,
        'critical': 2,
        'down': 2,
        'error': 2,
        'failed': 2,
        'unknown': 3
    }
    return priorities.get(str(status).lower(), 3)

# Configuration helpers
def validate_health_config(config):
    """Validate health monitoring configuration"""
    errors = []
    
    if not isinstance(config, dict):
        errors.append("Configuration must be a dictionary")
        return errors
    
    # Validate services configuration
    if 'services' in config:
        if not isinstance(config['services'], dict):
            errors.append("Services configuration must be a dictionary")
        else:
            for service_name, service_config in config['services'].items():
                if not isinstance(service_config, dict):
                    errors.append(f"Service '{service_name}' configuration must be a dictionary")
                    continue
                
                # Check required fields for HTTP services
                if service_config.get('type') == 'http' and 'url' not in service_config:
                    errors.append(f"HTTP service '{service_name}' missing 'url' field")
    
    # Validate thresholds
    if 'thresholds' in config:
        thresholds = config['thresholds']
        if not isinstance(thresholds, dict):
            errors.append("Thresholds configuration must be a dictionary")
        else:
            for metric, values in thresholds.items():
                if isinstance(values, dict):
                    if 'warning' in values and 'critical' in values:
                        if values['warning'] >= values['critical']:
                            errors.append(f"Warning threshold for '{metric}' must be less than critical threshold")
    
    return errors

def get_default_config():
    """Get default health monitoring configuration"""
    return {
        'services': {
            'database': {
                'type': 'database',
                'check_interval': 60,
                'enabled': True
            },
            'redis': {
                'type': 'redis', 
                'check_interval': 60,
                'enabled': True
            }
        },
        'thresholds': DEFAULT_THRESHOLDS.copy(),
        'monitoring': {
            'global_check_interval': 30,
            'max_retries': 3,
            'retry_delay': 5,
            'health_history_days': 7
        }
    }

# Module information
MODULE_INFO = {
    'name': 'health',
    'version': __version__,
    'description': __description__,
    'check_types': list(HEALTH_CHECK_TYPES.keys()),
    'default_thresholds': DEFAULT_THRESHOLDS,
    'functions': [func for func in __all__ if not func[0].isupper()]
}

def get_module_info():
    """Get module information"""
    return MODULE_INFO.copy()

# Add utility functions to exports
__all__.extend([
    'is_healthy',
    'is_critical', 
    'is_warning',
    'get_status_priority',
    'validate_health_config',
    'get_default_config',
    'get_module_info'
])
