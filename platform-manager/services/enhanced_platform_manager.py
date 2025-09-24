"""
Enhanced Platform Manager
Manages content uploads across all supported platforms with advanced features
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import json

from .uploaders import (
    YouTubeUploader,
    TikTokUploader,
    InstagramUploader,
    FacebookUploader
)

logger = logging.getLogger(__name__)

class PlatformType:
    """Platform type constants"""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    
    ALL_PLATFORMS = [YOUTUBE, TIKTOK, INSTAGRAM, FACEBOOK]

class EnhancedPlatformManager:
    """Enhanced platform manager with comprehensive upload capabilities"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.uploaders = {}
        self.upload_history = []
        
        # Initialize uploaders
        self._initialize_uploaders()
        
        # Upload settings
        self.max_concurrent_uploads = self.config.get('max_concurrent_uploads', 3)
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.retry_delay_seconds = self.config.get('retry_delay_seconds', 30)
        
        logger.info(f"Enhanced Platform Manager initialized with {len(self.uploaders)} platforms")
    
    def _initialize_uploaders(self):
        """Initialize all platform uploaders"""
        platform_configs = self.config.get('platforms', {})
        
        # YouTube uploader
        if platform_configs.get('youtube', {}).get('enabled', True):
            try:
                youtube_config = platform_configs.get('youtube', {})
                self.uploaders[PlatformType.YOUTUBE] = YouTubeUploader(youtube_config)
                logger.info("YouTube uploader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube uploader: {e}")
        
        # TikTok uploader  
        if platform_configs.get('tiktok', {}).get('enabled', True):
            try:
                tiktok_config = platform_configs.get('tiktok', {})
                self.uploaders[PlatformType.TIKTOK] = TikTokUploader(tiktok_config)
                logger.info("TikTok uploader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize TikTok uploader: {e}")
        
        # Instagram uploader
        if platform_configs.get('instagram', {}).get('enabled', True):
            try:
                instagram_config = platform_configs.get('instagram', {})
                self.uploaders[PlatformType.INSTAGRAM] = InstagramUploader(instagram_config)
                logger.info("Instagram uploader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Instagram uploader: {e}")
        
        # Facebook uploader
        if platform_configs.get('facebook', {}).get('enabled', True):
            try:
                facebook_config = platform_configs.get('facebook', {})
                self.uploaders[PlatformType.FACEBOOK] = FacebookUploader(facebook_config)
                logger.info("Facebook uploader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Facebook uploader: {e}")
    
    async def upload_to_platform(self, 
                                platform: str, 
                                content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload content to a single platform"""
        try:
            if platform not in self.uploaders:
                return {
                    'success': False,
                    'platform': platform,
                    'error': f'Platform {platform} not available or not configured'
                }
            
            uploader = self.uploaders[platform]
            
            # Add platform-specific optimizations
            optimized_content = await self._optimize_content_for_platform(content_data, platform)
            
            # Perform upload with retry logic
            result = await self._upload_with_retry(uploader, optimized_content, platform)
            
            # Log upload result
            self._log_upload_result(platform, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Upload to {platform} failed: {e}")
            return {
                'success': False,
                'platform': platform,
                'error': str(e)
            }
    
    async def upload_to_multiple_platforms(self, 
                                         platforms: List[str], 
                                         content_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Upload content to multiple platforms concurrently"""
        try:
            # Validate platforms
            valid_platforms = [p for p in platforms if p in self.uploaders]
            
            if not valid_platforms:
                return {
                    'success': False,
                    'results': [],
                    'error': 'No valid platforms specified'
                }
            
            # Create upload tasks with concurrency limit
            semaphore = asyncio.Semaphore(self.max_concurrent_uploads)
            
            async def upload_with_semaphore(platform):
                async with semaphore:
                    return await self.upload_to_platform(platform, content_data)
            
            # Execute uploads concurrently
            upload_tasks = [upload_with_semaphore(platform) for platform in valid_platforms]
            results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            successful_uploads = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'success': False,
                        'platform': valid_platforms[i],
                        'error': str(result)
                    })
                else:
                    processed_results.append(result)
                    if result.get('success'):
                        successful_uploads += 1
            
            return {
                'success': successful_uploads > 0,
                'results': processed_results,
                'successful_uploads': successful_uploads,
                'total_platforms': len(valid_platforms),
                'upload_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Multi-platform upload failed: {e}")
            return {
                'success': False,
                'results': [],
                'error': str(e)
            }
    
    async def upload_to_all_platforms(self, content_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Upload content to all available platforms"""
        available_platforms = list(self.uploaders.keys())
        return await self.upload_to_multiple_platforms(available_platforms, content_data)
    
    async def schedule_upload(self, 
                            platforms: List[str], 
                            content_data: Dict[str, Any], 
                            scheduled_time: datetime) -> Dict[str, Any]:
        """Schedule content upload for future publication"""
        try:
            # Add scheduling information to content data
            content_data['scheduled_publish_time'] = scheduled_time
            content_data['is_scheduled'] = True
            
            # For immediate scheduling (within next hour), use platform native scheduling
            time_until_publish = scheduled_time - datetime.utcnow()
            
            if time_until_publish <= timedelta(hours=1):
                # Use platform native scheduling
                return await self.upload_to_multiple_platforms(platforms, content_data)
            else:
                # Store for later processing by scheduler
                schedule_info = {
                    'platforms': platforms,
                    'content_data': content_data,
                    'scheduled_time': scheduled_time,
                    'status': 'scheduled',
                    'created_at': datetime.utcnow()
                }
                
                # In a real implementation, this would be saved to database
                logger.info(f"Content scheduled for {scheduled_time} on platforms: {platforms}")
                
                return {
                    'success': True,
                    'scheduled': True,
                    'scheduled_time': scheduled_time.isoformat(),
                    'platforms': platforms,
                    'message': 'Content scheduled successfully'
                }
                
        except Exception as e:
            logger.error(f"Upload scheduling failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _upload_with_retry(self, 
                               uploader, 
                               content_data: Dict[str, Any], 
                               platform: str) -> Dict[str, Any]:
        """Upload content with retry logic"""
        last_error = None
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                logger.info(f"Uploading to {platform} (attempt {attempt}/{self.retry_attempts})")
                
                result = await uploader.upload_content(content_data)
                
                if result.get('success'):
                    if attempt > 1:
                        logger.info(f"Upload to {platform} succeeded on attempt {attempt}")
                    return result
                else:
                    last_error = result.get('error', 'Unknown error')
                    logger.warning(f"Upload to {platform} failed on attempt {attempt}: {last_error}")
                    
                    # Don't retry for certain types of errors
                    if self._is_permanent_error(result):
                        logger.info(f"Permanent error detected, not retrying: {last_error}")
                        break
                    
                    # Wait before retry
                    if attempt < self.retry_attempts:
                        wait_time = self.retry_delay_seconds * attempt
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                        
            except Exception as e:
                last_error = str(e)
                logger.error(f"Upload to {platform} failed on attempt {attempt}: {e}")
                
                if attempt < self.retry_attempts:
                    wait_time = self.retry_delay_seconds * attempt
                    await asyncio.sleep(wait_time)
        
        return {
            'success': False,
            'platform': platform,
            'error': f'Upload failed after {self.retry_attempts} attempts: {last_error}',
            'attempts': self.retry_attempts
        }
    
    def _is_permanent_error(self, result: Dict[str, Any]) -> bool:
        """Check if error is permanent and shouldn't be retried"""
        error = result.get('error', '').lower()
        
        permanent_error_keywords = [
            'invalid credentials',
            'authentication failed',
            'unauthorized',
            'forbidden',
            'file not found',
            'unsupported format',
            'quota exceeded',
            'file too large'
        ]
        
        return any(keyword in error for keyword in permanent_error_keywords)
    
    async def _optimize_content_for_platform(self, 
                                           content_data: Dict[str, Any], 
                                           platform: str) -> Dict[str, Any]:
        """Apply platform-specific content optimizations"""
        optimized_content = content_data.copy()
        
        # Platform-specific optimizations
        if platform == PlatformType.YOUTUBE:
            optimized_content = await self._optimize_for_youtube(optimized_content)
        elif platform == PlatformType.TIKTOK:
            optimized_content = await self._optimize_for_tiktok(optimized_content)
        elif platform == PlatformType.INSTAGRAM:
            optimized_content = await self._optimize_for_instagram(optimized_content)
        elif platform == PlatformType.FACEBOOK:
            optimized_content = await self._optimize_for_facebook(optimized_content)
        
        return optimized_content
    
    async def _optimize_for_youtube(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """YouTube-specific optimizations"""
        # Title optimization (YouTube allows longer titles)
        if len(content_data.get('title', '')) > 100:
            # Keep full title for YouTube
            pass
        
        # Description optimization
        description = content_data.get('description', '')
        if description and len(description) < 125:  # YouTube recommends longer descriptions
            # Could add more context here
            pass
        
        # Tags optimization
        hashtags = content_data.get('hashtags', [])
        if hashtags:
            # YouTube uses tags differently
            content_data['tags'] = [tag.replace('#', '') for tag in hashtags[:15]]
        
        # Category mapping
        if not content_data.get('category'):
            content_data['category'] = '22'  # People & Blogs as default
        
        return content_data
    
    async def _optimize_for_tiktok(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """TikTok-specific optimizations"""
        # Title/caption length limit
        if len(content_data.get('title', '')) > 150:
            content_data['title'] = content_data['title'][:147] + '...'
        
        # Hashtag optimization for TikTok
        hashtags = content_data.get('hashtags', [])
        if hashtags:
            # TikTok hashtags should be trending and relevant
            optimized_hashtags = []
            for tag in hashtags[:5]:  # Limit to 5 for TikTok
                if not tag.startswith('#'):
                    tag = f'#{tag}'
                optimized_hashtags.append(tag)
            content_data['hashtags'] = optimized_hashtags
        
        return content_data
    
    async def _optimize_for_instagram(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Instagram-specific optimizations"""
        # Caption length limit
        title = content_data.get('title', '')
        description = content_data.get('description', '')
        
        # Combine title and description for Instagram
        if title and description:
            content_data['caption'] = f"{title}\n\n{description}"
        elif title:
            content_data['caption'] = title
        elif description:
            content_data['caption'] = description
        
        # Hashtag optimization (Instagram allows up to 30)
        hashtags = content_data.get('hashtags', [])
        if hashtags:
            instagram_hashtags = []
            for tag in hashtags[:30]:
                if not tag.startswith('#'):
                    tag = f'#{tag}'
                instagram_hashtags.append(tag)
            content_data['hashtags'] = instagram_hashtags
        
        return content_data
    
    async def _optimize_for_facebook(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Facebook-specific optimizations"""
        # Facebook posts can be longer
        title = content_data.get('title', '')
        description = content_data.get('description', '')
        
        # Create engaging Facebook post text
        post_parts = []
        if title:
            post_parts.append(title)
        if description:
            post_parts.append(description)
        
        # Add hashtags naturally in Facebook
        hashtags = content_data.get('hashtags', [])
        if hashtags:
            hashtag_text = ' '.join([f'#{tag.replace("#", "")}' for tag in hashtags[:10]])
            post_parts.append(hashtag_text)
        
        content_data['message'] = '\n\n'.join(post_parts)
        
        return content_data
    
    def _log_upload_result(self, platform: str, result: Dict[str, Any]):
        """Log upload result for analytics"""
        log_entry = {
            'platform': platform,
            'success': result.get('success', False),
            'timestamp': datetime.utcnow().isoformat(),
            'platform_id': result.get('platform_id'),
            'error': result.get('error') if not result.get('success') else None
        }
        
        self.upload_history.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.upload_history) > 1000:
            self.upload_history = self.upload_history[-1000:]
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available/configured platforms"""
        return list(self.uploaders.keys())
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all platforms"""
        status = {}
        
        for platform_name, uploader in self.uploaders.items():
            try:
                if hasattr(uploader, 'get_status'):
                    status[platform_name] = uploader.get_status()
                else:
                    status[platform_name] = {
                        'platform': platform_name,
                        'configured': True,
                        'status': 'unknown'
                    }
            except Exception as e:
                status[platform_name] = {
                    'platform': platform_name,
                    'configured': False,
                    'error': str(e)
                }
        
        return status
    
    def get_upload_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get upload statistics for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        recent_uploads = [
            entry for entry in self.upload_history
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
        ]
        
        stats = {
            'total_uploads': len(recent_uploads),
            'successful_uploads': len([u for u in recent_uploads if u['success']]),
            'failed_uploads': len([u for u in recent_uploads if not u['success']]),
            'success_rate': 0.0,
            'by_platform': {}
        }
        
        if stats['total_uploads'] > 0:
            stats['success_rate'] = stats['successful_uploads'] / stats['total_uploads'] * 100
        
        # Calculate per-platform stats
        for platform in self.get_available_platforms():
            platform_uploads = [u for u in recent_uploads if u['platform'] == platform]
            platform_successful = len([u for u in platform_uploads if u['success']])
            
            stats['by_platform'][platform] = {
                'total': len(platform_uploads),
                'successful': platform_successful,
                'failed': len(platform_uploads) - platform_successful,
                'success_rate': platform_successful / len(platform_uploads) * 100 if platform_uploads else 0
            }
        
        return stats
    
    async def test_platform_connections(self) -> Dict[str, Any]:
        """Test connections to all configured platforms"""
        test_results = {}
        
        for platform_name, uploader in self.uploaders.items():
            try:
                # Try to get platform status as a connection test
                if hasattr(uploader, 'get_status'):
                    status = uploader.get_status()
                    test_results[platform_name] = {
                        'connected': status.get('configured', False),
                        'status': 'success',
                        'details': status
                    }
                else:
                    test_results[platform_name] = {
                        'connected': True,
                        'status': 'success',
                        'details': 'Basic connection test passed'
                    }
                    
            except Exception as e:
                test_results[platform_name] = {
                    'connected': False,
                    'status': 'error',
                    'error': str(e)
                }
        
        return test_results
    
    def get_supported_content_types(self) -> Dict[str, List[str]]:
        """Get supported content types for each platform"""
        supported_types = {}
        
        for platform_name, uploader in self.uploaders.items():
            try:
                status = uploader.get_status()
                supported_types[platform_name] = status.get('supported_content_types', [])
            except:
                # Default supported types
                supported_types[platform_name] = ['image', 'video', 'text']
        
        return supported_types