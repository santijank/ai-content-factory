# content-engine/models/content_plan.py
from typing import Dict, Any
import time

class ContentPlan:
    def __init__(self, **kwargs):
        self.content_type = kwargs.get('content_type', 'educational')
        self.platform = kwargs.get('platform', 'youtube')
        self.script = kwargs.get('script', {})
        self.visual_plan = kwargs.get('visual_plan', {})
        self.audio_plan = kwargs.get('audio_plan', {})
        self.platform_optimization = kwargs.get('platform_optimization', {})
        self.production_estimate = kwargs.get('production_estimate', {})
        self.generated_at = kwargs.get('generated_at', time.strftime('%Y-%m-%d %H:%M:%S'))
        self.ai_model = kwargs.get('ai_model', 'unknown')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentPlan':
        """สร้าง ContentPlan จาก dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลง ContentPlan เป็น dictionary"""
        return {
            'content_type': self.content_type,
            'platform': self.platform,
            'script': self.script,
            'visual_plan': self.visual_plan,
            'audio_plan': self.audio_plan,
            'platform_optimization': self.platform_optimization,
            'production_estimate': self.production_estimate,
            'generated_at': self.generated_at,
            'ai_model': self.ai_model
        }
    
    def __dict__(self):
        return self.to_dict()