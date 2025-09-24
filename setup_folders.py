#!/usr/bin/env python3
"""
Setup script สำหรับสร้างโครงสร้างโฟลเดอร์และไฟล์พื้นฐาน
"""

import os

def create_folder_structure():
    """สร้างโครงสร้างโฟลเดอร์"""
    folders = [
        'database',
        'trend-monitor',
        'content-engine', 
        'platform-manager',
        'shared',
        'logs',
        'uploads',
        'config'
    ]
    
    print("📁 Creating folder structure...")
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Created: {folder}/")
        
        # สร้าง __init__.py สำหรับ Python packages
        if folder not in ['logs', 'uploads', 'config']:
            init_file = os.path.join(folder, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write(f'"""AI Content Factory - {folder.replace("-", " ").title()} Module"""\n')
                print(f"✅ Created: {init_file}")

def create_config_files():
    """สร้างไฟล์ config พื้นฐาน"""
    print("\n⚙️ Creating config files...")
    
    # .gitignore
    gitignore_content = """
# Database
*.db
*.sqlite3

# Environment
.env
venv/
__pycache__/
*.pyc

# Logs
logs/
*.log

# Uploads
uploads/
temp/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content.strip())
    print("✅ Created: .gitignore")
    
    # README.md
    readme_content = """# AI Content Factory

เครื่องมือสร้างเนื้อหาอัตโนมัติด้วย AI

## Quick Start

```bash
# ติดตั้ง dependencies
pip install -r requirements.txt

# รัน setup
python setup_folders.py

# ทดสอบระบบ
python test_setup_simple.py

# เริ่มใช้งาน
python app.py
```

## Features

- 🔍 Trend Collection (YouTube, Google Trends)
- 🤖 AI-Powered Trend Analysis  
- 💡 Content Opportunity Generation
- 📊 Dashboard & Analytics

## Commands

```bash
python app.py collect     # เก็บ trends
python app.py analyze     # วิเคราะห์ trends
python app.py dashboard   # แสดง dashboard
python app.py full        # รันทั้งหมด
python app.py interactive # โหมด interactive
```
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content.strip())
    print("✅ Created: README.md")

def create_requirements():
    """สร้างไฟล์ requirements.txt แบบ minimal"""
    requirements = """
# Core Dependencies
requests==2.31.0
python-dotenv==1.0.0

# Optional AI Services (uncomment when needed)
# openai==0.28.1
# groq==0.4.2

# Web Framework (for future web interface)
# flask==2.3.3
# flask-cors==4.0.0
""".strip()
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("✅ Created: requirements.txt")

def main():
    """Main setup function"""
    print("🚀 AI Content Factory Setup")
    print("=" * 30)
    
    create_folder_structure()
    create_config_files() 
    create_requirements()
    
    print("\n✅ Setup completed!")
    print("\nNext steps:")
    print("1. Copy the code files from artifacts to their respective folders")
    print("2. Run: python test_setup_simple.py")
    print("3. Run: python app.py")
    
    print("\nFiles to create:")
    print("- database/models_simple.py")
    print("- trend-monitor/trend_collector.py") 
    print("- content-engine/ai_trend_analyzer.py")
    print("- app.py")
    print("- test_setup_simple.py")

if __name__ == "__main__":
    main()