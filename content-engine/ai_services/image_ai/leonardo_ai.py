"""
Leonardo AI Image Generation Service
Implementation of BaseImageAI for Leonardo AI platform
"""

import asyncio
import aiohttp
import aiofiles
import logging
import os
import json
import uuid
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

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


class LeonardoConfig:
    """การตั้งค่าเฉพาะสำหรับ Leonardo AI"""
    
    def __init__(self):
        self.api_endpoint = "https://cloud.leonardo.ai/api/rest/v1"
        self.api_key = None
        self.default_model_id = "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3"  # Leonardo Creative
        self.available_models = {
            "leonardo_creative": {
                "id": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
                "name": "Leonardo Creative",
                "description": "Versatile model for creative artwork",
                "max_resolution": 1024,
                "supports_negative_prompt": True,
                "cost_multiplier": 1.0
            },
            "leonardo_select": {
                "id": "cd2b2a15-9760-4174-a5ff-4d2925057376", 
                "name": "Leonardo Select",
                "description": "High-quality photorealistic images",
                "max_resolution": 768,
                "supports_negative_prompt": True,
                "cost_multiplier": 1.2
            },
            "leonardo_signature": {
                "id": "291be633-cb24-434f-898f-e662799936ad",
                "name": "Leonardo Signature",
                "description": "Premium artistic style",
                "max_resolution": 1024,
                "supports_negative_prompt": True,
                "cost_multiplier": 1.5
            },
            "dreamshaper": {
                "id": "ac614f96-1082-45bf-be9d-757f2d31c174",
                "name": "DreamShaper",
                "description": "Fantasy and creative content",
                "max_resolution": 768,
                "supports_negative_prompt": True,
                "cost_multiplier": 1.1
            },
            "stable_diffusion_xl": {
                "id": "b820ea11-02bf-4652-97ae-9ac0cc00593d",
                "name": "Stable Diffusion XL",
                "description": "SDXL on Leonardo platform",
                "max_resolution": 1024,
                "supports_negative_prompt": True,
                "cost_multiplier": 1.3
            }
        }
        self.max_images_per_request = 8
        self.enable_alchemy = True  # ใช้ Alchemy enhancement
        self.enable_prompt_magic = True  # ปรับปรุง prompt อัตโนมัติ
        self.enable_photoreal = False  # PhotoReal mode
        self.generation_timeout = 300  # 5 นาที
        self.max_retries = 3
        self.polling_interval = 5  # วินาที


class LeonardoAI(BaseImageAI):
    """
    Leonardo AI implementation with advanced features
    """
    
    def __init__(self, api_key: str,
                 leonardo_config: LeonardoConfig = None,
                 quality_tier: QualityTier = QualityTier.BUDGET,
                 processing_config: ImageProcessingConfig = None):
        
        # Setup configs
        self.leonardo_config = leonardo_config or LeonardoConfig()
        self.leonardo_config.api_key = api_key
        
        super().__init__(quality_tier, processing_config)
        
        self.session = None
        self.user_info = None
        
        # Leonardo-specific settings
        self.generation_presets = self._load_generation_presets()
        self.style_mappings = self._load_style_mappings()
        self.preset_models = self._load_preset_models()

    def _initialize_service(self):
        """Initialize Leonardo AI service"""
        
        if not self.leonardo_config.api_key:
            raise ImageGenerationError("Leonardo AI API key is required")
        
        # จะตรวจสอบ API key และโหลด user info ใน first request

    def _load_generation_presets(self) -> Dict[QualityTier, Dict]:
        """โหลด generation presets สำหรับแต่ละ quality tier"""
        
        return {
            QualityTier.BUDGET: {
                "guidance_scale": 7,
                "num_inference_steps": 10,
                "width": 512,
                "height": 512,
                "num_images": 1,
                "enable_alchemy": False,
                "enable_prompt_magic": False,
                "scheduler": "EULER_DISCRETE"
            },
            QualityTier.BALANCED: {
                "guidance_scale": 7,
                "num_inference_steps": 15,
                "width": 768,
                "height": 768,
                "num_images": 2,
                "enable_alchemy": True,
                "enable_prompt_magic": True,
                "scheduler": "DPM_SOLVER"
            },
            QualityTier.PREMIUM: {
                "guidance_scale": 10,
                "num_inference_steps": 25,
                "width": 1024,
                "height": 1024,
                "num_images": 4,
                "enable_alchemy": True,
                "enable_prompt_magic": True,
                "scheduler": "KLMS"
            }
        }

    def _load_style_mappings(self) -> Dict[ImageStyle, Dict]:
        """โหลด style mappings สำหรับ Leonardo AI"""
        
        return {
            ImageStyle.REALISTIC: {
                "preferred_models": ["leonardo_select", "stable_diffusion_xl"],
                "prompt_enhancement": "photorealistic, highly detailed, professional photography",
                "negative_prompt": "cartoon, anime, painting, sketch, artistic",
                "enable_photoreal": True,
                "guidance_scale": 7
            },
            ImageStyle.CARTOON: {
                "preferred_models": ["leonardo_creative", "dreamshaper"],
                "prompt_enhancement": "cartoon style, animated, colorful illustration",
                "negative_prompt": "realistic, photographic, dark, gritty",
                "enable_photoreal": False,
                "guidance_scale": 8
            },
            ImageStyle.ANIME: {
                "preferred_models": ["leonardo_creative", "dreamshaper"],
                "prompt_enhancement": "anime style, manga, japanese animation, cel shading",
                "negative_prompt": "realistic, western cartoon, 3d render",
                "enable_photoreal": False,
                "guidance_scale": 9
            },
            ImageStyle.MINIMALIST: {
                "preferred_models": ["leonardo_creative"],
                "prompt_enhancement": "minimalist, clean, simple, geometric, white background",
                "negative_prompt": "cluttered, busy, complex, detailed background",
                "enable_photoreal": False,
                "guidance_scale": 6
            },
            ImageStyle.DIGITAL_ART: {
                "preferred_models": ["leonardo_signature", "leonardo_creative"],
                "prompt_enhancement": "digital art, concept art, detailed illustration, artstation",
                "negative_prompt": "photograph, realistic, amateur, sketch",
                "enable_photoreal": False,
                "guidance_scale": 8
            },
            ImageStyle.CONCEPT_ART: {
                "preferred_models": ["leonardo_signature", "dreamshaper"],
                "prompt_enhancement": "concept art, matte painting, detailed environment design",
                "negative_prompt": "amateur, low quality, blurry",
                "enable_photoreal": False,
                "guidance_scale": 9
            }
        }

    def _load_preset_models(self) -> Dict[str, str]:
        """โหลด preset models สำหรับงานเฉพาะ"""
        
        return {
            "portrait": "leonardo_select",
            "landscape": "stable_diffusion_xl", 
            "fantasy": "dreamshaper",
            "architecture": "leonardo_creative",
            "character": "leonardo_signature",
            "abstract": "leonardo_creative"
        }

    def _get_service_name(self) -> str:
        return "Leonardo AI"

    def _get_model_name(self) -> str:
        model_key = self._get_model_key_from_id(self.leonardo_config.default_model_id)
        if model_key:
            return self.leonardo_config.available_models[model_key]["name"]
        return "Leonardo Creative"

    def _get_model_key_from_id(self, model_id: str) -> Optional[str]:
        """หา model key จาก model ID"""
        
        for key, model_info in self.leonardo_config.available_models.items():
            if model_info["id"] == model_id:
                return key
        return None

    async def _ensure_session(self):
        """สร้าง HTTP session ถ้ายังไม่มี"""
        
        if not self.session:
            headers = {
                "Authorization": f"Bearer {self.leonardo_config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            self.session = aiohttp.ClientSession(headers=headers)
            
            # ตรวจสอบ API key และโหลด user info
            await self._load_user_info()

    async def _load_user_info(self):
        """โหลดข้อมูล user และตรวจสอบ API key"""
        
        try:
            url = urljoin(self.leonardo_config.api_endpoint, "/me")
            
            async with self.session.get(url) as response:
                if response.status == 401:
                    raise ImageGenerationError("Invalid Leonardo AI API key")
                elif response.status != 200:
                    raise ImageGenerationError(f"Failed to authenticate: {response.status}")
                
                self.user_info = await response.json()
                
                # ตรวจสอบ credits
                user_data = self.user_info.get("user_details", [{}])[0]
                token_renewal_date = user_data.get("tokenRenewalDate")
                api_credit = user_data.get("apiCredit", 0)
                
                self.logger.info(f"Leonardo AI authenticated. Credits: {api_credit}")
                
                if api_credit <= 0:
                    self.logger.warning("Leonardo AI credits are low or exhausted")
                
        except aiohttp.ClientError as e:
            raise ImageGenerationError(f"Failed to connect to Leonardo AI: {e}")

    async def _generate_image_internal(self, request: ImageGenerationRequest) -> str:
        """สร้างภาพด้วย Leonardo AI"""
        
        await self._ensure_session()
        
        # เตรียม generation request
        generation_request = await self._prepare_generation_request(request)
        
        # ส่ง generation request
        generation_id = await self._submit_generation(generation_request)
        
        # รอและดาวน์โหลดผลลัพธ์
        image_urls = await self._wait_for_generation(generation_id)
        
        # ดาวน์โหลดภาพแรก (หรือทั้งหมดถ้าเป็น batch)
        image_path = await self._download_generated_image(image_urls[0], generation_id)
        
        return image_path

    async def _prepare_generation_request(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        """เตรียม generation request สำหรับ Leonardo AI"""
        
        # เลือก model ที่เหมาะสม
        model_id = await self._select_optimal_model(request)
        
        # ได้ preset สำหรับ quality tier
        preset = self.generation_presets[self.quality_tier]
        
        # ได้ style mapping
        style_mapping = self.style_mappings.get(request.style, {})
        
        # เตรียม prompt
        enhanced_prompt = request.prompt
        if "prompt_enhancement" in style_mapping:
            enhanced_prompt = f"{enhanced_prompt}, {style_mapping['prompt_enhancement']}"
        
        # เตรียม negative prompt
        negative_prompt = request.negative_prompt or ""
        if "negative_prompt" in style_mapping:
            if negative_prompt:
                negative_prompt = f"{negative_prompt}, {style_mapping['negative_prompt']}"
            else:
                negative_prompt = style_mapping["negative_prompt"]
        
        # คำนวณขนาดภาพ
        width, height = self._calculate_optimal_dimensions(request, model_id)
        
        # สร้าง generation request
        generation_request = {
            "prompt": enhanced_prompt,
            "modelId": model_id,
            "width": width,
            "height": height,
            "num_images": min(preset["num_images"], request.additional_params.get("num_images", 1) if request.additional_params else 1),
            "guidance_scale": request.guidance_scale or style_mapping.get("guidance_scale", preset["guidance_scale"]),
            "num_inference_steps": request.steps or preset["num_inference_steps"],
            "scheduler": preset["scheduler"]
        }
        
        # เพิ่ม negative prompt ถ้ามี
        if negative_prompt:
            generation_request["negative_prompt"] = negative_prompt
        
        # เพิ่ม seed ถ้ามี
        if request.seed:
            generation_request["seed"] = request.seed
        
        # เพิ่ม Leonardo-specific features
        if self.leonardo_config.enable_alchemy and preset["enable_alchemy"]:
            generation_request["alchemy"] = True
        
        if self.leonardo_config.enable_prompt_magic and preset["enable_prompt_magic"]:
            generation_request["promptMagic"] = True
        
        # เพิ่ม PhotoReal mode สำหรับ realistic images
        if (self.leonardo_config.enable_photoreal and 
            request.style == ImageStyle.REALISTIC and 
            style_mapping.get("enable_photoreal", False)):
            generation_request["photoReal"] = True
            generation_request["photoRealVersion"] = "v2"
        
        return generation_request

    async def _select_optimal_model(self, request: ImageGenerationRequest) -> str:
        """เลือก model ที่เหมาะสมสำหรับ request"""
        
        # ถ้าระบุ model แล้ว
        if request.model and request.model in self.leonardo_config.available_models:
            return self.leonardo_config.available_models[request.model]["id"]
        
        # เลือกจาก style mapping
        style_mapping = self.style_mappings.get(request.style, {})
        preferred_models = style_mapping.get("preferred_models", [])
        
        if preferred_models:
            # เลือก model แรกที่มี
            for model_key in preferred_models:
                if model_key in self.leonardo_config.available_models:
                    return self.leonardo_config.available_models[model_key]["id"]
        
        # ใช้ default model
        return self.leonardo_config.default_model_id

    def _calculate_optimal_dimensions(self, request: ImageGenerationRequest, model_id: str) -> tuple:
        """คำนวณขนาดภาพที่เหมาะสม"""
        
        # หา model info
        model_info = None
        for model_data in self.leonardo_config.available_models.values():
            if model_data["id"] == model_id:
                model_info = model_data
                break
        
        max_resolution = model_info["max_resolution"] if model_info else 768
        
        # ถ้าระบุขนาดแล้ว
        if request.width and request.height:
            width = min(request.width, max_resolution)
            height = min(request.height, max_resolution)
            return width, height
        
        # คำนวณจาก aspect ratio
        preset = self.generation_presets[self.quality_tier]
        base_size = min(preset["width"], max_resolution)
        
        if request.aspect_ratio == AspectRatio.SQUARE:
            return base_size, base_size
        elif request.aspect_ratio == AspectRatio.LANDSCAPE:
            width = base_size
            height = int(base_size * 9 / 16)
        elif request.aspect_ratio == AspectRatio.PORTRAIT:
            width = int(base_size * 9 / 16)
            height = base_size
        elif request.aspect_ratio == AspectRatio.WIDE:
            width = base_size
            height = int(base_size * 9 / 21)
        else:  # default to square
            width = height = base_size
        
        # ปรับให้เป็นเลขคู่
        width = width - (width % 8)
        height = height - (height % 8)
        
        return width, height

    async def _submit_generation(self, generation_request: Dict[str, Any]) -> str:
        """ส่ง generation request และได้ generation ID"""
        
        url = urljoin(self.leonardo_config.api_endpoint, "/generations")
        
        try:
            async with self.session.post(url, json=generation_request) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Generation request failed: {response.status} - {error_text}")
                    
                    if response.status == 400:
                        raise ImageGenerationError("Invalid generation parameters")
                    elif response.status == 402:
                        raise ImageGenerationError("Insufficient Leonardo AI credits")
                    elif response.status == 429:
                        raise ImageGenerationError("Rate limit exceeded")
                    else:
                        raise ImageGenerationError(f"Generation request failed: {response.status}")
                
                response_data = await response.json()
                generation_id = response_data.get("sdGenerationJob", {}).get("generationId")
                
                if not generation_id:
                    raise ImageGenerationError("No generation ID returned")
                
                self.logger.info(f"Generation submitted: {generation_id}")
                return generation_id
                
        except aiohttp.ClientError as e:
            raise ImageGenerationError(f"Failed to submit generation: {e}")

    async def _wait_for_generation(self, generation_id: str) -> List[str]:
        """รอให้การสร้างภาพเสร็จและได้ URL ของภาพ"""
        
        url = urljoin(self.leonardo_config.api_endpoint, f"/generations/{generation_id}")
        
        start_time = time.time()
        timeout = self.leonardo_config.generation_timeout
        
        while time.time() - start_time < timeout:
            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        raise ImageGenerationError(f"Failed to check generation status: {response.status}")
                    
                    data = await response.json()
                    generation_data = data.get("generations_by_pk", {})
                    
                    status = generation_data.get("status")
                    
                    if status == "COMPLETE":
                        # ได้ URL ของภาพที่สร้างแล้ว
                        generated_images = generation_data.get("generated_images", [])
                        
                        if not generated_images:
                            raise ImageGenerationError("No images generated")
                        
                        image_urls = [img.get("url") for img in generated_images if img.get("url")]
                        
                        if not image_urls:
                            raise ImageGenerationError("No valid image URLs")
                        
                        self.logger.info(f"Generation completed: {len(image_urls)} images")
                        return image_urls
                    
                    elif status == "FAILED":
                        raise ImageGenerationError("Generation failed on Leonardo AI")
                    
                    elif status in ["PENDING", "IN_PROGRESS"]:
                        # ยังไม่เสร็จ รอต่อ
                        await asyncio.sleep(self.leonardo_config.polling_interval)
                        continue
                    
                    else:
                        self.logger.warning(f"Unknown generation status: {status}")
                        await asyncio.sleep(self.leonardo_config.polling_interval)
                        continue
                        
            except aiohttp.ClientError as e:
                self.logger.warning(f"Error checking generation status: {e}")
                await asyncio.sleep(self.leonardo_config.polling_interval)
                continue
        
        raise ImageGenerationError("Generation timeout")

    async def _download_generated_image(self, image_url: str, generation_id: str) -> str:
        """ดาวน์โหลดภาพที่สร้างแล้ว"""
        
        try:
            async with self.session.get(image_url) as response:
                if response.status != 200:
                    raise ImageGenerationError(f"Failed to download image: {response.status}")
                
                # สร้างชื่อไฟล์
                timestamp = int(datetime.now().timestamp())
                filename = f"leonardo_{generation_id}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
                image_path = os.path.join(self.config.output_directory, filename)
                
                # ดาวน์โหลดและบันทึก
                async with aiofiles.open(image_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                self.logger.info(f"Image downloaded: {image_path}")
                return image_path
                
        except aiohttp.ClientError as e:
            raise ImageGenerationError(f"Failed to download image: {e}")

    # Leonardo AI specific methods

    async def get_user_info(self) -> Dict[str, Any]:
        """ดูข้อมูล user และ credits"""
        
        await self._ensure_session()
        return self.user_info

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """ดูรายการ models ที่ใช้ได้"""
        
        await self._ensure_session()
        
        url = urljoin(self.leonardo_config.api_endpoint, "/models")
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise ImageGenerationError(f"Failed to fetch models: {response.status}")
                
                data = await response.json()
                return data.get("custom_models", [])
                
        except aiohttp.ClientError as e:
            raise ImageGenerationError(f"Failed to fetch models: {e}")

    async def generate_with_custom_model(self, prompt: str, custom_model_id: str,
                                       **kwargs) -> str:
        """สร้างภาพด้วย custom model"""
        
        request = ImageGenerationRequest(
            prompt=prompt,
            model=custom_model_id,
            **kwargs
        )
        
        result = await self.generate_image_from_request(request)
        return result.image_path

    async def generate_variations_advanced(self, base_prompt: str, 
                                         variation_prompts: List[str],
                                         **kwargs) -> List[str]:
        """สร้าง variations ขั้นสูงด้วย prompt ที่แตกต่างกัน"""
        
        results = []
        
        for variation in variation_prompts:
            combined_prompt = f"{base_prompt}, {variation}"
            
            try:
                result = await self.generate_image(combined_prompt, **kwargs)
                results.append(result.image_path)
            except Exception as e:
                self.logger.warning(f"Failed to generate variation '{variation}': {e}")
                continue
        
        return results

    async def generate_with_image_guidance(self, prompt: str, reference_image_path: str,
                                         strength: float = 0.5, **kwargs) -> str:
        """สร้างภาพด้วย image guidance (ถ้า Leonardo รองรับ)"""
        
        # Leonardo AI อาจมี image guidance features ในอนาคต
        # ตอนนี้ใช้ standard generation
        
        self.logger.warning("Image guidance not yet implemented for Leonardo AI")
        
        result = await self.generate_image(prompt, **kwargs)
        return result.image_path

    def get_model_info(self, model_key: str) -> Dict[str, Any]:
        """ดูข้อมูล model"""
        
        return self.leonardo_config.available_models.get(model_key, {})

    def get_all_models_info(self) -> Dict[str, Dict[str, Any]]:
        """ดูข้อมูล models ทั้งหมด"""
        
        return self.leonardo_config.available_models

    def set_model(self, model_key: str):
        """เปลี่ยน default model"""
        
        if model_key in self.leonardo_config.available_models:
            self.leonardo_config.default_model_id = self.leonardo_config.available_models[model_key]["id"]
        else:
            raise ValueError(f"Model {model_key} not found")

    def estimate_credits_cost(self, request: ImageGenerationRequest) -> int:
        """ประมาณจำนวน credits ที่จะใช้"""
        
        base_cost = 1  # 1 credit per image พื้นฐาน
        
        # ปรับตาม model
        model_id = request.model or self.leonardo_config.default_model_id
        model_key = self._get_model_key_from_id(model_id)
        
        if model_key:
            model_info = self.leonardo_config.available_models[model_key]
            base_cost *= model_info.get("cost_multiplier", 1.0)
        
        # ปรับตามขนาด
        if request.width and request.height:
            pixel_count = request.width * request.height
            if pixel_count > 512 * 512:
                base_cost *= 1.5
            if pixel_count > 768 * 768:
                base_cost *= 2.0
        
        # ปรับตาม enhancement features
        preset = self.generation_presets[self.quality_tier]
        if preset.get("enable_alchemy", False):
            base_cost *= 1.5
        if preset.get("enable_prompt_magic", False):
            base_cost *= 1.2
        
        return int(base_cost)

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            self.session = None


# Utility functions สำหรับ Leonardo AI

def create_leonardo_config(api_key: str, enable_premium_features: bool = True) -> LeonardoConfig:
    """
    สร้าง configuration สำหรับ Leonardo AI
    """
    
    config = LeonardoConfig()
    config.api_key = api_key
    config.enable_alchemy = enable_premium_features
    config.enable_prompt_magic = enable_premium_features
    config.enable_photoreal = enable_premium_features
    
    return config


async def quick_generate_leonardo(prompt: str, api_key: str,
                                style: ImageStyle = ImageStyle.DIGITAL_ART) -> str:
    """
    ฟังก์ชันสร้างภาพแบบง่ายด้วย Leonardo AI
    """
    
    config = create_leonardo_config(api_key, enable_premium_features=True)
    
    async with LeonardoAI(api_key, config, QualityTier.BALANCED) as leonardo:
        result = await leonardo.generate_image(prompt, style)
        return result.image_path


def get_leonardo_style_recommendations(content_type: str) -> Dict[str, Any]:
    """
    แนะนำ style และ model สำหรับประเภทเนื้อหา
    """
    
    recommendations = {
        "portrait": {
            "style": ImageStyle.REALISTIC,
            "model": "leonardo_select",
            "enable_photoreal": True,
            "guidance_scale": 7
        },
        "landscape": {
            "style": ImageStyle.REALISTIC,
            "model": "stable_diffusion_xl",
            "enable_photoreal": True,
            "guidance_scale": 8
        },
        "character_design": {
            "style": ImageStyle.DIGITAL_ART,
            "model": "leonardo_signature",
            "enable_photoreal": False,
            "guidance_scale": 9
        },
        "fantasy": {
            "style": ImageStyle.CONCEPT_ART,
            "model": "dreamshaper",
            "enable_photoreal": False,
            "guidance_scale": 8
        },
        "product": {
            "style": ImageStyle.REALISTIC,
            "model": "leonardo_select",
            "enable_photoreal": True,
            "guidance_scale": 7
        },
        "architecture": {
            "style": ImageStyle.REALISTIC,
            "model": "leonardo_creative",
            "enable_photoreal": True,
            "guidance_scale": 8
        },
        "abstract": {
            "style": ImageStyle.DIGITAL_ART,
            "model": "leonardo_creative",
            "enable_photoreal": False,
            "guidance_scale": 6
        }
    }
    
    return recommendations.get(content_type, recommendations["character_design"])


def analyze_leonardo_generation_cost(results: List[Any], api_credits_per_dollar: int = 10) -> Dict[str, Any]:
    """
    วิเคราะห์ต้นทุนการสร้างภาพใน Leonardo AI
    """
    
    if not results:
        return {"error": "No results to analyze"}
    
    total_cost_baht = sum(r.cost_estimate for r in results)
    total_time = sum(r.generation_time for r in results)
    avg_quality = sum(r.quality_score for r in results) / len(results)
    
    # ประมาณ credits ที่ใช้
    estimated_credits = len(results) * 2  # ประมาณ 2 credits ต่อภาพ
    cost_in_dollars = estimated_credits / api_credits_per_dollar
    
    analysis = {
        "total_images": len(results),
        "total_cost_baht": round(total_cost_baht, 2),
        "estimated_credits_used": estimated_credits,
        "estimated_cost_usd": round(cost_in_dollars, 2),
        "average_cost_per_image": round(total_cost_baht / len(results), 2),
        "total_generation_time": round(total_time, 2),
        "average_generation_time": round(total_time / len(results), 2),
        "average_quality_score": round(avg_quality, 2),
        "cost_per_quality_point": round(total_cost_baht / (avg_quality * len(results)), 2)
    }
    
    return analysis


def create_leonardo_batch_request(prompts: List[str], base_style: ImageStyle = ImageStyle.DIGITAL_ART,
                                base_model: str = "leonardo_creative") -> List[ImageGenerationRequest]:
    """
    สร้าง batch requests สำหรับ Leonardo AI
    """
    
    requests = []
    
    for i, prompt in enumerate(prompts):
        # เพิ่มความหลากหลายด้วย seed ที่แตกต่างกัน
        seed = hash(prompt) % 1000000 + i * 1000
        
        request = ImageGenerationRequest(
            prompt=prompt,
            style=base_style,
            model=base_model,
            seed=seed,
            aspect_ratio=AspectRatio.SQUARE
        )
        
        requests.append(request)
    
    return requests


def optimize_leonardo_prompt(base_prompt: str, style: ImageStyle = ImageStyle.DIGITAL_ART,
                           quality_focus: str = "balanced") -> str:
    """
    ปรับปรุง prompt สำหรับ Leonardo AI
    """
    
    # Style-specific enhancements
    style_enhancements = {
        ImageStyle.REALISTIC: "photorealistic, highly detailed, professional photography, 8k resolution",
        ImageStyle.DIGITAL_ART: "digital art, detailed illustration, artstation trending, concept art",
        ImageStyle.CARTOON: "cartoon style, animated, colorful illustration, clean art",
        ImageStyle.ANIME: "anime style, manga illustration, detailed character design",
        ImageStyle.CONCEPT_ART: "concept art, matte painting, environment design, cinematic",
        ImageStyle.MINIMALIST: "minimalist design, clean composition, simple geometric forms"
    }
    
    # Quality focus keywords
    quality_keywords = {
        "speed": "fast render, simple style",
        "balanced": "good quality, detailed",
        "premium": "masterpiece, ultra detailed, highest quality, professional",
        "artistic": "artistic vision, creative interpretation, unique style"
    }
    
    # สร้าง optimized prompt
    enhanced_prompt = base_prompt
    
    # เพิ่ม style enhancement
    if style in style_enhancements:
        enhanced_prompt += f", {style_enhancements[style]}"
    
    # เพิ่ม quality keywords
    if quality_focus in quality_keywords:
        enhanced_prompt += f", {quality_keywords[quality_focus]}"
    
    # เพิ่ม Leonardo-specific optimization
    enhanced_prompt += ", leonardo ai optimized"
    
    return enhanced_prompt


async def compare_leonardo_models(prompt: str, api_key: str,
                                models: List[str] = None) -> Dict[str, str]:
    """
    เปรียบเทียบผลลัพธ์จาก Leonardo models ต่างๆ
    """
    
    if not models:
        models = ["leonardo_creative", "leonardo_select", "dreamshaper"]
    
    config = create_leonardo_config(api_key)
    results = {}
    
    async with LeonardoAI(api_key, config, QualityTier.BALANCED) as leonardo:
        
        for model_key in models:
            if model_key not in leonardo.leonardo_config.available_models:
                continue
            
            try:
                # ใช้ seed เดียวกันเพื่อการเปรียบเทียบ
                request = ImageGenerationRequest(
                    prompt=prompt,
                    model=model_key,
                    seed=12345,
                    style=ImageStyle.DIGITAL_ART
                )
                
                result = await leonardo.generate_image_from_request(request)
                results[model_key] = result.image_path
                
            except Exception as e:
                results[model_key] = f"Error: {e}"
    
    return results


class LeonardoAIError(ImageGenerationError):
    """Specific error class for Leonardo AI"""
    pass


def handle_leonardo_api_error(response_status: int, response_text: str) -> str:
    """
    จัดการ error messages จาก Leonardo AI API
    """
    
    error_messages = {
        400: "Invalid request parameters",
        401: "Invalid API key or unauthorized",
        402: "Insufficient credits",
        403: "Access forbidden",
        404: "Resource not found",
        429: "Rate limit exceeded - too many requests",
        500: "Leonardo AI server error",
        503: "Service temporarily unavailable"
    }
    
    base_message = error_messages.get(response_status, "Unknown API error")
    
    # พยายามแยก error details
    try:
        import json
        error_data = json.loads(response_text)
        if "error" in error_data:
            return f"{base_message}: {error_data['error']}"
        elif "message" in error_data:
            return f"{base_message}: {error_data['message']}"
    except:
        pass
    
    return f"{base_message} (Status: {response_status})"


if __name__ == "__main__":
    # ตัวอย่างการใช้งาน Leonardo AI
    async def example_usage():
        
        # Setup (ใส่ API key จริง)
        api_key = "your-leonardo-ai-api-key"
        
        config = create_leonardo_config(
            api_key=api_key,
            enable_premium_features=True
        )
        
        processing_config = ImageProcessingConfig(
            output_directory="./leonardo_generated",
            watermark_enabled=True,
            watermark_text="Leonardo AI"
        )
        
        print("🎨 เริ่มทดสอบ Leonardo AI...")
        
        try:
            async with LeonardoAI(api_key, config, QualityTier.BALANCED, processing_config) as leonardo:
                
                # ดูข้อมูล user
                user_info = await leonardo.get_user_info()
                user_details = user_info.get("user_details", [{}])[0]
                credits = user_details.get("apiCredit", 0)
                print(f"👤 User credits: {credits}")
                
                # ทดสอบการสร้างภาพพื้นฐาน
                result1 = await leonardo.generate_image(
                    prompt="majestic dragon flying over fantasy castle",
                    style=ImageStyle.CONCEPT_ART,
                    aspect_ratio=AspectRatio.LANDSCAPE
                )
                
                print(f"✅ สร้างภาพพื้นฐานเสร็จ: {result1.image_path}")
                print(f"   คุณภาพ: {result1.quality_score}/10")
                print(f"   ต้นทุน: {result1.cost_estimate} บาท")
                print(f"   เวลา: {result1.generation_time:.2f}s")
                
                # ทดสอบ styles ต่างๆ
                print("\n🎭 ทดสอบ styles ต่างๆ...")
                
                style_tests = [
                    (ImageStyle.REALISTIC, "professional headshot of business woman"),
                    (ImageStyle.CARTOON, "cute cartoon cat with big eyes"),
                    (ImageStyle.ANIME, "anime warrior girl with magical sword"),
                    (ImageStyle.DIGITAL_ART, "futuristic cyberpunk city neon lights"),
                    (ImageStyle.CONCEPT_ART, "alien planet landscape with two moons")
                ]
                
                for style, prompt in style_tests:
                    try:
                        result = await leonardo.generate_image(prompt, style)
                        print(f"✅ {style.value}: {result.image_path}")
                    except Exception as e:
                        print(f"❌ {style.value}: {e}")
                
                # ทดสอบ model comparison
                print("\n🔧 ทดสอบ model comparison...")
                
                comparison_prompt = "beautiful fantasy forest with magical creatures"
                model_comparison = await compare_leonardo_models(
                    comparison_prompt, 
                    api_key,
                    ["leonardo_creative", "leonardo_select", "dreamshaper"]
                )
                
                print("📊 Model comparison results:")
                for model, result in model_comparison.items():
                    print(f"   {model}: {result}")
                
                # ทดสอบ advanced variations
                print("\n🔄 ทดสอบ advanced variations...")
                
                base_prompt = "epic medieval knight"
                variations = [
                    "in shining armor",
                    "on horseback", 
                    "fighting dragon",
                    "in dark armor"
                ]
                
                variation_results = await leonardo.generate_variations_advanced(
                    base_prompt, 
                    variations,
                    style=ImageStyle.CONCEPT_ART
                )
                
                print(f"✅ Variations เสร็จ: {len(variation_results)} ภาพ")
                for i, path in enumerate(variation_results):
                    print(f"   {i+1}. {path}")
                
                # ทดสอบ batch generation
                print("\n📦 ทดสอบ batch generation...")
                
                batch_prompts = [
                    "serene mountain lake at sunrise",
                    "bustling medieval marketplace", 
                    "space station orbiting Earth"
                ]
                
                batch_results = await leonardo.generate_multiple_images(
                    batch_prompts,
                    style=ImageStyle.DIGITAL_ART
                )
                
                print(f"✅ Batch generation เสร็จ: {len(batch_results)} ภาพ")
                
                # ทดสอบ custom model (ถ้ามี)
                print("\n🎨 ทดสอบ available models...")
                
                try:
                    available_models = await leonardo.list_available_models()
                    print(f"📋 Available custom models: {len(available_models)}")
                    
                    if available_models:
                        # ใช้ custom model แรก
                        custom_model = available_models[0]
                        model_id = custom_model.get("id")
                        model_name = custom_model.get("name", "Unknown")
                        
                        print(f"🔄 ทดสอบ custom model: {model_name}")
                        
                        custom_result = await leonardo.generate_with_custom_model(
                            "beautiful portrait in this style",
                            model_id
                        )
                        
                        print(f"✅ Custom model result: {custom_result}")
                
                except Exception as e:
                    print(f"❌ Custom model test failed: {e}")
                
                # ทดสอบ cost estimation
                print("\n💰 ทดสอบ cost estimation...")
                
                test_request = ImageGenerationRequest(
                    prompt="detailed fantasy illustration",
                    style=ImageStyle.CONCEPT_ART,
                    width=1024,
                    height=1024,
                    steps=25
                )
                
                estimated_credits = leonardo.estimate_credits_cost(test_request)
                estimated_cost = leonardo.get_cost_estimate(test_request)
                estimated_time = leonardo.estimate_generation_time(test_request)
                
                print(f"   Estimated credits: {estimated_credits}")
                print(f"   Estimated cost: {estimated_cost} บาท")
                print(f"   Estimated time: {estimated_time:.1f}s")
                
                # ดูสถิติรวม
                print("\n📊 สถิติการสร้างภาพ:")
                stats = leonardo.get_generation_statistics()
                print(f"   Total requests: {stats['total_requests']}")
                print(f"   Success rate: {stats['success_rate']}%")
                print(f"   Average cost: {stats['average_cost_per_image']} บาท/ภาพ")
                print(f"   Average time: {stats['average_generation_time']:.2f}s")
                print(f"   Cache hit rate: {stats['cache_hit_rate']}%")
                
                # วิเคราะห์ต้นทุน Leonardo
                all_results = [result1] + batch_results + [r for r in [result1] if hasattr(r, 'cost_estimate')]
                cost_analysis = analyze_leonardo_generation_cost(all_results)
                
                print("\n💳 Leonardo Cost Analysis:")
                print(f"   Total credits estimated: {cost_analysis['estimated_credits_used']}")
                print(f"   Total cost USD: ${cost_analysis['estimated_cost_usd']}")
                print(f"   Average cost per image: {cost_analysis['average_cost_per_image']} บาท")
                print(f"   Cost per quality point: {cost_analysis['cost_per_quality_point']} บาท")
                
                # ทดสอบ prompt optimization
                print("\n✨ ทดสอบ prompt optimization...")
                
                original_prompt = "castle in mountains"
                optimized_prompt = optimize_leonardo_prompt(
                    original_prompt,
                    style=ImageStyle.CONCEPT_ART,
                    quality_focus="premium"
                )
                
                print(f"Original: {original_prompt}")
                print(f"Optimized: {optimized_prompt}")
                
                # สร้างภาพด้วย optimized prompt
                optimized_result = await leonardo.generate_image(
                    optimized_prompt,
                    style=ImageStyle.CONCEPT_ART
                )
                
                print(f"✅ Optimized prompt result: {optimized_result.image_path}")
                print(f"   Quality score: {optimized_result.quality_score}/10")
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
            import traceback
            traceback.print_exc()
    
    # รัน example
    print("🎨 Leonardo AI Test Suite")
    print("="*50)
    asyncio.run(example_usage())