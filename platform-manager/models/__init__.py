"""
AI Content Factory - Platform Manager Models Package
==================================================

This package contains all data models and schemas specific to the platform
manager service. These models extend the shared models with platform-manager
specific functionality and database mappings.

Models included:
- PlatformType: Enhanced platform type with manager-specific attributes
- UploadMetadata: Extended upload metadata with tracking information
- UploadJob: Upload job management and tracking
- PlatformAccount: Platform account management with credentials
- UploadBatch: Batch upload operations
- PerformanceReport: Performance reporting and analytics
- ContentOptimization: Content optimization settings and results
- ScheduledUpload: Scheduled upload management
- WebhookEvent: Platform webhook event handling
- ApiQuota: API quota tracking and management

Architecture:
    Domain-Driven Design - Models represent business domain concepts
    Repository Pattern - Data access abstraction
    Event Sourcing - Upload event tracking and history
    CQRS - Separate read/write models for optimization

Usage:
    from platform_manager.models import UploadJob, PlatformAccount
    
    job = UploadJob.create(file_path="video.mp4", platform="youtube")
    account = PlatformAccount.get_active("youtube")
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import json

# Import base models from shared package
from shared.models.base_model import BaseDataClass, BasePydanticModel, StatusEnum
from shared.models.platform_model import (
    PlatformTypeEnum, UploadStatusEnum, ContentVisibilityEnum,
    PlatformMetadata, UploadTask, PlatformAnalytics
)
from shared.models.content_model import ContentTypeEnum, ContentFormatEnum

# Package version
__version__ = "1.0.0"

# Export all models
__all__ = [
    # Enhanced platform models
    'PlatformType',
    'UploadMetadata', 
    'UploadJob',
    'PlatformAccount',
    'UploadBatch',
    'PerformanceReport',
    'ContentOptimization',
    'ScheduledUpload',
    'WebhookEvent',
    'ApiQuota',
    
    # Enumerations
    'JobStatusEnum',
    'OptimizationTypeEnum',
    'WebhookTypeEnum',
    'QuotaTypeEnum',
    'AccountStatusEnum',
    
    # Utility classes
    'JobMetrics',
    'OptimizationResult',
    'QuotaUsage',
    'EventPayload',
    
    # Model factories
    'create_upload_job',
    'create_platform_account', 
    'create_scheduled_upload',
    'create_performance_report',
    
    # Model validators
    'validate_upload_job',
    'validate_platform_account',
    'validate_optimization_settings',
    
    # Model utilities
    'get_model_schema',
    'serialize_model',
    'deserialize_model'
]

# Extended enumerations
class JobStatusEnum(str, Enum):
    """Extended job status enumeration."""
    CREATED = "created"
    QUEUED = "queued"
    PREPARING = "preparing"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    OPTIMIZING = "optimizing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    SCHEDULED = "scheduled"

class OptimizationTypeEnum(str, Enum):
    """Content optimization types."""
    RESOLUTION = "resolution"
    BITRATE = "bitrate"
    COMPRESSION = "compression"
    THUMBNAIL = "thumbnail"
    METADATA = "metadata"
    SUBTITLES = "subtitles"
    WATERMARK = "watermark"
    ASPECT_RATIO = "aspect_ratio"

class WebhookTypeEnum(str, Enum):
    """Webhook event types."""
    UPLOAD_STARTED = "upload_started"
    UPLOAD_PROGRESS = "upload_progress"
    UPLOAD_COMPLETED = "upload_completed"
    UPLOAD_FAILED = "upload_failed"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    CONTENT_PUBLISHED = "content_published"
    ANALYTICS_UPDATED = "analytics_updated"

class QuotaTypeEnum(str, Enum):
    """API quota types."""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    UPLOAD_SIZE_PER_DAY = "upload_size_per_day"
    UPLOAD_COUNT_PER_DAY = "upload_count_per_day"

class AccountStatusEnum(str, Enum):
    """Platform account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    RATE_LIMITED = "rate_limited"
    EXPIRED = "expired"
    PENDING_VERIFICATION = "pending_verification"

@dataclass
class JobMetrics(BaseDataClass):
    """Upload job performance metrics."""
    
    file_size: int = 0
    upload_speed: float = 0.0  # MB/s
    processing_time: float = 0.0  # seconds
    total_time: float = 0.0  # seconds
    retry_count: int = 0
    bandwidth_used: int = 0  # bytes
    cpu_usage: float = 0.0  # percentage
    memory_usage: int = 0  # bytes
    error_count: int = 0
    
    def calculate_efficiency(self) -> float:
        """Calculate upload efficiency score (0-100)."""
        if self.total_time <= 0:
            return 0.0
        
        base_score = 50.0
        
        # Speed bonus (higher is better)
        if self.upload_speed > 10:  # > 10 MB/s
            base_score += 30
        elif self.upload_speed > 5:  # > 5 MB/s
            base_score += 20
        elif self.upload_speed > 1:  # > 1 MB/s
            base_score += 10
        
        # Retry penalty
        base_score -= (self.retry_count * 10)
        
        # Error penalty
        base_score -= (self.error_count * 5)
        
        return max(0.0, min(100.0, base_score))

@dataclass
class OptimizationResult(BaseDataClass):
    """Content optimization result."""
    
    optimization_type: OptimizationTypeEnum
    original_value: Any = None
    optimized_value: Any = None
    improvement_percentage: float = 0.0
    file_size_reduction: int = 0  # bytes
    quality_score: float = 0.0  # 0-100
    processing_time: float = 0.0  # seconds
    success: bool = True
    error_message: Optional[str] = None
    
    def to_summary(self) -> Dict[str, Any]:
        """Get optimization summary."""
        return {
            'type': self.optimization_type.value,
            'improvement': f"{self.improvement_percentage:.1f}%",
            'size_reduction': f"{self.file_size_reduction / 1024 / 1024:.1f} MB",
            'quality': f"{self.quality_score:.1f}/100",
            'success': self.success
        }

@dataclass
class QuotaUsage(BaseDataClass):
    """API quota usage tracking."""
    
    quota_type: QuotaTypeEnum
    limit: int
    used: int = 0
    remaining: int = 0
    reset_time: Optional[datetime] = None
    window_start: Optional[datetime] = None
    
    def __post_init__(self):
        if self.remaining == 0 and self.limit > 0:
            self.remaining = self.limit - self.used
    
    def is_exceeded(self) -> bool:
        """Check if quota is exceeded."""
        return self.used >= self.limit
    
    def usage_percentage(self) -> float:
        """Get usage percentage."""
        if self.limit <= 0:
            return 0.0
        return (self.used / self.limit) * 100
    
    def time_until_reset(self) -> Optional[timedelta]:
        """Get time until quota resets."""
        if self.reset_time:
            now = datetime.utcnow()
            if self.reset_time > now:
                return self.reset_time - now
        return None

@dataclass
class EventPayload(BaseDataClass):
    """Webhook event payload."""
    
    event_type: WebhookTypeEnum
    job_id: str
    platform: PlatformTypeEnum
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_webhook_payload(self) -> Dict[str, Any]:
        """Convert to webhook payload format."""
        return {
            'event': self.event_type.value,
            'job_id': self.job_id,
            'platform': self.platform.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'user_id': self.user_id,
            'metadata': self.metadata
        }

# Enhanced models extending shared models

@dataclass  
class PlatformType(BaseDataClass):
    """Enhanced platform type with manager-specific attributes."""
    
    platform: PlatformTypeEnum
    display_name: str = ""
    icon_url: Optional[str] = None
    color: str = "#000000"
    is_enabled: bool = True
    priority: int = 1  # 1 = highest priority
    max_concurrent_uploads: int = 3
    default_visibility: ContentVisibilityEnum = ContentVisibilityEnum.PUBLIC
    supported_formats: List[ContentFormatEnum] = field(default_factory=list)
    features: Dict[str, bool] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.platform.value.replace('_', ' ').title()

@dataclass
class UploadMetadata(PlatformMetadata):
    """Extended upload metadata with tracking information."""
    
    # Additional tracking fields
    upload_id: str = field(default_factory=lambda: str(uuid4()))
    source_file_path: str = ""
    optimized_file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    preview_url: Optional[str] = None
    
    # Job tracking
    job_id: Optional[str] = None
    batch_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Performance tracking
    file_size: int = 0
    upload_duration: Optional[float] = None
    processing_duration: Optional[float] = None
    
    # Quality metrics
    quality_score: float = 0.0
    optimization_applied: List[OptimizationTypeEnum] = field(default_factory=list)
    
    def add_optimization(self, optimization: OptimizationTypeEnum):
        """Add optimization type to the list."""
        if optimization not in self.optimization_applied:
            self.optimization_applied.append(optimization)

@dataclass
class UploadJob(BaseDataClass):
    """Upload job management and tracking."""
    
    job_id: str = field(default_factory=lambda: str(uuid4()))
    file_path: str = ""
    platforms: List[PlatformTypeEnum] = field(default_factory=list)
    metadata: UploadMetadata = field(default_factory=UploadMetadata)
    status: JobStatusEnum = JobStatusEnum.CREATED
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None
    
    # Progress tracking
    progress: float = 0.0  # 0.0 to 1.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    
    # Results
    upload_results: Dict[str, Any] = field(default_factory=dict)
    platform_ids: Dict[str, str] = field(default_factory=dict)  # platform -> platform_id
    platform_urls: Dict[str, str] = field(default_factory=dict)  # platform -> url
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Performance
    metrics: Optional[JobMetrics] = None
    
    # Configuration
    priority: int = 5  # 1-10, higher is more priority
    timeout: int = 3600  # seconds
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = JobMetrics()
    
    def start_job(self):
        """Mark job as started."""
        self.status = JobStatusEnum.QUEUED
        self.started_at = datetime.utcnow()
        self.progress = 0.0
    
    def update_progress(self, progress: float, step: str = ""):
        """Update job progress."""
        self.progress = max(0.0, min(1.0, progress))
        if step:
            self.current_step = step
        self.update_timestamp()
    
    def complete_job(self, success: bool = True):
        """Mark job as completed."""
        self.status = JobStatusEnum.PUBLISHED if success else JobStatusEnum.FAILED
        self.completed_at = datetime.utcnow()
        self.progress = 1.0
        
        if self.metrics and self.started_at and self.completed_at:
            self.metrics.total_time = (self.completed_at - self.started_at).total_seconds()
    
    def fail_job(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatusEnum.FAILED
        self.error_message = error_message
        self.retry_count += 1
        self.completed_at = datetime.utcnow()
    
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries and self.status == JobStatusEnum.FAILED
    
    def get_duration(self) -> Optional[timedelta]:
        """Get job duration if completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def get_eta(self) -> Optional[datetime]:
        """Estimate completion time based on progress."""
        if not self.started_at or self.progress <= 0:
            return None
        
        elapsed = datetime.utcnow() - self.started_at
        total_estimated = elapsed / self.progress
        return self.started_at + total_estimated

@dataclass
class PlatformAccount(BaseDataClass):
    """Platform account management with credentials."""
    
    account_id: str = field(default_factory=lambda: str(uuid4()))
    platform: PlatformTypeEnum
    username: str = ""
    display_name: str = ""
    email: Optional[str] = None
    
    # Account status
    status: AccountStatusEnum = AccountStatusEnum.PENDING_VERIFICATION
    is_verified: bool = False
    is_monetized: bool = False
    
    # Credentials (encrypted)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
    # Token management
    token_expires_at: Optional[datetime] = None
    last_token_refresh: Optional[datetime] = None
    
    # Account info
    follower_count: int = 0
    following_count: int = 0
    video_count: int = 0
    total_views: int = 0
    
    # Usage tracking
    quota_usage: Dict[str, QuotaUsage] = field(default_factory=dict)
    last_used: Optional[datetime] = None
    
    # Settings
    default_settings: Dict[str, Any] = field(default_factory=dict)
    upload_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if account is active and ready for uploads."""
        return (
            self.status == AccountStatusEnum.ACTIVE and
            self.is_verified and
            not self.is_token_expired() and
            not self.is_rate_limited()
        )
    
    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.token_expires_at:
            return False
        return datetime.utcnow() > self.token_expires_at
    
    def is_rate_limited(self) -> bool:
        """Check if account is rate limited."""
        return self.status == AccountStatusEnum.RATE_LIMITED
    
    def update_quota_usage(self, quota_type: QuotaTypeEnum, used: int):
        """Update quota usage."""
        if quota_type.value not in self.quota_usage:
            # Create new quota usage tracking
            self.quota_usage[quota_type.value] = QuotaUsage(
                quota_type=quota_type,
                limit=self._get_default_limit(quota_type),
                used=used
            )
        else:
            self.quota_usage[quota_type.value].used = used
            self.quota_usage[quota_type.value].remaining = (
                self.quota_usage[quota_type.value].limit - used
            )
    
    def _get_default_limit(self, quota_type: QuotaTypeEnum) -> int:
        """Get default quota limit for platform."""
        defaults = {
            QuotaTypeEnum.REQUESTS_PER_MINUTE: 60,
            QuotaTypeEnum.REQUESTS_PER_HOUR: 1000,
            QuotaTypeEnum.REQUESTS_PER_DAY: 10000,
            QuotaTypeEnum.UPLOAD_SIZE_PER_DAY: 10 * 1024**3,  # 10 GB
            QuotaTypeEnum.UPLOAD_COUNT_PER_DAY: 100
        }
        return defaults.get(quota_type, 1000)

@dataclass
class UploadBatch(BaseDataClass):
    """Batch upload operations."""
    
    batch_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    
    # Jobs in this batch
    job_ids: List[str] = field(default_factory=list)
    total_jobs: int = 0
    
    # Status tracking
    status: StatusEnum = StatusEnum.PENDING
    completed_jobs: int = 0
    failed_jobs: int = 0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Configuration
    max_concurrent: int = 3
    auto_retry_failed: bool = True
    
    # Progress
    overall_progress: float = 0.0
    
    # Results summary
    results_summary: Dict[str, Any] = field(default_factory=dict)
    
    def add_job(self, job_id: str):
        """Add job to batch."""
        if job_id not in self.job_ids:
            self.job_ids.append(job_id)
            self.total_jobs = len(self.job_ids)
    
    def remove_job(self, job_id: str):
        """Remove job from batch."""
        if job_id in self.job_ids:
            self.job_ids.remove(job_id)
            self.total_jobs = len(self.job_ids)
    
    def update_progress(self):
        """Update overall batch progress."""
        if self.total_jobs > 0:
            self.overall_progress = (self.completed_jobs + self.failed_jobs) / self.total_jobs
        
        # Update status
        if self.completed_jobs + self.failed_jobs >= self.total_jobs:
            self.status = StatusEnum.COMPLETED
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
        elif self.completed_jobs + self.failed_jobs > 0:
            self.status = StatusEnum.PROCESSING
    
    def get_success_rate(self) -> float:
        """Get batch success rate."""
        total_finished = self.completed_jobs + self.failed_jobs
        if total_finished > 0:
            return (self.completed_jobs / total_finished) * 100
        return 0.0

# Model factory functions

def create_upload_job(
    file_path: str,
    platforms: List[str],
    metadata: Dict[str, Any] = None,
    **kwargs
) -> UploadJob:
    """Create a new upload job."""
    
    platform_enums = [PlatformTypeEnum(p) for p in platforms]
    
    upload_metadata = UploadMetadata(
        source_file_path=file_path,
        **(metadata or {})
    )
    
    return UploadJob(
        file_path=file_path,
        platforms=platform_enums,
        metadata=upload_metadata,
        **kwargs
    )

def create_platform_account(
    platform: str,
    username: str,
    credentials: Dict[str, str] = None,
    **kwargs
) -> PlatformAccount:
    """Create a new platform account."""
    
    platform_enum = PlatformTypeEnum(platform)
    
    account = PlatformAccount(
        platform=platform_enum,
        username=username,
        **kwargs
    )
    
    # Set credentials if provided
    if credentials:
        for key, value in credentials.items():
            if hasattr(account, key):
                setattr(account, key, value)
    
    return account

def create_scheduled_upload(
    job: UploadJob,
    scheduled_time: datetime,
    **kwargs
) -> 'ScheduledUpload':
    """Create a scheduled upload."""
    
    return ScheduledUpload(
        job_id=job.job_id,
        scheduled_time=scheduled_time,
        job_data=job.to_dict(),
        **kwargs
    )

def create_performance_report(
    period_start: datetime,
    period_end: datetime,
    platforms: List[str] = None,
    **kwargs
) -> 'PerformanceReport':
    """Create a performance report."""
    
    platform_enums = [PlatformTypeEnum(p) for p in platforms] if platforms else []
    
    return PerformanceReport(
        period_start=period_start,
        period_end=period_end,
        platforms=platform_enums,
        **kwargs
    )

# Additional models

@dataclass
class PerformanceReport(BaseDataClass):
    """Performance reporting and analytics."""
    
    report_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    
    # Time period
    period_start: datetime
    period_end: datetime
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Scope
    platforms: List[PlatformTypeEnum] = field(default_factory=list)
    user_ids: List[str] = field(default_factory=list)
    job_ids: List[str] = field(default_factory=list)
    
    # Metrics
    total_uploads: int = 0
    successful_uploads: int = 0
    failed_uploads: int = 0
    total_upload_time: float = 0.0  # seconds
    total_file_size: int = 0  # bytes
    
    # Platform breakdown
    platform_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Performance metrics
    average_upload_speed: float = 0.0  # MB/s
    average_processing_time: float = 0.0  # seconds
    success_rate: float = 0.0  # percentage
    
    # Cost analysis
    total_cost: float = 0.0
    cost_per_upload: float = 0.0
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Trends
    daily_metrics: List[Dict[str, Any]] = field(default_factory=list)
    hourly_distribution: Dict[int, int] = field(default_factory=dict)
    
    def calculate_metrics(self):
        """Calculate derived metrics."""
        # Success rate
        if self.total_uploads > 0:
            self.success_rate = (self.successful_uploads / self.total_uploads) * 100
        
        # Average upload speed
        if self.total_upload_time > 0:
            total_size_mb = self.total_file_size / (1024 * 1024)
            self.average_upload_speed = total_size_mb / (self.total_upload_time / 60)
        
        # Cost per upload
        if self.total_uploads > 0:
            self.cost_per_upload = self.total_cost / self.total_uploads
    
    def add_platform_metrics(self, platform: str, metrics: Dict[str, Any]):
        """Add metrics for a specific platform."""
        self.platform_metrics[platform] = metrics
    
    def get_top_platforms(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing platforms."""
        sorted_platforms = sorted(
            self.platform_metrics.items(),
            key=lambda x: x[1].get('success_rate', 0),
            reverse=True
        )
        
        return [
            {'platform': platform, 'metrics': metrics}
            for platform, metrics in sorted_platforms[:limit]
        ]

@dataclass
class ContentOptimization(BaseDataClass):
    """Content optimization settings and results."""
    
    optimization_id: str = field(default_factory=lambda: str(uuid4()))
    job_id: str = ""
    
    # Original content info
    original_file_path: str = ""
    original_file_size: int = 0
    original_duration: Optional[float] = None
    original_resolution: Optional[str] = None
    original_bitrate: Optional[int] = None
    
    # Optimization settings
    target_platform: PlatformTypeEnum
    optimization_types: List[OptimizationTypeEnum] = field(default_factory=list)
    quality_preference: str = "balanced"  # quality, balanced, size
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    optimized_file_path: Optional[str] = None
    optimized_file_size: int = 0
    optimization_results: List[OptimizationResult] = field(default_factory=list)
    
    # Performance
    processing_time: float = 0.0
    size_reduction_percentage: float = 0.0
    quality_score: float = 0.0
    
    # Status
    status: StatusEnum = StatusEnum.PENDING
    error_message: Optional[str] = None
    
    def add_result(self, result: OptimizationResult):
        """Add optimization result."""
        self.optimization_results.append(result)
    
    def calculate_overall_improvement(self) -> float:
        """Calculate overall improvement percentage."""
        if not self.optimization_results:
            return 0.0
        
        improvements = [r.improvement_percentage for r in self.optimization_results if r.success]
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def get_file_size_reduction(self) -> int:
        """Get total file size reduction in bytes."""
        return self.original_file_size - self.optimized_file_size
    
    def calculate_size_reduction_percentage(self) -> float:
        """Calculate size reduction percentage."""
        if self.original_file_size > 0:
            reduction = self.get_file_size_reduction()
            return (reduction / self.original_file_size) * 100
        return 0.0

@dataclass
class ScheduledUpload(BaseDataClass):
    """Scheduled upload management."""
    
    schedule_id: str = field(default_factory=lambda: str(uuid4()))
    job_id: str = ""
    
    # Scheduling
    scheduled_time: datetime
    timezone: str = "UTC"
    recurring: bool = False
    recurrence_pattern: Optional[str] = None  # cron-like pattern
    
    # Job data
    job_data: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: StatusEnum = StatusEnum.PENDING
    executed_at: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    
    # Results
    execution_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Configuration
    max_executions: Optional[int] = None
    execution_count: int = 0
    retry_failed: bool = True
    
    def is_due(self) -> bool:
        """Check if upload is due for execution."""
        if self.status != StatusEnum.PENDING:
            return False
        
        now = datetime.utcnow()
        return now >= self.scheduled_time
    
    def execute(self, result: Dict[str, Any]):
        """Mark as executed with results."""
        self.status = StatusEnum.COMPLETED
        self.executed_at = datetime.utcnow()
        self.execution_count += 1
        self.execution_results.append(result)
        
        # Schedule next execution if recurring
        if self.recurring and self.recurrence_pattern:
            self.next_execution = self._calculate_next_execution()
            if self.max_executions is None or self.execution_count < self.max_executions:
                self.status = StatusEnum.PENDING
    
    def _calculate_next_execution(self) -> Optional[datetime]:
        """Calculate next execution time for recurring schedules."""
        # Simplified implementation - in practice, use a proper cron library
        if not self.recurrence_pattern:
            return None
        
        # Example: daily recurrence
        if self.recurrence_pattern == "daily":
            return self.scheduled_time + timedelta(days=1)
        
        return None

@dataclass
class WebhookEvent(BaseDataClass):
    """Platform webhook event handling."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    webhook_type: WebhookTypeEnum
    platform: PlatformTypeEnum
    
    # Event data
    payload: EventPayload
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    
    # Processing
    received_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    processing_status: StatusEnum = StatusEnum.PENDING
    
    # Response
    response_sent: bool = False
    response_data: Optional[Dict[str, Any]] = None
    
    # Retry handling
    retry_count: int = 0
    max_retries: int = 3
    
    def process(self, result: Dict[str, Any] = None):
        """Mark event as processed."""
        self.processing_status = StatusEnum.COMPLETED
        self.processed_at = datetime.utcnow()
        
        if result:
            self.response_data = result
    
    def fail_processing(self, error_message: str):
        """Mark processing as failed."""
        self.processing_status = StatusEnum.FAILED
        self.retry_count += 1
        
        if not self.response_data:
            self.response_data = {}
        self.response_data['error'] = error_message
    
    def can_retry(self) -> bool:
        """Check if event processing can be retried."""
        return (
            self.retry_count < self.max_retries and
            self.processing_status == StatusEnum.FAILED
        )

@dataclass
class ApiQuota(BaseDataClass):
    """API quota tracking and management."""
    
    quota_id: str = field(default_factory=lambda: str(uuid4()))
    platform: PlatformTypeEnum
    account_id: str = ""
    
    # Quota definition
    quota_type: QuotaTypeEnum
    limit: int
    window_size: int = 3600  # seconds
    
    # Usage tracking
    usage_records: List[QuotaUsage] = field(default_factory=list)
    current_usage: int = 0
    
    # Status
    is_exceeded: bool = False
    exceeded_at: Optional[datetime] = None
    reset_at: Optional[datetime] = None
    
    # Configuration
    warning_threshold: float = 0.8  # 80%
    auto_reset: bool = True
    
    def record_usage(self, amount: int = 1):
        """Record API usage."""
        now = datetime.utcnow()
        
        # Clean old records outside window
        cutoff_time = now - timedelta(seconds=self.window_size)
        self.usage_records = [
            record for record in self.usage_records 
            if record.created_at > cutoff_time
        ]
        
        # Add new usage record
        usage = QuotaUsage(
            quota_type=self.quota_type,
            limit=self.limit,
            used=amount
        )
        self.usage_records.append(usage)
        
        # Update current usage
        self.current_usage = sum(record.used for record in self.usage_records)
        
        # Check if exceeded
        if self.current_usage >= self.limit and not self.is_exceeded:
            self.is_exceeded = True
            self.exceeded_at = now
            
            # Set reset time
            if self.auto_reset:
                self.reset_at = now + timedelta(seconds=self.window_size)
    
    def get_remaining(self) -> int:
        """Get remaining quota."""
        return max(0, self.limit - self.current_usage)
    
    def get_usage_percentage(self) -> float:
        """Get usage as percentage."""
        return (self.current_usage / self.limit * 100) if self.limit > 0 else 0
    
    def is_warning_level(self) -> bool:
        """Check if usage is at warning level."""
        return self.get_usage_percentage() >= (self.warning_threshold * 100)
    
    def reset_quota(self):
        """Reset quota usage."""
        self.usage_records.clear()
        self.current_usage = 0
        self.is_exceeded = False
        self.exceeded_at = None
        self.reset_at = None

# Model validation functions

def validate_upload_job(job: UploadJob) -> List[str]:
    """Validate upload job data."""
    errors = []
    
    if not job.file_path:
        errors.append("File path is required")
    
    if not job.platforms:
        errors.append("At least one platform is required")
    
    if job.priority < 1 or job.priority > 10:
        errors.append("Priority must be between 1 and 10")
    
    if job.timeout <= 0:
        errors.append("Timeout must be positive")
    
    return errors

def validate_platform_account(account: PlatformAccount) -> List[str]:
    """Validate platform account data."""
    errors = []
    
    if not account.username:
        errors.append("Username is required")
    
    if not account.platform:
        errors.append("Platform is required")
    
    if account.email and "@" not in account.email:
        errors.append("Invalid email format")
    
    return errors

def validate_optimization_settings(optimization: ContentOptimization) -> List[str]:
    """Validate optimization settings."""
    errors = []
    
    if not optimization.original_file_path:
        errors.append("Original file path is required")
    
    if not optimization.target_platform:
        errors.append("Target platform is required")
    
    if not optimization.optimization_types:
        errors.append("At least one optimization type is required")
    
    return errors

# Model utilities

def get_model_schema(model_class) -> Dict[str, Any]:
    """Get JSON schema for a model class."""
    # Simplified schema generation
    return {
        'type': 'object',
        'properties': {
            field.name: {'type': 'string'}  # Simplified
            for field in model_class.__dataclass_fields__.values()
        },
        'required': [
            field.name for field in model_class.__dataclass_fields__.values()
            if field.default == dataclass.MISSING and field.default_factory == dataclass.MISSING
        ]
    }

def serialize_model(model_instance) -> Dict[str, Any]:
    """Serialize model instance to dictionary."""
    if hasattr(model_instance, 'to_dict'):
        return model_instance.to_dict()
    elif hasattr(model_instance, '__dict__'):
        return model_instance.__dict__.copy()
    else:
        return {}

def deserialize_model(model_class, data: Dict[str, Any]):
    """Deserialize dictionary to model instance."""
    if hasattr(model_class, 'from_dict'):
        return model_class.from_dict(data)
    else:
        return model_class(**data)

# Model registry for dynamic access
MODEL_REGISTRY = {
    'upload_job': UploadJob,
    'platform_account': PlatformAccount,
    'upload_batch': UploadBatch,
    'performance_report': PerformanceReport,
    'content_optimization': ContentOptimization,
    'scheduled_upload': ScheduledUpload,
    'webhook_event': WebhookEvent,
    'api_quota': ApiQuota
}

def get_model_class(model_name: str) -> Optional[type]:
    """Get model class by name."""
    return MODEL_REGISTRY.get(model_name)

def list_model_names() -> List[str]:
    """List all available model names."""
    return list(MODEL_REGISTRY.keys())

# Version and metadata
__author__ = "AI Content Factory Team"
__email__ = "dev@aicontentfactory.com"  
__status__ = "Production"
__last_updated__ = "2024-01-15"