# content-engine/services/ai_director.py
from typing import Dict, List, Optional
import logging
from ..ai_services.text_ai.groq_service import GroqService
from ..models.quality_tier import QualityTier
from ..models.content_plan import ContentPlan
import json
import time

logger = logging.getLogger(__name__)

class AIDirector:
    def __init__(self, quality_tier: QualityTier = QualityTier.BUDGET):
        self.quality_tier = quality_tier
        self.groq_service = GroqService()  # ใช้ Groq แทน OpenAI
        logger.info(f"AIDirector initialized with Groq service and {quality_tier} tier")
        
    def create_content_plan(self, user_request: Dict) -> ContentPlan:
        """สร้างแผนการผลิตเนื้อหาแบบครบวงจร"""
        try:
            # Extract ข้อมูลจาก request
            topic = user_request.get('topic', '')
            platform = user_request.get('platform', 'youtube')
            content_type = user_request.get('content_type', 'educational')
            target_audience = user_request.get('target_audience', 'general')
            
            logger.info(f"Creating content plan for: {topic} on {platform}")
            
            # สร้าง master prompt สำหรับ Groq
            master_prompt = f"""
            สร้างแผนการผลิตเนื้อหาแบบครบวงจร:
            
            INPUT:
            - หัวข้อ: {topic}
            - Platform: {platform}
            - ประเภทเนื้อหา: {content_type}
            - กลุ่มเป้าหมาย: {target_audience}
            
            OUTPUT ในรูปแบบ JSON:
            {{
                "content_type": "{content_type}",
                "platform": "{platform}",
                "script": {{
                    "title": "หัวข้อที่ดึงดูดและ SEO friendly",
                    "hook": "15 วินาทีแรกที่ดึงดูดผู้ชม",
                    "main_content": {{
                        "introduction": "การเริ่มต้นที่น่าสนใจ",
                        "key_points": [
                            "จุดสำคัญที่ 1 พร้อมคำอธิบาย",
                            "จุดสำคัญที่ 2 พร้อมคำอธิบาย", 
                            "จุดสำคัญที่ 3 พร้อมคำอธิบาย"
                        ],
                        "examples": "ตัวอย่างการใช้งานจริง",
                        "benefits": "ประโยชน์ที่ผู้ชมจะได้รับ"
                    }},
                    "cta": "Call-to-action ที่ชัดเจนและดึงดูด"
                }},
                "visual_plan": {{
                    "style": "realistic/cartoon/minimalist/modern",
                    "color_scheme": "โทนสีที่เหมาะสม",
                    "scenes": [
                        "ฉากเปิด: คำอธิบายและอารมณ์",
                        "ฉากกลาง: เนื้อหาหลักและการนำเสนอ",
                        "ฉากปิด: สรุปและ CTA"
                    ],
                    "text_overlays": [
                        "ข้อความที่ 1: จุดสำคัญ",
                        "ข้อความที่ 2: สถิติหรือตัวเลข",
                        "ข้อความที่ 3: CTA"
                    ],
                    "thumbnail_concept": "ไอเดีย thumbnail ที่สะดุดตาและคลิกง่าย"
                }},
                "audio_plan": {{
                    "voice_style": "energetic/calm/professional/friendly",
                    "speaking_pace": "slow/medium/fast",
                    "background_music": "upbeat/chill/none/inspirational", 
                    "sound_effects": [
                        "เสียงที่ 1: จังหวะการใช้",
                        "เสียงที่ 2: จังหวะการใช้"
                    ]
                }},
                "platform_optimization": {{
                    "title": "หัวข้อที่ปรับสำหรับ {platform}",
                    "description": "คำอธิบาย 150-250 คำที่เหมาะสมกับ platform",
                    "hashtags": [
                        "#{platform}",
                        "#เนื้อหาหลัก",
                        "#กลุ่มเป้าหมาย",
                        "#ประเภทเนื้อหา",
                        "#เทรนด์"
                    ],
                    "best_posting_time": "เวลาที่เหมาะสมสำหรับ {platform}",
                    "engagement_tactics": "วิธีการเพิ่ม engagement"
                }},
                "production_estimate": {{
                    "preparation_time": "เวลาเตรียมงาน (นาที)",
                    "recording_time": "เวลาถ่ายทำ (นาที)",
                    "editing_time": "เวลาตัดต่อ (นาที)",
                    "total_time": "เวลารวมทั้งหมด (นาที)",
                    "cost_breakdown": {{
                        "ai_generation": "ค่าใช้จ่าย AI",
                        "production": "ค่าใช้จ่ายการผลิต",
                        "total": "รวมทั้งหมด (บาท)"
                    }},
                    "complexity": "low/medium/high",
                    "required_resources": [
                        "ทรัพยากรที่ต้องการ 1",
                        "ทรัพยากรที่ต้องการ 2"
                    ]
                }}
            }}
            
            เน้น:
            - เนื้อหาที่มีคุณค่าและเป็นประโยชน์
            - เหมาะสมกับ {platform} 
            - ดึงดูดกลุ่ม {target_audience}
            - สามารถผลิตได้จริง
            
            ตอบเป็น JSON เท่านั้น ไม่ต้องอธิบายเพิ่มเติม
            """
            
            # เรียกใช้ Groq API
            messages = [{"role": "user", "content": master_prompt}]
            response = self.groq_service._make_request(
                messages, 
                model_type="creative",  # ใช้ mixtral สำหรับความคิดสร้างสรรค์
                temperature=0.8,
                max_tokens=3000
            )
            
            # Parse JSON response
            try:
                plan_data = json.loads(response)
                content_plan = ContentPlan.from_dict(plan_data)
                content_plan.generated_at = time.strftime('%Y-%m-%d %H:%M:%S')
                content_plan.ai_model = "groq-mixtral-8x7b"
                
                logger.info(f"Content plan created successfully for {topic}")
                return content_plan
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Groq response as JSON: {e}")
                # Fallback: สร้าง basic content plan
                return self._create_fallback_plan(user_request)
                
        except Exception as e:
            logger.error(f"Error creating content plan: {e}")
            return self._create_fallback_plan(user_request)
    
    def _create_fallback_plan(self, user_request: Dict) -> ContentPlan:
        """สร้างแผน fallback เมื่อ AI service ล้มเหลว"""
        topic = user_request.get('topic', 'Unknown Topic')
        platform = user_request.get('platform', 'youtube')
        
        fallback_data = {
            "content_type": user_request.get('content_type', 'educational'),
            "platform": platform,
            "script": {
                "title": f"{topic} - ทุกสิ่งที่ควรรู้!",
                "hook": f"สวัสดีครับ! วันนี้มาพูดเรื่อง {topic} กันครับ",
                "main_content": {
                    "introduction": f"เรื่อง {topic} เป็นเรื่องที่น่าสนใจมาก",
                    "key_points": [
                        f"ประเด็นแรก: ความสำคัญของ {topic}",
                        f"ประเด็นที่สอง: วิธีการใช้ {topic}",
                        f"ประเด็นสุดท้าย: อนาคตของ {topic}"
                    ],
                    "examples": f"ตัวอย่างการใช้ {topic} ในชีวิตประจำวัน",
                    "benefits": f"ประโยชน์ที่ได้จาก {topic}"
                },
                "cta": "ถ้าชอบคลิปนี้กด Like และ Subscribe นะครับ!"
            },
            "visual_plan": {
                "style": "modern",
                "color_scheme": "สีน้ำเงินและขาว",
                "scenes": [
                    "ฉากเปิด: แนะนำหัวข้อ",
                    "ฉากกลาง: อธิบายเนื้อหา", 
                    "ฉากปิด: สรุปและ CTA"
                ],
                "text_overlays": [f"{topic}", "Key Points", "Thank You"],
                "thumbnail_concept": f"รูป {topic} พร้อมข้อความดึงดูด"
            },
            "audio_plan": {
                "voice_style": "friendly",
                "speaking_pace": "medium",
                "background_music": "chill",
                "sound_effects": ["intro sound", "transition sound"]
            },
            "platform_optimization": {
                "title": f"{topic} - Complete Guide",
                "description": f"เรียนรู้เกี่ยวกับ {topic} แบบครบถ้วน",
                "hashtags": [f"#{topic.replace(' ', '')}", f"#{platform}", "#education", "#tutorial", "#thai"],
                "best_posting_time": "18:00-21:00",
                "engagement_tactics": "ใช้คำถามและ polls"
            },
            "production_estimate": {
                "preparation_time": "30",
                "recording_time": "15", 
                "editing_time": "45",
                "total_time": "90",
                "cost_breakdown": {
                    "ai_generation": "ฟรี (Groq)",
                    "production": "0-50 บาท",
                    "total": "0-50 บาท"
                },
                "complexity": "medium",
                "required_resources": ["โทรศัพท์หรือกล้อง", "ไมค์", "แสงธรรมชาติ"]
            }
        }
        
        content_plan = ContentPlan.from_dict(fallback_data)
        content_plan.generated_at = time.strftime('%Y-%m-%d %H:%M:%S')
        content_plan.ai_model = "fallback"
        
        return content_plan
    
    def analyze_trend_opportunity(self, trend_data: Dict) -> Dict:
        """วิเคราะห์โอกาสจาก trend โดยใช้ Groq"""
        return self.groq_service.analyze_trend_potential(trend_data)
    
    def generate_content_variations(self, base_plan: ContentPlan, num_variations: int = 3) -> List[ContentPlan]:
        """สร้างเนื้อหาหลายรูปแบบจากแผนพื้นฐาน"""
        variations = []
        
        for i in range(num_variations):
            # สร้าง variation โดยเปลี่ยนมุมมอง
            variation_request = {
                'topic': base_plan.script['title'],
                'platform': base_plan.platform,
                'content_type': base_plan.content_type,
                'target_audience': f'variation_{i+1}'
            }
            
            try:
                variation = self.create_content_plan(variation_request)
                variations.append(variation)
            except Exception as e:
                logger.error(f"Failed to create variation {i+1}: {e}")
                continue
        
        return variations
    
    def get_service_status(self) -> Dict:
        """ตรวจสอบสถานะของ AI services"""
        try:
            # ทดสอบ Groq API
            test_messages = [{"role": "user", "content": "Hello, this is a test."}]
            test_response = self.groq_service._make_request(
                test_messages, 
                model_type="fast",
                max_tokens=50
            )
            
            return {
                "groq_service": "online",
                "model_available": "llama-3.1-70b-versatile",
                "last_test": time.strftime('%Y-%m-%d %H:%M:%S'),
                "quality_tier": str(self.quality_tier),
                "cost_per_request": "ฟรี (100 requests/day)",
                "response_time": "~1-3 วินาที"
            }
            
        except Exception as e:
            logger.error(f"Groq service status check failed: {e}")
            return {
                "groq_service": "offline",
                "error": str(e),
                "last_test": time.strftime('%Y-%m-%d %H:%M:%S'),
                "fallback_available": True
            }
    
    def estimate_production_cost(self, content_plan: ContentPlan) -> Dict:
        """ประมาณการค่าใช้จ่ายการผลิต"""
        base_costs = {
            "ai_generation": 0,  # Groq ฟรี
            "voice_synthesis": 0,  # ใช้ GTTS ฟรีได้
            "image_generation": 0,  # ใช้ Stable Diffusion local
            "video_editing": 0,  # ใช้ FFmpeg ฟรี
            "platform_upload": 0  # API ฟรี
        }
        
        # ค่าใช้จ่ายเพิ่มเติมตาม quality tier
        if self.quality_tier == QualityTier.BALANCED:
            base_costs["voice_synthesis"] = 10  # Azure TTS
            base_costs["image_generation"] = 20  # Leonardo AI
            
        elif self.quality_tier == QualityTier.PREMIUM:
            base_costs["voice_synthesis"] = 30  # ElevenLabs
            base_costs["image_generation"] = 50  # Midjourney
        
        total_cost = sum(base_costs.values())
        
        return {
            "breakdown": base_costs,
            "total_cost": total_cost,
            "currency": "THB",
            "tier": str(self.quality_tier),
            "cost_per_minute": total_cost / max(1, content_plan.production_estimate.get('total_time', 60) / 60)
        }