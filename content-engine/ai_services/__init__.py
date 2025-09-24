"""
AI Services Package

This package contains all AI service implementations:
- Text AI: Language model services (Groq, OpenAI, Claude)
- Image AI: Image generation services (Stable Diffusion, Leonardo AI, Midjourney)
- Audio AI: Text-to-speech and audio services (GTTS, Azure TTS, ElevenLabs)
"""

# Text AI Services
from .text_ai.base_text_ai import BaseTextAI
from .text_ai.groq_service import GroqService
from .text_ai.openai_service import OpenAIService
from .text_ai.claude_service import ClaudeService

# Image AI Services  
from .image_ai.base_image_ai import BaseImageAI
from .image_ai.stable_diffusion import StableDiffusionService
from .image_ai.leonardo_ai import LeonardoAIService
from .image_ai.midjourney_api import MidjourneyService

# Audio AI Services
from .audio_ai.base_audio_ai import BaseAudioAI
from .audio_ai.gtts_service import GTTSService
from .audio_ai.azure_tts import AzureTTSService
from .audio_ai.elevenlabs_service import ElevenLabsService

__all__ = [
    # Text AI
    'BaseTextAI',
    'GroqService', 
    'OpenAIService',
    'ClaudeService',
    
    # Image AI
    'BaseImageAI',
    'StableDiffusionService',
    'LeonardoAIService', 
    'MidjourneyService',
    
    # Audio AI
    'BaseAudioAI',
    'GTTSService',
    'AzureTTSService',
    'ElevenLabsService'
]

# Service registry mappings
TEXT_AI_SERVICES = {
    'groq': GroqService,
    'openai': OpenAIService, 
    'claude': ClaudeService
}

IMAGE_AI_SERVICES = {
    'stable_diffusion': StableDiffusionService,
    'leonardo': LeonardoAIService,
    'midjourney': MidjourneyService
}

AUDIO_AI_SERVICES = {
    'gtts': GTTSService,
    'azure': AzureTTSService,
    'elevenlabs': ElevenLabsService
}

def get_text_ai_service(service_name: str, **kwargs):
    """Factory function to get text AI service"""
    if service_name not in TEXT_AI_SERVICES:
        raise ValueError(f"Unknown text AI service: {service_name}")
    return TEXT_AI_SERVICES[service_name](**kwargs)

def get_image_ai_service(service_name: str, **kwargs):
    """Factory function to get image AI service"""
    if service_name not in IMAGE_AI_SERVICES:
        raise ValueError(f"Unknown image AI service: {service_name}")
    return IMAGE_AI_SERVICES[service_name](**kwargs)

def get_audio_ai_service(service_name: str, **kwargs):
    """Factory function to get audio AI service"""
    if service_name not in AUDIO_AI_SERVICES:
        raise ValueError(f"Unknown audio AI service: {service_name}")
    return AUDIO_AI_SERVICES[service_name](**kwargs)