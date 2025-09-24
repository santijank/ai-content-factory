#!/usr/bin/env python3
"""
AI Content Generation Engine - Universal Thai Support
รองรับการแสดงผลภาษาไทยในทุกสภาพแวดล้อม
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, List

# ===============================
# Universal Thai Display Fix
# ===============================

def setup_universal_thai():
    """ตั้งค่าภาษาไทยสำหรับทุก environment"""
    
    # Set environment variables
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # Fix Windows CMD
    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 >nul 2>&1')
        except:
            pass
    
    # Reconfigure stdout/stderr if possible
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# Apply fixes immediately
setup_universal_thai()

# ===============================
# Safe Print Functions
# ===============================

def safe_print(text: str, end: str = '\n'):
    """พิมพ์ข้อความอย่างปลอดภัย รองรับภาษาไทย"""
    try:
        print(text, end=end, flush=True)
    except UnicodeEncodeError:
        # Fallback 1: Replace problematic characters
        try:
            safe_text = text.encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text, end=end, flush=True)
        except:
            # Fallback 2: ASCII only
            ascii_text = text.encode('ascii', errors='ignore').decode('ascii')
            print(ascii_text, end=end, flush=True)
    except Exception as e:
        print(f"[Print Error: {e}]", end=end, flush=True)

def print_header(text: str, char: str = "=", width: int = 70):
    """พิมพ์หัวข้อ"""
    safe_print(char * width)
    safe_print(text)
    safe_print(char * width)

def print_section(title: str):
    """พิมพ์หัวข้อส่วน"""
    safe_print(f"\n{title}")
    safe_print("-" * 40)

# ===============================
# Content Engine
# ===============================

class ContentEngine:
    """AI Content Generation Engine"""
    
    def __init__(self):
        self.stats = {
            "generated": 0,
            "total_cost": 0.0,
            "total_time": 0.0
        }
        safe_print("✅ Content Engine พร้อมใช้งาน")
    
    async def generate_content(self, request: Dict) -> Dict:
        """สร้างเนื้อหา"""
        import random
        
        start = datetime.now()
        safe_print(f"🎬 กำลังสร้าง: {request.get('topic', 'ไม่ระบุ')}")
        
        # Simulate processing
        await asyncio.sleep(random.uniform(1, 3))
        
        gen_time = random.uniform(10, 30)
        cost = random.uniform(1.5, 5.0)
        
        # Update stats
        self.stats["generated"] += 1
        self.stats["total_cost"] += cost
        self.stats["total_time"] += gen_time
        
        topic = request.get('topic', 'เทรนด์')
        angle = request.get('angle', 'วิเคราะห์')
        
        result = {
            "success": True,
            "time": round(gen_time, 1),
            "cost": round(cost, 2),
            "script": {
                "titles": [
                    f"{topic}: ที่ต้องรู้ในปี 2025",
                    f"วิเคราะห์ {topic} แบบเข้าใจง่าย",
                    f"{topic}: มุมมองใหม่ที่น่าสนใจ"
                ],
                "hook": f"สวัสดีครับ! วันนี้เรามาพูดถึง {topic} กัน",
                "intro": f"เรื่อง {topic} สำคัญมากเพราะว่า {angle}",
                "main": f"ประเด็นสำคัญของ {topic} มี 3 ข้อ:\n1. ความสำคัญ\n2. {angle}\n3. การนำไปใช้",
                "conclusion": f"สรุปได้ว่า {topic} คือสิ่งที่ควรติดตาม",
                "cta": "กด Like Subscribe และแชร์ให้เพื่อนด้วยนะครับ",
                "hashtags": [f"#{topic.replace(' ', '')}", "#viral", "#trending2025"]
            },
            "estimate": {
                "quality": round(random.uniform(7, 9.5), 1),
                "views": random.randint(5000, 50000),
                "roi": random.randint(300, 1500)
            }
        }
        
        safe_print(f"✅ สำเร็จ! ({gen_time:.1f}s)")
        return result

# ===============================
# User Interface
# ===============================

class UserInterface:
    """อินเทอร์เฟซผู้ใช้"""
    
    def __init__(self):
        self.engine = ContentEngine()
    
    def show_welcome(self):
        """แสดงหน้าต้อนรับ"""
        safe_print("")
        print_header("🎬 AI CONTENT GENERATION ENGINE")
        safe_print("")
        safe_print("🚀 สร้างเนื้อหา Viral อัตโนมัติด้วย AI")
        safe_print("💡 รองรับ: YouTube, TikTok, Instagram, Facebook")
        safe_print("💰 ต้นทุน: 1-5 บาท/วิดีโอ")
        safe_print("⚡ ความเร็ว: 10-60 วินาที")
        safe_print("")
        print_header("", char="=")
    
    def get_input(self) -> Dict:
        """รับข้อมูลจากผู้ใช้"""
        print_section("📝 สร้างเนื้อหาใหม่")
        
        # Topic
        safe_print("🎯 หัวข้อ (เช่น: AI, Crypto, Gaming):")
        topic = input("   > ").strip() or "เทรนด์ปี 2025"
        
        # Angle
        safe_print(f"\n💡 มุมมอง (เช่น: ฉบับมือใหม่, เจาะลึก):")
        angle = input("   > ").strip() or f"วิเคราะห์ {topic}"
        
        # Platform
        safe_print(f"\n📱 แพลตฟอร์ม:")
        safe_print("   1. YouTube (5-15 นาที)")
        safe_print("   2. TikTok (30-90 วินาที)")
        safe_print("   3. Instagram Reels")
        safe_print("   4. Facebook")
        
        platform_map = {
            "1": "youtube", "2": "tiktok",
            "3": "instagram", "4": "facebook"
        }
        choice = input("   > ").strip()
        platform = platform_map.get(choice, "youtube")
        
        safe_print(f"\n→ {topic} | {platform.upper()}")
        return {
            "topic": topic,
            "angle": angle,
            "platform": platform
        }
    
    def show_result(self, result: Dict):
        """แสดงผลลัพธ์"""
        safe_print("")
        print_header("🎉 ผลลัพธ์", char="=")
        
        if result["success"]:
            script = result["script"]
            estimate = result["estimate"]
            
            # Stats
            safe_print(f"⏱️  เวลา: {result['time']}s")
            safe_print(f"💰 ต้นทุน: ฿{result['cost']}")
            safe_print(f"💎 คุณภาพ: {estimate['quality']}/10")
            safe_print(f"📈 ROI: {estimate['roi']}%")
            
            # Preview
            print_section("📝 ตัวอย่าง")
            safe_print(f"📌 {script['titles'][0]}")
            safe_print(f"⚡ {script['hook'][:80]}...")
            safe_print(f"🏷️  {' '.join(script['hashtags'][:3])}")
            
            # Ask for full script
            safe_print(f"\n💡 ดูสคริปต์เต็ม? (y/n): ", end="")
            if input().strip().lower() in ['y', 'yes', 'ใช่']:
                self.show_full_script(script)
        else:
            safe_print(f"❌ ล้มเหลว: {result.get('error', 'Unknown')}")
    
    def show_full_script(self, script: Dict):
        """แสดงสคริปต์เต็ม"""
        print_section("📜 สคริปต์เต็ม")
        
        safe_print(f"\n🎬 ชื่อเรื่อง:")
        for i, title in enumerate(script['titles'], 1):
            safe_print(f"   {i}. {title}")
        
        safe_print(f"\n⚡ Hook:\n   {script['hook']}")
        safe_print(f"\n🎯 Intro:\n   {script['intro']}")
        safe_print(f"\n📋 เนื้อหา:\n   {script['main']}")
        safe_print(f"\n🎭 สรุป:\n   {script['conclusion']}")
        safe_print(f"\n📢 CTA:\n   {script['cta']}")
        safe_print(f"\n🏷️  Tags: {' '.join(script['hashtags'])}")
    
    async def run(self):
        """เริ่มโปรแกรม"""
        self.show_welcome()
        
        while True:
            try:
                # Get input
                request = self.get_input()
                
                safe_print(f"\n🚀 กำลังประมวลผล...")
                
                # Generate
                result = await self.engine.generate_content(request)
                
                # Show result
                self.show_result(result)
                
                # Continue?
                safe_print(f"\n" + "="*50)
                safe_print("🎯 สร้างต่อ? (y/n): ", end="")
                if input().strip().lower() not in ['y', 'yes', 'ใช่']:
                    safe_print("\n👋 ขอบคุณที่ใช้บริการ!")
                    break
                    
            except KeyboardInterrupt:
                safe_print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                safe_print(f"\n❌ Error: {e}")

# ===============================
# Main
# ===============================

async def main():
    """ฟังก์ชันหลัก"""
    ui = UserInterface()
    await ui.run()

if __name__ == "__main__":
    # Test Thai display
    safe_print("🧪 ทดสอบภาษาไทย: สวัสดี 🎬✨")
    
    # Run
    try:
        asyncio.run(main())
    except Exception as e:
        safe_print(f"\n❌ Fatal: {e}")
        input("\nกด Enter เพื่อปิด...")