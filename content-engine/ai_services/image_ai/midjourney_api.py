"""
Midjourney API Image Generation Service
Implementation of BaseImageAI for Midjourney API (via unofficial API or Discord bot)
"""

import asyncio
import aiohttp
import aiofiles
import logging
import os
import json
import uuid
import time
import re
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
import base64

from .base_image_ai import (
    BaseImageAI, 
    ImageGenerationRequest, 
    ImageStyle, 
    AspectRatio,
    ImageQuality,
    ImageProcessingConfig
)
from shared.models.quality_tier import QualityTier
from shared.utils.logger import get_logger
from shared.utils.error_handler import handle_errors, ImageGenerationError


class MidjourneyConfig:
    """การตั้งค่าเฉพาะสำหรับ Midjourney API"""
    
    def __init__(self):
        # API Configuration
        self.api_endpoint = "https://api.midjourney.com"  # หรือ unofficial API endpoint
        self.api_key = None
        self.discord_token = None  # สำหรับ Discord bot integration
        self.server_id = None  # Discord server ID
        self.channel_id = None  # Discord channel ID
        
        # Generation Settings
        self.default_version = "6.0"  # Midjourney version
        self.available_versions = ["5.2", "6.0", "6.1", "niji", "niji-6"]
        self.max_concurrent_jobs = 3
        self.generation_timeout = 600  # 10 นาที
        self.polling_interval = 10  # วินาที
        
        # Quality Settings
        self.default_quality = 1.0  # --q parameter
        self.default_stylize = 100  # --s parameter
        self.enable_remix = False
        self.enable_fast_mode = True  # fast vs relax mode
        
        # Advanced Features
        self.enable_upscaling = True
        self.enable_variations = True
        self.enable_describe = False  # reverse engineering prompts from images
        self.enable_blend = False  # image blending


class MidjourneyParameters:
    """พารามิเตอร์เฉพาะของ Midjourney"""
    
    def __init__(self):
        self.aspect_ratio = "1:1"  # --ar
        self.chaos = None  # --chaos 0-100
        self.quality = None  # --q 0.25, 0.5, 1, 2
        self.stylize = None  # --s 0-1000
        self.weird = None  # --weird 0-3000 (v6.1)
        self.tile = False  # --tile
        self.no_text = False  # --no text
        self.version = None  # --v
        self.niji = False  # --niji
        self.style_raw = False  # --style raw
        self.stop = None  # --stop 10-100


class MidjourneyAPI(BaseImageAI):
    """
    Midjourney implementation with Discord integration
    """
    
    def __init__(self, api_key: str = None,
                 discord_token: str = None,
                 midjourney_config: MidjourneyConfig = None,
                 quality_tier: QualityTier = QualityTier.BUDGET,
                 processing_config: ImageProcessingConfig = None):
        
        # Setup configs
        self.midjourney_config = midjourney_config or MidjourneyConfig()
        self.midjourney_config.api_key = api_key
        self.midjourney_config.discord_token = discord_token
        
        super().__init__(quality_tier, processing_config)
        
        self.session = None
        self.discord_session = None
        self.active_jobs: Dict[str, Dict] = {}
        
        # Midjourney-specific settings
        self.parameter_presets = self._load_parameter_presets()
        self.style_mappings = self._load_style_mappings()
        self.prompt_enhancers = self._load_prompt_enhancers()
        self.command_templates = self._load_command_templates()

    def _initialize_service(self):
        """Initialize Midjourney service"""
        
        if not self.midjourney_config.api_key and not self.midjourney_config.discord_token:
            self.logger.warning("No API key or Discord token provided for Midjourney")

    def _load_parameter_presets(self) -> Dict[QualityTier, MidjourneyParameters]:
        """โหลด parameter presets สำหรับแต่ละ quality tier"""
        
        presets = {}
        
        # Budget tier
        budget_params = MidjourneyParameters()
        budget_params.quality = 0.5
        budget_params.stylize = 50
        budget_params.version = "5.2"
        presets[QualityTier.BUDGET] = budget_params
        
        # Balanced tier
        balanced_params = MidjourneyParameters()
        balanced_params.quality = 1.0
        balanced_params.stylize = 100
        balanced_params.version = "6.0"
        presets[QualityTier.BALANCED] = balanced_params
        
        # Premium tier
        premium_params = MidjourneyParameters()
        premium_params.quality = 2.0
        premium_params.stylize = 250
        premium_params.version = "6.1"
        premium_params.weird = 500
        presets[QualityTier.PREMIUM] = premium_params
        
        return presets

    def _load_style_mappings(self) -> Dict[ImageStyle, Dict]:
        """โหลด style mappings สำหรับ Midjourney"""
        
        return {
            ImageStyle.REALISTIC: {
                "prompt_suffix": "photorealistic, hyperrealistic, photography",
                "negative_terms": ["cartoon", "anime", "painting", "illustration"],
                "stylize": 25,
                "version": "6.0",
                "style_raw": True
            },
            ImageStyle.CARTOON: {
                "prompt_suffix": "cartoon style, animation, colorful illustration",
                "negative_terms": ["realistic", "photographic"],
                "stylize": 150,
                "version": "6.0",
                "niji": False
            },
            ImageStyle.ANIME: {
                "prompt_suffix": "anime style, manga illustration",
                "negative_terms": ["realistic", "western"],
                "stylize": 200,
                "version": "niji-6",
                "niji": True
            },
            ImageStyle.MINIMALIST: {
                "prompt_suffix": "minimalist, clean, simple, geometric",
                "negative_terms": ["cluttered", "busy", "complex"],
                "stylize": 50,
                "version": "6.0"
            },
            ImageStyle.DIGITAL_ART: {
                "prompt_suffix": "digital art, concept art, detailed illustration",
                "negative_terms": ["photograph", "realistic"],
                "stylize": 200,
                "version": "6.0"
            },
            ImageStyle.CONCEPT_ART: {
                "prompt_suffix": "concept art, matte painting, cinematic",
                "negative_terms": ["amateur", "sketch"],
                "stylize": 300,
                "version": "6.0"
            }
        }

    def _load_prompt_enhancers(self) -> Dict[str, List[str]]:
        """โหลด prompt enhancers สำหรับ Midjourney"""
        
        return {
            "lighting": [
                "golden hour lighting", "studio lighting", "natural lighting",
                "dramatic lighting", "soft lighting", "cinematic lighting"
            ],
            "camera": [
                "shot on Canon EOS R5", "85mm lens", "wide angle",
                "macro photography", "portrait lens", "telephoto"
            ],
            "quality": [
                "ultra detailed", "highly detailed", "masterpiece",
                "professional", "award winning", "trending on artstation"
            ],
            "composition": [
                "rule of thirds", "symmetrical", "centered composition",
                "dynamic composition", "leading lines"
            ],
            "mood": [
                "ethereal", "mystical", "epic", "serene", "dramatic",
                "whimsical", "atmospheric", "moody"
            ]
        }

    def _load_command_templates(self) -> Dict[str, str]:
        """โหลด command templates สำหรับ Midjourney"""
        
        return {
            "imagine": "/imagine prompt: {prompt} {parameters}",
            "upscale": "/upscale {job_id} {upscale_index}",
            "variation": "/variation {job_id} {variation_index}",
            "describe": "/describe {image_url}",
            "blend": "/blend {image1_url} {image2_url} {parameters}",
            "remix": "/remix {job_id} {new_prompt}"
        }

    def _get_service_name(self) -> str:
        return "Midjourney"

    def _get_model_name(self) -> str:
        return f"Midjourney {self.midjourney_config.default_version}"

    async def _ensure_session(self):
        """สร้าง HTTP session ถ้ายังไม่มี"""
        
        if not self.session:
            headers = {}
            
            if self.midjourney_config.api_key:
                headers["Authorization"] = f"Bearer {self.midjourney_config.api_key}"
            
            self.session = aiohttp.ClientSession(headers=headers)

    async def _generate_image_internal(self, request: ImageGenerationRequest) -> str:
        """สร้างภาพด้วย Midjourney"""
        
        await self._ensure_session()
        
        # เตรียม Midjourney prompt
        midjourney_prompt = await self._prepare_midjourney_prompt(request)
        
        # ส่ง generation request
        job_id = await self._submit_imagine_command(midjourney_prompt)
        
        # รอผลลัพธ์
        job_result = await self._wait_for_generation_complete(job_id)
        
        # ดาวน์โหลดภาพ
        image_path = await self._download_midjourney_image(job_result)
        
        return image_path

    async def _prepare_midjourney_prompt(self, request: ImageGenerationRequest) -> str:
        """เตรียม prompt สำหรับ Midjourney"""
        
        # Base prompt
        prompt_parts = [request.prompt]
        
        # เพิ่ม style enhancements
        style_mapping = self.style_mappings.get(request.style, {})
        if "prompt_suffix" in style_mapping:
            prompt_parts.append(style_mapping["prompt_suffix"])
        
        # เพิ่ม quality enhancers ถ้าเป็น premium tier
        if self.quality_tier in [QualityTier.BALANCED, QualityTier.PREMIUM]:
            enhancers = self.prompt_enhancers
            
            # เลือก enhancers อย่างสุ่ม
            import random
            selected_quality = random.choice(enhancers["quality"])
            selected_lighting = random.choice(enhancers["lighting"])
            
            prompt_parts.extend([selected_quality, selected_lighting])
        
        # รวม prompt
        main_prompt = ", ".join(prompt_parts)
        
        # เพิ่ม negative prompt (Midjourney style)
        negative_terms = []
        if request.negative_prompt:
            negative_terms.append(request.negative_prompt)
        
        if "negative_terms" in style_mapping:
            negative_terms.extend(style_mapping["negative_terms"])
        
        if negative_terms:
            main_prompt += f" --no {', '.join(negative_terms)}"
        
        # เพิ่ม parameters
        parameters = self._build_parameters_string(request, style_mapping)
        main_prompt += parameters
        
        return main_prompt

    def _build_parameters_string(self, request: ImageGenerationRequest, 
                                style_mapping: Dict) -> str:
        """สร้าง parameters string สำหรับ Midjourney"""
        
        params = []
        
        # Aspect ratio
        if request.aspect_ratio:
            ar = self._convert_aspect_ratio(request.aspect_ratio)
            params.append(f"--ar {ar}")
        
        # Quality
        preset_params = self.parameter_presets[self.quality_tier]
        quality = request.additional_params.get("quality") if request.additional_params else preset_params.quality
        if quality:
            params.append(f"--q {quality}")
        
        # Stylize
        stylize = style_mapping.get("stylize", preset_params.stylize)
        if stylize:
            params.append(f"--s {stylize}")
        
        # Version
        version = style_mapping.get("version", preset_params.version)
        if version:
            if version.startswith("niji"):
                params.append(f"--{version}")
            else:
                params.append(f"--v {version}")
        
        # Style raw (for photorealistic)
        if style_mapping.get("style_raw", False):
            params.append("--style raw")
        
        # Chaos (for variety)
        if request.additional_params and "chaos" in request.additional_params:
            chaos = request.additional_params["chaos"]
            params.append(f"--chaos {chaos}")
        
        # Weird (v6.1 feature)
        if (preset_params.weird and 
            version in ["6.1"] and 
            request.style in [ImageStyle.DIGITAL_ART, ImageStyle.CONCEPT_ART]):
            params.append(f"--weird {preset_params.weird}")
        
        # Seed
        if request.seed:
            params.append(f"--seed {request.seed}")
        
        # Fast/Relax mode
        if not self.midjourney_config.enable_fast_mode:
            params.append("--relax")
        
        return " " + " ".join(params) if params else ""

    def _convert_aspect_ratio(self, aspect_ratio: AspectRatio) -> str:
        """แปลง AspectRatio enum เป็น Midjourney format"""
        
        conversions = {
            AspectRatio.SQUARE: "1:1",
            AspectRatio.LANDSCAPE: "16:9",
            AspectRatio.PORTRAIT: "9:16",
            AspectRatio.WIDE: "21:9",
            AspectRatio.CLASSIC: "4:3",
            AspectRatio.VERTICAL: "3:4"
        }
        
        return conversions.get(aspect_ratio, "1:1")

    async def _submit_imagine_command(self, prompt: str) -> str:
        """ส่ง /imagine command ไปยัง Midjourney"""
        
        # ถ้าใช้ official API
        if self.midjourney_config.api_key:
            return await self._submit_via_api(prompt)
        
        # ถ้าใช้ Discord integration
        elif self.midjourney_config.discord_token:
            return await self._submit_via_discord(prompt)
        
        else:
            # ใช้ unofficial API หรือ mock
            return await self._submit_via_unofficial_api(prompt)

    async def _submit_via_api(self, prompt: str) -> str:
        """ส่งผ่าน official Midjourney API (ถ้ามี)"""
        
        url = urljoin(self.midjourney_config.api_endpoint, "/v1/imagine")
        
        payload = {
            "prompt": prompt,
            "webhook_url": None,  # สำหรับ callback
            "webhook_type": "progress"
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ImageGenerationError(f"Midjourney API error: {response.status} - {error_text}")
                
                data = await response.json()
                job_id = data.get("job_id")
                
                if not job_id:
                    raise ImageGenerationError("No job ID returned from Midjourney API")
                
                self.logger.info(f"Midjourney job submitted: {job_id}")
                return job_id
                
        except aiohttp.ClientError as e:
            raise ImageGenerationError(f"Failed to submit to Midjourney API: {e}")

    async def _submit_via_discord(self, prompt: str) -> str:
        """ส่งผ่าน Discord bot integration"""
        
        # Discord API integration
        discord_api = "https://discord.com/api/v10"
        
        headers = {
            "Authorization": f"Bot {self.midjourney_config.discord_token}",
            "Content-Type": "application/json"
        }
        
        # Send message to Discord channel
        message_data = {
            "content": f"/imagine {prompt}",
            "tts": False
        }
        
        url = f"{discord_api}/channels/{self.midjourney_config.channel_id}/messages"
        
        try:
            if not self.discord_session:
                self.discord_session = aiohttp.ClientSession(headers=headers)
            
            async with self.discord_session.post(url, json=message_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ImageGenerationError(f"Discord API error: {response.status} - {error_text}")
                
                data = await response.json()
                message_id = data.get("id")
                
                # สร้าง job_id จาก message_id
                job_id = f"discord_{message_id}_{int(time.time())}"
                
                self.logger.info(f"Discord command sent: {job_id}")
                return job_id
                
        except aiohttp.ClientError as e:
            raise ImageGenerationError(f"Failed to send Discord command: {e}")

    async def _submit_via_unofficial_api(self, prompt: str) -> str:
        """ส่งผ่าน unofficial API หรือสร้าง mock job"""
        
        # Mock implementation สำหรับการทดสอบ
        job_id = f"mock_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        # เก็บ job info
        self.active_jobs[job_id] = {
            "prompt": prompt,
            "status": "submitted",
            "created_at": datetime.now(),
            "progress": 0
        }
        
        self.logger.info(f"Mock Midjourney job created: {job_id}")
        return job_id

    async def _wait_for_generation_complete(self, job_id: str) -> Dict[str, Any]:
        """รอให้การสร้างภาพเสร็จสมบูรณ์"""
        
        start_time = time.time()
        timeout = self.midjourney_config.generation_timeout
        
        while time.time() - start_time < timeout:
            try:
                status = await self._check_job_status(job_id)
                
                if status["status"] == "completed":
                    self.logger.info(f"Midjourney job completed: {job_id}")
                    return status
                
                elif status["status"] == "failed":
                    error_msg = status.get("error", "Unknown error")
                    raise ImageGenerationError(f"Midjourney generation failed: {error_msg}")
                
                elif status["status"] in ["submitted", "in_progress"]:
                    progress = status.get("progress", 0)
                    self.logger.debug(f"Job {job_id} progress: {progress}%")
                    
                    await asyncio.sleep(self.midjourney_config.polling_interval)
                    continue
                
                else:
                    self.logger.warning(f"Unknown job status: {status['status']}")
                    await asyncio.sleep(self.midjourney_config.polling_interval)
                    continue
                    
            except Exception as e:
                self.logger.warning(f"Error checking job status: {e}")
                await asyncio.sleep(self.midjourney_config.polling_interval)
                continue
        
        raise ImageGenerationError(f"Midjourney generation timeout for job {job_id}")

    async def _check_job_status(self, job_id: str) -> Dict[str, Any]:
        """ตรวจสอบสถานะของ job"""
        
        # ถ้าเป็น mock job
        if job_id.startswith("mock_"):
            return await self._check_mock_job_status(job_id)
        
        # ถ้าใช้ official API
        if self.midjourney_config.api_key:
            return await self._check_api_job_status(job_id)
        
        # ถ้าใช้ Discord
        elif self.midjourney_config.discord_token:
            return await self._check_discord_job_status(job_id)
        
        else:
            raise ImageGenerationError("No valid method to check job status")

    async def _check_mock_job_status(self, job_id: str) -> Dict[str, Any]:
        """ตรวจสอบสถานะ mock job"""
        
        if job_id not in self.active_jobs:
            return {"status": "failed", "error": "Job not found"}
        
        job = self.active_jobs[job_id]
        elapsed = (datetime.now() - job["created_at"]).total_seconds()
        
        # จำลองความคืบหน้า
        if elapsed < 30:
            progress = int(elapsed / 30 * 100)
            job["progress"] = progress
            return {"status": "in_progress", "progress": progress}
        else:
            # จำลองว่าเสร็จแล้ว
            return {
                "status": "completed",
                "progress": 100,
                "image_urls": [
                    f"https://example.com/midjourney_result_{job_id}.png"
                ],
                "upscale_urls": [],
                "variation_urls": []
            }

    async def _check_api_job_status(self, job_id: str) -> Dict[str, Any]:
        """ตรวจสอบสถานะผ่าน official API"""
        
        url = urljoin(self.midjourney_config.api_endpoint, f"/v1/jobs/{job_id}")
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {"status": "failed", "error": f"API error {response.status}"}
                
                data = await response.json()
                return {
                    "status": data.get("status", "unknown"),
                    "progress": data.get("progress", 0),
                    "image_urls": data.get("image_urls", []),
                    "upscale_urls": data.get("upscale_urls", []),
                    "variation_urls": data.get("variation_urls", []),
                    "error": data.get("error")
                }
                
        except aiohttp.ClientError as e:
            return {"status": "failed", "error": str(e)}

    async def _check_discord_job_status(self, job_id: str) -> Dict[str, Any]:
        """ตรวจสอบสถานะผ่าน Discord"""
        
        # Discord integration ต้องการการ polling messages
        # และ parsing ผลลัพธ์จาก Midjourney bot responses
        
        # Simplified implementation
        message_id = job_id.split("_")[1]
        
        discord_api = "https://discord.com/api/v10"
        url = f"{discord_api}/channels/{self.midjourney_config.channel_id}/messages"
        
        try:
            async with self.discord_session.get(url, params={"after": message_id, "limit": 50}) as response:
                if response.status != 200:
                    return {"status": "failed", "error": f"Discord API error {response.status}"}
                
                messages = await response.json()
                
                # หา response จาก Midjourney bot
                for message in messages:
                    if (message.get("author", {}).get("username") == "Midjourney Bot" and
                        message.get("attachments")):
                        
                        # พบภาพที่สร้างแล้ว
                        attachments = message["attachments"]
                        image_urls = [att["url"] for att in attachments if att.get("url")]
                        
                        return {
                            "status": "completed",
                            "progress": 100,
                            "image_urls": image_urls,
                            "upscale_urls": [],
                            "variation_urls": []
                        }
                
                # ยังไม่เจอผลลัพธ์
                return {"status": "in_progress", "progress": 50}
                
        except aiohttp.ClientError as e:
            return {"status": "failed", "error": str(e)}

    async def _download_midjourney_image(self, job_result: Dict[str, Any]) -> str:
        """ดาวน์โหลดภาพจาก Midjourney"""
        
        image_urls = job_result.get("image_urls", [])
        
        if not image_urls:
            raise ImageGenerationError("No image URLs in job result")
        
        # ดาวน์โหลดภาพแรก
        image_url = image_urls[0]
        
        if image_url.startswith("https://example.com"):
            # Mock URL - สร้างภาพ placeholder
            return await self._create_mock_midjourney_image(image_url)
        
        try:
            async with self.session.get(image_url) as response:
                if response.status != 200:
                    raise ImageGenerationError(f"Failed to download image: {response.status}")
                
                # สร้างชื่อไฟล์
                timestamp = int(datetime.now().timestamp())
                filename = f"midjourney_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                image_path = os.path.join(self.config.output_directory, filename)
                
                # ดาวน์โหลดและบันทึก
                async with aiofiles.open(image_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                self.logger.info(f"Midjourney image downloaded: {image_path}")
                return image_path
                
        except aiohttp.ClientError as e:
            raise ImageGenerationError(f"Failed to download Midjourney image: {e}")

    async def _create_mock_midjourney_image(self, mock_url: str) -> str:
        """สร้างภาพ mock สำหรับการทดสอบ"""
        
        from PIL import Image, ImageDraw, ImageFont
        
        # สร้างภาพ mock
        width, height = 1024, 1024
        image = Image.new('RGB', (width, height), color='lightcyan')
        draw = ImageDraw.Draw(image)
        
        # เขียนข้อความ
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        text_lines = [
            "Midjourney Style",
            "Generated Image",
            f"Mock Result",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ]
        
        y_offset = height // 4
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            
            draw.text((x, y_offset), line, fill='darkblue', font=font)
            y_offset += 80
        
        # เพิ่ม border สไตล์ Midjourney
        border_width = 10
        draw.rectangle([0, 0, width-1, height-1], outline='darkblue', width=border_width)
        
        # บันทึกภาพ
        timestamp = int(datetime.now().timestamp())
        filename = f"midjourney_mock_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        image_path = os.path.join(self.config.output_directory, filename)
        
        image.save(image_path)
        return image_path

    # Midjourney-specific methods

    async def upscale_image(self, job_id: str, upscale_index: int = 1) -> str:
        """
        Upscale ภาพจาก grid result
        """
        
        if not self.midjourney_config.enable_upscaling:
            raise ImageGenerationError("Upscaling not enabled")
        
        upscale_command = f"/upscale {job_id} U{upscale_index}"
        
        # ส่ง upscale command
        upscale_job_id = await self._submit_command(upscale_command)
        
        # รอผลลัพธ์
        result = await self._wait_for_generation_complete(upscale_job_id)
        
        # ดาวน์โหลดภาพ upscale
        return await self._download_midjourney_image(result)

    async def create_variations(self, job_id: str, variation_index: int = 1) -> str:
        """
        สร้าง variations จาก grid result
        """
        
        if not self.midjourney_config.enable_variations:
            raise ImageGenerationError("Variations not enabled")
        
        variation_command = f"/variation {job_id} V{variation_index}"
        
        # ส่ง variation command
        variation_job_id = await self._submit_command(variation_command)
        
        # รอผลลัพธ