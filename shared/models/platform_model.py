"""
AI Content Factory - Platform Models
===================================

Shared models for platform integration, upload management, and performance tracking.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator

from .base_model import BaseDataClass, BasePydanticModel, StatusEnum, validate_non_empty_string, validate_url


class PlatformTypeEnum(str, Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    PINTEREST = "pinterest"
    SNAPCHAT = "snapchat"
    TWITCH = "twitch"
    REDDIT = "reddit"


class UploadStatusEnum(str, Enum):
    """Upload status tracking."""
    QUEUED = "queued"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"
    DRAFT = "draft"


class ContentVisibilityEnum(str, Enum):
    """Content visibility settings."""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"
    SCHEDULED = "scheduled"


class MonetizationTypeEnum(str, Enum):
    """Monetization options."""
    NONE = "none"
    ADS = "ads"
    SPONSORSHIP = "sponsorship"
    AFFILIATE = "affiliate"
    MERCHANDISE = "merchandise"
    SUBSCRIPTION = "subscription"
    DONATION = "donation"


@dataclass
class PlatformCredentials(BaseDataClass):
    """Platform API credentials and authentication."""
    
    platform: PlatformTypeEnum
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    last_used: Optional[datetime] = None
    rate_limit_remaining: int = 0
    rate_limit_reset: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if credentials are expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_rate_limited(self) -> bool:
        """Check if rate limited."""
        if self.rate_limit_reset is None:
            return False
        return (
            self.rate_limit_remaining <= 0 and
            datetime.utcnow() < self.rate_limit_reset
        )
    
    def update_rate_limit(self, remaining: int, reset_time: datetime):
        """Update rate limit information."""
        self.rate_limit_remaining = remaining
        self.rate_limit_reset = reset_time
        self.last_used = datetime.utcnow()


@dataclass
class PlatformLimits(BaseDataClass):
    """Platform-specific limits and constraints."""
    
    platform: PlatformTypeEnum
    max_file_size: int  # bytes
    max_video_length: int  # seconds
    max_title_length: int
    max_description_length: int
    max_tags: int
    supported_formats: List[str] = field(default_factory=list)
    supported_resolutions: List[str] = field(default_factory=list)
    min_resolution: Optional[str] = None
    max_resolution: Optional[str] = None
    aspect_ratios: List[str] = field(default_factory=list)
    bitrate_limits: Dict[str, int] = field(default_factory=dict)
    
    def validate_file_size(self, size: int) -> bool:
        """Validate file size against platform limits."""
        return size <= self.max_file_size
    
    def validate_video_length(self, length: int) -> bool:
        """Validate video length against platform limits."""
        return length <= self.max_video_length
    
    def validate_format(self, format_type: str) -> bool:
        """Validate file format against platform limits."""
        return format_type.lower() in [f.lower() for f in self.supported_formats]


@dataclass
class PlatformMetadata(BaseDataClass):
    """Platform-specific metadata for content."""
    
    title: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    language: str = "th"
    visibility: ContentVisibilityEnum = ContentVisibilityEnum.PUBLIC
    allow_comments: bool = True
    allow_likes: bool = True
    allow_shares: bool = True
    monetization: MonetizationTypeEnum = MonetizationTypeEnum.NONE
    custom_thumbnail_url: Optional[str] = None
    scheduled_publish_time: Optional[datetime] = None
    location: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.title = validate_non_empty_string(self.title)
        if self.custom_thumbnail_url:
            self.custom_thumbnail_url = validate_url(self.custom_thumbnail_url)
    
    def add_tag(self, tag: str):
        """Add a tag if not already present."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def set_custom_field(self, key: str, value: Any):
        """Set custom platform-specific field."""
        self.custom_fields[key] = value
    
    def optimize_for_platform(self, platform: PlatformTypeEnum, limits: PlatformLimits):
        """Optimize metadata for specific platform limits."""
        # Truncate title if necessary
        if len(self.title) > limits.max_title_length:
            self.title = self.title[:limits.max_title_length - 3] + "..."
        
        # Truncate description if necessary
        if len(self.description) > limits.max_description_length:
            self.description = self.description[:limits.max_description_length - 3] + "..."
        
        # Limit tags
        if len(self.tags) > limits.max_tags:
            self.tags = self.tags[:limits.max_tags]


@dataclass
class UploadTask(BaseDataClass):
    """Upload task tracking and management."""
    
    content_id: str
    platform: PlatformTypeEnum
    file_path: str
    metadata: PlatformMetadata
    status: UploadStatusEnum = UploadStatusEnum.QUEUED
    progress: float = 0.0  # 0.0 to 1.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    platform_id: Optional[str] = None  # ID assigned by platform
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 5  # 1-10, higher is more priority
    
    def start_upload(self):
        """Mark upload as started."""
        self.status = UploadStatusEnum.UPLOADING
        self.started_at = datetime.utcnow()
        self.progress = 0.0
    
    def update_progress(self, progress: float):
        """Update upload progress."""
        self.progress = max(0.0, min(1.0, progress))
    
    def complete_upload(self, platform_id: str, platform_url: str):
        """Mark upload as completed."""
        self.status = UploadStatusEnum.PUBLISHED
        self.completed_at = datetime.utcnow()
        self.progress = 1.0
        self.platform_id = platform_id
        self.platform_url = platform_url
    
    def fail_upload(self, error_message: str):
        """Mark upload as failed."""
        self.status = UploadStatusEnum.FAILED
        self.error_message = error_message
        self.retry_count += 1
    
    def can_retry(self) -> bool:
        """Check if upload can be retried."""
        return self.retry_count < self.max_retries and self.status == UploadStatusEnum.FAILED
    
    def get_upload_duration(self) -> Optional[timedelta]:
        """Get upload duration if completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class PlatformAnalytics(BaseDataClass):
    """Platform-specific analytics and performance data."""
    
    upload_id: str
    platform: PlatformTypeEnum
    platform_id: str
    collected_at: datetime = field(default_factory=datetime.utcnow)
    
    # Engagement metrics
    views: int = 0
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    subscribers_gained: int = 0
    
    # Performance metrics
    click_through_rate: float = 0.0
    average_view_duration: float = 0.0
    audience_retention: Dict[str, float] = field(default_factory=dict)
    impressions: int = 0
    reach: int = 0
    
    # Demographic data
    age_demographics: Dict[str, float] = field(default_factory=dict)
    gender_demographics: Dict[str, float] = field(default_factory=dict)
    location_demographics: Dict[str, float] = field(default_factory=dict)
    device_demographics: Dict[str, float] = field(default_factory=dict)
    
    # Revenue data
    revenue: float = 0.0
    ad_revenue: float = 0.0
    sponsorship_revenue: float = 0.0
    
    # Traffic sources
    traffic_sources: Dict[str, float] = field(default_factory=dict)
    
    def calculate_engagement_rate(self) -> float:
        """Calculate overall engagement rate."""
        if self.views == 0:
            return 0.0
        
        total_engagement = self.likes + self.comments + self.shares + self.saves
        return (total_engagement / self.views) * 100
    
    def calculate_ctr(self) -> float:
        """Calculate click-through rate."""
        if self.impressions == 0:
            return 0.0
        
        return (self.views / self.impressions) * 100
    
    def get_performance_score(self) -> float:
        """Get overall performance score (0-10)."""
        engagement_rate = self.calculate_engagement_rate()
        ctr = self.calculate_ctr()
        retention_rate = self.average_view_duration / 100 if self.average_view_duration else 0
        
        # Weighted scoring
        score = (
            engagement_rate * 0.4 +  # 40% weight
            ctr * 0.3 +             # 30% weight
            retention_rate * 0.3    # 30% weight
        )
        
        return min(score, 10.0)


@dataclass
class PlatformAccount(BaseDataClass):
    """Platform account information and settings."""
    
    platform: PlatformTypeEnum
    account_id: str
    username: str
    display_name: str = ""
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    video_count: int = 0
    total_views: int = 0
    is_verified: bool = False
    is_monetized: bool = False
    account_type: str = "personal"  # personal, business, creator
    credentials: Optional[PlatformCredentials] = None
    limits: Optional[PlatformLimits] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update account statistics."""
        self.follower_count = stats.get('followers', self.follower_count)
        self.following_count = stats.get('following', self.following_count)
        self.video_count = stats.get('videos', self.video_count)
        self.total_views = stats.get('total_views', self.total_views)
        self.is_verified = stats.get('verified', self.is_verified)
        self.is_monetized = stats.get('monetized', self.is_monetized)
        self.update_timestamp()
    
    def is_active(self) -> bool:
        """Check if account is active and ready for uploads."""
        return (
            self.credentials is not None and
            self.credentials.is_active and
            not self.credentials.is_expired() and
            not self.credentials.is_rate_limited()
        )


class PlatformUploadRequest(BasePydanticModel):
    """Request model for platform upload."""
    
    content_id: str = Field(..., description="Content ID to upload")
    platforms: List[PlatformTypeEnum] = Field(..., description="Target platforms")
    metadata_overrides: Dict[PlatformTypeEnum, Dict[str, Any]] = Field(default_factory=dict)
    schedule_time: Optional[datetime] = Field(None, description="Schedule upload time")
    priority: int = Field(5, ge=1, le=10, description="Upload priority")
    auto_optimize: bool = Field(True, description="Auto-optimize for each platform")
    
    @validator('platforms')
    def validate_platforms(cls, v):
        if not v:
            raise ValueError("At least one platform must be specified")
        return v


@dataclass
class UploadBatch(BaseDataClass):
    """Batch upload management."""
    
    batch_id: str
    tasks: List[UploadTask] = field(default_factory=list)
    status: StatusEnum = StatusEnum.PENDING
    created_by: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    def add_task(self, task: UploadTask):
        """Add upload task to batch."""
        self.tasks.append(task)
        self.total_tasks = len(self.tasks)
    
    def update_status(self):
        """Update batch status based on task statuses."""
        if not self.tasks:
            self.status = StatusEnum.PENDING
            return
        
        completed = sum(1 for task in self.tasks if task.status == UploadStatusEnum.PUBLISHED)
        failed = sum(1 for task in self.tasks if task.status == UploadStatusEnum.FAILED)
        
        self.completed_tasks = completed
        self.failed_tasks = failed
        
        if completed == len(self.tasks):
            self.status = StatusEnum.COMPLETED
        elif failed == len(self.tasks):
            self.status = StatusEnum.FAILED
        elif completed + failed == len(self.tasks):
            self.status = StatusEnum.COMPLETED  # Partially completed
        else:
            self.status = StatusEnum.PROCESSING
    
    def get_progress(self) -> float:
        """Get overall batch progress."""
        if not self.tasks:
            return 0.0
        
        total_progress = sum(task.progress for task in self.tasks)
        return total_progress / len(self.tasks)


@dataclass
class PlatformPerformanceReport(BaseDataClass):
    """Performance report across platforms."""
    
    content_id: str
    report_period: str  # daily, weekly, monthly
    start_date: datetime
    end_date: datetime
    platform_analytics: Dict[PlatformTypeEnum, PlatformAnalytics] = field(default_factory=dict)
    
    def add_platform_data(self, platform: PlatformTypeEnum, analytics: PlatformAnalytics):
        """Add analytics data for a platform."""
        self.platform_analytics[platform] = analytics
    
    def get_total_views(self) -> int:
        """Get total views across all platforms."""
        return sum(analytics.views for analytics in self.platform_analytics.values())
    
    def get_total_engagement(self) -> int:
        """Get total engagement across all platforms."""
        return sum(
            analytics.likes + analytics.comments + analytics.shares + analytics.saves
            for analytics in self.platform_analytics.values()
        )
    
    def get_total_revenue(self) -> float:
        """Get total revenue across all platforms."""
        return sum(analytics.revenue for analytics in self.platform_analytics.values())
    
    def get_best_performing_platform(self) -> Optional[PlatformTypeEnum]:
        """Get platform with highest performance score."""
        if not self.platform_analytics:
            return None
        
        best_platform = max(
            self.platform_analytics.items(),
            key=lambda x: x[1].get_performance_score()
        )
        return best_platform[0]
    
    def get_platform_comparison(self) -> Dict[str, Any]:
        """Get detailed platform comparison."""
        comparison = {}
        
        for platform, analytics in self.platform_analytics.items():
            comparison[platform.value] = {
                'views': analytics.views,
                'engagement_rate': analytics.calculate_engagement_rate(),
                'ctr': analytics.calculate_ctr(),
                'performance_score': analytics.get_performance_score(),
                'revenue': analytics.revenue
            }
        
        return comparison


# Utility functions for platform operations

def get_platform_limits(platform: PlatformTypeEnum) -> PlatformLimits:
    """Get default platform limits and constraints."""
    
    platform_configs = {
        PlatformTypeEnum.YOUTUBE: PlatformLimits(
            platform=PlatformTypeEnum.YOUTUBE,
            max_file_size=128 * 1024**3,  # 128 GB
            max_video_length=12 * 3600,   # 12 hours
            max_title_length=100,
            max_description_length=5000,
            max_tags=500,
            supported_formats=['mp4', 'mov', 'avi', 'wmv', 'flv', 'webm'],
            supported_resolutions=['1920x1080', '1280x720', '854x480', '640x360'],
            aspect_ratios=['16:9', '4:3'],
            bitrate_limits={'1080p': 8000, '720p': 5000, '480p': 2500}
        ),
        
        PlatformTypeEnum.TIKTOK: PlatformLimits(
            platform=PlatformTypeEnum.TIKTOK,
            max_file_size=4 * 1024**3,    # 4 GB
            max_video_length=180,         # 3 minutes
            max_title_length=150,
            max_description_length=2200,
            max_tags=100,
            supported_formats=['mp4', 'mov', 'webm'],
            supported_resolutions=['1080x1920', '720x1280'],
            aspect_ratios=['9:16', '1:1'],
            bitrate_limits={'1080p': 10000, '720p': 6000}
        ),
        
        PlatformTypeEnum.INSTAGRAM: PlatformLimits(
            platform=PlatformTypeEnum.INSTAGRAM,
            max_file_size=4 * 1024**3,    # 4 GB
            max_video_length=90,          # 90 seconds for reels
            max_title_length=2200,
            max_description_length=2200,
            max_tags=30,
            supported_formats=['mp4', 'mov'],
            supported_resolutions=['1080x1920', '1080x1080', '1920x1080'],
            aspect_ratios=['9:16', '1:1', '16:9'],
            bitrate_limits={'1080p': 8000, '720p': 5000}
        ),
        
        PlatformTypeEnum.FACEBOOK: PlatformLimits(
            platform=PlatformTypeEnum.FACEBOOK,
            max_file_size=10 * 1024**3,   # 10 GB
            max_video_length=4 * 3600,    # 4 hours
            max_title_length=255,
            max_description_length=63206,
            max_tags=50,
            supported_formats=['mp4', 'mov', 'avi', 'wmv', 'flv'],
            supported_resolutions=['1920x1080', '1280x720', '854x480'],
            aspect_ratios=['16:9', '4:3', '1:1', '9:16'],
            bitrate_limits={'1080p': 8000, '720p': 5000, '480p': 2500}
        )
    }
    
    return platform_configs.get(platform, PlatformLimits(
        platform=platform,
        max_file_size=1024**3,  # 1 GB default
        max_video_length=600,   # 10 minutes default
        max_title_length=100,
        max_description_length=1000,
        max_tags=20
    ))


def optimize_metadata_for_platform(metadata: PlatformMetadata, platform: PlatformTypeEnum) -> PlatformMetadata:
    """Optimize metadata for specific platform."""
    limits = get_platform_limits(platform)
    optimized = metadata
    optimized.optimize_for_platform(platform, limits)
    
    # Platform-specific optimizations
    if platform == PlatformTypeEnum.YOUTUBE:
        # YouTube-specific optimizations
        optimized.set_custom_field('categoryId', '28')  # Science & Technology
        optimized.set_custom_field('defaultLanguage', metadata.language)
        
    elif platform == PlatformTypeEnum.TIKTOK:
        # TikTok-specific optimizations
        optimized.set_custom_field('duetEnabled', True)
        optimized.set_custom_field('stitchEnabled', True)
        
    elif platform == PlatformTypeEnum.INSTAGRAM:
        # Instagram-specific optimizations
        optimized.set_custom_field('feedType', 'REELS')
        optimized.set_custom_field('shareToFeed', True)
    
    return optimized


def calculate_upload_priority(content_type: str, trending_score: float, platform: PlatformTypeEnum) -> int:
    """Calculate upload priority based on various factors."""
    
    base_priority = 5
    
    # Trending score bonus
    if trending_score >= 9.0:
        base_priority += 3
    elif trending_score >= 7.0:
        base_priority += 2
    elif trending_score >= 5.0:
        base_priority += 1
    
    # Platform priority (some platforms may be more important)
    platform_weights = {
        PlatformTypeEnum.YOUTUBE: 1.0,
        PlatformTypeEnum.TIKTOK: 1.2,  # Slightly higher priority
        PlatformTypeEnum.INSTAGRAM: 0.9,
        PlatformTypeEnum.FACEBOOK: 0.8
    }
    
    weight = platform_weights.get(platform, 1.0)
    final_priority = int(base_priority * weight)
    
    return max(1, min(10, final_priority))


def estimate_upload_time(file_size: int, platform: PlatformTypeEnum, connection_speed: int = 50) -> int:
    """
    Estimate upload time in seconds.
    
    Args:
        file_size: File size in bytes
        platform: Target platform
        connection_speed: Upload speed in Mbps
        
    Returns:
        Estimated upload time in seconds
    """
    
    # Platform processing overhead (seconds)
    platform_overhead = {
        PlatformTypeEnum.YOUTUBE: 60,
        PlatformTypeEnum.TIKTOK: 30,
        PlatformTypeEnum.INSTAGRAM: 45,
        PlatformTypeEnum.FACEBOOK: 90
    }
    
    # Convert file size to megabits
    file_size_mb = (file_size / 1024**2) * 8
    
    # Calculate upload time
    upload_time = file_size_mb / connection_speed
    
    # Add platform overhead
    total_time = upload_time + platform_overhead.get(platform, 60)
    
    return int(total_time)