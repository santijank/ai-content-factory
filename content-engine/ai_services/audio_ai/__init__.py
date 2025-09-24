"""
Audio AI Services Package
Text-to-Speech services for AI Content Factory

This package provides various TTS services across different quality tiers:
- Budget: Google TTS (Free)
- Balanced: Azure Cognitive Services TTS
- Premium: ElevenLabs AI Voice

Usage:
    from content_engine.ai_services.audio_ai import BaseAudioAI, AudioConfig, AudioResult
    from content_engine.ai_services.audio_ai.gtts_service import GTTSService
    from content_engine.ai_services.audio_ai.azure_tts import AzureTTSService
    from content_engine.ai_services.audio_ai.elevenlabs_service import ElevenLabsService
"""

from .base_audio_ai import (
    BaseAudioAI,
    AudioConfig,
    AudioResult,
    combine_audio_results,
    save_audio_result,
    audio_config_from_plan
)

# Import specific services (will be available after we create them)
try:
    from .gtts_service import GTTSService
except ImportError:
    GTTSService = None

try:
    from .azure_tts import AzureTTSService
except ImportError:
    AzureTTSService = None

try:
    from .elevenlabs_service import ElevenLabsService
except ImportError:
    ElevenLabsService = None

# Available services registry
AVAILABLE_SERVICES = {}

if GTTSService:
    AVAILABLE_SERVICES['gtts'] = GTTSService
if AzureTTSService:
    AVAILABLE_SERVICES['azure'] = AzureTTSService
if ElevenLabsService:
    AVAILABLE_SERVICES['elevenlabs'] = ElevenLabsService

# Service tier mapping
SERVICE_TIERS = {
    'budget': 'gtts',
    'balanced': 'azure', 
    'premium': 'elevenlabs'
}

def get_service_by_tier(tier: str) -> type:
    """
    Get audio service class by quality tier
    
    Args:
        tier: Quality tier ('budget', 'balanced', 'premium')
        
    Returns:
        Service class or None if not available
    """
    service_name = SERVICE_TIERS.get(tier.lower())
    if service_name and service_name in AVAILABLE_SERVICES:
        return AVAILABLE_SERVICES[service_name]
    return None

def get_available_services() -> dict:
    """
    Get all available audio services
    
    Returns:
        Dictionary of available services
    """
    return AVAILABLE_SERVICES.copy()

def create_service(service_name: str, api_key: str = None, config: dict = None):
    """
    Factory function to create audio service instance
    
    Args:
        service_name: Name of the service ('gtts', 'azure', 'elevenlabs')
        api_key: API key for the service (if required)
        config: Additional configuration
        
    Returns:
        Service instance or None if service not available
    """
    if service_name in AVAILABLE_SERVICES:
        service_class = AVAILABLE_SERVICES[service_name]
        return service_class(api_key=api_key, config=config)
    return None

# Version info
__version__ = "1.0.0"
__author__ = "AI Content Factory Team"

# Package exports
__all__ = [
    'BaseAudioAI',
    'AudioConfig', 
    'AudioResult',
    'GTTSService',
    'AzureTTSService', 
    'ElevenLabsService',
    'combine_audio_results',
    'save_audio_result',
    'audio_config_from_plan',
    'get_service_by_tier',
    'get_available_services',
    'create_service',
    'AVAILABLE_SERVICES',
    'SERVICE_TIERS'
]