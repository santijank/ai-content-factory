# content-engine/services/video_assembler.py
import asyncio
import json
import os
import tempfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from moviepy.editor import *
from moviepy.video.fx import resize
from PIL import Image, ImageDraw, ImageFont
import numpy as np

@dataclass
class VideoProject:
    script_components: Dict
    visual_plan: Dict
    audio_components: bytes
    assets: List[Dict]
    platform: str
    duration_seconds: float

@dataclass
class VideoOutput:
    video_file: bytes
    thumbnail: bytes
    metadata: Dict
    file_size_mb: float
    resolution: str
    platform_optimized: bool

class VideoTemplateManager:
    """จัดการ template สำหรับประเภทวิดีโอต่างๆ"""
    
    def __init__(self):
        self.templates = {
            "talking_head": {
                "layout": "single_speaker",
                "text_overlay_position": "bottom_third",
                "transition_style": "cut",
                "intro_duration": 3,
                "outro_duration": 5
            },
            "tutorial": {
                "layout": "screen_recording",
                "text_overlay_position": "top_banner",
                "transition_style": "fade",
                "intro_duration": 5,
                "outro_duration": 8
            },
            "review": {
                "layout": "split_screen",
                "text_overlay_position": "side_panel",
                "transition_style": "slide",
                "intro_duration": 4,
                "outro_duration": 6
            },
            "entertainment": {
                "layout": "dynamic_montage",
                "text_overlay_position": "center",
                "transition_style": "zoom",
                "intro_duration": 2,
                "outro_duration": 3
            }
        }

    def get_template(self, content_type: str) -> Dict:
        return self.templates.get(content_type, self.templates["entertainment"])

class PlatformOptimizer:
    """ปรับแต่งวิดีโอสำหรับแต่ละแพลตฟอร์ม"""
    
    def __init__(self):
        self.platform_specs = {
            "youtube": {
                "resolution": (1920, 1080),
                "aspect_ratio": "16:9",
                "max_duration": 900,  # 15 minutes
                "bitrate": "8000k",
                "format": "mp4"
            },
            "tiktok": {
                "resolution": (1080, 1920),
                "aspect_ratio": "9:16",
                "max_duration": 180,  # 3 minutes
                "bitrate": "6000k",
                "format": "mp4"
            },
            "instagram": {
                "resolution": (1080, 1080),
                "aspect_ratio": "1:1",
                "max_duration": 90,  # 1.5 minutes
                "bitrate": "5000k",
                "format": "mp4"
            },
            "facebook": {
                "resolution": (1280, 720),
                "aspect_ratio": "16:9",
                "max_duration": 240,  # 4 minutes
                "bitrate": "4000k",
                "format": "mp4"
            }
        }

    def get_platform_specs(self, platform: str) -> Dict:
        return self.platform_specs.get(platform, self.platform_specs["youtube"])

    def optimize_for_platform(self, video_clip: VideoFileClip, platform: str) -> VideoFileClip:
        """ปรับแต่งวิดีโอให้เหมาะกับแพลตฟอร์ม"""
        
        specs = self.get_platform_specs(platform)
        target_resolution = specs["resolution"]
        
        # ปรับขนาด
        video_clip = video_clip.resize(target_resolution)
        
        # ตัดความยาวถ้าเกิน
        if video_clip.duration > specs["max_duration"]:
            video_clip = video_clip.subclip(0, specs["max_duration"])
        
        return video_clip

class VideoAssembler:
    """ประกอบวิดีโอจากองค์ประกอบต่างๆ"""
    
    def __init__(self):
        self.template_manager = VideoTemplateManager()
        self.platform_optimizer = PlatformOptimizer()
        
        # Default fonts (ในระบบจริงควรมี font ไทยที่ดี)
        self.font_paths = {
            "title": "assets/fonts/NotoSansThai-Bold.ttf",
            "subtitle": "assets/fonts/NotoSansThai-Regular.ttf",
            "body": "assets/fonts/NotoSansThai-Light.ttf"
        }

    async def assemble_video(self, project: VideoProject) -> VideoOutput:
        """ประกอบวิดีโอสมบูรณ์"""
        
        try:
            # เลือก template
            template = self.template_manager.get_template(
                project.script_components.get('content_type', 'entertainment')
            )
            
            # สร้าง video clips
            video_clips = await self._create_video_clips(project, template)
            
            # เพิ่ม audio
            final_video = await self._add_audio_track(video_clips, project.audio_components)
            
            # เพิ่ม text overlays
            final_video = await self._add_text_overlays(final_video, project)
            
            # เพิ่ม intro/outro
            final_video = await self._add_intro_outro(final_video, project, template)
            
            # ปรับแต่งสำหรับแพลตฟอร์ม
            final_video = self.platform_optimizer.optimize_for_platform(
                final_video, project.platform
            )
            
            # สร้าง thumbnail
            thumbnail = await self._generate_thumbnail(final_video, project)
            
            # Export video
            video_bytes = await self._export_video(final_video, project.platform)
            
            return VideoOutput(
                video_file=video_bytes,
                thumbnail=thumbnail,
                metadata=self._create_metadata(project, final_video),
                file_size_mb=len(video_bytes) / (1024 * 1024),
                resolution=f"{final_video.w}x{final_video.h}",
                platform_optimized=True
            )
            
        except Exception as e:
            print(f"Video assembly error: {e}")
            return await self._create_fallback_video(project)

    async def _create_video_clips(self, project: VideoProject, template: Dict) -> VideoFileClip:
        """สร้าง video clips หลัก"""
        
        visual_plan = project.visual_plan
        clips = []
        
        # สร้าง clips ตาม visual plan
        for i, scene in enumerate(visual_plan.get('scenes', [])):
            clip = await self._create_scene_clip(scene, project.assets, i)
            clips.append(clip)
        
        # ถ้าไม่มี scenes ให้สร้าง default clip
        if not clips:
            clips = [await self._create_default_clip(project)]
        
        # รวม clips ด้วย transitions
        final_clip = await self._combine_clips_with_transitions(
            clips, template.get('transition_style', 'cut')
        )
        
        return final_clip

    async def _create_scene_clip(self, scene: Dict, assets: List[Dict], scene_index: int) -> VideoFileClip:
        """สร้าง clip สำหรับแต่ละ scene"""
        
        try:
            visual_type = scene.get('visual_type', 'static_image')
            duration = self._parse_duration(scene.get('timestamp', '0:05'))
            
            if visual_type == 'talking_head':
                clip = await self._create_talking_head_clip(duration, scene_index)
            elif visual_type == 'b_roll':
                clip = await self._create_b_roll_clip(assets, duration, scene_index)
            elif visual_type == 'graphics':
                clip = await self._create_graphics_clip(scene, duration)
            else:
                clip = await self._create_static_image_clip(assets, duration, scene_index)
            
            return clip
            
        except Exception as e:
            print(f"Error creating scene clip: {e}")
            return await self._create_fallback_clip(5.0)

    def _parse_duration(self, timestamp: str) -> float:
        """แปลง timestamp เป็นวินาที"""
        try:
            if '-' in timestamp:
                start, end = timestamp.split('-')
                start_sec = self._time_to_seconds(start)
                end_sec = self._time_to_seconds(end)
                return end_sec - start_sec
            else:
                return 5.0  # default duration
        except:
            return 5.0

    def _time_to_seconds(self, time_str: str) -> float:
        """แปลง MM:SS เป็นวินาที"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
            else:
                return float(parts[0])
        except:
            return 0.0

    async def _create_talking_head_clip(self, duration: float, scene_index: int) -> VideoFileClip:
        """สร้าง talking head clip"""
        
        # สร้าง background สี
        background_color = self._get_scene_color(scene_index)
        
        # ใช้ ColorClip สำหรับ background
        clip = ColorClip(
            size=(1920, 1080),
            color=background_color,
            duration=duration
        )
        
        # เพิ่ม frame decoration
        clip = self._add_talking_head_frame(clip)
        
        return clip

    async def _create_b_roll_clip(self, assets: List[Dict], duration: float, scene_index: int) -> VideoFileClip:
        """สร้าง B-roll clip จาก assets"""
        
        try:
            if assets and scene_index < len(assets):
                asset = assets[scene_index]
                
                # ในระบบจริงจะโหลดรูปจาก URL
                # ตอนนี้สร้าง placeholder
                clip = await self._create_image_clip_from_asset(asset, duration)
            else:
                # สร้าง placeholder clip
                clip = await self._create_placeholder_clip(duration, f"B-Roll Scene {scene_index + 1}")
            
            return clip
            
        except Exception as e:
            print(f"Error creating B-roll clip: {e}")
            return await self._create_fallback_clip(duration)

    async def _create_graphics_clip(self, scene: Dict, duration: float) -> VideoFileClip:
        """สร้าง graphics/animation clip"""
        
        # สร้าง animated graphics
        def make_frame(t):
            # สร้าง frame แต่ละเฟรม
            img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            
            # เพิ่ม animation effect
            progress = t / duration
            center_x = int(960 + 200 * np.sin(progress * 2 * np.pi))
            center_y = 540
            
            # วาดวงกลมที่เคลื่อนไหว
            y, x = np.ogrid[:1080, :1920]
            mask = (x - center_x)**2 + (y - center_y)**2 < 50**2
            img[mask] = [100, 150, 255]  # สีฟ้า
            
            return img
        
        clip = VideoClip(make_frame, duration=duration)
        return clip

    async def _create_static_image_clip(self, assets: List[Dict], duration: float, scene_index: int) -> VideoFileClip:
        """สร้าง static image clip"""
        
        if assets and scene_index < len(assets):
            asset = assets[scene_index]
            return await self._create_image_clip_from_asset(asset, duration)
        else:
            return await self._create_placeholder_clip(duration, f"Scene {scene_index + 1}")

    async def _create_image_clip_from_asset(self, asset: Dict, duration: float) -> VideoFileClip:
        """สร้าง clip จาก image asset"""
        
        try:
            # ในระบบจริงจะดาวน์โหลดรูปจาก asset['url']
            # ตอนนี้สร้าง placeholder
            
            # สร้างรูปภาพ placeholder
            img = Image.new('RGB', (1920, 1080), color=(70, 130, 180))
            draw = ImageDraw.Draw(img)
            
            # เขียนข้อความ
            text = asset.get('description', 'Image Asset')
            try:
                font = ImageFont.truetype(self.font_paths.get('title', ''), 60)
            except:
                font = ImageFont.load_default()
            
            # คำนวณตำแหน่งข้อความ
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (1920 - text_width) // 2
            y = (1080 - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font)
            
            # แปลงเป็น numpy array
            img_array = np.array(img)
            
            # สร้าง ImageClip
            clip = ImageClip(img_array, duration=duration)
            
            return clip
            
        except Exception as e:
            print(f"Error creating image clip: {e}")
            return await self._create_fallback_clip(duration)

    async def _create_placeholder_clip(self, duration: float, text: str) -> VideoFileClip:
        """สร้าง placeholder clip"""
        
        # สร้างพื้นหลังไล่สี
        def make_frame(t):
            # สร้าง gradient background
            img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            
            for y in range(1080):
                color_value = int(50 + (y / 1080) * 100)
                img[y, :] = [color_value, color_value + 20, color_value + 50]
            
            return img
        
        clip = VideoClip(make_frame, duration=duration)
        
        # เพิ่มข้อความ
        txt_clip = TextClip(
            text,
            fontsize=60,
            color='white',
            font='Arial-Bold'
        ).set_position('center').set_duration(duration)
        
        final_clip = CompositeVideoClip([clip, txt_clip])
        return final_clip

    async def _create_fallback_clip(self, duration: float) -> VideoFileClip:
        """สร้าง fallback clip เมื่อเกิดข้อผิดพลาด"""
        
        clip = ColorClip(
            size=(1920, 1080),
            color=(50, 50, 50),
            duration=duration
        )
        
        return clip

    def _get_scene_color(self, scene_index: int) -> Tuple[int, int, int]:
        """ได้สีสำหรับแต่ละ scene"""
        colors = [
            (70, 130, 180),   # Steel Blue
            (100, 149, 237),  # Cornflower Blue
            (65, 105, 225),   # Royal Blue
            (30, 144, 255),   # Dodger Blue
            (0, 191, 255)     # Deep Sky Blue
        ]
        return colors[scene_index % len(colors)]

    def _add_talking_head_frame(self, clip: VideoFileClip) -> VideoFileClip:
        """เพิ่มกรอบสำหรับ talking head"""
        
        # สร้าง frame overlay
        def make_frame_overlay(t):
            img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            
            # วาดกรอบ
            border_width = 10
            img[:border_width, :] = [255, 255, 255]  # Top
            img[-border_width:, :] = [255, 255, 255]  # Bottom
            img[:, :border_width] = [255, 255, 255]  # Left
            img[:, -border_width:] = [255, 255, 255]  # Right
            
            return img
        
        frame_clip = VideoClip(make_frame_overlay, duration=clip.duration)
        frame_clip = frame_clip.set_opacity(0.3)
        
        return CompositeVideoClip([clip, frame_clip])

    async def _combine_clips_with_transitions(self, clips: List[VideoFileClip], transition_style: str) -> VideoFileClip:
        """รวม clips ด้วย transition effects"""
        
        if not clips:
            return await self._create_fallback_clip(5.0)
        
        if len(clips) == 1:
            return clips[0]
        
        try:
            if transition_style == 'fade':
                return self._fade_transitions(clips)
            elif transition_style == 'slide':
                return self._slide_transitions(clips)
            elif transition_style == 'zoom':
                return self._zoom_transitions(clips)
            else:  # 'cut'
                return concatenate_videoclips(clips)
                
        except Exception as e:
            print(f"Error with transitions: {e}")
            return concatenate_videoclips(clips)

    def _fade_transitions(self, clips: List[VideoFileClip]) -> VideoFileClip:
        """สร้าง fade transition"""
        
        fade_duration = 0.5
        result_clips = []
        
        for i, clip in enumerate(clips):
            if i == 0:
                # First clip: fade in only
                clip = clip.fadein(fade_duration)
            elif i == len(clips) - 1:
                # Last clip: fade out only
                clip = clip.fadeout(fade_duration)
            else:
                # Middle clips: fade in and out
                clip = clip.fadein(fade_duration).fadeout(fade_duration)
            
            result_clips.append(clip)
        
        return concatenate_videoclips(result_clips)

    def _slide_transitions(self, clips: List[VideoFileClip]) -> VideoFileClip:
        """สร้าง slide transition"""
        
        # ในระบบจริงจะมี slide effect ที่ซับซ้อนกว่า
        # ตอนนี้ใช้ fade แทน
        return self._fade_transitions(clips)

    def _zoom_transitions(self, clips: List[VideoFileClip]) -> VideoFileClip:
        """สร้าง zoom transition"""
        
        result_clips = []
        
        for clip in clips:
            # เพิ่ม zoom effect
            zoomed_clip = clip.resize(lambda t: 1 + 0.1 * t / clip.duration)
            result_clips.append(zoomed_clip)
        
        return concatenate_videoclips(result_clips)

    async def _add_audio_track(self, video: VideoFileClip, audio_bytes: bytes) -> VideoFileClip:
        """เพิ่ม audio track"""
        
        try:
            # บันทึก audio เป็นไฟล์ชั่วคราว
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_audio:
                tmp_audio.write(audio_bytes)
                tmp_audio.flush()
                
                # โหลด audio
                audio = AudioFileClip(tmp_audio.name)
                
                # ปรับความยาวให้ตรงกับวิดีโอ
                if audio.duration > video.duration:
                    audio = audio.subclip(0, video.duration)
                elif audio.duration < video.duration:
                    # Loop audio ถ้าสั้นกว่า
                    repeats = int(video.duration / audio.duration) + 1
                    audio = concatenate_audioclips([audio] * repeats)
                    audio = audio.subclip(0, video.duration)
                
                # ผสม audio กับ video
                final_video = video.set_audio(audio)
                
                # ลบไฟล์ชั่วคราว
                os.unlink(tmp_audio.name)
                
                return final_video
                
        except Exception as e:
            print(f"Error adding audio: {e}")
            return video

    async def _add_text_overlays(self, video: VideoFileClip, project: VideoProject) -> VideoFileClip:
        """เพิ่ม text overlays"""
        
        try:
            text_overlays = project.visual_plan.get('text_overlays', [])
            
            if not text_overlays:
                return video
            
            overlay_clips = [video]
            
            for overlay in text_overlays:
                text_clip = await self._create_text_overlay(overlay, video.duration)
                if text_clip:
                    overlay_clips.append(text_clip)
            
            return CompositeVideoClip(overlay_clips)
            
        except Exception as e:
            print(f"Error adding text overlays: {e}")
            return video

    async def _create_text_overlay(self, overlay_config: Dict, video_duration: float) -> Optional[TextClip]:
        """สร้าง text overlay"""
        
        try:
            text = overlay_config.get('text', '')
            timing = overlay_config.get('timing', '0:00-0:05')
            style = overlay_config.get('style', 'simple')
            
            if not text:
                return None
            
            # Parse timing
            start_time, end_time = self._parse_timing(timing)
            duration = min(end_time - start_time, video_duration - start_time)
            
            if duration <= 0:
                return None
            
            # สร้าง TextClip
            txt_clip = TextClip(
                text,
                fontsize=self._get_font_size(style),
                color=self._get_text_color(style),
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2
            )
            
            # ตั้งตำแหน่งและเวลา
            txt_clip = txt_clip.set_position(self._get_text_position(style))
            txt_clip = txt_clip.set_start(start_time).set_duration(duration)
            
            # เพิ่ม animation
            if style == 'animated':
                txt_clip = txt_clip.crossfadein(0.5).crossfadeout(0.5)
            
            return txt_clip
            
        except Exception as e:
            print(f"Error creating text overlay: {e}")
            return None

    def _parse_timing(self, timing: str) -> Tuple[float, float]:
        """แปลง timing string เป็น start, end seconds"""
        try:
            start_str, end_str = timing.split('-')
            start_time = self._time_to_seconds(start_str)
            end_time = self._time_to_seconds(end_str)
            return start_time, end_time
        except:
            return 0.0, 5.0

    def _get_font_size(self, style: str) -> int:
        """ได้ขนาดฟอนต์ตาม style"""
        sizes = {
            'title': 80,
            'subtitle': 60,
            'body': 40,
            'caption': 30,
            'animated': 70,
            'simple': 50
        }
        return sizes.get(style, 50)

    def _get_text_color(self, style: str) -> str:
        """ได้สีข้อความตาม style"""
        colors = {
            'title': 'white',
            'subtitle': 'yellow',
            'body': 'white',
            'caption': 'lightgray',
            'animated': 'cyan',
            'simple': 'white'
        }
        return colors.get(style, 'white')

    def _get_text_position(self, style: str) -> str:
        """ได้ตำแหน่งข้อความตาม style"""
        positions = {
            'title': 'center',
            'subtitle': ('center', 'top'),
            'body': 'center',
            'caption': ('center', 'bottom'),
            'animated': 'center',
            'simple': ('center', 'bottom')
        }
        return positions.get(style, 'center')

    async def _add_intro_outro(self, video: VideoFileClip, project: VideoProject, template: Dict) -> VideoFileClip:
        """เพิ่ม intro และ outro"""
        
        try:
            clips = []
            
            # สร้าง intro
            intro_duration = template.get('intro_duration', 3)
            intro_clip = await self._create_intro_clip(project, intro_duration)
            clips.append(intro_clip)
            
            # เพิ่มวิดีโอหลัก
            clips.append(video)
            
            # สร้าง outro
            outro_duration = template.get('outro_duration', 5)
            outro_clip = await self._create_outro_clip(project, outro_duration)
            clips.append(outro_clip)
            
            return concatenate_videoclips(clips)
            
        except Exception as e:
            print(f"Error adding intro/outro: {e}")
            return video

    async def _create_intro_clip(self, project: VideoProject, duration: float) -> VideoFileClip:
        """สร้าง intro clip"""
        
        # สร้าง background
        background = ColorClip(
            size=(1920, 1080),
            color=(20, 30, 50),
            duration=duration
        )
        
        # เพิ่มชื่อเรื่อง
        title = project.script_components.get('title_suggestions', ['วิดีโอใหม่'])[0]
        
        title_clip = TextClip(
            title,
            fontsize=80,
            color='white',
            font='Arial-Bold'
        ).set_position('center').set_duration(duration)
        
        # เพิ่ม animation
        title_clip = title_clip.crossfadein(1.0)
        
        return CompositeVideoClip([background, title_clip])

    async def _create_outro_clip(self, project: VideoProject, duration: float) -> VideoFileClip:
        """สร้าง outro clip"""
        
        # สร้าง background
        background = ColorClip(
            size=(1920, 1080),
            color=(30, 20, 50),
            duration=duration
        )
        
        # เพิ่ม CTA
        cta_text = project.script_components.get('call_to_action', 'อย่าลืม Like และ Subscribe!')
        
        cta_clip = TextClip(
            cta_text,
            fontsize=60,
            color='yellow',
            font='Arial-Bold'
        ).set_position('center').set_duration(duration)
        
        # เพิ่ม animation
        cta_clip = cta_clip.crossfadein(0.5).crossfadeout(0.5)
        
        return CompositeVideoClip([background, cta_clip])

    async def _generate_thumbnail(self, video: VideoFileClip, project: VideoProject) -> bytes:
        """สร้าง thumbnail จากวิดีโอ"""
        
        try:
            # ดึงเฟรมจากกลางวิดีโอ
            thumbnail_time = video.duration / 2
            frame = video.get_frame(thumbnail_time)
            
            # แปลงเป็น PIL Image
            img = Image.fromarray(frame.astype('uint8'))
            
            # ปรับขนาดสำหรับ thumbnail
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            
            # เพิ่มข้อความ title
            draw = ImageDraw.Draw(img)
            title = project.script_components.get('title_suggestions', [''])[0]
            
            if title:
                try:
                    font = ImageFont.truetype(self.font_paths.get('title', ''), 60)
                except:
                    font = ImageFont.load_default()
                
                # วาดข้อความพร้อม outline
                bbox = draw.textbbox((0, 0), title, font=font)
                text_width = bbox[2] - bbox[0]
                x = (1280 - text_width) // 2
                y = 50
                
                # Outline
                for dx in [-2, -1, 0, 1, 2]:
                    for dy in [-2, -1, 0, 1, 2]:
                        draw.text((x + dx, y + dy), title, fill='black', font=font)
                
                # Main text
                draw.text((x, y), title, fill='white', font=font)
            
            # แปลงเป็น bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return await self._create_default_thumbnail()

    async def _create_default_thumbnail(self) -> bytes:
        """สร้าง thumbnail พื้นฐาน"""
        
        img = Image.new('RGB', (1280, 720), color=(70, 130, 180))
        draw = ImageDraw.Draw(img)
        
        text = "Generated Video"
        try:
            font = ImageFont.truetype(self.font_paths.get('title', ''), 60)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1280 - text_width) // 2
        y = (720 - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        return buffer.getvalue()

    async def _export_video(self, video: VideoFileClip, platform: str) -> bytes:
        """Export วิดีโอเป็น bytes"""
        
        try:
            specs = self.platform_optimizer.get_platform_specs(platform)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                video.write_videofile(
                    tmp_file.name,
                    codec='libx264',
                    audio_codec='aac',
                    bitrate=specs['bitrate'],
                    fps=30,
                    verbose=False,
                    logger=None
                )
                
                # อ่านไฟล์เป็น bytes
                with open(tmp_file.name, 'rb') as f:
                    video_bytes = f.read()
                
                # ลบไฟล์ชั่วคราว
                os.unlink(tmp_file.name)
                
                return video_bytes
                
        except Exception as e:
            print(f"Error exporting video: {e}")
            raise

    def _create_metadata(self, project: VideoProject, video: VideoFileClip) -> Dict:
        """สร้าง metadata สำหรับวิดีโอ"""
        
        return {
            "title": project.script_components.get('title_suggestions', [''])[0],
            "description": project.script_components.get('introduction', ''),
            "duration_seconds": video.duration,
            "resolution": f"{video.w}x{video.h}",
            "fps": video.fps,
            "platform": project.platform,
            "hashtags": project.script_components.get('hashtags', []),
            "created_at": asyncio.get_event_loop().time()
        }

    async def _create_fallback_video(self, project: VideoProject) -> VideoOutput:
        """สร้างวิดีโอสำรองเมื่อเกิดข้อผิดพลาด"""
        
        # สร้างวิดีโอง่ายๆ
        clip = ColorClip(
            size=(1920, 1080),
            color=(50, 50, 50),
            duration=10
        )
        
        # เพิ่มข้อความ
        text_clip = TextClip(
            "Video Generation Error",
            fontsize=60,
            color='white',
            font='Arial-Bold'
        ).set_position('center').set_duration(10)
        
        video = CompositeVideoClip([clip, text_clip])
        
        # Export
        video_bytes = await self._export_video(video, project.platform)
        thumbnail = await self._create_default_thumbnail()
        
        return VideoOutput(
            video_file=video_bytes,
            thumbnail=thumbnail,
            metadata={"title": "Error Video", "duration_seconds": 10},
            file_size_mb=len(video_bytes) / (1024 * 1024),
            resolution="1920x1080",
            platform_optimized=False
        )

    async def _create_default_clip(self, project: VideoProject) -> VideoFileClip:
        """สร้าง default clip เมื่อไม่มี visual plan"""
        
        duration = 30.0  # default duration
        
        # สร้าง gradient background
        def make_frame(t):
            img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            
            # Gradient effect
            for y in range(1080):
                color_value = int(50 + (y / 1080) * 100)
                img[y, :] = [color_value, color_value + 30, color_value + 60]
            
            # เพิ่ม moving element
            progress = t / duration
            center_x = int(960 + 300 * np.sin(progress * 4 * np.pi))
            center_y = int(540 + 100 * np.cos(progress * 6 * np.pi))
            
            # วาดวงกลมเคลื่อนไหว
            y, x = np.ogrid[:1080, :1920]
            mask = (x - center_x)**2 + (y - center_y)**2 < 30**2
            img[mask] = [255, 255, 100]  # สีเหลือง
            
            return img
        
        clip = VideoClip(make_frame, duration=duration)
        
        # เพิ่มข้อความ
        title = project.script_components.get('title_suggestions', ['Generated Content'])[0]
        
        title_clip = TextClip(
            title,
            fontsize=70,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=3
        ).set_position('center').set_duration(duration)
        
        return CompositeVideoClip([clip, title_clip])

# Usage Example
async def main():
    """ตัวอย่างการใช้ Video Assembler"""
    
    # Mock project data
    project = VideoProject(
        script_components={
            "title_suggestions": ["AI สร้างวิดีโออัตโนมัติ"],
            "introduction": "วันนี้เราจะมาดู AI ที่สามารถสร้างวิดีโอได้",
            "call_to_action": "กด Like และ Subscribe นะครับ",
            "hashtags": ["#AI", "#AutoVideo", "#Tech"]
        },
        visual_plan={
            "scenes": [
                {
                    "timestamp": "0:00-0:05",
                    "visual_type": "talking_head",
                    "description": "เปิดเรื่อง"
                },
                {
                    "timestamp": "0:05-0:15",
                    "visual_type": "b_roll",
                    "description": "แสดงตัวอย่าง"
                }
            ],
            "text_overlays": [
                {
                    "text": "AI Video Generator",
                    "timing": "0:02-0:07",
                    "style": "title"
                }
            ]
        },
        audio_components=b"mock_audio_data",  # จริงๆ จะเป็น audio bytes
        assets=[
            {"description": "AI Robot", "url": "https://example.com/image1.jpg"},
            {"description": "Technology", "url": "https://example.com/image2.jpg"}
        ],
        platform="youtube",
        duration_seconds=30.0
    )
    
    # สร้างวิดีโอ
    assembler = VideoAssembler()
    
    try:
        result = await assembler.assemble_video(project)
        
        print(f"Video generated successfully!")
        print(f"File size: {result.file_size_mb:.2f} MB")
        print(f"Resolution: {result.resolution}")
        print(f"Platform optimized: {result.platform_optimized}")
        
        # บันทึกไฟล์ (ตัวอย่าง)
        with open("generated_video.mp4", "wb") as f:
            f.write(result.video_file)
        
        with open("generated_thumbnail.jpg", "wb") as f:
            f.write(result.thumbnail)
        
        return result
        
    except Exception as e:
        print(f"Error in video generation: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())