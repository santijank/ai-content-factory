"""
Unit Tests for Platform Manager
==============================

Tests for the platform management system including:
- PlatformManager main class
- Individual platform uploaders (YouTube, TikTok, Instagram, Facebook)
- Content optimization for different platforms
- Upload status tracking
- Error handling and retries
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio
import json
from datetime import datetime
import tempfile
import os

# Import modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from platform_manager.services.platform_manager import PlatformManager
from platform_manager.services.uploaders.youtube_uploader import YouTubeUploader
from platform_manager.services.uploaders.tiktok_uploader import TikTokUploader
from platform_manager.models.platform_type import PlatformType
from platform_manager.models.upload_metadata import UploadMetadata


class TestPlatformManager:
    """Test cases for PlatformManager main class."""
    
    @pytest.fixture
    def mock_uploaders(self):
        """Create mock uploaders for all platforms."""
        uploaders = {}
        
        for platform in [PlatformType.YOUTUBE, PlatformType.TIKTOK, 
                        PlatformType.INSTAGRAM, PlatformType.FACEBOOK]:
            uploader = Mock()
            uploader.upload = AsyncMock(return_value={
                "status": "success",
                "platform_id": f"mock_{platform.value}_id",
                "url": f"https://{platform.value}.com/mock_video"
            })
            uploaders[platform] = uploader
        
        return uploaders
    
    @pytest.fixture
    def platform_manager(self, mock_uploaders):
        """Create PlatformManager instance with mocked uploaders."""
        with patch.dict('platform_manager.services.platform_manager.PlatformManager.platforms', mock_uploaders):
            return PlatformManager()
    
    @pytest.fixture
    def sample_content(self):
        """Create sample content for upload testing."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'mock video content')
            return f.name
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample upload metadata."""
        return UploadMetadata(
            title="Test Video Title",
            description="This is a test video for AI content factory",
            tags=["AI", "content", "automation", "test"],
            category="Education",
            privacy="public",
            thumbnail_url="https://example.com/thumbnail.jpg"
        )
    
    @pytest.mark.asyncio
    async def test_upload_content_single_platform(self, platform_manager, sample_content, sample_metadata):
        """Test uploading content to a single platform."""
        platforms = [PlatformType.YOUTUBE]
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_optimize, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_optimize.return_value = sample_content
            mock_adapt.return_value = sample_metadata
            
            results = await platform_manager.upload_content(sample_content, platforms, sample_metadata)
            
            # Assertions
            assert len(results) == 1
            assert results[0]["status"] == "success"
            assert "youtube" in results[0]["platform_id"]
            
            # Verify optimization and adaptation were called
            mock_optimize.assert_called_once_with(sample_content, PlatformType.YOUTUBE)
            mock_adapt.assert_called_once_with(sample_metadata, PlatformType.YOUTUBE)
    
    @pytest.mark.asyncio
    async def test_upload_content_multiple_platforms(self, platform_manager, sample_content, sample_metadata):
        """Test uploading content to multiple platforms simultaneously."""
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_optimize, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_optimize.return_value = sample_content
            mock_adapt.return_value = sample_metadata
            
            results = await platform_manager.upload_content(sample_content, platforms, sample_metadata)
            
            # Should have results for all platforms
            assert len(results) == 3
            assert all(result["status"] == "success" for result in results)
            
            # Should have called optimization for each platform
            assert mock_optimize.call_count == 3
            assert mock_adapt.call_count == 3
    
    @pytest.mark.asyncio
    async def test_upload_with_failure(self, platform_manager, sample_content, sample_metadata):
        """Test handling of upload failures on some platforms."""
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK]
        
        # Mock YouTube to succeed, TikTok to fail
        platform_manager.platforms[PlatformType.YOUTUBE].upload = AsyncMock(return_value={
            "status": "success",
            "platform_id": "youtube_success"
        })
        
        platform_manager.platforms[PlatformType.TIKTOK].upload = AsyncMock(
            side_effect=Exception("Upload failed")
        )
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_optimize, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_optimize.return_value = sample_content
            mock_adapt.return_value = sample_metadata
            
            results = await platform_manager.upload_content(sample_content, platforms, sample_metadata)
            
            # Should have results for both platforms (success and error)
            assert len(results) == 2
            
            # Find success and error results
            success_result = next(r for r in results if r.get("status") == "success")
            error_result = next(r for r in results if r.get("status") == "error")
            
            assert success_result["platform_id"] == "youtube_success"
            assert "Upload failed" in error_result.get("error", "")
    
    @pytest.mark.asyncio
    async def test_optimize_for_platform(self, platform_manager, sample_content):
        """Test platform-specific content optimization."""
        # Test YouTube optimization
        with patch('moviepy.editor.VideoFileClip') as mock_video:
            mock_clip = Mock()
            mock_clip.resize.return_value = mock_clip
            mock_clip.write_videofile.return_value = None
            mock_video.return_value = mock_clip
            
            optimized = await platform_manager.optimize_for_platform(sample_content, PlatformType.YOUTUBE)
            
            assert optimized.endswith('_youtube.mp4')
            mock_clip.resize.assert_called()
    
    @pytest.mark.asyncio
    async def test_adapt_metadata(self, platform_manager, sample_metadata):
        """Test platform-specific metadata adaptation."""
        # Test YouTube metadata adaptation
        adapted = await platform_manager.adapt_metadata(sample_metadata, PlatformType.YOUTUBE)
        
        assert adapted.title == sample_metadata.title
        assert adapted.description == sample_metadata.description
        # YouTube should keep all tags
        assert len(adapted.tags) == len(sample_metadata.tags)
        
        # Test TikTok metadata adaptation
        adapted_tiktok = await platform_manager.adapt_metadata(sample_metadata, PlatformType.TIKTOK)
        
        # TikTok should convert tags to hashtags in description
        assert any(tag.replace('#', '') in adapted_tiktok.description for tag in sample_metadata.tags)
    
    def test_process_upload_results(self, platform_manager):
        """Test processing and formatting of upload results."""
        raw_results = [
            {"status": "success", "platform": "youtube", "platform_id": "youtube_123"},
            Exception("TikTok upload failed"),
            {"status": "success", "platform": "instagram", "platform_id": "instagram_456"}
        ]
        
        processed = platform_manager.process_upload_results(raw_results)
        
        assert len(processed) == 3
        
        # Check success results
        success_results = [r for r in processed if r["status"] == "success"]
        assert len(success_results) == 2
        
        # Check error result
        error_results = [r for r in processed if r["status"] == "error"]
        assert len(error_results) == 1
        assert "TikTok upload failed" in error_results[0]["error"]


class TestYouTubeUploader:
    """Test cases for YouTube uploader."""
    
    @pytest.fixture
    def mock_youtube_service(self):
        """Create mock YouTube API service."""
        service = Mock()
        
        # Mock videos().insert() chain
        insert_mock = Mock()
        insert_mock.execute.return_value = {
            "id": "youtube_video_123",
            "snippet": {"title": "Test Video"},
            "status": {"uploadStatus": "uploaded"}
        }
        
        service.videos.return_value.insert.return_value = insert_mock
        
        return service
    
    @pytest.fixture
    def youtube_uploader(self, mock_youtube_service):
        """Create YouTubeUploader with mocked service."""
        with patch('googleapiclient.discovery.build', return_value=mock_youtube_service):
            return YouTubeUploader(credentials_path="mock_credentials.json")
    
    @pytest.fixture
    def sample_video_file(self):
        """Create temporary video file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'mock video content for youtube test')
            yield f.name
        os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_upload_video_success(self, youtube_uploader, sample_video_file, sample_metadata):
        """Test successful video upload to YouTube."""
        result = await youtube_uploader.upload(sample_video_file, sample_metadata)
        
        assert result["status"] == "success"
        assert result["platform_id"] == "youtube_video_123"
        assert "youtube.com" in result["url"]
    
    @pytest.mark.asyncio
    async def test_upload_with_thumbnail(self, youtube_uploader, sample_video_file, sample_metadata):
        """Test video upload with custom thumbnail."""
        # Create mock thumbnail file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as thumb_file:
            thumb_file.write(b'mock thumbnail image')
            sample_metadata.thumbnail_path = thumb_file.name
        
        try:
            with patch.object(youtube_uploader.youtube.thumbnails(), 'set') as mock_thumbnail:
                mock_thumbnail.return_value.execute.return_value = {"kind": "youtube#thumbnailSetResponse"}
                
                result = await youtube_uploader.upload(sample_video_file, sample_metadata)
                
                assert result["status"] == "success"
                mock_thumbnail.assert_called_once()
        
        finally:
            os.unlink(sample_metadata.thumbnail_path)
    
    @pytest.mark.asyncio
    async def test_upload_api_error(self, youtube_uploader, sample_video_file, sample_metadata):
        """Test handling of YouTube API errors."""
        # Mock API to raise exception
        youtube_uploader.youtube.videos().insert().execute.side_effect = Exception("API quota exceeded")
        
        with pytest.raises(Exception, match="API quota exceeded"):
            await youtube_uploader.upload(sample_video_file, sample_metadata)
    
    def test_format_description(self, youtube_uploader, sample_metadata):
        """Test YouTube description formatting."""
        formatted = youtube_uploader.format_description(sample_metadata)
        
        assert sample_metadata.description in formatted
        assert all(tag in formatted for tag in sample_metadata.tags)
    
    def test_validate_metadata(self, youtube_uploader, sample_metadata):
        """Test YouTube metadata validation."""
        # Valid metadata should pass
        assert youtube_uploader.validate_metadata(sample_metadata) == True
        
        # Invalid metadata (too long title) should fail
        invalid_metadata = UploadMetadata(
            title="x" * 200,  # Too long for YouTube
            description="Valid description",
            tags=["valid"]
        )
        
        assert youtube_uploader.validate_metadata(invalid_metadata) == False


class TestTikTokUploader:
    """Test cases for TikTok uploader."""
    
    @pytest.fixture
    def mock_tiktok_api(self):
        """Create mock TikTok API client."""
        api = Mock()
        api.upload_video.return_value = {
            "data": {
                "video_id": "tiktok_video_789",
                "share_url": "https://tiktok.com/@user/video/789"
            }
        }
        return api
    
    @pytest.fixture
    def tiktok_uploader(self, mock_tiktok_api):
        """Create TikTokUploader with mocked API."""
        with patch('tiktok_uploader.TikTokApi', return_value=mock_tiktok_api):
            return TikTokUploader(access_token="mock_token")
    
    @pytest.mark.asyncio
    async def test_upload_video_success(self, tiktok_uploader, sample_video_file, sample_metadata):
        """Test successful video upload to TikTok."""
        result = await tiktok_uploader.upload(sample_video_file, sample_metadata)
        
        assert result["status"] == "success"
        assert result["platform_id"] == "tiktok_video_789"
        assert "tiktok.com" in result["url"]
    
    def test_format_caption(self, tiktok_uploader, sample_metadata):
        """Test TikTok caption formatting."""
        caption = tiktok_uploader.format_caption(sample_metadata)
        
        assert sample_metadata.description in caption
        # Tags should be converted to hashtags
        assert all(f"#{tag}" in caption for tag in sample_metadata.tags)
    
    def test_prepare_video_for_reels(self, instagram_uploader, sample_video_file):
        """Test video preparation for Instagram Reels."""
        with patch('moviepy.editor.VideoFileClip') as mock_video:
            mock_clip = Mock()
            mock_clip.duration = 45
            mock_clip.resize.return_value = mock_clip
            mock_clip.crop.return_value = mock_clip
            mock_clip.write_videofile.return_value = None
            mock_video.return_value = mock_clip
            
            prepared_video = instagram_uploader.prepare_video_for_reels(sample_video_file)
            
            assert prepared_video.endswith('_reels.mp4')
            mock_clip.resize.assert_called()


class TestFacebookUploader:
    """Test cases for Facebook uploader."""
    
    @pytest.fixture
    def mock_facebook_api(self):
        """Create mock Facebook Graph API."""
        api = Mock()
        api.put_video.return_value = {
            "id": "facebook_video_321",
            "permalink_url": "https://facebook.com/video/321"
        }
        return api
    
    @pytest.fixture
    def facebook_uploader(self, mock_facebook_api):
        """Create FacebookUploader with mocked API."""
        with patch('facebook.GraphAPI', return_value=mock_facebook_api):
            return FacebookUploader(access_token="mock_fb_token", page_id="test_page")
    
    @pytest.mark.asyncio
    async def test_upload_video_success(self, facebook_uploader, sample_video_file, sample_metadata):
        """Test successful video upload to Facebook."""
        result = await facebook_uploader.upload(sample_video_file, sample_metadata)
        
        assert result["status"] == "success"
        assert result["platform_id"] == "facebook_video_321"
        assert "facebook.com" in result["url"]
    
    def test_format_post_content(self, facebook_uploader, sample_metadata):
        """Test Facebook post content formatting."""
        content = facebook_uploader.format_post_content(sample_metadata)
        
        assert sample_metadata.title in content
        assert sample_metadata.description in content
        # Facebook uses hashtags differently
        assert any(tag in content for tag in sample_metadata.tags)


class TestContentOptimization:
    """Test content optimization for different platforms."""
    
    @pytest.fixture
    def platform_manager(self):
        """Create PlatformManager for optimization testing."""
        return PlatformManager()
    
    @pytest.fixture
    def sample_video_path(self):
        """Create sample video file."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'sample video content for optimization testing')
            yield f.name
        os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_youtube_video_optimization(self, platform_manager, sample_video_path):
        """Test YouTube video optimization (16:9, 1080p)."""
        with patch('moviepy.editor.VideoFileClip') as mock_video:
            mock_clip = Mock()
            mock_clip.size = [1920, 1080]
            mock_clip.duration = 300
            mock_clip.resize.return_value = mock_clip
            mock_clip.write_videofile = Mock()
            mock_video.return_value = mock_clip
            
            optimized = await platform_manager.optimize_for_platform(
                sample_video_path, PlatformType.YOUTUBE
            )
            
            # Should maintain 16:9 aspect ratio for YouTube
            assert optimized.endswith('_youtube.mp4')
            mock_clip.resize.assert_called_with(height=1080)
    
    @pytest.mark.asyncio
    async def test_tiktok_video_optimization(self, platform_manager, sample_video_path):
        """Test TikTok video optimization (9:16 vertical)."""
        with patch('moviepy.editor.VideoFileClip') as mock_video:
            mock_clip = Mock()
            mock_clip.size = [1920, 1080]  # Original horizontal
            mock_clip.duration = 60
            mock_clip.resize.return_value = mock_clip
            mock_clip.crop.return_value = mock_clip
            mock_clip.write_videofile = Mock()
            mock_video.return_value = mock_clip
            
            optimized = await platform_manager.optimize_for_platform(
                sample_video_path, PlatformType.TIKTOK
            )
            
            # Should convert to vertical for TikTok
            assert optimized.endswith('_tiktok.mp4')
            mock_clip.resize.assert_called()
            mock_clip.crop.assert_called()
    
    @pytest.mark.asyncio
    async def test_instagram_video_optimization(self, platform_manager, sample_video_path):
        """Test Instagram video optimization (square or vertical)."""
        with patch('moviepy.editor.VideoFileClip') as mock_video:
            mock_clip = Mock()
            mock_clip.size = [1920, 1080]
            mock_clip.duration = 90  # Over 60 seconds
            mock_clip.resize.return_value = mock_clip
            mock_clip.subclip.return_value = mock_clip
            mock_clip.write_videofile = Mock()
            mock_video.return_value = mock_clip
            
            optimized = await platform_manager.optimize_for_platform(
                sample_video_path, PlatformType.INSTAGRAM
            )
            
            # Should trim to 60 seconds max for Instagram
            assert optimized.endswith('_instagram.mp4')
            mock_clip.subclip.assert_called_with(0, 60)
    
    @pytest.mark.asyncio
    async def test_facebook_video_optimization(self, platform_manager, sample_video_path):
        """Test Facebook video optimization."""
        with patch('moviepy.editor.VideoFileClip') as mock_video:
            mock_clip = Mock()
            mock_clip.size = [1920, 1080]
            mock_clip.duration = 120
            mock_clip.resize.return_value = mock_clip
            mock_clip.write_videofile = Mock()
            mock_video.return_value = mock_clip
            
            optimized = await platform_manager.optimize_for_platform(
                sample_video_path, PlatformType.FACEBOOK
            )
            
            # Facebook supports various formats
            assert optimized.endswith('_facebook.mp4')
            mock_clip.resize.assert_called()


class TestUploadStatusTracking:
    """Test upload status tracking and monitoring."""
    
    @pytest.fixture
    def platform_manager(self):
        """Create PlatformManager for status tracking tests."""
        return PlatformManager()
    
    @pytest.mark.asyncio
    async def test_track_upload_progress(self, platform_manager):
        """Test tracking upload progress across platforms."""
        content = "/tmp/test_video.mp4"
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK]
        metadata = UploadMetadata(title="Test", description="Test video")
        
        # Mock uploaders with progress tracking
        upload_progress = {}
        
        async def mock_upload_with_progress(platform):
            upload_progress[platform] = "uploading"
            await asyncio.sleep(0.1)  # Simulate upload time
            upload_progress[platform] = "processing"
            await asyncio.sleep(0.1)  # Simulate processing time
            upload_progress[platform] = "completed"
            return {"status": "success", "platform_id": f"{platform}_123"}
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.return_value = content
            mock_adapt.return_value = metadata
            
            # Mock individual uploaders
            for platform in platforms:
                uploader = Mock()
                uploader.upload = AsyncMock(side_effect=lambda: mock_upload_with_progress(platform))
                platform_manager.platforms[platform] = uploader
            
            results = await platform_manager.upload_content(content, platforms, metadata)
            
            # All uploads should complete
            assert len(results) == 2
            assert all(result["status"] == "success" for result in results)
            
            # Progress should be tracked
            assert all(status == "completed" for status in upload_progress.values())
    
    def test_upload_retry_mechanism(self, platform_manager):
        """Test retry mechanism for failed uploads."""
        uploader = Mock()
        
        # Fail first two attempts, succeed on third
        uploader.upload = AsyncMock(side_effect=[
            Exception("Network error"),
            Exception("Temporary failure"), 
            {"status": "success", "platform_id": "retry_success"}
        ])
        
        async def upload_with_retry():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return await uploader.upload("/tmp/test.mp4", {})
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
            
        # Test the retry mechanism
        result = asyncio.run(upload_with_retry())
        assert result["status"] == "success"
        assert result["platform_id"] == "retry_success"
        assert uploader.upload.call_count == 3
    
    @pytest.mark.asyncio
    async def test_upload_timeout_handling(self, platform_manager):
        """Test handling of upload timeouts."""
        uploader = Mock()
        
        # Mock slow upload that times out
        async def slow_upload(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate very slow upload
            return {"status": "success"}
        
        uploader.upload = slow_upload
        platform_manager.platforms[PlatformType.YOUTUBE] = uploader
        
        content = "/tmp/test_video.mp4"
        platforms = [PlatformType.YOUTUBE]
        metadata = UploadMetadata(title="Test", description="Test")
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.return_value = content
            mock_adapt.return_value = metadata
            
            # Should timeout and handle gracefully
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    platform_manager.upload_content(content, platforms, metadata),
                    timeout=1.0
                )


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms."""
    
    @pytest.fixture
    def platform_manager(self):
        """Create PlatformManager for error testing."""
        return PlatformManager()
    
    @pytest.mark.asyncio
    async def test_partial_upload_failure(self, platform_manager):
        """Test handling when some platforms fail."""
        content = "/tmp/test_video.mp4"
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        metadata = UploadMetadata(title="Test", description="Test video")
        
        # Mock mixed success/failure
        youtube_uploader = Mock()
        youtube_uploader.upload = AsyncMock(return_value={"status": "success", "platform_id": "yt_123"})
        
        tiktok_uploader = Mock()
        tiktok_uploader.upload = AsyncMock(side_effect=Exception("TikTok API error"))
        
        instagram_uploader = Mock()
        instagram_uploader.upload = AsyncMock(return_value={"status": "success", "platform_id": "ig_456"})
        
        platform_manager.platforms = {
            PlatformType.YOUTUBE: youtube_uploader,
            PlatformType.TIKTOK: tiktok_uploader,
            PlatformType.INSTAGRAM: instagram_uploader
        }
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.return_value = content
            mock_adapt.return_value = metadata
            
            results = await platform_manager.upload_content(content, platforms, metadata)
            
            # Should have 3 results (2 success, 1 error)
            assert len(results) == 3
            
            success_results = [r for r in results if r.get("status") == "success"]
            error_results = [r for r in results if r.get("status") == "error"]
            
            assert len(success_results) == 2
            assert len(error_results) == 1
            assert "TikTok API error" in error_results[0]["error"]
    
    @pytest.mark.asyncio
    async def test_content_optimization_failure(self, platform_manager):
        """Test handling of content optimization failures."""
        content = "/tmp/test_video.mp4"
        platforms = [PlatformType.YOUTUBE]
        metadata = UploadMetadata(title="Test", description="Test")
        
        # Mock optimization to fail
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.side_effect = Exception("Video processing failed")
            mock_adapt.return_value = metadata
            
            results = await platform_manager.upload_content(content, platforms, metadata)
            
            # Should handle optimization failure gracefully
            assert len(results) == 1
            assert results[0]["status"] == "error"
            assert "Video processing failed" in results[0]["error"]
    
    def test_invalid_content_handling(self, platform_manager):
        """Test handling of invalid content files."""
        invalid_content = "/tmp/nonexistent_video.mp4"
        platforms = [PlatformType.YOUTUBE]
        metadata = UploadMetadata(title="Test", description="Test")
        
        # Should validate content exists before processing
        with pytest.raises(FileNotFoundError):
            asyncio.run(platform_manager.upload_content(invalid_content, platforms, metadata))
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_handling(self, platform_manager):
        """Test handling of API rate limits."""
        uploader = Mock()
        
        # Mock rate limit error followed by success
        uploader.upload = AsyncMock(side_effect=[
            Exception("Rate limit exceeded. Try again in 60 seconds"),
            {"status": "success", "platform_id": "rate_limit_success"}
        ])
        
        platform_manager.platforms[PlatformType.YOUTUBE] = uploader
        
        content = "/tmp/test_video.mp4"
        platforms = [PlatformType.YOUTUBE]
        metadata = UploadMetadata(title="Test", description="Test")
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:  # Mock sleep for testing
            
            mock_opt.return_value = content
            mock_adapt.return_value = metadata
            
            # Should implement rate limit backoff
            results = await platform_manager.upload_content(content, platforms, metadata)
            
            # Should eventually succeed after rate limit
            assert len(results) == 1
            # Implementation would determine if it retries or fails


class TestMetadataHandling:
    """Test metadata handling and validation."""
    
    def test_upload_metadata_validation(self):
        """Test UploadMetadata validation."""
        # Valid metadata
        valid_metadata = UploadMetadata(
            title="Valid Title",
            description="Valid description",
            tags=["tag1", "tag2"],
            category="Education",
            privacy="public"
        )
        
        assert valid_metadata.title == "Valid Title"
        assert len(valid_metadata.tags) == 2
        
        # Invalid metadata - empty title
        with pytest.raises(ValueError):
            UploadMetadata(title="", description="Valid description")
    
    def test_metadata_sanitization(self):
        """Test metadata sanitization for different platforms."""
        metadata = UploadMetadata(
            title="Title with <script>alert('xss')</script>",
            description="Description with\nnewlines\tand\ttabs",
            tags=["tag with spaces", "UPPERCASE", "special@chars#"]
        )
        
        sanitized = metadata.sanitize_for_platform(PlatformType.YOUTUBE)
        
        # Should remove HTML tags
        assert "<script>" not in sanitized.title
        assert "alert" not in sanitized.title
        
        # Should normalize whitespace
        assert "\n" not in sanitized.description
        assert "\t" not in sanitized.description
        
        # Should clean tags
        assert all(" " not in tag for tag in sanitized.tags if len(tag) > 0)
    
    def test_metadata_character_limits(self):
        """Test metadata character limit enforcement."""
        long_title = "x" * 200
        long_description = "x" * 10000
        many_tags = [f"tag{i}" for i in range(100)]
        
        metadata = UploadMetadata(
            title=long_title,
            description=long_description,
            tags=many_tags
        )
        
        # YouTube limits
        youtube_metadata = metadata.limit_for_platform(PlatformType.YOUTUBE)
        assert len(youtube_metadata.title) <= 100  # YouTube title limit
        assert len(youtube_metadata.description) <= 5000  # YouTube description limit
        assert len(youtube_metadata.tags) <= 15  # YouTube tag limit
        
        # TikTok limits
        tiktok_metadata = metadata.limit_for_platform(PlatformType.TIKTOK)
        assert len(tiktok_metadata.description) <= 300  # TikTok caption limit


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) for tag in sample_metadata.tags)
    
    def test_validate_video_specs(self, tiktok_uploader, sample_video_file):
        """Test TikTok video specification validation."""
        # Mock video properties check
        with patch('moviepy.editor.VideoFileClip') as mock_video:
            mock_clip = Mock()
            mock_clip.duration = 30  # Valid duration
            mock_clip.size = [1080, 1920]  # Valid vertical resolution
            mock_video.return_value = mock_clip
            
            assert tiktok_uploader.validate_video_specs(sample_video_file) == True
            
            # Test invalid duration
            mock_clip.duration = 200  # Too long
            assert tiktok_uploader.validate_video_specs(sample_video_file) == False


class TestInstagramUploader:
    """Test cases for Instagram uploader."""
    
    @pytest.fixture
    def mock_instagram_api(self):
        """Create mock Instagram API."""
        api = Mock()
        api.upload_video.return_value = {
            "id": "instagram_media_456",
            "permalink": "https://instagram.com/p/abc123"
        }
        return api
    
    @pytest.fixture
    def instagram_uploader(self, mock_instagram_api):
        """Create InstagramUploader with mocked API."""
        with patch('instagram_private_api.Client', return_value=mock_instagram_api):
            return InstagramUploader(username="test_user", password="test_pass")
    
    @pytest.mark.asyncio
    async def test_upload_reel_success(self, instagram_uploader, sample_video_file, sample_metadata):
        """Test successful Reel upload to Instagram."""
        result = await instagram_uploader.upload(sample_video_file, sample_metadata)
        
        assert result["status"] == "success"
        assert result["platform_id"] == "instagram_media_456"
        assert "instagram.com" in result["url"]
    
    def test_format_caption_with_hashtags(self, instagram_uploader, sample_metadata):
        """Test Instagram caption formatting with hashtags."""
        caption = instagram_uploader.format_caption(sample_metadata)
        
        assert sample_metadata.description in caption
        # Should add hashtags
        assert all(f"#{tag}" in caption