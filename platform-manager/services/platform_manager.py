"""
Platform Manager Service
จัดการการอัปโหลดเนื้อหาไปยัง social media platforms ต่างๆ
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.platform_type import PlatformType
from ..models.upload_metadata import UploadMetadata, UploadResult
from ..utils.content_optimizer import ContentOptimizer

from .uploaders.youtube_uploader import YouTubeUploader
from .uploaders.tiktok_uploader import TikTokUploader
from .uploaders.instagram_uploader import InstagramUploader
from .uploaders.facebook_uploader import FacebookUploader

logger = logging.getLogger(__name__)

class PlatformManager:
    """หลักการจัดการ platform ทั้งหมด"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.content_optimizer = ContentOptimizer()
        
        # Initialize uploaders
        self.uploaders = {
            PlatformType.YOUTUBE: YouTubeUploader(config_manager),
            PlatformType.TIKTOK: TikTokUploader(config_manager),
            PlatformType.INSTAGRAM: InstagramUploader(config_manager),
            PlatformType.FACEBOOK: FacebookUploader(config_manager)
        }
        
        # Track upload statistics
        self.upload_stats = {
            "total_uploads": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "platform_stats": {}
        }
        
        logger.info("Platform Manager initialized")

    async def test_connections(self) -> Dict[str, bool]:
        """ทดสอบการเชื่อมต่อกับ platforms ทั้งหมด"""
        
        connection_results = {}
        
        for platform_type, uploader in self.uploaders.items():
            try:
                logger.info(f"Testing connection to {platform_type.value}")
                
                # Test platform connection
                is_connected = await uploader.test_connection()
                connection_results[platform_type.value] = is_connected
                
                if is_connected:
                    logger.info(f"✅ {platform_type.value} connection successful")
                else:
                    logger.warning(f"❌ {platform_type.value} connection failed")
                    
            except Exception as e:
                logger.error(f"Error testing {platform_type.value}: {str(e)}")
                connection_results[platform_type.value] = False
        
        return connection_results

    async def upload_content(
        self, 
        content_path: str, 
        platforms: List[str], 
        metadata: UploadMetadata
    ) -> Dict[str, UploadResult]:
        """อัปโหลดเนื้อหาไปยัง platforms ที่กำหนด"""
        
        logger.info(f"Starting upload to platforms: {platforms}")
        upload_results = {}
        
        # Create upload tasks for each platform
        upload_tasks = []
        
        for platform_name in platforms:
            try:
                platform_type = self._get_platform_type(platform_name)
                if platform_type in self.uploaders:
                    task = self._upload_to_platform(
                        platform_type, content_path, metadata
                    )
                    upload_tasks.append((platform_name, task))
                else:
                    # Unknown platform
                    upload_results[platform_name] = UploadResult(
                        success=False,
                        error=f"Unknown platform: {platform_name}",
                        platform=platform_name
                    )
            except Exception as e:
                logger.error(f"Error preparing upload for {platform_name}: {str(e)}")
                upload_results[platform_name] = UploadResult(
                    success=False,
                    error=str(e),
                    platform=platform_name
                )
        
        # Execute uploads concurrently
        if upload_tasks:
            task_results = await asyncio.gather(
                *[task for _, task in upload_tasks],
                return_exceptions=True
            )
            
            # Process results
            for i, (platform_name, _) in enumerate(upload_tasks):
                result = task_results[i]
                
                if isinstance(result, Exception):
                    upload_results[platform_name] = UploadResult(
                        success=False,
                        error=str(result),
                        platform=platform_name
                    )
                else:
                    upload_results[platform_name] = result
        
        # Update statistics
        self._update_stats(upload_results)
        
        logger.info(f"Upload completed. Results: {len(upload_results)} platforms")
        return upload_results

    async def _upload_to_platform(
        self, 
        platform_type: PlatformType, 
        content_path: str, 
        metadata: UploadMetadata
    ) -> UploadResult:
        """อัปโหลดไปยัง platform เดียว"""
        
        try:
            logger.info(f"Uploading to {platform_type.value}")
            
            # Optimize content for platform
            optimized_path = await self._optimize_content_for_platform(
                content_path, platform_type
            )
            
            # Adapt metadata for platform
            platform_metadata = await self._adapt_metadata_for_platform(
                metadata, platform_type
            )
            
            # Get uploader
            uploader = self.uploaders[platform_type]
            
            # Perform upload
            result = await uploader.upload(optimized_path, platform_metadata)
            
            if result.success:
                logger.info(f"✅ Upload to {platform_type.value} successful: {result.url}")
            else:
                logger.error(f"❌ Upload to {platform_type.value} failed: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading to {platform_type.value}: {str(e)}")
            return UploadResult(
                success=False,
                error=str(e),
                platform=platform_type.value
            )

    async def _optimize_content_for_platform(
        self, 
        content_path: str, 
        platform_type: PlatformType
    ) -> str:
        """ปรับแต่งเนื้อหาให้เหมาะสมกับ platform"""
        
        try:
            # Get platform-specific optimization settings
            optimization_settings = self._get_optimization_settings(platform_type)
            
            # Optimize content
            optimized_path = self.content_optimizer.optimize_for_platform(
                content_path, 
                platform_type.value,
                optimization_settings
            )
            
            logger.debug(f"Content optimized for {platform_type.value}: {optimized_path}")
            return optimized_path
            
        except Exception as e:
            logger.warning(f"Content optimization failed for {platform_type.value}: {str(e)}")
            # Return original path if optimization fails
            return content_path

    async def _adapt_metadata_for_platform(
        self, 
        metadata: UploadMetadata, 
        platform_type: PlatformType
    ) -> UploadMetadata:
        """ปรับ metadata ให้เหมาะสมกับ platform"""
        
        try:
            adapted_metadata = UploadMetadata(
                title=metadata.title,
                description=metadata.description,
                tags=metadata.tags,
                category=metadata.category,
                thumbnail_path=metadata.thumbnail_path,
                privacy=metadata.privacy,
                scheduled_time=metadata.scheduled_time,
                custom_fields=metadata.custom_fields.copy()
            )
            
            # Platform-specific adaptations
            if platform_type == PlatformType.YOUTUBE:
                adapted_metadata = self._adapt_for_youtube(adapted_metadata)
            elif platform_type == PlatformType.TIKTOK:
                adapted_metadata = self._adapt_for_tiktok(adapted_metadata)
            elif platform_type == PlatformType.INSTAGRAM:
                adapted_metadata = self._adapt_for_instagram(adapted_metadata)
            elif platform_type == PlatformType.FACEBOOK:
                adapted_metadata = self._adapt_for_facebook(adapted_metadata)
            
            return adapted_metadata
            
        except Exception as e:
            logger.warning(f"Metadata adaptation failed for {platform_type.value}: {str(e)}")
            return metadata

    def _adapt_for_youtube(self, metadata: UploadMetadata) -> UploadMetadata:
        """ปรับ metadata สำหรับ YouTube"""
        
        # YouTube allows longer titles and descriptions
        if len(metadata.title) > 100:
            metadata.title = metadata.title[:97] + "..."
        
        # Add YouTube-specific tags
        if "youtube" not in [tag.lower() for tag in metadata.tags]:
            metadata.tags.append("YouTube")
        
        # Set YouTube category if not specified
        if not metadata.category:
            metadata.category = "Entertainment"
        
        # YouTube-specific custom fields
        metadata.custom_fields.update({
            "categoryId": self._get_youtube_category_id(metadata.category),
            "defaultLanguage": "th",
            "embeddable": True,
            "publicStatsViewable": True
        })
        
        return metadata

    def _adapt_for_tiktok(self, metadata: UploadMetadata) -> UploadMetadata:
        """ปรับ metadata สำหรับ TikTok"""
        
        # TikTok has shorter character limits
        if len(metadata.description) > 300:
            metadata.description = metadata.description[:297] + "..."
        
        # Convert tags to hashtags
        hashtags = [f"#{tag.replace(' ', '')}" for tag in metadata.tags[:5]]  # Max 5 hashtags
        
        # Add hashtags to description
        if hashtags:
            hashtag_text = " " + " ".join(hashtags)
            available_space = 300 - len(metadata.description)
            if len(hashtag_text) <= available_space:
                metadata.description += hashtag_text
        
        # TikTok-specific settings
        metadata.custom_fields.update({
            "allows_comment": True,
            "allows_duet": True,
            "allows_stitch": True,
            "auto_add_music": False
        })
        
        return metadata

    def _adapt_for_instagram(self, metadata: UploadMetadata) -> UploadMetadata:
        """ปรับ metadata สำหรับ Instagram"""
        
        # Instagram caption limit
        if len(metadata.description) > 2200:
            metadata.description = metadata.description[:2197] + "..."
        
        # Instagram hashtags (max 30)
        hashtags = [f"#{tag.replace(' ', '')}" for tag in metadata.tags[:25]]
        
        # Add hashtags to description
        if hashtags:
            hashtag_text = "\n\n" + " ".join(hashtags)
            available_space = 2200 - len(metadata.description)
            if len(hashtag_text) <= available_space:
                metadata.description += hashtag_text
        
        # Instagram-specific settings
        metadata.custom_fields.update({
            "location_id": None,
            "disable_comments": False,
            "is_story": False
        })
        
        return metadata

    def _adapt_for_facebook(self, metadata: UploadMetadata) -> UploadMetadata:
        """ปรับ metadata สำหรับ Facebook"""
        
        # Facebook allows long descriptions
        # Convert tags to hashtags
        hashtags = [f"#{tag.replace(' ', '')}" for tag in metadata.tags]
        
        if hashtags:
            hashtag_text = "\n\n" + " ".join(hashtags)
            metadata.description += hashtag_text
        
        # Facebook-specific settings
        metadata.custom_fields.update({
            "published": metadata.privacy == "public",
            "embeddable": True,
            "targeting": {}
        })
        
        return metadata

    def _get_optimization_settings(self, platform_type: PlatformType) -> Dict[str, Any]:
        """ได้รับการตั้งค่าการปรับแต่งสำหรับ platform"""
        
        settings = {
            PlatformType.YOUTUBE: {
                "max_file_size": "128GB",
                "recommended_formats": ["MP4", "MOV", "AVI"],
                "max_duration": 43200,  # 12 hours
                "aspect_ratios": ["16:9", "9:16", "1:1"]
            },
            PlatformType.TIKTOK: {
                "max_file_size": "4GB",
                "recommended_formats": ["MP4", "MOV"],
                "max_duration": 600,  # 10 minutes
                "aspect_ratios": ["9:16"]
            },
            PlatformType.INSTAGRAM: {
                "max_file_size": "4GB",
                "recommended_formats": ["MP4", "MOV"],
                "max_duration": 90,  # 90 seconds for reels
                "aspect_ratios": ["9:16", "1:1"]
            },
            PlatformType.FACEBOOK: {
                "max_file_size": "10GB",
                "recommended_formats": ["MP4", "MOV"],
                "max_duration": 7200,  # 2 hours
                "aspect_ratios": ["16:9", "1:1", "9:16"]
            }
        }
        
        return settings.get(platform_type, {})

    def _get_youtube_category_id(self, category: str) -> str:
        """แปลง category เป็น YouTube category ID"""
        
        category_mapping = {
            "entertainment": "24",
            "education": "27",
            "gaming": "20",
            "music": "10",
            "news": "25",
            "sports": "17",
            "tech": "28",
            "comedy": "23",
            "lifestyle": "22"
        }
        
        return category_mapping.get(category.lower(), "24")  # Default to Entertainment

    def _get_platform_type(self, platform_name: str) -> PlatformType:
        """แปลง platform name เป็น PlatformType"""
        
        platform_mapping = {
            "youtube": PlatformType.YOUTUBE,
            "tiktok": PlatformType.TIKTOK,
            "instagram": PlatformType.INSTAGRAM,
            "facebook": PlatformType.FACEBOOK
        }
        
        return platform_mapping.get(platform_name.lower(), PlatformType.YOUTUBE)

    def _update_stats(self, upload_results: Dict[str, UploadResult]) -> None:
        """อัปเดตสถิติการอัปโหลด"""
        
        self.upload_stats["total_uploads"] += len(upload_results)
        
        for platform, result in upload_results.items():
            if result.success:
                self.upload_stats["successful_uploads"] += 1
            else:
                self.upload_stats["failed_uploads"] += 1
            
            # Update platform-specific stats
            if platform not in self.upload_stats["platform_stats"]:
                self.upload_stats["platform_stats"][platform] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0
                }
            
            self.upload_stats["platform_stats"][platform]["total"] += 1
            if result.success:
                self.upload_stats["platform_stats"][platform]["successful"] += 1
            else:
                self.upload_stats["platform_stats"][platform]["failed"] += 1

    def get_available_platforms(self) -> List[str]:
        """ได้รับรายการ platforms ที่พร้อมใช้งาน"""
        
        return [platform_type.value for platform_type in self.uploaders.keys()]

    def get_platforms_status(self) -> Dict[str, Any]:
        """ได้รับสถานะของ platforms ทั้งหมด"""
        
        platforms_status = {}
        
        for platform_type, uploader in self.uploaders.items():
            platform_name = platform_type.value
            stats = self.upload_stats["platform_stats"].get(platform_name, {
                "total": 0, "successful": 0, "failed": 0
            })
            
            platforms_status[platform_name] = {
                "available": uploader.is_configured(),
                "total_uploads": stats["total"],
                "successful_uploads": stats["successful"],
                "failed_uploads": stats["failed"],
                "success_rate": (
                    stats["successful"] / stats["total"] * 100 
                    if stats["total"] > 0 else 0
                ),
                "last_upload": None,  # Could be tracked if needed
                "rate_limit_status": uploader.get_rate_limit_status()
            }
        
        return platforms_status

    def get_upload_stats(self) -> Dict[str, Any]:
        """ได้รับสถิติการอัปโหลดทั้งหมด"""
        
        stats = self.upload_stats.copy()
        
        # Calculate overall success rate
        total = stats["total_uploads"]
        successful = stats["successful_uploads"]
        stats["overall_success_rate"] = (successful / total * 100) if total > 0 else 0
        
        return stats

    async def schedule_upload(
        self, 
        content_path: str, 
        platforms: List[str], 
        metadata: UploadMetadata,
        scheduled_time: datetime
    ) -> str:
        """จัดเวลาการอัปโหลด"""
        
        # This would integrate with a task scheduler like Celery
        # For now, we'll return a task ID
        task_id = f"scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Upload scheduled for {scheduled_time} with task ID: {task_id}")
        
        # In a real implementation, this would:
        # 1. Store the task in a queue/database
        # 2. Schedule execution at the specified time
        # 3. Return the task ID for tracking
        
        return task_id

    async def cancel_upload(self, task_id: str) -> bool:
        """ยกเลิกการอัปโหลด"""
        
        # This would cancel a scheduled or in-progress upload
        logger.info(f"Attempting to cancel upload task: {task_id}")
        
        # Implementation would depend on the task scheduler being used
        return True

    def cleanup_temporary_files(self, file_paths: List[str]) -> None:
        """ทำความสะอาดไฟล์ชั่วคราว"""
        
        import os
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path) and "temp" in file_path:
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {str(e)}")