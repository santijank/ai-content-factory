# content-engine/services/audio_generator.py
import asyncio
import json
import os
import io
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pydub import AudioSegment
from pydub.effects import normalize
import requests
import base64
import tempfile

@dataclass
class AudioComponents:
    voice_audio: bytes
    background_music: Optional[bytes]
    sound_effects: List[bytes]
    final_mix: bytes
    duration_seconds: float
    voice_settings: Dict

@dataclass
class VoiceSettings:
    language: str = "th"
    gender: str = "female"
    speed: float = 1.0
    pitch: float = 1.0
    emotion: str = "neutral"
    voice_id: str = "default"

class TTSServiceManager:
    """จัดการ Text-to-Speech services หลายตัว"""
    
    def __init__(self):
        self.services = {
            "budget": GTTSService(),
            "standard": AzureTTSService(),
            "premium": ElevenLabsService()
        }
        self.current_tier = "budget"  # Default

    def set_quality_tier(self, tier: str):
        if tier in self.services:
            self.current_tier = tier

    async def text_to_speech(self, text: str, voice_settings: VoiceSettings) -> bytes:
        """แปลงข้อความเป็นเสียงตาม quality tier"""
        service = self.services[self.current_tier]
        return await service.generate_speech(text, voice_settings)

class GTTSService:
    """Google Text-to-Speech Service (Free Tier)"""
    
    async def generate_speech(self, text: str, voice_settings: VoiceSettings) -> bytes:
        """สร้างเสียงด้วย gTTS"""
        try:
            from gtts import gTTS
            
            # สร้าง TTS object
            tts = gTTS(
                text=text,
                lang=voice_settings.language,
                slow=False if voice_settings.speed >= 1.0 else True
            )
            
            # บันทึกเป็น bytes
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                with open(tmp_file.name, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                
                os.unlink(tmp_file.name)  # ลบไฟล์ temp
                
            # ปรับความเร็วถ้าจำเป็น
            if voice_settings.speed != 1.0:
                audio_bytes = await self._adjust_speed(audio_bytes, voice_settings.speed)
                
            return audio_bytes
            
        except Exception as e:
            print(f"gTTS Error: {e}")
            return await self._create_fallback_audio(text)

    async def _adjust_speed(self, audio_bytes: bytes, speed: float) -> bytes:
        """ปรับความเร็วเสียง"""
        try:
            audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            
            # เปลี่ยนความเร็วโดยไม่เปลี่ยน pitch
            if speed != 1.0:
                # ใช้ frame_rate manipulation
                new_sample_rate = int(audio.frame_rate * speed)
                adjusted_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
                adjusted_audio = adjusted_audio.set_frame_rate(audio.frame_rate)
            else:
                adjusted_audio = audio
            
            # Convert back to bytes
            buffer = io.BytesIO()
            adjusted_audio.export(buffer, format="mp3")
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Speed adjustment error: {e}")
            return audio_bytes

    async def _create_fallback_audio(self, text: str) -> bytes:
        """สร้างเสียงสำรองเมื่อเกิดข้อผิดพลาด"""
        # สร้าง silent audio ความยาวตามข้อความ
        duration_ms = len(text) * 100  # ประมาณ 100ms ต่อตัวอักษร
        silent_audio = AudioSegment.silent(duration=duration_ms)
        
        buffer = io.BytesIO()
        silent_audio.export(buffer, format="mp3")
        return buffer.getvalue()

class AzureTTSService:
    """Azure Cognitive Services TTS (Standard Tier)"""
    
    def __init__(self):
        self.api_key = os.getenv('AZURE_TTS_API_KEY', '')
        self.region = os.getenv('AZURE_TTS_REGION', 'southeastasia')
        
        # Thai voices available in Azure
        self.thai_voices = {
            "female": "th-TH-AcharaNeural",
            "male": "th-TH-NiwatNeural"
        }

    async def generate_speech(self, text: str, voice_settings: VoiceSettings) -> bytes:
        """สร้างเสียงด้วย Azure TTS"""
        if not self.api_key:
            print("Azure TTS API key not found, falling back to gTTS")
            gtts_service = GTTSService()
            return await gtts_service.generate_speech(text, voice_settings)
        
        try:
            # เลือก voice
            voice_name = self.thai_voices.get(voice_settings.gender, self.thai_voices["female"])
            
            # สร้าง SSML
            ssml = self._create_ssml(text, voice_name, voice_settings)
            
            # เรียก Azure API
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
            }
            
            url = f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1"
            
            response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"Azure TTS error: {response.status_code}")
                return await self._fallback_to_gtts(text, voice_settings)
                
        except Exception as e:
            print(f"Azure TTS exception: {e}")
            return await self._fallback_to_gtts(text, voice_settings)

    def _create_ssml(self, text: str, voice_name: str, voice_settings: VoiceSettings) -> str:
        """สร้าง SSML สำหรับ Azure TTS"""
        
        # คำนวณ rate และ pitch
        rate_percent = (voice_settings.speed - 1.0) * 50  # -50% to +50%
        pitch_percent = (voice_settings.pitch - 1.0) * 20  # -20% to +20%
        
        rate_str = f"{rate_percent:+.0f}%" if rate_percent != 0 else "0%"
        pitch_str = f"{pitch_percent:+.0f}%" if pitch_percent != 0 else "0%"
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="th-TH">
            <voice name="{voice_name}">
                <prosody rate="{rate_str}" pitch="{pitch_str}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        return ssml.strip()

    async def _fallback_to_gtts(self, text: str, voice_settings: VoiceSettings) -> bytes:
        """Fallback ไปใช้ gTTS"""
        gtts_service = GTTSService()
        return await gtts_service.generate_speech(text, voice_settings)

class ElevenLabsService:
    """ElevenLabs TTS Service (Premium Tier)"""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY', '')
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # ElevenLabs voice IDs (ตัวอย่าง)
        self.voice_ids = {
            "female_professional": "21m00Tcm4TlvDq8ikWAM",
            "male_friendly": "AZnzlk1XvdvUeBnXmlld",
            "female_energetic": "EXAVITQu4vr4xnSDxMaL"
        }

    async def generate_speech(self, text: str, voice_settings: VoiceSettings) -> bytes:
        """สร้างเสียงด้วย ElevenLabs"""
        if not self.api_key:
            print("ElevenLabs API key not found, falling back to Azure")
            azure_service = AzureTTSService()
            return await azure_service.generate_speech(text, voice_settings)
        
        try:
            # เลือก voice ID
            voice_key = f"{voice_settings.gender}_{voice_settings.emotion}"
            voice_id = self.voice_ids.get(voice_key, list(self.voice_ids.values())[0])
            
            # เตรียม payload
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.5,
                    "use_speaker_boost": True
                }
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"ElevenLabs error: {response.status_code}")
                return await self._fallback_to_azure(text, voice_settings)
                
        except Exception as e:
            print(f"ElevenLabs exception: {e}")
            return await self._fallback_to_azure(text, voice_settings)

    async def _fallback_to_azure(self, text: str, voice_settings: VoiceSettings) -> bytes:
        """Fallback ไปใช้ Azure"""
        azure_service = AzureTTSService()
        return await azure_service.generate_speech(text, voice_settings)

class BackgroundMusicManager:
    """จัดการเพลงพื้นหลังและ sound effects"""
    
    def __init__(self):
        self.music_library = {
            "upbeat": ["energetic_pop.mp3", "motivational_beat.mp3"],
            "chill": ["calm_ambient.mp3", "soft_piano.mp3"],
            "dramatic": ["epic_orchestral.mp3", "tension_build.mp3"],
            "corporate": ["professional_bg.mp3", "business_tone.mp3"]
        }
        
        self.sound_effects = {
            "transition": ["whoosh.mp3", "swoosh.mp3"],
            "notification": ["ding.mp3", "bell.mp3"],
            "emphasis": ["pop.mp3", "click.mp3"]
        }

    async def get_background_music(self, mood: str, duration_seconds: float) -> Optional[bytes]:
        """ดึงเพลงพื้นหลังตาม mood และความยาว"""
        
        try:
            # ในระบบจริงจะดึงจาก music library
            # ตอนนี้สร้าง mock audio
            return await self._create_mock_music(mood, duration_seconds)
            
        except Exception as e:
            print(f"Error getting background music: {e}")
            return None

    async def _create_mock_music(self, mood: str, duration_seconds: float) -> bytes:
        """สร้างเพลงพื้นหลัง mock"""
        
        # สร้าง simple tone ตาม mood
        from pydub.generators import Sine
        
        duration_ms = int(duration_seconds * 1000)
        
        if mood == "upbeat":
            # เสียงที่มีพลัง
            tone1 = Sine(440).to_audio_segment(duration=duration_ms//3)  # A note
            tone2 = Sine(523).to_audio_segment(duration=duration_ms//3)  # C note
            tone3 = Sine(659).to_audio_segment(duration=duration_ms//3)  # E note
            music = tone1 + tone2 + tone3
        elif mood == "chill":
            # เสียงเบาๆ
            tone = Sine(220).to_audio_segment(duration=duration_ms)  # A note, lower octave
            music = tone - 20  # ลดความดัง
        else:
            # เสียงเฉยๆ
            tone = Sine(330).to_audio_segment(duration=duration_ms)  # E note
            music = tone - 15
        
        # ทำให้เสียงเบาลง (เป็น background)
        music = music - 25  # ลด 25dB
        
        buffer = io.BytesIO()
        music.export(buffer, format="mp3")
        return buffer.getvalue()

class AudioMixer:
    """ผสมเสียงจากหลายแหล่ง"""
    
    async def mix_audio_components(self, 
                                 voice_audio: bytes,
                                 background_music: Optional[bytes] = None,
                                 sound_effects: List[Dict] = None) -> AudioComponents:
        """ผสมเสียงทั้งหมดเข้าด้วยกัน"""
        
        try:
            # โหลดเสียงหลัก
            voice = AudioSegment.from_mp3(io.BytesIO(voice_audio))
            voice = normalize(voice)  # ปรับระดับเสียง
            
            # เริ่มจาก voice audio
            final_mix = voice
            
            # เพิ่มเพลงพื้นหลัง
            if background_music:
                bg_music = AudioSegment.from_mp3(io.BytesIO(background_music))
                bg_music = self._adjust_background_music(bg_music, len(voice))
                final_mix = final_mix.overlay(bg_music)
            
            # เพิ่ม sound effects
            if sound_effects:
                for effect in sound_effects:
                    final_mix = await self._add_sound_effect(final_mix, effect)
            
            # ปรับระดับเสียงสุดท้าย
            final_mix = normalize(final_mix)
            
            # Export เป็น bytes
            buffer = io.BytesIO()
            final_mix.export(buffer, format="mp3", bitrate="192k")
            
            return AudioComponents(
                voice_audio=voice_audio,
                background_music=background_music,
                sound_effects=[],
                final_mix=buffer.getvalue(),
                duration_seconds=len(final_mix) / 1000.0,
                voice_settings={}
            )
            
        except Exception as e:
            print(f"Audio mixing error: {e}")
            # Return voice only if mixing fails
            return AudioComponents(
                voice_audio=voice_audio,
                background_music=None,
                sound_effects=[],
                final_mix=voice_audio,
                duration_seconds=0.0,
                voice_settings={}
            )

    def _adjust_background_music(self, bg_music: AudioSegment, target_duration_ms: int) -> AudioSegment:
        """ปรับเพลงพื้นหลังให้เหมาะกับความยาวเสียงหลัก"""
        
        # ลดความดัง
        bg_music = bg_music - 20  # ลด 20dB เพื่อเป็น background
        
        # ปรับความยาว
        if len(bg_music) < target_duration_ms:
            # Loop ถ้าสั้นเกินไป
            repeats = (target_duration_ms // len(bg_music)) + 1
            bg_music = bg_music * repeats
        
        # ตัดให้พอดี
        bg_music = bg_music[:target_duration_ms]
        
        # Fade in/out
        bg_music = bg_music.fade_in(1000).fade_out(1000)
        
        return bg_music

    async def _add_sound_effect(self, audio: AudioSegment, effect_config: Dict) -> AudioSegment:
        """เพิ่ม sound effect ที่ตำแหน่งที่กำหนด"""
        
        try:
            effect_file = effect_config.get('file', '')
            position_ms = effect_config.get('position_ms', 0)
            volume_adjustment = effect_config.get('volume', 0)
            
            # ในระบบจริงจะโหลดไฟล์จริง
            # ตอนนี้สร้าง mock sound effect
            effect_audio = await self._create_mock_sound_effect(effect_config.get('type', 'click'))
            
            # ปรับความดัง
            if volume_adjustment != 0:
                effect_audio = effect_audio + volume_adjustment
            
            # ใส่ effect ที่ตำแหน่งที่กำหนด
            audio = audio.overlay(effect_audio, position=position_ms)
            
            return audio
            
        except Exception as e:
            print(f"Error adding sound effect: {e}")
            return audio

    async def _create_mock_sound_effect(self, effect_type: str) -> AudioSegment:
        """สร้าง sound effect แบบ mock"""
        from pydub.generators import Sine
        
        if effect_type == "click":
            return Sine(800).to_audio_segment(duration=100)
        elif effect_type == "whoosh":
            # Sweep from high to low
            high_tone = Sine(2000).to_audio_segment(duration=150)
            low_tone = Sine(500).to_audio_segment(duration=150)
            return high_tone + low_tone
        else:
            return Sine(440).to_audio_segment(duration=200)

# Integration Example
async def main():
    """ตัวอย่างการใช้ระบบ audio generation"""
    
    # ตั้งค่าเสียง
    voice_settings = VoiceSettings(
        language="th",
        gender="female",
        speed=1.1,
        pitch=1.0,
        emotion="energetic"
    )
    
    # สร้างเสียงพูด
    tts_manager = TTSServiceManager()
    tts_manager.set_quality_tier("budget")  # เริ่มจาก budget
    
    script_text = """สวัสดีครับ วันนี้ผมจะมาพูดเรื่อง AI ที่กำลังเปลี่ยนโลก 
    เทคโนโลยีใหม่นี้สามารถทำอะไรได้บ้าง มาดูกันเลย"""
    
    voice_audio = await tts_manager.text_to_speech(script_text, voice_settings)
    
    # สร้างเพลงพื้นหลัง
    music_manager = BackgroundMusicManager()
    bg_music = await music_manager.get_background_music("upbeat", 30.0)
    
    # ผสมเสียง
    mixer = AudioMixer()
    
    sound_effects = [
        {"type": "click", "position_ms": 5000, "volume": -10},
        {"type": "whoosh", "position_ms": 15000, "volume": -5}
    ]
    
    final_audio = await mixer.mix_audio_components(
        voice_audio=voice_audio,
        background_music=bg_music,
        sound_effects=sound_effects
    )
    
    print(f"Audio generated successfully!")
    print(f"Duration: {final_audio.duration_seconds:.2f} seconds")
    print(f"Final mix size: {len(final_audio.final_mix)} bytes")
    
    # บันทึกไฟล์ (ตัวอย่าง)
    with open("generated_audio.mp3", "wb") as f:
        f.write(final_audio.final_mix)
    
    return final_audio

if __name__ == "__main__":
    asyncio.run(main())