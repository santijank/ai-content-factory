"""
Service Status and Health Models
สำหรับจัดการสถานะของ services และระบบ
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json


class ServiceStatus(Enum):
    """สถานะของ service"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    ERROR = "error"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


class ServiceType(Enum):
    """ประเภทของ service"""
    TREND_MONITOR = "trend_monitor"
    CONTENT_ENGINE = "content_engine"
    PLATFORM_MANAGER = "platform_manager"
    DATABASE = "database"
    AI_SERVICE = "ai_service"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"


@dataclass
class ServiceHealthInfo:
    """ข้อมูลสุขภาพของ service"""
    name: str
    service_type: ServiceType
    status: ServiceStatus
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            'name': self.name,
            'service_type': self.service_type.value,
            'status': self.status.value,
            'last_check': self.last_check.isoformat(),
            'response_time_ms': self.response_time_ms,
            'error_message': self.error_message,
            'metadata': self.metadata
        }
    
    def is_healthy(self) -> bool:
        """ตรวจสอบว่า service สุขภาพดีหรือไม่"""
        return self.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    def update_status(self, status: ServiceStatus, error_message: str = None):
        """อัปเดตสถานะ"""
        self.status = status
        self.error_message = error_message
        self.last_check = datetime.now(timezone.utc)


@dataclass
class SystemHealth:
    """สุขภาพของระบบทั้งหมด"""
    services: Dict[str, ServiceHealthInfo] = field(default_factory=dict)
    overall_status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_service(self, name: str, health_info: ServiceHealthInfo):
        """เพิ่ม service health info"""
        self.services[name] = health_info
        self._update_overall_status()
    
    def update_service_status(self, name: str, status: ServiceStatus, error_message: str = None):
        """อัปเดตสถานะของ service"""
        if name in self.services:
            self.services[name].update_status(status, error_message)
            self._update_overall_status()
    
    def _update_overall_status(self):
        """คำนวณสถานะรวมของระบบ"""
        if not self.services:
            self.overall_status = ServiceStatus.UNKNOWN
            return
        
        statuses = [service.status for service in self.services.values()]
        
        # ถ้ามี error หรือ unhealthy
        if ServiceStatus.ERROR in statuses or ServiceStatus.UNHEALTHY in statuses:
            self.overall_status = ServiceStatus.UNHEALTHY
        # ถ้ามี degraded
        elif ServiceStatus.DEGRADED in statuses:
            self.overall_status = ServiceStatus.DEGRADED
        # ถ้าทุกตัวเป็น healthy
        elif all(status == ServiceStatus.HEALTHY for status in statuses):
            self.overall_status = ServiceStatus.HEALTHY
        # ถ้ามี unknown หรือ starting
        elif ServiceStatus.UNKNOWN in statuses or ServiceStatus.STARTING in statuses:
            self.overall_status = ServiceStatus.STARTING
        else:
            self.overall_status = ServiceStatus.DEGRADED
        
        self.last_check = datetime.now(timezone.utc)
    
    @property
    def is_healthy(self) -> bool:
        """ตรวจสอบว่าระบบสุขภาพดีหรือไม่"""
        return self.overall_status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    def get_unhealthy_services(self) -> List[ServiceHealthInfo]:
        """ดึงรายการ services ที่ไม่สุขภาพดี"""
        return [
            service for service in self.services.values()
            if service.status in [ServiceStatus.ERROR, ServiceStatus.UNHEALTHY]
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """สร้างสรุปสถานะ"""
        status_counts = {}
        for status in ServiceStatus:
            status_counts[status.value] = 0
        
        for service in self.services.values():
            status_counts[service.status.value] += 1
        
        return {
            'overall_status': self.overall_status.value,
            'total_services': len(self.services),
            'healthy_services': status_counts[ServiceStatus.HEALTHY.value],
            'degraded_services': status_counts[ServiceStatus.DEGRADED.value],
            'unhealthy_services': status_counts[ServiceStatus.UNHEALTHY.value],
            'error_services': status_counts[ServiceStatus.ERROR.value],
            'last_check': self.last_check.isoformat(),
            'status_breakdown': status_counts
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            'overall_status': self.overall_status.value,
            'last_check': self.last_check.isoformat(),
            'services': {name: service.to_dict() for name, service in self.services.items()},
            'summary': self.get_summary()
        }
    
    def to_json(self) -> str:
        """แปลงเป็น JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass 
class PerformanceMetrics:
    """Metrics การทำงานของระบบ"""
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    network_io_bytes: Optional[int] = None
    active_connections: Optional[int] = None
    request_count: Optional[int] = None
    average_response_time_ms: Optional[float] = None
    error_rate_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_usage_mb': self.memory_usage_mb,
            'disk_usage_percent': self.disk_usage_percent,
            'network_io_bytes': self.network_io_bytes,
            'active_connections': self.active_connections,
            'request_count': self.request_count,
            'average_response_time_ms': self.average_response_time_ms,
            'error_rate_percent': self.error_rate_percent
        }


@dataclass
class ServiceMetrics:
    """Metrics เฉพาะของแต่ละ service"""
    service_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def add_custom_metric(self, key: str, value: Any):
        """เพิ่ม custom metric"""
        self.custom_metrics[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            'service_name': self.service_name,
            'timestamp': self.timestamp.isoformat(),
            'performance': self.performance.to_dict(),
            'custom_metrics': self.custom_metrics
        }


class HealthChecker:
    """Class สำหรับตรวจสอบสุขภาพ services"""
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, service_name: str, check_function):
        """ลงทะเบียน health check function"""
        self.checks[service_name] = check_function
    
    async def run_check(self, service_name: str) -> ServiceHealthInfo:
        """รัน health check สำหรับ service"""
        if service_name not in self.checks:
            return ServiceHealthInfo(
                name=service_name,
                service_type=ServiceType.SYSTEM,
                status=ServiceStatus.UNKNOWN,
                error_message=f"No health check registered for {service_name}"
            )
        
        try:
            start_time = datetime.now()
            result = await self.checks[service_name]()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if isinstance(result, ServiceHealthInfo):
                result.response_time_ms = response_time
                return result
            elif isinstance(result, bool):
                return ServiceHealthInfo(
                    name=service_name,
                    service_type=ServiceType.SYSTEM,
                    status=ServiceStatus.HEALTHY if result else ServiceStatus.UNHEALTHY,
                    response_time_ms=response_time
                )
            else:
                return ServiceHealthInfo(
                    name=service_name,
                    service_type=ServiceType.SYSTEM,
                    status=ServiceStatus.HEALTHY,
                    response_time_ms=response_time,
                    metadata=result if isinstance(result, dict) else {}
                )
                
        except Exception as e:
            return ServiceHealthInfo(
                name=service_name,
                service_type=ServiceType.SYSTEM,
                status=ServiceStatus.ERROR,
                error_message=str(e)
            )
    
    async def run_all_checks(self) -> SystemHealth:
        """รัน health checks ทั้งหมด"""
        system_health = SystemHealth()
        
        for service_name in self.checks:
            health_info = await self.run_check(service_name)
            system_health.add_service(service_name, health_info)
        
        return system_health


# Utility functions
def create_service_health(name: str, 
                         service_type: ServiceType,
                         status: ServiceStatus = ServiceStatus.HEALTHY,
                         **metadata) -> ServiceHealthInfo:
    """สร้าง ServiceHealthInfo อย่างง่าย"""
    return ServiceHealthInfo(
        name=name,
        service_type=service_type,
        status=status,
        metadata=metadata
    )


def get_status_emoji(status: ServiceStatus) -> str:
    """ดึง emoji สำหรับ status"""
    emoji_map = {
        ServiceStatus.HEALTHY: "✅",
        ServiceStatus.DEGRADED: "⚠️",
        ServiceStatus.UNHEALTHY: "❌",
        ServiceStatus.ERROR: "💥",
        ServiceStatus.UNKNOWN: "❓",
        ServiceStatus.STARTING: "🔄",
        ServiceStatus.STOPPING: "⏹️"
    }
    return emoji_map.get(status, "❓")


# Example usage
if __name__ == "__main__":
    # สร้าง system health
    system_health = SystemHealth()
    
    # เพิ่ม services
    system_health.add_service("database", create_service_health(
        "database", ServiceType.DATABASE, ServiceStatus.HEALTHY,
        connections=10, response_time_avg=50.0
    ))
    
    system_health.add_service("content_engine", create_service_health(
        "content_engine", ServiceType.CONTENT_ENGINE, ServiceStatus.DEGRADED,
        ai_model_load=0.8, queue_size=5
    ))
    
    system_health.add_service("platform_manager", create_service_health(
        "platform_manager", ServiceType.PLATFORM_MANAGER, ServiceStatus.ERROR,
        error_message="API key expired"
    ))
    
    # แสดงสรุป
    print(f"Overall Status: {get_status_emoji(system_health.overall_status)} {system_health.overall_status.value}")
    print(f"Total Services: {len(system_health.services)}")
    print(f"Healthy: {system_health.get_summary()['healthy_services']}")
    print(f"Unhealthy: {system_health.get_summary()['unhealthy_services']}")
    
    # แสดง JSON
    print("\nSystem Health JSON:")
    print(system_health.to_json())