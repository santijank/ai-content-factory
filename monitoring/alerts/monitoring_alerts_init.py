#!/usr/bin/env python3
"""
Alert Management Module for AI Content Factory
โมดูลจัดการการแจ้งเตือนผ่านช่องทางต่างๆ

This module provides comprehensive alert management capabilities:
- Multi-channel alert delivery (Slack, Discord, Teams, Email, SMS)
- Smart alert management (cooldowns, rate limiting, deduplication)
- Rich formatting for different platforms
- Retry logic and failure handling
- Alert history and analytics
- Template-based alert formatting
"""

__version__ = "1.0.0"
__description__ = "Multi-channel alert management and delivery"

# Import main classes and functions
try:
    from .webhook_alerts import (
        WebhookAlertManager,
        AlertData,
        AlertSeverity,
        WebhookType,
        WebhookConfig,
        send_critical_alert,
        send_warning_alert,
        send_info_alert
    )
    
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Alert management components not fully available: {e}")
    
    # Define placeholder classes to prevent import errors
    class WebhookAlertManager:
        pass
    class AlertData:
        pass
    class AlertSeverity:
        pass
    class WebhookType:
        pass
    class WebhookConfig:
        pass
    
    async def send_critical_alert(*args, **kwargs):
        pass
    async def send_warning_alert(*args, **kwargs):
        pass
    async def send_info_alert(*args, **kwargs):
        pass

# Module exports
__all__ = [
    'WebhookAlertManager',
    'AlertData',
    'AlertSeverity', 
    'WebhookType',
    'WebhookConfig',
    'send_critical_alert',
    'send_warning_alert',
    'send_info_alert',
    'create_alert_manager',
    'send_alert',
    'format_alert_message',
    'validate_webhook_config',
    'get_alert_templates',
    'create_webhook_config'
]

# Alert severity levels and their properties
SEVERITY_LEVELS = {
    'info': {
        'priority': 1,
        'color': '#36a64f',  # Green
        'emoji': 'ℹ️',
        'description': 'Informational message'
    },
    'warning': {
        'priority': 2,
        'color': '#ff9500',  # Orange
        'emoji': '⚠️',
        'description': 'Warning condition that needs attention'
    },
    'critical': {
        'priority': 3,
        'color': '#ff0000',  # Red
        'emoji': '🚨',
        'description': 'Critical condition requiring immediate action'
    }
}

# Supported webhook platforms and their properties
WEBHOOK_PLATFORMS = {
    'slack': {
        'name': 'Slack',
        'supports_rich_formatting': True,
        'supports_attachments': True,
        'supports_buttons': True,
        'max_message_length': 4000,
        'rate_limit': '1 per second'
    },
    'discord': {
        'name': 'Discord',
        'supports_rich_formatting': True,
        'supports_attachments': True,
        'supports_buttons': False,
        'max_message_length': 2000,
        'rate_limit': '5 per 5 seconds'
    },
    'teams': {
        'name': 'Microsoft Teams',
        'supports_rich_formatting': True,
        'supports_attachments': True,
        'supports_buttons': True,
        'max_message_length': 4000,
        'rate_limit': '1 per second'
    },
    'generic': {
        'name': 'Generic Webhook',
        'supports_rich_formatting': False,
        'supports_attachments': False,
        'supports_buttons': False,
        'max_message_length': 8000,
        'rate_limit': 'Varies'
    }
}

# Default alert templates
ALERT_TEMPLATES = {
    'service_down': {
        'title': 'Service Down Alert',
        'message': 'Service {{service}} is currently down and not responding.',
        'severity': 'critical',
        'fields': ['service', 'last_check', 'response_time']
    },
    'high_response_time': {
        'title': 'High Response Time',
        'message': 'Service {{service}} response time is {{response_time}}ms, exceeding threshold.',
        'severity': 'warning',
        'fields': ['service', 'response_time', 'threshold']
    },
    'system_resource_warning': {
        'title': 'System Resource Warning',
        'message': 'System {{resource}} usage is {{usage}}%, approaching critical levels.',
        'severity': 'warning',
        'fields': ['resource', 'usage', 'threshold']
    },
    'database_connection_error': {
        'title': 'Database Connection Error',
        'message': 'Unable to connect to database {{database}}. Please check connection.',
        'severity': 'critical',
        'fields': ['database', 'error_message', 'retry_count']
    },
    'deployment_success': {
        'title': 'Deployment Successful',
        'message': 'Successfully deployed {{version}} to {{environment}}.',
        'severity': 'info',
        'fields': ['version', 'environment', 'deployment_time']
    }
}

def create_alert_manager(config=None):
    """Create and configure an alert manager instance"""
    try:
        manager = WebhookAlertManager(config)
        return manager
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create alert manager: {e}")
        return None

async def send_alert(title, message, severity='info', service=None, data=None, config=None):
    """Send alert through configured channels"""
    try:
        manager = create_alert_manager(config)
        if not manager:
            return {'error': 'Failed to create alert manager'}
        
        results = await manager.send_alert(
            title=title,
            message=message,
            severity=severity,
            service=service,
            data=data
        )
        
        return {
            'status': 'success',
            'results': results,
            'timestamp': AlertData(title, message, AlertSeverity(severity)).timestamp.isoformat()
        }
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send alert: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

def format_alert_message(template_name, data=None):
    """Format alert message using template and data"""
    try:
        if template_name not in ALERT_TEMPLATES:
            return None
        
        template = ALERT_TEMPLATES[template_name]
        message = template['message']
        
        # Replace template variables
        if data:
            for key, value in data.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in message:
                    message = message.replace(placeholder, str(value))
        
        return {
            'title': template['title'],
            'message': message,
            'severity': template['severity'],
            'suggested_fields': template.get('fields', [])
        }
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to format alert message: {e}")
        return None

def validate_webhook_config(config):
    """Validate webhook configuration"""
    errors = []
    
    if not isinstance(config, dict):
        errors.append("Configuration must be a dictionary")
        return errors
    
    # Required fields
    required_fields = ['name', 'type', 'url']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate webhook type
    if 'type' in config:
        if config['type'] not in WEBHOOK_PLATFORMS:
            errors.append(f"Unsupported webhook type: {config['type']}")
    
    # Validate URL
    if 'url' in config:
        if not isinstance(config['url'], str) or not config['url'].startswith(('http://', 'https://')):
            errors.append("URL must be a valid HTTP/HTTPS URL")
    
    # Validate timeout
    if 'timeout' in config:
        if not isinstance(config['timeout'], (int, float)) or config['timeout'] <= 0:
            errors.append("Timeout must be a positive number")
    
    # Validate retry count
    if 'retry_count' in config:
        if not isinstance(config['retry_count'], int) or config['retry_count'] < 0:
            errors.append("Retry count must be a non-negative integer")
    
    return errors

def create_webhook_config(name, webhook_type, url, **kwargs):
    """Create a webhook configuration dictionary"""
    config = {
        'name': name,
        'type': webhook_type,
        'url': url,
        'enabled': kwargs.get('enabled', True),
        'timeout': kwargs.get('timeout', 30),
        'retry_count': kwargs.get('retry_count', 3),
        'retry_delay': kwargs.get('retry_delay', 5),
        'headers': kwargs.get('headers', {})
    }
    
    # Validate the configuration
    errors = validate_webhook_config(config)
    if errors:
        raise ValueError(f"Invalid webhook configuration: {', '.join(errors)}")
    
    return config

def get_alert_templates():
    """Get all available alert templates"""
    return ALERT_TEMPLATES.copy()

def add_alert_template(name, title, message, severity='info', fields=None):
    """Add a custom alert template"""
    if severity not in SEVERITY_LEVELS:
        raise ValueError(f"Invalid severity level: {severity}")
    
    ALERT_TEMPLATES[name] = {
        'title': title,
        'message': message,
        'severity': severity,
        'fields': fields or []
    }

def get_severity_info(severity):
    """Get information about a severity level"""
    return SEVERITY_LEVELS.get(severity.lower(), {})

def get_platform_info(platform):
    """Get information about a webhook platform"""
    return WEBHOOK_PLATFORMS.get(platform.lower(), {})

def get_supported_platforms():
    """Get list of supported webhook platforms"""
    return list(WEBHOOK_PLATFORMS.keys())

# Alert formatting utilities
def truncate_message(message, platform='generic', max_length=None):
    """Truncate message based on platform limits"""
    if max_length is None:
        platform_info = get_platform_info(platform)
        max_length = platform_info.get('max_message_length', 2000)
    
    if len(message) <= max_length:
        return message
    
    # Truncate and add ellipsis
    return message[:max_length-3] + '...'

def sanitize_message(message, platform='generic'):
    """Sanitize message for specific platform"""
    # Remove or escape platform-specific characters
    if platform == 'slack':
        # Escape Slack formatting characters
        message = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    elif platform == 'discord':
        # Escape Discord markdown
        message = message.replace('`', '\\`').replace('*', '\\*').replace('_', '\\_')
    
    return message

def add_emoji_to_message(message, severity):
    """Add appropriate emoji to message based on severity"""
    severity_info = get_severity_info(severity)
    emoji = severity_info.get('emoji', '')
    
    if emoji and not message.startswith(emoji):
        return f"{emoji} {message}"
    
    return message

# Alert history and analytics utilities
class AlertAnalytics:
    """Utility class for alert analytics"""
    
    @staticmethod
    def analyze_alert_history(alerts, hours=24):
        """Analyze alert history over specified period"""
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in alerts if a.timestamp >= cutoff_time]
        
        if not recent_alerts:
            return {
                'total_alerts': 0,
                'period_hours': hours,
                'alert_rate': 0.0
            }
        
        # Count by severity
        severity_counts = defaultdict(int)
        service_counts = defaultdict(int)
        hourly_counts = defaultdict(int)
        
        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1
            if alert.service:
                service_counts[alert.service] += 1
            
            # Group by hour
            hour_key = alert.timestamp.strftime('%Y-%m-%d %H:00')
            hourly_counts[hour_key] += 1
        
        return {
            'total_alerts': len(recent_alerts),
            'period_hours': hours,
            'alert_rate': len(recent_alerts) / hours,
            'severity_breakdown': dict(severity_counts),
            'service_breakdown': dict(service_counts),
            'hourly_distribution': dict(hourly_counts),
            'peak_hour': max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None
        }
    
    @staticmethod
    def get_alert_trends(alerts, days=7):
        """Get alert trends over specified days"""
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        cutoff_time = datetime.now() - timedelta(days=days)
        alerts_in_period = [a for a in alerts if a.timestamp >= cutoff_time]
        
        daily_counts = defaultdict(int)
        severity_trends = defaultdict(lambda: defaultdict(int))
        
        for alert in alerts_in_period:
            day_key = alert.timestamp.strftime('%Y-%m-%d')
            daily_counts[day_key] += 1
            severity_trends[day_key][alert.severity.value] += 1
        
        # Calculate trend direction
        if len(daily_counts) >= 2:
            sorted_days = sorted(daily_counts.keys())
            recent_avg = sum(daily_counts[day] for day in sorted_days[-3:]) / min(3, len(sorted_days))
            earlier_avg = sum(daily_counts[day] for day in sorted_days[:-3]) / max(1, len(sorted_days) - 3)
            
            if recent_avg > earlier_avg * 1.2:
                trend = 'increasing'
            elif recent_avg < earlier_avg * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'period_days': days,
            'daily_counts': dict(daily_counts),
            'severity_trends': dict(severity_trends),
            'overall_trend': trend,
            'avg_alerts_per_day': len(alerts_in_period) / days
        }

# Configuration helpers
def get_default_alert_config():
    """Get default alert management configuration"""
    return {
        'webhooks': [],
        'alert_settings': {
            'cooldown_minutes': 10,
            'max_alerts_per_hour': 100,
            'rate_limit_window_minutes': 1,
            'max_requests_per_window': 10
        },
        'formatting': {
            'include_timestamp': True,
            'include_service_info': True,
            'include_system_info': True,
            'truncate_long_messages': True,
            'add_emoji': True
        }
    }

def merge_alert_configs(base_config, override_config):
    """Merge two alert configurations"""
    import copy
    
    merged = copy.deepcopy(base_config)
    
    if not override_config:
        return merged
    
    # Merge webhooks
    if 'webhooks' in override_config:
        existing_names = {w['name'] for w in merged.get('webhooks', [])}
        for webhook in override_config['webhooks']:
            if webhook['name'] not in existing_names:
                merged.setdefault('webhooks', []).append(webhook)
    
    # Merge other settings
    for key, value in override_config.items():
        if key == 'webhooks':
            continue
        elif isinstance(value, dict) and key in merged:
            merged[key].update(value)
        else:
            merged[key] = value
    
    return merged

# Alert scheduling and batching
class AlertBatcher:
    """Utility for batching alerts to reduce noise"""
    
    def __init__(self, batch_window_seconds=60, max_batch_size=10):
        self.batch_window = batch_window_seconds
        self.max_batch_size = max_batch_size
        self.pending_alerts = []
        self.last_flush_time = None
    
    def add_alert(self, alert_data):
        """Add alert to batch"""
        from datetime import datetime
        
        self.pending_alerts.append({
            'alert': alert_data,
            'timestamp': datetime.now()
        })
        
        # Check if we should flush
        if (len(self.pending_alerts) >= self.max_batch_size or 
            self._should_flush()):
            return self.flush()
        
        return None
    
    def _should_flush(self):
        """Check if batch should be flushed"""
        from datetime import datetime, timedelta
        
        if not self.pending_alerts:
            return False
        
        oldest_alert = min(self.pending_alerts, key=lambda x: x['timestamp'])
        return datetime.now() - oldest_alert['timestamp'] >= timedelta(seconds=self.batch_window)
    
    def flush(self):
        """Flush pending alerts and return batch"""
        if not self.pending_alerts:
            return None
        
        batch = self.pending_alerts.copy()
        self.pending_alerts.clear()
        
        from datetime import datetime
        self.last_flush_time = datetime.now()
        
        return batch

# Module information
MODULE_INFO = {
    'name': 'alerts',
    'version': __version__,
    'description': __description__,
    'supported_platforms': list(WEBHOOK_PLATFORMS.keys()),
    'severity_levels': list(SEVERITY_LEVELS.keys()),
    'alert_templates': list(ALERT_TEMPLATES.keys()),
    'features': [
        'Multi-platform webhook delivery',
        'Smart rate limiting and cooldowns',
        'Rich message formatting',
        'Alert templating system',
        'Retry logic with exponential backoff',
        'Alert analytics and trends',
        'Batch processing for noise reduction'
    ]
}

def get_module_info():
    """Get module information"""
    return MODULE_INFO.copy()

# Add utility classes and functions to exports
__all__.extend([
    'SEVERITY_LEVELS',
    'WEBHOOK_PLATFORMS', 
    'ALERT_TEMPLATES',
    'AlertAnalytics',
    'AlertBatcher',
    'add_alert_template',
    'get_severity_info',
    'get_platform_info',
    'get_supported_platforms',
    'truncate_message',
    'sanitize_message',
    'add_emoji_to_message',
    'get_default_alert_config',
    'merge_alert_configs',
    'get_module_info'
])

# Package initialization for alerts module
def _initialize_alerts_module():
    """Initialize the alerts module"""
    import logging
    import os
    
    logger = logging.getLogger(__name__)
    
    # Load alert configuration from environment
    webhook_urls = {
        'slack': os.getenv('SLACK_WEBHOOK_URL'),
        'discord': os.getenv('DISCORD_WEBHOOK_URL'),
        'teams': os.getenv('TEAMS_WEBHOOK_URL')
    }
    
    configured_webhooks = [
        platform for platform, url in webhook_urls.items() 
        if url and url.strip()
    ]
    
    if configured_webhooks:
        logger.info(f"Alert webhooks configured for: {', '.join(configured_webhooks)}")
    else:
        logger.warning("No webhook URLs configured - alerts will not be delivered")
    
    logger.debug(f"Alerts module initialized (version {__version__})")

# Initialize when module is imported
_initialize_alerts_module()