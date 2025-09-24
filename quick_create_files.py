# quick_create_files.py - สร้างไฟล์พื้นฐานอย่างรวดเร็ว

import os

def create_directory_structure():
    """สร้างโครงสร้างไฟล์ที่จำเป็น"""
    
    # สร้าง directories
    dirs = [
        "ai-content-factory/trend-monitor",
        "ai-content-factory/trend-monitor/services", 
        "ai-content-factory/content-engine",
        "ai-content-factory/content-engine/services",
        "ai-content-factory/platform-manager",
        "ai-content-factory/platform-manager/services",
        "ai-content-factory/database",
        "ai-content-factory/database/models",
        "ai-content-factory/config"
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # สร้างไฟล์พื้นฐาน
    files = {
        "ai-content-factory/trend-monitor/app.py": '''"""Trend Monitor Service"""
import asyncio
from datetime import datetime

async def main():
    print("Trend Monitor Service Started")

if __name__ == "__main__":
    asyncio.run(main())
''',
        "ai-content-factory/content-engine/app.py": '''"""Content Engine Service"""  
import asyncio
from datetime import datetime

async def main():
    print("Content Engine Service Started")

if __name__ == "__main__":
    asyncio.run(main())
''',
        "ai-content-factory/database/models/base.py": '''"""Database Base Models"""
from datetime import datetime
import uuid

class BaseModel:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
''',
        "ai-content-factory/config/app_config.yaml": '''# AI Content Factory Configuration
app:
  name: "AI Content Factory"
  version: "1.0.0"
  debug: true

database:
  url: "sqlite:///content_factory.db"

apis:
  youtube:
    enabled: true
  groq:
    enabled: true  
  openai:
    enabled: true
'''
    }
    
    for file_path, content in files.items():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created: {file_path}")
    
    # สร้าง __init__.py files
    init_files = [
        "ai-content-factory/__init__.py",
        "ai-content-factory/trend-monitor/__init__.py",
        "ai-content-factory/trend-monitor/services/__init__.py", 
        "ai-content-factory/content-engine/__init__.py",
        "ai-content-factory/content-engine/services/__init__.py",
        "ai-content-factory/platform-manager/__init__.py",
        "ai-content-factory/platform-manager/services/__init__.py",
        "ai-content-factory/database/__init__.py",
        "ai-content-factory/database/models/__init__.py"
    ]
    
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write("")
        print(f"✅ Created: {init_file}")

if __name__ == "__main__":
    print("🚀 Creating AI Content Factory File Structure")
    print("=" * 50)
    
    create_directory_structure()
    
    print("\n🎉 File structure created successfully!")
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install google-api-python-client pytrends") 
    print("2. Run test again: python test_real_integration.py")
    print("3. If tests pass: python real_integration_main.py")