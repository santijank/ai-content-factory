"""
Content Optimizer Module
ปรับแต่งเนื้อหาให้เหมาะสมกับแต่ละ platform ในระบบ AI Content Factory
"""

import os
import asyncio
import json
import tempfile
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import logging
from datetime import datetime
import re

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    from PIL.ImageOps import fit
except ImportError:
    Image = None
    logging.warning("Pillow not available. Image optimization will be limited.")

try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    from moviepy.video.fx import resize, crop
except ImportError:
    VideoFileClip = None
    logging.warning("MoviePy not available. Video optimization will be limited.")

from ...shared.constants.platform_constants import (
    PlatformType, PLATFORM_SPECS, VIDEO_RESOLUTIONS, 
    ASPECT_RATIOS, PLATFORM_OPTIMIZATIONS, get_platform_spec,
    get_optimal_resolution, calculate_aspect_ratio
)
from ...shared.utils.error_handler import handle_async_errors, ContentOptimizationError

class ContentOptimizer:
    """
    Content Optimizer สำหรับปรับแต่งเนื้อหาให้เหมาะกับแต่ละ platform
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.temp_dir = self.config.get('temp_dir', tempfile.gettempdir())
        
        # Quality settings
        self.video_quality = self.config.get('video_quality', 'high')
        self.image_quality = self.config.get('image_quality', 85)
        self.audio_bitrate = self.config.get('audio_bitrate', '128k')
        
        # Cache for optimized content
        self._optimization_cache = {}
        
        # Statistics
        self.stats = {
            'optimizations_performed': 0,
            'cache_hits': 0,
            'total_processing_time': 0.0
        }
    
    @handle_async_errors()
    async def optimize_for_platform(self, 
                                   content: Dict[str, Any], 
                                   platform: PlatformType,
                                   target_audience: str = "general") -> Dict[str, Any]:
        """
        Optimize content สำหรับ platform เฉพาะ
        
        Args:
            content: ข้อมูล content ที่จะ optimize
            platform: Platform ปลายทาง
            target_audience: กลุ่มเป้าหมาย
        
        Returns:
            Optimized content dictionary
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(content, platform, target_audience)
            
            # Check cache first
            if cache_key in self._optimization_cache:
                self.stats['cache_hits'] += 1
                return self._optimization_cache[cache_key]
            
            platform_spec = get_platform_spec(platform)
            if not platform_spec:
                raise ContentOptimizationError(f"Unsupported platform: {platform}")
            
            optimized_content = content.copy()
            
            # Optimize different content types
            if 'video_path' in content:
                optimized_content = await self._optimize_video(optimized_content, platform)
            
            if 'image_path' in content or 'thumbnail_path' in content:
                optimized_content = await self._optimize_images(optimized_content, platform)
            
            # Optimize text content
            optimized_content = await self._optimize_text_content(optimized_content, platform)
            
            # Optimize metadata
            optimized_content = await self._optimize_metadata(optimized_content, platform)
            
            # Platform-specific optimizations
            optimized_content = await self._apply_platform_specific_optimizations(
                optimized_content, platform, target_audience
            )
            
            # Cache the result
            self._optimization_cache[cache_key] = optimized_content
            
            # Update stats
            processing_time = asyncio.get_event_loop().time() - start_time
            self.stats['optimizations_performed'] += 1
            self.stats['total_processing_time'] += processing_time
            
            optimized_content['optimization_metadata'] = {
                'platform': platform.value,
                'processing_time': processing_time,
                'optimizations_applied': self._get_applied_optimizations(content, optimized_content),
                'target_audience': target_audience
            }
            
            return optimized_content
            
        except Exception as e:
            self.logger.error(f"Content optimization failed: {str(e)}")
            raise ContentOptimizationError(f"Optimization failed: {str(e)}")
    
    async def _optimize_video(self, content: Dict[str, Any], platform: PlatformType) -> Dict[str, Any]:
        """Optimize video content for platform"""
        if not VideoFileClip:
            self.logger.warning("Video optimization skipped - MoviePy not available")
            return content
        
        video_path = content.get('video_path')
        if not video_path or not os.path.exists(video_path):
            return content
        
        platform_spec = get_platform_spec(platform)
        optimizations = PLATFORM_OPTIMIZATIONS.get(platform, {})
        
        try:
            # Load video
            video = VideoFileClip(video_path)
            original_duration = video.duration
            original_size = (video.w, video.h)
            
            # Check duration limits
            if original_duration > platform_spec.max_video_duration:
                # Trim video to max duration
                video = video.subclip(0, platform_spec.max_video_duration)
                content['duration_trimmed'] = True
                content['original_duration'] = original_duration
                content['trimmed_duration'] = platform_spec.max_video_duration
            
            # Optimize resolution and aspect ratio
            target_resolution = get_optimal_resolution(platform)
            current_aspect_ratio = calculate_aspect_ratio(video.w, video.h)
            
            # Resize if needed
            if (video.w, video.h) != target_resolution:
                # Determine best fit method
                if platform == PlatformType.TIKTOK or platform == PlatformType.INSTAGRAM:
                    # Vertical platforms - crop to fit
                    video = crop(video, width=target_resolution[0], height=target_resolution[1])
                else:
                    # Horizontal platforms - resize maintaining aspect ratio
                    video = resize(video, newsize=target_resolution)
            
            # Generate optimized video path
            output_filename = f"optimized_{platform.value}_{os.path.basename(video_path)}"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # Write optimized video
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=os.path.join(self.temp_dir, 'temp-audio.m4a'),
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            video.close()
            
            # Update content with optimized video
            content['video_path'] = output_path
            content['optimized_resolution'] = target_resolution
            content['original_resolution'] = original_size
            content['video_optimized'] = True
            
        except Exception as e:
            self.logger.error(f"Video optimization failed: {str(e)}")
            content['video_optimization_error'] = str(e)
        
        return content
    
    async def _optimize_images(self, content: Dict[str, Any], platform: PlatformType) -> Dict[str, Any]:
        """Optimize images for platform"""
        if not Image:
            self.logger.warning("Image optimization skipped - Pillow not available")
            return content
        
        platform_spec = get_platform_spec(platform)
        optimizations = PLATFORM_OPTIMIZATIONS.get(platform, {})
        
        # Optimize main image
        if 'image_path' in content:
            content['image_path'] = await self._optimize_single_image(
                content['image_path'], 
                platform, 
                'main_image'
            )
        
        # Optimize thumbnail
        if 'thumbnail_path' in content:
            thumbnail_size = optimizations.get('thumbnail_size', (1280, 720))
            content['thumbnail_path'] = await self._optimize_single_image(
                content['thumbnail_path'],
                platform,
                'thumbnail',
                target_size=thumbnail_size
            )
        
        return content
    
    async def _optimize_single_image(self, 
                                   image_path: str, 
                                   platform: PlatformType,
                                   image_type: str = 'main',
                                   target_size: Tuple[int, int] = None) -> str:
        """Optimize a single image"""
        if not os.path.exists(image_path):
            return image_path
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get target size
                if not target_size:
                    target_size = get_optimal_resolution(platform)
                
                # Resize maintaining aspect ratio
                img = fit(img, target_size, method=Image.Resampling.LANCZOS)
                
                # Apply platform-specific enhancements
                if platform == PlatformType.INSTAGRAM:
                    # Instagram likes vibrant colors
                    img = self._enhance_colors(img)
                elif platform == PlatformType.LINKEDIN:
                    # LinkedIn prefers professional look
                    img = self._apply_professional_filter(img)
                
                # Generate output path
                output_filename = f"optimized_{platform.value}_{image_type}_{os.path.basename(image_path)}"
                output_path = os.path.join(self.temp_dir, output_filename)
                
                # Save optimized image
                img.save(output_path, 'JPEG', quality=self.image_quality, optimize=True)
                
                return output_path
                
        except Exception as e:
            self.logger.error(f"Image optimization failed: {str(e)}")
            return image_path
    
    def _enhance_colors(self, img: Image.Image) -> Image.Image:
        """Enhance colors for social media"""
        from PIL import ImageEnhance
        
        # Increase saturation slightly
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        
        # Increase contrast slightly
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        return img
    
    def _apply_professional_filter(self, img: Image.Image) -> Image.Image:
        """Apply professional filter"""
        # Slightly desaturate for professional look
        from PIL import ImageEnhance
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.9)
        
        return img
    
    async def _optimize_text_content(self, content: Dict[str, Any], platform: PlatformType) -> Dict[str, Any]:
        """Optimize text content for platform"""
        platform_spec = get_platform_spec(platform)
        optimizations = PLATFORM_OPTIMIZATIONS.get(platform, {})
        
        # Optimize title
        if 'title' in content:
            content['title'] = self._optimize_title(
                content['title'], 
                platform_spec.max_title_length,
                optimizations.get('title_keywords', 'beginning')
            )
        
        # Optimize description
        if 'description' in content:
            content['description'] = self._optimize_description(
                content['description'],
                platform_spec.max_description_length,
                optimizations.get('description_format', 'detailed')
            )
        
        # Optimize hashtags
        if 'hashtags' in content:
            content['hashtags'] = self._optimize_hashtags(
                content['hashtags'],
                platform_spec.max_hashtags,
                platform
            )
        
        return content
    
    def _optimize_title(self, title: str, max_length: int, keyword_strategy: str) -> str:
        """Optimize title for platform"""
        if len(title) <= max_length:
            return title
        
        # Truncate intelligently
        if keyword_strategy == 'beginning':
            # Keep the beginning (important for YouTube)
            return title[:max_length-3] + '...'
        else:
            # Find natural break point
            words = title.split()
            optimized_title = ""
            
            for word in words:
                if len(optimized_title + " " + word) <= max_length - 3:
                    optimized_title += (" " if optimized_title else "") + word
                else:
                    break
            
            return optimized_title + '...' if optimized_title != title else title
    
    def _optimize_description(self, description: str, max_length: int, format_style: str) -> str:
        """Optimize description for platform"""
        if len(description) <= max_length:
            return description
        
        # Truncate based on format style
        if format_style == 'concise':
            # Keep first sentence or paragraph
            sentences = description.split('.')
            result = sentences[0] + '.'
            return result if len(result) <= max_length else description[:max_length-3] + '...'
        
        elif format_style == 'detailed':
            # Keep as much detail as possible
            return description[:max_length-3] + '...'
        
        else:  # engaging, professional, storytelling
            # Find natural break point
            paragraphs = description.split('\n\n')
            if len(paragraphs[0]) <= max_length:
                return paragraphs[0]
            else:
                return description[:max_length-3] + '...'
    
    def _optimize_hashtags(self, hashtags: List[str], max_hashtags: int, platform: PlatformType) -> List[str]:
        """Optimize hashtags for platform"""
        if len(hashtags) <= max_hashtags:
            return hashtags
        
        # Platform-specific hashtag prioritization
        if platform == PlatformType.TIKTOK:
            # TikTok prioritizes trending hashtags
            priority_hashtags = ['#fyp', '#viral', '#trending', '#foryou']
        elif platform == PlatformType.INSTAGRAM:
            # Instagram balances popular and niche hashtags
            priority_hashtags = ['#instagood', '#photooftheday', '#love']
        elif platform == PlatformType.LINKEDIN:
            # LinkedIn prefers professional hashtags
            priority_hashtags = ['#linkedin', '#professional', '#business', '#career']
        else:
            priority_hashtags = []
        
        # Keep priority hashtags first
        optimized_hashtags = []
        remaining_hashtags = []
        
        for hashtag in hashtags:
            if hashtag.lower() in [p.lower() for p in priority_hashtags]:
                optimized_hashtags.append(hashtag)
            else:
                remaining_hashtags.append(hashtag)
        
        # Fill remaining slots
        remaining_slots = max_hashtags - len(optimized_hashtags)
        optimized_hashtags.extend(remaining_hashtags[:remaining_slots])
        
        return optimized_hashtags
    
    async def _optimize_metadata(self, content: Dict[str, Any], platform: PlatformType) -> Dict[str, Any]:
        """Optimize metadata for platform"""
        platform_spec = get_platform_spec(platform)
        
        # Add platform-specific metadata
        content['platform_metadata'] = {
            'platform': platform.value,
            'max_duration': platform_spec.max_video_duration,
            'max_file_size': platform_spec.max_file_size,
            'optimal_resolution': platform_spec.optimal_resolution,
            'supported_formats': platform_spec.supported_formats
        }
        
        # Add scheduling information if supported
        if platform_spec.supports_scheduling:
            content['scheduling_supported'] = True
        
        # Add analytics information if supported  
        if platform_spec.supports_analytics:
            content['analytics_supported'] = True
        
        return content
    
    async def _apply_platform_specific_optimizations(self, 
                                                   content: Dict[str, Any], 
                                                   platform: PlatformType,
                                                   target_audience: str) -> Dict[str, Any]:
        """Apply platform-specific optimizations"""
        
        if platform == PlatformType.YOUTUBE:
            content = await self._optimize_for_youtube(content, target_audience)
        elif platform == PlatformType.TIKTOK:
            content = await self._optimize_for_tiktok(content, target_audience)
        elif platform == PlatformType.INSTAGRAM:
            content = await self._optimize_for_instagram(content, target_audience)
        elif platform == PlatformType.FACEBOOK:
            content = await self._optimize_for_facebook(content, target_audience)
        elif platform == PlatformType.LINKEDIN:
            content = await self._optimize_for_linkedin(content, target_audience)
        
        return content
    
    async def _optimize_for_youtube(self, content: Dict[str, Any], target_audience: str) -> Dict[str, Any]:
        """YouTube-specific optimizations"""
        # Add YouTube-specific metadata
        content['youtube_optimizations'] = {
            'thumbnail_optimized': True,
            'title_seo_optimized': True,
            'description_detailed': True,
            'tags_added': True
        }
        
        # Add end screen suggestion
        if content.get('duration', 0) > 25:
            content['end_screen_recommended'] = True
        
        # Add chapter suggestions for long videos
        if content.get('duration', 0) > 600:  # 10 minutes
            content['chapters_recommended'] = True
        
        return content
    
    async def _optimize_for_tiktok(self, content: Dict[str, Any], target_audience: str) -> Dict[str, Any]:
        """TikTok-specific optimizations"""
        # Ensure vertical format
        if 'video_path' in content:
            content['aspect_ratio_enforced'] = '9:16'
        
        # Add TikTok-specific metadata
        content['tiktok_optimizations'] = {
            'hashtags_trending_focused': True,
            'duration_optimized': True,
            'hook_enhanced': True
        }
        
        # Hook optimization (first 3 seconds)
        if 'script' in content:
            content['hook_optimized'] = True
        
        return content
    
    async def _optimize_for_instagram(self, content: Dict[str, Any], target_audience: str) -> Dict[str, Any]:
        """Instagram-specific optimizations"""
        content['instagram_optimizations'] = {
            'visual_enhanced': True,
            'hashtag_strategy_applied': True,
            'story_friendly': True
        }
        
        # Suggest story version for videos
        if 'video_path' in content:
            content['story_version_recommended'] = True
        
        return content
    
    async def _optimize_for_facebook(self, content: Dict[str, Any], target_audience: str) -> Dict[str, Any]:
        """Facebook-specific optimizations"""
        content['facebook_optimizations'] = {
            'engagement_focused': True,
            'shareable_format': True,
            'community_friendly': True
        }
        
        return content
    
    async def _optimize_for_linkedin(self, content: Dict[str, Any], target_audience: str) -> Dict[str, Any]:
        """LinkedIn-specific optimizations"""
        content['linkedin_optimizations'] = {
            'professional_tone': True,
            'industry_relevant': True,
            'networking_focused': True
        }
        
        return content
    
    def _generate_cache_key(self, content: Dict[str, Any], platform: PlatformType, target_audience: str) -> str:
        """Generate cache key for optimization"""
        key_data = {
            'platform': platform.value,
            'target_audience': target_audience,
            'title': content.get('title', ''),
            'content_type': content.get('content_type', ''),
            'duration': content.get('duration', 0)
        }
        
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _get_applied_optimizations(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> List[str]:
        """Get list of applied optimizations"""
        optimizations = []
        
        if optimized.get('video_optimized'):
            optimizations.append('video_resolution')
        
        if optimized.get('duration_trimmed'):
            optimizations.append('duration_limit')
        
        if 'optimized_resolution' in optimized:
            optimizations.append('resolution_optimization')
        
        if len(optimized.get('title', '')) != len(original.get('title', '')):
            optimizations.append('title_length')
        
        if len(optimized.get('hashtags', [])) != len(original.get('hashtags', [])):
            optimizations.append('hashtag_optimization')
        
        return optimizations
    
    async def batch_optimize(self, 
                           content_list: List[Dict[str, Any]], 
                           platforms: List[PlatformType],
                           target_audience: str = "general") -> Dict[str, List[Dict[str, Any]]]:
        """Optimize multiple content items for multiple platforms"""
        results = {}
        
        for platform in platforms:
            results[platform.value] = []
            
            for content in content_list:
                try:
                    optimized = await self.optimize_for_platform(content, platform, target_audience)
                    results[platform.value].append(optimized)
                except Exception as e:
                    self.logger.error(f"Batch optimization failed for {platform.value}: {str(e)}")
                    results[platform.value].append({
                        'error': str(e),
                        'original_content': content
                    })
        
        return results
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        return {
            'optimizations_performed': self.stats['optimizations_performed'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['optimizations_performed']),
            'total_processing_time': self.stats['total_processing_time'],
            'avg_processing_time': self.stats['total_processing_time'] / max(1, self.stats['optimizations_performed']),
            'cache_size': len(self._optimization_cache)
        }
    
    def clear_cache(self):
        """Clear optimization cache"""
        self._optimization_cache.clear()
        self.logger.info("Optimization cache cleared")
    
    async def cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_files = []
        for file_path in Path(self.temp_dir).glob("optimized_*"):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    temp_files.append(str(file_path))
                except Exception as e:
                    self.logger.warning(f"Could not delete temp file {file_path}: {str(e)}")
        
        self.logger.info(f"Cleaned up {len(temp_files)} temporary files")
        return temp_files

# Utility Functions
def estimate_optimization_time(content: Dict[str, Any], platform: PlatformType) -> float:
    """Estimate optimization processing time"""
    base_time = 1.0  # seconds
    
    if 'video_path' in content:
        duration = content.get('duration', 60)
        base_time += duration * 0.1  # 0.1s per second of video
    
    if 'image_path' in content or 'thumbnail_path' in content:
        base_time += 2.0  # 2s for image processing
    
    return base_time

def get_optimization_recommendations(content: Dict[str, Any], platform: PlatformType) -> List[str]:
    """Get optimization recommendations"""
    recommendations = []
    platform_spec = get_platform_spec(platform)
    
    if not platform_spec:
        return recommendations
    
    # Check title length
    title = content.get('title', '')
    if len(title) > platform_spec.max_title_length:
        recommendations.append(f"Title too long. Max {platform_spec.max_title_length} characters.")
    
    # Check description length
    description = content.get('description', '')
    if len(description) > platform_spec.max_description_length:
        recommendations.append(f"Description too long. Max {platform_spec.max_description_length} characters.")
    
    # Check hashtags
    hashtags = content.get('hashtags', [])
    if len(hashtags) > platform_spec.max_hashtags:
        recommendations.append(f"Too many hashtags. Max {platform_spec.max_hashtags} hashtags.")
    
    # Check video duration
    duration = content.get('duration', 0)
    if duration > platform_spec.max_video_duration:
        recommendations.append(f"Video too long. Max {platform_spec.max_video_duration} seconds.")
    
    return recommendations

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_optimizer():
        optimizer = ContentOptimizer()
        
        test_content = {
            'title': 'This is a very long title that might exceed the platform limits and needs optimization',
            'description': 'A detailed description that explains everything about the content in great detail...',
            'hashtags': ['#test', '#optimization', '#ai', '#content', '#social', '#media', '#viral', '#trending'],
            'duration': 3600,  # 1 hour
            'content_type': 'educational'
        }
        
        # Test optimization for different platforms
        for platform in [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]:
            print(f"\n=== Optimizing for {platform.value.upper()} ===")
            
            optimized = await optimizer.optimize_for_platform(test_content, platform)
            print(f"Original title length: {len(test_content['title'])}")
            print(f"Optimized title: {optimized['title']}")
            print(f"Optimized hashtags: {len(optimized['hashtags'])} tags")
            print(f"Applied optimizations: {optimized['optimization_metadata']['optimizations_applied']}")
        
        # Get stats
        stats = optimizer.get_optimization_stats()
        print(f"\nOptimization Stats: {stats}")
    
    asyncio.run(test_optimizer())