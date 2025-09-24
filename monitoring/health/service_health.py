#!/usr/bin/env python3
"""
Service Health Monitor for AI Content Factory
ใช้สำหรับติดตามสุขภาพของ services ต่างๆ อย่างต่อเนื่อง
"""

import os
import sys
import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque
import json
import requests
import psycopg2
import redis
from concurrent.futures import ThreadPoolExecutor
import schedule

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.utils.logger import setup_logger
from shared.utils.error_handler import ErrorHandler
from monitoring.alerts.webhook_alerts import WebhookAlertManager

@dataclass
class ServiceMetrics:
    """Service metrics data structure"""
    service_name: str
    status: str
    response_time_ms: float
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_rate: float = 0.0
    request_count: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class HealthThreshold:
    """Health threshold configuration"""
    response_time_warning: float = 1000  # ms
    response_time_critical: float = 5000  # ms
    error_rate_warning: float = 5.0  # %
    error_rate_critical: float = 15.0  # %
    cpu_warning: float = 80.0  # %
    cpu_critical: float = 95.0  # %
    memory_warning: float = 80.0  # %
    memory_critical: float = 95.0  # %

class ServiceHealthMonitor:
    """Main service health monitoring class"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = setup_logger("service_health_monitor")
        self.error_handler = ErrorHandler()
        self.config = config or self._load_default_config()
        
        # Initialize components
        self.alert_manager = WebhookAlertManager(self.config.get('alerts', {}))
        self.thresholds = HealthThreshold(**self.config.get('thresholds', {}))
        
        # Data storage
        self.metrics_history: Dict[str, deque] = {}
        self.current_metrics: Dict[str, ServiceMetrics] = {}
        self.service_status: Dict[str, str] = {}
        
        # Monitoring control
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Initialize metrics history for each service
        for service_name in self.config['services'].keys():
            self.metrics_history[service_name] = deque(maxlen=1000)  # Keep last 1000 metrics
            self.service_status[service_name] = 'unknown'
        
        self.logger.info("Service Health Monitor initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'services': {
                'trend_monitor': {
                    'url': 'http://localhost:5001/health',
                    'timeout': 10,
                    'check_interval': 30,
                    'enabled': True
                },
                'content_engine': {
                    'url': 'http://localhost:5002/health',
                    'timeout': 15,
                    'check_interval': 30,
                    'enabled': True
                },
                'platform_manager': {
                    'url': 'http://localhost:5003/health',
                    'timeout': 10,
                    'check_interval': 30,
                    'enabled': True
                },
                'web_dashboard': {
                    'url': 'http://localhost:3000/health',
                    'timeout': 5,
                    'check_interval': 60,
                    'enabled': True
                },
                'database': {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': int(os.getenv('DB_PORT', 5432)),
                    'database': os.getenv('DB_NAME', 'content_factory'),
                    'user': os.getenv('DB_USER', 'admin'),
                    'password': os.getenv('DB_PASSWORD', 'password'),
                    'check_interval': 60,
                    'enabled': True
                },
                'redis': {
                    'host': os.getenv('REDIS_HOST', 'localhost'),
                    'port': int(os.getenv('REDIS_PORT', 6379)),
                    'db': int(os.getenv('REDIS_DB', 0)),
                    'check_interval': 60,
                    'enabled': True
                }
            },
            'monitoring': {
                'global_check_interval': 30,
                'max_retries': 3,
                'retry_delay': 5,
                'health_history_days': 7
            },
            'thresholds': {
                'response_time_warning': 1000,
                'response_time_critical': 5000,
                'error_rate_warning': 5.0,
                'error_rate_critical': 15.0,
                'cpu_warning': 80.0,
                'cpu_critical': 95.0,
                'memory_warning': 80.0,
                'memory_critical': 95.0
            },
            'alerts': {
                'enabled': True,
                'webhooks': [],
                'cooldown_minutes': 10
            }
        }
    
    def check_http_service(self, service_name: str, service_config: Dict[str, Any]) -> ServiceMetrics:
        """Check HTTP-based service health"""
        start_time = time.time()
        
        try:
            response = requests.get(
                service_config['url'],
                timeout=service_config.get('timeout', 10),
                headers=service_config.get('headers', {})
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Parse response for additional metrics
            metrics_data = {}
            if response.status_code == 200:
                try:
                    data = response.json()
                    metrics_data = data.get('metrics', {})
                except:
                    pass
            
            status = 'healthy' if response.status_code == 200 else 'warning'
            if response.status_code >= 500:
                status = 'critical'
            
            return ServiceMetrics(
                service_name=service_name,
                status=status,
                response_time_ms=response_time,
                cpu_usage=metrics_data.get('cpu_usage', 0.0),
                memory_usage=metrics_data.get('memory_usage', 0.0),
                error_rate=metrics_data.get('error_rate', 0.0),
                request_count=metrics_data.get('request_count', 0)
            )
            
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return ServiceMetrics(
                service_name=service_name,
                status='critical',
                response_time_ms=response_time,
                error_rate=100.0
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return ServiceMetrics(
                service_name=service_name,
                status='critical',
                response_time_ms=response_time,
                error_rate=100.0
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"HTTP service check failed for {service_name}: {str(e)}")
            return ServiceMetrics(
                service_name=service_name,
                status='unknown',
                response_time_ms=response_time,
                error_rate=100.0
            )
    
    def check_database_service(self, service_config: Dict[str, Any]) -> ServiceMetrics:
        """Check database service health"""
        start_time = time.time()
        
        try:
            conn = psycopg2.connect(
                host=service_config['host'],
                port=service_config['port'],
                database=service_config['database'],
                user=service_config['user'],
                password=service_config['password'],
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            
            # Test query and get metrics
            cursor.execute("""
                SELECT 
                    count(*) as active_connections,
                    pg_database_size(%s) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries
            """, (service_config['database'],))
            
            active_connections, db_size, active_queries = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return ServiceMetrics(
                service_name='database',
                status='healthy',
                response_time_ms=response_time,
                request_count=active_connections
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Database check failed: {str(e)}")
            return ServiceMetrics(
                service_name='database',
                status='critical',
                response_time_ms=response_time,
                error_rate=100.0
            )
    
    def check_redis_service(self, service_config: Dict[str, Any]) -> ServiceMetrics:
        """Check Redis service health"""
        start_time = time.time()
        
        try:
            r = redis.Redis(
                host=service_config['host'],
                port=service_config['port'],
                db=service_config['db'],
                socket_timeout=5,
                decode_responses=True
            )
            
            # Test ping and get info
            r.ping()
            info = r.info()
            
            response_time = (time.time() - start_time) * 1000
            
            memory_usage = (info.get('used_memory', 0) / info.get('maxmemory', 1)) * 100 if info.get('maxmemory') else 0
            
            return ServiceMetrics(
                service_name='redis',
                status='healthy',
                response_time_ms=response_time,
                memory_usage=memory_usage,
                request_count=info.get('connected_clients', 0)
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Redis check failed: {str(e)}")
            return ServiceMetrics(
                service_name='redis',
                status='critical',
                response_time_ms=response_time,
                error_rate=100.0
            )
    
    def check_service_health(self, service_name: str) -> ServiceMetrics:
        """Check individual service health"""
        service_config = self.config['services'].get(service_name)
        
        if not service_config or not service_config.get('enabled', True):
            return ServiceMetrics(
                service_name=service_name,
                status='disabled',
                response_time_ms=0
            )
        
        try:
            if service_name == 'database':
                return self.check_database_service(service_config)
            elif service_name == 'redis':
                return self.check_redis_service(service_config)
            else:
                return self.check_http_service(service_name, service_config)
                
        except Exception as e:
            self.logger.error(f"Service health check failed for {service_name}: {str(e)}")
            return ServiceMetrics(
                service_name=service_name,
                status='unknown',
                response_time_ms=0,
                error_rate=100.0
            )
    
    def analyze_service_health(self, metrics: ServiceMetrics) -> Dict[str, Any]:
        """Analyze service metrics against thresholds"""
        analysis = {
            'service_name': metrics.service_name,
            'current_status': metrics.status,
            'alerts': [],
            'recommendations': []
        }
        
        # Response time analysis
        if metrics.response_time_ms >= self.thresholds.response_time_critical:
            analysis['alerts'].append({
                'type': 'critical',
                'metric': 'response_time',
                'value': metrics.response_time_ms,
                'threshold': self.thresholds.response_time_critical,
                'message': f"Response time critical: {metrics.response_time_ms:.1f}ms"
            })
        elif metrics.response_time_ms >= self.thresholds.response_time_warning:
            analysis['alerts'].append({
                'type': 'warning',
                'metric': 'response_time',
                'value': metrics.response_time_ms,
                'threshold': self.thresholds.response_time_warning,
                'message': f"Response time high: {metrics.response_time_ms:.1f}ms"
            })
        
        # Error rate analysis
        if metrics.error_rate >= self.thresholds.error_rate_critical:
            analysis['alerts'].append({
                'type': 'critical',
                'metric': 'error_rate',
                'value': metrics.error_rate,
                'threshold': self.thresholds.error_rate_critical,
                'message': f"Error rate critical: {metrics.error_rate:.1f}%"
            })
        elif metrics.error_rate >= self.thresholds.error_rate_warning:
            analysis['alerts'].append({
                'type': 'warning',
                'metric': 'error_rate',
                'value': metrics.error_rate,
                'threshold': self.thresholds.error_rate_warning,
                'message': f"Error rate high: {metrics.error_rate:.1f}%"
            })
        
        # CPU usage analysis
        if metrics.cpu_usage >= self.thresholds.cpu_critical:
            analysis['alerts'].append({
                'type': 'critical',
                'metric': 'cpu_usage',
                'value': metrics.cpu_usage,
                'threshold': self.thresholds.cpu_critical,
                'message': f"CPU usage critical: {metrics.cpu_usage:.1f}%"
            })
        elif metrics.cpu_usage >= self.thresholds.cpu_warning:
            analysis['alerts'].append({
                'type': 'warning',
                'metric': 'cpu_usage',
                'value': metrics.cpu_usage,
                'threshold': self.thresholds.cpu_warning,
                'message': f"CPU usage high: {metrics.cpu_usage:.1f}%"
            })
        
        # Memory usage analysis
        if metrics.memory_usage >= self.thresholds.memory_critical:
            analysis['alerts'].append({
                'type': 'critical',
                'metric': 'memory_usage',
                'value': metrics.memory_usage,
                'threshold': self.thresholds.memory_critical,
                'message': f"Memory usage critical: {metrics.memory_usage:.1f}%"
            })
        elif metrics.memory_usage >= self.thresholds.memory_warning:
            analysis['alerts'].append({
                'type': 'warning',
                'metric': 'memory_usage',
                'value': metrics.memory_usage,
                'threshold': self.thresholds.memory_warning,
                'message': f"Memory usage high: {metrics.memory_usage:.1f}%"
            })
        
        # Generate recommendations
        if metrics.response_time_ms > self.thresholds.response_time_warning:
            analysis['recommendations'].append("Consider optimizing service performance or scaling resources")
        
        if metrics.error_rate > 0:
            analysis['recommendations'].append("Investigate and fix service errors")
        
        if metrics.cpu_usage > self.thresholds.cpu_warning:
            analysis['recommendations'].append("Consider CPU optimization or horizontal scaling")
        
        if metrics.memory_usage > self.thresholds.memory_warning:
            analysis['recommendations'].append("Consider memory optimization or increasing memory allocation")
        
        return analysis
    
    def get_service_trend(self, service_name: str, hours: int = 1) -> Dict[str, Any]:
        """Get service health trend over specified hours"""
        if service_name not in self.metrics_history:
            return {'error': 'Service not found'}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history[service_name] 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {'error': 'No recent data available'}
        
        # Calculate trend metrics
        response_times = [m.response_time_ms for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]
        cpu_usage = [m.cpu_usage for m in recent_metrics if m.cpu_usage > 0]
        memory_usage = [m.memory_usage for m in recent_metrics if m.memory_usage > 0]
        
        trend = {
            'service_name': service_name,
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'response_time': {
                'avg': sum(response_times) / len(response_times) if response_times else 0,
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0
            },
            'error_rate': {
                'avg': sum(error_rates) / len(error_rates) if error_rates else 0,
                'max': max(error_rates) if error_rates else 0
            },
            'availability': (len([m for m in recent_metrics if m.status == 'healthy']) / len(recent_metrics)) * 100,
            'status_distribution': {}
        }
        
        if cpu_usage:
            trend['cpu_usage'] = {
                'avg': sum(cpu_usage) / len(cpu_usage),
                'max': max(cpu_usage)
            }
        
        if memory_usage:
            trend['memory_usage'] = {
                'avg': sum(memory_usage) / len(memory_usage),
                'max': max(memory_usage)
            }
        
        # Status distribution
        statuses = [m.status for m in recent_metrics]
        for status in set(statuses):
            trend['status_distribution'][status] = statuses.count(status)
        
        return trend
    
    def run_health_check_cycle(self):
        """Run one complete health check cycle for all services"""
        self.logger.debug("Running health check cycle...")
        
        with ThreadPoolExecutor(max_workers=len(self.config['services'])) as executor:
            futures = {
                executor.submit(self.check_service_health, service_name): service_name
                for service_name in self.config['services'].keys()
            }
            
            for future in futures:
                service_name = futures[future]
                try:
                    metrics = future.result(timeout=30)
                    
                    # Store metrics
                    self.current_metrics[service_name] = metrics
                    self.metrics_history[service_name].append(metrics)
                    
                    # Update service status
                    old_status = self.service_status.get(service_name, 'unknown')
                    new_status = metrics.status
                    self.service_status[service_name] = new_status
                    
                    # Check for status changes and alert if necessary
                    if old_status != new_status:
                        self._handle_status_change(service_name, old_status, new_status, metrics)
                    
                    # Analyze metrics and send alerts if needed
                    analysis = self.analyze_service_health(metrics)
                    if analysis['alerts']:
                        self._handle_alerts(service_name, analysis)
                    
                except Exception as e:
                    self.logger.error(f"Health check failed for {service_name}: {str(e)}")
    
    def _handle_status_change(self, service_name: str, old_status: str, new_status: str, metrics: ServiceMetrics):
        """Handle service status change"""
        self.logger.info(f"Service {service_name} status changed: {old_status} -> {new_status}")
        
        # Send alert for status changes
        if self.alert_manager:
            alert_data = {
                'type': 'status_change',
                'service': service_name,
                'old_status': old_status,
                'new_status': new_status,
                'response_time_ms': metrics.response_time_ms,
                'timestamp': metrics.timestamp.isoformat()
            }
            
            severity = 'critical' if new_status == 'critical' else 'warning' if new_status == 'warning' else 'info'
            
            asyncio.create_task(self.alert_manager.send_alert(
                title=f"Service Status Change: {service_name}",
                message=f"Service {service_name} status changed from {old_status} to {new_status}",
                severity=severity,
                data=alert_data
            ))
    
    def _handle_alerts(self, service_name: str, analysis: Dict[str, Any]):
        """Handle service health alerts"""
        for alert in analysis['alerts']:
            if self.alert_manager:
                alert_data = {
                    'type': 'metric_threshold',
                    'service': service_name,
                    'metric': alert['metric'],
                    'value': alert['value'],
                    'threshold': alert['threshold'],
                    'message': alert['message'],
                    'timestamp': datetime.now().isoformat()
                }
                
                asyncio.create_task(self.alert_manager.send_alert(
                    title=f"Service Alert: {service_name}",
                    message=alert['message'],
                    severity=alert['type'],
                    data=alert_data
                ))
    
    def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.logger.info("Starting service health monitoring...")
        
        # Schedule health checks
        interval = self.config['monitoring']['global_check_interval']
        schedule.every(interval).seconds.do(self.run_health_check_cycle)
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info(f"Service health monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("Service health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(5)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current status of all services"""
        return {
            'timestamp': datetime.now().isoformat(),
            'monitoring_active': self.monitoring_active,
            'services': {
                name: {
                    'status': status,
                    'last_check': self.current_metrics[name].timestamp.isoformat() if name in self.current_metrics else None,
                    'response_time_ms': self.current_metrics[name].response_time_ms if name in self.current_metrics else 0,
                    'metrics': asdict(self.current_metrics[name]) if name in self.current_metrics else {}
                }
                for name, status in self.service_status.items()
            }
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all services"""
        healthy_count = sum(1 for status in self.service_status.values() if status == 'healthy')
        warning_count = sum(1 for status in self.service_status.values() if status == 'warning')
        critical_count = sum(1 for status in self.service_status.values() if status == 'critical')
        unknown_count = sum(1 for status in self.service_status.values() if status == 'unknown')
        
        total_services = len(self.service_status)
        
        overall_status = 'healthy'
        if critical_count > 0:
            overall_status = 'critical'
        elif warning_count > 0:
            overall_status = 'warning'
        elif unknown_count > 0:
            overall_status = 'unknown'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'total_services': total_services,
            'healthy': healthy_count,
            'warning': warning_count,
            'critical': critical_count,
            'unknown': unknown_count,
            'availability_percentage': (healthy_count / total_services * 100) if total_services > 0 else 0
        }

# Example usage and CLI
def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Service Health Monitor")
    parser.add_argument('action', choices=['start', 'status', 'check', 'trends'], 
                       help='Action to perform')
    parser.add_argument('--service', '-s', help='Specific service name')
    parser.add_argument('--hours', type=int, default=1, help='Hours for trend analysis')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger("service_health_main", level=log_level)
    
    # Initialize monitor
    monitor = ServiceHealthMonitor()
    
    if args.action == 'start':
        logger.info("Starting service health monitoring...")
        monitor.start_monitoring()
        
        try:
            while True:
                time.sleep(10)
                summary = monitor.get_health_summary()
                logger.info(f"Health Summary - Overall: {summary['overall_status']} | "
                          f"Healthy: {summary['healthy']}/{summary['total_services']} | "
                          f"Availability: {summary['availability_percentage']:.1f}%")
        except KeyboardInterrupt:
            logger.info("Stopping monitoring...")
            monitor.stop_monitoring()
    
    elif args.action == 'status':
        status = monitor.get_current_status()
        print(json.dumps(status, indent=2))
    
    elif args.action == 'check':
        if args.service:
            metrics = monitor.check_service_health(args.service)
            print(json.dumps(asdict(metrics), indent=2, default=str))
        else:
            monitor.run_health_check_cycle()
            summary = monitor.get_health_summary()
            print(json.dumps(summary, indent=2))
    
    elif args.action == 'trends':
        if args.service:
            trend = monitor.get_service_trend(args.service, args.hours)
            print(json.dumps(trend, indent=2))
        else:
            logger.error("Service name required for trend analysis")

if __name__ == "__main__":
    main()