#!/usr/bin/env python3
"""
AI Content Factory - Performance Monitoring System
===============================================

This module provides comprehensive performance monitoring including:
- System metrics (CPU, Memory, Disk, Network)
- Application metrics (Response times, Throughput, Error rates)
- Database performance monitoring
- AI service performance tracking
- Alert system for performance issues

Path: ai-content-factory/shared/utils/performance_monitor.py
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Any, Optional, Callable, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from functools import wraps
import json
import threading
from collections import deque, defaultdict
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    COUNTER = "counter"           # Cumulative values (requests count)
    GAUGE = "gauge"               # Point-in-time values (CPU usage)
    HISTOGRAM = "histogram"       # Distribution of values (response times)
    SUMMARY = "summary"           # Summary statistics
    TIMER = "timer"              # Time-based measurements


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class AlertRule:
    """Performance alert rule configuration"""
    name: str
    metric_name: str
    condition: str              # e.g., "> 80", "< 0.95", "== 0"
    threshold: float
    duration: int               # Alert after N consecutive violations
    level: AlertLevel = AlertLevel.WARNING
    enabled: bool = True
    cooldown: int = 300         # Cooldown period in seconds


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage_percent: float
    disk_io_read: int
    disk_io_write: int
    network_io_sent: int
    network_io_recv: int
    load_average: List[float]
    process_count: int
    timestamp: datetime


class MetricsCollector:
    """Collects various performance metrics"""
    
    def __init__(self, collection_interval: float = 60.0):
        self.collection_interval = collection_interval
        self._metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self._running = False
        self._collector_task = None
        self._custom_collectors = {}
    
    async def start(self):
        """Start metrics collection"""
        if not self._running:
            self._running = True
            self._collector_task = asyncio.create_task(self._collection_loop())
            logger.info("Metrics collection started")
    
    async def stop(self):
        """Stop metrics collection"""
        self._running = False
        if self._collector_task:
            self._collector_task.cancel()
            try:
                await self._collector_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collection stopped")
    
    def add_custom_collector(self, name: str, collector_func: Callable[[], Dict[str, float]]):
        """Add custom metric collector"""
        self._custom_collectors[name] = collector_func
    
    async def _collection_loop(self):
        """Main metrics collection loop"""
        while self._running:
            try:
                # Collect system metrics
                system_metrics = await self._collect_system_metrics()
                self._store_metrics("system", system_metrics)
                
                # Collect custom metrics
                for name, collector in self._custom_collectors.items():
                    try:
                        if asyncio.iscoroutinefunction(collector):
                            custom_metrics = await collector()
                        else:
                            custom_metrics = collector()
                        self._store_metrics(f"custom_{name}", custom_metrics)
                    except Exception as e:
                        logger.error(f"Error collecting custom metrics {name}: {e}")
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_1m': load_avg[0],
                'load_5m': load_avg[1],
                'load_15m': load_avg[2],
                'memory_percent': memory.percent,
                'memory_used': memory.used,
                'memory_available': memory.available,
                'memory_total': memory.total,
                'swap_percent': swap.percent,
                'swap_used': swap.used,
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'disk_used': disk.used,
                'disk_free': disk.free,
                'disk_total': disk.total,
                'disk_io_read': disk_io.read_bytes if disk_io else 0,
                'disk_io_write': disk_io.write_bytes if disk_io else 0,
                'network_io_sent': network_io.bytes_sent if network_io else 0,
                'network_io_recv': network_io.bytes_recv if network_io else 0,
                'process_count': process_count,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _store_metrics(self, category: str, metrics: Dict[str, float]):
        """Store metrics in history"""
        timestamp = datetime.now()
        for name, value in metrics.items():
            metric_point = MetricPoint(
                name=f"{category}.{name}",
                value=value,
                timestamp=timestamp
            )
            self._metrics_history[metric_point.name].append(metric_point)
    
    def get_metrics(self, name: str, duration_minutes: int = 60) -> List[MetricPoint]:
        """Get metrics history for specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [
            point for point in self._metrics_history[name]
            if point.timestamp >= cutoff_time
        ]
    
    def get_latest_metrics(self) -> Dict[str, MetricPoint]:
        """Get latest metric values"""
        latest = {}
        for name, history in self._metrics_history.items():
            if history:
                latest[name] = history[-1]
        return latest


class PerformanceProfiler:
    """Context manager for profiling code performance"""
    
    def __init__(self, name: str, metrics_collector: MetricsCollector = None):
        self.name = name
        self.metrics_collector = metrics_collector
        self.start_time = None
        self.end_time = None
        self._active_profiles = {}
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        execution_time = self.end_time - self.start_time
        
        if self.metrics_collector:
            self.metrics_collector._store_metrics("performance", {
                f"{self.name}.execution_time": execution_time,
                f"{self.name}.success": 1 if exc_type is None else 0,
                f"{self.name}.error": 1 if exc_type is not None else 0
            })
        
        logger.debug(f"Performance profile {self.name}: {execution_time:.4f}s")


class ApplicationMetrics:
    """Application-specific metrics tracking"""
    
    def __init__(self):
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(list)
        self._timers = defaultdict(list)
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value"""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a value in a histogram"""
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            
            # Keep only recent values to prevent memory issues
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-500:]
    
    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Record a timer duration"""
        with self._lock:
            key = self._make_key(name, labels)
            self._timers[key].append(duration)
            
            # Keep only recent values
            if len(self._timers[key]) > 1000:
                self._timers[key] = self._timers[key][-500:]
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create a unique key for metric with labels"""
        if not labels:
            return name
        
        label_str = ",".join([f"{k}={v}" for k, v in sorted(labels.items())])
        return f"{name}{{{label_str}}}"
    
    def get_counter(self, name: str, labels: Dict[str, str] = None) -> int:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)
    
    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            'count': count,
            'sum': sum(sorted_values),
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'avg': sum(sorted_values) / count,
            'p50': sorted_values[int(count * 0.5)],
            'p95': sorted_values[int(count * 0.95)],
            'p99': sorted_values[int(count * 0.99)]
        }
    
    def get_timer_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get timer statistics"""
        key = self._make_key(name, labels)
        durations = self._timers.get(key, [])
        
        if not durations:
            return {}
        
        sorted_durations = sorted(durations)
        count = len(sorted_durations)
        
        return {
            'count': count,
            'total_time': sum(sorted_durations),
            'min_time': sorted_durations[0],
            'max_time': sorted_durations[-1],
            'avg_time': sum(sorted_durations) / count,
            'p50_time': sorted_durations[int(count * 0.5)],
            'p95_time': sorted_durations[int(count * 0.95)],
            'p99_time': sorted_durations[int(count * 0.99)]
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self._lock:
            result = {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {},
                'timers': {}
            }
            
            # Get histogram stats
            for key in self._histograms.keys():
                name_parts = key.split('{', 1)
                name = name_parts[0]
                labels = self._parse_labels(name_parts[1][:-1]) if len(name_parts) > 1 else None
                result['histograms'][key] = self.get_histogram_stats(name, labels)
            
            # Get timer stats
            for key in self._timers.keys():
                name_parts = key.split('{', 1)
                name = name_parts[0]
                labels = self._parse_labels(name_parts[1][:-1]) if len(name_parts) > 1 else None
                result['timers'][key] = self.get_timer_stats(name, labels)
            
            return result
    
    def _parse_labels(self, label_str: str) -> Dict[str, str]:
        """Parse labels from string"""
        if not label_str:
            return {}
        
        labels = {}
        for pair in label_str.split(','):
            if '=' in pair:
                key, value = pair.split('=', 1)
                labels[key.strip()] = value.strip()
        
        return labels


class AlertManager:
    """Manages performance alerts and notifications"""
    
    def __init__(self, webhook_url: str = None, slack_webhook: str = None):
        self.webhook_url = webhook_url
        self.slack_webhook = slack_webhook
        self.rules = {}
        self.alert_state = {}  # Track alert states to prevent spam
        self._lock = threading.Lock()
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        with self._lock:
            self.rules[rule.name] = rule
            self.alert_state[rule.name] = {
                'violations': 0,
                'last_alert': None,
                'is_alerting': False
            }
    
    def remove_rule(self, rule_name: str):
        """Remove an alert rule"""
        with self._lock:
            self.rules.pop(rule_name, None)
            self.alert_state.pop(rule_name, None)
    
    async def check_alerts(self, metrics: Dict[str, MetricPoint]):
        """Check all alert rules against current metrics"""
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            metric = metrics.get(rule.metric_name)
            if not metric:
                continue
            
            violation = self._evaluate_condition(metric.value, rule.condition, rule.threshold)
            await self._process_alert_state(rule, violation)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        condition = condition.strip()
        
        if condition.startswith('>='):
            return value >= threshold
        elif condition.startswith('<='):
            return value <= threshold
        elif condition.startswith('>'):
            return value > threshold
        elif condition.startswith('<'):
            return value < threshold
        elif condition.startswith('=='):
            return abs(value - threshold) < 0.001
        elif condition.startswith('!='):
            return abs(value - threshold) >= 0.001
        else:
            # Default to greater than
            return value > threshold
    
    async def _process_alert_state(self, rule: AlertRule, violation: bool):
        """Process alert state and send notifications if needed"""
        state = self.alert_state[rule.name]
        current_time = time.time()
        
        if violation:
            state['violations'] += 1
            
            # Check if we should trigger an alert
            if (state['violations'] >= rule.duration and 
                not state['is_alerting'] and
                (not state['last_alert'] or 
                 current_time - state['last_alert'] > rule.cooldown)):
                
                await self._send_alert(rule, 'FIRING')
                state['is_alerting'] = True
                state['last_alert'] = current_time
        else:
            if state['is_alerting']:
                await self._send_alert(rule, 'RESOLVED')
                state['is_alerting'] = False
            
            state['violations'] = 0
    
    async def _send_alert(self, rule: AlertRule, status: str):
        """Send alert notification"""
        alert_data = {
            'rule_name': rule.name,
            'metric_name': rule.metric_name,
            'status': status,
            'level': rule.level.value,
            'threshold': rule.threshold,
            'condition': rule.condition,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to webhook
        if self.webhook_url:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(self.webhook_url, json=alert_data)
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")
        
        # Send to Slack
        if self.slack_webhook:
            await self._send_slack_alert(alert_data)
        
        logger.warning(f"Alert {status}: {rule.name} - {rule.metric_name} {rule.condition} {rule.threshold}")
    
    async def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Send alert to Slack"""
        color = {
            'INFO': '#36a64f',
            'WARNING': '#ff9500', 
            'CRITICAL': '#ff0000',
            'EMERGENCY': '#8b0000'
        }.get(alert_data['level'].upper(), '#ff9500')
        
        status_emoji = '🔥' if alert_data['status'] == 'FIRING' else '✅'
        
        slack_message = {
            'text': f"{status_emoji} Performance Alert: {alert_data['rule_name']}",
            'attachments': [{
                'color': color,
                'fields': [
                    {'title': 'Status', 'value': alert_data['status'], 'short': True},
                    {'title': 'Level', 'value': alert_data['level'].title(), 'short': True},
                    {'title': 'Metric', 'value': alert_data['metric_name'], 'short': True},
                    {'title': 'Condition', 'value': f"{alert_data['condition']} {alert_data['threshold']}", 'short': True},
                    {'title': 'Time', 'value': alert_data['timestamp'], 'short': False}
                ]
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.slack_webhook, json=slack_message)
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")


class DatabaseMetricsCollector:
    """Collect database performance metrics"""
    
    def __init__(self, db_connection_func: Callable):
        self.db_connection_func = db_connection_func
    
    async def collect_metrics(self) -> Dict[str, float]:
        """Collect database performance metrics"""
        try:
            # This would be implemented based on your database type
            # Example for PostgreSQL:
            
            conn = await self.db_connection_func()
            
            queries = {
                'active_connections': """
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active';
                """,
                'idle_connections': """
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'idle';
                """,
                'slow_queries': """
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active' AND query_start < now() - interval '30 seconds';
                """,
                'database_size': """
                    SELECT pg_database_size(current_database());
                """,
                'cache_hit_ratio': """
                    SELECT 
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100
                    FROM pg_statio_user_tables;
                """
            }
            
            metrics = {}
            for metric_name, query in queries.items():
                try:
                    result = await conn.fetchval(query)
                    metrics[f"db.{metric_name}"] = float(result or 0)
                except Exception as e:
                    logger.error(f"Error collecting {metric_name}: {e}")
                    metrics[f"db.{metric_name}"] = 0.0
            
            await conn.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {}


class AIServiceMetricsCollector:
    """Collect AI service performance metrics"""
    
    def __init__(self):
        self.service_stats = defaultdict(lambda: {
            'requests': 0,
            'errors': 0,
            'total_time': 0.0,
            'last_request': None
        })
    
    def record_request(self, service: str, duration: float, success: bool):
        """Record AI service request"""
        stats = self.service_stats[service]
        stats['requests'] += 1
        stats['total_time'] += duration
        stats['last_request'] = time.time()
        
        if not success:
            stats['errors'] += 1
    
    def get_metrics(self) -> Dict[str, float]:
        """Get AI service metrics"""
        metrics = {}
        
        for service, stats in self.service_stats.items():
            if stats['requests'] > 0:
                avg_time = stats['total_time'] / stats['requests']
                error_rate = (stats['errors'] / stats['requests']) * 100
                
                metrics[f"ai.{service}.requests"] = stats['requests']
                metrics[f"ai.{service}.errors"] = stats['errors']
                metrics[f"ai.{service}.avg_time"] = avg_time
                metrics[f"ai.{service}.error_rate"] = error_rate
                
                if stats['last_request']:
                    time_since_last = time.time() - stats['last_request']
                    metrics[f"ai.{service}.time_since_last"] = time_since_last
        
        return metrics


# Performance monitoring decorators
def monitor_performance(metric_name: str = None, app_metrics: ApplicationMetrics = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                
                if app_metrics:
                    app_metrics.record_timer(f"{name}.duration", duration)
                    app_metrics.increment_counter(f"{name}.calls")
                    if not success:
                        app_metrics.increment_counter(f"{name}.errors")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                
                if app_metrics:
                    app_metrics.record_timer(f"{name}.duration", duration)
                    app_metrics.increment_counter(f"{name}.calls")
                    if not success:
                        app_metrics.increment_counter(f"{name}.errors")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.metrics_collector = MetricsCollector(
            collection_interval=self.config.get('collection_interval', 60.0)
        )
        
        self.app_metrics = ApplicationMetrics()
        
        self.alert_manager = AlertManager(
            webhook_url=self.config.get('webhook_url'),
            slack_webhook=self.config.get('slack_webhook')
        )
        
        self.db_collector = None
        self.ai_collector = AIServiceMetricsCollector()
        
        self._monitoring_task = None
    
    async def start(self):
        """Start performance monitoring"""
        await self.metrics_collector.start()
        
        # Add AI service collector
        self.metrics_collector.add_custom_collector('ai_services', self.ai_collector.get_metrics)
        
        # Add database collector if configured
        if self.config.get('db_connection_func'):
            self.db_collector = DatabaseMetricsCollector(self.config['db_connection_func'])
            self.metrics_collector.add_custom_collector('database', self.db_collector.collect_metrics)
        
        # Start alert monitoring
        self._monitoring_task = asyncio.create_task(self._alert_monitoring_loop())
        
        # Setup default alerts
        self._setup_default_alerts()
        
        logger.info("Performance monitoring started")
    
    async def stop(self):
        """Stop performance monitoring"""
        await self.metrics_collector.stop()
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                metric_name="system.cpu_percent",
                condition="> 80",
                threshold=80.0,
                duration=3,
                level=AlertLevel.WARNING
            ),
            AlertRule(
                name="high_memory_usage",
                metric_name="system.memory_percent",
                condition="> 90",
                threshold=90.0,
                duration=2,
                level=AlertLevel.CRITICAL
            ),
            AlertRule(
                name="high_disk_usage",
                metric_name="system.disk_usage_percent",
                condition="> 85",
                threshold=85.0,
                duration=1,
                level=AlertLevel.WARNING
            ),
            AlertRule(
                name="high_error_rate",
                metric_name="app.error_rate",
                condition="> 5",
                threshold=5.0,
                duration=2,
                level=AlertLevel.CRITICAL
            )
        ]
        
        for rule in default_rules:
            self.alert_manager.add_rule(rule)
    
    async def _alert_monitoring_loop(self):
        """Main alert monitoring loop"""
        while True:
            try:
                latest_metrics = self.metrics_collector.get_latest_metrics()
                await self.alert_manager.check_alerts(latest_metrics)
                await asyncio.sleep(30)  # Check alerts every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(30)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for performance dashboard"""
        latest_metrics = self.metrics_collector.get_latest_metrics()
        app_metrics = self.app_metrics.get_all_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {
                name.replace('system.', ''): metric.value 
                for name, metric in latest_metrics.items() 
                if name.startswith('system.')
            },
            'application_metrics': app_metrics,
            'ai_service_metrics': {
                name.replace('custom_ai_services.', ''): metric.value
                for name, metric in latest_metrics.items()
                if name.startswith('custom_ai_services.')
            },
            'database_metrics': {
                name.replace('custom_database.', ''): metric.value
                for name, metric in latest_metrics.items()
                if name.startswith('custom_database.')
            }
        }


# Usage examples and context managers
@asynccontextmanager
async def performance_monitoring(config: Dict[str, Any] = None):
    """Context manager for performance monitoring"""
    monitor = PerformanceMonitor(config)
    try:
        await monitor.start()
        yield monitor
    finally:
        await monitor.stop()


# Example usage
if __name__ == "__main__":
    async def example_usage():
        config = {
            'collection_interval': 30.0,
            'slack_webhook': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        }
        
        async with performance_monitoring(config) as monitor:
            # Simulate some work
            for i in range(10):
                monitor.app_metrics.increment_counter('test.requests')
                monitor.app_metrics.record_timer('test.duration', 0.1 + (i * 0.01))
                await asyncio.sleep(1)
            
            # Get dashboard data
            dashboard_data = monitor.get_dashboard_data()
            print(json.dumps(dashboard_data, indent=2, default=str))
    
    # Run example
    asyncio.run(example_usage())