"""
Image AI Services Package

This package contains all image generation AI services:
- Base class for image AI services
- Stable Diffusion service implementation
- Leonardo AI service implementation
- Midjourney API service implementation
"""

from .base_image_ai import BaseImageAI
from .stable_diffusion import StableDiffusionService
from .leonardo_ai import LeonardoAIService
from .midjourney_api import MidjourneyService

__all__ = [
    'BaseImageAI',
    'StableDiffusionService',
    'LeonardoAIService',
    'MidjourneyService'
]

# Service configuration mappings
SERVICE_CONFIGS = {
    'stable_diffusion': {
        'name': 'Stable Diffusion',
        'description': 'Local/self-hosted image generation',
        'cost_tier': 'budget',
        'speed': 'medium',
        'quality': 'good',
        'max_resolution': '1024x1024'
    },
    'leonardo': {
        'name': 'Leonardo AI',
        'description': 'Balanced cloud-based image generation',
        'cost_tier': 'balanced', 
        'speed': 'fast',
        'quality': 'high',
        'max_resolution': '1536x1536'
    },
    'midjourney': {
        'name': 'Midjourney',
        'description': 'Premium artistic image generation',
        'cost_tier': 'premium',
        'speed': 'slow',
        'quality': 'very_high', 
        'max_resolution': '2048x2048'
    }
}

# Style presets for different content types
STYLE_PRESETS = {
    'youtube_thumbnail': {
        'stable_diffusion': 'vibrant colors, bold text overlay, high contrast, eye-catching',
        'leonardo': 'professional thumbnail style, clean composition, readable text',
        'midjourney': 'cinematic lighting, professional grade, magazine quality'
    },
    'social_media': {
        'stable_diffusion': 'modern, trendy, social media optimized, mobile-friendly',
        'leonardo': 'instagram-ready, clean aesthetic, good lighting',
        'midjourney': 'artistic, premium social media content, influencer style'
    },
    'educational': {
        'stable_diffusion': 'clean, professional, educational diagrams, clear visuals',
        'leonardo': 'infographic style, easy to understand, academic quality',
        'midjourney': 'sophisticated educational content, textbook quality'
    },
    'entertainment': {
        'stable_diffusion': 'fun, colorful, engaging, entertainment focused',
        'leonardo': 'dynamic, entertaining visuals, audience engagement',
        'midjourney': 'cinematic entertainment, movie poster style'
    }
}

# Platform-specific image requirements
PLATFORM_SPECS = {
    'youtube': {
        'thumbnail': {'width': 1280, 'height': 720, 'format': 'jpg'},
        'banner': {'width': 2560, 'height': 1440, 'format': 'jpg'}
    },
    'tiktok': {
        'cover': {'width': 1080, 'height': 1920, 'format': 'jpg'},
        'profile': {'width': 200, 'height': 200, 'format': 'jpg'}
    },
    'instagram': {
        'post': {'width': 1080, 'height': 1080, 'format': 'jpg'},
        'story': {'width': 1080, 'height': 1920, 'format': 'jpg'},
        'reel_cover': {'width': 1080, 'height': 1920, 'format': 'jpg'}
    },
    'facebook': {
        'post': {'width': 1200, 'height': 630, 'format': 'jpg'},
        'cover': {'width': 1640, 'height': 859, 'format': 'jpg'}
    }
}

def get_service_info(service_name: str) -> dict:
    """Get service configuration information"""
    return SERVICE_CONFIGS.get(service_name, {})

def get_style_preset(content_type: str, service_name: str) -> str:
    """Get style preset for content type and service"""
    presets = STYLE_PRESETS.get(content_type, {})
    return presets.get(service_name, '')

def get_platform_specs(platform: str, image_type: str = 'post') -> dict:
    """Get platform-specific image specifications"""
    platform_specs = PLATFORM_SPECS.get(platform, {})
    return platform_specs.get(image_type, {'width': 1080, 'height': 1080, 'format': 'jpg'})

def build_prompt(base_prompt: str, content_type: str, platform: str = None, service_name: str = 'stable_diffusion') -> str:
    """Build optimized prompt for specific service and platform"""
    # Add style preset
    style = get_style_preset(content_type, service_name)
    if style:
        base_prompt = f"{base_prompt}, {style}"
    
    # Add platform-specific optimizations
    if platform:
        if platform == 'youtube':
            base_prompt += ", youtube thumbnail style, clickbait worthy"
        elif platform == 'tiktok':
            base_prompt += ", vertical format, mobile-optimized, trendy"
        elif platform == 'instagram':
            base_prompt += ", instagram aesthetic, social media ready"
        elif platform == 'facebook':
            base_prompt += ", facebook post style, engagement focused"
    
    # Add service-specific quality indicators
    if service_name == 'midjourney':
        base_prompt += ", high quality, professional photography, 8k resolution"
    elif service_name == 'leonardo':
        base_prompt += ", high quality, detailed, clean composition"
    elif service_name == 'stable_diffusion':
        base_prompt += ", detailed, high resolution, sharp focus"
    
    return base_prompt

# Common negative prompts to improve quality
NEGATIVE_PROMPTS = {
    'general': 'blurry, low quality, distorted, ugly, bad anatomy, watermark, signature, text',
    'thumbnail': 'cluttered, unreadable text, poor contrast, low quality',
    'social_media': 'unprofessional, low engagement, boring, generic',
    'educational': 'confusing, unclear, unprofessional, misleading'
}

def get_negative_prompt(content_type: str = 'general') -> str:
    """Get appropriate negative prompt for content type"""
    return NEGATIVE_PROMPTS.get(content_type, NEGATIVE_PROMPTS['general'])