import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque
import threading
import psutil
import requests

logger = logging.getLogger(__name__)

class MetricLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class SystemMetric:
    name: str
    value: float
    unit: str
    timestamp: datetime
    level: MetricLevel = MetricLevel.INFO
    metadata: Dict[str, Any] = None

@dataclass
class ServiceHealth:
    service_name: str
    status: str  # healthy, degraded, down
    response_time: Optional[float]
    error_rate: float
    last_check: datetime
    endpoints: Dict[str, bool] = None

class MetricsBuffer:
    """Thread-safe metrics buffer with rolling window"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.metrics = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add_metric(self, metric: SystemMetric):
        with self.lock:
            self.metrics.append(metric)
    
    def get_metrics(self, since: Optional[datetime] = None) -> List[SystemMetric]:
        with self.lock:
            if since is None:
                return list(self.metrics)
            return [m for m in self.metrics if m.timestamp >= since]
    
    def get_latest(self, metric_name: str) -> Optional[SystemMetric]:
        with self.lock:
            for metric in reversed(self.metrics):
                if metric.name == metric_name:
                    return metric
        return None

class MetricsCollector:
    """Comprehensive system metrics collector"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_buffer = MetricsBuffer(max_size=config.get('buffer_size', 10000))
        self.collection_interval = config.get('collection_interval', 60)  # seconds
        self.is_running = False
        self.collection_thread = None
        
        # Service endpoints for health checks
        self.service_endpoints = {
            'content_engine': config.get('content_engine_url', 'http://localhost:5001'),
            'platform_manager': config.get('platform_manager_url', 'http://localhost:5002'),
            'trend_monitor': config.get('trend_monitor_url', 'http://localhost:5003')
        }
        
        # Performance counters
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        
        logger.info("MetricsCollector initialized")

    def start_collection(self):
        """Start background metrics collection"""
        if not self.is_running:
            self.is_running = True
            self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
            self.collection_thread.start()
            logger.info("Metrics collection started")

    def stop_collection(self):
        """Stop background metrics collection"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Metrics collection stopped")

    def _collection_loop(self):
        """Main collection loop running in background thread"""
        while self.is_running:
            try:
                # Collect system metrics
                asyncio.run(self._collect_system_metrics())
                
                # Collect service health
                asyncio.run(self._collect_service_health())
                
                # Collect application metrics
                self._collect_application_metrics()
                
                # Sleep until next collection
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(10)  # Wait before retrying

    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            timestamp = datetime.now()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_buffer.add_metric(SystemMetric(
                name="system.cpu.usage",
                value=cpu_percent,
                unit="percent",
                timestamp=timestamp,
                level=MetricLevel.WARNING if cpu_percent > 80 else MetricLevel.INFO
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics_buffer.add_metric(SystemMetric(
                name="system.memory.usage",
                value=memory.percent,
                unit="percent", 
                timestamp=timestamp,
                level=MetricLevel.WARNING if memory.percent > 85 else MetricLevel.INFO
            ))
            
            self.metrics_buffer.add_metric(SystemMetric(
                name="system.memory.available",
                value=memory.available / (1024**3),  # GB
                unit="GB",
                timestamp=timestamp
            ))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.metrics_buffer.add_metric(SystemMetric(
                name="system.disk.usage",
                value=disk_percent,
                unit="percent",
                timestamp=timestamp,
                level=MetricLevel.WARNING if disk_percent > 85 else MetricLevel.INFO
            ))
            
            # Network metrics
            net_io = psutil.net_io_counters()
            self.metrics_buffer.add_metric(SystemMetric(
                name="system.network.bytes_sent",
                value=net_io.bytes_sent,
                unit="bytes",
                timestamp=timestamp
            ))
            
            self.metrics_buffer.add_metric(SystemMetric(
                name="system.network.bytes_recv",
                value=net_io.bytes_recv,
                unit="bytes",
                timestamp=timestamp
            ))
            
            # Process count
            process_count = len(psutil.pids())
            self.metrics_buffer.add_metric(SystemMetric(
                name="system.processes.count",
                value=process_count,
                unit="count",
                timestamp=timestamp
            ))
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _collect_service_health(self):
        """Collect health status of all services"""
        timestamp = datetime.now()
        
        for service_name, base_url in self.service_endpoints.items():
            try:
                health_status = await self._check_service_health(service_name, base_url)
                
                # Store service health metrics
                self.metrics_buffer.add_metric(SystemMetric(
                    name=f"service.{service_name}.health",
                    value=1 if health_status.status == "healthy" else 0,
                    unit="boolean",
                    timestamp=timestamp,
                    level=MetricLevel.CRITICAL if health_status.status == "down" else MetricLevel.INFO,
                    metadata=asdict(health_status)
                ))
                
                if health_status.response_time:
                    self.metrics_buffer.add_metric(SystemMetric(
                        name=f"service.{service_name}.response_time",
                        value=health_status.response_time,
                        unit="ms",
                        timestamp=timestamp,
                        level=MetricLevel.WARNING if health_status.response_time > 1000 else MetricLevel.INFO
                    ))
                
                self.metrics_buffer.add_metric(SystemMetric(
                    name=f"service.{service_name}.error_rate",
                    value=health_status.error_rate,
                    unit="percent",
                    timestamp=timestamp,
                    level=MetricLevel.WARNING if health_status.error_rate > 5 else MetricLevel.INFO
                ))
                
            except Exception as e:
                logger.error(f"Error checking health for {service_name}: {e}")
                # Record service as down
                self.metrics_buffer.add_metric(SystemMetric(
                    name=f"service.{service_name}.health",
                    value=0,
                    unit="boolean",
                    timestamp=timestamp,
                    level=MetricLevel.CRITICAL,
                    metadata={"error": str(e)}
                ))

    async def _check_service_health(self, service_name: str, base_url: str) -> ServiceHealth:
        """Check health of a specific service"""
        start_time = time.time()
        
        try:
            # Check main health endpoint
            health_url = f"{base_url}/health"
            response = requests.get(health_url, timeout=5)
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                status = "healthy"
            elif response.status_code < 500:
                status = "degraded"
            else:
                status = "down"
            
            # Check specific endpoints
            endpoints = {}
            test_endpoints = {
                'content_engine': ['/generate', '/analyze'],
                'platform_manager': ['/upload', '/platforms'],
                'trend_monitor': ['/trends', '/collect']
            }
            
            if service_name in test_endpoints:
                for endpoint in test_endpoints[service_name]:
                    try:
                        test_response = requests.get(f"{base_url}{endpoint}", timeout=3)
                        endpoints[endpoint] = test_response.status_code < 500
                    except:
                        endpoints[endpoint] = False
            
            # Calculate error rate (simplified)
            total_requests = self.request_counts[service_name]
            total_errors = self.error_counts[service_name]
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            return ServiceHealth(
                service_name=service_name,
                status=status,
                response_time=response_time,
                error_rate=error_rate,
                last_check=datetime.now(),
                endpoints=endpoints
            )
            
        except requests.exceptions.RequestException as e:
            return ServiceHealth(
                service_name=service_name,
                status="down",
                response_time=None,
                error_rate=100.0,
                last_check=datetime.now()
            )

    def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        timestamp = datetime.now()
        
        try:
            # Request rate metrics
            for service_name, count in self.request_counts.items():
                self.metrics_buffer.add_metric(SystemMetric(
                    name=f"app.{service_name}.requests_total",
                    value=count,
                    unit="count",
                    timestamp=timestamp
                ))
            
            # Error rate metrics
            for service_name, errors in self.error_counts.items():
                total_requests = self.request_counts[service_name]
                error_rate = (errors / total_requests * 100) if total_requests > 0 else 0
                
                self.metrics_buffer.add_metric(SystemMetric(
                    name=f"app.{service_name}.error_rate",
                    value=error_rate,
                    unit="percent",
                    timestamp=timestamp,
                    level=MetricLevel.WARNING if error_rate > 5 else MetricLevel.INFO
                ))
            
            # Response time metrics
            for service_name, times in self.response_times.items():
                if times:
                    avg_response_time = sum(times) / len(times)
                    self.metrics_buffer.add_metric(SystemMetric(
                        name=f"app.{service_name}.avg_response_time",
                        value=avg_response_time,
                        unit="ms",
                        timestamp=timestamp,
                        level=MetricLevel.WARNING if avg_response_time > 1000 else MetricLevel.INFO
                    ))
                    
                    # Clear old response times (keep only last 100)
                    self.response_times[service_name] = times[-100:]
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")

    def record_request(self, service_name: str, response_time: float, success: bool = True):
        """Record a request for metrics"""
        self.request_counts[service_name] += 1
        self.response_times[service_name].append(response_time)
        
        if not success:
            self.error_counts[service_name] += 1

    def get_metrics_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Get metrics summary for the last N minutes"""
        since = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = self.metrics_buffer.get_metrics(since)
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_name[metric.name].append(metric)
        
        summary = {}
        for metric_name, metrics in metrics_by_name.items():
            if metrics:
                latest = metrics[-1]
                values = [m.value for m in metrics]
                
                summary[metric_name] = {
                    "latest_value": latest.value,
                    "unit": latest.unit,
                    "avg_value": sum(values) / len(values),
                    "min_value": min(values),
                    "max_value": max(values),
                    "data_points": len(values),
                    "level": latest.level.value,
                    "last_updated": latest.timestamp.isoformat()
                }
        
        return summary

    def get_alerts(self, level: MetricLevel = MetricLevel.WARNING) -> List[Dict[str, Any]]:
        """Get current alerts based on metric levels"""
        alerts = []
        
        # Get recent metrics with warning/critical levels
        recent_metrics = self.metrics_buffer.get_metrics(
            since=datetime.now() - timedelta(minutes=10)
        )
        
        # Group by metric name and get latest
        latest_metrics = {}
        for metric in recent_metrics:
            if metric.level.value in [MetricLevel.WARNING.value, MetricLevel.CRITICAL.value]:
                if (metric.name not in latest_metrics or 
                    metric.timestamp > latest_metrics[metric.name].timestamp):
                    latest_metrics[metric.name] = metric
        
        # Convert to alerts
        for metric_name, metric in latest_metrics.items():
            if metric.level == level or (level == MetricLevel.WARNING and metric.level == MetricLevel.CRITICAL):
                alerts.append({
                    "metric_name": metric_name,
                    "level": metric.level.value,
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                    "message": self._generate_alert_message(metric),
                    "metadata": metric.metadata
                })
        
        return sorted(alerts, key=lambda x: x["timestamp"], reverse=True)

    def _generate_alert_message(self, metric: SystemMetric) -> str:
        """Generate human-readable alert message"""
        if "cpu.usage" in metric.name:
            return f"High CPU usage: {metric.value:.1f}%"
        elif "memory.usage" in metric.name:
            return f"High memory usage: {metric.value:.1f}%"
        elif "disk.usage" in metric.name:
            return f"High disk usage: {metric.value:.1f}%"
        elif "service" in metric.name and "health" in metric.name:
            service = metric.name.split('.')[1]
            return f"Service {service} is unhealthy"
        elif "response_time" in metric.name:
            service = metric.name.split('.')[1]
            return f"High response time for {service}: {metric.value:.1f}ms"
        elif "error_rate" in metric.name:
            service = metric.name.split('.')[1]
            return f"High error rate for {service}: {metric.value:.1f}%"
        else:
            return f"Alert for {metric.name}: {metric.value} {metric.unit}"

    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        # Get latest metrics for each category
        cpu_metric = self.metrics_buffer.get_latest("system.cpu.usage")
        memory_metric = self.metrics_buffer.get_latest("system.memory.usage")
        disk_metric = self.metrics_buffer.get_latest("system.disk.usage")
        
        # Service health
        services_health = {}
        for service_name in self.service_endpoints.keys():
            health_metric = self.metrics_buffer.get_latest(f"service.{service_name}.health")
            response_metric = self.metrics_buffer.get_latest(f"service.{service_name}.response_time")
            
            if health_metric:
                services_health[service_name] = {
                    "status": "healthy" if health_metric.value == 1 else "unhealthy",
                    "response_time": response_metric.value if response_metric else None,
                    "last_check": health_metric.timestamp.isoformat()
                }
        
        # Overall system health score
        health_score = self._calculate_health_score()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": health_score,
            "system_resources": {
                "cpu_usage": cpu_metric.value if cpu_metric else None,
                "memory_usage": memory_metric.value if memory_metric else None,
                "disk_usage": disk_metric.value if disk_metric else None
            },
            "services": services_health,
            "alerts_count": {
                "critical": len(self.get_alerts(MetricLevel.CRITICAL)),
                "warning": len(self.get_alerts(MetricLevel.WARNING))
            },
            "total_requests": sum(self.request_counts.values()),
            "total_errors": sum(self.error_counts.values())
        }

    def _calculate_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score (0-100)"""
        score = 100
        status = "healthy"
        
        # Check system resources
        cpu_metric = self.metrics_buffer.get_latest("system.cpu.usage")
        memory_metric = self.metrics_buffer.get_latest("system.memory.usage")
        disk_metric = self.metrics_buffer.get_latest("system.disk.usage")
        
        if cpu_metric and cpu_metric.value > 90:
            score -= 20
            status = "degraded"
        elif cpu_metric and cpu_metric.value > 80:
            score -= 10
        
        if memory_metric and memory_metric.value > 90:
            score -= 20
            status = "degraded"
        elif memory_metric and memory_metric.value > 85:
            score -= 10
        
        if disk_metric and disk_metric.value > 95:
            score -= 15
            status = "degraded"
        
        # Check service health
        unhealthy_services = 0
        for service_name in self.service_endpoints.keys():
            health_metric = self.metrics_buffer.get_latest(f"service.{service_name}.health")
            if health_metric and health_metric.value == 0:
                unhealthy_services += 1
        
        if unhealthy_services > 0:
            score -= unhealthy_services * 25
            status = "critical" if unhealthy_services > 1 else "degraded"
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        if score < 50:
            status = "critical"
        elif score < 80:
            status = "degraded"
        
        return {
            "score": score,
            "status": status,
            "last_calculated": datetime.now().isoformat()
        }

    def export_metrics(self, format_type: str = "json", since: Optional[datetime] = None) -> Any:
        """Export metrics in various formats"""
        metrics = self.metrics_buffer.get_metrics(since)
        
        if format_type == "json":
            return {
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp.isoformat(),
                        "level": m.level.value,
                        "metadata": m.metadata
                    }
                    for m in metrics
                ],
                "export_time": datetime.now().isoformat(),
                "total_metrics": len(metrics)
            }
        
        elif format_type == "prometheus":
            # Convert to Prometheus format
            prometheus_metrics = []
            for metric in metrics:
                # Convert metric name to Prometheus format
                prom_name = metric.name.replace(".", "_")
                timestamp = int(metric.timestamp.timestamp() * 1000)
                
                prometheus_metrics.append(
                    f'{prom_name} {metric.value} {timestamp}'
                )
            
            return '\n'.join(prometheus_metrics)
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def clear_old_metrics(self, older_than_hours: int = 24):
        """Clear metrics older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        with self.metrics_buffer.lock:
            # Keep only metrics newer than cutoff
            self.metrics_buffer.metrics = deque(
                [m for m in self.metrics_buffer.metrics if m.timestamp >= cutoff_time],
                maxlen=self.metrics_buffer.max_size
            )
        
        logger.info(f"Cleared metrics older than {older_than_hours} hours")

# Usage example and testing functions
async def test_metrics_collector():
    """Test function for metrics collector"""
    config = {
        'buffer_size': 1000,
        'collection_interval': 10,
        'content_engine_url': 'http://localhost:5001',
        'platform_manager_url': 'http://localhost:5002',
        'trend_monitor_url': 'http://localhost:5003'
    }
    
    collector = MetricsCollector(config)
    collector.start_collection()
    
    # Simulate some requests
    collector.record_request("content_engine", 150.0, True)
    collector.record_request("content_engine", 200.0, True)
    collector.record_request("platform_manager", 100.0, False)
    
    await asyncio.sleep(15)  # Let it collect some metrics
    
    # Get summary
    summary = collector.get_metrics_summary(minutes=1)
    print("Metrics Summary:", json.dumps(summary, indent=2))
    
    # Get alerts
    alerts = collector.get_alerts()
    print("Alerts:", json.dumps(alerts, indent=2))
    
    # Get system overview
    overview = collector.get_system_overview()
    print("System Overview:", json.dumps(overview, indent=2))
    
    collector.stop_collection()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    asyncio.run(test_metrics_collector())