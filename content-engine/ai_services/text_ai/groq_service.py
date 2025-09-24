# content-engine/ai_services/text_ai/groq_service.py - Fixed JSON handling
import requests
import json
import time
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "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"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.models = {
            "fast": "llama-3.1-8b-instant",
            "balanced": "llama-3.1-70b-versatile", 
            "creative": "mixtral-8x7b-32768"
        }
        
    def _make_request(self, messages: List[Dict], model_type: str = "balanced", 
                     temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """ส่ง request ไป Groq API"""
        try:
            payload = {
                "model": self.models[model_type],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 1,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """แยก JSON ออกจาก response ที่อาจมีข้อความอื่นปนมา"""
        try:
            # ลองแปลง response ทั้งหมดเป็น JSON ก่อน
            return json.loads(response)
        except json.JSONDecodeError:
            # ถ้าไม่ได้ ให้หา JSON block ใน response
            json_matches = re.findall(r'\{.*\}', response, re.DOTALL)
            
            for match in json_matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            # ถ้าหาไม่เจอ ให้หา JSON ที่อยู่ระหว่าง ```json และ ```
            code_block_matches = re.findall(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            for match in code_block_matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            # ถ้าหาไม่เจอเลย ให้สร้าง JSON จาก text
            return self._create_json_from_text(response)
    
    def _create_json_from_text(self, text: str) -> Dict:
        """สร้าง JSON structure จาก plain text response"""
        lines = text.split('\n')
        
        # หาหัวข้อจากบรรทัดแรกที่ไม่ใช่ช่องว่าง
        title = ""
        for line in lines:
            if line.strip():
                title = line.strip()
                break
        
        if not title:
            title = "เนื้อหาที่สร้างด้วย AI"
            
        return {
            "title": title,
            "description": text[:200] + "..." if len(text) > 200 else text,
            "script": {
                "hook": "เนื้อหาน่าสนใจที่จะทำให้คุณหยุดเลื่อน!",
                "main_content": text,
                "cta": "ถ้าชอบเนื้อหานี้ อย่าลืม Like และ Subscribe นะครับ!"
            },
            "hashtags": ["#content", "#ai", "#trending", "#educational", "#thai"],
            "platform": "youtube",
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "model_used": "groq-fallback"
        }
    
    def generate_content_script(self, opportunity_data: Dict) -> Dict:
        """สร้าง script เนื้อหาจาก opportunity"""
        trend_topic = opportunity_data.get('topic', '')
        content_angle = opportunity_data.get('suggested_angle', '')
        platform = opportunity_data.get('platform', 'youtube')
        
        # Simplified prompt ที่มุ่งเน้น JSON output
        prompt = f"""
คุณคือ AI ที่เชี่ยวชาญการสร้าง content script สำหรับ {platform}

หัวข้อ: {trend_topic}
มุมมอง: {content_angle}

สร้าง JSON ในรูปแบบนี้เท่านั้น (ห้ามมีข้อความอื่น):

{{
    "title": "หัวข้อที่ดึงดูดสำหรับ {platform}",
    "description": "คำอธิบาย 150 คำ",
    "script": {{
        "hook": "15 วินาทีแรกที่ดึงดูด",
        "main_content": "เนื้อหาหลัก 3-4 ประเด็น",
        "cta": "Call to action"
    }},
    "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
    "platform": "{platform}",
    "estimated_duration": "3-5 นาที"
}}

ตอบเป็น JSON เท่านั้น:
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self._make_request(messages, model_type="balanced", temperature=0.7)
            
            # แยก JSON จาก response
            result = self._extract_json_from_response(response)
            
            # เพิ่ม metadata
            result['generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            result['model_used'] = self.models["balanced"]
            result['trend_topic'] = trend_topic
            
            logger.info(f"✅ Generated content script for: {trend_topic}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Content generation failed for {trend_topic}: {e}")
            
            # Fallback: สร้าง content พื้นฐาน
            return {
                "title": f"{trend_topic} - ทุกสิ่งที่ควรรู้!",
                "description": f"มาเรียนรู้เรื่อง {trend_topic} กันครับ! ในเนื้อหานี้จะพาไปดูรายละเอียดที่น่าสนใจและเป็นประโยชน์",
                "script": {
                    "hook": f"หยุดเลื่อนก่อน! เรื่อง {trend_topic} นี้กำลังฮิตมากตอนนี้",
                    "main_content": f"วันนี้เราจะมาดูเรื่อง {trend_topic} กันครับ ซึ่งเป็นเรื่องที่กำลังเป็นที่สนใจของหลายคน เราจะมาดูว่ามันคืออะไร ทำไมถึงได้รับความสนใจ และเราจะนำไปใช้ประโยชน์ได้อย่างไร",
                    "cta": "ถ้าชอบเนื้อหานี้ กด Like Subscribe และแชร์ให้เพื่อนๆ ด้วยนะครับ!"
                },
                "hashtags": ["#" + trend_topic.replace(" ", ""), "#trending", "#content", "#education", "#thai"],
                "platform": platform,
                "estimated_duration": "3-5 นาที",
                "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "model_used": "fallback",
                "trend_topic": trend_topic,
                "note": "This is a fallback response due to API error"
            }
    
    def analyze_trend_potential(self, trend_data: Dict) -> Dict:
        """วิเคราะห์ความน่าสนใจของ trend - Simplified version"""
        try:
            prompt = f"""
วิเคราะห์ trend นี้และตอบเป็น JSON เท่านั้น:

หัวข้อ: {trend_data.get('topic', 'Unknown')}
ความนิยม: {trend_data.get('popularity_score', 5)}/10

JSON:
{{
    "viral_potential": 8,
    "content_saturation": 5,
    "audience_interest": 7,
    "monetization_opportunity": 6,
    "overall_score": 7,
    "recommendation": "ควรสร้างเนื้อหาโดยเร็ว"
}}
"""
            
            messages = [{"role": "user", "content": prompt}]
            response = self._make_request(messages, model_type="fast", temperature=0.3)
            
            result = self._extract_json_from_response(response)
            
            # ตรวจสอบว่ามี field ที่จำเป็นหรือไม่
            required_fields = ['viral_potential', 'content_saturation', 'audience_interest', 'monetization_opportunity', 'overall_score']
            for field in required_fields:
                if field not in result:
                    result[field] = 6  # default value
                    
            return result
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            # Fallback analysis
            return {
                "viral_potential": 7,
                "content_saturation": 5,
                "audience_interest": 8,
                "monetization_opportunity": 6,
                "content_angles": [
                    f"คู่มือเบื้องต้นเรื่อง {trend_data.get('topic', '')}",
                    f"เทคนิคและเคล็ดลับ {trend_data.get('topic', '')}",
                    f"อนาคตและแนวโน้มของ {trend_data.get('topic', '')}"
                ],
                "target_platforms": ["youtube", "tiktok"],
                "best_timing": "24-48 ชั่วโมง",
                "overall_score": 7,
                "recommendation": "ควรสร้างเนื้อหาโดยเร็ว",
                "analysis_method": "fallback"
            }

    def test_connection(self) -> Dict:
        """ทดสอบการเชื่อมต่อกับ Groq API"""
        try:
            test_messages = [{"role": "user", "content": "สวัสดี ทดสอบ API"}]
            response = self._make_request(test_messages, model_type="fast", max_tokens=50)
            
            return {
                "success": True,
                "response": response,
                "model": self.models["fast"],
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }