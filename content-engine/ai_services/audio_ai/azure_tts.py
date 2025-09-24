"""
Azure Text-to-Speech Service (Balanced Tier)
Microsoft Azure Cognitive Services TTS

Features:
- High quality neural voices
- Multiple voice options per language
- SSML support for advanced control
- Good pricing for moderate usage
- Professional quality output
"""

import asyncio
import aiohttp
import json
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import base64

from .base_audio_ai import BaseAudioAI, AudioConfig, AudioResult

class AzureTTSService(BaseAudioAI):
    """
    Azure Text-to-Speech service implementation
    Balanced tier - Good quality with reasonable pricing
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize Azure TTS service
        
        Args:
            api_key: Azure Cognitive Services API key
            config: Additional configuration including region
        """
        super().__init__(api_key=api_key, config=config)
        self.service_name = "Azure TTS (Balanced)"
        
        # Azure configuration
        self.region = config.get("region", "southeastasia") if config else "southeastasia"
        self.subscription_key = api_key
        self.max_chars = 10000  # Azure limit per request
        
        # Azure endpoints
        self.token_url = f"https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        self.tts_url = f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1"
        self.voices_url = f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        
        # Token management
        self.access_token = None
        self.token_expires_at = None
        
        # Voice mappings for different styles
        self.thai_voices = {
            "neutral": "th-TH-AcharaNeural",
            "calm": "th-TH-NiwatNeural", 
            "energetic": "th-TH-AcharaNeural",
            "professional": "th-TH-NiwatNeural"
        }
        
        self.english_voices = {
            "neutral": "en-US-AriaNeural",
            "calm": "en-US-DavisNeural",
            "energetic": "en-US-JaneNeural", 
            "professional": "en-US-TonyNeural"
        }
        
        # Pricing (approximate - Azure charges per character)
        self.cost_per_char = 0.000016  # ~16 satang per 1000 characters
        
        self.is_available = False
        
    async def text_to_speech(
        self, 
        text: str, 
        audio_config: Optional[AudioConfig] = None
    ) -> AudioResult:
        """
        Convert text to speech using Azure TTS
        
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
        
        if not self.subscription_key:
            raise ValueError("Azure API key is required")
        
        # Use default config if not provided
        if audio_config is None:
            audio_config = self.create_default_config()
        
        # Check text length
        if len(text) > self.max_chars:
            raise ValueError(f"Text too long. Max {self.max_chars} characters for Azure TTS")
        
        try:
            # Get access token
            await self._ensure_valid_token()
            
            # Prepare SSML
            ssml = self._create_ssml(text, audio_config)
            
            # Generate speech
            audio_data = await self._generate_speech_async(ssml, audio_config)
            
            # Calculate metadata
            duration = self._estimate_duration(text, audio_config)
            cost = self.estimate_cost(text, audio_config)
            
            return AudioResult(
                audio_data=audio_data,
                format=audio_config.format,
                duration_seconds=duration,
                file_size_bytes=len(audio_data),
                metadata={
                    "service": "azure_tts",
                    "language": audio_config.language,
                    "voice_style": audio_config.voice_style,
                    "voice_name": self._get_voice_name(audio_config),
                    "text_length": len(text),
                    "region": self.region
                },
                cost_credits=cost
            )
            
        except Exception as e:
            raise RuntimeError(f"Azure TTS generation failed: {str(e)}")
    
    async def get_available_voices(self, language: str = "th") -> List[Dict[str, Any]]:
        """
        Get available voices from Azure for the specified language
        
        Args:
            language: Language code
            
        Returns:
            List of available voices
        """
        try:
            await self._ensure_valid_token()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(self.voices_url, headers=headers) as response:
                    if response.status == 200:
                        voices_data = await response.json()
                        
                        # Filter voices by language
                        filtered_voices = []
                        for voice in voices_data:
                            if voice.get("Locale", "").startswith(language):
                                filtered_voices.append({
                                    "id": voice.get("ShortName", ""),
                                    "name": voice.get("DisplayName", ""),
                                    "language": voice.get("Locale", ""),
                                    "gender": voice.get("Gender", "").lower(),
                                    "style": voice.get("VoiceType", ""),
                                    "quality": "neural" if "Neural" in voice.get("ShortName", "") else "standard"
                                })
                        
                        return filtered_voices
                    else:
                        return self._get_fallback_voices(language)
                        
        except Exception:
            return self._get_fallback_voices(language)
    
    async def check_service_health(self) -> bool:
        """
        Check if Azure TTS service is available
        
        Returns:
            True if service is healthy
        """
        try:
            if not self.subscription_key:
                self.is_available = False
                return False
            
            # Try to get access token
            await self._ensure_valid_token()
            
            # Test with small text
            test_text = "สวัสดี"
            test_config = AudioConfig(language="th")
            
            await self.text_to_speech(test_text, test_config)
            self.is_available = True
            return True
            
        except Exception:
            self.is_available = False
            return False
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes
        
        Returns:
            List of language codes
        """
        return ["th", "en", "ja", "ko", "zh", "es", "fr", "de", "it", "pt"]
    
    def get_supported_formats(self) -> List[str]:
        """
        Get supported audio formats
        
        Returns:
            List of supported formats
        """
        return ["mp3", "wav", "ogg"]
    
    def estimate_cost(self, text: str, audio_config: Optional[AudioConfig] = None) -> float:
        """
        Estimate cost for Azure TTS
        
        Args:
            text: Text to be converted
            audio_config: Audio configuration
            
        Returns:
            Estimated cost in Thai Baht
        """
        char_count = len(text)
        return char_count * self.cost_per_char
    
    async def _ensure_valid_token(self):
        """
        Ensure we have a valid access token
        """
        if self.access_token is None or self._is_token_expired():
            await self._get_access_token()
    
    def _is_token_expired(self) -> bool:
        """
        Check if current token is expired
        
        Returns:
            True if token is expired
        """
        if self.token_expires_at is None:
            return True
        return datetime.now() >= self.token_expires_at
    
    async def _get_access_token(self):
        """
        Get access token from Azure
        """
        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "0"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, headers=headers) as response:
                if response.status == 200:
                    self.access_token = await response.text()
                    # Token expires in 10 minutes, refresh at 9 minutes
                    self.token_expires_at = datetime.now() + timedelta(minutes=9)
                else:
                    raise RuntimeError(f"Failed to get Azure access token: {response.status}")
    
    def _create_ssml(self, text: str, audio_config: AudioConfig) -> str:
        """
        Create SSML for Azure TTS
        
        Args:
            text: Text to convert
            audio_config: Audio configuration
            
        Returns:
            SSML string
        """
        voice_name = self._get_voice_name(audio_config)
        
        # Create SSML with prosody controls
        ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{audio_config.language}'>
            <voice name='{voice_name}'>
                <prosody rate='{self._get_rate_value(audio_config.speed)}' 
                         pitch='{self._get_pitch_value(audio_config.pitch)}' 
                         volume='{self._get_volume_value(audio_config.volume)}'>
                    {text}
                </prosody>
            </voice>
        </speak>"""
        
        return ssml
    
    def _get_voice_name(self, audio_config: AudioConfig) -> str:
        """
        Get appropriate voice name for the configuration
        
        Args:
            audio_config: Audio configuration
            
        Returns:
            Voice name
        """
        if audio_config.language.startswith("th"):
            return self.thai_voices.get(audio_config.voice_style, self.thai_voices["neutral"])
        elif audio_config.language.startswith("en"):
            return self.english_voices.get(audio_config.voice_style, self.english_voices["neutral"])
        else:
            # Fallback to English neutral
            return self.english_voices["neutral"]
    
    def _get_rate_value(self, speed: float) -> str:
        """
        Convert speed to Azure rate value
        
        Args:
            speed: Speed multiplier (0.5-2.0)
            
        Returns:
            Azure rate string
        """
        if speed <= 0.7:
            return "slow"
        elif speed <= 0.9:
            return "medium"
        elif speed <= 1.1:
            return "default"
        elif speed <= 1.5:
            return "fast"
        else:
            return "x-fast"
    
    def _get_pitch_value(self, pitch: float) -> str:
        """
        Convert pitch to Azure pitch value
        
        Args:
            pitch: Pitch multiplier (0.5-2.0)
            
        Returns:
            Azure pitch string
        """
        if pitch <= 0.7:
            return "x-low"
        elif pitch <= 0.9:
            return "low"
        elif pitch <= 1.1:
            return "default"
        elif pitch <= 1.5:
            return "high"
        else:
            return "x-high"
    
    def _get_volume_value(self, volume: float) -> str:
        """
        Convert volume to Azure volume value
        
        Args:
            volume: Volume multiplier (0.0-1.0)
            
        Returns:
            Azure volume string
        """
        if volume <= 0.2:
            return "x-soft"
        elif volume <= 0.4:
            return "soft"
        elif volume <= 0.6:
            return "medium"
        elif volume <= 0.8:
            return "loud"
        else:
            return "x-loud"
    
    async def _generate_speech_async(self, ssml: str, audio_config: AudioConfig) -> bytes:
        """
        Generate speech from SSML
        
        Args:
            ssml: SSML string
            audio_config: Audio configuration
            
        Returns:
            Audio data as bytes
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": self._get_output_format(audio_config.format),
            "User-Agent": "AI-Content-Factory"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.tts_url, headers=headers, data=ssml.encode('utf-8')) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Azure TTS API error {response.status}: {error_text}")
    
    def _get_output_format(self, format_type: str) -> str:
        """
        Get Azure output format string
        
        Args:
            format_type: Format type (mp3, wav, ogg)
            
        Returns:
            Azure format string
        """
        format_mapping = {
            "mp3": "audio-16khz-128kbitrate-mono-mp3",
            "wav": "riff-16khz-16bit-mono-pcm", 
            "ogg": "ogg-16khz-16bit-mono-opus"
        }
        return format_mapping.get(format_type, format_mapping["mp3"])
    
    def _estimate_duration(self, text: str, audio_config: AudioConfig) -> float:
        """
        Estimate audio duration
        
        Args:
            text: Text to convert
            audio_config: Audio configuration
            
        Returns:
            Estimated duration in seconds
        """
        # More accurate estimation for neural voices
        words = len(text.split())
        base_wpm = 160  # Neural voices are typically faster
        
        if audio_config.language.startswith("th"):
            base_wpm = 140  # Thai is typically slower
        
        base_duration = (words / base_wpm) * 60
        
        # Adjust for speed setting
        base_duration = base_duration / audio_config.speed
        
        return max(1.0, base_duration)
    
    def _get_fallback_voices(self, language: str) -> List[Dict[str, Any]]:
        """
        Get fallback voice list when API is unavailable
        
        Args:
            language: Language code
            
        Returns:
            List of fallback voices
        """
        if language.startswith("th"):
            return [
                {
                    "id": "th-TH-AcharaNeural",
                    "name": "Achara (Thai Female Neural)",
                    "language": "th-TH",
                    "gender": "female",
                    "style": "neural",
                    "quality": "neural"
                },
                {
                    "id": "th-TH-NiwatNeural", 
                    "name": "Niwat (Thai Male Neural)",
                    "language": "th-TH",
                    "gender": "male",
                    "style": "neural",
                    "quality": "neural"
                }
            ]
        else:
            return [
                {
                    "id": "en-US-AriaNeural",
                    "name": "Aria (English Female Neural)",
                    "language": "en-US",
                    "gender": "female", 
                    "style": "neural",
                    "quality": "neural"
                }
            ]
    
    def __str__(self) -> str:
        return f"AzureTTSService(region={self.region}, available={self.is_available})"