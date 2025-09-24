"""
TikTok Uploader
จัดการการอัปโหลดวิดีโอไปยัง TikTok ผ่าน TikTok API for Developers
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import aiohttp
import base64
import hashlib
import hmac
from urllib.parse import urlencode, quote
import time

from ...models.upload_metadata import UploadMetadata, UploadResult
from ...models.platform_type import PlatformRegistry, PlatformType

logger = logging.getLogger(__name__)

class TikTokUploader:
    """TikTok API uploader implementation"""
    
    # TikTok API endpoints
    BASE_URL = "https://open-api.tiktok.com"
    UPLOAD_URL = f"{BASE_URL}/share/video/upload/"
    PUBLISH_URL = f"{BASE_URL}/video/publish/"
    OAUTH_URL = "https://www.tiktok.com/auth/authorize/"
    TOKEN_URL = f"{BASE_URL}/oauth/access_token/"
    
    # API scopes required
    REQUIRED_SCOPES = ["video.upload", "user.info.basic"]
    
    # Maximum retries for upload
    MAX_RETRIES = 3
    
    # Supported video formats
    SUPPORTED_FORMATS = ["mp4", "mov", "webm"]
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.platform_config = config_manager.get_platform_config("tiktok")
        self.credentials = config_manager.get_platform_credentials("tiktok")
        
        # Rate limiting
        self.last_upload_time = None
        self.upload_count_today = 0
        self.api_calls_today = 0
        
        # Platform specs
        self.platform_specs = PlatformRegistry.get_platform_specs(PlatformType.TIKTOK)
        
        # HTTP session for API calls
        self.session = None
        
        logger.info("TikTok Uploader initialized")
    
    def is_configured(self) -> bool:
        """ตรวจสอบว่า TikTok uploader ได้รับการตั้งค่าแล้วหรือไม่"""
        
        if not self.platform_config or not self.platform_config.enabled:
            return False
        
        required_credentials = ["client_key", "client_secret", "access_token"]
        return all(self.credentials.get(key) for key in required_credentials)
    
    async def test_connection(self) -> bool:
        """ทดสอบการเชื่อมต่อกับ TikTok API"""
        
        if not self.is_configured():
            return False
        
        try:
            # Test API connection by getting user info
            session = await self._get_http_session()
            
            headers = await self._get_auth_headers()
            
            async with session.get(
                f"{self.BASE_URL}/user/info/",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("data") and data["data"].get("user"):
                        logger.info("TikTok API connection successful")
                        return True
                    else:
                        logger.warning("TikTok API connection failed: Invalid response")
                        return False
                else:
                    logger.warning(f"TikTok API connection failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"TikTok API connection test failed: {str(e)}")
            return False
    
    async def upload(self, video_path: str, metadata: UploadMetadata) -> UploadResult:
        """อัปโหลดวิดีโอไปยัง TikTok"""
        
        try:
            logger.info(f"Starting TikTok upload: {os.path.basename(video_path)}")
            
            # Validate file
            if not os.path.exists(video_path):
                return UploadResult(
                    success=False,
                    platform="tiktok",
                    error="Video file not found"
                )
            
            # Validate file format and specs
            validation_result = self._validate_video_file(video_path)
            if not validation_result["valid"]:
                return UploadResult(
                    success=False,
                    platform="tiktok",
                    error=f"File validation failed: {validation_result['error']}"
                )
            
            # Check rate limits
            rate_limit_check = await self._check_rate_limits()
            if not rate_limit_check["allowed"]:
                return UploadResult(
                    success=False,
                    platform="tiktok",
                    error=f"Rate limit exceeded: {rate_limit_check['reason']}"
                )
            
            # Prepare TikTok metadata
            tiktok_metadata = self._prepare_tiktok_metadata(metadata)
            
            # Upload video in chunks
            upload_result = await self._upload_video_chunked(video_path, tiktok_metadata)
            
            if upload_result["success"]:
                # Publish video
                publish_result = await self._publish_video(upload_result["upload_id"], tiktok_metadata)
                
                if publish_result["success"]:
                    # Update rate limiting counters
                    self._update_rate_limits()
                    
                    logger.info(f"TikTok upload successful: {publish_result['video_url']}")
                    
                    return UploadResult(
                        success=True,
                        platform="tiktok",
                        platform_id=publish_result["video_id"],
                        url=publish_result["video_url"],
                        file_size=os.path.getsize(video_path),
                        metadata_used={
                            "description": tiktok_metadata["description"],
                            "privacy": tiktok_metadata["privacy_level"],
                            "allows_comment": tiktok_metadata["allows_comment"],
                            "allows_duet": tiktok_metadata["allows_duet"],
                            "allows_stitch": tiktok_metadata["allows_stitch"]
                        }
                    )
                else:
                    return UploadResult(
                        success=False,
                        platform="tiktok",
                        error=f"Failed to publish video: {publish_result['error']}"
                    )
            else:
                return UploadResult(
                    success=False,
                    platform="tiktok",
                    error=f"Failed to upload video: {upload_result['error']}"
                )
                
        except Exception as e:
            logger.error(f"Error uploading to TikTok: {str(e)}")
            return UploadResult(
                success=False,
                platform="tiktok",
                error=str(e)
            )
    
    async def _get_http_session(self) -> aiohttp.ClientSession:
        """ได้รับ HTTP session สำหรับ API calls"""
        
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        
        return self.session
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """ได้รับ headers สำหรับ authentication"""
        
        access_token = self.credentials.get("access_token")
        
        if not access_token:
            raise Exception("No access token available")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def _validate_video_file(self, video_path: str) -> Dict[str, Any]:
        """ตรวจสอบความถูกต้องของไฟล์วิดีโอ"""
        
        try:
            # Check file exists
            if not os.path.exists(video_path):
                return {"valid": False, "error": "File not found"}
            
            # Check file size
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            max_size_mb = self.platform_specs.max_file_size_mb
            
            if file_size_mb > max_size_mb:
                return {
                    "valid": False, 
                    "error": f"File too large: {file_size_mb:.1f}MB > {max_size_mb}MB"
                }
            
            # Check file format
            file_extension = os.path.splitext(video_path)[1][1:].lower()
            if file_extension not in self.SUPPORTED_FORMATS:
                return {
                    "valid": False,
                    "error": f"Unsupported format: {file_extension}. Supported: {self.SUPPORTED_FORMATS}"
                }
            
            # Additional validations can be added here (duration, resolution, etc.)
            
            return {"valid": True, "error": None}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def _prepare_tiktok_metadata(self, metadata: UploadMetadata) -> Dict[str, Any]:
        """เตรียม metadata สำหรับ TikTok"""
        
        # Adapt metadata for TikTok
        tiktok_metadata = metadata.adapt_for_platform("tiktok")
        
        # Build TikTok-specific metadata
        prepared_metadata = {
            "description": tiktok_metadata.description,
            "privacy_level": self._convert_privacy_level(tiktok_metadata.privacy),
            "allows_comment": tiktok_metadata.custom_fields.get("allows_comment", True),
            "allows_duet": tiktok_metadata.custom_fields.get("allows_duet", True),
            "allows_stitch": tiktok_metadata.custom_fields.get("allows_stitch", True),
            "auto_add_music": tiktok_metadata.custom_fields.get("auto_add_music", False),
        }
        
        # Add scheduled publish time if specified
        if tiktok_metadata.scheduled_time and tiktok_metadata.privacy == "scheduled":
            prepared_metadata["publish_time"] = int(tiktok_metadata.scheduled_time.timestamp())
        
        return prepared_metadata
    
    def _convert_privacy_level(self, privacy: str) -> str:
        """แปลง privacy level ให้เหมาะกับ TikTok"""
        
        privacy_mapping = {
            "public": "public",
            "private": "self_only",
            "unlisted": "friends_only",  # TikTok doesn't have unlisted, use friends
            "scheduled": "public"  # Will be scheduled
        }
        
        return privacy_mapping.get(privacy, "public")
    
    async def _upload_video_chunked(self, video_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """อัปโหลดวิดีโอแบบแบ่งเป็น chunks"""
        
        try:
            session = await self._get_http_session()
            
            # Step 1: Initialize upload
            init_result = await self._initialize_upload(video_path, metadata)
            if not init_result["success"]:
                return init_result
            
            upload_id = init_result["upload_id"]
            upload_url = init_result["upload_url"]
            
            # Step 2: Upload video file
            upload_result = await self._upload_video_file(video_path, upload_url)
            if not upload_result["success"]:
                return upload_result
            
            # Step 3: Complete upload
            complete_result = await self._complete_upload(upload_id)
            if not complete_result["success"]:
                return complete_result
            
            return {
                "success": True,
                "upload_id": upload_id,
                "message": "Video uploaded successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in chunked upload: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _initialize_upload(self, video_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """เริ่มต้นการอัปโหลด"""
        
        try:
            session = await self._get_http_session()
            headers = await self._get_auth_headers()
            
            # Prepare upload initialization payload
            file_size = os.path.getsize(video_path)
            
            payload = {
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": min(1024*1024*10, file_size),  # 10MB chunks or file size
                    "total_chunk_count": max(1, (file_size + 1024*1024*10 - 1) // (1024*1024*10))
                }
            }
            
            async with session.post(
                f"{self.BASE_URL}/share/video/upload/",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("error", {}).get("code") == "ok":
                        upload_data = data.get("data", {})
                        return {
                            "success": True,
                            "upload_id": upload_data.get("upload_id"),
                            "upload_url": upload_data.get("upload_url")
                        }
                    else:
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        return {"success": False, "error": f"API error: {error_msg}"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Initialize upload failed: {str(e)}"}
    
    async def _upload_video_file(self, video_path: str, upload_url: str) -> Dict[str, Any]:
        """อัปโหลดไฟล์วิดีโอจริง"""
        
        try:
            session = await self._get_http_session()
            
            # Upload file using multipart form data
            with open(video_path, 'rb') as video_file:
                data = aiohttp.FormData()
                data.add_field('video',
                             video_file,
                             filename=os.path.basename(video_path),
                             content_type='video/mp4')
                
                async with session.post(upload_url, data=data) as response:
                    
                    if response.status == 200:
                        return {"success": True, "message": "File uploaded successfully"}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"Upload failed: HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            return {"success": False, "error": f"File upload failed: {str(e)}"}
    
    async def _complete_upload(self, upload_id: str) -> Dict[str, Any]:
        """เสร็จสิ้นการอัปโหลด"""
        
        try:
            session = await self._get_http_session()
            headers = await self._get_auth_headers()
            
            payload = {
                "upload_id": upload_id
            }
            
            async with session.post(
                f"{self.BASE_URL}/share/video/upload/complete/",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("error", {}).get("code") == "ok":
                        return {"success": True, "message": "Upload completed"}
                    else:
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        return {"success": False, "error": f"Complete upload failed: {error_msg}"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Complete upload failed: {str(e)}"}
    
    async def _publish_video(self, upload_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """เผยแพร่วิดีโอ"""
        
        try:
            session = await self._get_http_session()
            headers = await self._get_auth_headers()
            
            # Prepare publish payload
            payload = {
                "post_info": {
                    "title": metadata["description"][:100],  # TikTok uses description as title
                    "description": metadata["description"],
                    "privacy_level": metadata["privacy_level"],
                    "allows_comment": metadata["allows_comment"],
                    "allows_duet": metadata["allows_duet"],
                    "allows_stitch": metadata["allows_stitch"],
                    "auto_add_music": metadata["auto_add_music"]
                },
                "source_info": {
                    "upload_id": upload_id
                }
            }
            
            # Add scheduled publish time if specified
            if "publish_time" in metadata:
                payload["post_info"]["publish_time"] = metadata["publish_time"]
            
            async with session.post(
                f"{self.BASE_URL}/video/publish/",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("error", {}).get("code") == "ok":
                        publish_data = data.get("data", {})
                        video_id = publish_data.get("video_id")
                        
                        # TikTok doesn't always provide direct video URL immediately
                        video_url = f"https://www.tiktok.com/@username/video/{video_id}" if video_id else None
                        
                        return {
                            "success": True,
                            "video_id": video_id,
                            "video_url": video_url,
                            "message": "Video published successfully"
                        }
                    else:
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        return {"success": False, "error": f"Publish failed: {error_msg}"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Publish failed: {str(e)}"}
    
    async def _check_rate_limits(self) -> Dict[str, Any]:
        """ตรวจสอบ rate limits"""
        
        try:
            rate_limits = self.config_manager.get_rate_limits("tiktok")
            
            daily_upload_limit = rate_limits.get("uploads_per_day", 50)
            daily_api_limit = rate_limits.get("api_calls_per_day", 1000)
            
            # Check daily upload count
            if self.upload_count_today >= daily_upload_limit:
                return {
                    "allowed": False,
                    "reason": f"Daily upload limit reached ({daily_upload_limit} uploads)"
                }
            
            # Check daily API calls
            if self.api_calls_today >= daily_api_limit:
                return {
                    "allowed": False,
                    "reason": f"Daily API limit reached ({daily_api_limit} calls)"
                }
            
            # Check minimum time between uploads
            if self.last_upload_time:
                time_since_last = (datetime.now() - self.last_upload_time).total_seconds()
                min_interval = 30  # 30 seconds minimum between uploads
                
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
        self.api_calls_today += 3  # Upload typically uses 3 API calls
        
        logger.info(f"Rate limits updated: {self.upload_count_today} uploads, {self.api_calls_today} API calls today")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """ได้รับสถานะ rate limits ปัจจุบัน"""
        
        rate_limits = self.config_manager.get_rate_limits("tiktok")
        
        return {
            "uploads_today": self.upload_count_today,
            "uploads_remaining": max(0, rate_limits.get("uploads_per_day", 50) - self.upload_count_today),
            "api_calls_today": self.api_calls_today,
            "api_calls_remaining": max(0, rate_limits.get("api_calls_per_day", 1000) - self.api_calls_today),
            "last_upload": self.last_upload_time.isoformat() if self.last_upload_time else None,
            "next_upload_allowed": (
                self.last_upload_time + timedelta(seconds=30)
            ).isoformat() if self.last_upload_time else datetime.now().isoformat()
        }
    
    def reset_daily_counters(self) -> None:
        """รีเซ็ตตัวนับรายวัน"""
        
        logger.info("Resetting TikTok daily counters")
        self.upload_count_today = 0
        self.api_calls_today = 0
    
    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """ได้รับข้อมูลผู้ใช้ TikTok"""
        
        try:
            session = await self._get_http_session()
            headers = await self._get_auth_headers()
            
            async with session.get(
                f"{self.BASE_URL}/user/info/",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("error", {}).get("code") == "ok":
                        user_data = data.get("data", {}).get("user", {})
                        return {
                            "user_id": user_data.get("open_id"),
                            "username": user_data.get("username"),
                            "display_name": user_data.get("display_name"),
                            "avatar_url": user_data.get("avatar_url"),
                            "follower_count": user_data.get("follower_count", 0),
                            "following_count": user_data.get("following_count", 0),
                            "likes_count": user_data.get("likes_count", 0)
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """ได้รับข้อมูลวิดีโอ"""
        
        try:
            session = await self._get_http_session()
            headers = await self._get_auth_headers()
            
            params = {
                "video_id": video_id
            }
            
            async with session.get(
                f"{self.BASE_URL}/video/query/",
                headers=headers,
                params=params
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("error", {}).get("code") == "ok":
                        video_data = data.get("data", {}).get("video", {})
                        return {
                            "video_id": video_id,
                            "title": video_data.get("title"),
                            "description": video_data.get("description"),
                            "view_count": video_data.get("view_count", 0),
                            "like_count": video_data.get("like_count", 0),
                            "comment_count": video_data.get("comment_count", 0),
                            "share_count": video_data.get("share_count", 0),
                            "create_time": video_data.get("create_time"),
                            "video_url": video_data.get("share_url")
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return None
    
    async def close(self) -> None:
        """ปิด HTTP session"""
        
        if self.session and not self.session.closed:
            await self.session.close()

# Utility functions for OAuth setup
def get_oauth_url(client_key: str, redirect_uri: str, state: str = None) -> str:
    """สร้าง OAuth authorization URL สำหรับ TikTok"""
    
    params = {
        "client_key": client_key,
        "scope": ",".join(TikTokUploader.REQUIRED_SCOPES),
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state or "tiktok_oauth_state"
    }
    
    return f"{TikTokUploader.OAUTH_URL}?{urlencode(params)}"

async def exchange_code_for_token(
    client_key: str,
    client_secret: str, 
    authorization_code: str,
    redirect_uri: str
) -> Dict[str, Any]:
    """แลกเปลี่ยน authorization code เป็น access token"""
    
    try:
        payload = {
            "client_key": client_key,
            "client_secret": client_secret,
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TikTokUploader.TOKEN_URL,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("error", {}).get("code") == "ok":
                        token_data = data.get("data", {})
                        return {
                            "success": True,
                            "access_token": token_data.get("access_token"),
                            "refresh_token": token_data.get("refresh_token"),
                            "expires_in": token_data.get("expires_in"),
                            "scope": token_data.get("scope"),
                            "open_id": token_data.get("open_id")
                        }
                    else:
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        return {"success": False, "error": error_msg}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
    except Exception as e:
        return {"success": False, "error": f"Token exchange failed: {str(e)}"}

def validate_tiktok_webhook(payload: str, signature: str, client_secret: str) -> bool:
    """ตรวจสอบ webhook signature จาก TikTok"""
    
    try:
        # TikTok uses HMAC-SHA256 for webhook verification
        expected_signature = hmac.new(
            client_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Error validating webhook: {str(e)}")
        return False