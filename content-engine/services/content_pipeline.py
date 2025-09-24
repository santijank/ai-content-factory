"""
Content Generation Pipeline
Pipeline หลักสำหรับสร้างเนื้อหาจาก Content Opportunities ผ่านระบบ AI แบบครบวงจร
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import uuid
from pathlib import Path
import aiofiles

from shared.models.content_opportunity import ContentOpportunity
from shared.models.content_plan import ContentPlan, ScriptPlan, VisualPlan, AudioPlan, PlatformOptimization
from shared.models.quality_tier import QualityTier
from services.service_registry import ServiceRegistry
from services.ai_director import AIDirector
from utils.config_manager import ConfigManager
from shared.utils.logger import get_logger
from shared.utils.error_handler import handle_errors, PipelineError


@dataclass
class ContentAssets:
    """เนื้อหาที่สร้างเสร็จแล้ว"""
    script: Dict[str, str]  # {"hook": "...", "main_content": "...", "cta": "..."}
    images: List[str]  # paths to generated images
    audio_files: Dict[str, str]  # {"voice": "path", "background": "path", "final": "path"}
    video_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    generation_stats: Dict[str, Any] = None


@dataclass
class PipelineConfig:
    """การตั้งค่า Pipeline"""
    quality_tier: QualityTier = QualityTier.BUDGET
    target_platforms: List[str] = None
    max_concurrent_jobs: int = 3
    timeout_seconds: int = 300
    save_intermediate: bool = True
    output_directory: str = "./content_output"
    temp_directory: str = "./temp"


@dataclass
class GenerationProgress:
    """ความคืบหน้าการสร้าง"""
    stage: str  # "planning", "script", "visuals", "audio", "assembly", "optimization"
    progress: float  # 0.0 - 1.0
    message: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    error: Optional[str] = None


class ContentPipeline:
    """
    Pipeline หลักสำหรับสร้างเนื้อหาแบบครบวงจร
    """
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.logger = get_logger(__name__)
        self.service_registry = ServiceRegistry()
        self.ai_director = AIDirector(self.config.quality_tier)
        self.config_manager = ConfigManager()
        
        # สร้าง directories
        self._ensure_directories()
        
        # Track ongoing generations
        self.active_generations: Dict[str, GenerationProgress] = {}
        self.generation_semaphore = asyncio.Semaphore(self.config.max_concurrent_jobs)
        
        # Load pipeline settings
        self.pipeline_settings = self._load_pipeline_settings()
        
    def _ensure_directories(self):
        """สร้าง directories ที่จำเป็น"""
        Path(self.config.output_directory).mkdir(parents=True, exist_ok=True)
        Path(self.config.temp_directory).mkdir(parents=True, exist_ok=True)
        Path(f"{self.config.output_directory}/scripts").mkdir(exist_ok=True)
        Path(f"{self.config.output_directory}/images").mkdir(exist_ok=True)
        Path(f"{self.config.output_directory}/audio").mkdir(exist_ok=True)
        Path(f"{self.config.output_directory}/videos").mkdir(exist_ok=True)
        
    def _load_pipeline_settings(self) -> Dict:
        """โหลดการตั้งค่า pipeline"""
        return {
            "script_generation": {
                "min_hook_length": 10,
                "max_hook_length": 50,
                "min_main_length": 100,
                "max_main_length": 1000,
                "cta_templates": [
                    "กดไลค์และติดตามถ้าชอบเนื้อหา!",
                    "แชร์ให้เพื่อนดูกันด้วย!",
                    "คอมเมนต์บอกความคิดเห็นได้เลย!",
                    "กดกระดิ่งเพื่อไม่พลาดคลิปใหม่!"
                ]
            },
            "visual_generation": {
                "default_aspect_ratio": "16:9",
                "max_scenes": 8,
                "image_quality": "high",
                "style_presets": {
                    "educational": "clean, modern, infographic style",
                    "entertainment": "vibrant, colorful, engaging",
                    "tutorial": "clear, step-by-step, instructional",
                    "news": "professional, credible, journalistic"
                }
            },
            "audio_generation": {
                "voice_speed": "normal",
                "background_volume": 0.3,
                "fade_in_duration": 1.0,
                "fade_out_duration": 2.0
            }
        }

    async def generate_content(self, opportunity: ContentOpportunity) -> ContentAssets:
        """
        สร้างเนื้อหาจาก ContentOpportunity
        """
        generation_id = str(uuid.uuid4())
        
        try:
            async with self.generation_semaphore:
                return await self._generate_content_internal(opportunity, generation_id)
        except Exception as e:
            self.logger.error(f"Content generation failed for {opportunity.id}: {e}")
            if generation_id in self.active_generations:
                self.active_generations[generation_id].error = str(e)
            raise PipelineError(f"Content generation failed: {e}")

    async def _generate_content_internal(self, opportunity: ContentOpportunity, generation_id: str) -> ContentAssets:
        """สร้างเนื้อหาแบบละเอียด"""
        
        self.logger.info(f"Starting content generation for opportunity: {opportunity.content_idea.title}")
        
        # Initialize progress tracking
        progress = GenerationProgress(
            stage="planning",
            progress=0.0,
            message="กำลังวางแผนการสร้างเนื้อหา...",
            started_at=datetime.now()
        )
        self.active_generations[generation_id] = progress
        
        try:
            # Stage 1: Content Planning (10%)
            await self._update_progress(generation_id, "planning", 0.1, "สร้างแผนการผลิตเนื้อหา...")
            content_plan = await self._create_detailed_content_plan(opportunity)
            
            # Stage 2: Script Generation (30%)
            await self._update_progress(generation_id, "script", 0.3, "กำลังสร้าง script...")
            script = await self._generate_script(content_plan, opportunity)
            
            # Stage 3: Visual Generation (50%)
            await self._update_progress(generation_id, "visuals", 0.5, "กำลังสร้างภาพประกอบ...")
            images = await self._generate_visuals(content_plan, script)
            
            # Stage 4: Audio Generation (70%)
            await self._update_progress(generation_id, "audio", 0.7, "กำลังสร้างเสียงบรรยาย...")
            audio_files = await self._generate_audio(content_plan, script)
            
            # Stage 5: Video Assembly (90%)
            await self._update_progress(generation_id, "assembly", 0.9, "กำลังประกอบวิดีโอ...")
            video_path = await self._assemble_video(script, images, audio_files, content_plan)
            
            # Stage 6: Platform Optimization (100%)
            await self._update_progress(generation_id, "optimization", 1.0, "ปรับแต่งสำหรับแต่ละ platform...")
            metadata = await self._optimize_for_platforms(content_plan, opportunity)
            
            # Create final assets
            assets = ContentAssets(
                script=script,
                images=images,
                audio_files=audio_files,
                video_path=video_path,
                metadata=metadata,
                generation_stats=self._calculate_generation_stats(generation_id)
            )
            
            # Save assets if configured
            if self.config.save_intermediate:
                await self._save_content_assets(assets, opportunity, generation_id)
            
            self.logger.info(f"Content generation completed for {opportunity.content_idea.title}")
            
            # Clean up progress tracking
            if generation_id in self.active_generations:
                del self.active_generations[generation_id]
            
            return assets
            
        except Exception as e:
            await self._update_progress(generation_id, "error", 0.0, f"เกิดข้อผิดพลาด: {str(e)}")
            raise

    async def _create_detailed_content_plan(self, opportunity: ContentOpportunity) -> ContentPlan:
        """สร้างแผนการผลิตเนื้อหาแบบละเอียด"""
        
        # ใช้ AI Director สร้างแผนเนื้อหา
        plan_request = {
            "trend_topic": opportunity.trend_data.topic,
            "content_idea": opportunity.content_idea.title,
            "content_type": opportunity.content_idea.content_type,
            "target_audience": opportunity.content_idea.target_audience,
            "estimated_duration": opportunity.content_idea.estimated_duration,
            "platforms": self.config.target_platforms or ["youtube", "tiktok"],
            "quality_tier": self.config.quality_tier.value
        }
        
        content_plan = await self.ai_director.create_comprehensive_content_plan(plan_request)
        
        # เพิ่มข้อมูลเฉพาะ pipeline
        content_plan.generation_id = str(uuid.uuid4())
        content_plan.estimated_cost = self._calculate_estimated_cost(content_plan)
        
        return content_plan

    async def _generate_script(self, content_plan: ContentPlan, opportunity: ContentOpportunity) -> Dict[str, str]:
        """สร้าง script สำหรับเนื้อหา"""
        
        text_ai = self.service_registry.get_service("text_ai", self.config.quality_tier)
        
        # สร้าง prompt สำหรับ script
        script_prompt = self._build_script_prompt(content_plan, opportunity)
        
        # Generate script
        script_response = await text_ai.generate_content(script_prompt)
        
        # Parse และ validate script
        script = self._parse_script_response(script_response)
        script = self._validate_and_fix_script(script, content_plan)
        
        return script

    def _build_script_prompt(self, content_plan: ContentPlan, opportunity: ContentOpportunity) -> str:
        """สร้าง prompt สำหรับการสร้าง script"""
        
        settings = self.pipeline_settings["script_generation"]
        
        prompt = f"""
สร้าง script สำหรับวิดีโอตามข้อมูลต่อไปนี้:

หัวข้อ: {opportunity.content_idea.title}
ประเภทเนื้อหา: {opportunity.content_idea.content_type}
กลุ่มเป้าหมาย: {opportunity.content_idea.target_audience}
ระยะเวลา: {opportunity.content_idea.estimated_duration} วินาที
Platform หลัก: {', '.join(self.config.target_platforms or ['YouTube'])}

แผนเนื้อหา:
- Hook: {content_plan.script_plan.hook_concept}
- เนื้อหาหลัก: {content_plan.script_plan.main_points}
- Call-to-Action: {content_plan.script_plan.cta_style}

กรุณาสร้าง script ในรูปแบบ JSON:
{{
  "hook": "ประโยคเปิดที่ดึงดูดใจใน 3-5 วินาทีแรก ({settings['min_hook_length']}-{settings['max_hook_length']} คำ)",
  "main_content": "เนื้อหาหลักที่ครอบคลุมประเด็นสำคัญ ({settings['min_main_length']}-{settings['max_main_length']} คำ)",
  "cta": "призв призыв к действию ที่เหมาะสมกับ platform"
}}

ข้อกำหนด:
- ใช้ภาษาไทยที่เข้าใจง่าย
- เหมาะสมกับกลุ่มเป้าหมาย
- มีความน่าสนใจและดึงดูดความสนใจ
- เนื้อหาต้องถูกต้องและให้ประโยชน์
- ไม่ใช้คำหยาบหรือเนื้อหาที่ไม่เหมาะสม
"""
        
        return prompt.strip()

    def _parse_script_response(self, response: str) -> Dict[str, str]:
        """แยกวิเคราะห์ response จาก AI เป็น script"""
        
        try:
            # พยายาม parse เป็น JSON
            if response.strip().startswith('{'):
                script = json.loads(response)
            else:
                # ถ้าไม่ใช่ JSON ให้แยกแบบ manual
                script = self._manual_parse_script(response)
            
            # ตรวจสอบ keys ที่จำเป็น
            required_keys = ["hook", "main_content", "cta"]
            for key in required_keys:
                if key not in script:
                    script[key] = f"[Missing {key}]"
            
            return script
            
        except Exception as e:
            self.logger.warning(f"Failed to parse script response: {e}")
            return self._create_fallback_script()

    def _manual_parse_script(self, response: str) -> Dict[str, str]:
        """แยกวิเคราะห์ script แบบ manual"""
        
        script = {}
        lines = response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if 'hook' in line.lower() and ':' in line:
                if current_section:
                    script[current_section] = '\n'.join(current_content).strip()
                current_section = 'hook'
                current_content = [line.split(':', 1)[-1].strip()]
            elif 'main' in line.lower() and ':' in line:
                if current_section:
                    script[current_section] = '\n'.join(current_content).strip()
                current_section = 'main_content'
                current_content = [line.split(':', 1)[-1].strip()]
            elif 'cta' in line.lower() and ':' in line:
                if current_section:
                    script[current_section] = '\n'.join(current_content).strip()
                current_section = 'cta'
                current_content = [line.split(':', 1)[-1].strip()]
            elif line and current_section:
                current_content.append(line)
        
        if current_section:
            script[current_section] = '\n'.join(current_content).strip()
        
        return script

    def _create_fallback_script(self) -> Dict[str, str]:
        """สร้าง script สำรองเมื่อ AI ล้มเหลว"""
        
        settings = self.pipeline_settings["script_generation"]
        
        return {
            "hook": "สวัสดีครับทุกคน! วันนี้มีเรื่องน่าสนใจมาแชร์",
            "main_content": "เนื้อหาหลักของวิดีโอที่จะให้ความรู้และความบันเทิงแก่ผู้ชม โดยจะครอบคลุมประเด็นสำคัญและให้ข้อมูลที่เป็นประโยชน์",
            "cta": settings["cta_templates"][0]
        }

    def _validate_and_fix_script(self, script: Dict[str, str], content_plan: ContentPlan) -> Dict[str, str]:
        """ตรวจสอบและแก้ไข script ให้เหมาะสม"""
        
        settings = self.pipeline_settings["script_generation"]
        
        # ตรวจสอบความยาว hook
        hook_words = len(script["hook"].split())
        if hook_words < settings["min_hook_length"]:
            script["hook"] += " น่าสนใจมากเลย!"
        elif hook_words > settings["max_hook_length"]:
            words = script["hook"].split()
            script["hook"] = " ".join(words[:settings["max_hook_length"]])
        
        # ตรวจสอบความยาว main content
        main_words = len(script["main_content"].split())
        if main_words < settings["min_main_length"]:
            script["main_content"] += " ขอให้ทุกคนได้ความรู้และความบันเทิงจากเนื้อหานี้นะครับ"
        elif main_words > settings["max_main_length"]:
            words = script["main_content"].split()
            script["main_content"] = " ".join(words[:settings["max_main_length"]])
        
        # เพิ่ม full text
        script["full_text"] = f"{script['hook']} {script['main_content']} {script['cta']}"
        
        return script

    async def _generate_visuals(self, content_plan: ContentPlan, script: Dict[str, str]) -> List[str]:
        """สร้างภาพประกอบสำหรับเนื้อหา"""
        
        if self.config.quality_tier == QualityTier.BUDGET:
            # สำหรับ budget tier ใช้ภาพ placeholder
            return await self._generate_placeholder_images(content_plan)
        
        image_ai = self.service_registry.get_service("image_ai", self.config.quality_tier)
        
        if not image_ai:
            self.logger.warning("No image AI service available, using placeholders")
            return await self._generate_placeholder_images(content_plan)
        
        images = []
        settings = self.pipeline_settings["visual_generation"]
        
        for i, scene in enumerate(content_plan.visual_plan.scenes):
            try:
                # สร้าง prompt สำหรับภาพ
                image_prompt = self._build_image_prompt(scene, content_plan, settings)
                
                # สร้างภาพ
                image_path = await image_ai.generate_image(
                    prompt=image_prompt,
                    style=settings["style_presets"].get(content_plan.content_type, "modern"),
                    aspect_ratio=settings["default_aspect_ratio"],
                    quality=settings["image_quality"]
                )
                
                if image_path:
                    images.append(image_path)
                    
            except Exception as e:
                self.logger.warning(f"Failed to generate image for scene {i}: {e}")
                # สร้างภาพ placeholder แทน
                placeholder = await self._create_placeholder_image(scene, i)
                images.append(placeholder)
        
        return images

    def _build_image_prompt(self, scene: str, content_plan: ContentPlan, settings: Dict) -> str:
        """สร้าง prompt สำหรับการสร้างภาพ"""
        
        style = settings["style_presets"].get(content_plan.content_type, "modern")
        
        prompt = f"""
{scene}, {style}, high quality, detailed, professional lighting, 
aspect ratio {settings["default_aspect_ratio"]}, 
suitable for {content_plan.content_type} content,
clean composition, engaging visual
"""
        
        return prompt.strip()

    async def _generate_placeholder_images(self, content_plan: ContentPlan) -> List[str]:
        """สร้างภาพ placeholder สำหรับ budget tier"""
        
        images = []
        
        for i, scene in enumerate(content_plan.visual_plan.scenes):
            placeholder_path = await self._create_placeholder_image(scene, i)
            images.append(placeholder_path)
        
        return images

    async def _create_placeholder_image(self, scene: str, index: int) -> str:
        """สร้างภาพ placeholder"""
        
        # สร้างภาพ placeholder ด้วย text
        from PIL import Image, ImageDraw, ImageFont
        
        width, height = 1920, 1080  # 16:9 aspect ratio
        image = Image.new('RGB', (width, height), color='lightblue')
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # วาด text
        text = f"Scene {index + 1}: {scene[:50]}..."
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='darkblue', font=font)
        
        # บันทึกภาพ
        timestamp = int(datetime.now().timestamp())
        image_path = f"{self.config.output_directory}/images/placeholder_{index}_{timestamp}.png"
        image.save(image_path)
        
        return image_path

    async def _generate_audio(self, content_plan: ContentPlan, script: Dict[str, str]) -> Dict[str, str]:
        """สร้างไฟล์เสียงสำหรับเนื้อหา"""
        
        audio_files = {}
        
        # สร้างเสียงบรรยาย
        voice_path = await self._generate_voice_audio(script["full_text"], content_plan)
        audio_files["voice"] = voice_path
        
        # สร้างเสียงพื้นหลัง (ถ้าต้องการ)
        if content_plan.audio_plan.background_music != "none":
            bg_path = await self._generate_background_music(content_plan)
            audio_files["background"] = bg_path
        
        # รวมเสียง
        final_path = await self._mix_audio_files(audio_files, content_plan)
        audio_files["final"] = final_path
        
        return audio_files

    async def _generate_voice_audio(self, text: str, content_plan: ContentPlan) -> str:
        """สร้างเสียงบรรยาย"""
        
        tts_service = self.service_registry.get_service("tts", self.config.quality_tier)
        
        if not tts_service:
            # สร้างไฟล์เสียงเงียบสำหรับ placeholder
            return await self._create_silent_audio()
        
        try:
            voice_path = await tts_service.text_to_speech(
                text=text,
                voice_style=content_plan.audio_plan.voice_style,
                speed=self.pipeline_settings["audio_generation"]["voice_speed"]
            )
            
            return voice_path
            
        except Exception as e:
            self.logger.warning(f"Failed to generate voice audio: {e}")
            return await self._create_silent_audio()

    async def _create_silent_audio(self) -> str:
        """สร้างไฟล์เสียงเงียบ"""
        
        import wave
        import numpy as np
        
        duration = 30  # 30 seconds
        sample_rate = 44100
        
        # สร้าง silent audio
        audio_data = np.zeros(int(duration * sample_rate), dtype=np.int16)
        
        timestamp = int(datetime.now().timestamp())
        audio_path = f"{self.config.output_directory}/audio/silent_{timestamp}.wav"
        
        with wave.open(audio_path, 'w') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return audio_path

    async def _generate_background_music(self, content_plan: ContentPlan) -> Optional[str]:
        """สร้างหรือเลือกเพลงพื้นหลัง"""
        
        # ในการใช้งานจริงจะเชื่อมต่อกับ music generation service
        # หรือใช้ library เพลงที่มี license
        
        # ตอนนี้ return None (ไม่มีเพลงพื้นหลัง)
        return None

    async def _mix_audio_files(self, audio_files: Dict[str, str], content_plan: ContentPlan) -> str:
        """รวมไฟล์เสียงทั้งหมด"""
        
        # ถ้าไม่มีเพลงพื้นหลัง ให้ใช้เสียงบรรยายอย่างเดียว
        if "background" not in audio_files or not audio_files["background"]:
            return audio_files["voice"]
        
        # ในการใช้งานจริงจะใช้ library เช่น pydub ในการ mix audio
        # ตอนนี้ return voice audio อย่างเดียว
        return audio_files["voice"]

    async def _assemble_video(self, script: Dict[str, str], images: List[str], 
                            audio_files: Dict[str, str], content_plan: ContentPlan) -> str:
        """ประกอบวิดีโอจาก assets ทั้งหมด"""
        
        # ในการใช้งานจริงจะใช้ video_assembler.py
        # ตอนนี้สร้าง placeholder video path
        
        timestamp = int(datetime.now().timestamp())
        video_path = f"{self.config.output_directory}/videos/content_{timestamp}.mp4"
        
        # สร้างไฟล์ placeholder
        with open(video_path, 'w') as f:
            f.write(f"Video placeholder for: {content_plan.title}\n")
            f.write(f"Script: {script['hook'][:50]}...\n")
            f.write(f"Images: {len(images)} files\n")
            f.write(f"Audio: {audio_files.get('final', 'none')}\n")
        
        return video_path

    async def _optimize_for_platforms(self, content_plan: ContentPlan, 
                                    opportunity: ContentOpportunity) -> Dict[str, Any]:
        """ปรับแต่งเนื้อหาสำหรับแต่ละ platform"""
        
        metadata = {}
        
        for platform in (self.config.target_platforms or ["youtube"]):
            platform_data = {
                "title": self._optimize_title_for_platform(content_plan.title, platform),
                "description": self._generate_description_for_platform(content_plan, opportunity, platform),
                "hashtags": self._generate_hashtags_for_platform(opportunity, platform),
                "thumbnail_concept": content_plan.visual_plan.thumbnail_concept,
                "optimal_posting_time": self._suggest_posting_time(platform),
                "content_warnings": self._check_content_warnings(content_plan, platform)
            }
            
            metadata[platform] = platform_data
        
        return metadata

    def _optimize_title_for_platform(self, title: str, platform: str) -> str:
        """ปรับแต่ง title สำหรับ platform"""
        
        platform_limits = {
            "youtube": 100,
            "tiktok": 150,
            "instagram": 125,
            "facebook": 255
        }
        
        max_length = platform_limits.get(platform, 100)
        
        if len(title) > max_length:
            return title[:max_length-3] + "..."
        
        return title

    def _generate_description_for_platform(self, content_plan: ContentPlan, 
                                         opportunity: ContentOpportunity, platform: str) -> str:
        """สร้าง description สำหรับ platform"""
        
        base_description = f"""
{content_plan.description}

เกี่ยวกับ: {opportunity.trend_data.topic}
ประเภท: {opportunity.content_idea.content_type}

#ติดตาม #แชร์ #คอมเมนต์
"""
        
        platform_additions = {
            "youtube": "\n\n🔔 กดกระดิ่งเพื่อไม่พลาดคลิปใหม่!\n📱 ติดตามเราได้ที่ช่องนี้",
            "tiktok": "\n\n✨ Follow สำหรับเนื้อหาเจ๋งๆ ทุกวัน\n💫 #fyp #trending",
            "instagram": "\n\n📸 ติดตามสำหรับเนื้อหาคุณภาพ\n💝 Save ไว้ดูภึกได้นะ",
            "facebook": "\n\n👥 แชร์ให้เพื่อนๆ ดูกันด้วย\n❤️ กดไลค์ถ้าชอบ"
        }
        
        return base_description + platform_additions.get(platform, "")

    def _generate_hashtags_for_platform(self, opportunity: ContentOpportunity, platform: str) -> List[str]:
        """สร้าง hashtags สำหรับ platform"""
        
        base_hashtags = [
            f"#{opportunity.trend_data.topic.replace(' ', '')}",
            f"#{opportunity.content_idea.content_type}",
            "#ไทย", "#Thailand"
        ]
        
        platform_hashtags = {
            "youtube": ["#YouTubeThailand", "#คลิปไทย"],
            "tiktok": ["#fyp", "#trending", "#viral", "#TikTokThailand"],
            "instagram": ["#instathailand", "#อินสตาไทย", "#content"],
            "facebook": ["#เฟสบุ๊ก", "#แชร์", "#เนื้อหาดี"]
        }
        
        hashtags = base_hashtags + platform_hashtags.get(platform, [])
        
        # จำกัดจำนวน hashtags ตาม platform
        limits = {"tiktok": 10, "instagram": 30, "youtube": 15, "facebook": 20}
        max_tags = limits.get(platform, 15)
        
        return hashtags[:max_tags]

    def _suggest_posting_time(self, platform: str) -> str:
        """แนะนำเวลาโพสต์ที่เหมาะสม"""
        
        optimal_times = {
            "youtube": "19:00-22:00 (หลังเลิกงาน)",
            "tiktok": "18:00-21:00 (prime time)",
            "instagram": "11:00-13:00, 19:00-21:00",
            "facebook": "15:00-16:00, 20:00-21:00"
        }
        
        return optimal_times.get(platform, "20:00-21:00 (เวลาไทย)")

    def _check_content_warnings(self, content_plan: ContentPlan, platform: str) -> List[str]:
        """ตรวจสอบคำเตือนเนื้อหา"""
        
        warnings = []
        
        # ตรวจสอบเนื้อหาที่อาจมีปัญหา
        sensitive_keywords = ["การเมือง", "ศาสนา", "เพศ", "ความรุนแรง"]
        
        content_text = f"{content_plan.title} {content_plan.description}".lower()
        
        for keyword in sensitive_keywords:
            if keyword in content_text:
                warnings.append(f"มีเนื้อหาเกี่ยวกับ{keyword} - ควรตรวจสอบนโยบาย platform")
        
        # ตรวจสอบเฉพาะ platform
        platform_restrictions = {
            "youtube": ["copyright", "misinformation"],
            "tiktok": ["political", "adult_content"],
            "instagram": ["violence", "nudity"],
            "facebook": ["hate_speech", "false_news"]
        }
        
        restrictions = platform_restrictions.get(platform, [])
        for restriction in restrictions:
            warnings.append(f"ตรวจสอบ {restriction} สำหรับ {platform}")
        
        return warnings

    async def _update_progress(self, generation_id: str, stage: str, progress: float, message: str):
        """อัพเดทความคืบหน้า"""
        
        if generation_id in self.active_generations:
            self.active_generations[generation_id].stage = stage
            self.active_generations[generation_id].progress = progress
            self.active_generations[generation_id].message = message
            
            # ประมาณเวลาที่เหลือ
            elapsed = datetime.now() - self.active_generations[generation_id].started_at
            if progress > 0:
                total_time = elapsed / progress
                remaining = total_time - elapsed
                self.active_generations[generation_id].estimated_completion = datetime.now() + remaining

    def _calculate_estimated_cost(self, content_plan: ContentPlan) -> float:
        """คำนวณค่าใช้จ่ายโดยประมาณ"""
        
        base_costs = {
            QualityTier.BUDGET: 10.0,
            QualityTier.BALANCED: 50.0,
            QualityTier.PREMIUM: 150.0
        }
        
        base_cost = base_costs.get(self.config.quality_tier, 25.0)
        
        # ปรับตามความซับซ้อน
        complexity_multiplier = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.5
        }
        
        complexity = getattr(content_plan, 'complexity', 'medium')
        multiplier = complexity_multiplier.get(complexity, 1.5)
        
        # ปรับตามจำนวน scenes
        scene_count = len(getattr(content_plan.visual_plan, 'scenes', []))
        scene_cost = scene_count * 5.0
        
        total_cost = (base_cost * multiplier) + scene_cost
        
        return round(total_cost, 2)

    def _calculate_generation_stats(self, generation_id: str) -> Dict[str, Any]:
        """คำนวณสถิติการสร้าง"""
        
        if generation_id not in self.active_generations:
            return {}
        
        progress = self.active_generations[generation_id]
        
        total_time = datetime.now() - progress.started_at
        
        return {
            "total_generation_time": total_time.total_seconds(),
            "stages_completed": progress.stage,
            "final_progress": progress.progress,
            "quality_tier": self.config.quality_tier.value,
            "cost_estimate": 0.0,  # จะคำนวณจากการใช้ API จริง
            "platforms_optimized": len(self.config.target_platforms or []),
            "generation_timestamp": datetime.now().isoformat()
        }

    async def _save_content_assets(self, assets: ContentAssets, opportunity: ContentOpportunity, generation_id: str):
        """บันทึก content assets"""
        
        save_data = {
            "generation_id": generation_id,
            "opportunity_id": opportunity.id,
            "content_title": opportunity.content_idea.title,
            "assets": {
                "script": assets.script,
                "images": assets.images,
                "audio_files": {k: v for k, v in assets.audio_files.items() if v},
                "video_path": assets.video_path,
                "metadata": assets.metadata
            },
            "generation_stats": assets.generation_stats,
            "created_at": datetime.now().isoformat()
        }
        
        # บันทึกเป็น JSON
        save_path = f"{self.config.output_directory}/assets_{generation_id}.json"
        
        async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(save_data, indent=2, ensure_ascii=False))
        
        self.logger.info(f"Content assets saved to {save_path}")

    # Public methods สำหรับติดตามความคืบหน้า
    
    def get_generation_progress(self, generation_id: str) -> Optional[GenerationProgress]:
        """ดูความคืบหน้าการสร้าง"""
        return self.active_generations.get(generation_id)

    def get_all_active_generations(self) -> Dict[str, GenerationProgress]:
        """ดูการสร้างที่กำลังดำเนินการทั้งหมด"""
        return self.active_generations.copy()

    async def cancel_generation(self, generation_id: str) -> bool:
        """ยกเลิกการสร้างเนื้อหา"""
        
        if generation_id in self.active_generations:
            self.active_generations[generation_id].error = "Cancelled by user"
            del self.active_generations[generation_id]
            self.logger.info(f"Generation {generation_id} cancelled")
            return True
        
        return False

    # Batch processing methods
    
    async def generate_multiple_content(self, opportunities: List[ContentOpportunity]) -> List[ContentAssets]:
        """สร้างเนื้อหาหลายรายการพร้อมกัน"""
        
        self.logger.info(f"Starting batch generation for {len(opportunities)} opportunities")
        
        # สร้าง tasks สำหรับแต่ละ opportunity
        tasks = [
            self.generate_content(opportunity)
            for opportunity in opportunities
        ]
        
        # รัน parallel แต่จำกัดด้วย semaphore
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # แยก results และ errors
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "opportunity_id": opportunities[i].id,
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        if errors:
            self.logger.warning(f"Batch generation completed with {len(errors)} errors")
            for error in errors:
                self.logger.error(f"Error in {error['opportunity_id']}: {error['error']}")
        
        self.logger.info(f"Batch generation completed: {len(successful_results)} successful, {len(errors)} failed")
        
        return successful_results

    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """ดูสถิติ pipeline"""
        
        return {
            "active_generations": len(self.active_generations),
            "max_concurrent_jobs": self.config.max_concurrent_jobs,
            "quality_tier": self.config.quality_tier.value,
            "output_directory": self.config.output_directory,
            "total_content_generated": len(list(Path(self.config.output_directory).glob("assets_*.json"))),
            "pipeline_uptime": "N/A",  # จะคำนวณจากเวลาเริ่มต้น service
            "average_generation_time": "N/A",  # จะคำนวณจากสถิติที่เก็บไว้
        }


# Utility functions สำหรับการใช้งาน

async def create_content_from_opportunity(opportunity: ContentOpportunity, 
                                        quality_tier: QualityTier = QualityTier.BUDGET,
                                        target_platforms: List[str] = None) -> ContentAssets:
    """
    ฟังก์ชันสำหรับสร้างเนื้อหาจาก opportunity แบบง่าย
    """
    
    config = PipelineConfig(
        quality_tier=quality_tier,
        target_platforms=target_platforms or ["youtube"]
    )
    
    pipeline = ContentPipeline(config)
    assets = await pipeline.generate_content(opportunity)
    
    return assets


async def batch_create_content(opportunities: List[ContentOpportunity],
                             quality_tier: QualityTier = QualityTier.BUDGET,
                             max_concurrent: int = 3) -> List[ContentAssets]:
    """
    ฟังก์ชันสำหรับสร้างเนื้อหาหลายรายการ
    """
    
    config = PipelineConfig(
        quality_tier=quality_tier,
        max_concurrent_jobs=max_concurrent
    )
    
    pipeline = ContentPipeline(config)
    results = await pipeline.generate_multiple_content(opportunities)
    
    return results


if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    async def example_usage():
        from shared.models.content_opportunity import ContentOpportunity
        from shared.models.trend_data import TrendData
        from services.opportunity_engine import ContentIdea
        
        # สร้าง mock opportunity
        trend_data = TrendData(
            id="trend_001",
            source="youtube",
            topic="AI สร้างคลิป",
            keywords=["AI", "วิดีโอ", "เทคโนโลยี"],
            popularity_score=80.0,
            growth_rate=25.5,
            category="technology",
            region="TH",
            collected_at=datetime.now(),
            raw_data={}
        )
        
        content_idea = ContentIdea(
            title="สอนใช้ AI สร้างคลิปง่ายๆ ที่บ้าน",
            description="คู่มือสอนการใช้ AI ในการสร้างวิดีโอ",
            content_type="educational",
            angle="มุมมองคนไทย",
            target_audience="นักเรียน นักศึกษา",
            estimated_duration=300,
            production_complexity="medium",
            viral_potential=7.5,
            monetization_potential=8.0
        )
        
        opportunity = ContentOpportunity(
            id="opp_001",
            trend_id="trend_001",
            trend_data=trend_data,
            content_idea=content_idea,
            market_analysis=None,  # จะถูกสร้างใน pipeline
            estimated_roi=3.5,
            production_cost=75.0,
            competition_level="medium",
            priority_score=8.2,
            created_at=datetime.now(),
            status="pending"
        )
        
        # สร้างเนื้อหา
        print("🚀 เริ่มสร้างเนื้อหา...")
        
        assets = await create_content_from_opportunity(
            opportunity,
            quality_tier=QualityTier.BALANCED,
            target_platforms=["youtube", "tiktok"]
        )
        
        print("✅ สร้างเนื้อหาเสร็จแล้ว!")
        print(f"📝 Script hook: {assets.script['hook']}")
        print(f"🖼️ Images generated: {len(assets.images)}")
        print(f"🎵 Audio files: {len(assets.audio_files)}")
        print(f"🎬 Video: {assets.video_path}")
        print(f"📊 Platforms optimized: {list(assets.metadata.keys())}")
    
    # รัน example
    asyncio.run(example_usage())