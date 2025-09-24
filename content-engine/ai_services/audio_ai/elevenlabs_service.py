"""
ElevenLabs AI Voice Service (Premium Tier)
High-quality AI voice synthesis with emotional control

Features:
- Ultra-realistic AI voices
- Emotional and style control
- Voice cloning capabilities
- Multiple languages with native accent
- Professional broadcast quality
- Advanced voice settings
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import base64

from .base_audio_ai import BaseAudioAI, AudioConfig, AudioResult

class ElevenLabsService(BaseAudioAI):
    """
    ElevenLabs AI Voice service implementation
    Premium tier - Professional quality with advanced features
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize ElevenLabs service
        
        Args:
            api_key: ElevenLabs API key
            config: Additional configuration
        """
        super().__init__(api_key=api_key, config=config)
        self.service_name = "ElevenLabs AI Voice (Premium)"
        
        # ElevenLabs configuration
        self.base_url = "https://api.elevenlabs.io/v1"
        self.max_chars = 5000  # ElevenLabs limit per request for free tier
        self.max_chars_premium = 100000  # Higher limit for paid plans
        
        # Voice style to ElevenLabs voice ID mapping
        self.premium_voices = {
            "neutral": {
                "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel - English
                "th": "pNInz6obpgDQGcFmaJgB"   # Adam (works well for Thai)
            },
            "energetic": {
                "en": "EXAVITQu4vr4xnSDxMaL",  # Bella - Energetic female
                "th": "VR6AewLTigWG4xSOukaG"   # Josh (energetic male)
            },
            "calm": {
                "en": "CYw3kZ02Hs0563khs1Fj",  # Dave - Calm male
                "th": "pNInz6obpgDQGcFmaJgB"   # Adam (calm style)
            },
            "professional": {
                "en": "TX3LPaxmHKxFdv7VOQHJ",  # Liam - Professional
                "th": "21m00Tcm4TlvDq8ikWAM"   # Rachel (professional)
            }
        }
        
        # Voice settings for different styles
        self.voice_settings = {
            "neutral": {
                "stability": 0.75,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            },
            "energetic": {
                "stability": 0.65,
                "similarity_boost": 0.8,
                "style": 0.3,
                "use_speaker_boost": True
            },
            "calm": {
                "stability": 0.85,
                "similarity_boost": 0.7,
                "style": -0.2,
                "use_speaker_boost": True
            },
            "professional": {
                "stability": 0.8,
                "similarity_boost": 0.75,
                "style": 0.1,
                "use_speaker_boost": True
            }
        }
        
        # Pricing (ElevenLabs charges per character)
        self.cost_per_char = 0.0003  # ~30 satang per 1000 characters (premium pricing)
        
        # Model settings
        self.model_id = "eleven_multilingual_v2"  # Best model for multiple languages
        
        self.is_available = False
    
    async def text_to_speech(
        self, 
        text: str, 
        audio_config: Optional[AudioConfig] = None
    ) -> AudioResult:
        """
        Convert text to speech using ElevenLabs AI
        
        Args:
            text: Text to convert
            audio_config: Audio configuration
            
        Returns:
            AudioResult with generated audio
        """
        # Validate input
        is_valid, error_msg = self.validate_text(text)
        if not is_valid:
            raise ValueError(f"Invalid text: {error_msg}")
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
        
        # Use default config if not provided
        if audio_config is None:
            audio_config = self.create_default_config()
        
        # Check text length
        char_limit = self.max_chars_premium if self._is_premium_account() else self.max_chars
        if len(text) > char_limit:
            raise ValueError(f"Text too long. Max {char_limit} characters for your plan")
        
        try:
            # Get voice ID and settings
            voice_id = self._get_voice_id(audio_config)
            voice_settings = self._prepare_voice_settings(audio_config)
            
            # Generate speech
            audio_data = await self._generate_speech_async(text, voice_id, voice_settings, audio_config)
            
            # Calculate metadata
            duration = self._estimate_duration(text, audio_config)
            cost = self.estimate_cost(text, audio_config)
            
            return AudioResult(
                audio_data=audio_data,
                format=audio_config.format,
                duration_seconds=duration,
                file_size_bytes=len(audio_data),
                metadata={
                    "service": "elevenlabs",
                    "language": audio_config.language,
                    "voice_style": audio_config.voice_style,
                    "voice_id": voice_id,
                    "model_id": self.model_id,
                    "text_length": len(text),
                    "voice_settings": voice_settings
                },
                cost_credits=cost
            )
            
        except Exception as e:
            raise RuntimeError(f"ElevenLabs generation failed: {str(e)}")
    
    async def get_available_voices(self, language: str = "th") -> List[Dict[str, Any]]:
        """
        Get available voices from ElevenLabs
        
        Args:
            language: Language code (used for filtering)
            
        Returns:
            List of available voices
        """
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/voices", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        voices = []
                        
                        for voice in data.get("voices", []):
                            # Extract voice information
                            voice_info = {
                                "id": voice.get("voice_id", ""),
                                "name": voice.get("name", ""),
                                "language": self._detect_voice_language(voice),
                                "gender": self._detect_gender(voice.get("name", "")),
                                "style": voice.get("category", "generated"),
                                "quality": "premium",
                                "description": voice.get("description", ""),
                                "accent": voice.get("labels", {}).get("accent", ""),
                                "age": voice.get("labels", {}).get("age", ""),
                                "use_case": voice.get("labels", {}).get("use case", "")
                            }
                            voices.append(voice_info)
                        
                        return voices
                    else:
                        return self._get_fallback_voices(language)
                        
        except Exception:
            return self._get_fallback_voices(language)
    
    async def check_service_health(self) -> bool:
        """
        Check if ElevenLabs service is available
        
        Returns:
            True if service is healthy
        """
        try:
            if not self.api_key:
                self.is_available = False
                return False
            
            # Check API key validity by getting user info
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/user", headers=headers) as response:
                    if response.status == 200:
                        self.is_available = True
                        return True
                    else:
                        self.is_available = False
                        return False
            
        except Exception:
            self.is_available = False
            return False
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes
        
        Returns:
            List of language codes
        """
        return ["en", "th", "ja", "ko", "zh", "es", "fr", "de", "it", "pt", "pl", "hi", "ar"]
    
    def get_supported_formats(self) -> List[str]:
        """
        Get supported audio formats
        
        Returns:
            List of supported formats
        """
        return ["mp3", "wav", "ogg"]
    
    def estimate_cost(self, text: str, audio_config: Optional[AudioConfig] = None) -> float:
        """
        Estimate cost for ElevenLabs TTS
        
        Args:
            text: Text to be converted
            audio_config: Audio configuration
            
        Returns:
            Estimated cost in Thai Baht
        """
        char_count = len(text)
        return char_count * self.cost_per_char
    
    def _get_voice_id(self, audio_config: AudioConfig) -> str:
        """
        Get appropriate voice ID for the configuration
        
        Args:
            audio_config: Audio configuration
            
        Returns:
            Voice ID
        """
        lang_code = "en" if audio_config.language.startswith("en") else "th"
        
        voice_map = self.premium_voices.get(audio_config.voice_style, self.premium_voices["neutral"])
        return voice_map.get(lang_code, voice_map["en"])
    
    def _prepare_voice_settings(self, audio_config: AudioConfig) -> Dict[str, Any]:
        """
        Prepare voice settings for ElevenLabs
        
        Args:
            audio_config: Audio configuration
            
        Returns:
            Voice settings dictionary
        """
        base_settings = self.voice_settings.get(
            audio_config.voice_style, 
            self.voice_settings["neutral"]
        ).copy()
        
        # Adjust stability based on speed
        if audio_config.speed > 1.2:
            base_settings["stability"] = max(0.3, base_settings["stability"] - 0.2)
        elif audio_config.speed < 0.8:
            base_settings["stability"] = min(1.0, base_settings["stability"] + 0.1)
        
        # Adjust style based on pitch
        if audio_config.pitch > 1.1:
            base_settings["style"] = min(1.0, base_settings["style"] + 0.2)
        elif audio_config.pitch < 0.9:
            base_settings["style"] = max(-1.0, base_settings["style"] - 0.2)
        
        return base_settings
    
    async def _generate_speech_async(
        self, 
        text: str, 
        voice_id: str, 
        voice_settings: Dict[str, Any],
        audio_config: AudioConfig
    ) -> bytes:
        """
        Generate speech using ElevenLabs API
        
        Args:
            text: Text to convert
            voice_id: ElevenLabs voice ID
            voice_settings: Voice configuration
            audio_config: Audio configuration
            
        Returns:
            Audio data as bytes
        """
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        # Prepare request data
        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": voice_settings
        }
        
        # Add pronunciation dictionary if needed (for Thai text)
        if audio_config.language.startswith("th"):
            data["pronunciation_dictionary_locators"] = []
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    
                    # Apply post-processing if needed
                    if audio_config.format != "mp3":
                        audio_data = await self._convert_audio_format(audio_data, "mp3", audio_config.format)
                    
                    return audio_data
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"ElevenLabs API error {response.status}: {error_text}")
    
    async def _convert_audio_format(self, audio_data: bytes, from_format: str, to_format: str) -> bytes:
        """
        Convert audio format (placeholder - would need actual audio processing library)
        
        Args:
            audio_data: Input audio data
            from_format: Source format
            to_format: Target format
            
        Returns:
            Converted audio data
        """
        # For now, return as-is. In production, use ffmpeg or similar
        # This would require additional dependencies like pydub or ffmpeg-python
        return audio_data
    
    def _estimate_duration(self, text: str, audio_config: AudioConfig) -> float:
        """
        Estimate audio duration for ElevenLabs voices
        
        Args:
            text: Text to convert
            audio_config: Audio configuration
            
        Returns:
            Estimated duration in seconds
        """
        # ElevenLabs voices are quite natural, estimate based on natural speech
        words = len(text.split())
        base_wpm = 180  # Faster than traditional TTS
        
        if audio_config.language.startswith("th"):
            base_wpm = 150  # Thai is typically slower
        
        base_duration = (words / base_wpm) * 60
        
        # Adjust for voice style
        style_multipliers = {
            "energetic": 0.9,
            "calm": 1.2,
            "professional": 1.0,
            "neutral": 1.0
        }
        
        style_multiplier = style_multipliers.get(audio_config.voice_style, 1.0)
        base_duration *= style_multiplier
        
        return max(1.0, base_duration)
    
    def _detect_voice_language(self, voice_data: Dict[str, Any]) -> str:
        """
        Detect language from voice data
        
        Args:
            voice_data: Voice information from API
            
        Returns:
            Language code
        """
        labels = voice_data.get("labels", {})
        accent = labels.get("accent", "").lower()
        
        # Simple language detection based on accent
        if "british" in accent or "american" in accent or "australian" in accent:
            return "en"
        elif "thai" in accent:
            return "th"
        elif "japanese" in accent:
            return "ja"
        elif "korean" in accent:
            return "ko"
        else:
            return "en"  # Default to English
    
    def _detect_gender(self, name: str) -> str:
        """
        Detect gender from voice name (simple heuristic)
        
        Args:
            name: Voice name
            
        Returns:
            Gender string
        """
        name_lower = name.lower()
        
        # Simple name-based detection
        female_indicators = ["bella", "rachel", "domi", "elli", "sarah", "emily"]
        male_indicators = ["adam", "josh", "liam", "dave", "ethan", "sam"]
        
        for indicator in female_indicators:
            if indicator in name_lower:
                return "female"
        
        for indicator in male_indicators:
            if indicator in name_lower:
                return "male"
        
        return "neutral"
    
    def _is_premium_account(self) -> bool:
        """
        Check if this is a premium account (placeholder)
        
        Returns:
            True if premium account
        """
        # In production, this would check the actual account status
        # For now, assume premium if API key is provided
        return bool(self.api_key)
    
    def _get_fallback_voices(self, language: str) -> List[Dict[str, Any]]:
        """
        Get fallback voice list when API is unavailable
        
        Args:
            language: Language code
            
        Returns:
            List of fallback voices
        """
        return [
            {
                "id": "21m00Tcm4TlvDq8ikWAM",
                "name": "Rachel (Premium Female)",
                "language": "en",
                "gender": "female",
                "style": "premium",
                "quality": "premium",
                "description": "Natural, versatile voice suitable for various content",
                "accent": "American",
                "age": "young adult",
                "use_case": "general"
            },
            {
                "id": "pNInz6obpgDQGcFmaJgB", 
                "name": "Adam (Premium Male)",
                "language": "en",
                "gender": "male",
                "style": "premium",
                "quality": "premium",
                "description": "Deep, confident voice perfect for professional content",
                "accent": "American",
                "age": "middle aged",
                "use_case": "professional"
            }
        ]
    
    async def clone_voice(self, voice_name: str, audio_files: List[bytes]) -> str:
        """
        Clone a voice using audio samples (Premium feature)
        
        Args:
            voice_name: Name for the cloned voice
            audio_files: List of audio file data for training
            
        Returns:
            Voice ID of the cloned voice
        """
        if not self._is_premium_account():
            raise RuntimeError("Voice cloning requires premium account")
        
        # This would implement the voice cloning API
        # Placeholder for premium feature
        raise NotImplementedError("Voice cloning feature not yet implemented")
    
    def __str__(self) -> str:
        return f"ElevenLabsService(model={self.model_id}, available={self.is_available})"