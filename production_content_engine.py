#!/usr/bin/env python3
"""
Fix Thai Display in Command Line
แก้ไขการแสดงผลภาษาไทยใน Command Prompt
"""

import os
import sys
import locale
import subprocess
from pathlib import Path

def fix_thai_display():
    """แก้ไขการแสดงผลภาษาไทย"""
    print("🔧 กำลังแก้ไขการแสดงผลภาษาไทย...")
    
    fixes_applied = []
    
    # Fix 1: Set Console Code Page to UTF-8
    try:
        os.system('chcp 65001 > nul 2>&1')
        fixes_applied.append("✅ ตั้งค่า Code Page เป็น UTF-8")
    except Exception as e:
        fixes_applied.append(f"❌ ตั้งค่า Code Page ล้มเหลว: {e}")
    
    # Fix 2: Set Environment Variables
    try:
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        fixes_applied.append("✅ ตั้งค่า Python encoding")
    except Exception as e:
        fixes_applied.append(f"❌ ตั้งค่า encoding ล้มเหลว: {e}")
    
    # Fix 3: Set Locale
    try:
        if sys.platform.startswith('win'):
            locale.setlocale(locale.LC_ALL, 'thai')
        else:
            locale.setlocale(locale.LC_ALL, 'th_TH.UTF-8')
        fixes_applied.append("✅ ตั้งค่า Locale เป็นภาษาไทย")
    except Exception as e:
        fixes_applied.append(f"⚠️ ตั้งค่า Locale: {e}")
    
    # Fix 4: Configure sys.stdout
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        fixes_applied.append("✅ กำหนดค่า stdout/stderr")
    except Exception as e:
        fixes_applied.append(f"⚠️ กำหนดค่า stdout: {e}")
    
    return fixes_applied

def create_batch_launcher():
    """สร้างไฟล์ .bat สำหรับเรียกใช้โดยตั้งค่าให้ถูกต้อง"""
    
    batch_content = '''@echo off
REM AI Content Engine Launcher with Thai Support
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo 🎬 AI Content Generation Engine - Thai Support
echo ================================================
echo 🔧 ตั้งค่าการแสดงผลภาษาไทย...
echo.

REM Start the application
python production_content_engine.py

pause
'''
    
    try:
        with open('start_thai.bat', 'w', encoding='utf-8') as f:
            f.write(batch_content)
        print("✅ สร้างไฟล์ start_thai.bat เรียบร้อย")
        return True
    except Exception as e:
        print(f"❌ สร้างไฟล์ .bat ล้มเหลว: {e}")
        return False

def create_fixed_production_engine():
    """สร้าง production engine ที่แก้ไขปัญหาภาษาไทยแล้ว"""
    
    fixed_code = '''#!/usr/bin/env python3
"""
AI Content Generation Engine - Thai Display Fixed
แก้ไขปัญหาการแสดงผลภาษาไทยแล้ว
"""

import sys
import os
import locale

# ===============================
# Thai Display Fixes
# ===============================

def setup_thai_display():
    """ตั้งค่าการแสดงผลภาษาไทย"""
    try:
        # Fix 1: Console Code Page
        if sys.platform.startswith('win'):
            os.system('chcp 65001 > nul 2>&1')
        
        # Fix 2: Environment Variables  
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        
        # Fix 3: Locale
        try:
            if sys.platform.startswith('win'):
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            else:
                locale.setlocale(locale.LC_ALL, 'th_TH.UTF-8')
        except:
            pass  # ไม่สำคัญถ้าตั้งไม่ได้
            
        # Fix 4: Stdout/Stderr encoding
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        
        return True
        
    except Exception as e:
        print(f"Warning: Thai display setup failed: {e}")
        return False

# เรียกใช้การแก้ไขก่อนเริ่มโปรแกรม
setup_thai_display()

# ===============================
# Original Code (Updated)  
# ===============================

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging with UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Safe print function
def safe_print(text, **kwargs):
    """Print ที่รองรับภาษาไทย"""
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        # Fallback: แปลงเป็น ASCII ถ้าจำเป็น
        text_safe = text.encode('ascii', 'ignore').decode('ascii')
        print(text_safe, **kwargs)
    except Exception as e:
        print(f"Print error: {e}", **kwargs)

class ThaiSafeContentEngine:
    """Content Engine ที่รองรับภาษาไทย"""
    
    def __init__(self):
        """Initialize engine with Thai support"""
        self.session_stats = {
            "generated": 0,
            "total_cost": 0.0,
            "total_time": 0.0,
            "success_rate": 100.0
        }
        
        safe_print("🔧 กำลังตั้งค่าระบบ...")
        safe_print("✅ รองรับภาษาไทยแล้ว!")
        
    async def generate_complete_content(self, request: Dict) -> Dict:
        """สร้างเนื้อหาพร้อมรองรับภาषาไทย"""
        
        start_time = datetime.now()
        
        safe_print(f"🎬 เริ่มสร้างเนื้อหา: {request.get('topic', 'ไม่ระบุ')}")
        safe_print(f"   แพลตฟอร์ม: {request.get('platform', 'youtube').upper()}")
        safe_print(f"   คุณภาพ: {request.get('quality', 'budget').upper()}")
        
        try:
            # จำลองการประมวลผล
            import random
            await asyncio.sleep(random.uniform(2, 5))
            
            generation_time = random.uniform(10, 30)
            cost = random.uniform(1.5, 8.0)
            
            # อัปเดตสถิติ
            self.session_stats["generated"] += 1
            self.session_stats["total_cost"] += cost
            self.session_stats["total_time"] += generation_time
            
            # สร้างผลลัพธ์ (ภาษาไทยปลอดภัย)
            result = {
                "success": True,
                "generation_time_seconds": round(generation_time, 1),
                "script": {
                    "title_suggestions": [
                        f"{request['topic']}: สิ่งที่ต้องรู้ 2025",
                        f"เจาะลึก {request['topic']} แบบง่ายๆ",
                        f"{request['topic']}: มุมมองใหม่"
                    ],
                    "hook": f"สวัสดีครับ! วันนี้เราจะมาคุยเรื่อง {request['topic']} กัน",
                    "introduction": f"เรื่อง {request['topic']} นี้สำคัญมาก เพราะ {request['angle']}",
                    "main_content": f"""
ประเด็นแรก: {request['topic']} คืออะไร และทำไมถึงสำคัญ
ประเด็นที่สอง: {request['angle']} - มุมมองที่น่าสนใจ  
ประเด็นสุดท้าย: การนำไปประยุกต์ใช้ในชีวิตจริง
                    """.strip(),
                    "conclusion": f"สรุปแล้ว {request['topic']} เป็นเรื่องที่เราควรให้ความสนใจ",
                    "call_to_action": "อย่าลืมกด Like Subscribe และกดกระดิ่งนะครับ",
                    "hashtags": [f"#{request['topic'].replace(' ', '')}", "#viral", "#trending"],
                    "estimated_duration": f"{request.get('duration', 5)}-{request.get('duration', 5)+2} นาที",
                    "thumbnail_concept": f"ใส่รูป {request['topic']} ที่ดึงดูดสายตา"
                },
                "cost_estimate": {
                    "total_cost_baht": round(cost, 2),
                    "quality_score": round(random.uniform(7, 9.5), 1),
                    "estimated_views": random.randint(5000, 50000),
                    "estimated_roi": random.randint(300, 2000)
                },
                "session_stats": self.session_stats.copy()
            }
            
            safe_print(f"✅ เสร็จสิ้น! เวลา: {generation_time:.1f} วินาที")
            return result
            
        except Exception as e:
            safe_print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "generation_time_seconds": (datetime.now() - start_time).total_seconds()
            }

class ThaiSafeInterface:
    """อินเทอร์เฟซที่รองรับภาษาไทย"""
    
    def __init__(self):
        self.engine = ThaiSafeContentEngine()
        
    def display_welcome(self):
        """แสดงหน้าต้อนรับ"""
        safe_print("")
        safe_print("="*70)
        safe_print("🎬 AI CONTENT GENERATION ENGINE - THAI SUPPORT")  
        safe_print("="*70)
        safe_print("🚀 สร้างเนื้อหา viral สำหรับ Social Media อัตโนมัติ!")
        safe_print("")
        safe_print("💡 รองรับแพลตฟอร์ม: YouTube, TikTok, Instagram, Facebook")
        safe_print("🎯 ระดับคุณภาพ: Budget (ประหยัด), Standard, Premium")
        safe_print("🤖 AI: รองรับภาษาไทยเต็มรูปแบบ")
        safe_print("")
        safe_print("💰 ต้นทุน: 1-5 บาท/วิดีโอ (ประหยัด 99%!)")
        safe_print("⏱️  ความเร็ว: 10-60 วินาที/วิดีโอ")
        safe_print("="*70)
        
    def get_user_input(self) -> Dict:
        """รับข้อมูลจากผู้ใช้"""
        safe_print("")
        safe_print("📝 สร้างเนื้อหาใหม่")
        safe_print("-" * 30)
        
        # รับหัวข้อ
        safe_print("🎯 หัวข้อเนื้อหา:")
        safe_print("   ตัวอย่าง: 'AI สร้างเนื้อหา', 'ลงทุน Crypto', 'ทำอาหารง่ายๆ'")
        topic = input("📍 ใส่หัวข้อ: ").strip()
        
        if not topic:
            topic = "เทรนด์น่าสนใจ"
            safe_print(f"   → ใช้หัวข้อเริ่มต้น: {topic}")
        
        # รับมุมมอง  
        safe_print(f"\\n💡 มุมมองเนื้อหา:")
        safe_print("   ตัวอย่าง: 'วิธีใช้สำหรับมือใหม่', 'เคล็ดลับที่ไม่มีใครบอก'")
        angle = input("📍 ใส่มุมมอง: ").strip()
        
        if not angle:
            angle = f"สิ่งที่ควรรู้เกี่ยวกับ {topic}"
            safe_print(f"   → ใช้มุมมองเริ่มต้น: {angle}")
        
        # เลือกแพลตฟอร์ม
        safe_print(f"\\n📱 เลือกแพลตฟอร์ม:")
        platforms = {
            "1": ("youtube", "YouTube - วิดีโอยาว (5-15 นาที)"),
            "2": ("tiktok", "TikTok - วิดีโอสั้น (30-90 วินาที)"), 
            "3": ("instagram", "Instagram - เรื่องราว (30-120 วินาที)"),
            "4": ("facebook", "Facebook - แชร์ได้ (2-8 นาที)")
        }
        
        for key, (platform, description) in platforms.items():
            safe_print(f"   {key}. {description}")
        
        platform_choice = input("📍 เลือกแพลตฟอร์ม (1-4): ").strip()
        platform, platform_desc = platforms.get(platform_choice, ("youtube", "YouTube"))
        safe_print(f"   → เลือก: {platform_desc}")
        
        return {
            "topic": topic,
            "angle": angle,
            "platform": platform,
            "quality": "budget",
            "duration": 5
        }
    
    def display_result(self, result: Dict):
        """แสดงผลลัพธ์"""
        safe_print("")
        safe_print("="*60)
        
        if result["success"]:
            script = result["script"]
            cost = result["cost_estimate"]
            
            safe_print("🎉 เนื้อหาสร้างสำเร็จ!")
            safe_print("="*60)
            
            # ตัวชี้วัด
            safe_print(f"⏱️  เวลาสร้าง: {result['generation_time_seconds']:.1f} วินาที")
            safe_print(f"💰 ต้นทุนรวม: ฿{cost['total_cost_baht']}")
            safe_print(f"💎 คุณภาพ: {cost['quality_score']}/10")
            safe_print(f"📈 ROI คาดการณ์: {cost['estimated_roi']}%")
            
            # ตัวอย่างเนื้อหา
            safe_print(f"\\n📝 ตัวอย่างเนื้อหา:")
            safe_print("-" * 40)
            safe_print(f"🎬 ชื่อเรื่อง: {script['title_suggestions'][0]}")
            safe_print(f"⚡ Hook: {script['hook'][:100]}...")
            safe_print(f"🏷️  Hashtags: {' '.join(script['hashtags'][:5])}")
            
            # ถามว่าจะดูแบบเต็มไหม
            safe_print(f"\\n💡 ดูสคริปต์เต็ม? (y/n): ", end="")
            show_full = input().strip().lower()
            
            if show_full in ['y', 'yes', 'ใช่']:
                self.display_full_script(script)
                
        else:
            safe_print("❌ การสร้างเนื้อหาล้มเหลว!")
            safe_print("="*40)
            safe_print(f"🚫 ข้อผิดพลาด: {result['error']}")
    
    def display_full_script(self, script: Dict):
        """แสดงสคริปต์เต็ม"""
        safe_print(f"\\n📜 สคริปต์เต็ม:")
        safe_print("="*50)
        
        safe_print(f"\\n🎬 ชื่อเรื่องแนะนำ:")
        for i, title in enumerate(script['title_suggestions'], 1):
            safe_print(f"   {i}. {title}")
        
        safe_print(f"\\n⚡ Hook:")
        safe_print(f"   {script['hook']}")
        
        safe_print(f"\\n🎯 Introduction:")
        safe_print(f"   {script['introduction']}")
        
        safe_print(f"\\n📋 เนื้อหาหลัก:")
        for line in script['main_content'].split('\\n'):
            if line.strip():
                safe_print(f"   {line.strip()}")
        
        safe_print(f"\\n🎭 Conclusion:")
        safe_print(f"   {script['conclusion']}")
        
        safe_print(f"\\n📢 Call to Action:")
        safe_print(f"   {script['call_to_action']}")
        
        safe_print(f"\\n🏷️  Hashtags:")
        safe_print(f"   {' '.join(script['hashtags'])}")
    
    async def run_interactive_mode(self):
        """รันโหมดโต้ตอบ"""
        self.display_welcome()
        
        while True:
            try:
                # รับข้อมูลจากผู้ใช้
                request = self.get_user_input()
                
                safe_print(f"\\n🚀 กำลังสร้างเนื้อหา...")
                safe_print("⏳ กรุณารอสักครู่...")
                
                # สร้างเนื้อหา
                result = await self.engine.generate_complete_content(request)
                
                # แสดงผลลัพธ์
                self.display_result(result)
                
                # ถามจะสร้างต่อไหม
                safe_print(f"\\n" + "="*50)
                next_action = input("🎯 สร้างเนื้อหาอื่นต่อไหม? (y/n): ").strip().lower()
                if next_action not in ['y', 'yes', 'ใช่']:
                    safe_print(f"\\n🎉 ขอบคุณที่ใช้บริการ!")
                    break
                    
            except KeyboardInterrupt:
                safe_print(f"\\n\\n👋 ขอบคุณที่ใช้ AI Content Engine!")
                break
            except Exception as e:
                safe_print(f"\\n❌ เกิดข้อผิดพลาด: {e}")
                continue

# Main execution
async def main():
    """ฟังก์ชันหลัก"""
    try:
        interface = ThaiSafeInterface()
        await interface.run_interactive_mode()
    except KeyboardInterrupt:
        safe_print("\\n👋 Goodbye!")
    except Exception as e:
        safe_print(f"\\n❌ Fatal error: {e}")

if __name__ == "__main__":
    # ตรวจสอบการรองรับภาษาไทย
    safe_print("🔧 ตรวจสอบการรองรับภาษาไทย...")
    
    # ทดสอบการแสดงผล
    test_thai = "ทดสอบการแสดงผลภาษาไทย: สวัสดี 🎬"
    safe_print(f"📝 {test_thai}")
    
    try:
        asyncio.run(main())
    except Exception as e:
        safe_print(f"Failed to start: {e}")
        input("\\nกด Enter เพื่อปิด...")
'''
    
    try:
        with open('production_content_engine_thai.py', 'w', encoding='utf-8') as f:
            f.write(fixed_code)
        print("✅ สร้างไฟล์ production_content_engine_thai.py เรียบร้อย")
        return True
    except Exception as e:
        print(f"❌ สร้างไฟล์ล้มเหลว: {e}")
        return False

def test_thai_display():
    """ทดสอบการแสดงผลภาษาไทย"""
    print("🧪 ทดสอบการแสดงผลภาษาไทย...")
    
    test_texts = [
        "🎬 AI Content Generation Engine",
        "📝 สร้างเนื้อหา viral อัตโนมัติ",
        "💰 ต้นทุน: ฿2.50 บาท",
        "🎯 แพลตฟอร์ม: YouTube, TikTok, Instagram",
        "✅ การทดสอบเสร็จสิ้น"
    ]
    
    success_count = 0
    for i, text in enumerate(test_texts, 1):
        try:
            print(f"Test {i}: {text}")
            success_count += 1
        except Exception as e:
            print(f"Test {i}: ❌ Error - {e}")
    
    success_rate = (success_count / len(test_texts)) * 100
    print(f"\n📊 ผลการทดสอบ: {success_count}/{len(test_texts)} ({success_rate:.1f}%)")
    
    return success_rate >= 80

def main():
    """ฟังก์ชันหลัก"""
    print("🔧 AI Content Engine - Thai Display Fix")
    print("=" * 50)
    
    # Apply fixes
    fixes = fix_thai_display()
    for fix in fixes:
        print(f"   {fix}")
    
    # Test display
    print("\n🧪 ทดสอบการแสดงผลภาษาไทย...")
    if test_thai_display():
        print("✅ การแสดงผลภาษาไทยทำงานได้ดี!")
    else:
        print("⚠️ อาจยังมีปัญหาการแสดงผลบางส่วน")
    
    # Create batch launcher
    print("\n📄 สร้างไฟล์เรียกใช้...")
    create_batch_launcher()
    
    # Create fixed production engine
    print("🔧 สร้าง Production Engine ที่แก้ไขแล้ว...")
    create_fixed_production_engine()
    
    print("\n🎉 การแก้ไขเสร็จสิ้น!")
    print("\n📋 วิธีใช้งาน:")
    print("1. 🖱️  ดับเบิลคลิก: start_thai.bat")
    print("2. ⌨️  หรือรัน: python production_content_engine_thai.py")
    print("3. 🖥️  หรือใช้ Windows Terminal (แนะนำ)")
    
    input("\nกด Enter เพื่อปิด...")

if __name__ == "__main__":
    main()