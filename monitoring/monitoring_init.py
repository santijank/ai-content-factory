#!/usr/bin/env python3
"""
Monitoring Package for AI Content Factory
ระบบติดตามและแจ้งเตือนสำหรับ AI Content Factory

This package provides comprehensive monitoring capabilities including:
- Health monitoring for services and system resources
- Alert management through various channels (webhooks, email, etc.)
- Performance metrics collection and analysis
- Dashboard and reporting functionality
"""

__version__ = "1.0.0"
__author__ = "AI Content Factory Team"
__description__ = "Comprehensive monitoring and alerting system"

# Import main classes for easy access
try:
    from .health.service_health import (
        ServiceHealthMonitor,
        ServiceMetrics,
        HealthThreshold
    )
    
    from .alerts.webhook_alerts import (
        WebhookAlertManager,
        AlertData,
        AlertSeverity,
        WebhookType,
        WebhookConfig,
        send_critical_alert,
        send_warning_alert,
        send_info_alert
    )
    
    from .dashboard.performance_dashboard import (
        PerformanceDashboard
    ) if __name__ != '__main__' else None
    
except ImportError as e:
    # Handle import errors gracefully during development
    import logging
    logging.getLogger(__name__).warning(f"Some monitoring components not available: {e}")

# Package metadata
__all__ = [
    # Health monitoring
    'ServiceHealthMonitor',
    'ServiceMetrics', 
    'HealthThreshold',
    
    # Alert management
    'WebhookAlertManager',
    'AlertData',
    'AlertSeverity',
    'WebhookType',
    'WebhookConfig',
    'send_critical_alert',
    'send_warning_alert',
    'send_info_alert',
    
    # Dashboard (if available)
    'PerformanceDashboard',
    
    # Utility functions
    'get_system_status',
    'create_health_monitor',
    'create_alert_manager',
    'setup_monitoring'
]

# Configuration defaults
DEFAULT_CONFIG = {
    'monitoring': {
        'enabled': True,
        'check_interval': 30,
        'log_level': 'INFO'
    },
    'health': {
        'services': {},
        'thresholds': {
            'response_time_warning': 1000,
            'response_time_critical': 5000,
            'error_rate_warning': 5.0,
            'error_rate_critical': 15.0
        }
    },
    'alerts': {
        'enabled': True,
        'cooldown_minutes': 10,
        'webhooks': []
    }
}

def get_version():
    """Get package version"""
    return __version__

def get_system_status():
    """Get overall system monitoring status"""
    try:
        # Quick health check
        from .health.service_health import ServiceHealthMonitor
        monitor = ServiceHealthMonitor()
        return monitor.get_health_summary()
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Monitoring system error: {str(e)}'
        }

def create_health_monitor(config=None):
    """Factory function to create health monitor"""
    try:
        from .health.service_health import ServiceHealthMonitor
        return ServiceHealthMonitor(config)
    except ImportError:
        raise ImportError("Health monitoring components not available")

def create_alert_manager(config=None):
    """Factory function to create alert manager"""
    try:
        from .alerts.webhook_alerts import WebhookAlertManager
        return WebhookAlertManager(config)
    except ImportError:
        raise ImportError("Alert management components not available")

def setup_monitoring(config=None):
    """Setup complete monitoring system"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Merge with default config
        final_config = DEFAULT_CONFIG.copy()
        if config:
            final_config.update(config)
        
        monitoring_components = {}
        
        # Initialize health monitor
        if final_config['monitoring']['enabled']:
            health_monitor = create_health_monitor(final_config.get('health'))
            monitoring_components['health_monitor'] = health_monitor
            logger.info("Health monitor initialized")
        
        # Initialize alert manager
        if final_config['alerts']['enabled']:
            alert_manager = create_alert_manager(final_config.get('alerts'))
            monitoring_components['alert_manager'] = alert_manager
            logger.info("Alert manager initialized")
        
        # Initialize dashboard if available
        try:
            from .dashboard.performance_dashboard import PerformanceDashboard
            dashboard = PerformanceDashboard(final_config.get('dashboard'))
            monitoring_components['dashboard'] = dashboard
            logger.info("Performance dashboard initialized")
        except ImportError:
            logger.debug("Performance dashboard not available")
        
        logger.info("Monitoring system setup completed")
        return monitoring_components
        
    except Exception as e:
        logger.error(f"Failed to setup monitoring system: {str(e)}")
        raise

# Package initialization
def _initialize_package():
    """Initialize the monitoring package"""
    import logging
    import os
    
    # Setup package logging
    logger = logging.getLogger(__name__)
    
    # Set log level from environment or default
    log_level = os.getenv('MONITORING_LOG_LEVEL', 'INFO').upper()
    if hasattr(logging, log_level):
        logger.setLevel(getattr(logging, log_level))
    
    logger.debug(f"Monitoring package initialized (version {__version__})")

# Initialize when package is imported
_initialize_package()

# Package information for introspection
PACKAGE_INFO = {
    'name': 'monitoring',
    'version': __version__,
    'description': __description__,
    'author': __author__,
    'components': {
        'health': 'Service and system health monitoring',
        'alerts': 'Multi-channel alert management',
        'dashboard': 'Performance dashboard and metrics'
    },
    'features': [
        'Real-time health monitoring',
        'Webhook-based alerts (Slack, Discord, Teams)',
        'System resource monitoring',
        'Service dependency tracking',
        'Historical metrics and trends',
        'Configurable thresholds and cooldowns',
        'Rate limiting and deduplication'
    ]
}

def get_package_info():
    """Get comprehensive package information"""
    return PACKAGE_INFO.copy()

# Convenience functions for common operations
async def quick_health_check():
    """Perform quick health check of all services"""
    try:
        monitor = create_health_monitor()
        results = monitor.run_all_checks(parallel=True)
        return {
            'status': 'success',
            'results': results,
            'summary': monitor.get_health_summary()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

async def send_system_alert(title, message, severity='warning', service=None):
    """Send system alert through configured channels"""
    try:
        alert_manager = create_alert_manager()
        results = await alert_manager.send_alert(
            title=title,
            message=message,
            severity=severity,
            service=service
        )
        return {
            'status': 'success',
            'results': results
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# Export convenience functions
__all__.extend([
    'quick_health_check',
    'send_system_alert',
    'get_package_info',
    'setup_monitoring'
])
