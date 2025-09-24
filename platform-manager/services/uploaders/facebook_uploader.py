"""
Facebook Content Uploader
Handles uploading various content types to Facebook using Facebook Graph API
Supports pages, profiles, and groups
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import os
import json
from pathlib import Path
import hashlib
import time
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class FacebookUploader:
    """Upload content to Facebook"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Facebook API credentials
        self.app_id = self._get_config_value('app_id', 'FACEBOOK_APP_ID')
        self.app_secret = self._get_config_value('app_secret', 'FACEBOOK_APP_SECRET')
        self.access_token = self._get_config_value('access_token', 'FACEBOOK_ACCESS_TOKEN')
        self.page_id = self._get_config_value('page_id', 'FACEBOOK_PAGE_ID')
        self.page_access_token = self._get_config_value('page_access_token', 'FACEBOOK_PAGE_ACCESS_TOKEN')
        
        # API settings
        self.graph_api_version = self.config.get('graph_api_version', 'v18.0')
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"
        
        # Upload settings
        self.max_file_size_mb = self.config.get('max_file_size_mb', 4096)  # Facebook limit: 4GB
        self.max_video_size_mb = self.config.get('max_video_size_mb', 10240)  # 10GB for videos
        self.supported_video_formats = self.config.get('supported_video_formats', ['.mp4', '.mov', '.avi'])
        self.supported_image_formats = self.config.get('supported_image_formats', ['.jpg', '.jpeg', '.png', '.gif'])
        self.max_post_length = 63206  # Facebook post character limit
        
        # Rate limiting
        self.requests_per_hour = 600  # Facebook API limit varies by app
        self.request_timestamps = []
        
        # Content types
        self.supported_content_types = [
            'text', 'image', 'video', 'link', 'event', 'live_video'
        ]
        
        logger.info(f"Facebook uploader initialized (Page: {bool(self.page_id)})")
    
    def _get_config_value(self, config_key: str, env_key: str) -> Optional[str]:
        """Get configuration value from config or environment"""
        return self.config.get(config_key) or os.environ.get(env_key)
    
    async def upload_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main upload method for Facebook content"""
        try:
            if not self._validate_credentials():
                return {
                    'success': False,
                    'error': 'Facebook credentials not properly configured'
                }
            
            content_type = content_data.get('content_type', 'text')
            
            if content_type not in self.supported_content_types:
                return {
                    'success': False,
                    'error': f'Unsupported content type: {content_type}'
                }
            
            # Apply rate limiting
            await self._apply_rate_limit()
            
            # Route to appropriate upload method
            if content_type == 'text':
                result = await self._upload_text_post(content_data)
            elif content_type == 'image':
                result = await self._upload_image_post(content_data)
            elif content_type == 'video':
                result = await self._upload_video_post(content_data)
            elif content_type == 'link':
                result = await self._upload_link_post(content_data)
            elif content_type == 'event':
                result = await self._create_event(content_data)
            elif content_type == 'live_video':
                result = await self._start_live_video(content_data)
            else:
                return {
                    'success': False,
                    'error': f'Upload method not implemented for: {content_type}'
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Facebook upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'facebook'
            }
    
    def _validate_credentials(self) -> bool:
        """Validate that required credentials are available"""
        if self.page_id and self.page_access_token:
            return True  # Page posting (preferred)
        elif self.access_token:
            return True  # User posting
        else:
            return False
    
    def _get_posting_endpoint(self) -> Tuple[str, str]:
        """Get the appropriate endpoint and access token for posting"""
        if self.page_id and self.page_access_token:
            # Post as page
            endpoint = f"{self.base_url}/{self.page_id}/feed"
            access_token = self.page_access_token
        else:
            # Post as user
            endpoint = f"{self.base_url}/me/feed"
            access_token = self.access_token
        
        return endpoint, access_token
    
    async def _upload_text_post(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload text-only post to Facebook"""
        try:
            endpoint, access_token = self._get_posting_endpoint()
            
            # Prepare post data
            post_data = {
                'access_token': access_token,
                'message': self._prepare_message(content_data)
            }
            
            # Add scheduling if specified
            if content_data.get('scheduled_publish_time'):
                post_data['scheduled_publish_time'] = content_data['scheduled_publish_time']
                post_data['published'] = False
            
            # Add targeting if specified
            if content_data.get('targeting'):
                post_data['targeting'] = json.dumps(content_data['targeting'])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, data=post_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'platform_id': result.get('id'),
                            'platform_url': self._get_post_url(result.get('id')),
                            'content_type': 'text',
                            'uploaded_at': datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Text post upload failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Upload failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error uploading text post: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_image_post(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload image post to Facebook"""
        try:
            file_path = content_data.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                return {'success': False, 'error': 'Image file not found'}
            
            # Validate file
            validation_result = await self._validate_file(file_path, 'image')
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            endpoint, access_token = self._get_posting_endpoint()
            
            # For images, we use the photos endpoint
            if self.page_id and self.page_access_token:
                photo_endpoint = f"{self.base_url}/{self.page_id}/photos"
            else:
                photo_endpoint = f"{self.base_url}/me/photos"
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('access_token', access_token)
            data.add_field('message', self._prepare_message(content_data))
            
            # Add image file
            with open(file_path, 'rb') as f:
                filename = Path(file_path).name
                data.add_field('source', f, filename=filename, content_type='image/*')
            
            # Add scheduling if specified
            if content_data.get('scheduled_publish_time'):
                data.add_field('scheduled_publish_time', str(content_data['scheduled_publish_time']))
                data.add_field('published', 'false')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(photo_endpoint, data=data, timeout=300) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'platform_id': result.get('id') or result.get('post_id'),
                            'platform_url': self._get_post_url(result.get('id') or result.get('post_id')),
                            'content_type': 'image',
                            'uploaded_at': datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Image post upload failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Upload failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error uploading image post: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_video_post(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload video post to Facebook"""
        try:
            file_path = content_data.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                return {'success': False, 'error': 'Video file not found'}
            
            # Validate file
            validation_result = await self._validate_file(file_path, 'video')
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Check if file is large enough to require resumable upload
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            
            if file_size_mb > 1024:  # Files larger than 1GB use resumable upload
                return await self._upload_large_video(file_path, content_data)
            else:
                return await self._upload_small_video(file_path, content_data)
                
        except Exception as e:
            logger.error(f"Error uploading video post: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_small_video(self, file_path: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload small video file (< 1GB) directly"""
        try:
            endpoint, access_token = self._get_posting_endpoint()
            
            # For videos, we use the videos endpoint
            if self.page_id and self.page_access_token:
                video_endpoint = f"{self.base_url}/{self.page_id}/videos"
            else:
                video_endpoint = f"{self.base_url}/me/videos"
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('access_token', access_token)
            data.add_field('description', self._prepare_message(content_data))
            
            # Add video file
            with open(file_path, 'rb') as f:
                filename = Path(file_path).name
                data.add_field('source', f, filename=filename, content_type='video/*')
            
            # Add scheduling if specified
            if content_data.get('scheduled_publish_time'):
                data.add_field('scheduled_publish_time', str(content_data['scheduled_publish_time']))
                data.add_field('published', 'false')
            
            # Add video-specific options
            if content_data.get('title'):
                data.add_field('title', content_data['title'])
            
            if content_data.get('privacy'):
                data.add_field('privacy', json.dumps(content_data['privacy']))
            
            async with aiohttp.ClientSession() as session:
                async with session.post(video_endpoint, data=data, timeout=1800) as response:  # 30 min timeout
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'platform_id': result.get('id'),
                            'platform_url': self._get_video_url(result.get('id')),
                            'content_type': 'video',
                            'uploaded_at': datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Video upload failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Upload failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error uploading small video: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_large_video(self, file_path: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload large video file using resumable upload"""
        try:
            endpoint, access_token = self._get_posting_endpoint()
            
            # Step 1: Initialize resumable upload session
            file_size = Path(file_path).stat().st_size
            
            if self.page_id and self.page_access_token:
                init_endpoint = f"{self.base_url}/{self.page_id}/videos"
            else:
                init_endpoint = f"{self.base_url}/me/videos"
            
            init_data = {
                'access_token': access_token,
                'upload_phase': 'start',
                'file_size': file_size
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(init_endpoint, data=init_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f'Failed to initialize upload: {error_text}'
                        }
                    
                    init_result = await response.json()
                    upload_session_id = init_result.get('upload_session_id')
                    
                    if not upload_session_id:
                        return {
                            'success': False,
                            'error': 'No upload session ID returned'
                        }
            
            # Step 2: Upload video in chunks
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            
            with open(file_path, 'rb') as f:
                offset = 0
                
                while offset < file_size:
                    chunk_data = f.read(chunk_size)
                    
                    if not chunk_data:
                        break
                    
                    # Upload chunk
                    chunk_form_data = aiohttp.FormData()
                    chunk_form_data.add_field('access_token', access_token)
                    chunk_form_data.add_field('upload_phase', 'transfer')
                    chunk_form_data.add_field('upload_session_id', upload_session_id)
                    chunk_form_data.add_field('start_offset', str(offset))
                    chunk_form_data.add_field('video_file_chunk', chunk_data, content_type='application/octet-stream')
                    
                    async with session.post(init_endpoint, data=chunk_form_data, timeout=300) as chunk_response:
                        if chunk_response.status != 200:
                            error_text = await chunk_response.text()
                            logger.error(f"Chunk upload failed: {chunk_response.status} - {error_text}")
                            return {
                                'success': False,
                                'error': f'Chunk upload failed: {error_text}'
                            }
                    
                    offset += len(chunk_data)
                    logger.info(f"Uploaded {offset}/{file_size} bytes ({offset/file_size*100:.1f}%)")
            
            # Step 3: Finalize upload
            finish_data = {
                'access_token': access_token,
                'upload_phase': 'finish',
                'upload_session_id': upload_session_id,
                'description': self._prepare_message(content_data)
            }
            
            if content_data.get('title'):
                finish_data['title'] = content_data['title']
            
            if content_data.get('scheduled_publish_time'):
                finish_data['scheduled_publish_time'] = content_data['scheduled_publish_time']
                finish_data['published'] = False
            
            async with session.post(init_endpoint, data=finish_data) as finish_response:
                if finish_response.status == 200:
                    result = await finish_response.json()
                    return {
                        'success': True,
                        'platform_id': result.get('id'),
                        'platform_url': self._get_video_url(result.get('id')),
                        'content_type': 'video',
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'upload_method': 'resumable'
                    }
                else:
                    error_text = await finish_response.text()
                    return {
                        'success': False,
                        'error': f'Failed to finalize upload: {error_text}'
                    }
                    
        except Exception as e:
            logger.error(f"Error uploading large video: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_link_post(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload link post to Facebook"""
        try:
            link_url = content_data.get('link_url')
            
            if not link_url:
                return {'success': False, 'error': 'Link URL is required'}
            
            endpoint, access_token = self._get_posting_endpoint()
            
            post_data = {
                'access_token': access_token,
                'message': self._prepare_message(content_data),
                'link': link_url
            }
            
            # Add link-specific metadata
            if content_data.get('link_name'):
                post_data['name'] = content_data['link_name']
            
            if content_data.get('link_caption'):
                post_data['caption'] = content_data['link_caption']
            
            if content_data.get('link_description'):
                post_data['description'] = content_data['link_description']
            
            if content_data.get('link_picture'):
                post_data['picture'] = content_data['link_picture']
            
            # Add scheduling if specified
            if content_data.get('scheduled_publish_time'):
                post_data['scheduled_publish_time'] = content_data['scheduled_publish_time']
                post_data['published'] = False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, data=post_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'platform_id': result.get('id'),
                            'platform_url': self._get_post_url(result.get('id')),
                            'content_type': 'link',
                            'uploaded_at': datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Link post upload failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Upload failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error uploading link post: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _create_event(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Facebook event"""
        try:
            if not self.page_id or not self.page_access_token:
                return {
                    'success': False,
                    'error': 'Page access required for creating events'
                }
            
            event_endpoint = f"{self.base_url}/{self.page_id}/events"
            
            # Required event fields
            required_fields = ['name', 'start_time']
            for field in required_fields:
                if not content_data.get(field):
                    return {
                        'success': False,
                        'error': f'Required field missing: {field}'
                    }
            
            event_data = {
                'access_token': self.page_access_token,
                'name': content_data['name'],
                'start_time': content_data['start_time']
            }
            
            # Optional event fields
            optional_fields = [
                'end_time', 'description', 'location', 'privacy',
                'ticket_uri', 'category', 'cover'
            ]
            
            for field in optional_fields:
                if content_data.get(field):
                    event_data[field] = content_data[field]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(event_endpoint, data=event_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'platform_id': result.get('id'),
                            'platform_url': f"https://www.facebook.com/events/{result.get('id')}/",
                            'content_type': 'event',
                            'uploaded_at': datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Event creation failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Event creation failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _start_live_video(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start Facebook live video"""
        try:
            if not self.page_id or not self.page_access_token:
                return {
                    'success': False,
                    'error': 'Page access required for live video'
                }
            
            live_endpoint = f"{self.base_url}/{self.page_id}/live_videos"
            
            live_data = {
                'access_token': self.page_access_token,
                'status': 'LIVE_NOW'
            }
            
            # Optional live video fields
            if content_data.get('title'):
                live_data['title'] = content_data['title']
            
            if content_data.get('description'):
                live_data['description'] = content_data['description']
            
            if content_data.get('privacy'):
                live_data['privacy'] = json.dumps(content_data['privacy'])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(live_endpoint, data=live_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'platform_id': result.get('id'),
                            'platform_url': result.get('permalink_url'),
                            'stream_url': result.get('stream_url'),
                            'secure_stream_url': result.get('secure_stream_url'),
                            'content_type': 'live_video',
                            'uploaded_at': datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Live video start failed: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Live video start failed: {error_text}'
                        }
                        
        except Exception as e:
            logger.error(f"Error starting live video: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _validate_file(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """Validate file for Facebook upload"""
        try:
            if not os.path.exists(file_path):
                return {'valid': False, 'error': 'File does not exist'}
            
            file_path_obj = Path(file_path)
            file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
            file_extension = file_path_obj.suffix.lower()
            
            # Check file format
            if content_type == 'image':
                if file_extension not in self.supported_image_formats:
                    return {
                        'valid': False,
                        'error': f'Unsupported image format: {file_extension}'
                    }
                
                if file_size_mb > self.max_file_size_mb:
                    return {
                        'valid': False,
                        'error': f'Image size {file_size_mb:.1f}MB exceeds limit {self.max_file_size_mb}MB'
                    }
            
            elif content_type == 'video':
                if file_extension not in self.supported_video_formats:
                    return {
                        'valid': False,
                        'error': f'Unsupported video format: {file_extension}'
                    }
                
                if file_size_mb > self.max_video_size_mb:
                    return {
                        'valid': False,
                        'error': f'Video size {file_size_mb:.1f}MB exceeds limit {self.max_video_size_mb}MB'
                    }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _prepare_message(self, content_data: Dict[str, Any]) -> str:
        """Prepare message text for Facebook post"""
        message_parts = []
        
        if content_data.get('title'):
            message_parts.append(content_data['title'])
        
        if content_data.get('description'):
            message_parts.append(content_data['description'])
        
        # Add hashtags
        hashtags = content_data.get('hashtags', [])
        if hashtags:
            # Ensure hashtags start with #
            hashtags = [tag if tag.startswith('#') else f'#{tag}' for tag in hashtags]
            message_parts.append(' '.join(hashtags))
        
        # Combine message parts
        full_message = '\n\n'.join(message_parts)
        
        # Limit message length
        if len(full_message) > self.max_post_length:
            full_message = full_message[:self.max_post_length - 3] + '...'
        
        return full_message
    
    def _get_post_url(self, post_id: str) -> str:
        """Generate Facebook post URL"""
        if not post_id:
            return ""
        
        if self.page_id:
            return f"https://www.facebook.com/{self.page_id}/posts/{post_id}"
        else:
            return f"https://www.facebook.com/posts/{post_id}"
    
    def _get_video_url(self, video_id: str) -> str:
        """Generate Facebook video URL"""
        if not video_id:
            return ""
        
        return f"https://www.facebook.com/watch/?v={video_id}"
    
    async def _apply_rate_limit(self):
        """Apply Facebook API rate limiting"""
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
    
    async def get_post_insights(self, post_id: str) -> Dict[str, Any]:
        """Get insights/analytics for a Facebook post"""
        try:
            insights_endpoint = f"{self.base_url}/{post_id}/insights"
            
            access_token = self.page_access_token or self.access_token
            
            params = {
                'access_token': access_token,
                'metric': 'post_impressions,post_engaged_users,post_reactions_like_total,post_clicks'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(insights_endpoint, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get post insights: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error getting post insights: {e}")
            return {}
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete a Facebook post"""
        try:
            delete_endpoint = f"{self.base_url}/{post_id}"
            
            access_token = self.page_access_token or self.access_token
            
            params = {'access_token': access_token}
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(delete_endpoint, params=params) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error deleting post: {e}")
            return False
    
    async def schedule_post(self, content_data: Dict[str, Any], publish_time: datetime) -> Dict[str, Any]:
        """Schedule a post for future publication"""
        # Add scheduled time to content data
        content_data['scheduled_publish_time'] = int(publish_time.timestamp())
        
        # Upload as normal - Facebook will handle scheduling
        return await self.upload_content(content_data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get uploader status information"""
        return {
            'platform': 'facebook',
            'configured': self._validate_credentials(),
            'page_access': bool(self.page_id and self.page_access_token),
            'user_access': bool(self.access_token),
            'supported_content_types': self.supported_content_types,
            'supported_formats': {
                'images': self.supported_image_formats,
                'videos': self.supported_video_formats
            },
            'limits': {
                'max_file_size_mb': self.max_file_size_mb,
                'max_video_size_mb': self.max_video_size_mb,
                'max_post_length': self.max_post_length,
                'requests_per_hour': self.requests_per_hour
            },
            'features': {
                'text_posts': True,
                'image_posts': True,
                'video_posts': True,
                'link_posts': True,
                'events': bool(self.page_id),
                'live_video': bool(self.page_id),
                'scheduling': True,
                'large_video_upload': True,
                'insights': True
            }
        }