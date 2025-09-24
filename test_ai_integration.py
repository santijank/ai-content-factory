# test_ai_integration.py - เวอร์ชันที่แก้ไขแล้ว
import asyncio
import os
import sys
from dotenv import load_dotenv

# เพิ่ม path สำหรับ import
sys.path.append('content-engine')
sys.path.append('.')

load_dotenv()

async def test_groq_api():
    """ทดสอบ Groq API ด้วย model ใหม่"""
    print("🔄 ทดสอบ Groq API...")
    
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        # ลิสต์ models ใหม่ที่น่าจะยังใช้ได้
        models_to_try = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile", 
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "gemma-7b-it"
        ]
        
        working_model = None
        
        for model in models_to_try:
            try:
                print(f"  🔍 ทดสอบ model: {model}")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "สวัสดี ตอบสั้นๆ ว่าคุณคือใคร"}
                    ],
                    max_tokens=50
                )
                
                working_model = model
                print(f"✅ Groq API ทำงานได้ด้วย model: {model}")
                print(f"ตอบกลับ: {response.choices[0].message.content}")
                break
                
            except Exception as e:
                print(f"  ❌ Model {model} ไม่ทำงาน: {str(e)[:100]}...")
                continue
        
        if working_model:
            return True, working_model
        else:
            print("❌ ไม่มี model ใดที่ใช้ได้")
            return False, None
            
    except Exception as e:
        print(f"❌ Groq API Connection Error: {e}")
        return False, None

async def test_openai_api():
    """ทดสอบ OpenAI API"""
    print("\n🔄 ทดสอบ OpenAI API...")
    
    try:
        import openai
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "สวัสดี ตอบสั้นๆ ว่าคุณคือใคร"}
            ],
            max_tokens=50
        )
        
        print("✅ OpenAI API ทำงานได้!")
        print(f"ตอบกลับ: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        if "insufficient_quota" in str(e):
            print("⚠️ OpenAI quota หมด (ไม่มี credit)")
        elif "invalid_api_key" in str(e):
            print("❌ OpenAI API key ไม่ถูกต้อง")
        else:
            print(f"❌ OpenAI API Error: {e}")
        return False

async def test_trend_analysis():
    """ทดสอบการวิเคราะห์ trend ด้วย service ใหม่"""
    print("\n🔄 ทดสอบการวิเคราะห์ trend...")
    
    try:
        # ใช้ Groq Service ที่อัพเดตแล้ว
        from ai_services.text_ai.groq_service import GroqService
        
        groq = GroqService()
        
        # ข้อมูล trend ทดสอบ
        trend_data = {
            'topic': 'AI สร้างเนื้อหา 2024',
            'popularity_score': 85,
            'growth_rate': 23
        }
        
        result = await groq.analyze_trend(trend_data)
        print("✅ การวิเคราะห์ trend สำเร็จ!")
        print(f"Viral Potential: {result['scores']['viral_potential']}")
        print(f"Content Angles: {result['content_angles']}")
        return True
        
    except Exception as e:
        print(f"❌ Trend Analysis Error: {e}")
        return False

async def test_content_generation():
    """ทดสอบการสร้างเนื้อหา"""
    print("\n🔄 ทดสอบการสร้างเนื้อหา...")
    
    try:
        from ai_services.text_ai.groq_service import GroqService
        
        groq = GroqService()
        
        result = await groq.generate_content_script(
            idea="วิธีการเพิ่มผู้ติดตามใน TikTok",
            platform="tiktok"
        )
        
        print("✅ การสร้างเนื้อหาสำเร็จ!")
        print(f"Title: {result['title']}")
        print(f"Hook: {result['script']['hook']}")
        return True
        
    except Exception as e:
        print(f"❌ Content Generation Error: {e}")
        return False

async def main():
    print("🚀 เริ่มทดสอบ AI Integration (อัพเดตเวอร์ชัน)\n")
    
    # ทดสอบ API connections
    groq_ok, working_model = await test_groq_api()
    openai_ok = await test_openai_api()
    
    # ทดสอบ AI services
    trend_ok = False
    content_ok = False
    
    if groq_ok:
        trend_ok = await test_trend_analysis()
        content_ok = await test_content_generation()
    
    print("\n📊 สรุปผลการทดสอบ:")
    print(f"Groq API: {'✅' if groq_ok else '❌'}")
    if groq_ok and working_model:
        print(f"  └─ Working Model: {working_model}")
    print(f"OpenAI API: {'✅' if openai_ok else '❌'}")
    print(f"Trend Analysis: {'✅' if trend_ok else '❌'}")
    print(f"Content Generation: {'✅' if content_ok else '❌'}")
    
    if groq_ok or openai_ok:
        print("\n🎉 ระบบพร้อมใช้งาน!")
        print("\n📝 ขั้นตอนต่อไป:")
        print("1. python main.py")
        print("2. เปิดเบราว์เซอร์ไปที่: http://localhost:5000")
        print("3. กดปุ่ม 'Collect Trends'")
        print("4. ดู AI analysis ที่ได้")
        
        if groq_ok:
            print(f"\n✨ ระบบจะใช้ Groq model: {working_model}")
        
    else:
        print("\n❌ ไม่มี AI service ที่ใช้ได้")
        print("💡 แนะนำ:")
        print("- ตรวจสอบ API keys ใน .env")
        print("- ตรวจสอบ internet connection")
        print("- ลองเพิ่ม credit ใน OpenAI account")

if __name__ == "__main__":
    asyncio.run(main())