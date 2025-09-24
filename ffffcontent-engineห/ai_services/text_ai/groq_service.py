# content-engine/ai_services/text_ai/groq_service.py
import os
import json
import asyncio
from groq import Groq
from .base_text_ai import BaseTextAI
from dotenv import load_dotenv

load_dotenv()

class GroqService(BaseTextAI):
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        # ใช้ model ใหม่ที่ยังใช้ได้
        self.available_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile", 
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
        self.model = self.available_models[0]  # ใช้ model แรกที่มี
    
    def test_model(self):
        """ทดสอบ model ว่าใช้ได้ไหม"""
        for model in self.available_models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hello, test message"}],
                    max_tokens=10
                )
                self.model = model
                print(f"✅ Using model: {model}")
                return True
            except Exception as e:
                print(f"❌ Model {model} failed: {e}")
                continue
        return False
    
    async def analyze_trend(self, trend_data: dict) -> dict:
        """วิเคราะห์ trend จริงด้วย Groq AI"""
        # ทดสอบ model ก่อน
        if not self.test_model():
            print("⚠️ No working models found, using fallback data")
            return self._get_fallback_analysis()
        
        prompt = f"""
วิเคราะห์ trending topic นี้สำหรับสร้างเนื้อหา:

หัวข้อ: {trend_data.get('topic', '')}
ความนิยม: {trend_data.get('popularity_score', 0)}
อัตราเติบโต: {trend_data.get('growth_rate', 0)}

ให้คะแนน 1-10 สำหรับ:
- viral_potential (ศักยภาพการแพร่กระจาย)
- content_saturation (ความอิ่มตัวของเนื้อหา) 
- audience_interest (ความสนใจของผู้ชม)
- monetization_opportunity (โอกาสการทำรายได้)

แนะนำ 3 มุมมองเนื้อหาที่ไม่ซ้ำใคร

ตอบเป็น JSON เท่านั้น:
{
    "scores": {
        "viral_potential": 8,
        "content_saturation": 3,
        "audience_interest": 9,
        "monetization_opportunity": 7
    },
    "content_angles": [
        "มุมมองที่ 1",
        "มุมมองที่ 2", 
        "มุมมองที่ 3"
    ],
    "recommended_platforms": ["youtube", "tiktok"],
    "estimated_reach": 50000
}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "คุณเป็นผู้เชี่ยวชาญวิเคราะห์เทรนด์ ตอบเป็น JSON เท่านั้น"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            # ลองแยก JSON จากข้อความ
            if '{' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                print(f"✅ Groq analysis successful with {self.model}")
                return result
            else:
                raise ValueError("No JSON found in response")
            
        except Exception as e:
            print(f"❌ Groq API Error: {e}")
            return self._get_fallback_analysis()
    
    async def generate_content_script(self, idea: str, platform: str = "youtube") -> dict:
        """สร้าง script เนื้อหาจริงด้วย Groq"""
        if not hasattr(self, 'model') or not self.model:
            if not self.test_model():
                return self._get_fallback_script(idea)
        
        prompt = f"""
สร้าง script สำหรับเนื้อหา: {idea}
Platform: {platform}

สร้าง script ที่มี:
1. Hook (3 วินาทีแรก) - ดึงดูดความสนใจ
2. เนื้อหาหลัก - ข้อมูลที่มีประโยชน์
3. Call-to-action - เรียกไปยังการกระทำ

ตอบเป็น JSON เท่านั้น:
{
    "title": "หัวข้อที่ดึงดูด",
    "description": "คำอธิบายสั้น",
    "script": {
        "hook": "3 วินาทีแรก",
        "main_content": "เนื้อหาหลัก",
        "cta": "call to action"
    },
    "hashtags": ["#tag1", "#tag2"],
    "estimated_duration": "60 วินาที"
}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "คุณเป็นนักเขียน script มืออาชีพ ตอบเป็น JSON เท่านั้น"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            if '{' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                print(f"✅ Script generated with {self.model}")
                return result
            else:
                raise ValueError("No JSON in response")
            
        except Exception as e:
            print(f"❌ Groq Script Error: {e}")
            return self._get_fallback_script(idea)
    
    def _get_fallback_analysis(self):
        """ข้อมูล fallback เมื่อ AI ไม่ทำงาน"""
        return {
            "scores": {
                "viral_potential": 6, 
                "content_saturation": 4, 
                "audience_interest": 7, 
                "monetization_opportunity": 6
            },
            "content_angles": [
                "มุมมองที่น่าสนใจ", 
                "วิธีการใหม่ๆ", 
                "เคล็ดลับที่ไม่เคยรู้"
            ],
            "recommended_platforms": ["youtube", "tiktok"],
            "estimated_reach": 15000
        }
    
    def _get_fallback_script(self, idea):
        """Script fallback"""
        return {
            "title": f"เนื้อหาเกี่ยวกับ {idea}",
            "description": "เนื้อหาที่น่าสนใจและมีประโยชน์",
            "script": {
                "hook": "สวัสดีครับ! วันนี้เรามาเรียนรู้เรื่องที่น่าสนใจกัน",
                "main_content": f"เรื่อง {idea} นั้นสำคัญมากเพราะ...",
                "cta": "ถ้าชอบก็กด Like และ Subscribe นะครับ"
            },
            "hashtags": ["#content", "#viral", "#educational"],
            "estimated_duration": "2-3 นาที"
        }

# ทดสอบ models ที่ใช้ได้
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🔍 ตรวจสอบ Groq models...")
    available_models = check_available_models()
    
    if available_models:
        print(f"✅ พบ {len(available_models)} models")
        
        # ทดสอบ service
        service = GroqService()
        if service.test_model():
            print(f"🎉 Groq service พร้อมใช้งานด้วย model: {service.model}")
        else:
            print("❌ ไม่มี model ที่ใช้ได้")
    else:
        print("❌ ไม่สามารถเชื่อมต่อ Groq ได้")
