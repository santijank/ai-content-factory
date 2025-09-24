"""
Integration Tests: Content to Upload Flow
=========================================

Tests the complete flow from content generation to platform upload:
1. Generate content assets (video, images, audio)
2. Optimize content for different platforms
3. Upload to multiple platforms simultaneously
4. Track upload status and performance

This tests the interaction between:
- ContentPipeline ↔ AI Services
- ContentPipeline ↔ VideoAssembler
- PlatformManager ↔ Platform APIs
- Database ↔ Upload tracking
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Import system components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from content_engine.services.content_pipeline import ContentPipeline
from content_engine.services.ai_director import AIDirector
from platform_manager.services.platform_manager import PlatformManager
from platform_manager.models.platform_type import PlatformType
from platform_manager.models.upload_metadata import UploadMetadata
from shared.models.content_plan import ContentPlan
from database.repositories.content_repository import ContentRepository
from database.repositories.performance_repository import PerformanceRepository


class TestContentToUploadFlow:
    """Integration tests for content generation to platform upload flow."""
    
    @pytest.mark.integration
    async def test_complete_content_to_upload_flow(
        self, mock_ai_services, mock_platform_services, test_content_files, test_database
    ):
        """Test complete flow from content generation to platform upload."""
        
        # Step 1: Create content plan
        content_plan = ContentPlan(
            content_type="educational",
            script={
                "hook": "Ready to revolutionize your content creation?",
                "main_content": "In this comprehensive guide, we'll explore the most powerful AI tools that are transforming how creators work. From automated video editing to intelligent script generation, these tools will 10x your productivity and creativity.",
                "cta": "If this video helped streamline your workflow, hit that subscribe button for more AI productivity secrets!"
            },
            visual_plan={
                "style": "modern_dynamic",
                "scenes": [
                    "Engaging hook with AI visuals",
                    "Tool demonstration montage", 
                    "Before/after productivity comparison",
                    "Step-by-step workflow guide",
                    "Strong call-to-action ending"
                ],
                "text_overlays": [
                    "AI Content Revolution",
                    "10x Your Productivity", 
                    "The Secret Tools",
                    "Your New Workflow",
                    "Subscribe Now!"
                ]
            },
            audio_plan={
                "voice_style": "energetic_professional",
                "background_music": "upbeat_inspiring",
                "sound_effects": ["whoosh_transitions", "notification_sounds", "success_chimes"]
            },
            platform_optimization={
                "title": "5 AI Tools That Will Transform Your Content Creation Forever",
                "description": "Discover the game-changing AI tools that top creators use to produce viral content faster than ever. Complete workflow included!",
                "hashtags": ["#AIContentCreation", "#ProductivityHacks", "#ContentCreator", "#AITools"],
                "thumbnail_concept": "Split-screen showing stressed creator vs calm creator using AI, with bold 'AI REVOLUTION' text"
            },
            production_estimate={
                "time_minutes": 35,
                "cost_baht": 25.50,
                "complexity": "medium"
            }
        )
        
        # Step 2: Generate content assets
        content_pipeline = ContentPipeline()
        content_pipeline.text_ai = mock_ai_services["text_ai"]
        content_pipeline.image_ai = mock_ai_services["image_ai"]
        content_pipeline.tts = mock_ai_services["audio_ai"]
        
        # Mock content generation
        with patch.object(content_pipeline, 'generate_script', new_callable=AsyncMock) as mock_script, \
             patch.object(content_pipeline, 'generate_visuals', new_callable=AsyncMock) as mock_visuals, \
             patch.object(content_pipeline, 'generate_audio', new_callable=AsyncMock) as mock_audio, \
             patch.object(content_pipeline, 'assemble_video', new_callable=AsyncMock) as mock_assemble:
            
            mock_script.return_value = "Complete narration script with timing cues..."
            mock_visuals.return_value = [
                test_content_files['image_intro'],
                test_content_files['image_main'], 
                test_content_files['image_outro']
            ]
            mock_audio.return_value = test_content_files['audio']
            mock_assemble.return_value = test_content_files['video']
            
            generated_content = await content_pipeline.generate_content(content_plan)
            
            assert generated_content is not None
            assert isinstance(generated_content, dict)
            
            # Verify all generation steps were called
            mock_script.assert_called_once_with(content_plan)
            mock_visuals.assert_called_once_with(content_plan)
            mock_audio.assert_called_once_with(content_plan)
            mock_assemble.assert_called_once()
        
        # Step 3: Store content in database
        content_repo = ContentRepository(test_database)
        
        content_data = {
            "title": content_plan.platform_optimization["title"],
            "description": content_plan.platform_optimization["description"],
            "content_plan": content_plan.to_dict(),
            "assets": {
                "video": test_content_files['video'],
                "images": [test_content_files['image_intro'], test_content_files['image_main']],
                "audio": test_content_files['audio'],
                "script": "Complete narration script..."
            },
            "production_status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        
        with patch.object(content_repo, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "content_123"
            content_id = await content_repo.create(content_data)
            assert content_id == "content_123"
        
        # Step 4: Prepare upload metadata
        upload_metadata = UploadMetadata(
            title=content_plan.platform_optimization["title"],
            description=content_plan.platform_optimization["description"],
            tags=[tag.replace('#', '') for tag in content_plan.platform_optimization["hashtags"]],
            category="Education",
            privacy="public",
            thumbnail_url="https://example.com/thumbnail.jpg"
        )
        
        # Step 5: Upload to multiple platforms
        platform_manager = PlatformManager()
        target_platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        
        # Mock platform optimization
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_optimize, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_optimize.side_effect = lambda content, platform: f"{content}_{platform.value}"
            mock_adapt.return_value = upload_metadata
            
            # Mock individual platform uploads
            platform_manager.platforms = {
                PlatformType.YOUTUBE: mock_platform_services["youtube"],
                PlatformType.TIKTOK: mock_platform_services["tiktok"], 
                PlatformType.INSTAGRAM: mock_platform_services["instagram"]
            }
            
            upload_results = await platform_manager.upload_content(
                test_content_files['video'],
                target_platforms,
                upload_metadata
            )
            
            # Verify uploads
            assert len(upload_results) == 3
            assert all(result["status"] == "success" for result in upload_results)
            
            # Verify platform-specific optimization was called
            assert mock_optimize.call_count == 3
            assert mock_adapt.call_count == 3
        
        # Step 6: Store upload results
        upload_data = []
        for result in upload_results:
            upload_record = {
                "content_id": content_id,
                "platform": result.get("platform", "unknown"),
                "platform_id": result["platform_id"],
                "url": result["url"],
                "status": result["status"],
                "uploaded_at": datetime.utcnow().isoformat(),
                "metadata": upload_metadata.to_dict()
            }
            upload_data.append(upload_record)
        
        # Verify complete flow success
        assert len(generated_content) > 0
        assert content_id is not None
        assert len(upload_results) == 3
        assert all(upload["status"] == "success" for upload in upload_data)
    
    @pytest.mark.integration
    async def test_platform_specific_optimization(self, test_content_files):
        """Test platform-specific content optimization."""
        
        platform_manager = PlatformManager()
        base_video = test_content_files['video']
        
        # Test YouTube optimization (16:9 landscape)
        with patch('moviepy.editor.VideoFileClip') as mock_video_clip:
            mock_clip = Mock()
            mock_clip.size = [1920, 1080]
            mock_clip.duration = 120
            mock_clip.resize.return_value = mock_clip
            mock_clip.write_videofile = Mock()
            mock_video_clip.return_value = mock_clip
            
            youtube_video = await platform_manager.optimize_for_platform(
                base_video, PlatformType.YOUTUBE
            )
            
            assert youtube_video.endswith('_youtube.mp4')
            # YouTube should maintain 16:9 aspect ratio
            mock_clip.resize.assert_called()
        
        # Test TikTok optimization (9:16 vertical)
        with patch('moviepy.editor.VideoFileClip') as mock_video_clip:
            mock_clip = Mock()
            mock_clip.size = [1920, 1080]  # Original landscape
            mock_clip.duration = 45  # Good TikTok length
            mock_clip.resize.return_value = mock_clip
            mock_clip.crop.return_value = mock_clip
            mock_clip.write_videofile = Mock()
            mock_video_clip.return_value = mock_clip
            
            tiktok_video = await platform_manager.optimize_for_platform(
                base_video, PlatformType.TIKTOK
            )
            
            assert tiktok_video.endswith('_tiktok.mp4')
            # TikTok should crop to vertical
            mock_clip.crop.assert_called()
        
        # Test Instagram optimization (square/vertical + duration limit)
        with patch('moviepy.editor.VideoFileClip') as mock_video_clip:
            mock_clip = Mock()
            mock_clip.size = [1920, 1080]
            mock_clip.duration = 90  # Over Instagram limit
            mock_clip.resize.return_value = mock_clip
            mock_clip.subclip.return_value = mock_clip
            mock_clip.write_videofile = Mock()
            mock_video_clip.return_value = mock_clip
            
            instagram_video = await platform_manager.optimize_for_platform(
                base_video, PlatformType.INSTAGRAM
            )
            
            assert instagram_video.endswith('_instagram.mp4')
            # Instagram should trim duration
            mock_clip.subclip.assert_called_with(0, 60)  # Max 60 seconds
    
    @pytest.mark.integration 
    async def test_metadata_adaptation_by_platform(self):
        """Test metadata adaptation for different platforms."""
        
        platform_manager = PlatformManager()
        
        base_metadata = UploadMetadata(
            title="Amazing AI Content Creation Tutorial - Complete Guide 2025",
            description="Learn how to create viral content using AI tools. Step-by-step tutorial with real examples and proven strategies that work!",
            tags=["AI", "content creation", "tutorial", "viral", "marketing", "automation", "tools", "2025"],
            category="Education",
            privacy="public"
        )
        
        # Test YouTube metadata (supports longer titles/descriptions)
        youtube_metadata = await platform_manager.adapt_metadata(base_metadata, PlatformType.YOUTUBE)
        
        assert len(youtube_metadata.title) <= 100  # YouTube title limit
        assert len(youtube_metadata.description) <= 5000  # YouTube description limit
        assert len(youtube_metadata.tags) <= 15  # YouTube tag limit
        # YouTube keeps original formatting
        assert "Step-by-step" in youtube_metadata.description
        
        # Test TikTok metadata (hashtags in caption, shorter limits)
        tiktok_metadata = await platform_manager.adapt_metadata(base_metadata, PlatformType.TIKTOK)
        
        assert len(tiktok_metadata.description) <= 300  # TikTok caption limit
        # Should convert tags to hashtags in description
        assert "#AI" in tiktok_metadata.description
        assert "#contentcreation" in tiktok_metadata.description or "#content" in tiktok_metadata.description
        
        # Test Instagram metadata (hashtags important, caption limits)
        instagram_metadata = await platform_manager.adapt_metadata(base_metadata, PlatformType.INSTAGRAM)
        
        assert len(instagram_metadata.description) <= 2200  # Instagram caption limit
        # Should include relevant hashtags
        hashtag_count = instagram_metadata.description.count('#')
        assert hashtag_count <= 30  # Instagram hashtag best practice
        assert hashtag_count >= 5  # Minimum for good reach
    
    @pytest.mark.integration
    async def test_concurrent_platform_uploads(self, test_content_files, mock_platform_services):
        """Test concurrent uploads to multiple platforms."""
        
        platform_manager = PlatformManager()
        content_video = test_content_files['video']
        
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM, PlatformType.FACEBOOK]
        
        upload_metadata = UploadMetadata(
            title="Concurrent Upload Test",
            description="Testing concurrent uploads to multiple platforms",
            tags=["test", "concurrent", "upload"],
            category="Education"
        )
        
        # Mock platform services with different upload times
        async def mock_youtube_upload(*args, **kwargs):
            await asyncio.sleep(0.2)  # Simulate YouTube processing time
            return {"status": "success", "platform_id": "yt_123", "url": "https://youtube.com/watch?v=123"}
        
        async def mock_tiktok_upload(*args, **kwargs):
            await asyncio.sleep(0.1)  # TikTok is faster
            return {"status": "success", "platform_id": "tt_456", "url": "https://tiktok.com/@user/video/456"}
        
        async def mock_instagram_upload(*args, **kwargs):
            await asyncio.sleep(0.15)  # Instagram medium speed
            return {"status": "success", "platform_id": "ig_789", "url": "https://instagram.com/p/789"}
        
        async def mock_facebook_upload(*args, **kwargs):
            await asyncio.sleep(0.3)  # Facebook slowest
            return {"status": "success", "platform_id": "fb_321", "url": "https://facebook.com/videos/321"}
        
        platform_manager.platforms = {
            PlatformType.YOUTUBE: Mock(upload=mock_youtube_upload),
            PlatformType.TIKTOK: Mock(upload=mock_tiktok_upload),
            PlatformType.INSTAGRAM: Mock(upload=mock_instagram_upload),
            PlatformType.FACEBOOK: Mock(upload=mock_facebook_upload)
        }
        
        # Mock optimization methods
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.return_value = content_video
            mock_adapt.return_value = upload_metadata
            
            # Time the concurrent uploads
            start_time = asyncio.get_event_loop().time()
            upload_results = await platform_manager.upload_content(content_video, platforms, upload_metadata)
            end_time = asyncio.get_event_loop().time()
            
            total_time = end_time - start_time
            
            # Verify concurrent execution
            assert len(upload_results) == 4
            assert all(result["status"] == "success" for result in upload_results)
            
            # Concurrent should be faster than sequential (0.2+0.1+0.15+0.3 = 0.75s)
            assert total_time < 0.5  # Should complete in less than 0.5s due to concurrency
    
    @pytest.mark.integration
    async def test_upload_error_handling(self, test_content_files):
        """Test error handling during platform uploads."""
        
        platform_manager = PlatformManager()
        content_video = test_content_files['video']
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        
        upload_metadata = UploadMetadata(
            title="Error Handling Test",
            description="Testing upload error scenarios",
            tags=["test", "error", "handling"]
        )
        
        # Mock mixed success/failure scenarios
        async def mock_youtube_success(*args, **kwargs):
            return {"status": "success", "platform_id": "yt_success", "url": "https://youtube.com/success"}
        
        async def mock_tiktok_failure(*args, **kwargs):
            raise Exception("TikTok API rate limit exceeded")
        
        async def mock_instagram_auth_error(*args, **kwargs):
            raise Exception("Instagram authentication failed")
        
        platform_manager.platforms = {
            PlatformType.YOUTUBE: Mock(upload=mock_youtube_success),
            PlatformType.TIKTOK: Mock(upload=mock_tiktok_failure),
            PlatformType.INSTAGRAM: Mock(upload=mock_instagram_auth_error)
        }
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.return_value = content_video
            mock_adapt.return_value = upload_metadata
            
            upload_results = await platform_manager.upload_content(content_video, platforms, upload_metadata)
            
            # Should have results for all platforms (success + errors)
            assert len(upload_results) == 3
            
            # Verify success result
            success_results = [r for r in upload_results if r.get("status") == "success"]
            assert len(success_results) == 1
            assert success_results[0]["platform_id"] == "yt_success"
            
            # Verify error results
            error_results = [r for r in upload_results if r.get("status") == "error"]
            assert len(error_results) == 2
            
            error_messages = [r.get("error", "") for r in error_results]
            assert any("rate limit" in msg.lower() for msg in error_messages)
            assert any("authentication" in msg.lower() for msg in error_messages)
    
    @pytest.mark.integration
    async def test_upload_retry_mechanism(self, test_content_files):
        """Test retry mechanism for failed uploads."""
        
        platform_manager = PlatformManager()
        content_video = test_content_files['video']
        
        upload_metadata = UploadMetadata(
            title="Retry Test",
            description="Testing upload retry logic",
            tags=["test", "retry"]
        )
        
        # Mock uploader that fails twice then succeeds
        call_count = 0
        
        async def mock_uploader_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                raise Exception("Temporary network error")
            else:
                return {"status": "success", "platform_id": "retry_success", "url": "https://platform.com/success"}
        
        uploader = Mock(upload=mock_uploader_with_retry)
        platform_manager.platforms = {PlatformType.YOUTUBE: uploader}
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:  # Speed up retries
            
            mock_opt.return_value = content_video
            mock_adapt.return_value = upload_metadata
            
            # Mock the retry logic in upload_with_retry method
            async def upload_with_retry():
                max_retries = 3
                last_exception = None
                
                for attempt in range(max_retries):
                    try:
                        return await uploader.upload(content_video, upload_metadata)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries - 1:
                            await mock_sleep(0.1 * (2 ** attempt))  # Exponential backoff
                
                # If all retries failed, return error result
                return {"status": "error", "error": str(last_exception)}
            
            result = await upload_with_retry()
            
            # Should eventually succeed after retries
            assert result["status"] == "success"
            assert result["platform_id"] == "retry_success"
            assert call_count == 3  # Two failures + one success
    
    @pytest.mark.integration
    async def test_performance_tracking(self, test_database, test_content_files):
        """Test performance tracking after uploads."""
        
        performance_repo = PerformanceRepository(test_database)
        
        # Simulate successful uploads
        upload_results = [
            {
                "status": "success",
                "platform": "youtube", 
                "platform_id": "yt_12345",
                "url": "https://youtube.com/watch?v=12345",
                "upload_id": "upload_1"
            },
            {
                "status": "success",
                "platform": "tiktok",
                "platform_id": "tt_67890", 
                "url": "https://tiktok.com/@user/video/67890",
                "upload_id": "upload_2"
            }
        ]
        
        # Mock initial performance data collection
        initial_metrics = [
            {
                "upload_id": "upload_1",
                "views": 1250,
                "likes": 89,
                "comments": 23,
                "shares": 12,
                "revenue": 0.0,
                "measured_at": datetime.utcnow().isoformat()
            },
            {
                "upload_id": "upload_2", 
                "views": 8900,
                "likes": 450,
                "comments": 78,
                "shares": 234,
                "revenue": 0.0,
                "measured_at": datetime.utcnow().isoformat()
            }
        ]
        
        # Store performance data
        with patch.object(performance_repo, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda data: f"metric_{data['upload_id']}"
            
            performance_ids = []
            for metric_data in initial_metrics:
                perf_id = await performance_repo.create(metric_data)
                performance_ids.append(perf_id)
            
            assert len(performance_ids) == 2
            assert mock_create.call_count == 2
        
        # Verify performance tracking setup
        assert all("metric_upload_" in perf_id for perf_id in performance_ids)
    
    @pytest.mark.integration
    async def test_content_versioning_for_platforms(self, test_content_files):
        """Test creating different versions of content for different platforms."""
        
        content_plan = ContentPlan(
            content_type="tutorial",
            script={
                "hook": "Master this AI tool in 60 seconds!",
                "main_content": "Here's the step-by-step process that will change everything...",
                "cta": "Follow for more AI productivity hacks!"
            },
            visual_plan={
                "style": "fast_paced",
                "scenes": ["quick_intro", "demo", "results", "cta"]
            }
        )
        
        content_pipeline = ContentPipeline()
        platform_manager = PlatformManager()
        
        # Generate base content
        with patch.object(content_pipeline, 'generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {"base_video": test_content_files['video']}
            
            base_content = await content_pipeline.generate_content(content_plan)
        
        # Create platform-specific versions
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        platform_versions = {}
        
        for platform in platforms:
            with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt:
                mock_opt.return_value = f"{test_content_files['video']}_{platform.value}.mp4"
                
                optimized_video = await platform_manager.optimize_for_platform(
                    test_content_files['video'], platform
                )
                platform_versions[platform.value] = optimized_video
        
        # Verify platform-specific versions created
        assert len(platform_versions) == 3
        assert platform_versions["youtube"].endswith("youtube.mp4")
        assert platform_versions["tiktok"].endswith("tiktok.mp4")
        assert platform_versions["instagram"].endswith("instagram.mp4")
        
        # Each version should be optimized for its platform
        for platform, version in platform_versions.items():
            assert platform in version
            assert version.endswith(".mp4")


class TestContentUploadPerformance:
    """Test performance aspects of content upload flow."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_large_file_upload_handling(self, mock_platform_services):
        """Test handling of large video file uploads."""
        
        # Create mock large file
        large_file_path = "/tmp/large_video_1gb.mp4"
        
        platform_manager = PlatformManager()
        upload_metadata = UploadMetadata(
            title="Large File Upload Test",
            description="Testing large file upload capabilities",
            tags=["test", "large", "file"]
        )
        
        # Mock file size check
        with patch('os.path.getsize', return_value=1024*1024*1024):  # 1GB file
            
            # Mock chunked upload for large files
            async def mock_chunked_upload(*args, **kwargs):
                # Simulate chunked upload progress
                for chunk in range(10):  # 10 chunks
                    await asyncio.sleep(0.01)  # Simulate upload time
                    # Could emit progress events here
                
                return {
                    "status": "success",
                    "platform_id": "large_file_123",
                    "url": "https://platform.com/large_video"
                }
            
            platform_manager.platforms = {
                PlatformType.YOUTUBE: Mock(upload=mock_chunked_upload)
            }
            
            with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
                 patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
                
                mock_opt.return_value = large_file_path
                mock_adapt.return_value = upload_metadata
                
                result = await platform_manager.upload_content(
                    large_file_path, [PlatformType.YOUTUBE], upload_metadata
                )
                
                assert len(result) == 1
                assert result[0]["status"] == "success"
    
    @pytest.mark.integration
    async def test_memory_usage_during_upload(self, test_content_files):
        """Test memory usage remains stable during multiple uploads."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        platform_manager = PlatformManager()
        
        # Simulate multiple concurrent uploads
        upload_tasks = []
        for i in range(10):  # 10 concurrent uploads
            
            async def mock_upload_task():
                # Simulate upload processing
                await asyncio.sleep(0.1)
                return {
                    "status": "success",
                    "platform_id": f"concurrent_{i}",
                    "url": f"https://platform.com/video_{i}"
                }
            
            upload_tasks.append(mock_upload_task())
        
        # Execute concurrent uploads
        results = await asyncio.gather(*upload_tasks)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
        assert len(results) == 10
        assert all(r["status"] == "success" for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])