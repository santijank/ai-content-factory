# content-engine/services/script_generator.py
import json
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
import google.generativeai as genai
from ..utils.config_manager import ConfigManager

@dataclass
class ScriptComponents:
    hook: str
    introduction: str
    main_content: str
    conclusion: str
    call_to_action: str
    title_suggestions: List[str]
    hashtags: List[str]
    thumbnail_concept: str

class ScriptTemplateManager:
    """จัดการ template สำหรับแต่ละประเภทเนื้อหา"""
    
    def __init__(self):
        self.templates = {
            "tutorial": {
                "structure": "hook → problem → solution → demonstration → conclusion",
                "hook_style": "ถามคำถามหรือแสดงปัญหาที่น่าสนใจ",
                "cta_focus": "subscribe และ follow tutorial series"
            },
            "review": {
                "structure": "hook → overview → pros/cons → verdict → recommendation",
                "hook_style": "แสดงผลลัพธ์หรือความคาดหวัง",
                "cta_focus": "ขอความคิดเห็นและแนะนำสินค้าอื่น"
            },
            "entertainment": {
                "structure": "hook → setup → content → climax → reaction",
                "hook_style": "ตัวอย่างหรือ teaser ที่น่าตื่นเต้น",
                "cta_focus": "like, share และ comment"
            },
            "educational": {
                "structure": "hook → context → explanation → examples → summary",
                "hook_style": "สถิติหรือข้อเท็จจริงที่น่าประหลาดใจ",
                "cta_focus": "subscribe สำหรับเนื้อหาการศึกษาเพิ่มเติม"
            }
        }

    def get_template(self, content_type: str) -> Dict:
        return self.templates.get(content_type, self.templates["entertainment"])

class ScriptGenerator:
    """ระบบสร้าง script อัตโนมัติ"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.template_manager = ScriptTemplateManager()
        
        # ตั้งค่า Gemini API
        genai.configure(api_key=self.config.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_script(self, 
                            trend_topic: str,
                            content_angle: str,
                            content_type: str = "entertainment",
                            platform: str = "youtube",
                            duration_minutes: int = 5) -> ScriptComponents:
        """สร้าง script สมบูรณ์จาก trend และ angle"""
        
        template = self.template_manager.get_template(content_type)
        
        prompt = self._build_script_prompt(
            trend_topic, content_angle, template, platform, duration_minutes
        )
        
        try:
            response = await self._call_gemini_api(prompt)
            return self._parse_script_response(response)
        except Exception as e:
            print(f"Error generating script: {e}")
            return self._create_fallback_script(trend_topic, content_angle)

    def _build_script_prompt(self, trend_topic: str, content_angle: str, 
                           template: Dict, platform: str, duration_minutes: int) -> str:
        """สร้าง prompt สำหรับ Gemini API"""
        
        platform_specs = self._get_platform_specifications(platform)
        
        return f"""สร้าง script สำหรับวิดีโอเกี่ยวกับเทรนด์: {trend_topic}
มุมมองเนื้อหา: {content_angle}
ประเภทเนื้อหา: {template}
แพลตฟอร์ม: {platform} ({platform_specs})
ระยะเวลา: {duration_minutes} นาที

โครงสร้างที่ต้องการ:
{template['structure']}

Hook Style: {template['hook_style']}
CTA Focus: {template['cta_focus']}

กรุณาสร้างในรูปแบบ JSON:
{{
    "hook": "3-5 วินาทีแรกที่ดึงดูดความสนใจ",
    "introduction": "แนะนำหัวข้อและสร้าง context",
    "main_content": "เนื้อหาหลักแบ่งเป็นจุดๆ",
    "conclusion": "สรุปและเชื่อมต่อกับ CTA",
    "call_to_action": "เรียกร้องให้ผู้ชมทำอะไร",
    "title_suggestions": ["ชื่อเรื่อง 1", "ชื่อเรื่อง 2", "ชื่อเรื่อง 3"],
    "hashtags": ["#tag1", "#tag2", "#tag3"],
    "thumbnail_concept": "แนวคิดสำหรับ thumbnail"
}}

เขียนเป็นภาษาไทยที่เป็นธรรมชาติและเหมาะกับกลุ่มเป้าหมาย"""

    def _get_platform_specifications(self, platform: str) -> str:
        """ได้ข้อมูลเฉพาะของแต่ละแพลตฟอร์ม"""
        specs = {
            "youtube": "อัตราส่วน 16:9, เน้น retention rate, ชื่อเรื่องสำคัญมาก",
            "tiktok": "อัตราส่วน 9:16, เนื้อหาต้องดึงดูดใน 3 วินาทีแรก",
            "instagram": "รองรับทั้ง 9:16 และ 1:1, เน้น visual appeal",
            "facebook": "อัตราส่วน 16:9, เหมาะกับเนื้อหาที่ share ได้"
        }
        return specs.get(platform, specs["youtube"])

    async def _call_gemini_api(self, prompt: str) -> str:
        """เรียก Gemini API แบบ async"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

    def _parse_script_response(self, response: str) -> ScriptComponents:
        """แปลง response จาก API เป็น ScriptComponents"""
        try:
            # ลองแยก JSON จาก response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            data = json.loads(json_str)
            
            return ScriptComponents(
                hook=data.get('hook', ''),
                introduction=data.get('introduction', ''),
                main_content=data.get('main_content', ''),
                conclusion=data.get('conclusion', ''),
                call_to_action=data.get('call_to_action', ''),
                title_suggestions=data.get('title_suggestions', []),
                hashtags=data.get('hashtags', []),
                thumbnail_concept=data.get('thumbnail_concept', '')
            )
        except Exception as e:
            print(f"Error parsing script response: {e}")
            return self._create_fallback_script("", "")

    def _create_fallback_script(self, topic: str, angle: str) -> ScriptComponents:
        """สร้าง script พื้นฐานเมื่อ AI ล้มเหลว"""
        return ScriptComponents(
            hook=f"สวัสดีครับ วันนี้มาพูดเรื่อง {topic}",
            introduction=f"เรื่องนี้กำลังฮิตมากในตอนนี้ เพราะ {angle}",
            main_content="เนื้อหาหลักที่น่าสนใจ...",
            conclusion="สรุปแล้วเรื่องนี้สำคัญมาก",
            call_to_action="อย่าลืม like และ subscribe นะครับ",
            title_suggestions=[f"{topic} - สิ่งที่คุณควรรู้", f"แนวโน้ม {topic} ปี 2025"],
            hashtags=["#trending", "#content", "#viral"],
            thumbnail_concept="ใส่รูปที่เกี่ยวข้องกับหัวข้อ"
        )

class ContentStructureOptimizer:
    """ปรับปรุงโครงสร้างเนื้อหาให้เหมาะกับแต่ละแพลตฟอร์ม"""
    
    def optimize_for_platform(self, script: ScriptComponents, platform: str) -> ScriptComponents:
        """ปรับแต่ง script ให้เหมาะกับแพลตฟอร์มเฉพาะ"""
        
        if platform == "tiktok":
            return self._optimize_for_tiktok(script)
        elif platform == "youtube":
            return self._optimize_for_youtube(script)
        elif platform == "instagram":
            return self._optimize_for_instagram(script)
        else:
            return script

    def _optimize_for_tiktok(self, script: ScriptComponents) -> ScriptComponents:
        """ปรับแต่งสำหรับ TikTok - เน้นความสั้นและดึงดูด"""
        script.hook = f"⚡ {script.hook[:50]}..."
        script.main_content = script.main_content[:200] + "..."
        script.hashtags = script.hashtags[:5]  # TikTok จำกัด hashtags
        return script

    def _optimize_for_youtube(self, script: ScriptComponents) -> ScriptComponents:
        """ปรับแต่งสำหรับ YouTube - เน้น retention และ engagement"""
        script.introduction = f"ในวิดีโอนี้ผมจะพาไปดู {script.introduction}"
        script.call_to_action = f"{script.call_to_action} และกดกระดิ่งเพื่อไม่พลาดคลิปใหม่"
        return script

    def _optimize_for_instagram(self, script: ScriptComponents) -> ScriptComponents:
        """ปรับแต่งสำหรับ Instagram - เน้น visual storytelling"""
        script.hashtags = script.hashtags[:10]  # Instagram limit
        return script

# Usage Example
async def main():
    generator = ScriptGenerator()
    optimizer = ContentStructureOptimizer()
    
    # สร้าง script
    script = await generator.generate_script(
        trend_topic="AI สร้างเนื้อหา",
        content_angle="วิธีใช้ AI ทำ YouTube อัตโนมัติ",
        content_type="tutorial",
        platform="youtube",
        duration_minutes=8
    )
    
    # ปรับแต่งให้เหมาะกับแพลตฟอร์ม
    optimized_script = optimizer.optimize_for_platform(script, "youtube")
    
    print("Generated Script:")
    print(f"Hook: {optimized_script.hook}")
    print(f"Title Suggestions: {optimized_script.title_suggestions}")
    print(f"Hashtags: {optimized_script.hashtags}")

if __name__ == "__main__":
    asyncio.run(main())