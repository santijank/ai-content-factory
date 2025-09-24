"""
Instagram Content Uploader
Handles uploading various content types to Instagram using Instagram Basic Display API
and Instagram Graph API for business accounts
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import os
import json
from pathlib import Path
import hashlib
import time

logger = logging.getLogger(__name__)

class InstagramUploader:
    """Upload content to Instagram"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Instagram API credentials
        self.app_id = self._get_config_value('app_id', 'INSTAGRAM_APP_ID')
        self.app_secret = self._get_config_value('app_secret', 'INSTAGRAM_APP_SECRET')
        self.access_token = self._get_config_value('access_token', 'INSTAGRAM_ACCESS_TOKEN')
        self.business_account_id = self._get_config_value('business_account_id', 'INSTAGRAM_BUSINESS_ACCOUNT_ID')
        
        # API endpoints
        self.graph_api_version = self.config.get('graph_api_version', 'v18.0')
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"
        
        # Upload settings
        self.max_file_size_mb = self.config.get('max_file_size_mb', 100)  # Instagram limit
        self.supported_video_formats = self.config.get('supported_video_formats', ['.mp4', '.mov'])
        self.supported_image_formats = self.config.get('supported_image_formats', ['.jpg', '.jpeg', '.png'])
        self.max_caption_length = 2200  # Instagram caption limit
        self.max_hashtags = 30  # Instagram hashtag limit
        
        # Rate limiting
        self.requests_per_hour = 200  # Instagram API limit
        self.request_timestamps = []
        
        logger.info(f"Instagram uploader initialized (Business Account: {bool(self.business_account_id)})")
    
    def _get_config_value(self, config_key: str, env_key: str) -> Optional[str]:
        """Get configuration value from config or environment"""
        return self.config.get(config_key) or os.environ.get(env_key)
    
    async def upload_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main upload method for Instagram content"""
        try:
            if not self.access_token:
                return {
                    'success': False,
                    'error': 'Instagram access token not configured'
                }
            
            content_type = content_data.get('content_type', 'image')
            file_path = content_data.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'Content file not found'
                }
            
            # Validate file
            validation_result = await self._validate_file(file_path, content_type)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error']
                }
            
            # Apply rate limiting
            await self._apply_rate_limit()
            
            # Prepare content metadata
            upload_metadata = self._prepare_upload_metadata(content_data)
            
            # Upload based on content type
            if content_type == 'image':
                result = await self._upload_image(file_path, upload_metadata)
            elif content_type == 'video':
                result = await self._upload_video(file_path, upload_metadata)
            elif content_type == 'carousel':
                result = await self._upload_carousel(content_data.get('media_files', []), upload_metadata)
            elif content_type == 'story':
                result = await self._upload_story(file_path, upload_metadata)
            elif content_type == 'reel':
                result = await self._upload_reel(file_path, upload_metadata)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported content type: {content_type}'
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Instagram upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'instagram'
            }
    
    async def _upload_image(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload single image to Instagram"""
        try:
            # Step 1: Upload image to get media ID
            media_id = await self._upload_media_file(file_path, 'IMAGE')
            
            if not media_id:
                return {'success': False, 'error': 'Failed to upload image file'}
            
            # Step 2: Create media container
            container_result = await self._create_media_container(
                media_id=media_id,
                media_type='IMAGE',
                metadata=metadata
            )
            
            if not container_result['success']:
                return container_result
            
            # Step 3: Publish the container
            publish_result = await self._publish_media(container_result['container_id'])
            
            if publish_result['success']:
                return {
                    'success': True,
                    'platform_id': publish_result['media_id'],
                    'platform_url': f"https://www.instagram.com/p/{publish_result['media_id']}/",
                    'content_type': 'image',
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            
            return publish_result
            
        except Exception as e:
            logger.error(f"Instagram image upload failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_video(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload video to Instagram"""
        try:
            # Step 1: Upload video to get media ID
            media_id = await self._upload_media_file(file_path, 'VIDEO')
            
            if not media_id:
                return {'success': False, 'error': 'Failed to upload video file'}
            
            # Step 2: Create media container
            container_result = await self._create_media_container(
                media_id=media_id,
                media_type='VIDEO',
                metadata=metadata
            )
            
            if not container_result['success']:
                return container_result
            
            # Step 3: Wait for video processing
            processing_result = await self._wait_for_video_processing(container_result['container_id'])
            
            if not processing_result['success']:
                return processing_result
            
            # Step 4: Publish the container
            publish_result = await self._publish_media(container_result['container_id'])
            
            if publish_result['success']:
                return {
                    'success': True,
                    'platform_id': publish_result['media_id'],
                    'platform_url': f"https://www.instagram.com/p/{publish_result['media_id']}/",
                    'content_type': 'video',
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            
            return publish_result
            
        except Exception as e:
            logger.error(f"Instagram video upload failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_carousel(self, media_files: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload carousel post (multiple images/videos)"""
        try:
            if not media_files or len(media_files) < 2:
                return {'success': False, 'error': 'Carousel requires at least 2 media files'}
            
            if len(media_files) > 10:
                return {'success': False, 'error': 'Carousel supports maximum 10 media files'}
            
            # Upload all media files and get media IDs
            media_ids = []
            for file_path in media_files:
                if not os.path.exists(file_path):
                    logger.warning(f"Carousel media file not found: {file_path}")
                    continue
                
                # Determine media type
                file_extension = Path(file_path).suffix.lower()
                if file_extension in self.supported_image_formats:
                    media_type = 'IMAGE'
                elif file_extension in self.supported_video_formats:
                    media_type = 'VIDEO'
                else:
                    logger.warning(f"Unsupported carousel media format: {file_extension}")
                    continue
                
                media_id = await self._upload_media_file(file_path, media_type)
                if media_id:
                    media_ids.append({'media_id': media_id, 'media_type': media_type})
                    
                # Rate limiting between uploads
                await asyncio.sleep(1)
            
            if len(media_ids) < 2:
                return {'success': False, 'error': 'Failed to upload sufficient media for carousel'}
            
            # Create carousel container
            container_result = await self._create_carousel_container(media_ids, metadata)
            
            if not container_result['success']:
                return container_result
            
            # Publish carousel
            publish_result = await self._publish_media(container_result['container_id'])
            
            if publish_result['success']:
                return {
                    'success': True,
                    'platform_id': publish_result['media_id'],
                    'platform_url': f"https://www.instagram.com/p/{publish_result['media_id']}/",
                    'content_type': 'carousel',
                    'media_count': len(media_ids),
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            
            return publish_result
            
        except Exception as e:
            logger.error(f"Instagram carousel upload failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_story(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload Instagram Story"""
        try:
            # Determine media type
            file_extension = Path(file_path).suffix.lower()
            if file_extension in self.supported_image_formats:
                media_type = 'STORIES'
            elif file_extension in self.supported_video_formats:
                media_type = 'STORIES'  # Instagram handles both image and video stories
            else:
                return {'success': False, 'error': 'Unsupported story media format'}
            
            # Upload media file
            media_id = await self._upload_media_file(file_path, media_type)
            
            if not media_id:
                return {'success': False, 'error': 'Failed to upload story media'}
            
            # Create story container
            container_result = await self._create_media_container(
                media_id=media_id,
                media_type=media_type,
                metadata=metadata
            )
            
            if not container_result['success']:
                return container_result
            
            # Publish story
            publish_result = await self._publish_media(container_result['container_id'])
            
            if publish_result['success']:
                return {
                    'success': True,
                    'platform_id': publish_result['media_id'],
                    'platform_url': f"https://www.instagram.com/stories/{self.business_account_id}/{publish_result['media_id']}/",
                    'content_type': 'story',
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            
            return publish_result
            
        except Exception as e:
            logger.error(f"Instagram story upload failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_reel(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload Instagram Reel"""
        try:
            # Validate video file for reels
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in self.supported_video_formats:
                return {'success': False, 'error': 'Reels require video format (MP4 or MOV)'}
            
            # Upload video file
            media_id = await self._upload_media_file(file_path, 'REELS')
            
            if not media_id:
                return {'success': False, 'error': 'Failed to upload reel video'}
            
            # Create reel container
            container_result = await self._create_media_container(
                media_id=media_id,
                media_type='REELS',
                metadata=metadata
            )
            
            if not container_result['success']:
                return container_result
            
            # Wait for video processing
            processing_result = await self._wait_for_video_processing(container_result['container_id'])
            
            if not processing_result['success']:
                return processing_result
            
            # Publish reel
            publish_result = await self._publish_media(container_result['container_id'])
            
            if publish_result['success']:
                return {
                    'success': True,
                    'platform_id': publish_result['media_id'],
                    'platform_url': f"https://www.instagram.com/reel/{publish_result['media_id']}/",
                    'content_type': 'reel',
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            
            return publish_result
            
        except Exception as e:
            logger.error(f"Instagram reel upload failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_media_file(self, file_path: str, media_type: str) -> Optional[str]:
        """Upload media file and get media ID"""
        try:
            if not self.business_account_id:
                logger.error("Business account ID required for media upload")
                return None
            
            url = f"{self.base_url}/{self.business_account_id}/media"
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            
            # Add file
            with open(file_path, 'rb') as f:
                filename = Path(file_path).name
                data.add_field('source', f, filename=filename)
            
            # Add media type
            data.add_field('media_type', media_type)
            data.add_field('access_token', self.access_token)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, timeout=300) as response:  # 5 min timeout for large files
                    if response.status == 200:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error_text = await response.text()
                        logger.error(f"Media upload failed: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error uploading media file: {e}")
            return None
    
    async def _create_media_container(self, 
                                    media_id: str, 
                                    media_type: str, 
                                    metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create media container with caption and metadata"""
        try:
            url = f"{self.base_url}/{self.business_account_id}/media"
            
            params = {
                'access_token': self.access_token,
                'media_type': media_type,
                'media_id': media_id
            }
            
            # Add caption if provided
            if metadata.get('caption'):
                params['caption'] = metadata['caption']
            
            # Add location if provided
            if metadata.get('location_id'):
                params['location_id'] = metadata['location_id']
            
            # Add user tags if provided
            if metadata.get('user_tags'):
                params['user_tags'] = json.dumps(metadata['user_tags'])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'container_id': result.get('id')
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Container creation failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Container creation failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error creating media container: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _create_carousel_container(self, 
                                       media_items: List[Dict[str, Any]], 
                                       metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create carousel container"""
        try:
            url = f"{self.base_url}/{self.business_account_id}/media"
            
            params = {
                'access_token': self.access_token,
                'media_type': 'CAROUSEL',
                'children': ','.join([item['media_id'] for item in media_items])
            }
            
            # Add caption if provided
            if metadata.get('caption'):
                params['caption'] = metadata['caption']
            
            # Add location if provided
            if metadata.get('location_id'):
                params['location_id'] = metadata['location_id']
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'container_id': result.get('id')
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Carousel container creation failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Carousel container creation failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error creating carousel container: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _wait_for_video_processing(self, container_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """Wait for video processing to complete"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # Check container status
                url = f"{self.base_url}/{container_id}"
                params = {
                    'access_token': self.access_token,
                    'fields': 'status_code,status'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            status_code = result.get('status_code')
                            
                            if status_code == 'FINISHED':
                                return {'success': True}
                            elif status_code == 'ERROR':
                                return {
                                    'success': False,
                                    'error': 'Video processing failed'
                                }
                            elif status_code == 'IN_PROGRESS':
                                # Continue waiting
                                await asyncio.sleep(5)
                                continue
                            else:
                                logger.warning(f"Unknown status code: {status_code}")
                                await asyncio.sleep(5)
                                continue
                        else:
                            error_text = await response.text()
                            logger.error(f"Status check failed: {response.status} - {error_text}")
                            await asyncio.sleep(5)
                            continue
            
            return {
                'success': False,
                'error': 'Video processing timeout'
            }
            
        except Exception as e:
            logger.error(f"Error waiting for video processing: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _publish_media(self, container_id: str) -> Dict[str, Any]:
        """Publish media container"""
        try:
            url = f"{self.base_url}/{self.business_account_id}/media_publish"
            
            params = {
                'access_token': self.access_token,
                'creation_id': container_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'media_id': result.get('id')
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Media publish failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Media publish failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error publishing media: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _validate_file(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """Validate file for Instagram upload"""
        try:
            if not os.path.exists(file_path):
                return {'valid': False, 'error': 'File does not exist'}
            
            file_path_obj = Path(file_path)
            file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
            file_extension = file_path_obj.suffix.lower()
            
            # Check file size
            if file_size_mb > self.max_file_size_mb:
                return {
                    'valid': False,
                    'error': f'File size {file_size_mb:.1f}MB exceeds limit {self.max_file_size_mb}MB'
                }
            
            # Check file format based on content type
            if content_type in ['image', 'story'] and file_extension not in self.supported_image_formats:
                if file_extension not in self.supported_video_formats:
                    return {
                        'valid': False,
                        'error': f'Unsupported file format: {file_extension}'
                    }
            elif content_type in ['video', 'reel'] and file_extension not in self.supported_video_formats:
                return {
                    'valid': False,
                    'error': f'Unsupported video format: {file_extension}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _prepare_upload_metadata(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for upload"""
        metadata = {}
        
        # Prepare caption with hashtags
        caption_parts = []
        
        if content_data.get('title'):
            caption_parts.append(content_data['title'])
        
        if content_data.get('description'):
            caption_parts.append(content_data['description'])
        
        # Add hashtags
        hashtags = content_data.get('hashtags', [])
        if hashtags:
            # Limit hashtags to Instagram's limit
            hashtags = hashtags[:self.max_hashtags]
            # Ensure hashtags start with #
            hashtags = [tag if tag.startswith('#') else f'#{tag}' for tag in hashtags]
            caption_parts.append(' '.join(hashtags))
        
        # Combine caption parts
        full_caption = '\n\n'.join(caption_parts)
        
        # Limit caption length
        if len(full_caption) > self.max_caption_length:
            full_caption = full_caption[:self.max_caption_length - 3] + '...'
        
        metadata['caption'] = full_caption
        
        # Add location if provided
        if content_data.get('location_id'):
            metadata['location_id'] = content_data['location_id']
        
        # Add user tags if provided
        if content_data.get('user_tags'):
            metadata['user_tags'] = content_data['user_tags']
        
        return metadata
    
    async def _apply_rate_limit(self):
        """Apply Instagram API rate limiting"""
        current_time = time.time()
        
        # Remove timestamps older than 1 hour
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 3600
        ]
        
        # Check if we're at the rate limit
        if len(self.request_timestamps) >= self.requests_per_hour:
            # Wait until the oldest request is more than 1 hour old
            oldest_request = self.request_timestamps[0]
            wait_time = 3600 - (current_time - oldest_request)
            
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current request timestamp
        self.request_timestamps.append(current_time)
    
    async def get_media_info(self, media_id: str) -> Dict[str, Any]:
        """Get information about uploaded media"""
        try:
            url = f"{self.base_url}/{media_id}"
            params = {
                'access_token': self.access_token,
                'fields': 'id,media_type,media_url,permalink,timestamp,caption'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get media info: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error getting media info: {e}")
            return {}
    
    async def delete_media(self, media_id: str) -> bool:
        """Delete media from Instagram"""
        try:
            url = f"{self.base_url}/{media_id}"
            params = {'access_token': self.access_token}
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, params=params) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error deleting media: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get uploader status information"""
        return {
            'platform': 'instagram',
            'configured': bool(self.access_token and self.business_account_id),
            'business_account': bool(self.business_account_id),
            'supported_formats': {
                'images': self.supported_image_formats,
                'videos': self.supported_video_formats
            },
            'limits': {
                'max_file_size_mb': self.max_file_size_mb,
                'max_caption_length': self.max_caption_length,
                'max_hashtags': self.max_hashtags,
                'requests_per_hour': self.requests_per_hour
            },
            'features': {
                'images': True,
                'videos': True,
                'carousel': True,
                'stories': True,
                'reels': True
            }
        }