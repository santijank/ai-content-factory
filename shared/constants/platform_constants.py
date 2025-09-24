"""
Platform Constants Module
ค่าคงที่สำหรับ platforms ต่างๆ ในระบบ AI Content Factory
"""

from enum import Enum
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

# Platform Types
class PlatformType(Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"

# Content Types
class ContentType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"
    STORY = "story"
    REEL = "reel"
    SHORT = "short"

# Upload Status
class UploadStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"

# Video Quality Settings
class VideoQuality(Enum):
    LOW = "low"        # 480p
    MEDIUM = "medium"  # 720p
    HIGH = "high"      # 1080p
    ULTRA = "ultra"    # 4K

@dataclass
class PlatformSpecs:
    """ข้อมูล specifications ของแต่ละ platform"""
    name: str
    max_video_duration: int    # seconds
    max_file_size: int        # MB
    supported_formats: List[str]
    optimal_resolution: Tuple[int, int]  # width, height
    supported_aspect_ratios: List[str]
    max_title_length: int
    max_description_length: int
    max_hashtags: int
    supports_scheduling: bool
    supports_analytics: bool
    api_endpoints: Dict[str, str]

# Platform Specifications
PLATFORM_SPECS = {
    PlatformType.YOUTUBE: PlatformSpecs(
        name="YouTube",
        max_video_duration=43200,  # 12 hours
        max_file_size=128000,      # 128 GB (in MB)
        supported_formats=[
            "mp4", "mov", "avi", "wmv", "flv", "webm", "mpg", "3gpp"
        ],
        optimal_resolution=(1920, 1080),
        supported_aspect_ratios=["16:9", "9:16", "1:1", "4:3"],
        max_title_length=100,
        max_description_length=5000,
        max_hashtags=15,
        supports_scheduling=True,
        supports_analytics=True,
        api_endpoints={
            "upload": "https://www.googleapis.com/upload/youtube/v3/videos",
            "search": "https://www.googleapis.com/youtube/v3/search",
            "analytics": "https://youtubeanalytics.googleapis.com/v2/reports"
        }
    ),
    
    PlatformType.TIKTOK: PlatformSpecs(
        name="TikTok",
        max_video_duration=600,    # 10 minutes
        max_file_size=4000,       # 4 GB
        supported_formats=["mp4", "mov", "webm"],
        optimal_resolution=(1080, 1920),  # 9:16 aspect ratio
        supported_aspect_ratios=["9:16", "1:1", "16:9"],
        max_title_length=150,
        max_description_length=2200,
        max_hashtags=20,
        supports_scheduling=True,
        supports_analytics=True,
        api_endpoints={
            "upload": "https://open-api.tiktok.com/share/video/upload/",
            "user_info": "https://open-api.tiktok.com/user/info/"
        }
    ),
    
    PlatformType.INSTAGRAM: PlatformSpecs(
        name="Instagram",
        max_video_duration=60,     # 1 minute for reels
        max_file_size=100,         # 100 MB
        supported_formats=["mp4", "mov"],
        optimal_resolution=(1080, 1920),
        supported_aspect_ratios=["9:16", "1:1", "4:5"],
        max_title_length=125,      # Caption length
        max_description_length=2200,
        max_hashtags=30,
        supports_scheduling=False,  # Limited scheduling
        supports_analytics=True,
        api_endpoints={
            "upload": "https://graph.instagram.com/me/media",
            "insights": "https://graph.instagram.com/{media-id}/insights"
        }
    ),
    
    PlatformType.FACEBOOK: PlatformSpecs(
        name="Facebook",
        max_video_duration=7200,   # 2 hours
        max_file_size=10000,       # 10 GB
        supported_formats=["mp4", "mov", "avi", "mkv", "webm"],
        optimal_resolution=(1920, 1080),
        supported_aspect_ratios=["16:9", "1:1", "4:5", "9:16"],
        max_title_length=255,
        max_description_length=63206,
        max_hashtags=20,
        supports_scheduling=True,
        supports_analytics=True,
        api_endpoints={
            "upload": "https://graph.facebook.com/me/videos",
            "insights": "https://graph.facebook.com/{post-id}/insights"
        }
    ),
    
    PlatformType.TWITTER: PlatformSpecs(
        name="Twitter",
        max_video_duration=140,    # 2 minutes 20 seconds
        max_file_size=512,         # 512 MB
        supported_formats=["mp4", "mov"],
        optimal_resolution=(1280, 720),
        supported_aspect_ratios=["16:9", "1:1"],
        max_title_length=280,      # Tweet length
        max_description_length=280,
        max_hashtags=10,          # Recommended
        supports_scheduling=True,
        supports_analytics=True,
        api_endpoints={
            "upload": "https://upload.twitter.com/1.1/media/upload.json",
            "tweet": "https://api.twitter.com/2/tweets"
        }
    ),
    
    PlatformType.LINKEDIN: PlatformSpecs(
        name="LinkedIn",
        max_video_duration=600,    # 10 minutes
        max_file_size=5000,        # 5 GB
        supported_formats=["mp4", "mov", "wmv", "flv", "avi"],
        optimal_resolution=(1920, 1080),
        supported_aspect_ratios=["16:9", "1:1", "4:5"],
        max_title_length=150,
        max_description_length=3000,
        max_hashtags=5,            # Recommended
        supports_scheduling=True,
        supports_analytics=True,
        api_endpoints={
            "upload": "https://api.linkedin.com/v2/assets",
            "share": "https://api.linkedin.com/v2/ugcPosts"
        }
    )
}

# Video Resolution Presets
VIDEO_RESOLUTIONS = {
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
    
    # Mobile/Vertical formats
    "mobile_hd": (1080, 1920),
    "instagram_story": (1080, 1920),
    "tiktok_optimal": (1080, 1920),
    
    # Square formats
    "square_hd": (1080, 1080),
    "instagram_feed": (1080, 1080)
}

# Aspect Ratio Calculations
ASPECT_RATIOS = {
    "16:9": 16/9,      # Landscape (YouTube, Facebook)
    "9:16": 9/16,      # Portrait (TikTok, Instagram Stories)
    "1:1": 1,          # Square (Instagram Feed)
    "4:5": 4/5,        # Portrait (Instagram Feed)
    "4:3": 4/3,        # Traditional TV
    "21:9": 21/9       # Ultra-wide
}

# Popular Hashtag Categories
HASHTAG_CATEGORIES = {
    "general": ["#viral", "#trending", "#fyp", "#explore", "#content"],
    "tech": ["#technology", "#ai", "#innovation", "#digital", "#future"],
    "lifestyle": ["#lifestyle", "#daily", "#motivation", "#inspiration", "#life"],
    "entertainment": ["#funny", "#entertainment", "#memes", "#comedy", "#fun"],
    "education": ["#education", "#learning", "#tutorial", "#howto", "#tips"],
    "business": ["#business", "#entrepreneur", "#marketing", "#success", "#growth"],
    "health": ["#health", "#fitness", "#wellness", "#selfcare", "#mindfulness"],
    "travel": ["#travel", "#wanderlust", "#adventure", "#explore", "#vacation"],
    "food": ["#food", "#cooking", "#recipe", "#foodie", "#delicious"],
    "fashion": ["#fashion", "#style", "#outfit", "#beauty", "#trend"]
}

# Best Posting Times (UTC)
OPTIMAL_POSTING_TIMES = {
    PlatformType.YOUTUBE: {
        "weekdays": [(14, 16), (20, 22)],  # 2-4 PM, 8-10 PM
        "weekends": [(9, 11), (14, 16)]    # 9-11 AM, 2-4 PM
    },
    PlatformType.TIKTOK: {
        "weekdays": [(6, 10), (19, 23)],   # 6-10 AM, 7-11 PM
        "weekends": [(9, 12), (19, 23)]    # 9 AM-12 PM, 7-11 PM
    },
    PlatformType.INSTAGRAM: {
        "weekdays": [(11, 13), (17, 19)],  # 11 AM-1 PM, 5-7 PM
        "weekends": [(10, 12), (14, 16)]   # 10 AM-12 PM, 2-4 PM
    },
    PlatformType.FACEBOOK: {
        "weekdays": [(13, 15), (20, 22)],  # 1-3 PM, 8-10 PM
        "weekends": [(12, 14), (19, 21)]   # 12-2 PM, 7-9 PM
    },
    PlatformType.TWITTER: {
        "weekdays": [(9, 10), (19, 20)],   # 9-10 AM, 7-8 PM
        "weekends": [(10, 11), (20, 21)]   # 10-11 AM, 8-9 PM
    },
    PlatformType.LINKEDIN: {
        "weekdays": [(8, 10), (17, 18)],   # 8-10 AM, 5-6 PM
        "weekends": []                      # Not recommended
    }
}

# Content Template Structures
CONTENT_TEMPLATES = {
    "educational": {
        "structure": ["hook", "problem", "solution", "explanation", "cta"],
        "duration": 60,
        "platforms": [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
    },
    "entertainment": {
        "structure": ["hook", "setup", "punchline", "reaction", "outro"],
        "duration": 30,
        "platforms": [PlatformType.TIKTOK, PlatformType.INSTAGRAM, PlatformType.TWITTER]
    },
    "news": {
        "structure": ["headline", "context", "details", "impact", "source"],
        "duration": 45,
        "platforms": [PlatformType.YOUTUBE, PlatformType.FACEBOOK, PlatformType.TWITTER]
    },
    "tutorial": {
        "structure": ["intro", "overview", "step1", "step2", "step3", "conclusion"],
        "duration": 120,
        "platforms": [PlatformType.YOUTUBE, PlatformType.INSTAGRAM]
    }
}

# Platform-Specific Optimization Settings
PLATFORM_OPTIMIZATIONS = {
    PlatformType.YOUTUBE: {
        "thumbnail_size": (1280, 720),
        "title_keywords": "beginning",  # Important keywords at the beginning
        "description_format": "detailed",
        "tags_importance": "high",
        "chapters_supported": True,
        "end_screen_duration": 20,
        "cards_supported": True,
        "premiere_supported": True,
        "shorts_max_duration": 60
    },
    
    PlatformType.TIKTOK: {
        "thumbnail_size": (1080, 1920),
        "title_keywords": "hashtags",
        "description_format": "concise",
        "tags_importance": "critical",
        "effects_supported": True,
        "duet_supported": True,
        "stitch_supported": True,
        "trending_sounds": True
    },
    
    PlatformType.INSTAGRAM: {
        "thumbnail_size": (1080, 1080),
        "title_keywords": "hashtags",
        "description_format": "engaging",
        "tags_importance": "high",
        "story_highlights": True,
        "igtv_supported": True,
        "reels_supported": True,
        "shopping_tags": True
    },
    
    PlatformType.FACEBOOK: {
        "thumbnail_size": (1200, 630),
        "title_keywords": "emotional",
        "description_format": "storytelling",
        "tags_importance": "medium",
        "live_streaming": True,
        "events_supported": True,
        "polls_supported": True,
        "reactions_tracking": True
    },
    
    PlatformType.TWITTER: {
        "thumbnail_size": (1200, 675),
        "title_keywords": "trending",
        "description_format": "concise",
        "tags_importance": "medium",
        "thread_supported": True,
        "spaces_supported": True,
        "moments_supported": True,
        "fleet_supported": False  # Discontinued
    },
    
    PlatformType.LINKEDIN: {
        "thumbnail_size": (1200, 627),
        "title_keywords": "professional",
        "description_format": "professional",
        "tags_importance": "low",
        "articles_supported": True,
        "polls_supported": True,
        "events_supported": True,
        "company_pages": True
    }
}

# Error Codes และ Messages สำหรับแต่ละ Platform
PLATFORM_ERROR_CODES = {
    PlatformType.YOUTUBE: {
        "quota_exceeded": "Daily quota exceeded",
        "invalid_format": "Unsupported video format",
        "copyright_claim": "Copyright content detected",
        "community_guidelines": "Community guidelines violation",
        "file_too_large": "File size exceeds limit",
        "duration_too_long": "Video duration exceeds limit"
    },
    
    PlatformType.TIKTOK: {
        "rate_limited": "Too many requests",
        "invalid_token": "Invalid access token",
        "content_moderated": "Content flagged by moderation",
        "file_corrupted": "Video file corrupted",
        "audio_copyright": "Copyrighted audio detected"
    },
    
    PlatformType.INSTAGRAM: {
        "media_limit": "Daily media upload limit reached",
        "hashtag_limit": "Too many hashtags",
        "story_expired": "Story upload window expired",
        "account_restricted": "Account temporarily restricted"
    },
    
    PlatformType.FACEBOOK: {
        "page_not_found": "Page not accessible",
        "permission_denied": "Insufficient permissions",
        "content_blocked": "Content blocked by policies",
        "spam_detected": "Content detected as spam"
    }
}

# Revenue และ Monetization Settings
MONETIZATION_REQUIREMENTS = {
    PlatformType.YOUTUBE: {
        "min_subscribers": 1000,
        "min_watch_hours": 4000,  # In past 12 months
        "shorts_views": 10000000,  # Alternative requirement
        "revenue_share": 0.55,     # Creator gets 55%
        "payment_threshold": 100   # USD
    },
    
    PlatformType.TIKTOK: {
        "min_followers": 10000,
        "min_age": 18,
        "creator_fund": True,
        "live_gifts": True,
        "brand_partnerships": True
    },
    
    PlatformType.INSTAGRAM: {
        "reels_play_bonus": True,
        "igtv_ads": True,
        "affiliate_marketing": True,
        "badges_in_live": True
    },
    
    PlatformType.FACEBOOK: {
        "min_followers": 10000,
        "page_monetization": True,
        "in_stream_ads": True,
        "fan_subscriptions": True,
        "stars_program": True
    }
}

# API Rate Limits สำหรับแต่ละ Platform
API_RATE_LIMITS = {
    PlatformType.YOUTUBE: {
        "quota_per_day": 10000,
        "uploads_per_day": 100,
        "search_requests": 100,
        "analytics_requests": 50
    },
    
    PlatformType.TIKTOK: {
        "uploads_per_day": 10,
        "api_calls_per_day": 1000,
        "user_info_requests": 100
    },
    
    PlatformType.INSTAGRAM: {
        "media_per_hour": 25,
        "api_calls_per_hour": 200,
        "story_uploads_per_day": 100
    },
    
    PlatformType.FACEBOOK: {
        "posts_per_hour": 25,
        "api_calls_per_hour": 200,
        "page_posts_per_day": 100
    }
}

# Content Classification และ Tags
CONTENT_CATEGORIES = {
    "entertainment": {
        "tags": ["comedy", "funny", "entertainment", "viral", "trending"],
        "audience": "general",
        "best_platforms": [PlatformType.TIKTOK, PlatformType.INSTAGRAM, PlatformType.YOUTUBE]
    },
    
    "education": {
        "tags": ["education", "learning", "tutorial", "howto", "tips"],
        "audience": "learners",
        "best_platforms": [PlatformType.YOUTUBE, PlatformType.LINKEDIN, PlatformType.INSTAGRAM]
    },
    
    "technology": {
        "tags": ["tech", "technology", "ai", "innovation", "digital"],
        "audience": "tech_enthusiasts",
        "best_platforms": [PlatformType.YOUTUBE, PlatformType.LINKEDIN, PlatformType.TWITTER]
    },
    
    "lifestyle": {
        "tags": ["lifestyle", "daily", "routine", "motivation", "wellness"],
        "audience": "general",
        "best_platforms": [PlatformType.INSTAGRAM, PlatformType.TIKTOK, PlatformType.FACEBOOK]
    },
    
    "business": {
        "tags": ["business", "entrepreneur", "marketing", "success", "finance"],
        "audience": "professionals",
        "best_platforms": [PlatformType.LINKEDIN, PlatformType.YOUTUBE, PlatformType.TWITTER]
    },
    
    "news": {
        "tags": ["news", "current", "breaking", "update", "politics"],
        "audience": "general",
        "best_platforms": [PlatformType.TWITTER, PlatformType.FACEBOOK, PlatformType.YOUTUBE]
    }
}

# Platform Authentication Requirements
AUTH_REQUIREMENTS = {
    PlatformType.YOUTUBE: {
        "oauth_scopes": [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly"
        ],
        "client_secrets": True,
        "refresh_token": True
    },
    
    PlatformType.TIKTOK: {
        "app_key": True,
        "app_secret": True,
        "access_token": True,
        "webhook_verification": True
    },
    
    PlatformType.INSTAGRAM: {
        "facebook_app_id": True,
        "facebook_app_secret": True,
        "instagram_business_account": True,
        "access_token": True
    },
    
    PlatformType.FACEBOOK: {
        "app_id": True,
        "app_secret": True,
        "page_access_token": True,
        "permissions": ["pages_manage_posts", "pages_read_engagement"]
    }
}

# Utility Functions
def get_platform_spec(platform: PlatformType) -> PlatformSpecs:
    """Get specifications for a specific platform"""
    return PLATFORM_SPECS.get(platform)

def get_optimal_resolution(platform: PlatformType, aspect_ratio: str = "16:9") -> Tuple[int, int]:
    """Get optimal resolution for platform and aspect ratio"""
    spec = get_platform_spec(platform)
    if not spec:
        return (1920, 1080)  # Default
    
    if aspect_ratio == "16:9":
        return spec.optimal_resolution
    elif aspect_ratio == "9:16":
        return (spec.optimal_resolution[1], spec.optimal_resolution[0])
    elif aspect_ratio == "1:1":
        size = min(spec.optimal_resolution)
        return (size, size)
    else:
        return spec.optimal_resolution

def is_format_supported(platform: PlatformType, file_format: str) -> bool:
    """Check if file format is supported by platform"""
    spec = get_platform_spec(platform)
    return spec and file_format.lower() in spec.supported_formats

def get_max_duration(platform: PlatformType) -> int:
    """Get maximum video duration for platform"""
    spec = get_platform_spec(platform)
    return spec.max_video_duration if spec else 3600  # Default 1 hour

def validate_title_length(platform: PlatformType, title: str) -> bool:
    """Validate title length for platform"""
    spec = get_platform_spec(platform)
    return spec and len(title) <= spec.max_title_length

def validate_description_length(platform: PlatformType, description: str) -> bool:
    """Validate description length for platform"""
    spec = get_platform_spec(platform)
    return spec and len(description) <= spec.max_description_length

def get_recommended_hashtags(category: str, platform: PlatformType, count: int = 5) -> List[str]:
    """Get recommended hashtags for content category and platform"""
    if category not in HASHTAG_CATEGORIES:
        category = "general"
    
    base_tags = HASHTAG_CATEGORIES[category]
    spec = get_platform_spec(platform)
    max_tags = spec.max_hashtags if spec else 10
    
    return base_tags[:min(count, max_tags)]

def get_best_posting_time(platform: PlatformType, is_weekend: bool = False) -> List[Tuple[int, int]]:
    """Get best posting times for platform"""
    times = OPTIMAL_POSTING_TIMES.get(platform, {})
    return times.get("weekends" if is_weekend else "weekdays", [(12, 14)])

def calculate_aspect_ratio(width: int, height: int) -> str:
    """Calculate aspect ratio from width and height"""
    ratio = width / height
    
    # Find closest standard aspect ratio
    closest_ratio = "16:9"
    closest_diff = abs(ratio - ASPECT_RATIOS["16:9"])
    
    for name, value in ASPECT_RATIOS.items():
        diff = abs(ratio - value)
        if diff < closest_diff:
            closest_diff = diff
            closest_ratio = name
    
    return closest_ratio

def get_platform_error_message(platform: PlatformType, error_code: str) -> str:
    """Get error message for platform and error code"""
    errors = PLATFORM_ERROR_CODES.get(platform, {})
    return errors.get(error_code, "Unknown error occurred")

def is_monetization_eligible(platform: PlatformType, stats: Dict[str, Any]) -> bool:
    """Check if account is eligible for monetization"""
    requirements = MONETIZATION_REQUIREMENTS.get(platform)
    if not requirements:
        return False
    
    if platform == PlatformType.YOUTUBE:
        return (stats.get("subscribers", 0) >= requirements["min_subscribers"] and
                stats.get("watch_hours", 0) >= requirements["min_watch_hours"])
    
    elif platform == PlatformType.TIKTOK:
        return (stats.get("followers", 0) >= requirements["min_followers"] and
                stats.get("age", 0) >= requirements["min_age"])
    
    elif platform == PlatformType.FACEBOOK:
        return stats.get("followers", 0) >= requirements["min_followers"]
    
    return True  # Default for platforms without specific requirements

# Export all important constants and functions
__all__ = [
    "PlatformType", "ContentType", "UploadStatus", "VideoQuality",
    "PLATFORM_SPECS", "VIDEO_RESOLUTIONS", "ASPECT_RATIOS",
    "HASHTAG_CATEGORIES", "OPTIMAL_POSTING_TIMES", "CONTENT_TEMPLATES",
    "PLATFORM_OPTIMIZATIONS", "PLATFORM_ERROR_CODES", "MONETIZATION_REQUIREMENTS",
    "API_RATE_LIMITS", "CONTENT_CATEGORIES", "AUTH_REQUIREMENTS",
    "get_platform_spec", "get_optimal_resolution", "is_format_supported",
    "get_max_duration", "validate_title_length", "validate_description_length",
    "get_recommended_hashtags", "get_best_posting_time", "calculate_aspect_ratio",
    "get_platform_error_message", "is_monetization_eligible"
]