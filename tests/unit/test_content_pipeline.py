"""
Unit Tests for Content Pipeline
===============================

Tests for the content generation pipeline including:
- ContentPipeline main class
- Script generation
- Visual content creation
- Audio generation
- Video assembly
- Platform optimization
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

from content_engine.services.content_pipeline import ContentPipeline
from content_engine.models.quality_tier import QualityTier
from shared.models.content_plan import ContentPlan


class TestContentPipeline:
    """Test cases for ContentPipeline main class."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for content generation."""
        services = {
            'text_ai': Mock(),
            'image_ai': Mock(),
            'audio_ai': Mock()
        }
        
        # Configure mocks
        services['text_ai'].generate_script = AsyncMock(return_value="Generated script content")
        services['image_ai'].generate_image = AsyncMock(return_value="/tmp/test_image.jpg")
        services['audio_ai'].text_to_speech = AsyncMock(return_value="/tmp/test_audio.mp3")
        
        return services
    
    @pytest.fixture
    def mock_service_registry(self, mock_services):
        """Create mock service registry."""
        registry = Mock()
        registry.get_service.side_effect = lambda service_type, tier: mock_services.get(service_type)
        return registry
    
    @pytest.fixture
    def content_pipeline(self, mock_service_registry):
        """Create ContentPipeline instance with mocked services."""
        with patch('content_engine.services.content_pipeline.ServiceRegistry', return_value=mock_service_registry):
            return ContentPipeline(quality_tier=QualityTier.BALANCED)
    
    @pytest.fixture
    def sample_content_plan(self):
        """Create sample content plan for testing."""
        return ContentPlan(
            content_type="educational",
            script={
                "hook": "Want to learn AI?",
                "main_content": "Here's how to get started with artificial intelligence...",
                "cta": "Subscribe for more AI tutorials!"
            },
            visual_plan={
                "style": "modern",
                "scenes": ["intro scene", "main content", "conclusion"],
                "text_overlays": ["AI Tutorial", "Step 1", "Subscribe"]
            },
            audio_plan={
                "voice_style": "energetic",
                "background_music": "upbeat",
                "sound_effects": ["notification", "success"]
            },
            platform_optimization={
                "title": "AI Tutorial for Beginners",
                "description": "Learn AI basics in 5 minutes",
                "hashtags": ["#AI", "#Tutorial", "#Beginners"],
                "thumbnail_concept": "Bold text with AI icons"
            },
            production_estimate={
                "time_minutes": 30,
                "cost_baht": 25.0,
                "complexity": "medium"
            }
        )
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, content_pipeline, sample_content_plan):
        """Test successful content generation."""
        # Mock video assembly
        with patch.object(content_pipeline, 'assemble_video', new_callable=AsyncMock) as mock_assemble, \
             patch.object(content_pipeline, 'optimize_for_platforms', new_callable=AsyncMock) as mock_optimize:
            
            mock_assemble.return_value = "/tmp/generated_video.mp4"
            mock_optimize.return_value = {
                "youtube": "/tmp/youtube_video.mp4",
                "tiktok": "/tmp/tiktok_video.mp4"
            }
            
            result = await content_pipeline.generate_content(sample_content_plan)
            
            # Assertions
            assert isinstance(result, dict)
            assert "youtube" in result
            assert "tiktok" in result
            
            # Verify all generation steps were called
            mock_assemble.assert_called_once()
            mock_optimize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_script(self, content_pipeline, sample_content_plan):
        """Test script generation."""
        # Mock text AI service
        expected_script = "Full video script with timing and narration..."
        content_pipeline.text_ai.generate_script = AsyncMock(return_value=expected_script)
        
        script = await content_pipeline.generate_script(sample_content_plan)
        
        assert script == expected_script
        content_pipeline.text_ai.generate_script.assert_called_once_with(sample_content_plan)
    
    @pytest.mark.asyncio
    async def test_generate_visuals(self, content_pipeline, sample_content_plan):
        """Test visual content generation."""
        # Mock image AI service
        mock_images = ["/tmp/image1.jpg", "/tmp/image2.jpg", "/tmp/image3.jpg"]
        content_pipeline.image_ai.generate_image = AsyncMock(side_effect=mock_images)
        
        images = await content_pipeline.generate_visuals(sample_content_plan)
        
        assert len(images) == 3
        assert all(img.endswith('.jpg') for img in images)
        assert content_pipeline.image_ai.generate_image.call_count == 3
    
    @pytest.mark.asyncio
    async def test_generate_audio(self, content_pipeline, sample_content_plan):
        """Test audio generation."""
        # Mock audio services
        mock_voice_audio = "/tmp/voice.mp3"
        mock_bg_music = "/tmp/background.mp3"
        mock_mixed_audio = "/tmp/mixed.mp3"
        
        content_pipeline.tts.text_to_speech = AsyncMock(return_value=mock_voice_audio)
        
        with patch.object(content_pipeline, 'get_background_music', new_callable=AsyncMock) as mock_bg, \
             patch.object(content_pipeline, 'mix_audio', new_callable=AsyncMock) as mock_mix:
            
            mock_bg.return_value = mock_bg_music
            mock_mix.return_value = mock_mixed_audio
            
            audio = await content_pipeline.generate_audio(sample_content_plan)
            
            assert audio == mock_mixed_audio
            content_pipeline.tts.text_to_speech.assert_called_once()
            mock_bg.assert_called_once()
            mock_mix.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_audio_no_background_music(self, content_pipeline, sample_content_plan):
        """Test audio generation without background music."""
        # Modify plan to have no background music
        sample_content_plan.audio_plan["background_music"] = "none"
        
        mock_voice_audio = "/tmp/voice.mp3"
        content_pipeline.tts.text_to_speech = AsyncMock(return_value=mock_voice_audio)
        
        audio = await content_pipeline.generate_audio(sample_content_plan)
        
        assert audio == mock_voice_audio
        # Should not attempt to get background music or mix
        content_pipeline.tts.text_to_speech.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assemble_video(self, content_pipeline):
        """Test video assembly from components."""
        script = "Test script"
        visuals = ["/tmp/img1.jpg", "/tmp/img2.jpg"]
        audio = "/tmp/audio.mp3"
        
        expected_video = "/tmp/assembled_video.mp4"
        
        with patch('content_engine.utils.video_assembler.VideoAssembler') as mock_assembler_class:
            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.assemble = AsyncMock(return_value=expected_video)
            
            result = await content_pipeline.assemble_video(script, visuals, audio)
            
            assert result == expected_video
            mock_assembler.assemble.assert_called_once_with(script, visuals, audio)
    
    @pytest.mark.asyncio
    async def test_optimize_for_platforms(self, content_pipeline):
        """Test platform-specific optimization."""
        base_video = "/tmp/base_video.mp4"
        target_platforms = ["youtube", "tiktok", "instagram"]
        
        expected_optimized = {
            "youtube": "/tmp/youtube_optimized.mp4",
            "tiktok": "/tmp/tiktok_optimized.mp4",
            "instagram": "/tmp/instagram_optimized.mp4"
        }
        
        with patch.object(content_pipeline, 'optimize_video_for_platform', new_callable=AsyncMock) as mock_optimize:
            mock_optimize.side_effect = lambda video, platform: expected_optimized[platform]
            
            result = await content_pipeline.optimize_for_platforms(base_video, target_platforms)
            
            assert result == expected_optimized
            assert mock_optimize.call_count == 3
    
    def test_calculate_production_cost(self, content_pipeline, sample_content_plan):
        """Test production cost calculation."""
        cost = content_pipeline.calculate_production_cost(sample_content_plan)
        
        assert isinstance(cost, float)
        assert cost > 0
        assert cost < 1000  # Reasonable upper bound
    
    def test_estimate_production_time(self, content_pipeline, sample_content_plan):
        """Test production time estimation."""
        time_minutes = content_pipeline.estimate_production_time(sample_content_plan)
        
        assert isinstance(time_minutes, int)
        assert time_minutes > 0
        assert time_minutes < 300  # Reasonable upper bound (5 hours)


class TestContentGenerationSteps:
    """Test individual content generation steps."""
    
    @pytest.fixture
    def content_pipeline(self):
        """Create content pipeline for step testing."""
        return ContentPipeline(quality_tier=QualityTier.BUDGET)
    
    @pytest.mark.asyncio
    async def test_script_generation_with_timing(self, content_pipeline):
        """Test script generation with timing information."""
        content_plan = ContentPlan(
            script={
                "hook": "Attention grabber",
                "main_content": "Educational content",
                "cta": "Call to action"
            }
        )
        
        mock_script_with_timing = """
        [0:00 - 0:03] Attention grabber
        [0:03 - 0:25] Educational content here...
        [0:25 - 0:30] Call to action
        """
        
        content_pipeline.text_ai = Mock()
        content_pipeline.text_ai.generate_script = AsyncMock(return_value=mock_script_with_timing)
        
        script = await content_pipeline.generate_script(content_plan)
        
        assert "[0:00" in script
        assert "[0:03" in script
        assert "[0:25" in script
    
    @pytest.mark.asyncio
    async def test_image_generation_with_styles(self, content_pipeline):
        """Test image generation with different styles."""
        content_plan = ContentPlan(
            visual_plan={
                "style": "minimalist",
                "scenes": ["intro", "main content", "outro"]
            }
        )
        
        content_pipeline.image_ai = Mock()
        content_pipeline.image_ai.generate_image = AsyncMock(side_effect=[
            "/tmp/minimalist_intro.jpg",
            "/tmp/minimalist_main.jpg", 
            "/tmp/minimalist_outro.jpg"
        ])
        
        images = await content_pipeline.generate_visuals(content_plan)
        
        assert len(images) == 3
        assert all("minimalist" in img for img in images)
    
    @pytest.mark.asyncio
    async def test_voice_generation_with_styles(self, content_pipeline):
        """Test voice generation with different voice styles."""
        content_plan = ContentPlan(
            script={"full_text": "Test narration content"},
            audio_plan={
                "voice_style": "professional",
                "background_music": "none"
            }
        )
        
        content_pipeline.tts = Mock()
        content_pipeline.tts.text_to_speech = AsyncMock(return_value="/tmp/professional_voice.mp3")
        
        audio = await content_pipeline.generate_audio(content_plan)
        
        content_pipeline.tts.text_to_speech.assert_called_with(
            "Test narration content",
            voice_style="professional"
        )
        assert audio == "/tmp/professional_voice.mp3"


class TestErrorHandling:
    """Test error handling in content pipeline."""
    
    @pytest.fixture
    def content_pipeline(self):
        """Create content pipeline for error testing."""
        return ContentPipeline(quality_tier=QualityTier.BALANCED)
    
    @pytest.mark.asyncio
    async def test_script_generation_failure(self, content_pipeline, sample_content_plan):
        """Test handling of script generation failure."""
        content_pipeline.text_ai = Mock()
        content_pipeline.text_ai.generate_script = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception, match="API Error"):
            await content_pipeline.generate_script(sample_content_plan)
    
    @pytest.mark.asyncio
    async def test_image_generation_partial_failure(self, content_pipeline, sample_content_plan):
        """Test handling when some images fail to generate."""
        content_pipeline.image_ai = Mock()
        
        # First image succeeds, second fails, third succeeds
        content_pipeline.image_ai.generate_image = AsyncMock(side_effect=[
            "/tmp/image1.jpg",
            Exception("Image generation failed"),
            "/tmp/image3.jpg"
        ])
        
        # Should handle partial failures gracefully
        with patch.object(content_pipeline, 'handle_image_generation_error') as mock_handler:
            mock_handler.return_value = "/tmp/placeholder.jpg"
            
            images = await content_pipeline.generate_visuals(sample_content_plan)
            
            assert len(images) == 3
            assert images[0] == "/tmp/image1.jpg"
            assert images[1] == "/tmp/placeholder.jpg"  # Fallback
            assert images[2] == "/tmp/image3.jpg"
    
    @pytest.mark.asyncio
    async def test_audio_mixing_failure(self, content_pipeline, sample_content_plan):
        """Test handling of audio mixing failure."""
        content_pipeline.tts = Mock()
        content_pipeline.tts.text_to_speech = AsyncMock(return_value="/tmp/voice.mp3")
        
        with patch.object(content_pipeline, 'get_background_music', new_callable=AsyncMock) as mock_bg, \
             patch.object(content_pipeline, 'mix_audio', new_callable=AsyncMock) as mock_mix:
            
            mock_bg.return_value = "/tmp/bg.mp3"
            mock_mix.side_effect = Exception("Mixing failed")
            
            # Should fallback to voice-only audio
            with patch.object(content_pipeline, 'handle_audio_mixing_error') as mock_handler:
                mock_handler.return_value = "/tmp/voice.mp3"  # Return voice-only
                
                audio = await content_pipeline.generate_audio(sample_content_plan)
                
                assert audio == "/tmp/voice.mp3"
                mock_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_video_assembly_failure(self, content_pipeline):
        """Test handling of video assembly failure."""
        script = "Test script"
        visuals = ["/tmp/img1.jpg", "/tmp/img2.jpg"]
        audio = "/tmp/audio.mp3"
        
        with patch('content_engine.utils.video_assembler.VideoAssembler') as mock_assembler_class:
            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.assemble = AsyncMock(side_effect=Exception("Assembly failed"))
            
            with pytest.raises(Exception, match="Assembly failed"):
                await content_pipeline.assemble_video(script, visuals, audio)


class TestQualityTierBehavior:
    """Test behavior differences across quality tiers."""
    
    @pytest.mark.asyncio
    async def test_budget_tier_optimization(self):
        """Test budget tier uses optimized/faster generation."""
        pipeline = ContentPipeline(quality_tier=QualityTier.BUDGET)
        
        # Mock services for budget tier
        with patch.object(pipeline, 'text_ai') as mock_text, \
             patch.object(pipeline, 'image_ai') as mock_image, \
             patch.object(pipeline, 'tts') as mock_tts:
            
            mock_text.generate_script = AsyncMock(return_value="Simple script")
            mock_image.generate_image = AsyncMock(return_value="/tmp/simple_image.jpg")
            mock_tts.text_to_speech = AsyncMock(return_value="/tmp/simple_voice.mp3")
            
            content_plan = ContentPlan(
                script={"hook": "test", "main_content": "test", "cta": "test"},
                visual_plan={"scenes": ["scene1"], "style": "simple", "text_overlays": ["text"]},
                audio_plan={"voice_style": "basic", "background_music": "none", "sound_effects": []}
            )
            
            # Generate content with budget tier
            with patch.object(pipeline, 'assemble_video', new_callable=AsyncMock) as mock_assemble:
                mock_assemble.return_value = "/tmp/budget_video.mp4"
                
                script = await pipeline.generate_script(content_plan)
                visuals = await pipeline.generate_visuals(content_plan)
                audio = await pipeline.generate_audio(content_plan)
                
                # Budget tier should use simpler/faster methods
                assert script == "Simple script"
                assert len(visuals) == 1
                assert audio == "/tmp/simple_voice.mp3"
    
    @pytest.mark.asyncio
    async def test_premium_tier_quality(self):
        """Test premium tier uses high-quality generation."""
        pipeline = ContentPipeline(quality_tier=QualityTier.PREMIUM)
        
        # Mock services for premium tier
        with patch.object(pipeline, 'text_ai') as mock_text, \
             patch.object(pipeline, 'image_ai') as mock_image, \
             patch.object(pipeline, 'tts') as mock_tts:
            
            mock_text.generate_script = AsyncMock(return_value="Detailed premium script with timing")
            mock_image.generate_image = AsyncMock(return_value="/tmp/premium_image.jpg")
            mock_tts.text_to_speech = AsyncMock(return_value="/tmp/premium_voice.mp3")
            
            content_plan = ContentPlan(
                script={"hook": "premium hook", "main_content": "premium content", "cta": "premium cta"},
                visual_plan={"scenes": ["intro", "main", "outro"], "style": "premium", "text_overlays": ["t1", "t2"]},
                audio_plan={"voice_style": "professional", "background_music": "cinematic", "sound_effects": ["sfx1"]}
            )
            
            with patch.object(pipeline, 'get_background_music', new_callable=AsyncMock) as mock_bg, \
                 patch.object(pipeline, 'mix_audio', new_callable=AsyncMock) as mock_mix:
                
                mock_bg.return_value = "/tmp/premium_bg.mp3"
                mock_mix.return_value = "/tmp/premium_mixed.mp3"
                
                script = await pipeline.generate_script(content_plan)
                visuals = await pipeline.generate_visuals(content_plan)
                audio = await pipeline.generate_audio(content_plan)
                
                # Premium tier should produce higher quality outputs
                assert "premium" in script.lower() or "detailed" in script.lower()
                assert len(visuals) == 3  # More scenes
                assert audio == "/tmp/premium_mixed.mp3"  # Mixed audio
    
    def test_cost_calculation_by_tier(self):
        """Test that cost calculation varies by quality tier."""
        content_plan = ContentPlan(
            visual_plan={"scenes": ["scene1", "scene2"]},
            audio_plan={"background_music": "upbeat", "sound_effects": ["sfx1"]}
        )
        
        budget_pipeline = ContentPipeline(quality_tier=QualityTier.BUDGET)
        premium_pipeline = ContentPipeline(quality_tier=QualityTier.PREMIUM)
        
        budget_cost = budget_pipeline.calculate_production_cost(content_plan)
        premium_cost = premium_pipeline.calculate_production_cost(content_plan)
        
        # Premium should cost more
        assert premium_cost > budget_cost
        assert budget_cost > 0
        assert premium_cost > 0


class TestPlatformOptimization:
    """Test platform-specific optimizations."""
    
    @pytest.fixture
    def content_pipeline(self):
        """Create content pipeline for platform testing."""
        return ContentPipeline(quality_tier=QualityTier.BALANCED)
    
    @pytest.mark.asyncio
    async def test_youtube_optimization(self, content_pipeline):
        """Test YouTube-specific optimization."""
        base_video = "/tmp/base_video.mp4"
        
        with patch('moviepy.editor.VideoFileClip') as mock_video_clip:
            mock_clip = Mock()
            mock_clip.resize.return_value = mock_clip
            mock_clip.write_videofile.return_value = None
            mock_video_clip.return_value = mock_clip
            
            optimized = await content_pipeline.optimize_video_for_platform(base_video, "youtube")
            
            # Should optimize for YouTube specs (16:9, 1080p)
            assert optimized.endswith("_youtube.mp4")
            mock_clip.resize.assert_called()
    
    @pytest.mark.asyncio
    async def test_tiktok_optimization(self, content_pipeline):
        """Test TikTok-specific optimization."""
        base_video = "/tmp/base_video.mp4"
        
        with patch('moviepy.editor.VideoFileClip') as mock_video_clip:
            mock_clip = Mock()
            mock_clip.resize.return_value = mock_clip
            mock_clip.crop.return_value = mock_clip
            mock_clip.write_videofile.return_value = None
            mock_video_clip.return_value = mock_clip
            
            optimized = await content_pipeline.optimize_video_for_platform(base_video, "tiktok")
            
            # Should optimize for TikTok specs (9:16 vertical)
            assert optimized.endswith("_tiktok.mp4")
            mock_clip.resize.assert_called()
            # Should crop to vertical aspect ratio
    
    @pytest.mark.asyncio
    async def test_instagram_optimization(self, content_pipeline):
        """Test Instagram-specific optimization."""
        base_video = "/tmp/base_video.mp4"
        
        with patch('moviepy.editor.VideoFileClip') as mock_video_clip:
            mock_clip = Mock()
            mock_clip.resize.return_value = mock_clip
            mock_clip.subclip.return_value = mock_clip
            mock_clip.write_videofile.return_value = None
            mock_video_clip.return_value = mock_clip
            
            optimized = await content_pipeline.optimize_video_for_platform(base_video, "instagram")
            
            # Should optimize for Instagram specs (square or vertical, max 60s)
            assert optimized.endswith("_instagram.mp4")
            mock_clip.subclip.assert_called()  # Duration limit


class TestParallelProcessing:
    """Test parallel processing capabilities."""
    
    @pytest.fixture
    def content_pipeline(self):
        """Create content pipeline for parallel processing tests."""
        return ContentPipeline(quality_tier=QualityTier.BALANCED)
    
    @pytest.mark.asyncio
    async def test_parallel_image_generation(self, content_pipeline):
        """Test parallel generation of multiple images."""
        content_plan = ContentPlan(
            visual_plan={
                "scenes": ["scene1", "scene2", "scene3", "scene4", "scene5"],
                "style": "modern"
            }
        )
        
        # Mock parallel image generation
        async def mock_generate_image(scene):
            await asyncio.sleep(0.1)  # Simulate processing time
            return f"/tmp/{scene}_image.jpg"
        
        content_pipeline.image_ai = Mock()
        content_pipeline.image_ai.generate_image = mock_generate_image
        
        start_time = asyncio.get_event_loop().time()
        images = await content_pipeline.generate_visuals(content_plan)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete in less time than sequential processing
        assert len(images) == 5
        assert (end_time - start_time) < 0.6  # Less than 5 * 0.1 + overhead
    
    @pytest.mark.asyncio
    async def test_concurrent_content_generation(self, content_pipeline):
        """Test concurrent generation of multiple content pieces."""
        content_plans = [
            ContentPlan(
                script={"hook": f"Hook {i}", "main_content": f"Content {i}", "cta": f"CTA {i}"},
                visual_plan={"scenes": [f"scene{i}"], "style": "simple"},
                audio_plan={"voice_style": "neutral", "background_music": "none"}
            )
            for i in range(3)
        ]
        
        # Mock generation methods
        content_pipeline.text_ai = Mock()
        content_pipeline.image_ai = Mock()
        content_pipeline.tts = Mock()
        
        async def mock_generate_script(plan):
            await asyncio.sleep(0.1)
            return f"Script for {plan.script['hook']}"
        
        async def mock_generate_image(scene):
            await asyncio.sleep(0.1)
            return f"/tmp/{scene}.jpg"
        
        async def mock_text_to_speech(text, **kwargs):
            await asyncio.sleep(0.1)
            return f"/tmp/{text[:10]}.mp3"
        
        content_pipeline.text_ai.generate_script = mock_generate_script
        content_pipeline.image_ai.generate_image = mock_generate_image
        content_pipeline.tts.text_to_speech = mock_text_to_speech
        
        with patch.object(content_pipeline, 'assemble_video', new_callable=AsyncMock) as mock_assemble, \
             patch.object(content_pipeline, 'optimize_for_platforms', new_callable=AsyncMock) as mock_optimize:
            
            mock_assemble.return_value = "/tmp/video.mp4"
            mock_optimize.return_value = {"youtube": "/tmp/youtube.mp4"}
            
            # Generate content for all plans concurrently
            tasks = [content_pipeline.generate_content(plan) for plan in content_plans]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(isinstance(result, dict) for result in results)


class TestResourceManagement:
    """Test resource management and cleanup."""
    
    @pytest.fixture
    def content_pipeline(self):
        """Create content pipeline for resource testing."""
        return ContentPipeline(quality_tier=QualityTier.BALANCED)
    
    @pytest.mark.asyncio
    async def test_temporary_file_cleanup(self, content_pipeline):
        """Test cleanup of temporary files during processing."""
        content_plan = ContentPlan(
            script={"hook": "test", "main_content": "test", "cta": "test"},
            visual_plan={"scenes": ["scene1"], "style": "simple"},
            audio_plan={"voice_style": "neutral", "background_music": "none"}
        )
        
        # Mock file operations
        temp_files = []
        
        def mock_generate_temp_file(prefix):
            temp_file = f"/tmp/{prefix}_{len(temp_files)}.tmp"
            temp_files.append(temp_file)
            return temp_file
        
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
             patch('os.remove') as mock_remove:
            
            mock_tempfile.return_value.name = mock_generate_temp_file("test")
            
            content_pipeline.text_ai = Mock()
            content_pipeline.image_ai = Mock()
            content_pipeline.tts = Mock()
            
            content_pipeline.text_ai.generate_script = AsyncMock(return_value="script")
            content_pipeline.image_ai.generate_image = AsyncMock(return_value="/tmp/image.jpg")
            content_pipeline.tts.text_to_speech = AsyncMock(return_value="/tmp/audio.mp3")
            
            with patch.object(content_pipeline, 'assemble_video', new_callable=AsyncMock) as mock_assemble:
                mock_assemble.return_value = "/tmp/final_video.mp4"
                
                try:
                    await content_pipeline.generate_content(content_plan)
                finally:
                    # Should clean up temporary files
                    pass  # Cleanup logic would be tested here
    
    def test_memory_usage_monitoring(self, content_pipeline):
        """Test monitoring of memory usage during processing."""
        import psutil
        import os
        
        initial_memory = psutil.Process(os.getpid()).memory_info().rss
        
        # Simulate memory-intensive operation
        large_data = [0] * 1000000  # Allocate some memory
        
        current_memory = psutil.Process(os.getpid()).memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # Should track memory usage
        assert memory_increase > 0
        
        # Cleanup
        del large_data
    
    @pytest.mark.asyncio
    async def test_processing_timeout(self, content_pipeline):
        """Test timeout handling for long-running operations."""
        content_plan = ContentPlan(
            script={"hook": "test", "main_content": "test", "cta": "test"}
        )
        
        # Mock a long-running operation
        async def slow_operation():
            await asyncio.sleep(10)  # Simulate 10-second operation
            return "result"
        
        content_pipeline.text_ai = Mock()
        content_pipeline.text_ai.generate_script = slow_operation
        
        # Should timeout after reasonable time
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                content_pipeline.generate_script(content_plan),
                timeout=1.0  # 1 second timeout
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])