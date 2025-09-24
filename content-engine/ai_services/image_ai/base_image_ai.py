"""
Base Image AI Service
Base class และ interfaces สำหรับ image generation services ทั้งหมด
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
import uuid
from pathlib import Path
import base64
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from shared.models.quality_tier import QualityTier
from shared.utils.logger import get_logger
from shared.utils.error_handler import handle_errors, ImageGenerationError
from shared.utils.cache import CacheManager
from shared.utils.rate_limiter import RateLimiter


class ImageStyle(Enum):
    """รูปแบบการสร้างภาพ"""
    REALISTIC = "realistic"
    CARTOON = "cartoon"
    ANIME = "anime"
    MINIMALIST = "minimalist"
    ABSTRACT = "abstract"
    PHOTOGRAPHIC = "photographic"
    DIGITAL_ART = "digital_art"
    CONCEPT_ART = "concept_art"
    VINTAGE = "vintage"
    MODERN = "modern"


class AspectRatio(Enum):
    """อัตราส่วนภาพ"""
    SQUARE = "1:1"
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    WIDE = "21:9"
    CLASSIC = "4:3"
    VERTICAL = "3:4"


class ImageQuality(Enum):
    """คุณภาพภาพ"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class ImageGenerationRequest:
    """คำขอสร้างภาพ"""
    prompt: str
    negative_prompt: Optional[str] = None
    style: ImageStyle = ImageStyle.REALISTIC
    aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE
    quality: ImageQuality = ImageQuality.MEDIUM
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None
    steps: Optional[int] = None
    guidance_scale: Optional[float] = None
    model: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None


@dataclass
class ImageGenerationResult:
    """ผลลัพธ์การสร้างภาพ"""
    image_path: str
    prompt_used: str
    style: ImageStyle
    dimensions: Tuple[int, int]
    file_size: int  # bytes
    generation_time: float  # seconds
    cost_estimate: float  # บาท
    quality_score: float  # 0-10
    ai_service: str
    model_used: str
    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class ImageProcessingConfig:
    """การตั้งค่าการประมวลผลภาพ"""
    output_directory: str = "./generated_images"
    cache_enabled: bool = True
    cache_duration_hours: int = 24
    max_image_size: int = 2048  # pixels
    compression_quality: int = 85  # JPEG quality
    watermark_enabled: bool = False
    watermark_text: Optional[str] = None
    auto_upscale: bool = False
    format: str = "PNG"  # PNG, JPEG, WEBP


class BaseImageAI(ABC):
    """
    Base class สำหรับ image generation services ทั้งหมด
    """
    
    def __init__(self, quality_tier: QualityTier = QualityTier.BUDGET, 
                 config: ImageProcessingConfig = None):
        self.quality_tier = quality_tier
        self.config = config or ImageProcessingConfig()
        self.logger = get_logger(self.__class__.__name__)
        
        # Setup components
        self.cache_manager = CacheManager() if self.config.cache_enabled else None
        self.rate_limiter = RateLimiter()
        
        # Service configuration
        self.service_config = self._load_service_config()
        
        # Quality settings
        self.quality_settings = self._load_quality_settings()
        
        # Style templates
        self.style_templates = self._load_style_templates()
        
        # Statistics
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_cost": 0.0,
            "average_generation_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Create directories
        self._ensure_directories()
        
        # Initialize service-specific components
        self._initialize_service()

    def _load_service_config(self) -> Dict[str, Any]:
        """โหลดการตั้งค่าเฉพาะของ service"""
        return {
            "max_concurrent_requests": 3,
            "timeout_seconds": 120,
            "retry_attempts": 2,
            "rate_limit_per_minute": 60,
            "cost_per_image": {
                QualityTier.BUDGET: 2.0,
                QualityTier.BALANCED: 8.0,
                QualityTier.PREMIUM: 25.0
            }
        }

    def _load_quality_settings(self) -> Dict[QualityTier, Dict]:
        """โหลดการตั้งค่าคุณภาพแต่ละ tier"""
        return {
            QualityTier.BUDGET: {
                "default_size": (512, 512),
                "max_size": (768, 768),
                "steps": 20,
                "guidance_scale": 7.0,
                "quality": ImageQuality.LOW,
                "batch_size": 1
            },
            QualityTier.BALANCED: {
                "default_size": (768, 768),
                "max_size": (1024, 1024),
                "steps": 30,
                "guidance_scale": 7.5,
                "quality": ImageQuality.MEDIUM,
                "batch_size": 2
            },
            QualityTier.PREMIUM: {
                "default_size": (1024, 1024),
                "max_size": (2048, 2048),
                "steps": 50,
                "guidance_scale": 8.0,
                "quality": ImageQuality.HIGH,
                "batch_size": 4
            }
        }

    def _load_style_templates(self) -> Dict[ImageStyle, Dict]:
        """โหลด template สำหรับแต่ละ style"""
        return {
            ImageStyle.REALISTIC: {
                "prompt_suffix": ", photorealistic, highly detailed, professional photography",
                "negative_prompt": "cartoon, anime, painting, sketch, blurry, low quality",
                "recommended_steps": 30,
                "guidance_scale": 7.5
            },
            ImageStyle.CARTOON: {
                "prompt_suffix": ", cartoon style, colorful, vibrant, clean lines",
                "negative_prompt": "realistic, photographic, dark, gritty",
                "recommended_steps": 25,
                "guidance_scale": 8.0
            },
            ImageStyle.ANIME: {
                "prompt_suffix": ", anime style, manga, cel shading, vibrant colors",
                "negative_prompt": "realistic, western cartoon, 3d render",
                "recommended_steps": 28,
                "guidance_scale": 8.5
            },
            ImageStyle.MINIMALIST: {
                "prompt_suffix": ", minimalist, clean, simple, white background",
                "negative_prompt": "cluttered, busy, complex, detailed background",
                "recommended_steps": 20,
                "guidance_scale": 7.0
            },
            ImageStyle.DIGITAL_ART: {
                "prompt_suffix": ", digital art, concept art, detailed, artistic",
                "negative_prompt": "photograph, realistic, amateur",
                "recommended_steps": 35,
                "guidance_scale": 8.0
            }
        }

    def _ensure_directories(self):
        """สร้าง directories ที่จำเป็น"""
        Path(self.config.output_directory).mkdir(parents=True, exist_ok=True)
        Path(f"{self.config.output_directory}/temp").mkdir(exist_ok=True)
        Path(f"{self.config.output_directory}/processed").mkdir(exist_ok=True)

    @abstractmethod
    def _initialize_service(self):
        """Initialize service-specific components"""
        pass

    @abstractmethod
    async def _generate_image_internal(self, request: ImageGenerationRequest) -> str:
        """สร้างภาพ (implementation เฉพาะของแต่ละ service)"""
        pass

    @abstractmethod
    def _get_service_name(self) -> str:
        """ได้ชื่อ service"""
        pass

    @abstractmethod
    def _get_model_name(self) -> str:
        """ได้ชื่อ model ที่ใช้"""
        pass

    # Public methods

    async def generate_image(self, prompt: str, style: ImageStyle = ImageStyle.REALISTIC,
                           aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE,
                           quality: ImageQuality = None) -> ImageGenerationResult:
        """
        สร้างภาพจาก prompt
        """
        
        # สร้าง request object
        request = ImageGenerationRequest(
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            quality=quality or self.quality_settings[self.quality_tier]["quality"]
        )
        
        return await self.generate_image_from_request(request)

    async def generate_image_from_request(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """
        สร้างภาพจาก request object
        """
        
        self.generation_stats["total_requests"] += 1
        start_time = datetime.now()
        
        try:
            # ตรวจสอบ cache ก่อน
            if self.cache_manager:
                cached_result = await self._check_cache(request)
                if cached_result:
                    self.generation_stats["cache_hits"] += 1
                    self.logger.info(f"Cache hit for prompt: {request.prompt[:50]}...")
                    return cached_result
                else:
                    self.generation_stats["cache_misses"] += 1
            
            # ปรับแต่ง request ตาม quality tier
            optimized_request = self._optimize_request(request)
            
            # ตรวจสอบ rate limit
            await self._check_rate_limit()
            
            # สร้างภาพ
            image_path = await self._generate_with_retry(optimized_request)
            
            # ประมวลผลภาพหลังสร้าง
            processed_path = await self._post_process_image(image_path, optimized_request)
            
            # คำนวณ metrics
            generation_time = (datetime.now() - start_time).total_seconds()
            quality_score = await self._evaluate_image_quality(processed_path, optimized_request)
            cost = self._calculate_cost(optimized_request, generation_time)
            
            # สร้าง result
            result = ImageGenerationResult(
                image_path=processed_path,
                prompt_used=optimized_request.prompt,
                style=optimized_request.style,
                dimensions=self._get_image_dimensions(processed_path),
                file_size=os.path.getsize(processed_path),
                generation_time=generation_time,
                cost_estimate=cost,
                quality_score=quality_score,
                ai_service=self._get_service_name(),
                model_used=self._get_model_name(),
                metadata=self._create_metadata(optimized_request),
                created_at=datetime.now()
            )
            
            # บันทึกใน cache
            if self.cache_manager:
                await self._save_to_cache(request, result)
            
            # อัพเดทสถิติ
            self._update_statistics(result)
            
            self.logger.info(f"Generated image: {processed_path}")
            return result
            
        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            self.logger.error(f"Image generation failed: {e}")
            raise ImageGenerationError(f"Failed to generate image: {e}")

    async def generate_multiple_images(self, prompts: List[str], 
                                     style: ImageStyle = ImageStyle.REALISTIC,
                                     **kwargs) -> List[ImageGenerationResult]:
        """
        สร้างภาพหลายรูปพร้อมกัน
        """
        
        self.logger.info(f"Generating {len(prompts)} images")
        
        # สร้าง requests
        requests = [
            ImageGenerationRequest(prompt=prompt, style=style, **kwargs)
            for prompt in prompts
        ]
        
        # จำกัดจำนวน concurrent requests
        max_concurrent = self.service_config["max_concurrent_requests"]
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(request):
            async with semaphore:
                return await self.generate_image_from_request(request)
        
        # รัน parallel
        tasks = [generate_single(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # แยก results และ errors
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "prompt": prompts[i],
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        if errors:
            self.logger.warning(f"Batch generation completed with {len(errors)} errors")
        
        return successful_results

    async def generate_variations(self, base_prompt: str, count: int = 4,
                                style: ImageStyle = ImageStyle.REALISTIC) -> List[ImageGenerationResult]:
        """
        สร้างภาพที่หลากหลายจาก prompt เดียว
        """
        
        variations = []
        
        # สร้าง variations ของ prompt
        for i in range(count):
            # เพิ่ม variation keywords
            variation_keywords = [
                "variation", "alternative", "different angle", 
                "unique perspective", "creative interpretation"
            ]
            
            varied_prompt = f"{base_prompt}, {variation_keywords[i % len(variation_keywords)]}"
            
            # ใช้ seed ที่แตกต่างกัน
            request = ImageGenerationRequest(
                prompt=varied_prompt,
                style=style,
                seed=i * 1000 + hash(base_prompt) % 1000
            )
            
            variations.append(request)
        
        # สร้างภาพทั้งหมด
        results = []
        for request in variations:
            try:
                result = await self.generate_image_from_request(request)
                results.append(result)
            except Exception as e:
                self.logger.warning(f"Failed to generate variation: {e}")
                continue
        
        return results

    # Private helper methods

    def _optimize_request(self, request: ImageGenerationRequest) -> ImageGenerationRequest:
        """ปรับแต่ง request ตาม quality tier"""
        
        tier_settings = self.quality_settings[self.quality_tier]
        style_template = self.style_templates.get(request.style, {})
        
        # ปรับ prompt
        optimized_prompt = request.prompt
        if "prompt_suffix" in style_template:
            optimized_prompt += style_template["prompt_suffix"]
        
        # ปรับ negative prompt
        negative_prompt = request.negative_prompt or ""
        if "negative_prompt" in style_template:
            if negative_prompt:
                negative_prompt += ", " + style_template["negative_prompt"]
            else:
                negative_prompt = style_template["negative_prompt"]
        
        # ปรับขนาดภาพ
        if not request.width or not request.height:
            width, height = self._calculate_dimensions(request.aspect_ratio, tier_settings)
        else:
            width, height = request.width, request.height
        
        # จำกัดขนาดสูงสุด
        max_size = tier_settings["max_size"][0]
        if width > max_size or height > max_size:
            scale = max_size / max(width, height)
            width = int(width * scale)
            height = int(height * scale)
        
        # สร้าง optimized request
        return ImageGenerationRequest(
            prompt=optimized_prompt,
            negative_prompt=negative_prompt,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            quality=request.quality or tier_settings["quality"],
            width=width,
            height=height,
            seed=request.seed,
            steps=request.steps or style_template.get("recommended_steps", tier_settings["steps"]),
            guidance_scale=request.guidance_scale or style_template.get("guidance_scale", tier_settings["guidance_scale"]),
            model=request.model,
            additional_params=request.additional_params
        )

    def _calculate_dimensions(self, aspect_ratio: AspectRatio, 
                            tier_settings: Dict) -> Tuple[int, int]:
        """คำนวณขนาดภาพจาก aspect ratio"""
        
        base_size = tier_settings["default_size"][0]
        
        ratios = {
            AspectRatio.SQUARE: (1, 1),
            AspectRatio.LANDSCAPE: (16, 9),
            AspectRatio.PORTRAIT: (9, 16),
            AspectRatio.WIDE: (21, 9),
            AspectRatio.CLASSIC: (4, 3),
            AspectRatio.VERTICAL: (3, 4)
        }
        
        ratio_w, ratio_h = ratios.get(aspect_ratio, (1, 1))
        
        # คำนวณขนาดที่เหมาะสม
        if ratio_w >= ratio_h:
            width = base_size
            height = int(base_size * ratio_h / ratio_w)
        else:
            height = base_size
            width = int(base_size * ratio_w / ratio_h)
        
        # ปรับให้เป็นเลขคู่ (requirement ของบาง AI models)
        width = width - (width % 8)
        height = height - (height % 8)
        
        return width, height

    async def _generate_with_retry(self, request: ImageGenerationRequest) -> str:
        """สร้างภาพพร้อม retry logic"""
        
        max_retries = self.service_config["retry_attempts"]
        
        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self._generate_image_internal(request),
                    timeout=self.service_config["timeout_seconds"]
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"Generation timeout on attempt {attempt + 1}")
                if attempt == max_retries:
                    raise ImageGenerationError("Generation timed out after all retries")
            except Exception as e:
                self.logger.warning(f"Generation failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def _post_process_image(self, image_path: str, 
                                request: ImageGenerationRequest) -> str:
        """ประมวลผลภาพหลังการสร้าง"""
        
        try:
            with Image.open(image_path) as img:
                # แปลงเป็น RGB ถ้าจำเป็น
                if img.mode != 'RGB' and self.config.format == 'JPEG':
                    img = img.convert('RGB')
                
                # ปรับขนาดหากจำเป็น
                if self.config.auto_upscale:
                    img = await self._upscale_image(img)
                
                # เพิ่ม watermark
                if self.config.watermark_enabled:
                    img = self._add_watermark(img)
                
                # บันทึกไฟล์ที่ประมวลผลแล้ว
                processed_path = self._get_processed_path(image_path)
                
                save_kwargs = {}
                if self.config.format == 'JPEG':
                    save_kwargs['quality'] = self.config.compression_quality
                    save_kwargs['optimize'] = True
                elif self.config.format == 'PNG':
                    save_kwargs['optimize'] = True
                
                img.save(processed_path, format=self.config.format, **save_kwargs)
                
                return processed_path
                
        except Exception as e:
            self.logger.warning(f"Post-processing failed, using original: {e}")
            return image_path

    async def _upscale_image(self, img: Image.Image) -> Image.Image:
        """ขยายภาพให้ใหญ่ขึ้น (placeholder implementation)"""
        
        # ในการใช้งานจริงจะใช้ AI upscaling services
        # ตอนนี้ใช้ simple bicubic interpolation
        
        current_size = max(img.size)
        if current_size < self.config.max_image_size:
            scale_factor = self.config.max_image_size / current_size
            new_size = (
                int(img.width * scale_factor),
                int(img.height * scale_factor)
            )
            img = img.resize(new_size, Image.Resampling.BICUBIC)
        
        return img

    def _add_watermark(self, img: Image.Image) -> Image.Image:
        """เพิ่ม watermark ลงในภาพ"""
        
        if not self.config.watermark_text:
            return img
        
        # สร้าง overlay
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # คำนวณขนาดฟอนต์
        font_size = max(img.width, img.height) // 30
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # คำนวณตำแหน่ง
        bbox = draw.textbbox((0, 0), self.config.watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = img.width - text_width - 20
        y = img.height - text_height - 20
        
        # วาดข้อความ
        draw.text((x, y), self.config.watermark_text, 
                 fill=(255, 255, 255, 128), font=font)
        
        # รวมกับภาพต้นฉบับ
        watermarked = Image.alpha_composite(img.convert('RGBA'), overlay)
        return watermarked.convert('RGB')

    def _get_processed_path(self, original_path: str) -> str:
        """ได้ path สำหรับไฟล์ที่ประมวลผลแล้ว"""
        
        original_name = Path(original_path).stem
        timestamp = int(datetime.now().timestamp())
        
        processed_name = f"{original_name}_processed_{timestamp}.{self.config.format.lower()}"
        return os.path.join(self.config.output_directory, "processed", processed_name)

    async def _evaluate_image_quality(self, image_path: str, 
                                    request: ImageGenerationRequest) -> float:
        """ประเมินคุณภาพภาพ"""
        
        try:
            with Image.open(image_path) as img:
                score = 5.0  # คะแนนพื้นฐาน
                
                # ตรวจสอบขนาด
                width, height = img.size
                expected_w, expected_h = request.width or 512, request.height or 512
                
                size_match = 1.0 - abs(width - expected_w) / expected_w
                score += size_match * 2.0
                
                # ตรวจสอบคุณภาพโดยทั่วไป (placeholder)
                # ในการใช้งานจริงจะใช้ AI models สำหรับ quality assessment
                
                # ตรวจสอบความคมชัด
                gray = img.convert('L')
                sharpness = ImageEnhance.Sharpness(gray)
                enhanced = sharpness.enhance(2.0)
                if enhanced != gray:
                    score += 1.0
                
                # ตรวจสอบความสว่าง
                brightness = ImageEnhance.Brightness(img)
                if brightness:
                    score += 0.5
                
                return min(score, 10.0)
                
        except Exception as e:
            self.logger.warning(f"Quality evaluation failed: {e}")
            return 7.0  # คะแนนเฉลี่ย

    def _calculate_cost(self, request: ImageGenerationRequest, generation_time: float) -> float:
        """คำนวณต้นทุนการสร้างภาพ"""
        
        base_cost = self.service_config["cost_per_image"][self.quality_tier]
        
        # ปรับตามคุณภาพ
        quality_multipliers = {
            ImageQuality.LOW: 0.7,
            ImageQuality.MEDIUM: 1.0,
            ImageQuality.HIGH: 1.5,
            ImageQuality.ULTRA: 2.5
        }
        
        quality_multiplier = quality_multipliers.get(request.quality, 1.0)
        
        # ปรับตามขนาด
        if request.width and request.height:
            pixel_count = request.width * request.height
            size_multiplier = pixel_count / (512 * 512)  # Base: 512x512
        else:
            size_multiplier = 1.0
        
        # ปรับตามเวลาที่ใช้
        time_multiplier = 1.0 + (generation_time / 60.0) * 0.1  # เพิ่ม 10% ต่อนาที
        
        total_cost = base_cost * quality_multiplier * size_multiplier * time_multiplier
        
        return round(total_cost, 2)

    def _get_image_dimensions(self, image_path: str) -> Tuple[int, int]:
        """ได้ขนาดภาพ"""
        
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception:
            return (0, 0)

    def _create_metadata(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        """สร้าง metadata สำหรับผลลัพธ์"""
        
        return {
            "original_prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "style": request.style.value,
            "aspect_ratio": request.aspect_ratio.value,
            "quality": request.quality.value if request.quality else None,
            "steps": request.steps,
            "guidance_scale": request.guidance_scale,
            "seed": request.seed,
            "model": request.model,
            "service": self._get_service_name(),
            "quality_tier": self.quality_tier.value,
            "additional_params": request.additional_params
        }

    def _update_statistics(self, result: ImageGenerationResult):
        """อัพเดทสถิติ"""
        
        self.generation_stats["successful_generations"] += 1
        self.generation_stats["total_cost"] += result.cost_estimate
        
        # อัพเดทเวลาเฉลี่ย
        total_gens = self.generation_stats["successful_generations"]
        current_avg = self.generation_stats["average_generation_time"]
        new_avg = ((current_avg * (total_gens - 1)) + result.generation_time) / total_gens
        self.generation_stats["average_generation_time"] = round(new_avg, 2)

    # Cache methods

    async def _check_cache(self, request: ImageGenerationRequest) -> Optional[ImageGenerationResult]:
        """ตรวจสอบ cache"""
        
        if not self.cache_manager:
            return None
        
        cache_key = self._generate_cache_key(request)
        cached_data = await self.cache_manager.get(cache_key)
        
        if cached_data:
            # ตรวจสอบว่าไฟล์ยังอยู่หรือไม่
            if os.path.exists(cached_data["image_path"]):
                return ImageGenerationResult(**cached_data)
            else:
                # ลบ cache ที่ไฟล์หาย
                await self.cache_manager.delete(cache_key)
        
        return None

    async def _save_to_cache(self, request: ImageGenerationRequest, 
                           result: ImageGenerationResult):
        """บันทึกผลลัพธ์ลง cache"""
        
        if not self.cache_manager:
            return
        
        cache_key = self._generate_cache_key(request)
        cache_data = asdict(result)
        
        await self.cache_manager.set(
            cache_key, 
            cache_data,