"""
Platform Type Models
กำหนดประเภทของ platforms ที่รองรับและ specifications ของแต่ละ platform
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

class PlatformType(Enum):
    """ประเภทของ platforms ที่รองรับ"""
    
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"  # สำหรับอนาคต
    LINKEDIN = "linkedin"  # สำหรับอนาคต
    TWITCH = "twitch"  # สำหรับอนาคต

@dataclass
class PlatformSpecs:
    """ข้อมูล specifications ของแต่ละ platform"""
    
    name: str
    display_name: str
    max_file_size_mb: int
    max_duration_seconds: int
    supported_formats: List[str]
    supported_aspect_ratios: List[str]
    recommended_resolution: Dict[str, tuple]
    max_title_length: int
    max_description_length: int
    max_tags: int
    supports_thumbnails: bool
    supports_scheduling: bool
    supports_monetization: bool
    api_endpoints: Dict[str, str]
    rate_limits: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "max_file_size_mb": self.max_file_size_mb,
            "max_duration_seconds": self.max_duration_seconds,
            "supported_formats": self.supported_formats,
            "supported_aspect_ratios": self.supported_aspect_ratios,
            "recommended_resolution": self.recommended_resolution,
            "max_title_length": self.max_title_length,
            "max_description_length": self.max_description_length,
            "max_tags": self.max_tags,
            "supports_thumbnails": self.supports_thumbnails,
            "supports_scheduling": self.supports_scheduling,
            "supports_monetization": self.supports_monetization,
            "api_endpoints": self.api_endpoints,
            "rate_limits": self.rate_limits
        }

class PlatformRegistry:
    """Registry สำหรับเก็บข้อมูล platform specifications"""
    
    _platforms = {
        PlatformType.YOUTUBE: PlatformSpecs(
            name="youtube",
            display_name="YouTube",
            max_file_size_mb=128 * 1024,  # 128GB
            max_duration_seconds=43200,  # 12 hours
            supported_formats=["MP4", "MOV", "AVI", "WMV", "FLV", "WebM"],
            supported_aspect_ratios=["16:9", "9:16", "1:1", "4:3"],
            recommended_resolution={
                "16:9": (1920, 1080),
                "9:16": (1080, 1920),
                "1:1": (1080, 1080)
            },
            max_title_length=100,
            max_description_length=5000,
            max_tags=500,  # 500 characters total
            supports_thumbnails=True,
            supports_scheduling=True,
            supports_monetization=True,
            api_endpoints={
                "upload": "https://www.googleapis.com/upload/youtube/v3/videos",
                "update": "https://www.googleapis.com/youtube/v3/videos",
                "thumbnails": "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
            },
            rate_limits={
                "uploads_per_day": 6,  # For unverified channels
                "api_units_per_day": 10000,
                "quota_cost_upload": 1600
            }
        ),
        
        PlatformType.TIKTOK: PlatformSpecs(
            name="tiktok",
            display_name="TikTok",
            max_file_size_mb=4 * 1024,  # 4GB
            max_duration_seconds=600,  # 10 minutes
            supported_formats=["MP4", "MOV"],
            supported_aspect_ratios=["9:16"],
            recommended_resolution={
                "9:16": (1080, 1920)
            },
            max_title_length=0,  # TikTok doesn't have separate titles
            max_description_length=300,
            max_tags=0,  # Tags are included in description as hashtags
            supports_thumbnails=False,  # Auto-generated
            supports_scheduling=True,
            supports_monetization=True,
            api_endpoints={
                "upload": "https://open-api.tiktok.com/share/video/upload/",
                "publish": "https://open-api.tiktok.com/video/publish/"
            },
            rate_limits={
                "uploads_per_day": 50,
                "api_calls_per_day": 1000
            }
        ),
        
        PlatformType.INSTAGRAM: PlatformSpecs(
            name="instagram",
            display_name="Instagram",
            max_file_size_mb=4 * 1024,  # 4GB
            max_duration_seconds=90,  # 90 seconds for Reels
            supported_formats=["MP4", "MOV"],
            supported_aspect_ratios=["9:16", "1:1", "4:5"],
            recommended_resolution={
                "9:16": (1080, 1920),  # Reels
                "1:1": (1080, 1080),   # Square posts
                "4:5": (1080, 1350)    # Portrait posts
            },
            max_title_length=0,  # Instagram doesn't have separate titles
            max_description_length=2200,
            max_tags=30,  # 30 hashtags max
            supports_thumbnails=True,
            supports_scheduling=True,
            supports_monetization=True,
            api_endpoints={
                "upload": "https://graph.facebook.com/v18.0/{user-id}/media",
                "publish": "https://graph.facebook.com/v18.0/{user-id}/media_publish"
            },
            rate_limits={
                "uploads_per_hour": 25,
                "api_calls_per_hour": 200
            }
        ),
        
        PlatformType.FACEBOOK: PlatformSpecs(
            name="facebook",
            display_name="Facebook",
            max_file_size_mb=10 * 1024,  # 10GB
            max_duration_seconds=7200,  # 2 hours
            supported_formats=["MP4", "MOV", "AVI"],
            supported_aspect_ratios=["16:9", "1:1", "9:16", "4:5"],
            recommended_resolution={
                "16:9": (1280, 720),
                "1:1": (720, 720),
                "9:16": (720, 1280)
            },
            max_title_length=255,
            max_description_length=63206,  # Very long for Facebook
            max_tags=0,  # Facebook uses different tagging system
            supports_thumbnails=True,
            supports_scheduling=True,
            supports_monetization=True,
            api_endpoints={
                "upload": "https://graph.facebook.com/v18.0/{page-id}/videos",
                "photos": "https://graph.facebook.com/v18.0/{page-id}/photos"
            },
            rate_limits={
                "uploads_per_hour": 100,
                "api_calls_per_hour": 600
            }
        ),
        
        PlatformType.TWITTER: PlatformSpecs(
            name="twitter",
            display_name="Twitter (X)",
            max_file_size_mb=512,  # 512MB
            max_duration_seconds=140,  # 2 minutes 20 seconds
            supported_formats=["MP4", "MOV"],
            supported_aspect_ratios=["16:9", "1:1", "9:16"],
            recommended_resolution={
                "16:9": (1280, 720),
                "1:1": (720, 720),
                "9:16": (720, 1280)
            },
            max_title_length=0,  # Twitter doesn't have separate titles
            max_description_length=280,  # Tweet character limit
            max_tags=0,  # Uses hashtags in tweet text
            supports_thumbnails=False,
            supports_scheduling=True,
            supports_monetization=False,
            api_endpoints={
                "upload": "https://upload.twitter.com/1.1/media/upload.json",
                "tweet": "https://api.twitter.com/2/tweets"
            },
            rate_limits={
                "uploads_per_day": 300,
                "tweets_per_day": 2400
            }
        ),
        
        PlatformType.LINKEDIN: PlatformSpecs(
            name="linkedin",
            display_name="LinkedIn",
            max_file_size_mb=5 * 1024,  # 5GB
            max_duration_seconds=600,  # 10 minutes
            supported_formats=["MP4", "MOV", "AVI"],
            supported_aspect_ratios=["16:9", "1:1", "9:16"],
            recommended_resolution={
                "16:9": (1280, 720),
                "1:1": (1080, 1080),
                "9:16": (1080, 1920)
            },
            max_title_length=150,
            max_description_length=3000,
            max_tags=0,  # LinkedIn uses mentions and hashtags differently
            supports_thumbnails=True,
            supports_scheduling=True,
            supports_monetization=False,
            api_endpoints={
                "upload": "https://api.linkedin.com/v2/shares",
                "media": "https://api.linkedin.com/v2/assets"
            },
            rate_limits={
                "uploads_per_day": 150,
                "api_calls_per_day": 2000
            }
        ),
        
        PlatformType.TWITCH: PlatformSpecs(
            name="twitch",
            display_name="Twitch",
            max_file_size_mb=10 * 1024,  # 10GB
            max_duration_seconds=7200,  # 2 hours
            supported_formats=["MP4", "MOV"],
            supported_aspect_ratios=["16:9"],
            recommended_resolution={
                "16:9": (1920, 1080)
            },
            max_title_length=140,
            max_description_length=500,
            max_tags=10,
            supports_thumbnails=True,
            supports_scheduling=False,  # Twitch is primarily live streaming
            supports_monetization=True,
            api_endpoints={
                "upload": "https://api.twitch.tv/helix/videos",
                "clips": "https://api.twitch.tv/helix/clips"
            },
            rate_limits={
                "uploads_per_day": 5,  # Limited for regular users
                "api_calls_per_minute": 800
            }
        )
    }
    
    @classmethod
    def get_platform_specs(cls, platform_type: PlatformType) -> Optional[PlatformSpecs]:
        """ได้รับ specs ของ platform"""
        return cls._platforms.get(platform_type)
    
    @classmethod
    def get_all_platforms(cls) -> Dict[PlatformType, PlatformSpecs]:
        """ได้รับ specs ของ platforms ทั้งหมด"""
        return cls._platforms.copy()
    
    @classmethod
    def get_supported_platforms(cls) -> List[PlatformType]:
        """ได้รับรายการ platforms ที่รองรับ"""
        return list(cls._platforms.keys())
    
    @classmethod
    def is_platform_supported(cls, platform_type: PlatformType) -> bool:
        """ตรวจสอบว่า platform รองรับหรือไม่"""
        return platform_type in cls._platforms
    
    @classmethod
    def get_platform_by_name(cls, name: str) -> Optional[PlatformType]:
        """หา platform type จากชื่อ"""
        for platform_type in cls._platforms:
            if platform_type.value.lower() == name.lower():
                return platform_type
        return None
    
    @classmethod
    def get_platforms_supporting_feature(cls, feature: str) -> List[PlatformType]:
        """หา platforms ที่รองรับ feature ที่กำหนด"""
        supported_platforms = []
        
        for platform_type, specs in cls._platforms.items():
            if hasattr(specs, f"supports_{feature}"):
                if getattr(specs, f"supports_{feature}"):
                    supported_platforms.append(platform_type)
        
        return supported_platforms
    
    @classmethod
    def get_optimal_resolution(cls, platform_type: PlatformType, aspect_ratio: str) -> Optional[tuple]:
        """ได้รับ resolution ที่เหมาะสมสำหรับ platform และ aspect ratio"""
        specs = cls.get_platform_specs(platform_type)
        if specs and aspect_ratio in specs.recommended_resolution:
            return specs.recommended_resolution[aspect_ratio]
        return None
    
    @classmethod
    def validate_content_specs(cls, platform_type: PlatformType, content_info: Dict[str, Any]) -> Dict[str, bool]:
        """ตรวจสอบว่าเนื้อหาเป็นไปตาม specs ของ platform หรือไม่"""
        specs = cls.get_platform_specs(platform_type)
        if not specs:
            return {"valid": False, "error": "Platform not supported"}
        
        validation_results = {
            "valid": True,
            "file_size_ok": True,
            "duration_ok": True,
            "format_ok": True,
            "resolution_ok": True,
            "title_length_ok": True,
            "description_length_ok": True,
            "warnings": []
        }
        
        # Check file size
        file_size_mb = content_info.get("file_size_mb", 0)
        if file_size_mb > specs.max_file_size_mb:
            validation_results["file_size_ok"] = False
            validation_results["valid"] = False
            validation_results["warnings"].append(
                f"File size {file_size_mb}MB exceeds limit {specs.max_file_size_mb}MB"
            )
        
        # Check duration
        duration = content_info.get("duration_seconds", 0)
        if duration > specs.max_duration_seconds:
            validation_results["duration_ok"] = False
            validation_results["valid"] = False
            validation_results["warnings"].append(
                f"Duration {duration}s exceeds limit {specs.max_duration_seconds}s"
            )
        
        # Check format
        file_format = content_info.get("format", "").upper()
        if file_format and file_format not in specs.supported_formats:
            validation_results["format_ok"] = False
            validation_results["valid"] = False
            validation_results["warnings"].append(
                f"Format {file_format} not supported. Supported: {specs.supported_formats}"
            )
        
        # Check title length
        title_length = len(content_info.get("title", ""))
        if title_length > specs.max_title_length:
            validation_results["title_length_ok"] = False
            validation_results["warnings"].append(
                f"Title length {title_length} exceeds limit {specs.max_title_length}"
            )
        
        # Check description length
        description_length = len(content_info.get("description", ""))
        if description_length > specs.max_description_length:
            validation_results["description_length_ok"] = False
            validation_results["warnings"].append(
                f"Description length {description_length} exceeds limit {specs.max_description_length}"
            )
        
        return validation_results

@dataclass
class PlatformStatus:
    """สถานะของ platform"""
    
    platform_type: PlatformType
    is_available: bool
    is_configured: bool
    last_upload: Optional[str]
    rate_limit_remaining: int
    rate_limit_reset_time: Optional[str]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "platform": self.platform_type.value,
            "is_available": self.is_available,
            "is_configured": self.is_configured,
            "last_upload": self.last_upload,
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset_time": self.rate_limit_reset_time,
            "error_message": self.error_message
        }

class PlatformFeatures:
    """คลาสสำหรับจัดการ features ของแต่ละ platform"""
    
    FEATURES = {
        "thumbnails": ["youtube", "instagram", "facebook", "linkedin", "twitch"],
        "scheduling": ["youtube", "tiktok", "instagram", "facebook", "twitter", "linkedin"],
        "monetization": ["youtube", "tiktok", "instagram", "facebook", "twitch"],
        "live_streaming": ["youtube", "facebook", "twitch", "instagram"],
        "stories": ["instagram", "facebook"],
        "hashtags": ["tiktok", "instagram", "twitter", "linkedin"],
        "categories": ["youtube"],
        "location_tagging": ["instagram", "facebook"],
        "collaborations": ["youtube", "tiktok", "instagram"],
        "analytics": ["youtube", "tiktok", "instagram", "facebook", "twitter", "linkedin"]
    }
    
    @classmethod
    def get_platform_features(cls, platform_name: str) -> List[str]:
        """ได้รับรายการ features ที่ platform รองรับ"""
        features = []
        for feature, platforms in cls.FEATURES.items():
            if platform_name.lower() in platforms:
                features.append(feature)
        return features
    
    @classmethod
    def supports_feature(cls, platform_name: str, feature: str) -> bool:
        """ตรวจสอบว่า platform รองรับ feature หรือไม่"""
        platforms = cls.FEATURES.get(feature, [])
        return platform_name.lower() in platforms

def get_platform_comparison() -> Dict[str, Dict[str, Any]]:
    """เปรียบเทียบ specs ของ platforms ทั้งหมด"""
    
    comparison = {}
    
    for platform_type in PlatformRegistry.get_supported_platforms():
        specs = PlatformRegistry.get_platform_specs(platform_type)
        if specs:
            comparison[platform_type.value] = {
                "display_name": specs.display_name,
                "max_file_size_gb": specs.max_file_size_mb / 1024,
                "max_duration_minutes": specs.max_duration_seconds / 60,
                "supported_formats": specs.supported_formats,
                "supports_thumbnails": specs.supports_thumbnails,
                "supports_scheduling": specs.supports_scheduling,
                "supports_monetization": specs.supports_monetization,
                "features": PlatformFeatures.get_platform_features(platform_type.value)
            }
    
    return comparison

# Utility functions
def validate_platform_name(platform_name: str) -> bool:
    """ตรวจสอบว่าชื่อ platform ถูกต้องหรือไม่"""
    return PlatformRegistry.get_platform_by_name(platform_name) is not None

def get_recommended_settings(platform_name: str) -> Optional[Dict[str, Any]]:
    """ได้รับการตั้งค่าที่แนะนำสำหรับ platform"""
    platform_type = PlatformRegistry.get_platform_by_name(platform_name)
    if not platform_type:
        return None
    
    specs = PlatformRegistry.get_platform_specs(platform_type)
    if not specs:
        return None
    
    return {
        "recommended_format": specs.supported_formats[0],  # First format is usually preferred
        "recommended_resolution": specs.recommended_resolution,
        "optimal_duration": min(60, specs.max_duration_seconds),  # 1 minute or platform max
        "title_tips": f"Keep under {specs.max_title_length} characters" if specs.max_title_length > 0 else "No separate title needed",
        "description_tips": f"Keep under {specs.max_description_length} characters",
        "features_available": PlatformFeatures.get_platform_features(platform_name)
    }