#!/usr/bin/env python3
"""
Health Check System for AI Content Factory
ใช้สำหรับตรวจสอบสุขภาพของระบบและ services ต่างๆ
"""

import os
import sys
import asyncio
import logging
import time
import psutil
import requests
import psycopg2
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.utils.logger import setup_logger
from shared.utils.error_handler import ErrorHandler

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    service_name: str
    status: HealthStatus
    response_time_ms: float
    message: str
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}

class SystemHealthChecker:
    """Main system health checker"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = setup_logger("health_checker")
        self.error_handler = ErrorHandler()
        self.config = config or self._load_default_config()
        self.results = {}
        
        self.logger.info("System Health Checker initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default health check configuration"""
        return {
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'content_factory'),
                'user': os.getenv('DB_USER', 'admin'),
                'password': os.getenv('DB_PASSWORD', 'password'),
                'timeout': 5
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'timeout': 3
            },
            'services': {
                'trend_monitor': {
                    'url': 'http://localhost:5001/health',
                    'timeout': 10
                },
                'content_engine': {
                    'url': 'http://localhost:5002/health',
                    'timeout': 15
                },
                'platform_manager': {
                    'url': 'http://localhost:5003/health',
                    'timeout': 10
                },
                'web_dashboard': {
                    'url': 'http://localhost:3000/health',
                    'timeout': 5
                }
            },
            'external_apis': {
                'openai': {
                    'url': 'https://api.openai.com/v1/models',
                    'headers': {'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY", "")}'},
                    'timeout': 10
                },
                'groq': {
                    'url': 'https://api.groq.com/openai/v1/models',
                    'headers': {'Authorization': f'Bearer {os.getenv("GROQ_API_KEY", "")}'},
                    'timeout': 10
                }
            },
            'system': {
                'cpu_warning_threshold': 80,
                'cpu_critical_threshold': 95,
                'memory_warning_threshold': 80,
                'memory_critical_threshold': 95,
                'disk_warning_threshold': 80,
                'disk_critical_threshold': 95
            },
            'thresholds': {
                'response_time_warning': 1000,  # ms
                'response_time_critical': 5000  # ms
            }
        }
    
    def check_database_health(self) -> HealthCheckResult:
        """Check PostgreSQL database health"""
        start_time = time.time()
        
        try:
            db_config = self.config['database']
            
            # Attempt connection
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                connect_timeout=db_config['timeout']
            )
            
            # Test query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # Get database stats
            cursor.execute("""
                SELECT 
                    pg_database_size(%s) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE datname = %s) as connections
            """, (db_config['database'], db_config['database']))
            
            db_size, connections = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service_name="database",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                message="Database connection successful",
                details={
                    'database_size_mb': round(db_size / (1024 * 1024), 2) if db_size else 0,
                    'active_connections': connections,
                    'host': db_config['host'],
                    'port': db_config['port']
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="database",
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"Database connection failed: {str(e)}",
                details={'error': str(e)}
            )
    
    def check_redis_health(self) -> HealthCheckResult:
        """Check Redis health"""
        start_time = time.time()
        
        try:
            redis_config = self.config['redis']
            
            # Connect to Redis
            r = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                db=redis_config['db'],
                socket_timeout=redis_config['timeout'],
                decode_responses=True
            )
            
            # Test ping
            pong = r.ping()
            
            # Get Redis info
            info = r.info()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service_name="redis",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                message="Redis connection successful",
                details={
                    'version': info.get('redis_version', 'unknown'),
                    'used_memory_mb': round(info.get('used_memory', 0) / (1024 * 1024), 2),
                    'connected_clients': info.get('connected_clients', 0),
                    'uptime_seconds': info.get('uptime_in_seconds', 0)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="redis",
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"Redis connection failed: {str(e)}",
                details={'error': str(e)}
            )
    
    def check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> HealthCheckResult:
        """Check individual service health via HTTP"""
        start_time = time.time()
        
        try:
            response = requests.get(
                service_config['url'],
                headers=service_config.get('headers', {}),
                timeout=service_config.get('timeout', 10)
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    service_data = response.json()
                except:
                    service_data = {'raw_response': response.text}
                
                return HealthCheckResult(
                    service_name=service_name,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Service is healthy",
                    details=service_data
                )
            else:
                return HealthCheckResult(
                    service_name=service_name,
                    status=HealthStatus.WARNING,
                    response_time_ms=response_time,
                    message=f"Service returned status {response.status_code}",
                    details={'status_code': response.status_code, 'response': response.text[:200]}
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=service_name,
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message="Service timeout",
                details={'timeout_seconds': service_config.get('timeout', 10)}
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=service_name,
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message="Service unreachable",
                details={'url': service_config['url']}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=service_name,
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"Service check failed: {str(e)}",
                details={'error': str(e)}
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine overall status
            thresholds = self.config['system']
            status = HealthStatus.HEALTHY
            warnings = []
            
            if cpu_percent >= thresholds['cpu_critical_threshold']:
                status = HealthStatus.CRITICAL
                warnings.append(f"CPU usage critical: {cpu_percent}%")
            elif cpu_percent >= thresholds['cpu_warning_threshold']:
                status = HealthStatus.WARNING
                warnings.append(f"CPU usage high: {cpu_percent}%")
            
            if memory_percent >= thresholds['memory_critical_threshold']:
                status = HealthStatus.CRITICAL
                warnings.append(f"Memory usage critical: {memory_percent}%")
            elif memory_percent >= thresholds['memory_warning_threshold']:
                if status != HealthStatus.CRITICAL:
                    status = HealthStatus.WARNING
                warnings.append(f"Memory usage high: {memory_percent}%")
            
            if disk_percent >= thresholds['disk_critical_threshold']:
                status = HealthStatus.CRITICAL
                warnings.append(f"Disk usage critical: {disk_percent:.1f}%")
            elif disk_percent >= thresholds['disk_warning_threshold']:
                if status != HealthStatus.CRITICAL:
                    status = HealthStatus.WARNING
                warnings.append(f"Disk usage high: {disk_percent:.1f}%")
            
            message = "System resources normal"
            if warnings:
                message = "; ".join(warnings)
            
            return HealthCheckResult(
                service_name="system_resources",
                status=status,
                response_time_ms=response_time,
                message=message,
                details={
                    'cpu_percent': round(cpu_percent, 1),
                    'memory_percent': round(memory_percent, 1),
                    'memory_available_gb': round(memory.available / (1024**3), 2),
                    'disk_percent': round(disk_percent, 1),
                    'disk_free_gb': round(disk.free / (1024**3), 2),
                    'process_count': process_count,
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="system_resources",
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"System resource check failed: {str(e)}",
                details={'error': str(e)}
            )
    
    def check_docker_containers(self) -> HealthCheckResult:
        """Check Docker containers status"""
        start_time = time.time()
        
        try:
            # Run docker ps command
            result = subprocess.run(
                ['docker', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise Exception(f"Docker command failed: {result.stderr}")
            
            containers = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    try:
                        container = json.loads(line)
                        containers.append({
                            'name': container.get('Names', ''),
                            'image': container.get('Image', ''),
                            'status': container.get('Status', ''),
                            'ports': container.get('Ports', '')
                        })
                    except json.JSONDecodeError:
                        pass
            
            response_time = (time.time() - start_time) * 1000
            
            # Check for specific containers
            expected_containers = ['postgres', 'redis', 'n8n']
            running_containers = [c['name'] for c in containers]
            
            missing_containers = []
            for expected in expected_containers:
                if not any(expected in name for name in running_containers):
                    missing_containers.append(expected)
            
            status = HealthStatus.HEALTHY
            message = f"Found {len(containers)} running containers"
            
            if missing_containers:
                status = HealthStatus.WARNING
                message = f"Missing expected containers: {', '.join(missing_containers)}"
            
            return HealthCheckResult(
                service_name="docker_containers",
                status=status,
                response_time_ms=response_time,
                message=message,
                details={
                    'container_count': len(containers),
                    'containers': containers,
                    'missing_containers': missing_containers
                }
            )
            
        except subprocess.TimeoutExpired:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="docker_containers",
                status=HealthStatus.WARNING,
                response_time_ms=response_time,
                message="Docker command timeout",
                details={'error': 'Command timeout'}
            )
        except FileNotFoundError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="docker_containers",
                status=HealthStatus.WARNING,
                response_time_ms=response_time,
                message="Docker not available",
                details={'error': 'Docker command not found'}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="docker_containers",
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"Docker check failed: {str(e)}",
                details={'error': str(e)}
            )
    
    def run_all_checks(self, parallel: bool = True) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        self.logger.info("Starting comprehensive health check...")
        
        if parallel:
            return self._run_checks_parallel()
        else:
            return self._run_checks_sequential()
    
    def _run_checks_sequential(self) -> Dict[str, HealthCheckResult]:
        """Run health checks sequentially"""
        results = {}
        
        # Database check
        results['database'] = self.check_database_health()
        
        # Redis check
        results['redis'] = self.check_redis_health()
        
        # System resources check
        results['system_resources'] = self.check_system_resources()
        
        # Docker containers check
        results['docker_containers'] = self.check_docker_containers()
        
        # Service checks
        for service_name, service_config in self.config['services'].items():
            results[service_name] = self.check_service_health(service_name, service_config)
        
        # External API checks
        for api_name, api_config in self.config['external_apis'].items():
            if api_config.get('headers', {}).get('Authorization', '').endswith(''):
                # Skip if no API key configured
                continue
            results[f"external_{api_name}"] = self.check_service_health(f"external_{api_name}", api_config)
        
        self.results = results
        return results
    
    def _run_checks_parallel(self) -> Dict[str, HealthCheckResult]:
        """Run health checks in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            
            # Submit all checks
            futures['database'] = executor.submit(self.check_database_health)
            futures['redis'] = executor.submit(self.check_redis_health)
            futures['system_resources'] = executor.submit(self.check_system_resources)
            futures['docker_containers'] = executor.submit(self.check_docker_containers)
            
            # Service checks
            for service_name, service_config in self.config['services'].items():
                futures[service_name] = executor.submit(
                    self.check_service_health, service_name, service_config
                )
            
            # External API checks
            for api_name, api_config in self.config['external_apis'].items():
                if api_config.get('headers', {}).get('Authorization', '').endswith(''):
                    continue
                futures[f"external_{api_name}"] = executor.submit(
                    self.check_service_health, f"external_{api_name}", api_config
                )
            
            # Collect results
            for future_name, future in futures.items():
                try:
                    results[future_name] = future.result(timeout=30)
                except Exception as e:
                    results[future_name] = HealthCheckResult(
                        service_name=future_name,
                        status=HealthStatus.UNKNOWN,
                        response_time_ms=0,
                        message=f"Health check failed: {str(e)}",
                        details={'error': str(e)}
                    )
        
        self.results = results
        return results
    
    def get_overall_status(self) -> Tuple[HealthStatus, str]:
        """Get overall system health status"""
        if not self.results:
            return HealthStatus.UNKNOWN, "No health checks performed"
        
        statuses = [result.status for result in self.results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            critical_services = [
                name for name, result in self.results.items() 
                if result.status == HealthStatus.CRITICAL
            ]
            return HealthStatus.CRITICAL, f"Critical issues in: {', '.join(critical_services)}"
        
        if HealthStatus.WARNING in statuses:
            warning_services = [
                name for name, result in self.results.items() 
                if result.status == HealthStatus.WARNING
            ]
            return HealthStatus.WARNING, f"Warnings in: {', '.join(warning_services)}"
        
        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN, "Some services have unknown status"
        
        return HealthStatus.HEALTHY, "All systems operational"
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        if not self.results:
            self.run_all_checks()
        
        overall_status, overall_message = self.get_overall_status()
        
        # Calculate summary statistics
        healthy_count = sum(1 for r in self.results.values() if r.status == HealthStatus.HEALTHY)
        warning_count = sum(1 for r in self.results.values() if r.status == HealthStatus.WARNING)
        critical_count = sum(1 for r in self.results.values() if r.status == HealthStatus.CRITICAL)
        unknown_count = sum(1 for r in self.results.values() if r.status == HealthStatus.UNKNOWN)
        
        avg_response_time = sum(r.response_time_ms for r in self.results.values()) / len(self.results)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status.value,
            'overall_message': overall_message,
            'summary': {
                'total_checks': len(self.results),
                'healthy': healthy_count,
                'warning': warning_count,
                'critical': critical_count,
                'unknown': unknown_count,
                'average_response_time_ms': round(avg_response_time, 2)
            },
            'services': {}
        }
        
        # Add detailed results
        for service_name, result in self.results.items():
            report['services'][service_name] = {
                'status': result.status.value,
                'message': result.message,
                'response_time_ms': result.response_time_ms,
                'details': result.details,
                'timestamp': result.timestamp.isoformat()
            }
        
        return report
    
    def save_report(self, filename: str = None) -> str:
        """Save health report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"
        
        report = self.generate_health_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Health report saved to: {filename}")
        return filename

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Content Factory Health Check")
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--output', '-o', help='Output file for report')
    parser.add_argument('--format', choices=['json', 'text'], default='text', 
                       help='Output format')
    parser.add_argument('--parallel', action='store_true', default=True,
                       help='Run checks in parallel')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger("health_check_main", level=log_level)
    
    # Initialize health checker
    health_checker = SystemHealthChecker()
    
    # Run health checks
    logger.info("Starting health checks...")
    results = health_checker.run_all_checks(parallel=args.parallel)
    
    # Generate report
    report = health_checker.generate_health_report()
    
    # Output results
    if args.format == 'json':
        if args.output:
            health_checker.save_report(args.output)
        else:
            print(json.dumps(report, indent=2))
    else:
        # Text format
        overall_status, overall_message = health_checker.get_overall_status()
        
        print(f"\n🏥 AI Content Factory Health Check Report")
        print(f"{'='*50}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Overall Status: {overall_status.value.upper()}")
        print(f"Message: {overall_message}")
        print(f"\n📊 Summary:")
        print(f"  Total Checks: {report['summary']['total_checks']}")
        print(f"  ✅ Healthy: {report['summary']['healthy']}")
        print(f"  ⚠️  Warning: {report['summary']['warning']}")
        print(f"  ❌ Critical: {report['summary']['critical']}")
        print(f"  ❓ Unknown: {report['summary']['unknown']}")
        print(f"  ⏱️  Avg Response: {report['summary']['average_response_time_ms']:.1f}ms")
        
        print(f"\n🔍 Service Details:")
        for service, details in report['services'].items():
            status_icon = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '❌',
                'unknown': '❓'
            }.get(details['status'], '❓')
            
            print(f"  {status_icon} {service}: {details['message']} ({details['response_time_ms']:.1f}ms)")
        
        if args.output:
            health_checker.save_report(args.output)
            print(f"\n📄 Full report saved to: {args.output}")

if __name__ == "__main__":
    main()