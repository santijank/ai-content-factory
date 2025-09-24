# content-engine/ai_services/text_ai/base_text_ai.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTextAI(ABC):
    """Base class สำหรับ Text AI services"""
    
    @abstractmethod
    async def analyze_trend(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """วิเคราะห์ trend และให้คะแนน"""
        pass
    
    @abstractmethod
    async def generate_content_script(self, idea: str, platform: str = "youtube") -> Dict[str, Any]:
        """สร้าง script เนื้อหา"""
        pass
