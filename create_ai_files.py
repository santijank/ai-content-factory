# create_ai_files.py - สร้างไฟล์ที่จำเป็น
import os

def create_directories():
    """สร้าง directories ที่จำเป็น"""
    dirs = [
        'content-engine',
        'content-engine/services',
        'content-engine/ai_services',
        'content-engine/ai_services/text_ai',
        'content-engine/ai_services/image_ai',
        'content-engine/ai_services/audio_ai',
        'content-engine/models',
        'templates'
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created: {dir_path}")

def create_init_files():
    """สร้างไฟล์ __init__.py"""
    init_files = [
        'content-engine/__init__.py',
        'content-engine/services/__init__.py',
        'content-engine/ai_services/__init__.py',
        'content-engine/ai_services/text_ai/__init__.py',
        'content-engine/ai_services/image_ai/__init__.py',
        'content-engine/ai_services/audio_ai/__init__.py',
        'content-engine/models/__init__.py'
    ]
    
    for file_path in init_files:
        with open(file_path, 'w') as f:
            f.write('# Package initialization\n')
        print(f"✅ Created: {file_path}")

def create_base_text_ai():
    """สร้าง base class สำหรับ text AI"""
    content = """# content-engine/ai_services/text_ai/base_text_ai.py
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
"""
    
    with open('content-engine/ai_services/text_ai/base_text_ai.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: base_text_ai.py")

if __name__ == "__main__":
    print("🚀 สร้างไฟล์ที่จำเป็นสำหรับ AI Integration...")
    
    create_directories()
    create_init_files() 
    create_base_text_ai()
    
    print("\n✅ สร้างไฟล์เสร็จสิ้น!")
    print("\n📝 ขั้นตอนต่อไป:")
    print("1. python fix_groq_service.py")
    print("2. python test_ai_integration.py")
    print("3. python main.py")
