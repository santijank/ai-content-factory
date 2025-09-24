#!/usr/bin/env python3
"""
ทดสอบการแสดงผลภาษาไทยหลังแก้ไข Registry
"""

import sys
import os

def test_thai_display():
    """ทดสอบการแสดงผลภาษาไทย"""
    print("🧪 ทดสอบการแสดงผลภาษาไทยหลังแก้ไข Registry")
    print("=" * 60)
    
    # ตรวจสอบ Code Page
    try:
        import subprocess
        result = subprocess.run(['chcp'], capture_output=True, text=True, shell=True)
        current_cp = result.stdout.strip()
        print(f"📋 Code Page ปัจจุบัน: {current_cp}")
        
        if "65001" in current_cp:
            print("✅ Code Page ตั้งค่าเป็น UTF-8 แล้ว")
        else:
            print("⚠️ Code Page ยังไม่ใช่ UTF-8")
    except:
        print("ℹ️ ไม่สามารถตรวจสอบ Code Page ได้")
    
    print("\n🔤 ทดสอบการแสดงผลข้อความภาษาไทย:")
    print("-" * 40)
    
    # ข้อความทดสอบ
    test_texts = [
        "🎬 AI Content Generation Engine",
        "📝 สร้างเนื้อหา viral สำหรับ Social Media",
        "💰 ต้นทุน: ฿2.50 บาท ประหยัด 99%",
        "🎯 แพลตฟอร์ม: YouTube, TikTok, Instagram, Facebook",
        "⚡ ความเร็ว: 10-30 วินาทีต่อวิดีโอ",
        "🏷️ Hashtags: #AI #สร้างเนื้อหา #viral #trending",
        "📊 ROI คาดการณ์: 500-2000%",
        "🚀 พร้อมใช้งานจริงแล้ว!"
    ]
    
    success_count = 0
    for i, text in enumerate(test_texts, 1):
        try:
            print(f"{i:2d}. {text}")
            success_count += 1
        except Exception as e:
            print(f"{i:2d}. ❌ Error: {e}")
    
    # สรุปผลการทดสอบ
    success_rate = (success_count / len(test_texts)) * 100
    print("\n" + "=" * 60)
    print(f"📊 ผลการทดสอบ: {success_count}/{len(test_texts)} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 การแสดงผลภาษาไทยทำงานได้เยี่ยม!")
        print("✅ พร้อมใช้งาน AI Content Engine แล้ว!")
        
        # แสดงคำแนะนำการใช้งาน
        print("\n🚀 วิธีใช้งาน:")
        print("1. รันคำสั่ง: python production_content_engine.py")
        print("2. หรือใช้ไฟล์: python production_content_engine_thai.py (ถ้ามี)")
        print("3. ทำตามขั้นตอนในโปรแกรม")
        
        return True
        
    elif success_rate >= 70:
        print("⚠️ การแสดงผลภาษาไทยทำงานได้บางส่วน")
        print("💡 อาจต้องปรับฟอนต์ใน Command Prompt:")
        print("   - คลิกขวาที่ title bar → Properties → Font")
        print("   - เลือก 'Consolas' หรือ 'Courier New'")
        return True
        
    else:
        print("❌ การแสดงผลภาษาไทยยังมีปัญหา")
        print("🔧 วิธีแก้ไขเพิ่มเติม:")
        print("1. ใช้ Windows Terminal แทน Command Prompt")
        print("2. ใช้ PowerShell แทน Command Prompt") 
        print("3. ใช้ Web Dashboard (python web_dashboard.py)")
        return False

def show_usage_guide():
    """แสดงคำแนะนำการใช้งาน"""
    print("\n" + "=" * 60)
    print("📋 คำแนะนำการใช้งาน AI Content Engine")
    print("=" * 60)
    
    print("\n🎯 ตัวเลือกการใช้งาน:")
    print("1. 📱 Command Line (ที่แก้ไขแล้ว)")
    print("   - รัน: python production_content_engine.py")
    print("   - เหมาะสำหรับ: ผู้เชี่ยวชาญ, automation")
    
    print("\n2. 🌐 Web Dashboard (แนะนำสำหรับมือใหม่)")
    print("   - รัน: python web_dashboard.py") 
    print("   - เข้าใช้: http://localhost:5000")
    print("   - เหมาะสำหรับ: การใช้งานทั่วไป, UI สวย")
    
    print("\n3. ⚡ Windows Terminal (แนะนำสำหรับ Advanced)")
    print("   - ติดตั้งจาก Microsoft Store")
    print("   - เปิด Windows Terminal แล้วรันคำสั่ง")
    print("   - เหมาะสำหรับ: ประสบการณ์ที่ดีที่สุด")

def main():
    """ฟังก์ชันหลัก"""
    # ตั้งค่า encoding
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        pass
    
    # รันการทดสอบ
    test_result = test_thai_display()
    
    # แสดงคำแนะนำ
    show_usage_guide()
    
    # ถามว่าจะรัน Content Engine ไหม
    if test_result:
        print("\n" + "=" * 60)
        try:
            choice = input("🚀 ต้องการทดลองใช้ AI Content Engine เลยไหม? (y/n): ").strip().lower()
            
            if choice in ['y', 'yes', 'ใช่']:
                print("\n⏳ กำลังเริ่มต้น AI Content Engine...")
                print("📝 กรุณารอสักครู่...")
                
                # Import และรัน Content Engine
                try:
                    # ลองใช้ production engine ปกติก่อน
                    os.system('python production_content_engine.py')
                except FileNotFoundError:
                    print("❌ ไม่พบไฟล์ production_content_engine.py")
                    print("💡 กรุณาตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์เดียวกัน")
                except KeyboardInterrupt:
                    print("\n👋 ปิดการใช้งานแล้ว")
                except Exception as e:
                    print(f"\n❌ เกิดข้อผิดพลาด: {e}")
            else:
                print("\n👍 เข้าใจแล้ว! คุณสามารถรันคำสั่งด้านบนได้เมื่อพร้อม")
                
        except KeyboardInterrupt:
            print("\n👋 ขอบคุณที่ใช้บริการ!")
    
    print("\n🎉 การทดสอบเสร็จสิ้น!")
    input("กด Enter เพื่อปิด...")

if __name__ == "__main__":
    main()