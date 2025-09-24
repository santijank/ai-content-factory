"""
Base Audio AI Service - Abstract class for Text-to-Speech services
Part of AI Content Factory System
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import io

@dataclass
class AudioConfig:
    """Configuration for audio generation"""
    voice_style: str = "neutral"  # energetic, calm, professional, etc.
    language: str = "th"  # th, en, etc.
    speed: float = 1.0  # 0.5 - 2.0
    pitch: float = 1.0  # 0.5 - 2.0
    volume: float = 1.0  # 0.0 - 1.0
    format: str = "mp3"  # mp3, wav, ogg
    quality: str = "standard"  # low, standard, high
    
@dataclass
class AudioResult:
    """Result from audio generation"""
    audio_data: bytes
    format: str
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    cost_credits: Optional[float] = None
    
class BaseAudioAI(ABC):
    """
    Abstract base class for all Audio AI services
    Provides consistent interface for Text-to-Speech generation
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the audio AI service
        
        Args:
            api_key: API key for the service (if required)
            config: Additional configuration
        """
        self.api_key = api_key
        self.config = config or {}
        self.service_name = self.__class__.__name__
        self.is_available = False
        
    @abstractmethod
    async def text_to_speech(
        self, 
        text: str, 
        audio_config: Optional[AudioConfig] = None
    ) -> AudioResult:
        """
        Convert text to speech
        
        Args:
            text: Text to convert to speech
            audio_config: Audio generation configuration
            
        Returns:
            AudioResult containing audio data and metadata
        """
        pass
    
    @abstractmethod
    async def get_available_voices(self, language: str = "th") -> list[Dict[str, Any]]:
        """
        Get list of available voices for the language
        
        Args:
            language: Language code (th, en, etc.)
            
        Returns:
            List of available voices with metadata
        """
        pass
    
    @abstractmethod
    async def check_service_health(self) -> bool:
        """
        Check if the service is available and working
        
        Returns:
            True if service is healthy, False otherwise
        """
        pass
    
    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported language codes
        Default implementation - override in specific services
        """
        return ["th", "en"]
    
    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported audio formats
        Default implementation - override in specific services
        """
        return ["mp3", "wav"]
    
    def estimate_cost(self, text: str, audio_config: Optional[AudioConfig] = None) -> float:
        """
        Estimate cost for generating audio from text
        
        Args:
            text: Text to be converted
            audio_config: Audio configuration
            
        Returns:
            Estimated cost in credits/baht
        """
        # Default implementation - override in specific services
        char_count = len(text)
        base_cost = char_count * 0.001  # 0.001 baht per character
        return base_cost
    
    def validate_text(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Validate input text for TTS generation
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Text cannot be empty"
        
        if len(text) > 10000:  # 10K character limit
            return False, "Text too long (max 10,000 characters)"
        
        return True, None
    
    def split_long_text(self, text: str, max_length: int = 1000) -> list[str]:
        """
        Split long text into smaller chunks for TTS processing
        
        Args:
            text: Text to split
            max_length: Maximum length per chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def generate_audio_with_retry(
        self, 
        text: str, 
        audio_config: Optional[AudioConfig] = None,
        max_retries: int = 3
    ) -> AudioResult:
        """
        Generate audio with retry mechanism
        
        Args:
            text: Text to convert
            audio_config: Audio configuration
            max_retries: Maximum number of retries
            
        Returns:
            AudioResult
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.text_to_speech(text, audio_config)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        raise last_error
    
    async def process_long_text(
        self, 
        text: str, 
        audio_config: Optional[AudioConfig] = None
    ) -> list[AudioResult]:
        """
        Process long text by splitting and generating multiple audio files
        
        Args:
            text: Long text to process
            audio_config: Audio configuration
            
        Returns:
            List of AudioResult objects
        """
        chunks = self.split_long_text(text)
        results = []
        
        for chunk in chunks:
            result = await self.text_to_speech(chunk, audio_config)
            results.append(result)
        
        return results
    
    def create_default_config(self, voice_style: str = "neutral") -> AudioConfig:
        """
        Create default audio configuration
        
        Args:
            voice_style: Voice style to use
            
        Returns:
            AudioConfig with default settings
        """
        return AudioConfig(
            voice_style=voice_style,
            language="th",
            speed=1.0,
            pitch=1.0,
            volume=1.0,
            format="mp3",
            quality="standard"
        )
    
    def __str__(self) -> str:
        return f"{self.service_name}(available={self.is_available})"
    
    def __repr__(self) -> str:
        return f"{self.service_name}(api_key={'***' if self.api_key else None}, available={self.is_available})"


# Utility functions for audio processing
import asyncio

async def combine_audio_results(results: list[AudioResult]) -> AudioResult:
    """
    Combine multiple audio results into one
    Simple concatenation - for more advanced mixing, use external library
    
    Args:
        results: List of AudioResult objects to combine
        
    Returns:
        Combined AudioResult
    """
    if not results:
        raise ValueError("No audio results to combine")
    
    if len(results) == 1:
        return results[0]
    
    # Simple concatenation of audio data
    combined_data = b"".join([result.audio_data for result in results])
    total_duration = sum([r.duration_seconds or 0 for r in results])
    total_cost = sum([r.cost_credits or 0 for r in results])
    
    return AudioResult(
        audio_data=combined_data,
        format=results[0].format,
        duration_seconds=total_duration,
        file_size_bytes=len(combined_data),
        metadata={
            "source": "combined",
            "parts_count": len(results),
            "original_parts": [r.metadata for r in results if r.metadata]
        },
        cost_credits=total_cost
    )

def save_audio_result(result: AudioResult, filename: str) -> str:
    """
    Save AudioResult to file
    
    Args:
        result: AudioResult to save
        filename: Output filename (without extension)
        
    Returns:
        Full filename with extension
    """
    full_filename = f"{filename}.{result.format}"
    
    with open(full_filename, "wb") as f:
        f.write(result.audio_data)
    
    return full_filename

def audio_config_from_plan(audio_plan: Dict[str, Any]) -> AudioConfig:
    """
    Create AudioConfig from content plan audio settings
    
    Args:
        audio_plan: Audio plan from content generation
        
    Returns:
        AudioConfig object
    """
    return AudioConfig(
        voice_style=audio_plan.get("voice_style", "neutral"),
        language=audio_plan.get("language", "th"),
        speed=audio_plan.get("speed", 1.0),
        pitch=audio_plan.get("pitch", 1.0),
        volume=audio_plan.get("volume", 1.0),
        format=audio_plan.get("format", "mp3"),
        quality=audio_plan.get("quality", "standard")
    )