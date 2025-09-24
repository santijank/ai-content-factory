"""
Google Text-to-Speech Service
Budget tier TTS service สำหรับระบบ AI Content Factory
"""

import os
import asyncio
import tempfile
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import io
import time

try:
    from gtts import gTTS
    from gtts.lang import tts_langs
except ImportError:
    raise ImportError("Please install gtts: pip install gtts")

try:
    from pydub import AudioSegment
    from pydub.effects import speedup, normalize
except ImportError:
    AudioSegment = None
    logging.warning("pydub not available. Audio processing will be limited.")

from .base_audio_ai import BaseAudioAI
from ...models.quality_tier import QualityTier
from ....shared.utils.error_handler import handle_async_errors, AudioAIError
from ....shared.utils.rate_limiter import rate_limit
from ....shared.constants.platform_constants import PlatformType

class GTTSService(BaseAudioAI):
    """
    Google Text-to-Speech Service Implementation
    ใช้สำหรับ Budget tier - ฟรีแต่มีข้อจำกัด
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.service_name = "gtts"
        self.quality_tier = QualityTier.BUDGET
        self.logger = logging.getLogger(__name__)
        
        # gTTS Configuration
        self.default_lang = self.config.get('default_language', 'en')
        self.default_tld = self.config.get('default_tld', 'com')  # Top-level domain
        self.slow_speech = self.config.get('slow_speech', False)
        self.temp_dir = self.config.get('temp_dir', tempfile.gettempdir())
        
        # Audio Processing Settings
        self.normalize_audio = self.config.get('normalize_audio', True)
        self.target_bitrate = self.config.get('target_bitrate', '128k')
        self.sample_rate = self.config.get('sample_rate', 22050)
        
        # Voice Styles Mapping (gTTS limitations workaround)
        self.voice_styles = {
            'normal': {'slow': False, 'tld': 'com'},
            'slow': {'slow': True, 'tld': 'com'},
            'energetic': {'slow': False, 'tld': 'com'},  # Same as normal for gTTS
            'calm': {'slow': True, 'tld': 'com'},
            'professional': {'slow': False, 'tld': 'com'},
            'casual': {'slow': False, 'tld': 'com'},
            'excited': {'slow': False, 'tld': 'com'},
            'serious': {'slow': False, 'tld': 'com'}
        }
        
        # Language Support
        self.supported_languages = self._get_supported_languages()
        
        # Stats tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_characters': 0,
            'total_duration': 0.0
        }
    
    def _get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages from gTTS"""
        try:
            return tts_langs()
        except Exception as e:
            self.logger.warning(f"Could not fetch gTTS languages: {e}")
            # Fallback to common languages
            return {
                'en': 'English',
                'th': 'Thai', 
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh': 'Chinese'
            }
    
    @rate_limit("gtts_free", tokens=1)
    @handle_async_errors()
    async def text_to_speech(self, 
                            text: str,
                            voice_style: str = "normal",
                            language: str = None,
                            output_format: str = "mp3",
                            **kwargs) -> Dict[str, Any]:
        """
        Convert text to speech using Google TTS
        
        Args:
            text: Text to convert
            voice_style: Voice style (limited options for gTTS)
            language: Language code (e.g., 'en', 'th')
            output_format: Output format (mp3, wav)
            **kwargs: Additional parameters
        
        Returns:
            Dict with audio_data, duration, and metadata
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not text or len(text.strip()) == 0:
                raise AudioAIError("Text cannot be empty", "EMPTY_TEXT")
            
            # Character limit check (gTTS has practical limits)
            if len(text) > 5000:
                self.logger.warning("Text is very long, may cause issues with gTTS")
            
            # Language setup
            lang = language or self.default_lang
            if lang not in self.supported_languages:
                self.logger.warning(f"Language {lang} not supported, using default")
                lang = self.default_lang
            
            # Voice style setup
            style_config = self.voice_styles.get(voice_style, self.voice_styles['normal'])
            
            # Generate speech
            audio_data = await self._generate_speech(
                text=text,
                lang=lang,
                slow=style_config['slow'],
                tld=style_config['tld']
            )
            
            # Post-process audio if needed
            if AudioSegment and (output_format != 'mp3' or self.normalize_audio):
                audio_data = await self._process_audio(
                    audio_data, 
                    output_format,
                    voice_style
                )
            
            # Calculate duration (rough estimate)
            duration = self._estimate_duration(text, style_config['slow'])
            
            # Update stats
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1
            self.stats['total_characters'] += len(text)
            self.stats['total_duration'] += duration
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'audio_data': audio_data,
                'duration': duration,
                'format': output_format,
                'metadata': {
                    'service': self.service_name,
                    'language': lang,
                    'voice_style': voice_style,
                    'character_count': len(text),
                    'processing_time': processing_time,
                    'quality_tier': self.quality_tier.value
                }
            }
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            self.logger.error(f"TTS generation failed: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'audio_data': None,
                'duration': 0,
                'metadata': {
                    'service': self.service_name,
                    'processing_time': time.time() - start_time
                }
            }
    
    async def _generate_speech(self, 
                              text: str, 
                              lang: str, 
                              slow: bool = False,
                              tld: str = 'com') -> bytes:
        """Generate speech using gTTS"""
        
        def _sync_generate():
            """Synchronous gTTS generation"""
            tts = gTTS(
                text=text,
                lang=lang,
                slow=slow,
                tld=tld
            )
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.read()
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(None, _sync_generate)
        
        return audio_data
    
    async def _process_audio(self, 
                           audio_data: bytes, 
                           output_format: str,
                           voice_style: str) -> bytes:
        """Post-process audio with pydub"""
        
        def _sync_process():
            """Synchronous audio processing"""
            # Load audio
            audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            
            # Apply voice style effects
            if voice_style == 'energetic':
                # Speed up slightly and increase volume
                audio = speedup(audio, playback_speed=1.1)
                audio = audio + 3  # Increase volume by 3dB
                
            elif voice_style == 'calm':
                # Slow down and normalize
                audio = speedup(audio, playback_speed=0.9)
                
            elif voice_style == 'excited':
                # Speed up and increase pitch (limited pitch control in pydub)
                audio = speedup(audio, playback_speed=1.15)
                audio = audio + 5
                
            # Normalize audio
            if self.normalize_audio:
                audio = normalize(audio)
            
            # Set sample rate
            audio = audio.set_frame_rate(self.sample_rate)
            
            # Export to desired format
            output_buffer = io.BytesIO()
            
            if output_format.lower() == 'wav':
                audio.export(output_buffer, format='wav')
            elif output_format.lower() == 'ogg':
                audio.export(output_buffer, format='ogg')
            else:
                # Default to MP3
                audio.export(output_buffer, format='mp3', bitrate=self.target_bitrate)
            
            output_buffer.seek(0)
            return output_buffer.read()
        
        if not AudioSegment:
            self.logger.warning("pydub not available, returning original audio")
            return audio_data
        
        loop = asyncio.get_event_loop()
        processed_audio = await loop.run_in_executor(None, _sync_process)
        
        return processed_audio
    
    def _estimate_duration(self, text: str, slow: bool = False) -> float:
        """Estimate audio duration based on text length"""
        # Average speaking rate: 150-200 words per minute
        # Slow speech: ~100 words per minute
        
        word_count = len(text.split())
        
        if slow:
            words_per_minute = 100
        else:
            words_per_minute = 175
        
        duration_minutes = word_count / words_per_minute
        duration_seconds = duration_minutes * 60
        
        # Add some buffer time
        return duration_seconds * 1.1
    
    async def get_available_voices(self, language: str = None) -> List[Dict[str, Any]]:
        """
        Get available voices for gTTS (limited compared to premium services)
        """
        lang = language or self.default_lang
        
        # gTTS doesn't have multiple voices per language, but we can simulate
        # different styles through processing
        voices = []
        
        if lang in self.supported_languages:
            for style_name, style_config in self.voice_styles.items():
                voices.append({
                    'name': f"{self.supported_languages[lang]} ({style_name})",
                    'id': style_name,
                    'language': lang,
                    'language_name': self.supported_languages[lang],
                    'gender': 'neutral',  # gTTS doesn't specify gender
                    'style': style_name,
                    'sample_rate': self.sample_rate,
                    'quality': 'budget'
                })
        
        return voices
    
    async def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages"""
        return self.supported_languages.copy()
    
    async def estimate_cost(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Estimate cost for TTS generation
        gTTS is free but has usage limits
        """
        character_count = len(text)
        
        return {
            'service': self.service_name,
            'character_count': character_count,
            'estimated_cost': 0.0,  # gTTS is free
            'currency': 'USD',
            'notes': 'gTTS is free but has daily usage limits',
            'rate_limit_info': {
                'requests_per_day': 'Unlimited (with reasonable usage)',
                'characters_per_request': '5000 (recommended max)',
                'concurrent_requests': '1-2 (recommended)'
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            'name': 'Google Text-to-Speech (gTTS)',
            'quality_tier': self.quality_tier.value,
            'supported_languages': len(self.supported_languages),
            'supported_formats': ['mp3', 'wav', 'ogg'],
            'features': {
                'voice_styles': list(self.voice_styles.keys()),
                'languages': list(self.supported_languages.keys()),
                'max_text_length': 5000,
                'concurrent_requests': 2,
                'free_tier': True,
                'commercial_usage': True
            },
            'limitations': {
                'no_voice_selection': True,
                'limited_customization': True,
                'internet_required': True,
                'rate_limits': True,
                'no_ssml_support': True
            },
            'stats': self.stats.copy()
        }
    
    async def test_service(self) -> Dict[str, Any]:
        """Test the service connectivity and functionality"""
        test_text = "Hello, this is a test of the Google Text-to-Speech service."
        
        try:
            result = await self.text_to_speech(
                text=test_text,
                voice_style="normal"
            )
            
            return {
                'success': result['success'],
                'service': self.service_name,
                'response_time': result['metadata']['processing_time'],
                'test_text_length': len(test_text),
                'audio_generated': result['audio_data'] is not None,
                'estimated_duration': result['duration']
            }
            
        except Exception as e:
            return {
                'success': False,
                'service': self.service_name,
                'error': str(e),
                'test_text_length': len(test_text)
            }
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_characters': 0,
            'total_duration': 0.0
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        # gTTS doesn't require special cleanup
        self.logger.info(f"gTTS service cleanup completed. Final stats: {self.stats}")

# Utility Functions for gTTS optimization
def optimize_text_for_gtts(text: str) -> str:
    """
    Optimize text for better gTTS output
    """
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Handle abbreviations that gTTS might mispronounce
    abbreviations = {
        'AI': 'Artificial Intelligence',
        'API': 'A P I',
        'URL': 'U R L',
        'HTML': 'H T M L',
        'CSS': 'C S S',
        'JS': 'JavaScript',
        'PHP': 'P H P',
        'SQL': 'S Q L',
        'JSON': 'Jason',  # More natural pronunciation
        'XML': 'X M L',
        'HTTP': 'H T T P',
        'HTTPS': 'H T T P S'
    }
    
    for abbr, replacement in abbreviations.items():
        text = text.replace(abbr, replacement)
    
    # Add pauses for better flow
    text = text.replace('.', '. ')
    text = text.replace(',', ', ')
    text = text.replace(';', '; ')
    text = text.replace(':', ': ')
    
    # Clean up multiple spaces
    text = ' '.join(text.split())
    
    return text

def split_long_text(text: str, max_length: int = 5000) -> List[str]:
    """
    Split long text into chunks suitable for gTTS
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    sentences = text.split('. ')
    current_chunk = ""
    
    for sentence in sentences:
        # Add sentence to current chunk if it fits
        if len(current_chunk + sentence + '. ') <= max_length:
            current_chunk += sentence + '. '
        else:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '
    
    # Add last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_gtts():
        service = GTTSService({
            'normalize_audio': True,
            'target_bitrate': '128k'
        })
        
        # Test service
        test_result = await service.test_service()
        print("Test result:", test_result)
        
        # Test TTS generation
        result = await service.text_to_speech(
            text="สวัสดีครับ นี่คือการทดสอบระบบ Text-to-Speech ภาษาไทย",
            language="th",
            voice_style="normal"
        )
        
        print("TTS Result:", {k: v for k, v in result.items() if k != 'audio_data'})
        
        # Get service info
        info = service.get_service_info()
        print("Service Info:", info)
    
    asyncio.run(test_gtts())