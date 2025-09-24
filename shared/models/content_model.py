"""
AI Content Factory - Content Models
==================================

Shared models for content generation, management, and optimization.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator

from .base_model import BaseDataClass, BasePydanticModel, StatusEnum, QualityTierEnum, validate_non_empty_string, validate_positive_number


class ContentTypeEnum(str, Enum):
    """Content types supported by the system."""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    BLOG_POST = "blog_post"
    SOCIAL_POST = "social_post"
    SCRIPT = "script"
    THUMBNAIL = "thumbnail"
    DESCRIPTION = "description"
    TITLE = "title"


class ContentFormatEnum(str, Enum):
    """Content format specifications."""
    # Video formats
    MP4 = "mp4"
    MOV = "mov" 
    AVI = "avi"
    WEBM = "webm"
    
    # Audio formats
    MP3 = "mp3"
    WAV = "wav"
    AAC = "aac"
    
    # Image formats
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"
    
    # Text formats
    TXT = "txt"
    MD = "md"
    HTML = "html"
    JSON = "json"


class ContentStyleEnum(str, Enum):
    """Content style categories."""
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    REVIEW = "review"
    TUTORIAL = "tutorial"
    LISTICLE = "listicle"
    COMEDY = "comedy"
    DRAMA = "drama"
    DOCUMENTARY = "documentary"
    VLOG = "vlog"
    INTERVIEW = "interview"
    REACTION = "reaction"
    UNBOXING = "unboxing"
    GAMING = "gaming"


class ContentLengthEnum(str, Enum):
    """Content length categories."""
    SHORT = "short"        # < 60 seconds
    MEDIUM = "medium"      # 1-10 minutes
    LONG = "long"          # 10+ minutes
    FEATURE = "feature"    # 30+ minutes


@dataclass
class ContentSpecification(BaseDataClass):
    """Content specification and requirements."""
    
    content_type: ContentTypeEnum
    format: ContentFormatEnum
    style: ContentStyleEnum = ContentStyleEnum.EDUCATIONAL
    length: ContentLengthEnum = ContentLengthEnum.MEDIUM
    quality_tier: QualityTierEnum = QualityTierEnum.BALANCED
    target_duration: Optional[int] = None  # seconds
    resolution: Optional[str] = None  # e.g., "1920x1080"
    aspect_ratio: Optional[str] = None  # e.g., "16:9", "9:16"
    frame_rate: Optional[int] = None
    bitrate: Optional[int] = None
    color_profile: Optional[str] = None
    language: str = "th"  # Default to Thai
    subtitle_required: bool = False
    watermark_required: bool = False
    
    def get_optimal_settings(self) -> Dict[str, Any]:
        """Get optimal settings based on specifications."""
        settings = {
            "quality_tier": self.quality_tier.value,
            "language": self.language
        }
        
        # Video-specific settings
        if self.content_type == ContentTypeEnum.VIDEO:
            if self.length == ContentLengthEnum.SHORT:
                settings.update({
                    "resolution": "1080x1920",  # Vertical for shorts
                    "aspect_ratio": "9:16",
                    "target_duration": min(self.target_duration or 60, 60)
                })
            else:
                settings.update({
                    "resolution": "1920x1080",  # Horizontal for regular videos
                    "aspect_ratio": "16:9",
                    "target_duration": self.target_duration or 300
                })
            
            settings.update({
                "frame_rate": self.frame_rate or 30,
                "bitrate": self.bitrate or 5000
            })
        
        # Audio-specific settings
        elif self.content_type == ContentTypeEnum.AUDIO:
            settings.update({
                "sample_rate": 44100,
                "bitrate": 320,
                "channels": 2
            })
        
        return settings


@dataclass
class ContentScript(BaseDataClass):
    """Content script and narrative structure."""
    
    title: str
    hook: str  # Opening 3 seconds
    introduction: str
    main_content: List[str] = field(default_factory=list)
    conclusion: str = ""
    call_to_action: str = ""
    total_words: int = 0
    estimated_duration: int = 0  # seconds
    tone: str = "professional"  # professional, casual, energetic, calm
    target_audience: str = "general"
    
    def __post_init__(self):
        self.title = validate_non_empty_string(self.title)
        self.hook = validate_non_empty_string(self.hook)
        self.calculate_metrics()
    
    def calculate_metrics(self):
        """Calculate script metrics."""
        all_text = f"{self.hook} {self.introduction} {' '.join(self.main_content)} {self.conclusion} {self.call_to_action}"
        self.total_words = len(all_text.split())
        # Estimate duration: average 150 words per minute
        self.estimated_duration = int((self.total_words / 150) * 60)
    
    def add_section(self, content: str):
        """Add content section."""
        self.main_content.append(content)
        self.calculate_metrics()
    
    def get_full_script(self) -> str:
        """Get complete script text."""
        sections = [self.hook, self.introduction]
        sections.extend(self.main_content)
        sections.extend([self.conclusion, self.call_to_action])
        return "\n\n".join(filter(None, sections))


@dataclass
class VisualPlan(BaseDataClass):
    """Visual content planning and specifications."""
    
    style: str = "realistic"  # realistic, cartoon, minimalist, cinematic
    color_scheme: List[str] = field(default_factory=list)
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    text_overlays: List[Dict[str, Any]] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)
    background_music: Optional[str] = None
    sound_effects: List[str] = field(default_factory=list)
    
    def add_scene(self, description: str, duration: int = 5, **kwargs):
        """Add visual scene."""
        scene = {
            "description": description,
            "duration": duration,
            "timestamp": sum(s.get("duration", 0) for s in self.scenes),
            **kwargs
        }
        self.scenes.append(scene)
    
    def add_text_overlay(self, text: str, start_time: int, duration: int = 3, **kwargs):
        """Add text overlay."""
        overlay = {
            "text": text,
            "start_time": start_time,
            "duration": duration,
            **kwargs
        }
        self.text_overlays.append(overlay)
    
    def get_total_duration(self) -> int:
        """Get total visual duration."""
        return sum(scene.get("duration", 0) for scene in self.scenes)


@dataclass
class AudioPlan(BaseDataClass):
    """Audio content planning and specifications."""
    
    voice_style: str = "professional"  # professional, casual, energetic, calm
    speaking_rate: float = 1.0  # 0.5 - 2.0
    background_music: Optional[str] = None
    sound_effects: List[Dict[str, Any]] = field(default_factory=list)
    volume_levels: Dict[str, float] = field(default_factory=dict)
    fade_in_duration: float = 1.0
    fade_out_duration: float = 1.0
    
    def add_sound_effect(self, effect: str, timestamp: float, duration: float = 1.0, volume: float = 0.5):
        """Add sound effect."""
        self.sound_effects.append({
            "effect": effect,
            "timestamp": timestamp,
            "duration": duration,
            "volume": volume
        })
    
    def set_volume_level(self, track: str, volume: float):
        """Set volume level for audio track."""
        self.volume_levels[track] = max(0.0, min(1.0, volume))


@dataclass
class ContentPlan(BaseDataClass):
    """Complete content production plan."""
    
    specification: ContentSpecification
    script: ContentScript
    visual_plan: Optional[VisualPlan] = None
    audio_plan: Optional[AudioPlan] = None
    platform_optimizations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    production_notes: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_production_time: int = 0  # minutes
    
    def __post_init__(self):
        if self.specification.content_type == ContentTypeEnum.VIDEO:
            if self.visual_plan is None:
                self.visual_plan = VisualPlan()
            if self.audio_plan is None:
                self.audio_plan = AudioPlan()
    
    def add_platform_optimization(self, platform: str, optimization: Dict[str, Any]):
        """Add platform-specific optimization."""
        self.platform_optimizations[platform] = optimization
    
    def estimate_production_cost(self) -> float:
        """Estimate production cost based on specifications."""
        base_costs = {
            QualityTierEnum.BUDGET: 15,
            QualityTierEnum.BALANCED: 45,
            QualityTierEnum.PREMIUM: 150
        }
        
        base_cost = base_costs[self.specification.quality_tier]
        
        # Adjust for content type
        type_multipliers = {
            ContentTypeEnum.VIDEO: 1.0,
            ContentTypeEnum.AUDIO: 0.3,
            ContentTypeEnum.IMAGE: 0.2,
            ContentTypeEnum.TEXT: 0.1
        }
        
        # Adjust for length
        length_multipliers = {
            ContentLengthEnum.SHORT: 0.5,
            ContentLengthEnum.MEDIUM: 1.0,
            ContentLengthEnum.LONG: 2.0,
            ContentLengthEnum.FEATURE: 4.0
        }
        
        self.estimated_cost = (
            base_cost * 
            type_multipliers.get(self.specification.content_type, 1.0) *
            length_multipliers.get(self.specification.length, 1.0)
        )
        
        return self.estimated_cost
    
    def validate_plan(self) -> List[str]:
        """Validate content plan for completeness."""
        issues = []
        
        if not self.script.title:
            issues.append("Script title is required")
        
        if not self.script.hook:
            issues.append("Script hook is required")
        
        if self.specification.content_type == ContentTypeEnum.VIDEO:
            if not self.visual_plan or not self.visual_plan.scenes:
                issues.append("Video content requires visual scenes")
            
            if not self.audio_plan:
                issues.append("Video content requires audio plan")
        
        return issues


@dataclass
class ContentAsset(BaseDataClass):
    """Individual content asset (file, image, audio, etc.)."""
    
    asset_type: ContentTypeEnum
    format: ContentFormatEnum
    file_path: Optional[str] = None
    url: Optional[str] = None
    size_bytes: int = 0
    duration: Optional[int] = None  # seconds for video/audio
    dimensions: Optional[str] = None  # e.g., "1920x1080"
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate_asset(self) -> bool:
        """Validate asset integrity."""
        if not self.file_path and not self.url:
            return False
        
        # Add format validation logic here
        return True
    
    def get_asset_info(self) -> Dict[str, Any]:
        """Get comprehensive asset information."""
        return {
            "type": self.asset_type.value,
            "format": self.format.value,
            "size": self.size_bytes,
            "duration": self.duration,
            "dimensions": self.dimensions,
            "quality": self.quality_score,
            "metadata": self.metadata
        }


@dataclass
class ContentItem(BaseDataClass):
    """Complete content item with all assets and metadata."""
    
    title: str
    description: str
    content_plan: ContentPlan
    assets: List[ContentAsset] = field(default_factory=list)
    thumbnail: Optional[ContentAsset] = None
    status: StatusEnum = StatusEnum.PENDING
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    target_platforms: List[str] = field(default_factory=list)
    production_started_at: Optional[datetime] = None
    production_completed_at: Optional[datetime] = None
    total_cost: float = 0.0
    performance_prediction: Dict[str, Any] = field(default_factory=dict)
    
    def add_asset(self, asset: ContentAsset):
        """Add content asset."""
        self.assets.append(asset)
    
    def get_primary_asset(self) -> Optional[ContentAsset]:
        """Get the primary content asset."""
        if not self.assets:
            return None
        
        # Return the first video asset, or first asset if no video
        for asset in self.assets:
            if asset.asset_type == ContentTypeEnum.VIDEO:
                return asset
        
        return self.assets[0]
    
    def calculate_production_time(self) -> Optional[timedelta]:
        """Calculate actual production time."""
        if self.production_started_at and self.production_completed_at:
            return self.production_completed_at - self.production_started_at
        return None
    
    def is_ready_for_upload(self) -> bool:
        """Check if content is ready for platform upload."""
        return (
            self.status == StatusEnum.COMPLETED and
            len(self.assets) > 0 and
            self.get_primary_asset() is not None
        )


class ContentGenerationRequest(BasePydanticModel):
    """Request model for content generation."""
    
    trend_topic: str = Field(..., description="Trending topic to create content about")
    content_type: ContentTypeEnum = ContentTypeEnum.VIDEO
    content_style: ContentStyleEnum = ContentStyleEnum.EDUCATIONAL
    content_length: ContentLengthEnum = ContentLengthEnum.MEDIUM
    quality_tier: QualityTierEnum = QualityTierEnum.BALANCED
    target_platforms: List[str] = Field(default_factory=list)
    target_audience: str = "general"
    language: str = "th"
    special_requirements: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('target_platforms')
    def validate_platforms(cls, v):
        valid_platforms = ['youtube', 'tiktok', 'instagram', 'facebook']
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}")
        return v


@dataclass
class ContentAnalytics(BaseDataClass):
    """Content performance analytics."""
    
    content_id: str
    platform: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    click_through_rate: float = 0.0
    engagement_rate: float = 0.0
    revenue: float = 0.0
    cost_per_view: float = 0.0
    return_on_investment: float = 0.0
    audience_retention: Dict[str, float] = field(default_factory=dict)
    demographics: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_metrics(self):
        """Calculate derived metrics."""
        if self.views > 0:
            total_engagement = self.likes + self.comments + self.shares + self.saves
            self.engagement_rate = (total_engagement / self.views) * 100
            
            if self.revenue > 0:
                self.cost_per_view = self.revenue / self.views
        
        # Calculate ROI if cost data is available
        if hasattr(self, 'production_cost') and self.production_cost > 0:
            self.return_on_investment = ((self.revenue - self.production_cost) / self.production_cost) * 100
    
    def get_performance_grade(self) -> str:
        """Get performance grade based on metrics."""
        if self.engagement_rate >= 10:
            return "A+"
        elif self.engagement_rate >= 7:
            return "A"
        elif self.engagement_rate >= 5:
            return "B"
        elif self.engagement_rate >= 3:
            return "C"
        else:
            return "D"


# Utility functions for content operations

def optimize_content_for_platform(content_plan: ContentPlan, platform: str) -> ContentPlan:
    """Optimize content plan for specific platform."""
    optimized_plan = content_plan
    
    platform_specs = {
        'youtube': {
            'max_title_length': 100,
            'max_description_length': 5000,
            'optimal_duration': 480,  # 8 minutes
            'aspect_ratio': '16:9'
        },
        'tiktok': {
            'max_title_length': 150,
            'max_description_length': 2200,
            'optimal_duration': 30,
            'aspect_ratio': '9:16'
        },
        'instagram': {
            'max_title_length': 2200,
            'max_description_length': 2200,
            'optimal_duration': 60,
            'aspect_ratio': '9:16'
        }
    }
    
    if platform in platform_specs:
        specs = platform_specs[platform]
        optimization = {
            'title_length': specs['max_title_length'],
            'description_length': specs['max_description_length'],
            'target_duration': specs['optimal_duration'],
            'aspect_ratio': specs['aspect_ratio']
        }
        optimized_plan.add_platform_optimization(platform, optimization)
        
        # Adjust specifications
        if specs['aspect_ratio'] == '9:16':
            optimized_plan.specification.aspect_ratio = '9:16'
            optimized_plan.specification.resolution = '1080x1920'
        
        if specs['optimal_duration'] <= 60:
            optimized_plan.specification.length = ContentLengthEnum.SHORT
    
    return optimized_plan


def estimate_content_performance(content_item: ContentItem, historical_data: List[ContentAnalytics] = None) -> Dict[str, Any]:
    """Estimate content performance based on historical data."""
    if not historical_data:
        # Default predictions
        return {
            'estimated_views': 1000,
            'estimated_engagement_rate': 3.0,
            'estimated_revenue': 50.0,
            'confidence': 0.3
        }
    
    # Analyze similar content performance
    similar_content = [
        analytics for analytics in historical_data
        if analytics.content_id != content_item.id
    ]
    
    if not similar_content:
        return {
            'estimated_views': 500,
            'estimated_engagement_rate': 2.0,
            'estimated_revenue': 25.0,
            'confidence': 0.2
        }
    
    # Calculate averages from similar content
    avg_views = sum(a.views for a in similar_content) / len(similar_content)
    avg_engagement = sum(a.engagement_rate for a in similar_content) / len(similar_content)
    avg_revenue = sum(a.revenue for a in similar_content) / len(similar_content)
    
    return {
        'estimated_views': int(avg_views),
        'estimated_engagement_rate': avg_engagement,
        'estimated_revenue': avg_revenue,
        'confidence': min(len(similar_content) / 10, 1.0)  # Higher confidence with more data
    }