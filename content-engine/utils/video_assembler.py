"""
Video Assembler Module
รวมไฟล์ต่างๆ เป็นวิดีโอสมบูรณ์และปรับให้เหมาะกับแต่ละ platform
"""

import os
import asyncio
import json
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

# Video processing libraries
try:
    from moviepy.editor import (
        VideoFileClip, ImageClip, AudioFileClip, 
        CompositeVideoClip, CompositeAudioClip,
        TextClip, concatenate_videoclips
    )
except ImportError:
    logging.warning("MoviePy not installed. Video assembly will be limited.")

from ..models.quality_tier import QualityTier
from ..models.content_plan import ContentPlan, VideoSpec

logger = logging.getLogger(__name__)

class PlatformSpecs:
    """Platform-specific video specifications"""
    
    YOUTUBE = {
        "max_duration": 900,  # 15 minutes for shorts
        "aspect_ratio": (16, 9),
        "resolution": (1920, 1080),
        "fps": 30,
        "bitrate": "8M",
        "audio_bitrate": "192k",
        "format": "mp4"
    }
    
    TIKTOK = {
        "max_duration": 180,  # 3 minutes
        "aspect_ratio": (9, 16),
        "resolution": (1080, 1920),
        "fps": 30,
        "bitrate": "16M",
        "audio_bitrate": "128k",
        "format": "mp4"
    }
    
    INSTAGRAM = {
        "max_duration": 90,  # 90 seconds for reels
        "aspect_ratio": (9, 16),
        "resolution": (1080, 1920),
        "fps": 30,
        "bitrate": "3.5M",
        "audio_bitrate": "128k",
        "format": "mp4"
    }
    
    FACEBOOK = {
        "max_duration": 240,  # 4 minutes
        "aspect_ratio": (16, 9),
        "resolution": (1280, 720),
        "fps": 30,
        "bitrate": "4M",
        "audio_bitrate": "128k",
        "format": "mp4"
    }

class VideoAssembler:
    """Main video assembly engine"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.platform_specs = {
            "youtube": PlatformSpecs.YOUTUBE,
            "tiktok": PlatformSpecs.TIKTOK,
            "instagram": PlatformSpecs.INSTAGRAM,
            "facebook": PlatformSpecs.FACEBOOK
        }
        
    async def assemble_video(
        self, 
        content_plan: ContentPlan,
        images: List[str],
        audio_file: str,
        target_platforms: List[str]
    ) -> Dict[str, str]:
        """
        Assemble final video from components
        
        Args:
            content_plan: Content plan with video specifications
            images: List of image file paths
            audio_file: Audio file path
            target_platforms: List of target platforms
            
        Returns:
            Dict mapping platform names to video file paths
        """
        try:
            logger.info(f"Starting video assembly for platforms: {target_platforms}")
            
            # Create base video
            base_video = await self._create_base_video(
                content_plan, images, audio_file
            )
            
            # Generate platform-specific versions
            platform_videos = {}
            for platform in target_platforms:
                if platform.lower() in self.platform_specs:
                    video_path = await self._optimize_for_platform(
                        base_video, platform.lower(), content_plan
                    )
                    platform_videos[platform] = video_path
                else:
                    logger.warning(f"Unknown platform: {platform}")
                    
            return platform_videos
            
        except Exception as e:
            logger.error(f"Error assembling video: {str(e)}")
            raise

    async def _create_base_video(
        self, 
        content_plan: ContentPlan, 
        images: List[str], 
        audio_file: str
    ) -> VideoFileClip:
        """Create base video from images and audio"""
        
        try:
            # Load audio to get duration
            audio = AudioFileClip(audio_file)
            total_duration = audio.duration
            
            # Calculate timing for each image
            image_duration = total_duration / len(images) if images else total_duration
            
            # Create video clips from images
            video_clips = []
            current_time = 0
            
            for i, image_path in enumerate(images):
                # Create image clip
                img_clip = ImageClip(image_path, duration=image_duration)
                img_clip = img_clip.set_start(current_time)
                
                # Add text overlays if specified
                if content_plan.visual_plan and content_plan.visual_plan.text_overlays:
                    if i < len(content_plan.visual_plan.text_overlays):
                        text_overlay = self._create_text_overlay(
                            content_plan.visual_plan.text_overlays[i],
                            image_duration,
                            img_clip.size
                        )
                        img_clip = CompositeVideoClip([img_clip, text_overlay])
                
                video_clips.append(img_clip)
                current_time += image_duration
            
            # Concatenate all clips
            if video_clips:
                video = concatenate_videoclips(video_clips, method="compose")
            else:
                # Create blank video if no images
                video = ImageClip(
                    self._create_blank_image(), 
                    duration=total_duration
                )
            
            # Add audio
            video = video.set_audio(audio)
            
            return video
            
        except Exception as e:
            logger.error(f"Error creating base video: {str(e)}")
            raise

    def _create_text_overlay(
        self, 
        text: str, 
        duration: float, 
        video_size: Tuple[int, int]
    ) -> TextClip:
        """Create text overlay for video"""
        
        try:
            # Calculate font size based on video resolution
            font_size = max(20, min(video_size) // 20)
            
            # Create text clip
            text_clip = TextClip(
                text,
                fontsize=font_size,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(video_size[0] * 0.8, None)  # 80% of video width
            )
            
            # Position text at bottom center
            text_clip = text_clip.set_position(('center', 'bottom')).set_duration(duration)
            
            return text_clip
            
        except Exception as e:
            logger.error(f"Error creating text overlay: {str(e)}")
            # Return empty clip if text creation fails
            return TextClip("", duration=duration).set_opacity(0)

    async def _optimize_for_platform(
        self, 
        video: VideoFileClip, 
        platform: str, 
        content_plan: ContentPlan
    ) -> str:
        """Optimize video for specific platform"""
        
        try:
            specs = self.platform_specs[platform]
            
            # Resize video to platform specifications
            target_resolution = specs["resolution"]
            target_ratio = specs["aspect_ratio"]
            
            # Calculate new size maintaining aspect ratio
            video_ratio = video.w / video.h
            platform_ratio = target_ratio[0] / target_ratio[1]
            
            if video_ratio > platform_ratio:
                # Video is wider, fit to height
                new_height = target_resolution[1]
                new_width = int(new_height * video_ratio)
            else:
                # Video is taller, fit to width
                new_width = target_resolution[0]
                new_height = int(new_width / video_ratio)
            
            # Resize video
            resized_video = video.resize((new_width, new_height))
            
            # Crop or pad to exact platform size
            final_video = self._crop_or_pad_video(
                resized_video, target_resolution
            )
            
            # Limit duration if needed
            if final_video.duration > specs["max_duration"]:
                final_video = final_video.subclip(0, specs["max_duration"])
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{platform}_{timestamp}.{specs['format']}"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # Write video file
            await self._write_video_async(
                final_video, output_path, specs
            )
            
            # Clean up
            final_video.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error optimizing video for {platform}: {str(e)}")
            raise

    def _crop_or_pad_video(
        self, 
        video: VideoFileClip, 
        target_size: Tuple[int, int]
    ) -> VideoFileClip:
        """Crop or pad video to exact target size"""
        
        current_w, current_h = video.w, video.h
        target_w, target_h = target_size
        
        if current_w == target_w and current_h == target_h:
            return video
        
        if current_w > target_w or current_h > target_h:
            # Need to crop
            x_center = current_w / 2
            y_center = current_h / 2
            
            x1 = max(0, x_center - target_w / 2)
            y1 = max(0, y_center - target_h / 2)
            x2 = min(current_w, x1 + target_w)
            y2 = min(current_h, y1 + target_h)
            
            return video.crop(x1=x1, y1=y1, x2=x2, y2=y2)
        else:
            # Need to pad (center video on colored background)
            from moviepy.editor import ColorClip
            
            background = ColorClip(
                size=target_size, 
                color=(0, 0, 0),  # Black background
                duration=video.duration
            )
            
            # Center the video on the background
            video_centered = video.set_position('center')
            
            return CompositeVideoClip([background, video_centered])

    async def _write_video_async(
        self, 
        video: VideoFileClip, 
        output_path: str, 
        specs: Dict[str, Any]
    ) -> None:
        """Write video file asynchronously"""
        
        def write_video():
            video.write_videofile(
                output_path,
                fps=specs["fps"],
                bitrate=specs["bitrate"],
                audio_bitrate=specs["audio_bitrate"],
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=f"{output_path}_temp_audio.m4a",
                remove_temp=True,
                verbose=False,
                logger=None
            )
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, write_video)

    def _create_blank_image(self, size: Tuple[int, int] = (1920, 1080)) -> str:
        """Create a blank image file"""
        
        try:
            from PIL import Image
            
            # Create blank black image
            img = Image.new('RGB', size, color='black')
            
            # Save to temp file
            temp_path = os.path.join(self.temp_dir, 'blank.png')
            img.save(temp_path)
            
            return temp_path
            
        except ImportError:
            # Fallback: create simple colored rectangle
            import numpy as np
            from moviepy.editor import ImageClip
            
            # Create black array
            array = np.zeros((size[1], size[0], 3), dtype=np.uint8)
            temp_path = os.path.join(self.temp_dir, 'blank.png')
            
            # Save using MoviePy
            clip = ImageClip(array, duration=1)
            clip.save_frame(temp_path)
            clip.close()
            
            return temp_path

    async def create_thumbnail(
        self, 
        video_path: str, 
        timestamp: float = 1.0
    ) -> str:
        """Extract thumbnail from video"""
        
        try:
            video = VideoFileClip(video_path)
            
            # Extract frame at specified timestamp
            frame_time = min(timestamp, video.duration - 0.1)
            frame = video.get_frame(frame_time)
            
            # Save as image
            thumbnail_path = video_path.replace('.mp4', '_thumbnail.jpg')
            
            from PIL import Image
            img = Image.fromarray(frame)
            img.save(thumbnail_path, 'JPEG', quality=85)
            
            video.close()
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            raise

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video file information"""
        
        try:
            video = VideoFileClip(video_path)
            
            info = {
                "duration": video.duration,
                "fps": video.fps,
                "size": (video.w, video.h),
                "aspect_ratio": video.w / video.h,
                "has_audio": video.audio is not None,
                "file_size": os.path.getsize(video_path)
            }
            
            video.close()
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return {}

    async def add_intro_outro(
        self, 
        video: VideoFileClip, 
        intro_path: Optional[str] = None,
        outro_path: Optional[str] = None
    ) -> VideoFileClip:
        """Add intro and outro to video"""
        
        clips = []
        
        # Add intro
        if intro_path and os.path.exists(intro_path):
            intro = VideoFileClip(intro_path)
            clips.append(intro)
        
        # Add main video
        clips.append(video)
        
        # Add outro
        if outro_path and os.path.exists(outro_path):
            outro = VideoFileClip(outro_path)
            clips.append(outro)
        
        if len(clips) > 1:
            return concatenate_videoclips(clips)
        else:
            return video

    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary files"""
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {str(e)}")

# Utility functions
async def quick_video_assembly(
    images: List[str],
    audio_file: str,
    output_path: str,
    platform: str = "youtube"
) -> str:
    """Quick video assembly for simple use cases"""
    
    assembler = VideoAssembler()
    
    # Create minimal content plan
    from ..models.content_plan import ContentPlan, VisualPlan
    
    content_plan = ContentPlan(
        content_type="simple",
        visual_plan=VisualPlan(
            style="simple",
            scenes=[f"Scene {i+1}" for i in range(len(images))],
            text_overlays=[]
        )
    )
    
    # Assemble video
    platform_videos = await assembler.assemble_video(
        content_plan, images, audio_file, [platform]
    )
    
    return platform_videos.get(platform, "")

def get_platform_specs(platform: str) -> Dict[str, Any]:
    """Get specifications for a platform"""
    
    specs_map = {
        "youtube": PlatformSpecs.YOUTUBE,
        "tiktok": PlatformSpecs.TIKTOK,
        "instagram": PlatformSpecs.INSTAGRAM,
        "facebook": PlatformSpecs.FACEBOOK
    }
    
    return specs_map.get(platform.lower(), PlatformSpecs.YOUTUBE)