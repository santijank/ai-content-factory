"""
Stable Diffusion Image AI Service
Implementation of BaseImageAI for Stable Diffusion (local and API-based)
"""

import asyncio
import aiohttp
import aiofiles
import logging
import os
import json
import uuid
import io
import base64
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
import subprocess
import tempfile

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


class StableDiffusionConfig:
    """การตั้งค่าเฉพาะสำหรับ Stable Diffusion"""
    
    def __init__(self):
        self.use_local_installation = False  # ใช้ local SD หรือ API
        self.local_sd_path = None  # path ไปยัง local stable diffusion
        self.api_endpoint = "https://api.stability.ai"  # Stability AI API
        self.api_key = None
        self.default_model = "stable-diffusion-xl-1024-v1-0"
        self.available_models = [
            "stable-diffusion-xl-1024-v1-0",
            "stable-diffusion-v1-6",
            "stable-diffusion-512-v2-1",
            "stable-diffusion-xl-beta-v2-2-2"
        ]
        self.safety_filter = True
        self.enhanced_prompt = True  # ปรับปรุง prompt อัตโนมัติ
        self.enable_upscaling = False
        self.max_inference_steps = 50
        self.enable_img2img = False  # สำหรับ image-to-image generation


class StableDiffusionAI(BaseImageAI):
    """
    Stable Diffusion implementation ที่รองรับทั้ง local และ API
    """
    
    def __init__(self, api_key: str = None, 
                 sd_config: StableDiffusionConfig = None,
                 quality_tier: QualityTier = QualityTier.BUDGET,
                 processing_config: ImageProcessingConfig = None):
        
        # Setup configs
        self.sd_config = sd_config or StableDiffusionConfig()
        self.sd_config.api_key = api_key
        
        super().__init__(quality_tier, processing_config)
        
        self.session = None
        self.local_sd_available = False
        
        # Model-specific settings
        self.model_settings = self._load_model_settings()
        
        # Prompt enhancement templates
        self.prompt_enhancers = self._load_prompt_enhancers()
        
        # Safety filter settings
        self.safety_settings = self._load_safety_settings()

    def _initialize_service(self):
        """Initialize Stable Diffusion service"""
        
        # ตรวจสอบ local installation
        if self.sd_config.use_local_installation:
            self._check_local_installation()
        
        # ตรวจสอบ API key
        if not self.sd_config.use_local_installation and not self.sd_config.api_key:
            self.logger.warning("No API key provided for Stability AI")

    def _load_model_settings(self) -> Dict[str, Dict]:
        """โหลดการตั้งค่าเฉพาะแต่ละ model"""
        
        return {
            "stable-diffusion-xl-1024-v1-0": {
                "max_resolution": (1024, 1024),
                "recommended_steps": 30,
                "guidance_range": (7.0, 15.0),
                "supports_negative_prompt": True,
                "supports_img2img": True,
                "cost_multiplier": 1.5
            },
            "stable-diffusion-v1-6": {
                "max_resolution": (768, 768),
                "recommended_steps": 25,
                "guidance_range": (7.0, 12.0),
                "supports_negative_prompt": True,
                "supports_img2img": True,
                "cost_multiplier": 1.0
            },
            "stable-diffusion-512-v2-1": {
                "max_resolution": (512, 512),
                "recommended_steps": 20,
                "guidance_range": (5.0, 10.0),
                "supports_negative_prompt": True,
                "supports_img2img": False,
                "cost_multiplier": 0.7
            }
        }

    def _load_prompt_enhancers(self) -> Dict[ImageStyle, Dict]:
        """โหลด prompt enhancers สำหรับแต่ละ style"""
        
        return {
            ImageStyle.REALISTIC: {
                "positive_keywords": [
                    "photorealistic", "hyperrealistic", "8k uhd", "high resolution",
                    "professional photography", "detailed", "sharp focus",
                    "natural lighting", "cinematic"
                ],
                "negative_keywords": [
                    "cartoon", "anime", "painting", "sketch", "artistic",
                    "blurry", "low quality", "pixelated", "distorted"
                ],
                "style_prompt": "professional photograph, highly detailed, realistic"
            },
            ImageStyle.CARTOON: {
                "positive_keywords": [
                    "cartoon style", "animated", "colorful", "vibrant colors",
                    "clean lines", "flat colors", "cel shading", "vector art"
                ],
                "negative_keywords": [
                    "realistic", "photographic", "3d render", "dark",
                    "gritty", "photorealistic"
                ],
                "style_prompt": "cartoon illustration, bright colors, clean art style"
            },
            ImageStyle.ANIME: {
                "positive_keywords": [
                    "anime style", "manga", "japanese animation", "cel shading",
                    "vibrant colors", "detailed character design", "studio quality"
                ],
                "negative_keywords": [
                    "realistic", "western cartoon", "3d render", "live action",
                    "photographic"
                ],
                "style_prompt": "anime art style, manga illustration, detailed anime"
            },
            ImageStyle.MINIMALIST: {
                "positive_keywords": [
                    "minimalist", "clean", "simple", "geometric", "white background",
                    "negative space", "modern design", "abstract"
                ],
                "negative_keywords": [
                    "cluttered", "busy", "complex", "detailed background",
                    "ornate", "decorative"
                ],
                "style_prompt": "minimalist design, clean simple composition"
            },
            ImageStyle.DIGITAL_ART: {
                "positive_keywords": [
                    "digital art", "concept art", "matte painting", "artstation",
                    "detailed digital painting", "fantasy art", "sci-fi art"
                ],
                "negative_keywords": [
                    "photograph", "realistic", "amateur", "sketch",
                    "unfinished"
                ],
                "style_prompt": "digital art, concept art, detailed illustration"
            }
        }

    def _load_safety_settings(self) -> Dict:
        """โหลดการตั้งค่า safety filter"""
        
        return {
            "blocked_keywords": [
                "nsfw", "nude", "explicit", "violence", "gore",
                "drugs", "illegal", "harmful", "dangerous"
            ],
            "warning_keywords": [
                "weapon", "political", "religious", "controversial"
            ],
            "auto_replace": {
                "sexy": "attractive",
                "hot": "warm",
                "kill": "defeat"
            }
        }

    def _get_service_name(self) -> str:
        return "Stable Diffusion"

    def _get_model_name(self) -> str:
        return self.sd_config.default_model

    def _check_local_installation(self):
        """ตรวจสอบ local Stable Diffusion installation"""
        
        if not self.sd_config.local_sd_path:
            self.logger.warning("Local SD path not specified")
            return
        
        try:
            # ตรวจสอบว่ามี diffusers หรือ automatic1111
            sd_path = Path(self.sd_config.local_sd_path)
            
            if (sd_path / "webui.py").exists():
                # Automatic1111 installation
                self.local_sd_available = True
                self.logger.info("Found Automatic1111 installation")
            elif (sd_path / "scripts").exists():
                # Diffusers installation
                self.local_sd_available = True
                self.logger.info("Found Diffusers installation")
            else:
                self.logger.warning("Local SD installation not found")
                
        except Exception as e:
            self.logger.error(f"Error checking local SD: {e}")

    async def _generate_image_internal(self, request: ImageGenerationRequest) -> str:
        """สร้างภาพด้วย Stable Diffusion"""
        
        # เตรียม prompt
        enhanced_request = await self._enhance_request(request)
        
        # ตรวจสอบ safety
        if self.sd_config.safety_filter:
            safe_request = self._apply_safety_filter(enhanced_request)
        else:
            safe_request = enhanced_request
        
        # เลือกวิธีการสร้าง
        if self.sd_config.use_local_installation and self.local_sd_available:
            return await self._generate_local(safe_request)
        else:
            return await self._generate_api(safe_request)

    async def _enhance_request(self, request: ImageGenerationRequest) -> ImageGenerationRequest:
        """ปรับปรุง request ด้วย prompt enhancement"""
        
        if not self.sd_config.enhanced_prompt:
            return request
        
        style_enhancer = self.prompt_enhancers.get(request.style, {})
        
        # ปรับปรุง positive prompt
        enhanced_prompt = request.prompt
        
        if "style_prompt" in style_enhancer:
            enhanced_prompt = f"{enhanced_prompt}, {style_enhancer['style_prompt']}"
        
        if "positive_keywords" in style_enhancer:
            keywords = style_enhancer["positive_keywords"][:3]  # เอาแค่ 3 keywords แรก
            enhanced_prompt += f", {', '.join(keywords)}"
        
        # ปรับปรุง negative prompt
        enhanced_negative = request.negative_prompt or ""
        
        if "negative_keywords" in style_enhancer:
            negative_keywords = style_enhancer["negative_keywords"]
            if enhanced_negative:
                enhanced_negative += f", {', '.join(negative_keywords)}"
            else:
                enhanced_negative = ", ".join(negative_keywords)
        
        # สร้าง enhanced request
        enhanced_request = ImageGenerationRequest(
            prompt=enhanced_prompt,
            negative_prompt=enhanced_negative,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            quality=request.quality,
            width=request.width,
            height=request.height,
            seed=request.seed,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            model=request.model or self.sd_config.default_model,
            additional_params=request.additional_params
        )
        
        return enhanced_request

    def _apply_safety_filter(self, request: ImageGenerationRequest) -> ImageGenerationRequest:
        """ใช้ safety filter กับ prompt"""
        
        prompt = request.prompt.lower()
        safety = self.safety_settings
        
        # ตรวจสอบ blocked keywords
        for blocked in safety["blocked_keywords"]:
            if blocked in prompt:
                raise ImageGenerationError(f"Prompt contains blocked content: {blocked}")
        
        # แทนที่คำที่มีปัญหา
        filtered_prompt = request.prompt
        for original, replacement in safety["auto_replace"].items():
            filtered_prompt = filtered_prompt.replace(original, replacement)
        
        # เตือนเกี่ยวกับ warning keywords
        for warning in safety["warning_keywords"]:
            if warning in prompt:
                self.logger.warning(f"Prompt contains potentially sensitive content: {warning}")
        
        # สร้าง filtered request
        filtered_request = ImageGenerationRequest(
            prompt=filtered_prompt,
            negative_prompt=request.negative_prompt,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            quality=request.quality,
            width=request.width,
            height=request.height,
            seed=request.seed,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            model=request.model,
            additional_params=request.additional_params
        )
        
        return filtered_request

    async def _generate_local(self, request: ImageGenerationRequest) -> str:
        """สร้างภาพด้วย local Stable Diffusion"""
        
        try:
            # สร้าง temporary script
            script_content = self._create_generation_script(request)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            # รัน script
            python_executable = "python"  # หรือ path ไปยัง Python ที่ติดตั้ง diffusers
            
            process = await asyncio.create_subprocess_exec(
                python_executable, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.sd_config.local_sd_path
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise ImageGenerationError(f"Local SD generation failed: {error_msg}")
            
            # หา path ของภาพที่สร้าง
            output_path = stdout.decode().strip().split('\n')[-1]
            
            # ย้ายไฟล์ไปยัง output directory
            final_path = await self._move_to_output_directory(output_path)
            
            # ลบ temporary script
            os.unlink(script_path)
            
            return final_path
            
        except Exception as e:
            self.logger.error(f"Local generation failed: {e}")
            raise ImageGenerationError(f"Local generation failed: {e}")

    def _create_generation_script(self, request: ImageGenerationRequest) -> str:
        """สร้าง Python script สำหรับ local generation"""
        
        script = f'''
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import os
from datetime import datetime
import uuid

# Setup
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "{request.model or self.sd_config.default_model}"

# Load pipeline
pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    safety_checker=None,  # ใช้ safety filter ของเราแทน
    requires_safety_checker=False
)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to(device)

# Generation parameters
prompt = """{request.prompt}"""
negative_prompt = """{request.negative_prompt or ""}"""
width = {request.width or 512}
height = {request.height or 512}
num_inference_steps = {request.steps or 25}
guidance_scale = {request.guidance_scale or 7.5}
seed = {request.seed or -1}

# Set seed if specified
if seed != -1:
    torch.manual_seed(seed)

# Generate image
with torch.autocast(device):
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt if negative_prompt else None,
        width=width,
        height=height,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale
    ).images[0]

# Save image
timestamp = int(datetime.now().timestamp())
filename = f"sd_local_{{timestamp}}_{{uuid.uuid4().hex[:8]}}.png"
output_path = os.path.join("{self.config.output_directory}", filename)
image.save(output_path)

# Output path for parent process
print(output_path)
'''
        
        return script

    async def _generate_api(self, request: ImageGenerationRequest) -> str:
        """สร้างภาพด้วย Stability AI API"""
        
        if not self.sd_config.api_key:
            raise ImageGenerationError("API key required for Stability AI")
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # เตรียม payload
            payload = {
                "text_prompts": [
                    {"text": request.prompt, "weight": 1.0}
                ],
                "cfg_scale": request.guidance_scale or 7.0,
                "height": request.height or 512,
                "width": request.width or 512,
                "samples": 1,
                "steps": request.steps or 30,
            }
            
            # เพิ่ม negative prompt
            if request.negative_prompt:
                payload["text_prompts"].append({
                    "text": request.negative_prompt,
                    "weight": -1.0
                })
            
            # เพิ่ม seed
            if request.seed:
                payload["seed"] = request.seed
            
            # Headers
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.sd_config.api_key}",
            }
            
            # API endpoint
            model = request.model or self.sd_config.default_model
            url = f"{self.sd_config.api_endpoint}/v1/generation/{model}/text-to-image"
            
            # ส่ง request
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ImageGenerationError(f"API error {response.status}: {error_text}")
                
                response_data = await response.json()
                
                # ดาวน์โหลดและบันทึกภาพ
                return await self._save_api_image(response_data)
                
        except aiohttp.ClientError as e:
            raise ImageGenerationError(f"API request failed: {e}")
        except Exception as e:
            raise ImageGenerationError(f"API generation failed: {e}")

    async def _save_api_image(self, response_data: Dict) -> str:
        """บันทึกภาพจาก API response"""
        
        if "artifacts" not in response_data:
            raise ImageGenerationError("No image data in API response")
        
        artifacts = response_data["artifacts"]
        if not artifacts:
            raise ImageGenerationError("Empty artifacts in API response")
        
        # เอาภาพแรก
        image_data = artifacts[0]
        
        if "base64" not in image_data:
            raise ImageGenerationError("No base64 data in artifact")
        
        # Decode base64
        image_bytes = base64.b64decode(image_data["base64"])
        
        # สร้างชื่อไฟล์
        timestamp = int(datetime.now().timestamp())
        filename = f"sd_api_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        image_path = os.path.join(self.config.output_directory, filename)
        
        # บันทึกไฟล์
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(image_bytes)
        
        return image_path

    async def _move_to_output_directory(self, source_path: str) -> str:
        """ย้ายไฟล์ไปยัง output directory"""
        
        source = Path(source_path)
        if not source.exists():
            raise ImageGenerationError(f"Generated image not found: {source_path}")
        
        # สร้างชื่อไฟล์ใหม่
        timestamp = int(datetime.now().timestamp())
        new_filename = f"sd_local_{timestamp}_{uuid.uuid4().hex[:8]}{source.suffix}"
        destination = Path(self.config.output_directory) / new_filename
        
        # ย้ายไฟล์
        import shutil
        shutil.move(str(source), str(destination))
        
        return str(destination)

    # Additional features specific to Stable Diffusion

    async def generate_img2img(self, base_image_path: str, prompt: str,
                              strength: float = 0.8, **kwargs) -> str:
        """
        Image-to-image generation (ต้องการ base image)
        """
        
        if not self.sd_config.enable_img2img:
            raise ImageGenerationError("Image-to-image generation not enabled")
        
        # สำหรับ local installation
        if self.sd_config.use_local_installation and self.local_sd_available:
            return await self._generate_img2img_local(base_image_path, prompt, strength, **kwargs)
        else:
            return await self._generate_img2img_api(base_image_path, prompt, strength, **kwargs)

    async def _generate_img2img_local(self, base_image_path: str, prompt: str,
                                    strength: float, **kwargs) -> str:
        """Local img2img generation"""
        
        script = f'''
import torch
from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image
import os
from datetime import datetime
import uuid

# Setup
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "{self.sd_config.default_model}"

# Load pipeline
pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    safety_checker=None,
    requires_safety_checker=False
)
pipe = pipe.to(device)

# Load base image
base_image = Image.open("{base_image_path}").convert("RGB")

# Generation parameters
prompt = """{prompt}"""
strength = {strength}
guidance_scale = {kwargs.get('guidance_scale', 7.5)}
num_inference_steps = {kwargs.get('steps', 30)}

# Generate image
with torch.autocast(device):
    image = pipe(
        prompt=prompt,
        image=base_image,
        strength=strength,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps
    ).images[0]

# Save image
timestamp = int(datetime.now().timestamp())
filename = f"sd_img2img_{{timestamp}}_{{uuid.uuid4().hex[:8]}}.png"
output_path = os.path.join("{self.config.output_directory}", filename)
image.save(output_path)

print(output_path)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            script_path = f.name
        
        try:
            process = await asyncio.create_subprocess_exec(
                "python", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise ImageGenerationError(f"Img2Img generation failed: {error_msg}")
            
            output_path = stdout.decode().strip().split('\n')[-1]
            return output_path
            
        finally:
            os.unlink(script_path)

    async def _generate_img2img_api(self, base_image_path: str, prompt: str,
                                  strength: float, **kwargs) -> str:
        """API img2img generation"""
        
        # อ่านภาพฐาน
        async with aiofiles.open(base_image_path, 'rb') as f:
            image_data = await f.read()
        
        image_b64 = base64.b64encode(image_data).decode()
        
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "init_image": image_b64,
            "image_strength": strength,
            "cfg_scale": kwargs.get('guidance_scale', 7.0),
            "steps": kwargs.get('steps', 30),
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.sd_config.api_key}",
        }
        
        url = f"{self.sd_config.api_endpoint}/v1/generation/{self.sd_config.default_model}/image-to-image"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ImageGenerationError(f"Img2Img API error {response.status}: {error_text}")
            
            response_data = await response.json()
            return await self._save_api_image(response_data)

    async def upscale_image(self, image_path: str, scale_factor: int = 2) -> str:
        """
        Upscale ภาพด้วย Real-ESRGAN หรือ similar
        """
        
        if not self.sd_config.enable_upscaling:
            raise ImageGenerationError("Image upscaling not enabled")
        
        # ในการใช้งานจริงจะใช้ Real-ESRGAN หรือ upscaling models
        # ตอนนี้ใช้ simple PIL upscaling
        
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                new_size = (img.width * scale_factor, img.height * scale_factor)
                upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # บันทึกภาพที่ upscale แล้ว
                timestamp = int(datetime.now().timestamp())
                filename = f"sd_upscaled_{scale_factor}x_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                output_path = os.path.join(self.config.output_directory, filename)
                
                upscaled.save(output_path)
                return output_path
                
        except Exception as e:
            raise ImageGenerationError(f"Upscaling failed: {e}")

    def get_available_models(self) -> List[str]:
        """ได้รายการ models ที่รองรับ"""
        return self.sd_config.available_models

    def set_model(self, model_name: str):
        """เปลี่ยน model ที่ใช้"""
        if model_name in self.sd_config.available_models:
            self.sd_config.default_model = model_name
        else:
            raise ValueError(f"Model {model_name} not supported")

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """ได้ข้อมูล model"""
        return self.model_settings.get(model_name, {})

    async def __aenter__(self):
        """Async context manager entry"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            self.session = None


# Utility functions สำหรับ Stable Diffusion

def create_sd_config(api_key: str = None, use_local: bool = False,
                    local_path: str = None) -> StableDiffusionConfig:
    """
    สร้าง configuration สำหรับ Stable Diffusion
    """
    
    config = StableDiffusionConfig()
    config.api_key = api_key
    config.use_local_installation = use_local
    config.local_sd_path = local_path
    
    return config


async def quick_generate_sd(prompt: str, api_key: str = None,
                          style: ImageStyle = ImageStyle.REALISTIC) -> str:
    """
    ฟังก์ชันสร้างภาพแบบง่าย
    """
    
    config = create_sd_config(api_key=api_key)
    
    async with StableDiffusionAI(api_key, config, QualityTier.BALANCED) as sd:
        result = await sd.generate_image(prompt, style)
        return result.image_path


if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    async def example_usage():
        
        # Setup
        api_key = "your-stability-ai-api-key"  # ใส่ API key จริง
        
        config = create_sd_config(
            api_key=api_key,
            use_local=False  # ใช้ API แทน local
        )
        
        processing_config = ImageProcessingConfig(
            output_directory="./sd_generated",
            watermark_enabled=True,
            watermark_text="Generated by SD"
        )
        
        print("🎨 เริ่มทดสอบ Stable Diffusion...")
        
        try:
            async with StableDiffusionAI(api_key, config, QualityTier.BALANCED, processing_config) as sd:
                
                # ทดสอบการสร้างภาพพื้นฐาน
                result1 = await sd.generate_image(
                    prompt="a beautiful sunset over mountains with lake reflection",
                    style=ImageStyle.REALISTIC,
                    aspect_ratio=AspectRatio.LANDSCAPE
                )
                
                print(f"✅ สร้างภาพพื้นฐานเสร็จ: {result1.image_path}")
                print(f"   คุณภาพ: {result1.quality_score}/10")
                print(f"   ต้นทุน: {result1.cost_estimate} บาท")
                print(f"   เวลา: {result1.generation_time:.2f}s")
                
                # ทดสอบ styles ต่างๆ
                styles_test = [
                    (ImageStyle.CARTOON, "cute cartoon cat sitting in garden"),
                    (ImageStyle.ANIME, "anime girl with blue hair in magical forest"),
                    (ImageStyle.MINIMALIST, "simple geometric shapes on white background"),
                    (ImageStyle.DIGITAL_ART, "futuristic cyberpunk city at night")
                ]
                
                print("\n🎭 ทดสอบ styles ต่างๆ...")
                
                for style, prompt in styles_test:
                    try:
                        result = await sd.generate_image(prompt, style)
                        print(f"✅ {style.value}: {result.image_path}")
                    except Exception as e:
                        print(f"❌ {style.value}: {e}")
                
                # ทดสอบ batch generation
                print("\n📦 ทดสอบ batch generation...")
                
                batch_prompts = [
                    "peaceful forest scene",
                    "modern architecture building",
                    "abstract colorful pattern"
                ]
                
                batch_results = await sd.generate_multiple_images(
                    batch_prompts,
                    style=ImageStyle.DIGITAL_ART
                )
                
                print(f"✅ Batch generation เสร็จ: {len(batch_results)} ภาพ")
                for i, result in enumerate(batch_results):
                    print(f"   {i+1}. {result.image_path}")
                
                # ทดสอบ variations
                print("\n🔄 ทดสอบ variations...")
                
                variations = await sd.generate_variations(
                    "magical crystal cave with glowing crystals",
                    count=3,
                    style=ImageStyle.DIGITAL_ART
                )
                
                print(f"✅ Variations เสร็จ: {len(variations)} ภาพ")
                
                # ทดสอบ model switching
                print("\n🔧 ทดสอบ model switching...")
                
                available_models = sd.get_available_models()
                print(f"📋 Models ที่รองรับ: {available_models}")
                
                # เปลี่ยน model
                try:
                    sd.set_model("stable-diffusion-v1-6")
                    print(f"🔄 เปลี่ยนเป็น model: {sd._get_model_name()}")
                    
                    model_info = sd.get_model_info("stable-diffusion-v1-6")
                    print(f"📊 Model info: {model_info}")
                    
                    # สร้างภาพด้วย model ใหม่
                    result_new_model = await sd.generate_image(
                        "serene japanese garden with cherry blossoms",
                        style=ImageStyle.REALISTIC
                    )
                    
                    print(f"✅ สร้างด้วย model ใหม่เสร็จ: {result_new_model.image_path}")
                    
                except Exception as e:
                    print(f"❌ Model switching error: {e}")
                
                # ทดสอบ advanced features
                print("\n🚀 ทดสอบ advanced features...")
                
                # Custom request with specific parameters
                from .base_image_ai import ImageGenerationRequest
                
                custom_request = ImageGenerationRequest(
                    prompt="epic fantasy dragon flying over castle, highly detailed",
                    negative_prompt="blurry, low quality, cartoon",
                    style=ImageStyle.DIGITAL_ART,
                    width=768,
                    height=768,
                    steps=40,
                    guidance_scale=8.5,
                    seed=12345
                )
                
                custom_result = await sd.generate_image_from_request(custom_request)
                print(f"✅ Custom request เสร็จ: {custom_result.image_path}")
                print(f"   Seed ที่ใช้: {custom_request.seed}")
                print(f"   Steps: {custom_request.steps}")
                print(f"   Guidance: {custom_request.guidance_scale}")
                
                # ทดสอบ upscaling (ถ้า enable)
                if sd.sd_config.enable_upscaling:
                    print("\n📈 ทดสอบ upscaling...")
                    try:
                        upscaled_path = await sd.upscale_image(custom_result.image_path, scale_factor=2)
                        print(f"✅ Upscaling เสร็จ: {upscaled_path}")
                    except Exception as e:
                        print(f"❌ Upscaling error: {e}")
                
                # ดูสถิติรวม
                print("\n📊 สถิติการสร้างภาพ:")
                stats = sd.get_generation_statistics()
                print(f"   Total requests: {stats['total_requests']}")
                print(f"   Success rate: {stats['success_rate']}%")
                print(f"   Average cost: {stats['average_cost_per_image']} บาท/ภาพ")
                print(f"   Average time: {stats['average_generation_time']:.2f}s")
                print(f"   Cache hit rate: {stats['cache_hit_rate']}%")
                print(f"   Total cost: {stats['total_cost']} บาท")
                
                # ทดสอบ cost estimation
                print("\n💰 ทดสอบ cost estimation...")
                
                test_request = ImageGenerationRequest(
                    prompt="test prompt",
                    style=ImageStyle.REALISTIC,
                    width=1024,
                    height=1024,
                    steps=50,
                    quality=ImageQuality.HIGH
                )
                
                estimated_cost = sd.get_cost_estimate(test_request)
                estimated_time = sd.estimate_generation_time(test_request)
                
                print(f"   Estimated cost: {estimated_cost} บาท")
                print(f"   Estimated time: {estimated_time:.1f}s")
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
            import traceback
            traceback.print_exc()
    
    # รัน example
    print("🎨 Stable Diffusion Test Suite")
    print("="*50)
    asyncio.run(example_usage())


# Additional utility functions

def create_prompt_variations(base_prompt: str, style: ImageStyle = ImageStyle.REALISTIC) -> List[str]:
    """
    สร้าง variations ของ prompt สำหรับการทดสอบ
    """
    
    style_modifiers = {
        ImageStyle.REALISTIC: [
            "photorealistic",
            "professional photography",
            "highly detailed",
            "8k resolution"
        ],
        ImageStyle.CARTOON: [
            "cartoon style",
            "animated",
            "colorful illustration",
            "cute and friendly"
        ],
        ImageStyle.ANIME: [
            "anime art style",
            "manga illustration",
            "japanese animation",
            "studio quality"
        ],
        ImageStyle.DIGITAL_ART: [
            "digital painting",
            "concept art",
            "artstation trending",
            "matte painting"
        ],
        ImageStyle.MINIMALIST: [
            "minimalist design",
            "clean and simple",
            "geometric shapes",
            "negative space"
        ]
    }
    
    modifiers = style_modifiers.get(style, ["detailed", "high quality"])
    
    variations = []
    for modifier in modifiers:
        variations.append(f"{base_prompt}, {modifier}")
    
    return variations


def analyze_sd_costs(results: List[Any]) -> Dict[str, Any]:
    """
    วิเคราะห์ต้นทุนจากผลลัพธ์การสร้างภาพหลายรูป
    """
    
    if not results:
        return {"error": "No results to analyze"}
    
    costs = [r.cost_estimate for r in results]
    times = [r.generation_time for r in results]
    qualities = [r.quality_score for r in results]
    
    analysis = {
        "total_cost": sum(costs),
        "average_cost": sum(costs) / len(costs),
        "min_cost": min(costs),
        "max_cost": max(costs),
        "total_time": sum(times),
        "average_time": sum(times) / len(times),
        "average_quality": sum(qualities) / len(qualities),
        "cost_per_quality_point": sum(costs) / sum(qualities) if sum(qualities) > 0 else 0,
        "images_generated": len(results)
    }
    
    return analysis


def create_style_comparison_prompts() -> Dict[ImageStyle, str]:
    """
    สร้าง prompts สำหรับเปรียบเทียบ styles ต่างๆ
    """
    
    base_prompt = "beautiful landscape with mountains, lake, and sunset"
    
    return {
        style: f"{base_prompt}, {style.value} style"
        for style in ImageStyle
    }


def estimate_batch_cost(prompts: List[str], quality_tier: QualityTier = QualityTier.BALANCED) -> Dict[str, float]:
    """
    ประมาณต้นทุนการสร้างภาพ batch
    """
    
    base_costs = {
        QualityTier.BUDGET: 2.0,
        QualityTier.BALANCED: 8.0,
        QualityTier.PREMIUM: 25.0
    }
    
    base_cost = base_costs.get(quality_tier, 8.0)
    
    # ปรับตามความซับซ้อนของ prompt
    total_cost = 0.0
    for prompt in prompts:
        # ประมาณความซับซ้อนจากความยาว prompt
        complexity_multiplier = 1.0 + (len(prompt.split()) / 50)
        cost = base_cost * complexity_multiplier
        total_cost += cost
    
    return {
        "total_estimated_cost": round(total_cost, 2),
        "average_cost_per_image": round(total_cost / len(prompts), 2),
        "number_of_images": len(prompts),
        "quality_tier": quality_tier.value
    }


# Error handling utilities

class StableDiffusionError(ImageGenerationError):
    """Specific error class for Stable Diffusion"""
    pass


def handle_sd_api_error(response_status: int, response_text: str) -> str:
    """
    จัดการ error messages จาก Stability AI API
    """
    
    error_messages = {
        400: "Invalid request parameters",
        401: "Invalid API key",
        402: "Insufficient credits",
        403: "Access forbidden",
        404: "Model not found",
        429: "Rate limit exceeded",
        500: "Server error"
    }
    
    base_message = error_messages.get(response_status, "Unknown API error")
    
    # พยายามแยก error details จาก response
    try:
        import json
        error_data = json.loads(response_text)
        if "message" in error_data:
            return f"{base_message}: {error_data['message']}"
    except:
        pass
    
    return f"{base_message} (Status: {response_status})"


# Configuration helpers

def get_optimal_sd_settings(target_quality: ImageQuality, 
                           target_size: tuple = (512, 512)) -> Dict[str, Any]:
    """
    ได้การตั้งค่าที่เหมาะสมสำหรับคุณภาพและขนาดที่ต้องการ
    """
    
    settings = {
        ImageQuality.LOW: {
            "steps": 15,
            "guidance_scale": 6.0,
            "max_size": (512, 512)
        },
        ImageQuality.MEDIUM: {
            "steps": 25,
            "guidance_scale": 7.5,
            "max_size": (768, 768)
        },
        ImageQuality.HIGH: {
            "steps": 35,
            "guidance_scale": 8.0,
            "max_size": (1024, 1024)
        },
        ImageQuality.ULTRA: {
            "steps": 50,
            "guidance_scale": 9.0,
            "max_size": (1536, 1536)
        }
    }
    
    base_settings = settings.get(target_quality, settings[ImageQuality.MEDIUM])
    
    # ปรับขนาดตามที่ต้องการ
    max_dimension = max(target_size)
    max_allowed = max(base_settings["max_size"])
    
    if max_dimension > max_allowed:
        # ลดขนาดให้พอดี
        scale = max_allowed / max_dimension
        adjusted_size = (int(target_size[0] * scale), int(target_size[1] * scale))
    else:
        adjusted_size = target_size
    
    return {
        "width": adjusted_size[0],
        "height": adjusted_size[1],
        "steps": base_settings["steps"],
        "guidance_scale": base_settings["guidance_scale"]
    }