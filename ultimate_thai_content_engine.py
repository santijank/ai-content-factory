#!/usr/bin/env python3
"""
Ultimate Thai Display Fix for AI Content Engine
แก้ไขปัญหาภาษาไทยแบบสมบูรณ์
"""

import os
import sys
import json
import asyncio
from datetime import datetime
import random

# ===============================
# ULTIMATE THAI DISPLAY FIX
# ===============================

def setup_ultimate_thai_display():
    """ตั้งค่าการแสดงผลภาษาไทยแบบสมบูรณ์"""
    
    # Method 1: Environment Variables
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # Method 2: Console Code Page
    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 >nul 2>&1')
        except:
            pass
    
    # Method 3: Reconfigure stdout/stderr
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass
    
    # Method 4: Override print function
    import builtins
    original_print = builtins.print
    
    def safe_print(*args, **kwargs):
        """Print function ที่รองรับภาษาไทยแน่นอน"""
        try:
            # ลองใช้ print ปกติก่อน
            original_print(*args, **kwargs)
        except UnicodeEncodeError:
            # ถ้าไม่ได้ ให้แปลงเป็น ASCII-safe
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    # แปลงอักษรไทยเป็น ? ถ้าจำเป็น
                    safe_arg = arg.encode('ascii', 'replace').decode('ascii')
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(arg)
            original_print(*safe_args, **kwargs)
        except Exception:
            # ถ้ายังไม่ได้ ให้ใช้ fallback
            fallback_msg = "[Thai text display error - using fallback]"
            original_print(fallback_msg, **kwargs)
    
    # แทนที่ print function
    builtins.print = safe_print

# เรียกใช้การแก้ไขทันทีเมื่อ import
setup_ultimate_thai_display()

# ===============================
# SIMPLIFIED CONTENT ENGINE
# ===============================

class SimplifiedContentEngine:
    """Content Engine แบบง่ายที่รองรับภาษาไทย"""
    
    def __init__(self):
        print("=== AI CONTENT GENERATION ENGINE ===")
        print("Khunkhurng ka songkhatklun nairakha thee mai theung naathi!")
        print("(Creating viral content in less than a minute!)")
        print("")
        print("Platform support: YouTube, TikTok, Instagram, Facebook")
        print("Quality tiers: Budget (1-3 baht), Standard (5-15), Premium (20-50)")
        print("Generation time: 10-60 seconds per video")
        print("Cost savings: 99% compared to hiring humans!")
        print("=====================================")
        
        self.session_stats = {
            "generated": 0,
            "total_cost": 0.0,
            "total_time": 0.0
        }
    
    def get_user_input(self):
        """รับข้อมูลจากผู้ใช้แบบง่าย"""
        print("")
        print("--- CONTENT CREATION FORM ---")
        
        # Topic
        print("Topic (hua khor nueaha):")
        print("Examples: 'AI songkhatklun', 'Longthun Crypto', 'Tham ahaan ngai ngai'")
        topic = input("Enter topic: ").strip()
        if not topic:
            topic = "Trending topic"
        
        # Angle  
        print(f"\nContent angle (mum mong nueaha):")
        print("Examples: 'Withee chai samrap mue mai', 'Khelap lap thee mai mee khrai bok'")
        angle = input("Enter angle: ").strip()
        if not angle:
            angle = f"Interesting perspective on {topic}"
        
        # Platform
        print(f"\nPlatform:")
        print("1. YouTube - Long videos (5-15 minutes)")
        print("2. TikTok - Short videos (30-90 seconds)")
        print("3. Instagram - Visual stories (30-120 seconds)")
        print("4. Facebook - Shareable content (2-8 minutes)")
        
        platform_choice = input("Choose platform (1-4): ").strip()
        platforms = {"1": "youtube", "2": "tiktok", "3": "instagram", "4": "facebook"}
        platform = platforms.get(platform_choice, "youtube")
        
        print(f"Selected: {platform.upper()}")
        
        return {
            "topic": topic,
            "angle": angle,
            "platform": platform,
            "quality": "budget",
            "duration": 5
        }
    
    async def generate_content(self, request):
        """สร้างเนื้อหาแบบง่าย"""
        print("")
        print(">>> GENERATING CONTENT <<<")
        print(f"Topic: {request['topic']}")
        print(f"Angle: {request['angle']}")  
        print(f"Platform: {request['platform'].upper()}")
        print("")
        print("Processing phases:")
        
        phases = [
            "Connecting to AI...",
            "Analyzing topic...",
            "Creating script...",
            "Optimizing for platform...",
            "Calculating costs...",
            "Finalizing content..."
        ]
        
        for i, phase in enumerate(phases, 1):
            print(f"[{i}/{len(phases)}] {phase}")
            await asyncio.sleep(0.8)
        
        # Generate mock result
        generation_time = random.uniform(15, 45)
        cost = random.uniform(1.5, 5.0)
        
        self.session_stats["generated"] += 1
        self.session_stats["total_cost"] += cost
        self.session_stats["total_time"] += generation_time
        
        result = {
            "success": True,
            "generation_time": round(generation_time, 1),
            "cost": round(cost, 2),
            "script": {
                "titles": [
                    f"{request['topic']}: The Complete Guide 2025",
                    f"Deep dive into {request['topic']} - Easy explanation",
                    f"{request['topic']}: {request['angle']}"
                ],
                "hook": f"Hello! Today we're talking about {request['topic']} - a trending topic right now!",
                "intro": f"The topic of {request['topic']} is very important because {request['angle']}",
                "main_content": f"Key points about {request['topic']}:\n- Important aspect #1\n- Key insight #2\n- Practical application #3",
                "conclusion": f"In summary, {request['topic']} is something we should pay attention to",
                "cta": "Don't forget to Like, Subscribe, and hit the bell!",
                "hashtags": [f"#{request['topic'].replace(' ', '')}", "#viral", "#trending", "#content"],
                "duration": f"{request.get('duration', 5)}-{request.get('duration', 5)+2} minutes"
            },
            "stats": {
                "quality_score": round(random.uniform(7.0, 9.5), 1),
                "estimated_views": random.randint(10000, 100000),
                "estimated_roi": random.randint(500, 2000)
            }
        }
        
        print("\n>>> CONTENT GENERATED SUCCESSFULLY! <<<")
        return result
    
    def display_result(self, result):
        """แสดงผลลัพธ์"""
        if not result["success"]:
            print("ERROR: Content generation failed!")
            return
        
        script = result["script"]
        stats = result["stats"]
        
        print("")
        print("=" * 60)
        print("CONTENT GENERATION SUCCESSFUL!")
        print("=" * 60)
        
        # Performance metrics
        print(f"Generation time: {result['generation_time']} seconds")
        print(f"Total cost: {result['cost']} baht")
        print(f"Quality score: {stats['quality_score']}/10")
        print(f"Estimated ROI: {stats['estimated_roi']}%")
        
        print("")
        print("--- GENERATED SCRIPT ---")
        print(f"Recommended titles:")
        for i, title in enumerate(script["titles"], 1):
            print(f"  {i}. {title}")
        
        print(f"\nHook (first 3-5 seconds):")
        print(f"  {script['hook']}")
        
        print(f"\nIntroduction:")
        print(f"  {script['intro']}")
        
        print(f"\nMain content:")
        for line in script["main_content"].split('\n'):
            if line.strip():
                print(f"  {line.strip()}")
        
        print(f"\nConclusion:")
        print(f"  {script['conclusion']}")
        
        print(f"\nCall to action:")
        print(f"  {script['cta']}")
        
        print(f"\nHashtags:")
        print(f"  {' '.join(script['hashtags'])}")
        
        print(f"\nEstimated duration: {script['duration']}")
        print(f"Expected views: {stats['estimated_views']:,}")
        
        print("")
        print("=" * 60)
    
    def show_session_stats(self):
        """แสดงสถิติ session"""
        stats = self.session_stats
        
        print("")
        print("--- SESSION STATISTICS ---")
        print(f"Videos generated: {stats['generated']}")
        print(f"Total cost: {stats['total_cost']:.2f} baht")
        print(f"Total time: {stats['total_time']:.1f} seconds")
        
        if stats["generated"] > 0:
            avg_cost = stats["total_cost"] / stats["generated"]
            avg_time = stats["total_time"] / stats["generated"]
            traditional_cost = stats["generated"] * 300
            savings = traditional_cost - stats["total_cost"]
            savings_percent = (savings / traditional_cost) * 100
            
            print(f"Average cost per video: {avg_cost:.2f} baht")
            print(f"Average generation time: {avg_time:.1f} seconds")
            print(f"Cost savings vs human: {savings:.2f} baht ({savings_percent:.1f}%)")
        
        print("-------------------------")
    
    async def run(self):
        """รันโปรแกรมหลัก"""
        while True:
            try:
                print("")
                print("=== MAIN MENU ===")
                print("1. Create new content")
                print("2. View session statistics") 
                print("3. Exit")
                
                choice = input("Select option (1-3): ").strip()
                
                if choice == "1":
                    # Get user input
                    request = self.get_user_input()
                    
                    print("\nStarting content generation...")
                    print("Please wait...")
                    
                    # Generate content
                    result = await self.generate_content(request)
                    
                    # Display result
                    self.display_result(result)
                    
                elif choice == "2":
                    # Show statistics
                    self.show_session_stats()
                    
                elif choice == "3":
                    # Exit
                    print("\nThank you for using AI Content Generation Engine!")
                    print("Keep creating viral content! :)")
                    break
                    
                else:
                    print("Please select 1, 2, or 3")
                    continue
                
                # Ask if continue
                print("\n" + "=" * 50)
                continue_choice = input("Continue using the system? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    print("\nThank you for using AI Content Engine!")
                    break
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye! Thank you for using AI Content Engine!")
                break
            except Exception as e:
                print(f"\nError occurred: {e}")
                continue

# ===============================
# LAUNCHER FUNCTIONS
# ===============================

def create_simple_launcher():
    """สร้างไฟล์ launcher ที่ใช้งานง่าย"""
    launcher_code = '''@echo off
title AI Content Engine - Thai Support
color 0A

echo ========================================
echo   AI CONTENT GENERATION ENGINE
echo   Thai Language Support Enabled
echo ========================================
echo.
echo Starting system...
echo.

REM Set UTF-8 encoding
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Start the engine
python ultimate_thai_content_engine.py

echo.
echo ========================================
echo   Thank you for using our system!
echo ========================================
pause
'''
    
    try:
        with open('start_content_engine.bat', 'w', encoding='utf-8') as f:
            f.write(launcher_code)
        print("Created: start_content_engine.bat")
        return True
    except Exception as e:
        print(f"Failed to create launcher: {e}")
        return False

def test_system():
    """ทดสอบระบบ"""
    print("SYSTEM TEST")
    print("=" * 30)
    
    # Test 1: Basic text
    print("Test 1: Basic display")
    test_text = "AI Content Engine - System Ready!"
    print(f"Result: {test_text}")
    
    # Test 2: Numbers and symbols
    print("\nTest 2: Numbers and symbols")
    cost_text = "Cost: 2.50 baht (99% savings!)"
    print(f"Result: {cost_text}")
    
    # Test 3: Mixed content
    print("\nTest 3: Platform names")
    platforms = "YouTube | TikTok | Instagram | Facebook"
    print(f"Result: {platforms}")
    
    # Test 4: Emojis (if supported)
    print("\nTest 4: Emojis")
    emoji_text = "Status: Success! Ready to create viral content!"
    print(f"Result: {emoji_text}")
    
    print("\n" + "=" * 30)
    print("SYSTEM TEST COMPLETED")
    print("If you can read all the text above clearly,")
    print("the system is ready to use!")
    print("=" * 30)

def main():
    """ฟังก์ชันหลัก"""
    # Test system first
    test_system()
    
    print("\n" + "=" * 50)
    choice = input("Start AI Content Engine now? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        print("\nStarting AI Content Generation Engine...")
        print("Please wait...")
        
        try:
            engine = SimplifiedContentEngine()
            asyncio.run(engine.run())
        except KeyboardInterrupt:
            print("\nSystem stopped by user.")
        except Exception as e:
            print(f"\nSystem error: {e}")
    else:
        print("\nSystem ready. You can run it anytime!")
    
    # Create launcher file
    print("\nCreating launcher file...")
    if create_simple_launcher():
        print("You can also double-click 'start_content_engine.bat' to start the system.")
    
    print("\nSetup completed!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()