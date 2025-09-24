#!/usr/bin/env python3
"""
Webhook Alert Manager for AI Content Factory
ใช้สำหรับส่งการแจ้งเตือนผ่าน webhooks ไปยัง Slack, Discord, Teams, และระบบอื่นๆ
"""

import os
import sys
import asyncio
import aiohttp
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.utils.logger import setup_logger
from shared.utils.error_handler import ErrorHandler

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class WebhookType(Enum):
    """Supported webhook types"""
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    GENERIC = "generic"
    EMAIL = "email"

@dataclass
class AlertData:
    """Alert data structure"""
    title: str
    message: str
    severity: AlertSeverity
    service: str = None
    data: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}

@dataclass
class WebhookConfig:
    """Webhook configuration"""
    name: str
    type: WebhookType
    url: str
    enabled: bool = True
    headers: Dict[str, str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 5
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

class WebhookAlertManager:
    """Main webhook alert management class"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = setup_logger("webhook_alerts")
        self.error_handler = ErrorHandler()
        self.config = config or self._load_default_config()
        
        # Initialize webhooks
        self.webhooks: List[WebhookConfig] = []
        self._load_webhooks()
        
        # Alert management
        self.alert_history = []
        self.cooldown_cache = defaultdict(dict)  # Track cooldowns per webhook/alert type
        
        # Rate limiting
        self.rate_limits = defaultdict(list)  # Track request timestamps per webhook
        
        self.logger.info("Webhook Alert Manager initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'webhooks': [
                {
                    'name': 'slack_alerts',
                    'type': 'slack',
                    'url': os.getenv('SLACK_WEBHOOK_URL', ''),
                    'enabled': bool(os.getenv('SLACK_WEBHOOK_URL')),
                    'timeout': 30,
                    'retry_count': 3
                },
                {
                    'name': 'discord_alerts',
                    'type': 'discord',
                    'url': os.getenv('DISCORD_WEBHOOK_URL', ''),
                    'enabled': bool(os.getenv('DISCORD_WEBHOOK_URL')),
                    'timeout': 30,
                    'retry_count': 3
                }
            ],
            'alert_settings': {
                'cooldown_minutes': 10,
                'max_alerts_per_hour': 100,
                'rate_limit_window_minutes': 1,
                'max_requests_per_window': 10
            },
            'formatting': {
                'include_timestamp': True,
                'include_service_info': True,
                'include_system_info': True
            }
        }
    
    def _load_webhooks(self):
        """Load webhook configurations"""
        for webhook_config in self.config.get('webhooks', []):
            if webhook_config.get('url') and webhook_config.get('enabled', True):
                webhook = WebhookConfig(
                    name=webhook_config['name'],
                    type=WebhookType(webhook_config['type']),
                    url=webhook_config['url'],
                    enabled=webhook_config.get('enabled', True),
                    headers=webhook_config.get('headers', {}),
                    timeout=webhook_config.get('timeout', 30),
                    retry_count=webhook_config.get('retry_count', 3),
                    retry_delay=webhook_config.get('retry_delay', 5)
                )
                self.webhooks.append(webhook)
                self.logger.info(f"Loaded webhook: {webhook.name} ({webhook.type.value})")
    
    def add_webhook(self, webhook: WebhookConfig):
        """Add a new webhook configuration"""
        self.webhooks.append(webhook)
        self.logger.info(f"Added webhook: {webhook.name}")
    
    def remove_webhook(self, webhook_name: str):
        """Remove a webhook by name"""
        self.webhooks = [w for w in self.webhooks if w.name != webhook_name]
        self.logger.info(f"Removed webhook: {webhook_name}")
    
    def _check_cooldown(self, webhook_name: str, alert_key: str) -> bool:
        """Check if alert is in cooldown period"""
        cooldown_minutes = self.config['alert_settings']['cooldown_minutes']
        
        if webhook_name in self.cooldown_cache and alert_key in self.cooldown_cache[webhook_name]:
            last_sent = self.cooldown_cache[webhook_name][alert_key]
            cooldown_until = last_sent + timedelta(minutes=cooldown_minutes)
            
            if datetime.now() < cooldown_until:
                return True
        
        return False
    
    def _update_cooldown(self, webhook_name: str, alert_key: str):
        """Update cooldown timestamp for alert"""
        self.cooldown_cache[webhook_name][alert_key] = datetime.now()
    
    def _check_rate_limit(self, webhook_name: str) -> bool:
        """Check if webhook is rate limited"""
        settings = self.config['alert_settings']
        window_minutes = settings['rate_limit_window_minutes']
        max_requests = settings['max_requests_per_window']
        
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=window_minutes)
        
        # Clean old timestamps
        self.rate_limits[webhook_name] = [
            ts for ts in self.rate_limits[webhook_name] if ts > cutoff_time
        ]
        
        # Check if we're over the limit
        if len(self.rate_limits[webhook_name]) >= max_requests:
            return True
        
        # Add current timestamp
        self.rate_limits[webhook_name].append(now)
        return False
    
    def _generate_alert_key(self, alert: AlertData) -> str:
        """Generate unique key for alert deduplication"""
        key_data = f"{alert.service}:{alert.title}:{alert.severity.value}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _format_slack_payload(self, alert: AlertData) -> Dict[str, Any]:
        """Format alert for Slack webhook"""
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9500",
            AlertSeverity.CRITICAL: "#ff0000"
        }
        
        emoji_map = {
            AlertSeverity.INFO: ":information_source:",
            AlertSeverity.WARNING: ":warning:",
            AlertSeverity.CRITICAL: ":rotating_light:"
        }
        
        fields = []
        
        if alert.service:
            fields.append({
                "title": "Service",
                "value": alert.service,
                "short": True
            })
        
        fields.append({
            "title": "Severity",
            "value": alert.severity.value.upper(),
            "short": True
        })
        
        if self.config['formatting']['include_timestamp']:
            fields.append({
                "title": "Time",
                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "short": True
            })
        
        # Add additional data fields
        if alert.data:
            for key, value in alert.data.items():
                if isinstance(value, (str, int, float, bool)):
                    fields.append({
                        "title": key.replace("_", " ").title(),
                        "value": str(value),
                        "short": True
                    })
        
        attachment = {
            "color": color_map.get(alert.severity, "#808080"),
            "title": f"{emoji_map.get(alert.severity, '')} {alert.title}",
            "text": alert.message,
            "fields": fields,
            "footer": "AI Content Factory Monitoring",
            "ts": int(alert.timestamp.timestamp())
        }
        
        return {
            "attachments": [attachment]
        }
    
    def _format_discord_payload(self, alert: AlertData) -> Dict[str, Any]:
        """Format alert for Discord webhook"""
        color_map = {
            AlertSeverity.INFO: 0x36a64f,
            AlertSeverity.WARNING: 0xff9500,
            AlertSeverity.CRITICAL: 0xff0000
        }
        
        embed = {
            "title": alert.title,
            "description": alert.message,
            "color": color_map.get(alert.severity, 0x808080),
            "timestamp": alert.timestamp.isoformat(),
            "footer": {
                "text": "AI Content Factory Monitoring"
            },
            "fields": []
        }
        
        if alert.service:
            embed["fields"].append({
                "name": "Service",
                "value": alert.service,
                "inline": True
            })
        
        embed["fields"].append({
            "name": "Severity",
            "value": alert.severity.value.upper(),
            "inline": True
        })
        
        # Add additional data fields
        if alert.data:
            for key, value in alert.data.items():
                if isinstance(value, (str, int, float, bool)) and len(embed["fields"]) < 25:
                    embed["fields"].append({
                        "name": key.replace("_", " ").title(),
                        "value": str(value),
                        "inline": True
                    })
        
        return {
            "embeds": [embed]
        }
    
    def _format_teams_payload(self, alert: AlertData) -> Dict[str, Any]:
        """Format alert for Microsoft Teams webhook"""
        color_map = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.CRITICAL: "attention"
        }
        
        facts = []
        
        if alert.service:
            facts.append({
                "name": "Service",
                "value": alert.service
            })
        
        facts.append({
            "name": "Severity",
            "value": alert.severity.value.upper()
        })
        
        facts.append({
            "name": "Time",
            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        })
        
        # Add additional data
        if alert.data:
            for key, value in alert.data.items():
                if isinstance(value, (str, int, float, bool)):
                    facts.append({
                        "name": key.replace("_", " ").title(),
                        "value": str(value)
                    })
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color_map.get(alert.severity, "default"),
            "summary": alert.title,
            "sections": [{
                "activityTitle": alert.title,
                "activitySubtitle": "AI Content Factory Monitoring",
                "text": alert.message,
                "facts": facts
            }]
        }
    
    def _format_generic_payload(self, alert: AlertData) -> Dict[str, Any]:
        """Format alert for generic webhook"""
        return {
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity.value,
            "service": alert.service,
            "timestamp": alert.timestamp.isoformat(),
            "data": alert.data
        }
    
    def _format_payload(self, webhook: WebhookConfig, alert: AlertData) -> Dict[str, Any]:
        """Format payload based on webhook type"""
        if webhook.type == WebhookType.SLACK:
            return self._format_slack_payload(alert)
        elif webhook.type == WebhookType.DISCORD:
            return self._format_discord_payload(alert)
        elif webhook.type == WebhookType.TEAMS:
            return self._format_teams_payload(alert)
        else:
            return self._format_generic_payload(alert)
    
    async def _send_webhook(self, webhook: WebhookConfig, payload: Dict[str, Any]) -> bool:
        """Send webhook with retry logic"""
        headers = {
            "Content-Type": "application/json",
            **webhook.headers
        }
        
        for attempt in range(webhook.retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=webhook.timeout)
                    ) as response:
                        if response.status < 400:
                            self.logger.debug(f"Webhook sent successfully: {webhook.name}")
                            return True
                        else:
                            self.logger.warning(f"Webhook failed: {webhook.name}, status: {response.status}")
                            if attempt < webhook.retry_count - 1:
                                await asyncio.sleep(webhook.retry_delay)
                            
            except asyncio.TimeoutError:
                self.logger.error(f"Webhook timeout: {webhook.name}")
                if attempt < webhook.retry_count - 1:
                    await asyncio.sleep(webhook.retry_delay)
            except Exception as e:
                self.logger.error(f"Webhook error: {webhook.name}, error: {str(e)}")
                if attempt < webhook.retry_count - 1:
                    await asyncio.sleep(webhook.retry_delay)
        
        return False
    
    async def send_alert(self, 
                        title: str, 
                        message: str, 
                        severity: str = "info",
                        service: str = None,
                        data: Dict[str, Any] = None) -> Dict[str, bool]:
        """Send alert to all configured webhooks"""
        alert = AlertData(
            title=title,
            message=message,
            severity=AlertSeverity(severity.lower()),
            service=service,
            data=data or {}
        )
        
        # Store in history
        self.alert_history.append(alert)
        
        # Keep only recent alerts (last 1000)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        results = {}
        alert_key = self._generate_alert_key(alert)
        
        for webhook in self.webhooks:
            if not webhook.enabled:
                continue
            
            # Check cooldown
            if self._check_cooldown(webhook.name, alert_key):
                self.logger.debug(f"Alert in cooldown for webhook: {webhook.name}")
                results[webhook.name] = False
                continue
            
            # Check rate limit
            if self._check_rate_limit(webhook.name):
                self.logger.warning(f"Rate limit exceeded for webhook: {webhook.name}")
                results[webhook.name] = False
                continue
            
            # Format and send
            try:
                payload = self._format_payload(webhook, alert)
                success = await self._send_webhook(webhook, payload)
                results[webhook.name] = success
                
                if success:
                    self._update_cooldown(webhook.name, alert_key)
                
            except Exception as e:
                self.logger.error(f"Failed to send alert via {webhook.name}: {str(e)}")
                results[webhook.name] = False
        
        self.logger.info(f"Alert sent: {title} (severity: {severity}) - Results: {results}")
        return results
    
    async def send_test_alert(self, webhook_name: str = None) -> Dict[str, bool]:
        """Send test alert to verify webhook configuration"""
        test_alert = AlertData(
            title="Test Alert",
            message="This is a test alert from AI Content Factory monitoring system.",
            severity=AlertSeverity.INFO,
            service="monitoring",
            data={
                "test": True,
                "system": "AI Content Factory",
                "component": "Webhook Alert Manager"
            }
        )
        
        results = {}
        
        webhooks_to_test = self.webhooks
        if webhook_name:
            webhooks_to_test = [w for w in self.webhooks if w.name == webhook_name]
        
        for webhook in webhooks_to_test:
            if not webhook.enabled:
                continue
            
            try:
                payload = self._format_payload(webhook, test_alert)
                success = await self._send_webhook(webhook, payload)
                results[webhook.name] = success
            except Exception as e:
                self.logger.error(f"Test alert failed for {webhook.name}: {str(e)}")
                results[webhook.name] = False
        
        return results
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        recent_alerts = [a for a in self.alert_history if a.timestamp >= last_hour]
        daily_alerts = [a for a in self.alert_history if a.timestamp >= last_day]
        
        severity_counts = defaultdict(int)
        service_counts = defaultdict(int)
        
        for alert in daily_alerts:
            severity_counts[alert.severity.value] += 1
            if alert.service:
                service_counts[alert.service] += 1
        
        return {
            "total_alerts_24h": len(daily_alerts),
            "alerts_last_hour": len(recent_alerts),
            "severity_breakdown_24h": dict(severity_counts),
            "service_breakdown_24h": dict(service_counts),
            "configured_webhooks": len(self.webhooks),
            "enabled_webhooks": len([w for w in self.webhooks if w.enabled]),
            "last_alert": self.alert_history[-1].timestamp.isoformat() if self.alert_history else None
        }
    
    def get_webhook_status(self) -> List[Dict[str, Any]]:
        """Get status of all configured webhooks"""
        status_list = []
        
        for webhook in self.webhooks:
            # Check recent rate limit status
            recent_requests = len(self.rate_limits.get(webhook.name, []))
            
            status_list.append({
                "name": webhook.name,
                "type": webhook.type.value,
                "enabled": webhook.enabled,
                "recent_requests": recent_requests,
                "rate_limited": self._check_rate_limit(webhook.name),
                "url_configured": bool(webhook.url),
                "timeout": webhook.timeout,
                "retry_count": webhook.retry_count
            })
        
        return status_list
    
    def clear_cooldowns(self):
        """Clear all cooldown timers"""
        self.cooldown_cache.clear()
        self.logger.info("All cooldowns cleared")
    
    def clear_rate_limits(self):
        """Clear all rate limit counters"""
        self.rate_limits.clear()
        self.logger.info("All rate limits cleared")

# Utility functions for easy alert sending

async def send_critical_alert(title: str, message: str, service: str = None, data: Dict[str, Any] = None):
    """Send critical alert - convenience function"""
    manager = WebhookAlertManager()
    return await manager.send_alert(title, message, "critical", service, data)

async def send_warning_alert(title: str, message: str, service: str = None, data: Dict[str, Any] = None):
    """Send warning alert - convenience function"""
    manager = WebhookAlertManager()
    return await manager.send_alert(title, message, "warning", service, data)

async def send_info_alert(title: str, message: str, service: str = None, data: Dict[str, Any] = None):
    """Send info alert - convenience function"""
    manager = WebhookAlertManager()
    return await manager.send_alert(title, message, "info", service, data)

# Example usage and CLI
async def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Webhook Alert Manager")
    parser.add_argument('action', choices=['test', 'send', 'status', 'stats'], 
                       help='Action to perform')
    parser.add_argument('--webhook', '-w', help='Specific webhook name')
    parser.add_argument('--title', '-t', help='Alert title')
    parser.add_argument('--message', '-m', help='Alert message')
    parser.add_argument('--severity', '-s', choices=['info', 'warning', 'critical'], 
                       default='info', help='Alert severity')
    parser.add_argument('--service', help='Service name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger("webhook_alert_main", level=log_level)
    
    # Initialize alert manager
    alert_manager = WebhookAlertManager()
    
    if args.action == 'test':
        logger.info("Sending test alerts...")
        results = await alert_manager.send_test_alert(args.webhook)
        print(f"Test results: {json.dumps(results, indent=2)}")
    
    elif args.action == 'send':
        if not args.title or not args.message:
            logger.error("Title and message are required for sending alerts")
            return
        
        logger.info(f"Sending {args.severity} alert: {args.title}")
        results = await alert_manager.send_alert(
            title=args.title,
            message=args.message,
            severity=args.severity,
            service=args.service
        )
        print(f"Send results: {json.dumps(results, indent=2)}")
    
    elif args.action == 'status':
        status = alert_manager.get_webhook_status()
        print(f"Webhook Status:\n{json.dumps(status, indent=2)}")
    
    elif args.action == 'stats':
        stats = alert_manager.get_alert_statistics()
        print(f"Alert Statistics:\n{json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())