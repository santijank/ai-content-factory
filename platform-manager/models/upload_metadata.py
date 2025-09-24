"""
Upload Metadata Models
กำหนดโครงสร้างข้อมูลสำหรับการอัปโหลดเนื้อหาไปยัง platforms ต่างๆ
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json

class PrivacyLevel(Enum):
    """ระดับความเป็นส่วนตัวของเนื้อหา"""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"
    SCHEDULED = "scheduled"

class ContentCategory(Enum):
    """หมวดหมู่เนื้อหา"""
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    GAMING = "gaming"
    MUSIC = "music"
    NEWS = "news"
    SPORTS = "sports"
    TECHNOLOGY = "technology"
    COMEDY = "comedy"
    LIFESTYLE = "lifestyle"
    TRAVEL = "travel"
    FOOD = "food"
    FITNESS = "fitness"
    BEAUTY = "beauty"
    BUSINESS = "business"
    SCIENCE = "science"

@dataclass
class UploadMetadata:
    """ข้อมูล metadata สำหรับการอัปโหลด"""
    
    # Basic metadata
    title: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = ContentCategory.ENTERTAINMENT.value
    
    # Media files
    thumbnail_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    
    # Privacy and scheduling
    privacy: str = PrivacyLevel.PUBLIC.value
    scheduled_time: Optional[datetime] = None
    
    # Platform-specific custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Additional metadata
    language: str = "th"  # Default to Thai
    location: Optional[Dict[str, Any]] = None
    audience_age_rating: Optional[str] = None
    
    def __post_init__(self):
        """ตรวจสอบและปรับแต่งข้อมูลหลังจากสร้าง object"""
        
        # Clean and validate title
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")
        self.title = self.title.strip()
        
        # Clean description
        self.description = self.description.strip() if self.description else ""
        
        # Clean and validate tags
        self.tags = [tag.strip() for tag in self.tags if tag.strip()]
        
        # Validate privacy level
        if self.privacy not in [p.value for p in PrivacyLevel]:
            self.privacy = PrivacyLevel.PUBLIC.value
        
        # Validate category
        if self.category not in [c.value for c in ContentCategory]:
            self.category = ContentCategory.ENTERTAINMENT.value
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "category": self.category,
            "thumbnail_path": self.thumbnail_path,
            "subtitle_path": self.subtitle_path,
            "privacy": self.privacy,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "custom_fields": self.custom_fields,
            "language": self.language,
            "location": self.location,
            "audience_age_rating": self.audience_age_rating
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadMetadata':
        """สร้าง object จาก dictionary"""
        
        # Handle scheduled_time conversion
        scheduled_time = None
        if data.get("scheduled_time"):
            if isinstance(data["scheduled_time"], str):
                scheduled_time = datetime.fromisoformat(data["scheduled_time"])
            elif isinstance(data["scheduled_time"], datetime):
                scheduled_time = data["scheduled_time"]
        
        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            category=data.get("category", ContentCategory.ENTERTAINMENT.value),
            thumbnail_path=data.get("thumbnail_path"),
            subtitle_path=data.get("subtitle_path"),
            privacy=data.get("privacy", PrivacyLevel.PUBLIC.value),
            scheduled_time=scheduled_time,
            custom_fields=data.get("custom_fields", {}),
            language=data.get("language", "th"),
            location=data.get("location"),
            audience_age_rating=data.get("audience_age_rating")
        )
    
    def clone(self) -> 'UploadMetadata':
        """สร้างสำเนาของ metadata"""
        return UploadMetadata.from_dict(self.to_dict())
    
    def adapt_for_platform(self, platform: str) -> 'UploadMetadata':
        """ปรับแต่ง metadata สำหรับ platform เฉพาะ"""
        
        adapted = self.clone()
        
        # Platform-specific adaptations
        if platform.lower() == "youtube":
            adapted = self._adapt_for_youtube(adapted)
        elif platform.lower() == "tiktok":
            adapted = self._adapt_for_tiktok(adapted)
        elif platform.lower() == "instagram":
            adapted = self._adapt_for_instagram(adapted)
        elif platform.lower() == "facebook":
            adapted = self._adapt_for_facebook(adapted)
        elif platform.lower() == "twitter":
            adapted = self._adapt_for_twitter(adapted)
        
        return adapted
    
    def _adapt_for_youtube(self, metadata: 'UploadMetadata') -> 'UploadMetadata':
        """ปรับแต่งสำหรับ YouTube"""
        
        # Limit title length
        if len(metadata.title) > 100:
            metadata.title = metadata.title[:97] + "..."
        
        # Limit description length
        if len(metadata.description) > 5000:
            metadata.description = metadata.description[:4997] + "..."
        
        # Add YouTube-specific fields
        metadata.custom_fields.update({
            "categoryId": self._get_youtube_category_id(metadata.category),
            "defaultLanguage": metadata.language,
            "embeddable": True,
            "publicStatsViewable": True,
            "madeForKids": False
        })
        
        return metadata
    
    def _adapt_for_tiktok(self, metadata: 'UploadMetadata') -> 'UploadMetadata':
        """ปรับแต่งสำหรับ TikTok"""
        
        # TikTok doesn't have separate title, combine with description
        if metadata.title:
            metadata.description = f"{metadata.title}\n\n{metadata.description}".strip()
        
        # Limit description length
        if len(metadata.description) > 300:
            metadata.description = metadata.description[:297] + "..."
        
        # Convert tags to hashtags and add to description
        hashtags = [f"#{tag.replace(' ', '')}" for tag in metadata.tags[:5]]
        if hashtags:
            hashtag_text = " " + " ".join(hashtags)
            available_space = 300 - len(metadata.description)
            if len(hashtag_text) <= available_space:
                metadata.description += hashtag_text
        
        # TikTok-specific fields
        metadata.custom_fields.update({
            "allows_comment": True,
            "allows_duet": True,
            "allows_stitch": True,
            "auto_add_music": False,
            "privacy_level": metadata.privacy
        })
        
        return metadata
    
    def _adapt_for_instagram(self, metadata: 'UploadMetadata') -> 'UploadMetadata':
        """ปรับแต่งสำหรับ Instagram"""
        
        # Instagram caption (combines title and description)
        caption = f"{metadata.title}\n\n{metadata.description}".strip() if metadata.title else metadata.description
        
        # Limit caption length
        if len(caption) > 2200:
            caption = caption[:2197] + "..."
        
        # Add hashtags
        hashtags = [f"#{tag.replace(' ', '')}" for tag in metadata.tags[:25]]
        if hashtags:
            hashtag_text = "\n\n" + " ".join(hashtags)
            available_space = 2200 - len(caption)
            if len(hashtag_text) <= available_space:
                caption += hashtag_text
        
        metadata.description = caption
        
        # Instagram-specific fields
        metadata.custom_fields.update({
            "caption": caption,
            "location_id": metadata.location.get("id") if metadata.location else None,
            "disable_comments": False,
            "like_and_view_counts_disabled": False
        })
        
        return metadata
    
    def _adapt_for_facebook(self, metadata: 'UploadMetadata') -> 'UploadMetadata':
        """ปรับแต่งสำหรับ Facebook"""
        
        # Facebook allows very long descriptions
        full_description = f"{metadata.title}\n\n{metadata.description}".strip() if metadata.title else metadata.description
        
        # Add hashtags
        hashtags = [f"#{tag.replace(' ', '')}" for tag in metadata.tags]
        if hashtags:
            full_description += "\n\n" + " ".join(hashtags)
        
        metadata.description = full_description
        
        # Facebook-specific fields
        metadata.custom_fields.update({
            "published": metadata.privacy == "public",
            "embeddable": True,
            "targeting": {},
            "call_to_action": None
        })
        
        return metadata
    
    def _adapt_for_twitter(self, metadata: 'UploadMetadata') -> 'UploadMetadata':
        """ปรับแต่งสำหรับ Twitter"""
        
        # Twitter has 280 character limit
        tweet_text = metadata.title if metadata.title else metadata.description
        
        # Add hashtags
        hashtags = [f"#{tag.replace(' ', '')}" for tag in metadata.tags[:3]]
        if hashtags:
            hashtag_text = " " + " ".join(hashtags)
            available_space = 280 - len(tweet_text)
            if len(hashtag_text) <= available_space:
                tweet_text += hashtag_text
        
        # Truncate if needed
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."
        
        metadata.description = tweet_text
        
        return metadata
    
    def _get_youtube_category_id(self, category: str) -> str:
        """แปลง category เป็น YouTube category ID"""
        
        category_mapping = {
            "entertainment": "24",
            "education": "27", 
            "gaming": "20",
            "music": "10",
            "news": "25",
            "sports": "17",
            "technology": "28",
            "comedy": "23",
            "lifestyle": "22",
            "travel": "19",
            "food": "26",
            "fitness": "17",
            "beauty": "26",
            "business": "27",
            "science": "28"
        }
        
        return category_mapping.get(category.lower(), "24")  # Default to Entertainment

@dataclass
class UploadResult:
    """ผลลัพธ์การอัปโหลด"""
    
    success: bool
    platform: str
    platform_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    upload_time: Optional[datetime] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    metadata_used: Optional[Dict[str, Any]] = None
    performance_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """ตั้งค่าเวลาอัปโหลดถ้าไม่ได้กำหนด"""
        if self.upload_time is None:
            self.upload_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "success": self.success,
            "platform": self.platform,
            "platform_id": self.platform_id,
            "url": self.url,
            "error": self.error,
            "upload_time": self.upload_time.isoformat() if self.upload_time else None,
            "file_size": self.file_size,
            "duration": self.duration,
            "metadata_used": self.metadata_used,
            "performance_data": self.performance_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadResult':
        """สร้าง object จาก dictionary"""
        
        upload_time = None
        if data.get("upload_time"):
            upload_time = datetime.fromisoformat(data["upload_time"])
        
        return cls(
            success=data.get("success", False),
            platform=data.get("platform", ""),
            platform_id=data.get("platform_id"),
            url=data.get("url"),
            error=data.get("error"),
            upload_time=upload_time,
            file_size=data.get("file_size"),
            duration=data.get("duration"),
            metadata_used=data.get("metadata_used"),
            performance_data=data.get("performance_data")
        )

@dataclass
class BatchUploadResult:
    """ผลลัพธ์การอัปโหลดแบบ batch"""
    
    batch_id: str
    total_items: int
    successful_uploads: List[UploadResult] = field(default_factory=list)
    failed_uploads: List[UploadResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def success_count(self) -> int:
        """จำนวนการอัปโหลดที่สำเร็จ"""
        return len(self.successful_uploads)
    
    @property
    def failure_count(self) -> int:
        """จำนวนการอัปโหลดที่ล้มเหลว"""
        return len(self.failed_uploads)
    
    @property
    def success_rate(self) -> float:
        """อัตราความสำเร็จเป็นเปอร์เซ็นต์"""
        if self.total_items == 0:
            return 0.0
        return (self.success_count / self.total_items) * 100
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """ระยะเวลาในการอัปโหลดทั้งหมด (วินาที)"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def add_result(self, result: UploadResult) -> None:
        """เพิ่มผลลัพธ์การอัปโหลด"""
        if result.success:
            self.successful_uploads.append(result)
        else:
            self.failed_uploads.append(result)
    
    def mark_completed(self) -> None:
        """ทำเครื่องหมายว่าการอัปโหลด batch เสร็จสิ้น"""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลงเป็น dictionary"""
        return {
            "batch_id": self.batch_id,
            "total_items": self.total_items,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "duration_seconds": self.duration_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "successful_uploads": [result.to_dict() for result in self.successful_uploads],
            "failed_uploads": [result.to_dict() for result in self.failed_uploads]
        }

@dataclass 
class PlatformCredentials:
    """ข้อมูลสำหรับเข้าสู่ระบบ platform"""
    
    platform: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    additional_credentials: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """ตรวจสอบว่าข้อมูลยังใช้ได้หรือไม่"""
        if self.expires_at and datetime.now() >= self.expires_at:
            return False
        
        # Platform-specific validation
        if self.platform.lower() == "youtube":
            return bool(self.access_token and self.client_id and self.client_secret)
        elif self.platform.lower() == "tiktok":
            return bool(self.access_token)
        elif self.platform.lower() == "instagram":
            return bool(self.access_token)
        elif self.platform.lower() == "facebook":
            return bool(self.access_token)
        
        return bool(self.api_key or self.access_token)
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """แปลงเป็น dictionary (ไม่รวม secrets โดยค่าเริ่มต้น)"""
        data = {
            "platform": self.platform,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_valid": self.is_valid()
        }
        
        if include_secrets:
            data.update({
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "additional_credentials": self.additional_credentials
            })
        
        return data

# Utility functions
def create_basic_metadata(title: str, description: str = "", tags: List[str] = None) -> UploadMetadata:
    """สร้าง metadata พื้นฐาน"""
    return UploadMetadata(
        title=title,
        description=description,
        tags=tags or []
    )

def create_scheduled_metadata(
    title: str, 
    description: str,
    scheduled_time: datetime,
    tags: List[str] = None
) -> UploadMetadata:
    """สร้าง metadata สำหรับการอัปโหลดแบบจัดเวลา"""
    return UploadMetadata(
        title=title,
        description=description,
        tags=tags or [],
        privacy=PrivacyLevel.SCHEDULED.value,
        scheduled_time=scheduled_time
    )

def validate_metadata(metadata: UploadMetadata) -> Dict[str, Any]:
    """ตรวจสอบความถูกต้องของ metadata"""
    
    errors = []
    warnings = []
    
    # Check title
    if not metadata.title:
        errors.append("Title is required")
    elif len(metadata.title) > 200:
        warnings.append("Title is very long, may be truncated on some platforms")
    
    # Check description length
    if len(metadata.description) > 10000:
        warnings.append("Description is very long, may be truncated on some platforms")
    
    # Check tags
    if len(metadata.tags) > 50:
        warnings.append("Too many tags, some platforms may ignore excess tags")
    
    # Check scheduled time
    if metadata.scheduled_time and metadata.scheduled_time <= datetime.now():
        errors.append("Scheduled time must be in the future")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }