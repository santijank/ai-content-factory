import asyncio
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from collections import defaultdict
import threading
import time

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

@dataclass
class AlertRule:
    name: str
    metric_name: str
    condition: str  # "greater_than", "less_than", "equals", "not_equals"
    threshold: float
    severity: AlertSeverity
    duration: int = 60  # seconds - how long condition must persist
    description: str = ""
    enabled: bool = True

@dataclass
class Alert:
    id: str
    rule_name: str
    metric_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    current_value: float
    threshold: float
    first_triggered: datetime
    last_triggered: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class NotificationChannel:
    name: str
    type: str  # "email", "slack", "webhook", "sms"
    config: Dict[str, Any]
    enabled: bool = True

class AlertManager:
    """Comprehensive alert management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = []
        self.notification_channels = {}
        
        # Alert state tracking
        self.metric_states = defaultdict(list)  # Track metric values over time
        self.rule_timers = {}  # Track how long conditions have been true
        
        # Threading
        self.is_running = False
        self.evaluation_thread = None
        self.evaluation_interval = config.get('evaluation_interval', 30)  # seconds
        
        # Load default rules and channels
        self._load_default_rules()
        self._load_notification_channels()
        
        logger.info("AlertManager initialized")

    def _load_default_rules(self):
        """Load default alerting rules"""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                metric_name="system.cpu.usage",
                condition="greater_than",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                duration=120,
                description="CPU usage is consistently high"
            ),
            AlertRule(
                name="critical_cpu_usage", 
                metric_name="system.cpu.usage",
                condition="greater_than",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration=60,
                description="CPU usage is critically high"
            ),
            AlertRule(
                name="high_memory_usage",
                metric_name="system.memory.usage",
                condition="greater_than",
                threshold=90.0,
                severity=AlertSeverity.WARNING,
                duration=120,
                description="Memory usage is consistently high"
            ),
            AlertRule(
                name="critical_memory_usage",
                metric_name="system.memory.usage", 
                condition="greater_than",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration=60,
                description="Memory usage is critically high"
            ),
            AlertRule(
                name="high_disk_usage",
                metric_name="system.disk.usage",
                condition="greater_than",
                threshold=90.0,
                severity=AlertSeverity.WARNING,
                duration=300,
                description="Disk usage is high"
            ),
            AlertRule(
                name="service_down",
                metric_name="service.*.health",
                condition="equals",
                threshold=0.0,
                severity=AlertSeverity.CRITICAL,
                duration=30,
                description="Service is down"
            ),
            AlertRule(
                name="high_error_rate",
                metric_name="app.*.error_rate",
                condition="greater_than",
                threshold=10.0,
                severity=AlertSeverity.WARNING,
                duration=180,
                description="High error rate detected"
            ),
            AlertRule(
                name="slow_response_time",
                metric_name="service.*.response_time",
                condition="greater_than",
                threshold=2000.0,  # 2 seconds
                severity=AlertSeverity.WARNING,
                duration=300,
                description="Service response time is slow"
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule

    def _load_notification_channels(self):
        """Load notification channels from config"""
        channels_config = self.config.get('notification_channels', {})
        
        # Email channel
        if 'email' in channels_config:
            self.notification_channels['email'] = NotificationChannel(
                name="email",
                type="email",
                config=channels_config['email']
            )
        
        # Slack channel
        if 'slack' in channels_config:
            self.notification_channels['slack'] = NotificationChannel(
                name="slack",
                type="slack", 
                config=channels_config['slack']
            )
        
        # Webhook channel
        if 'webhook' in channels_config:
            self.notification_channels['webhook'] = NotificationChannel(
                name="webhook",
                type="webhook",
                config=channels_config['webhook']
            )

    def start_monitoring(self):
        """Start alert monitoring"""
        if not self.is_running:
            self.is_running = True
            self.evaluation_thread = threading.Thread(target=self._evaluation_loop, daemon=True)
            self.evaluation_thread.start()
            logger.info("Alert monitoring started")

    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.is_running = False
        if self.evaluation_thread:
            self.evaluation_thread.join(timeout=5)
        logger.info("Alert monitoring stopped")

    def _evaluation_loop(self):
        """Main alert evaluation loop"""
        while self.is_running:
            try:
                self._evaluate_all_rules()
                time.sleep(self.evaluation_interval)
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                time.sleep(10)

    def add_metric_value(self, metric_name: str, value: float, timestamp: datetime = None):
        """Add metric value for alert evaluation"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Store metric value with timestamp
        self.metric_states[metric_name].append((timestamp, value))
        
        # Keep only recent values (last 1 hour)
        cutoff_time = timestamp - timedelta(hours=1)
        self.metric_states[metric_name] = [
            (ts, val) for ts, val in self.metric_states[metric_name] 
            if ts >= cutoff_time
        ]

    def _evaluate_all_rules(self):
        """Evaluate all alert rules"""
        current_time = datetime.now()
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
                
            try:
                self._evaluate_rule(rule, current_time)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_name}: {e}")

    def _evaluate_rule(self, rule: AlertRule, current_time: datetime):
        """Evaluate a single alert rule"""
        # Handle wildcard metric names
        if '*' in rule.metric_name:
            metric_names = self._find_matching_metrics(rule.metric_name)
        else:
            metric_names = [rule.metric_name]
        
        for metric_name in metric_names:
            self._evaluate_rule_for_metric(rule, metric_name, current_time)

    def _find_matching_metrics(self, pattern: str) -> List[str]:
        """Find metric names matching a pattern"""
        matching = []
        pattern_parts = pattern.split('*')
        
        for metric_name in self.metric_states.keys():
            matches = True
            pos = 0
            
            for i, part in enumerate(pattern_parts):
                if i == 0:  # First part must match from beginning
                    if not metric_name.startswith(part):
                        matches = False
                        break
                    pos = len(part)
                elif i == len(pattern_parts) - 1:  # Last part must match to end
                    if not metric_name[pos:].endswith(part):
                        matches = False
                        break
                else:  # Middle parts must exist somewhere
                    next_pos = metric_name.find(part, pos)
                    if next_pos == -1:
                        matches = False
                        break
                    pos = next_pos + len(part)
            
            if matches:
                matching.append(metric_name)
        
        return matching

    def _evaluate_rule_for_metric(self, rule: AlertRule, metric_name: str, current_time: datetime):
        """Evaluate rule for a specific metric"""
        metric_values = self.metric_states.get(metric_name, [])
        
        if not metric_values:
            return
        
        # Get latest value
        latest_timestamp, latest_value = metric_values[-1]
        
        # Check if condition is met
        condition_met = self._check_condition(rule, latest_value)
        
        rule_key = f"{rule.name}:{metric_name}"
        
        if condition_met:
            # Start or update timer
            if rule_key not in self.rule_timers:
                self.rule_timers[rule_key] = current_time
            
            # Check if condition has persisted long enough
            time_since_start = (current_time - self.rule_timers[rule_key]).total_seconds()
            
            if time_since_start >= rule.duration:
                # Trigger alert if not already active
                alert_id = f"{rule.name}:{metric_name}"
                
                if alert_id not in self.active_alerts:
                    self._trigger_alert(rule, metric_name, latest_value, current_time)
                else:
                    # Update existing alert
                    self.active_alerts[alert_id].last_triggered = current_time
                    self.active_alerts[alert_id].current_value = latest_value
        else:
            # Condition no longer met
            if rule_key in self.rule_timers:
                del self.rule_timers[rule_key]
            
            # Resolve alert if active
            alert_id = f"{rule.name}:{metric_name}"
            if alert_id in self.active_alerts:
                self._resolve_alert(alert_id, current_time)

    def _check_condition(self, rule: AlertRule, value: float) -> bool:
        """Check if alert condition is met"""
        if rule.condition == "greater_than":
            return value > rule.threshold
        elif rule.condition == "less_than":
            return value < rule.threshold
        elif rule.condition == "equals":
            return abs(value - rule.threshold) < 0.001  # Float comparison
        elif rule.condition == "not_equals":
            return abs(value - rule.threshold) >= 0.001
        else:
            logger.warning(f"Unknown condition: {rule.condition}")
            return False

    def _trigger_alert(self, rule: AlertRule, metric_name: str, value: float, timestamp: datetime):
        """Trigger a new alert"""
        alert_id = f"{rule.name}:{metric_name}"
        
        # Create alert
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            metric_name=metric_name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=self._generate_alert_message(rule, metric_name, value),
            current_value=value,
            threshold=rule.threshold,
            first_triggered=timestamp,
            last_triggered=timestamp,
            metadata={"rule_description": rule.description}
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        asyncio.create_task(self._send_alert_notifications(alert))
        
        logger.info(f"Alert triggered: {alert_id} - {alert.message}")

    def _resolve_alert(self, alert_id: str, timestamp: datetime):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = timestamp
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            # Send resolution notification
            asyncio.create_task(self._send_resolution_notification(alert))
            
            logger.info(f"Alert resolved: {alert_id}")

    def _generate_alert_message(self, rule: AlertRule, metric_name: str, value: float) -> str:
        """Generate human-readable alert message"""
        if "cpu.usage" in metric_name:
            return f"CPU usage is {value:.1f}% (threshold: {rule.threshold:.1f}%)"
        elif "memory.usage" in metric_name:
            return f"Memory usage is {value:.1f}% (threshold: {rule.threshold:.1f}%)"
        elif "disk.usage" in metric_name:
            return f"Disk usage is {value:.1f}% (threshold: {rule.threshold:.1f}%)"
        elif "service" in metric_name and "health" in metric_name:
            service = metric_name.split('.')[1]
            return f"Service {service} is down"
        elif "error_rate" in metric_name:
            service = metric_name.split('.')[1]
            return f"High error rate for {service}: {value:.1f}% (threshold: {rule.threshold:.1f}%)"
        elif "response_time" in metric_name:
            service = metric_name.split('.')[1]
            return f"Slow response time for {service}: {value:.1f}ms (threshold: {rule.threshold:.1f}ms)"
        else:
            return f"{rule.description}: {metric_name} = {value} (threshold: {rule.threshold})"

    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications through all enabled channels"""
        try:
            # Determine which channels to use based on severity
            channels_to_use = []
            
            if alert.severity == AlertSeverity.CRITICAL:
                channels_to_use = list(self.notification_channels.keys())
            elif alert.severity == AlertSeverity.WARNING:
                channels_to_use = ['email', 'slack']  # Skip SMS for warnings
            else:
                channels_to_use = ['email']  # Only email for info
            
            # Send notifications
            for channel_name in channels_to_use:
                if channel_name in self.notification_channels:
                    channel = self.notification_channels[channel_name]
                    if channel.enabled:
                        await self._send_notification(channel, alert)
                        
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")

    async def _send_resolution_notification(self, alert: Alert):
        """Send alert resolution notification"""
        try:
            # Only send resolution notifications for critical alerts
            if alert.severity == AlertSeverity.CRITICAL:
                for channel_name, channel in self.notification_channels.items():
                    if channel.enabled:
                        await self._send_resolution_notification_to_channel(channel, alert)
                        
        except Exception as e:
            logger.error(f"Error sending resolution notifications: {e}")

    async def _send_notification(self, channel: NotificationChannel, alert: Alert):
        """Send notification to a specific channel"""
        try:
            if channel.type == "email":
                await self._send_email_notification(channel, alert)
            elif channel.type == "slack":
                await self._send_slack_notification(channel, alert)
            elif channel.type == "webhook":
                await self._send_webhook_notification(channel, alert)
            else:
                logger.warning(f"Unknown notification channel type: {channel.type}")
                
        except Exception as e:
            logger.error(f"Error sending notification to {channel.name}: {e}")

    async def _send_email_notification(self, channel: NotificationChannel, alert: Alert):
        """Send email notification"""
        config = channel.config
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = config.get('from_email', 'alerts@aicontentfactory.com')
        msg['To'] = ', '.join(config.get('to_emails', []))
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.message}"
        
        # Email body
        body = f"""
        Alert Details:
        
        Alert ID: {alert.id}
        Severity: {alert.severity.value.upper()}
        Metric: {alert.metric_name}
        Current Value: {alert.current_value}
        Threshold: {alert.threshold}
        First Triggered: {alert.first_triggered.strftime('%Y-%m-%d %H:%M:%S')}
        Last Triggered: {alert.last_triggered.strftime('%Y-%m-%d %H:%M:%S')}
        
        Description: {alert.metadata.get('rule_description', 'No description available')}
        
        Please investigate and take appropriate action.
        
        ---
        AI Content Factory Monitoring System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        try:
            with smtplib.SMTP(config.get('smtp_server', 'localhost'), config.get('smtp_port', 587)) as server:
                if config.get('use_tls', True):
                    server.starttls()
                if config.get('username') and config.get('password'):
                    server.login(config['username'], config['password'])
                server.send_message(msg)
                
            logger.info(f"Email notification sent for alert {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    async def _send_slack_notification(self, channel: NotificationChannel, alert: Alert):
        """Send Slack notification"""
        import aiohttp
        
        config = channel.config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            logger.error("Slack webhook URL not configured")
            return
        
        # Determine color based on severity
        color_map = {
            AlertSeverity.INFO: "#36a64f",      # Green
            AlertSeverity.WARNING: "#ff9500",   # Orange
            AlertSeverity.CRITICAL: "#ff0000"   # Red
        }
        
        # Create Slack message
        slack_message = {
            "attachments": [
                {
                    "color": color_map[alert.severity],
                    "title": f"{alert.severity.value.upper()} Alert",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Metric",
                            "value": alert.metric_name,
                            "short": True
                        },
                        {
                            "title": "Current Value",
                            "value": str(alert.current_value),
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": str(alert.threshold),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.first_triggered.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": "AI Content Factory Monitoring",
                    "ts": int(alert.first_triggered.timestamp())
                }
            ]
        }
        
        # Send to Slack
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=slack_message) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert {alert.id}")
                    else:
                        logger.error(f"Failed to send Slack notification: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")

    async def _send_webhook_notification(self, channel: NotificationChannel, alert: Alert):
        """Send webhook notification"""
        import aiohttp
        
        config = channel.config
        webhook_url = config.get('url')
        
        if not webhook_url:
            logger.error("Webhook URL not configured")
            return
        
        # Create webhook payload
        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "metric_name": alert.metric_name,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "message": alert.message,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "first_triggered": alert.first_triggered.isoformat(),
            "last_triggered": alert.last_triggered.isoformat(),
            "metadata": alert.metadata
        }
        
        # Send webhook
        try:
            headers = config.get('headers', {})
            timeout = config.get('timeout', 10)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, 
                    json=payload, 
                    headers=headers, 
                    timeout=timeout
                ) as response:
                    if response.status < 400:
                        logger.info(f"Webhook notification sent for alert {alert.id}")
                    else:
                        logger.error(f"Webhook notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")

    async def _send_resolution_notification_to_channel(self, channel: NotificationChannel, alert: Alert):
        """Send resolution notification to specific channel"""
        if channel.type == "email":
            await self._send_email_resolution(channel, alert)
        elif channel.type == "slack":
            await self._send_slack_resolution(channel, alert)
        elif channel.type == "webhook":
            await self._send_webhook_resolution(channel, alert)

    async def _send_email_resolution(self, channel: NotificationChannel, alert: Alert):
        """Send email resolution notification"""
        config = channel.config
        
        msg = MIMEMultipart()
        msg['From'] = config.get('from_email', 'alerts@aicontentfactory.com')
        msg['To'] = ', '.join(config.get('to_emails', []))
        msg['Subject'] = f"[RESOLVED] {alert.message}"
        
        duration = alert.resolved_at - alert.first_triggered
        
        body = f"""
        Alert Resolved:
        
        Alert ID: {alert.id}
        Severity: {alert.severity.value.upper()}
        Metric: {alert.metric_name}
        Duration: {duration}
        Resolved At: {alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S')}
        
        The alert condition is no longer active.
        
        ---
        AI Content Factory Monitoring System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(config.get('smtp_server', 'localhost'), config.get('smtp_port', 587)) as server:
                if config.get('use_tls', True):
                    server.starttls()
                if config.get('username') and config.get('password'):
                    server.login(config['username'], config['password'])
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to send email resolution: {e}")

    async def _send_slack_resolution(self, channel: NotificationChannel, alert: Alert):
        """Send Slack resolution notification"""
        import aiohttp
        
        config = channel.config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            return
        
        duration = alert.resolved_at - alert.first_triggered
        
        slack_message = {
            "attachments": [
                {
                    "color": "#36a64f",  # Green for resolved
                    "title": "Alert Resolved",
                    "text": f"✅ {alert.message}",
                    "fields": [
                        {
                            "title": "Duration",
                            "value": str(duration),
                            "short": True
                        },
                        {
                            "title": "Resolved At",
                            "value": alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": "AI Content Factory Monitoring",
                    "ts": int(alert.resolved_at.timestamp())
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=slack_message) as response:
                    if response.status == 200:
                        logger.info(f"Slack resolution sent for alert {alert.id}")
                        
        except Exception as e:
            logger.error(f"Error sending Slack resolution: {e}")

    async def _send_webhook_resolution(self, channel: NotificationChannel, alert: Alert):
        """Send webhook resolution notification"""
        import aiohttp
        
        config = channel.config
        webhook_url = config.get('url')
        
        if not webhook_url:
            return
        
        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "metric_name": alert.metric_name,
            "severity": alert.severity.value,
            "status": "resolved",
            "message": alert.message,
            "first_triggered": alert.first_triggered.isoformat(),
            "resolved_at": alert.resolved_at.isoformat(),
            "duration_seconds": (alert.resolved_at - alert.first_triggered).total_seconds()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status < 400:
                        logger.info(f"Webhook resolution sent for alert {alert.id}")
                        
        except Exception as e:
            logger.error(f"Error sending webhook resolution: {e}")

    # Management methods
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by
            
            logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            return True
        
        return False

    def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule"""
        if rule.name in self.alert_rules:
            logger.warning(f"Alert rule {rule.name} already exists")
            return False
        
        self.alert_rules[rule.name] = rule
        logger.info(f"Alert rule added: {rule.name}")
        return True

    def remove_alert_rule(self, rule_name: str) -> bool:
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            
            # Remove any active alerts for this rule
            alerts_to_remove = [
                alert_id for alert_id in self.active_alerts
                if self.active_alerts[alert_id].rule_name == rule_name
            ]
            
            for alert_id in alerts_to_remove:
                self._resolve_alert(alert_id, datetime.now())
            
            logger.info(f"Alert rule removed: {rule_name}")
            return True
        
        return False

    def update_alert_rule(self, rule_name: str, updated_rule: AlertRule) -> bool:
        """Update an existing alert rule"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name] = updated_rule
            logger.info(f"Alert rule updated: {rule_name}")
            return True
        
        return False

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get list of active alerts"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.first_triggered, reverse=True)

    def get_alert_history(self, hours: int = 24, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get alert history for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = [
            alert for alert in self.alert_history
            if alert.first_triggered >= cutoff_time
        ]
        
        if severity:
            history = [alert for alert in history if alert.severity == severity]
        
        return sorted(history, key=lambda x: x.first_triggered, reverse=True)

    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.first_triggered >= cutoff_time
        ]
        
        # Count by severity
        severity_counts = defaultdict(int)
        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1
        
        # Count by rule
        rule_counts = defaultdict(int)
        for alert in recent_alerts:
            rule_counts[alert.rule_name] += 1
        
        # Average resolution time
        resolved_alerts = [
            alert for alert in recent_alerts
            if alert.status == AlertStatus.RESOLVED and alert.resolved_at
        ]
        
        avg_resolution_time = 0
        if resolved_alerts:
            total_time = sum(
                (alert.resolved_at - alert.first_triggered).total_seconds()
                for alert in resolved_alerts
            )
            avg_resolution_time = total_time / len(resolved_alerts)
        
        return {
            "time_period_hours": hours,
            "total_alerts": len(recent_alerts),
            "active_alerts": len(self.active_alerts),
            "severity_breakdown": dict(severity_counts),
            "top_rules": dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "average_resolution_time_seconds": avg_resolution_time,
            "resolution_rate": len(resolved_alerts) / len(recent_alerts) * 100 if recent_alerts else 0
        }

    def export_config(self) -> Dict[str, Any]:
        """Export alert manager configuration"""
        return {
            "alert_rules": {
                name: asdict(rule) for name, rule in self.alert_rules.items()
            },
            "notification_channels": {
                name: asdict(channel) for name, channel in self.notification_channels.items()
            },
            "config": self.config
        }

    def import_config(self, config_data: Dict[str, Any]):
        """Import alert manager configuration"""
        # Import alert rules
        if "alert_rules" in config_data:
            for name, rule_data in config_data["alert_rules"].items():
                rule = AlertRule(**rule_data)
                self.alert_rules[name] = rule
        
        # Import notification channels
        if "notification_channels" in config_data:
            for name, channel_data in config_data["notification_channels"].items():
                channel = NotificationChannel(**channel_data)
                self.notification_channels[name] = channel
        
        logger.info("Configuration imported successfully")

# Testing and usage example
async def test_alert_manager():
    """Test function for alert manager"""
    config = {
        'evaluation_interval': 10,
        'notification_channels': {
            'email': {
                'from_email': 'alerts@test.com',
                'to_emails': ['admin@test.com'],
                'smtp_server': 'localhost',
                'smtp_port': 587
            },
            'slack': {
                'webhook_url': 'https://hooks.slack.com/test'
            }
        }
    }
    
    alert_manager = AlertManager(config)
    alert_manager.start_monitoring()
    
    # Simulate high CPU usage
    for i in range(5):
        alert_manager.add_metric_value("system.cpu.usage", 90.0 + i)
        await asyncio.sleep(2)
    
    # Wait for alert evaluation
    await asyncio.sleep(15)
    
    # Check active alerts
    active_alerts = alert_manager.get_active_alerts()
    print(f"Active alerts: {len(active_alerts)}")
    
    for alert in active_alerts:
        print(f"Alert: {alert.message}")
        # Acknowledge alert
        alert_manager.acknowledge_alert(alert.id, "test_user")
    
    # Get statistics
    stats = alert_manager.get_alert_statistics()
    print("Alert Statistics:", json.dumps(stats, indent=2))
    
    alert_manager.stop_monitoring()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_alert_manager())