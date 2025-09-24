"""
YouTube Uploader
จัดการการอัปโหลดวิดีโอไปยัง YouTube ผ่าน YouTube Data API v3
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import mimetypes
import time

# Google API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logging.warning("Google API libraries not available. YouTube upload will be disabled.")

from ...models.upload_metadata import UploadMetadata, UploadResult
from ...models.platform_type import PlatformRegistry, PlatformType

logger = logging.getLogger(__name__)

class YouTubeUploader:
    """YouTube API uploader implementation"""
    
    # OAuth2 scopes required for upload
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]
    
    # Retriable HTTP status codes
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
    
    # Maximum number of retries
    MAX_RETRIES = 3
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.platform_config = config_manager.get_platform_config("youtube")
        self.credentials = config_manager.get_platform_credentials("youtube")
        
        # YouTube service instance
        self.youtube_service = None
        
        # Rate limiting
        self.last_upload_time = None
        self.upload_count_today = 0
        self.daily_quota_used = 0
        
        # Platform specs
        self.platform_specs = PlatformRegistry.get_platform_specs(PlatformType.YOUTUBE)
        
        logger.info("YouTube Uploader initialized")
    
    def is_configured(self) -> bool:
        """ตรวจสอบว่า YouTube uploader ได้รับการตั้งค่าแล้วหรือไม่"""
        
        if not GOOGLE_API_AVAILABLE:
            return False
        
        if not self.platform_config or not self.platform_config.enabled:
            return False
        
        required_credentials = ["client_id", "client_secret"]
        return all(self.credentials.get(key) for key in required_credentials)
    
    async def test_connection(self) -> bool:
        """ทดสอบการเชื่อมต่อกับ YouTube API"""
        
        if not self.is_configured():
            return False
        
        try:
            # Try to get the authenticated user's channel
            service = await self._get_youtube_service()
            
            if service:
                # Make a simple API call to test authentication
                channels_response = service.channels().list(
                    part="snippet,contentDetails",
                    mine=True
                ).execute()
                
                if channels_response.get("items"):
                    logger.info("YouTube API connection successful")
                    return True
                else:
                    logger.warning("YouTube API connection failed: No channels found")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"YouTube API connection test failed: {str(e)}")
            return False
    
    async def upload(self, video_path: str, metadata: UploadMetadata) -> UploadResult:
        """อัปโหลดวิดีโอไปยัง YouTube"""
        
        try:
            logger.info(f"Starting YouTube upload: {os.path.basename(video_path)}")
            
            # Validate file
            if not os.path.exists(video_path):
                return UploadResult(
                    success=False,
                    platform="youtube",
                    error="Video file not found"
                )
            
            # Check rate limits
            rate_limit_check = await self._check_rate_limits()
            if not rate_limit_check["allowed"]:
                return UploadResult(
                    success=False,
                    platform="youtube",
                    error=f"Rate limit exceeded: {rate_limit_check['reason']}"
                )
            
            # Get YouTube service
            service = await self._get_youtube_service()
            if not service:
                return UploadResult(
                    success=False,
                    platform="youtube",
                    error="Failed to initialize YouTube service"
                )
            
            # Prepare video metadata
            video_metadata = self._prepare_video_metadata(metadata)
            
            # Create media upload object
            media = MediaFileUpload(
                video_path,
                chunksize=1024*1024*4,  # 4MB chunks
                resumable=True
            )
            
            # Execute upload with retries
            upload_result = await self._execute_upload_with_retries(
                service, video_metadata, media, video_path
            )
            
            # Update rate limiting counters
            self._update_rate_limits()
            
            return upload_result
            
        except Exception as e:
            logger.error(f"Error uploading to YouTube: {str(e)}")
            return UploadResult(
                success=False,
                platform="youtube",
                error=str(e)
            )
    
    async def _get_youtube_service(self):
        """ได้รับ YouTube API service instance"""
        
        if self.youtube_service:
            return self.youtube_service
        
        try:
            # Get OAuth2 credentials
            creds = await self._get_valid_credentials()
            
            if not creds:
                logger.error("Failed to get valid YouTube credentials")
                return None
            
            # Build YouTube service
            self.youtube_service = build('youtube', 'v3', credentials=creds)
            return self.youtube_service
            
        except Exception as e:
            logger.error(f"Error building YouTube service: {str(e)}")
            return None
    
    async def _get_valid_credentials(self) -> Optional[Credentials]:
        """ได้รับ OAuth2 credentials ที่ใช้งานได้"""
        
        try:
            # Check if we have stored credentials
            stored_token = self.credentials.get("access_token")
            refresh_token = self.credentials.get("refresh_token")
            
            if stored_token:
                # Create credentials object
                creds = Credentials(
                    token=stored_token,
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.credentials.get("client_id"),
                    client_secret=self.credentials.get("client_secret"),
                    scopes=self.SCOPES
                )
                
                # Refresh if expired
                if not creds.valid:
                    if creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        
                        # Update stored credentials
                        self.config_manager.set_platform_credentials("youtube", {
                            "access_token": creds.token,
                            "refresh_token": creds.refresh_token,
                            "expires_at": creds.expiry.isoformat() if creds.expiry else None
                        })
                        
                        return creds
                    else:
                        logger.warning("YouTube credentials expired and cannot be refreshed")
                        return None
                else:
                    return creds
            
            # If no stored credentials, need to run OAuth flow
            logger.warning("No valid YouTube credentials found. OAuth flow required.")
            return None
            
        except Exception as e:
            logger.error(f"Error getting YouTube credentials: {str(e)}")
            return None
    
    def _prepare_video_metadata(self, metadata: UploadMetadata) -> Dict[str, Any]:
        """เตรียม metadata สำหรับ YouTube API"""
        
        # Adapt metadata for YouTube
        youtube_metadata = metadata.adapt_for_platform("youtube")
        
        # Build YouTube-specific metadata structure
        video_metadata = {
            "snippet": {
                "title": youtube_metadata.title,
                "description": youtube_metadata.description,
                "tags": youtube_metadata.tags,
                "categoryId": youtube_metadata.custom_fields.get("categoryId", "22"),
                "defaultLanguage": youtube_metadata.language,
                "defaultAudioLanguage": youtube_metadata.language
            },
            "status": {
                "privacyStatus": self._convert_privacy_status(youtube_metadata.privacy),
                "embeddable": youtube_metadata.custom_fields.get("embeddable", True),
                "license": "youtube",  # or "creativeCommon"
                "publicStatsViewable": youtube_metadata.custom_fields.get("publicStatsViewable", True),
                "madeForKids": youtube_metadata.custom_fields.get("madeForKids", False)
            }
        }
        
        # Add scheduled publish time if specified
        if youtube_metadata.scheduled_time and youtube_metadata.privacy == "scheduled":
            video_metadata["status"]["publishAt"] = youtube_metadata.scheduled_time.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )
        
        # Add location if specified
        if youtube_metadata.location:
            video_metadata["recordingDetails"] = {
                "location": {
                    "latitude": youtube_metadata.location.get("latitude"),
                    "longitude": youtube_metadata.location.get("longitude")
                }
            }
        
        return video_metadata
    
    def _convert_privacy_status(self, privacy: str) -> str:
        """แปลง privacy status ให้เหมาะกับ YouTube"""
        
        privacy_mapping = {
            "public": "public",
            "unlisted": "unlisted", 
            "private": "private",
            "scheduled": "private"  # Will be changed to public at scheduled time
        }
        
        return privacy_mapping.get(privacy, "private")
    
    async def _execute_upload_with_retries(
        self, 
        service, 
        video_metadata: Dict[str, Any],
        media: MediaFileUpload,
        video_path: str
    ) -> UploadResult:
        """ดำเนินการอัปโหลดพร้อม retry logic"""
        
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"Upload attempt {attempt + 1}/{self.MAX_RETRIES}")
                
                # Initialize upload request
                insert_request = service.videos().insert(
                    part=",".join(video_metadata.keys()),
                    body=video_metadata,
                    media_body=media
                )
                
                # Execute resumable upload
                response = await self._execute_resumable_upload(insert_request)
                
                if response:
                    # Upload successful
                    video_id = response["id"]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Upload thumbnail if specified
                    thumbnail_url = None
                    if hasattr(media, 'thumbnail_path') and media.thumbnail_path:
                        thumbnail_url = await self._upload_thumbnail(service, video_id, media.thumbnail_path)
                    
                    logger.info(f"YouTube upload successful: {video_url}")
                    
                    return UploadResult(
                        success=True,
                        platform="youtube",
                        platform_id=video_id,
                        url=video_url,
                        file_size=os.path.getsize(video_path),
                        metadata_used={
                            "title": video_metadata["snippet"]["title"],
                            "privacy": video_metadata["status"]["privacyStatus"],
                            "category": video_metadata["snippet"]["categoryId"],
                            "thumbnail_uploaded": thumbnail_url is not None
                        }
                    )
                
            except HttpError as e:
                if e.resp.status in self.RETRIABLE_STATUS_CODES:
                    logger.warning(f"Retriable error (attempt {attempt + 1}): {str(e)}")
                    if attempt < self.MAX_RETRIES - 1:
                        # Exponential backoff
                        wait_time = (2 ** attempt) * 60  # 1, 2, 4 minutes
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                else:
                    logger.error(f"Non-retriable YouTube API error: {str(e)}")
                    return UploadResult(
                        success=False,
                        platform="youtube",
                        error=f"YouTube API error: {str(e)}"
                    )
            
            except Exception as e:
                logger.error(f"Upload attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(30)  # Wait before retry
                    continue
                else:
                    return UploadResult(
                        success=False,
                        platform="youtube",
                        error=f"Upload failed after {self.MAX_RETRIES} attempts: {str(e)}"
                    )
        
        return UploadResult(
            success=False,
            platform="youtube",
            error=f"Upload failed after {self.MAX_RETRIES} attempts"
        )
    
    async def _execute_resumable_upload(self, insert_request) -> Optional[Dict[str, Any]]:
        """ดำเนินการอัปโหลดแบบ resumable"""
        
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                logger.info("Uploading file...")
                status, response = insert_request.next_chunk()
                
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
                
            except HttpError as e:
                if e.resp.status in self.RETRIABLE_STATUS_CODES:
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                else:
                    raise
            
            except Exception as e:
                error = f"An error occurred: {e}"
            
            if error is not None:
                logger.warning(error)
                retry += 1
                if retry > self.MAX_RETRIES:
                    raise Exception(f"Upload failed after {self.MAX_RETRIES} retries")
                
                max_sleep = 2 ** retry
                sleep_seconds = min(max_sleep, 64)  # Cap at 64 seconds
                logger.info(f"Sleeping {sleep_seconds} seconds and then retrying...")
                await asyncio.sleep(sleep_seconds)
        
        return response
    
    async def _upload_thumbnail(self, service, video_id: str, thumbnail_path: str) -> Optional[str]:
        """อัปโหลด thumbnail สำหรับวิดีโอ"""
        
        try:
            if not os.path.exists(thumbnail_path):
                logger.warning(f"Thumbnail file not found: {thumbnail_path}")
                return None
            
            logger.info(f"Uploading thumbnail for video {video_id}")
            
            # Create thumbnail upload request
            service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            
            logger.info("Thumbnail uploaded successfully")
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
        except Exception as e:
            logger.error(f"Error uploading thumbnail: {str(e)}")
            return None
    
    async def _check_rate_limits(self) -> Dict[str, Any]:
        """ตรวจสอบ rate limits"""
        
        try:
            # Get rate limit settings
            rate_limits = self.config_manager.get_rate_limits("youtube")
            
            daily_upload_limit = rate_limits.get("uploads_per_day", 6)
            daily_quota_limit = rate_limits.get("api_units_per_day", 10000)
            quota_per_upload = rate_limits.get("quota_cost_upload", 1600)
            
            # Check daily upload count
            if self.upload_count_today >= daily_upload_limit:
                return {
                    "allowed": False,
                    "reason": f"Daily upload limit reached ({daily_upload_limit} uploads)"
                }
            
            # Check daily quota
            if self.daily_quota_used + quota_per_upload > daily_quota_limit:
                return {
                    "allowed": False,
                    "reason": f"Daily API quota would be exceeded ({self.daily_quota_used + quota_per_upload}/{daily_quota_limit})"
                }
            
            # Check minimum time between uploads (prevent spam)
            if self.last_upload_time:
                time_since_last = (datetime.now() - self.last_upload_time).total_seconds()
                min_interval = 60  # 1 minute minimum between uploads
                
                if time_since_last < min_interval:
                    return {
                        "allowed": False,
                        "reason": f"Must wait {min_interval - time_since_last:.0f} seconds between uploads"
                    }
            
            return {"allowed": True, "reason": "Rate limits OK"}
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {str(e)}")
            return {"allowed": True, "reason": "Rate limit check failed, allowing upload"}
    
    def _update_rate_limits(self) -> None:
        """อัปเดตตัวนับ rate limits"""
        
        self.last_upload_time = datetime.now()
        self.upload_count_today += 1
        
        # Add quota cost for upload
        quota_per_upload = self.config_manager.get_rate_limits("youtube").get("quota_cost_upload", 1600)
        self.daily_quota_used += quota_per_upload
        
        logger.info(f"Rate limits updated: {self.upload_count_today} uploads today, {self.daily_quota_used} quota used")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """ได้รับสถานะ rate limits ปัจจุบัน"""
        
        rate_limits = self.config_manager.get_rate_limits("youtube")
        
        return {
            "uploads_today": self.upload_count_today,
            "uploads_remaining": max(0, rate_limits.get("uploads_per_day", 6) - self.upload_count_today),
            "quota_used_today": self.daily_quota_used,
            "quota_remaining": max(0, rate_limits.get("api_units_per_day", 10000) - self.daily_quota_used),
            "last_upload": self.last_upload_time.isoformat() if self.last_upload_time else None,
            "next_upload_allowed": (
                self.last_upload_time + timedelta(minutes=1)
            ).isoformat() if self.last_upload_time else datetime.now().isoformat()
        }
    
    def reset_daily_counters(self) -> None:
        """รีเซ็ตตัวนับรายวัน (เรียกใช้เมื่อเปลี่ยนวัน)"""
        
        logger.info("Resetting YouTube daily counters")
        self.upload_count_today = 0
        self.daily_quota_used = 0
    
    async def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """ได้รับข้อมูล YouTube channel"""
        
        try:
            service = await self._get_youtube_service()
            if not service:
                return None
            
            channels_response = service.channels().list(
                part="snippet,statistics,contentDetails",
                mine=True
            ).execute()
            
            if channels_response.get("items"):
                channel = channels_response["items"][0]
                return {
                    "id": channel["id"],
                    "title": channel["snippet"]["title"],
                    "description": channel["snippet"]["description"],
                    "subscriber_count": channel["statistics"].get("subscriberCount", 0),
                    "video_count": channel["statistics"].get("videoCount", 0),
                    "view_count": channel["statistics"].get("viewCount", 0),
                    "uploads_playlist_id": channel["contentDetails"]["relatedPlaylists"]["uploads"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting channel info: {str(e)}")
            return None
    
    async def get_video_performance(self, video_id: str) -> Optional[Dict[str, Any]]:
        """ได้รับข้อมูลประสิทธิภาพของวิดีโอ"""
        
        try:
            service = await self._get_youtube_service()
            if not service:
                return None
            
            videos_response = service.videos().list(
                part="statistics,snippet",
                id=video_id
            ).execute()
            
            if videos_response.get("items"):
                video = videos_response["items"][0]
                return {
                    "video_id": video_id,
                    "title": video["snippet"]["title"],
                    "published_at": video["snippet"]["publishedAt"],
                    "view_count": int(video["statistics"].get("viewCount", 0)),
                    "like_count": int(video["statistics"].get("likeCount", 0)),
                    "comment_count": int(video["statistics"].get("commentCount", 0)),
                    "duration": video["contentDetails"].get("duration", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting video performance: {str(e)}")
            return None

# Utility functions for OAuth flow (for initial setup)
def start_oauth_flow(client_id: str, client_secret: str, redirect_uri: str = None) -> str:
    """เริ่ม OAuth flow สำหรับ YouTube (ใช้ในการ setup ครั้งแรก)"""
    
    if not GOOGLE_API_AVAILABLE:
        raise Exception("Google API libraries not available")
    
    # Create OAuth2 flow
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri or "http://localhost:8080/oauth/callback"]
            }
        },
        YouTubeUploader.SCOPES
    )
    
    # Get authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    return auth_url

def complete_oauth_flow(
    client_id: str, 
    client_secret: str, 
    authorization_code: str,
    redirect_uri: str = None
) -> Dict[str, Any]:
    """เสร็จสิ้น OAuth flow และได้รับ tokens"""
    
    if not GOOGLE_API_AVAILABLE:
        raise Exception("Google API libraries not available")
    
    # Create OAuth2 flow
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri or "http://localhost:8080/oauth/callback"]
            }
        },
        YouTubeUploader.SCOPES
    )
    
    # Exchange authorization code for tokens
    flow.fetch_token(code=authorization_code)
    
    credentials = flow.credentials
    
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
        "client_id": client_id,
        "client_secret": client_secret
    }