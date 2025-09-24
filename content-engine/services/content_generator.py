"""
Content Generator
Core logic สำหรับการสร้างเนื้อหาแต่ละประเภทด้วย AI Services
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import re
from pathlib import Path

from shared.models.content_plan import ContentPlan
from shared.models.content_opportunity import ContentOpportunity
from shared.models.quality_tier import QualityTier
from services.service_registry import ServiceRegistry
from shared.utils.logger import get_logger
from shared.utils.error_handler import handle_errors, ContentGenerationError
from shared.constants.ai_prompts import PromptTemplates


@dataclass
class GenerationRequest:
    """คำขอสร้างเนื้อหา"""
    content_type: str  # "script", "title", "description", "hashtags", "thumbnail_concept"
    context: Dict[str, Any]  # ข้อมูลบริบท
    quality_tier: QualityTier
    platform: Optional[str] = None
    style_preferences: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResult:
    """ผลลัพธ์การสร้างเนื้อหา"""
    content_type: str
    generated_content: Any
    quality_score: float  # 0-10
    generation_time: float  # seconds
    ai_service_used: str
    cost_estimate: float  # บาท
    metadata: Dict[str, Any]
    created_at: datetime


class ContentGenerator:
    """
    Core engine สำหรับการสร้างเนื้อหาด้วย AI Services
    """
    
    def __init__(self, quality_tier: QualityTier = QualityTier.BUDGET):
        self.quality_tier = quality_tier
        self.logger = get_logger(__name__)
        self.service_registry = ServiceRegistry()
        self.prompt_templates = PromptTemplates()
        
        # Generation settings
        self.generation_settings = self._load_generation_settings()
        
        # Quality control
        self.quality_thresholds = self._load_quality_thresholds()
        
        # Content templates
        self.content_templates = self._load_content_templates()
        
        # Statistics
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_cost": 0.0,
            "average_quality": 0.0
        }

    def _load_generation_settings(self) -> Dict:
        """โหลดการตั้งค่าการสร้างเนื้อหา"""
        return {
            "script": {
                "max_retries": 3,
                "min_word_count": 50,
                "max_word_count": 2000,
                "required_sections": ["hook", "main_content", "cta"],
                "quality_checks": ["readability", "engagement", "structure"]
            },
            "title": {
                "max_retries": 2,
                "min_length": 10,
                "max_length": 100,
                "variations_count": 5,
                "seo_requirements": ["keyword_inclusion", "length_optimization"]
            },
            "description": {
                "max_retries": 2,
                "min_length": 50,
                "max_length": 500,
                "platform_specific": True,
                "include_keywords": True
            },
            "hashtags": {
                "max_retries": 1,
                "min_count": 5,
                "max_count": 30,
                "trending_weight": 0.4,
                "relevance_weight": 0.6
            },
            "thumbnail_concept": {
                "max_retries": 2,
                "style_consistency": True,
                "platform_optimization": True,
                "color_psychology": True
            }
        }

    def _load_quality_thresholds(self) -> Dict:
        """โหลดเกณฑ์คุณภาพ"""
        return {
            QualityTier.BUDGET: {
                "min_quality_score": 6.0,
                "max_generation_time": 30.0,
                "retry_threshold": 5.0
            },
            QualityTier.BALANCED: {
                "min_quality_score": 7.5,
                "max_generation_time": 60.0,
                "retry_threshold": 6.5
            },
            QualityTier.PREMIUM: {
                "min_quality_score": 8.5,
                "max_generation_time": 120.0,
                "retry_threshold": 7.5
            }
        }

    def _load_content_templates(self) -> Dict:
        """โหลด template เนื้อหา"""
        return {
            "thai_content_patterns": {
                "formal": {
                    "greeting": ["สวัสดีครับ", "สวัสดีค่ะ", "ยินดีต้อนรับ"],
                    "transition": ["ต่อไป", "ในขั้นตอนนี้", "สำหรับส่วนถัดไป"],
                    "conclusion": ["สรุปแล้ว", "ในที่สุด", "โดยรวมแล้ว"]
                },
                "casual": {
                    "greeting": ["ว่าไงครับ", "ฮาโหลทุกคน", "พบกันอีกแล้ว"],
                    "transition": ["แล้วนะ", "ต่อไปเลย", "มาดูกันต่อ"],
                    "conclusion": ["ก็ประมาณนี้แหละ", "เท่านี้ก่อน", "จบแล้วครับ"]
                },
                "energetic": {
                    "greeting": ["ไฮทุกคน!", "เฮ้ยยย!", "มาแล้วว!"],
                    "transition": ["ไปเลย!", "ต่อกันเลย!", "มาดูกัน!"],
                    "conclusion": ["เจ๋งมาก!", "สุดยอด!", "เยี่ยมเลย!"]
                }
            },
            "content_structures": {
                "educational": [
                    "introduction → problem → solution → example → conclusion",
                    "hook → background → main_points → practical_tips → summary"
                ],
                "entertainment": [
                    "hook → buildup → climax → reaction → call_to_action",
                    "surprise → explanation → demonstration → audience_engagement"
                ],
                "tutorial": [
                    "overview → requirements → step_by_step → troubleshooting → results",
                    "goal → preparation → process → verification → next_steps"
                ],
                "news": [
                    "breaking → background → analysis → implications → conclusion",
                    "headline → facts → context → expert_opinion → audience_impact"
                ]
            }
        }

    # Core generation methods

    async def generate_script(self, opportunity: ContentOpportunity, 
                            content_plan: ContentPlan) -> GenerationResult:
        """สร้าง script สำหรับเนื้อหา"""
        
        request = GenerationRequest(
            content_type="script",
            context={
                "opportunity": opportunity,
                "content_plan": content_plan,
                "target_audience": opportunity.content_idea.target_audience,
                "content_type": opportunity.content_idea.content_type,
                "duration": opportunity.content_idea.estimated_duration
            },
            quality_tier=self.quality_tier
        )
        
        return await self._generate_with_quality_control(request, self._generate_script_internal)

    async def _generate_script_internal(self, request: GenerationRequest) -> Dict[str, str]:
        """สร้าง script แบบละเอียด"""
        
        opportunity = request.context["opportunity"]
        content_plan = request.context["content_plan"]
        
        # เลือก AI service
        text_ai = self.service_registry.get_service("text_ai", request.quality_tier)
        
        # สร้าง prompt
        prompt = self._build_script_prompt(opportunity, content_plan, request)
        
        # Generate script
        response = await text_ai.generate_content(prompt)
        
        # Parse และ validate
        script = self._parse_script_response(response)
        script = await self._enhance_script_quality(script, request)
        
        return script

    def _build_script_prompt(self, opportunity: ContentOpportunity, 
                           content_plan: ContentPlan, request: GenerationRequest) -> str:
        """สร้าง prompt สำหรับ script generation"""
        
        settings = self.generation_settings["script"]
        content_type = opportunity.content_idea.content_type
        
        # เลือก style pattern
        style_patterns = self.content_templates["thai_content_patterns"]
        
        if "formal" in content_plan.style.lower():
            patterns = style_patterns["formal"]
        elif "casual" in content_plan.style.lower():
            patterns = style_patterns["casual"]
        else:
            patterns = style_patterns["energetic"]
        
        # เลือก structure
        structures = self.content_templates["content_structures"][content_type]
        structure = structures[0]  # ใช้ structure แรก
        
        prompt = f"""
สร้าง script สำหรับวิดีโอตามข้อมูลต่อไปนี้:

== ข้อมูลพื้นฐาน ==
หัวข้อ: {opportunity.content_idea.title}
ประเภท: {content_type}
กลุ่มเป้าหมาย: {opportunity.content_idea.target_audience}
ระยะเวลา: {opportunity.content_idea.estimated_duration} วินาที
Trend: {opportunity.trend_data.topic}

== รูปแบบเนื้อหา ==
Structure: {structure}
Style: {content_plan.style}
Tone: {patterns}

== เป้าหมาย ==
- สร้างความน่าสนใจตั้งแต่วินาทีแรก
- ให้ข้อมูลที่มีประโยชน์
- เหมาะสมกับกลุ่มเป้าหมาย
- มี call-to-action ที่ชัดเจน

กรุณาสร้าง script ในรูปแบบ JSON:
{{
  "hook": "ประโยคเปิดที่ดึงดูดใจ (3-5 วินาทีแรก)",
  "main_content": "เนื้อหาหลักที่ครอบคลุมประเด็นสำคัญ",
  "cta": "call-to-action ที่เหมาะสม",
  "transitions": ["ประโยคเชื่อมระหว่างส่วน"],
  "key_points": ["จุดสำคัญที่ต้องเน้น"],
  "emotional_hooks": ["จุดที่ต้องสร้างอารมณ์"]
}}

ข้อกำหนดเพิ่มเติม:
- ใช้ภาษาไทยที่เหมาะสมกับกลุ่มเป้าหมาย
- จำนวนคำรวม: {settings['min_word_count']}-{settings['max_word_count']} คำ
- หลีกเลี่ยงเนื้อหาที่อาจทำให้เกิดความขัดแย้ง
- เน้นความเป็นไทยและวัฒนธรรมท้องถิ่น
"""
        
        return prompt.strip()

    def _parse_script_response(self, response: str) -> Dict[str, str]:
        """แยกวิเคราะห์ response จาก AI"""
        
        try:
            # ลองแปลงเป็น JSON ก่อน
            if response.strip().startswith('{'):
                script = json.loads(response)
            else:
                # แยกแบบ manual
                script = self._manual_parse_script(response)
            
            # ตรวจสอบ required fields
            required = ["hook", "main_content", "cta"]
            for field in required:
                if field not in script or not script[field]:
                    script[field] = self._generate_fallback_content(field)
            
            return script
            
        except Exception as e:
            self.logger.warning(f"Failed to parse script response: {e}")
            return self._create_fallback_script()

    def _manual_parse_script(self, response: str) -> Dict[str, str]:
        """แยกวิเคราะห์ script แบบ manual"""
        
        script = {}
        
        # หา patterns ต่างๆ
        patterns = {
            "hook": r"hook[\"']?\s*:?\s*[\"']([^\"']+)[\"']?",
            "main_content": r"main[_\s]?content[\"']?\s*:?\s*[\"']([^\"']+)[\"']?",
            "cta": r"cta[\"']?\s*:?\s*[\"']([^\"']+)[\"']?"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                script[key] = match.group(1).strip()
        
        # ถ้าไม่เจอ pattern ให้แยกตาม line
        if not script:
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if any(word in line.lower() for word in ['hook', 'เปิด', 'เริ่ม']):
                    current_section = 'hook'
                    script[current_section] = line.split(':', 1)[-1].strip()
                elif any(word in line.lower() for word in ['main', 'เนื้อหา', 'หลัก']):
                    current_section = 'main_content'
                    script[current_section] = line.split(':', 1)[-1].strip()
                elif any(word in line.lower() for word in ['cta', 'ปิด', 'เชิญ']):
                    current_section = 'cta'
                    script[current_section] = line.split(':', 1)[-1].strip()
                elif line and current_section:
                    script[current_section] += ' ' + line
        
        return script

    def _generate_fallback_content(self, field: str) -> str:
        """สร้างเนื้อหาสำรองสำหรับ field ที่ขาดหาย"""
        
        fallbacks = {
            "hook": "สวัสดีครับทุกคน! วันนี้มีเรื่องน่าสนใจมาแชร์",
            "main_content": "เนื้อหาหลักที่จะให้ความรู้และความบันเทิงแก่ผู้ชม",
            "cta": "กดไลค์และติดตามถ้าชอบเนื้อหานะครับ"
        }
        
        return fallbacks.get(field, f"[Missing {field}]")

    def _create_fallback_script(self) -> Dict[str, str]:
        """สร้าง script สำรองเมื่อ AI ล้มเหลว"""
        
        return {
            "hook": "สวัสดีครับทุกคน! วันนี้มีเรื่องน่าสนใจมาแชร์",
            "main_content": "เนื้อหาหลักที่จะให้ความรู้และความบันเทิงแก่ผู้ชม โดยจะครอบคลุมประเด็นสำคัญและให้ข้อมูลที่เป็นประโยชน์",
            "cta": "กดไลค์และติดตามถ้าชอบเนื้อหานะครับ",
            "transitions": ["ต่อไป", "ในส่วนนี้", "สุดท้าย"],
            "key_points": ["จุดสำคัญ", "ข้อมูลหลัก", "สิ่งที่ควรรู้"],
            "emotional_hooks": ["น่าสนใจ", "ประทับใจ", "น่าติดตาม"]
        }

    async def _enhance_script_quality(self, script: Dict[str, str], 
                                    request: GenerationRequest) -> Dict[str, str]:
        """ปรับปรุงคุณภาพ script"""
        
        settings = self.generation_settings["script"]
        
        # ตรวจสอบความยาว
        script = self._adjust_script_length(script, settings)
        
        # ปรับปรุงการใช้ภาษา
        script = await self._improve_language_quality(script, request)
        
        # เพิ่ม emotional elements
        script = self._add_emotional_elements(script, request)
        
        # ตรวจสอบ SEO และ keyword
        script = self._optimize_for_keywords(script, request)
        
        return script

    def _adjust_script_length(self, script: Dict[str, str], settings: Dict) -> Dict[str, str]:
        """ปรับความยาว script ให้เหมาะสม"""
        
        total_words = sum(len(text.split()) for text in script.values() if isinstance(text, str))
        
        if total_words < settings["min_word_count"]:
            # ขยายเนื้อหา
            script["main_content"] += " นอกจากนี้ยังมีรายละเอียดเพิ่มเติมที่น่าสนใจ และข้อมูลที่เป็นประโยชน์สำหรับผู้ชม"
        elif total_words > settings["max_word_count"]:
            # ตัดเนื้อหา
            words = script["main_content"].split()
            max_main_words = settings["max_word_count"] - len(script["hook"].split()) - len(script["cta"].split())
            script["main_content"] = " ".join(words[:max_main_words])
        
        return script

    async def _improve_language_quality(self, script: Dict[str, str], 
                                      request: GenerationRequest) -> Dict[str, str]:
        """ปรับปรุงคุณภาพการใช้ภาษา"""
        
        # ตรวจสอบและแก้ไขไวยากรณ์พื้นฐาน
        for key, text in script.items():
            if isinstance(text, str):
                # แก้ไขเครื่องหมายวรรคตอน
                text = re.sub(r'\s+', ' ', text)  # ลบ space เกิน
                text = re.sub(r'([.!?])\s*([a-zA-Zก-ฮ])', r'\1 \2', text)  # เพิ่ม space หลังจุด
                text = text.strip()
                
                script[key] = text
        
        return script

    def _add_emotional_elements(self, script: Dict[str, str], 
                              request: GenerationRequest) -> Dict[str, str]:
        """เพิ่มองค์ประกอบทางอารมณ์"""
        
        content_type = request.context.get("content_type", "educational")
        
        emotional_enhancers = {
            "educational": ["น่าสนใจมาก", "เรียนรู้ได้จริง", "ประโยชน์แน่นอน"],
            "entertainment": ["สนุกมาก", "ฮาสุดๆ", "แจ่มเลย"],
            "tutorial": ["ง่ายมาก", "ทำตามได้แน่นอน", "เข้าใจง่าย"],
            "news": ["น่าติดตาม", "อัพเดทใหม่", "ข้อมูลสำคัญ"]
        }
        
        enhancers = emotional_enhancers.get(content_type, emotional_enhancers["educational"])
        
        # เพิ่มใน hook
        if not any(word in script["hook"] for word in enhancers):
            script["hook"] += f" {enhancers[0]}!"
        
        return script

    def _optimize_for_keywords(self, script: Dict[str, str], 
                             request: GenerationRequest) -> Dict[str, str]:
        """ปรับปรุงสำหรับ SEO และ keywords"""
        
        opportunity = request.context.get("opportunity")
        if not opportunity:
            return script
        
        keywords = opportunity.trend_data.keywords
        topic = opportunity.trend_data.topic
        
        # ตรวจสอบว่ามี keywords ในเนื้อหาหรือไม่
        main_content = script["main_content"].lower()
        
        for keyword in keywords:
            if keyword.lower() not in main_content:
                # เพิ่ม keyword อย่างธรรมชาติ
                script["main_content"] += f" เกี่ยวกับ{keyword}นี้มีรายละเอียดที่น่าสนใจ"
        
        # เพิ่ม topic ใน hook หากยังไม่มี
        if topic.lower() not in script["hook"].lower():
            script["hook"] = f"เรื่อง{topic}! " + script["hook"]
        
        return script

    # Title generation

    async def generate_titles(self, opportunity: ContentOpportunity, 
                            count: int = 5) -> GenerationResult:
        """สร้าง titles หลายตัวเลือก"""
        
        request = GenerationRequest(
            content_type="title",
            context={
                "opportunity": opportunity,
                "variations_count": count,
                "seo_focus": True
            },
            quality_tier=self.quality_tier
        )
        
        return await self._generate_with_quality_control(request, self._generate_titles_internal)

    async def _generate_titles_internal(self, request: GenerationRequest) -> List[str]:
        """สร้าง titles แบบละเอียด"""
        
        opportunity = request.context["opportunity"]
        count = request.context.get("variations_count", 5)
        
        text_ai = self.service_registry.get_service("text_ai", request.quality_tier)
        
        prompt = self._build_title_prompt(opportunity, count)
        response = await text_ai.generate_content(prompt)
        
        titles = self._parse_titles_response(response)
        titles = self._optimize_titles(titles, opportunity)
        
        return titles[:count]

    def _build_title_prompt(self, opportunity: ContentOpportunity, count: int) -> str:
        """สร้าง prompt สำหรับ title generation"""
        
        prompt = f"""
สร้าง {count} titles ที่แตกต่างกันสำหรับเนื้อหาต่อไปนี้:

หัวข้อเดิม: {opportunity.content_idea.title}
ประเภท: {opportunity.content_idea.content_type}
Trend: {opportunity.trend_data.topic}
Keywords: {', '.join(opportunity.trend_data.keywords)}
กลุ่มเป้าหมาย: {opportunity.content_idea.target_audience}

สร้าง titles ที่:
1. ดึงดูดความสนใจและคลิก
2. มี SEO ที่ดี (รวม keywords)
3. เหมาะสมกับกลุ่มเป้าหมาย
4. ไม่เกิน 100 ตัวอักษร
5. ใช้ภาษาไทยที่เข้าใจง่าย

ตัวอย่างรูปแบบที่ดี:
- "วิธี [ทำสิ่งใด] ง่ายๆ ที่บ้าน"
- "[เรื่องใด] ที่คุณไม่เคยรู้"
- "เปิดเผย [ความลับ] ของ [เรื่องใด]"
- "[จำนวน] วิธี [ทำสิ่งใด] แบบโปร"

กรุณาตอบเป็น JSON array:
["title 1", "title 2", "title 3", ...]
"""
        
        return prompt.strip()

    def _parse_titles_response(self, response: str) -> List[str]:
        """แยกวิเคราะห์ response ของ titles"""
        
        try:
            if response.strip().startswith('['):
                titles = json.loads(response)
            else:
                # แยกแบบ manual
                lines = response.split('\n')
                titles = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(('#', '//', '/*')):
                        # ลบหมายเลข และ quote
                        title = re.sub(r'^\d+[\.\)]\s*', '', line)
                        title = title.strip('"\'')
                        if title:
                            titles.append(title)
            
            return titles if titles else self._create_fallback_titles()
            
        except Exception as e:
            self.logger.warning(f"Failed to parse titles response: {e}")
            return self._create_fallback_titles()

    def _create_fallback_titles(self) -> List[str]:
        """สร้าง titles สำรอง"""
        
        return [
            "เนื้อหาน่าสนใจที่คุณไม่ควรพลาด",
            "ข้อมูลใหม่ที่จะเปลี่ยนมุมมองของคุณ",
            "วิธีง่ายๆ ที่ทุกคนทำได้",
            "เรื่องจริงที่คุณอาจไม่เคยรู้",
            "เทคนิคเด็ดที่มืออาชีพใช้"
        ]

    def _optimize_titles(self, titles: List[str], opportunity: ContentOpportunity) -> List[str]:
        """ปรับปรุง titles ให้ดีขึ้น"""
        
        optimized = []
        keywords = opportunity.trend_data.keywords
        
        for title in titles:
            # ตรวจสอบความยาว
            if len(title) > 100:
                title = title[:97] + "..."
            elif len(title) < 10:
                title += " ที่คุณควรรู้"
            
            # เพิ่ม keywords หากยังไม่มี
            title_lower = title.lower()
            for keyword in keywords:
                if keyword.lower() not in title_lower:
                    # พยายามเพิ่ม keyword อย่างธรรมชาติ
                    if len(title) + len(keyword) < 95:
                        title = f"{keyword}: {title}"
                    break
            
            optimized.append(title)
        
        return optimized

    # Description generation

    async def generate_descriptions(self, opportunity: ContentOpportunity,
                                  platforms: List[str] = None) -> GenerationResult:
        """สร้าง descriptions สำหรับหลาย platforms"""
        
        request = GenerationRequest(
            content_type="description",
            context={
                "opportunity": opportunity,
                "platforms": platforms or ["youtube", "tiktok"],
                "include_seo": True
            },
            quality_tier=self.quality_tier
        )
        
        return await self._generate_with_quality_control(request, self._generate_descriptions_internal)

    async def _generate_descriptions_internal(self, request: GenerationRequest) -> Dict[str, str]:
        """สร้าง descriptions แบบละเอียด"""
        
        opportunity = request.context["opportunity"]
        platforms = request.context.get("platforms", ["youtube"])
        
        text_ai = self.service_registry.get_service("text_ai", request.quality_tier)
        
        descriptions = {}
        
        for platform in platforms:
            prompt = self._build_description_prompt(opportunity, platform)
            response = await text_ai.generate_content(prompt)
            
            description = self._parse_description_response(response, platform)
            description = self._optimize_description(description, platform, opportunity)
            
            descriptions[platform] = description
        
        return descriptions

    def _build_description_prompt(self, opportunity: ContentOpportunity, platform: str) -> str:
        """สร้าง prompt สำหรับ description"""
        
        platform_specs = {
            "youtube": {"max_length": 5000, "style": "detailed, SEO-friendly"},
            "tiktok": {"max_length": 300, "style": "short, catchy"},
            "instagram": {"max_length": 2200, "style": "engaging, hashtag-rich"},
            "facebook": {"max_length": 2000, "style": "conversational, shareable"}
        }
        
        spec = platform_specs.get(platform, platform_specs["youtube"])
        
        prompt = f"""
สร้าง description สำหรับ {platform.upper()} ตามข้อมูลต่อไปนี้:

หัวข้อ: {opportunity.content_idea.title}
ประเภท: {opportunity.content_idea.content_type}
Trend: {opportunity.trend_data.topic}
Keywords: {', '.join(opportunity.trend_data.keywords)}
กลุ่มเป้าหมาย: {opportunity.content_idea.target_audience}

ข้อกำหนดสำหรับ {platform}:
- ความยาวไม่เกิน {spec['max_length']} ตัวอักษร
- สไตล์: {spec['style']}
- รวม keywords ที่เกี่ยวข้อง
- เหมาะสมกับการค้นหา (SEO)
- มี call-to-action ที่เหมาะสม

เนื้อหาควรประกอบด้วย:
1. สรุปเนื้อหาที่น่าสนใจ
2. ประโยชน์ที่ผู้ชมจะได้รับ
3. เชิญชวนให้ engagement (like, share, comment)
4. Hashtags ที่เกี่ยวข้อง (สำหรับ social media)

ตัวอย่างรูปแบบ:
{self._get_description_template(platform)}

กรุณาสร้าง description ที่สมบูรณ์:
"""
        
        return prompt.strip()

    def _get_description_template(self, platform: str) -> str:
        """ได้ template สำหรับ description แต่ละ platform"""
        
        templates = {
            "youtube": """
🎯 ในวิดีโอนี้เราจะพาคุณมาเรียนรู้เกี่ยวกับ [หัวข้อ]

📍 สิ่งที่คุณจะได้เรียนรู้:
• [จุดสำคัญ 1]
• [จุดสำคัญ 2]
• [จุดสำคัญ 3]

🔔 กดกระดิ่งเพื่อไม่พลาดคลิปใหม่
👍 กดไลค์ถ้าชอบ
💬 คอมเมนต์บอกความคิดเห็น

#แฮชแท็ก #ที่เกี่ยวข้อง
""",
            "tiktok": """
[อีโมจิ] [สรุปสั้นๆ ที่ดึงดูด]

✨ [ประโยชน์หลัก]
💫 [ข้อมูลน่าสนใจ]

Follow สำหรับเนื้อหาดีๆ ทุกวัน! 

#fyp #viral #แฮชแท็ก
""",
            "instagram": """
[อีโมจิ] [Hook ที่น่าสนใจ]

[เนื้อหาหลักที่มีประโยชน์]

💝 Save ไว้ดูภึกได้
📱 Share ให้เพื่อนๆ
💭 คอมเมนต์บอกความคิดเห็น

#แฮชแท็ก #instagram #content
""",
            "facebook": """
[ประโยคเปิดที่น่าสนใจ]

[เนื้อหาหลักที่มีรายละเอียด]

👥 แชร์ให้เพื่อนๆ ดูกันด้วย
❤️ กดไลค์ถ้าเห็นด้วย
💬 คอมเมนต์แบ่งปันประสบการณ์
"""
        }
        
        return templates.get(platform, templates["youtube"])

    def _parse_description_response(self, response: str, platform: str) -> str:
        """แยกวิเคราะห์ response ของ description"""
        
        # ลบ markdown และ formatting ที่ไม่จำเป็น
        description = response.strip()
        
        # ลบ code blocks
        description = re.sub(r'```[\s\S]*?```', '', description)
        description = re.sub(r'`([^`]+)`', r'\1', description)
        
        # ลบ headers ที่ไม่จำเป็น
        description = re.sub(r'^#+\s*', '', description, flags=re.MULTILINE)
        
        # ทำความสะอาด
        description = re.sub(r'\n{3,}', '\n\n', description)
        description = description.strip()
        
        return description

    def _optimize_description(self, description: str, platform: str, 
                            opportunity: ContentOpportunity) -> str:
        """ปรับปรุง description ให้เหมาะสม"""
        
        platform_specs = {
            "youtube": {"max_length": 5000},
            "tiktok": {"max_length": 300},
            "instagram": {"max_length": 2200},
            "facebook": {"max_length": 2000}
        }
        
        max_length = platform_specs.get(platform, {}).get("max_length", 2000)
        
        # ตัดความยาวหากเกิน
        if len(description) > max_length:
            description = description[:max_length-3] + "..."
        
        # เพิ่ม keywords หากยังไม่มี
        keywords = opportunity.trend_data.keywords
        description_lower = description.lower()
        
        for keyword in keywords:
            if keyword.lower() not in description_lower:
                if len(description) + len(keyword) + 10 < max_length:
                    description += f"\n\n#{keyword.replace(' ', '')}"
        
        return description

    # Hashtags generation

    async def generate_hashtags(self, opportunity: ContentOpportunity,
                              platform: str = "general") -> GenerationResult:
        """สร้าง hashtags สำหรับเนื้อหา"""
        
        request = GenerationRequest(
            content_type="hashtags",
            context={
                "opportunity": opportunity,
                "platform": platform,
                "trending_focus": True
            },
            quality_tier=self.quality_tier
        )
        
        return await self._generate_with_quality_control(request, self._generate_hashtags_internal)

    async def _generate_hashtags_internal(self, request: GenerationRequest) -> List[str]:
        """สร้าง hashtags แบบละเอียด"""
        
        opportunity = request.context["opportunity"]
        platform = request.context.get("platform", "general")
        
        text_ai = self.service_registry.get_service("text_ai", request.quality_tier)
        
        prompt = self._build_hashtags_prompt(opportunity, platform)
        response = await text_ai.generate_content(prompt)
        
        hashtags = self._parse_hashtags_response(response)
        hashtags = self._optimize_hashtags(hashtags, platform, opportunity)
        
        return hashtags

    def _build_hashtags_prompt(self, opportunity: ContentOpportunity, platform: str) -> str:
        """สร้าง prompt สำหรับ hashtags"""
        
        platform_limits = {
            "tiktok": 10,
            "instagram": 30,
            "youtube": 15,
            "facebook": 20,
            "general": 15
        }
        
        max_hashtags = platform_limits.get(platform, 15)
        
        prompt = f"""
สร้าง hashtags สำหรับเนื้อหาต่อไปนี้:

หัวข้อ: {opportunity.content_idea.title}
ประเภท: {opportunity.content_idea.content_type}
Trend: {opportunity.trend_data.topic}
Keywords: {', '.join(opportunity.trend_data.keywords)}
Platform: {platform}

สร้าง {max_hashtags} hashtags ที่:
1. เกี่ยวข้องกับเนื้อหา
2. มีโอกาสเป็น trending
3. เหมาะสมกับ {platform}
4. ช่วยเพิ่ม reach และ engagement
5. ใช้ทั้งภาษาไทยและอังกฤษ

ประเภท hashtags ที่ควรมี:
- Hashtags เฉพาะเนื้อหา (3-5 tags)
- Hashtags ทั่วไปของประเภท (2-3 tags)
- Hashtags trending (2-3 tags)
- Hashtags platform-specific (2-3 tags)
- Hashtags community/audience (2-3 tags)

ตัวอย่างรูปแบบ:
#เนื้อหาหลัก #ประเภท #trending #platform #community

กรุณาตอบเป็น JSON array:
["#hashtag1", "#hashtag2", "#hashtag3", ...]
"""
        
        return prompt.strip()

    def _parse_hashtags_response(self, response: str) -> List[str]:
        """แยกวิเคราะห์ response ของ hashtags"""
        
        try:
            if response.strip().startswith('['):
                hashtags = json.loads(response)
            else:
                # แยกแบบ manual
                hashtags = []
                
                # หา hashtags ในข้อความ
                hash_pattern = r'#[^\s#]+(?=[^\w]|$)'
                matches = re.findall(hash_pattern, response)
                hashtags.extend(matches)
                
                # ถ้าไม่เจอ hashtags ให้แยกจาก lines
                if not hashtags:
                    lines = response.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('#'):
                            hashtags.append(line.split()[0])
            
            # ทำความสะอาด hashtags
            cleaned_hashtags = []
            for tag in hashtags:
                if isinstance(tag, str):
                    tag = tag.strip()
                    if not tag.startswith('#'):
                        tag = '#' + tag
                    tag = re.sub(r'[^\w#ก-ฮ]', '', tag)
                    if len(tag) > 1:  # ต้องมีมากกว่า # อย่างเดียว
                        cleaned_hashtags.append(tag)
            
            return cleaned_hashtags if cleaned_hashtags else self._create_fallback_hashtags()
            
        except Exception as e:
            self.logger.warning(f"Failed to parse hashtags response: {e}")
            return self._create_fallback_hashtags()

    def _create_fallback_hashtags(self) -> List[str]:
        """สร้าง hashtags สำรอง"""
        
        return [
            "#เนื้อหาดี", "#ความรู้", "#สนุกสนาน", "#ไทย", "#Thailand",
            "#ติดตาม", "#แชร์", "#ไลค์", "#เทรนด์", "#viral",
            "#content", "#learning", "#entertainment", "#education", "#trending"
        ]

    def _optimize_hashtags(self, hashtags: List[str], platform: str, 
                         opportunity: ContentOpportunity) -> List[str]:
        """ปรับปรุง hashtags ให้เหมาะสม"""
        
        platform_limits = {
            "tiktok": 10,
            "instagram": 30,
            "youtube": 15,
            "facebook": 20,
            "general": 15
        }
        
        max_hashtags = platform_limits.get(platform, 15)
        
        # เพิ่ม platform-specific hashtags
        platform_tags = {
            "tiktok": ["#fyp", "#viral", "#TikTokThailand"],
            "instagram": ["#instathailand", "#อินสตาไทย"],
            "youtube": ["#YouTubeThailand", "#คลิปไทย"],
            "facebook": ["#เฟสบุ๊ก", "#แชร์"]
        }
        
        if platform in platform_tags:
            for tag in platform_tags[platform]:
                if tag not in hashtags and len(hashtags) < max_hashtags:
                    hashtags.append(tag)
        
        # เพิ่ม keywords จาก trend
        for keyword in opportunity.trend_data.keywords:
            keyword_tag = f"#{keyword.replace(' ', '')}"
            if keyword_tag not in hashtags and len(hashtags) < max_hashtags:
                hashtags.append(keyword_tag)
        
        # จำกัดจำนวน
        return hashtags[:max_hashtags]

    # Thumbnail concept generation

    async def generate_thumbnail_concept(self, opportunity: ContentOpportunity,
                                       style_preferences: Dict = None) -> GenerationResult:
        """สร้างแนวคิด thumbnail"""
        
        request = GenerationRequest(
            content_type="thumbnail_concept",
            context={
                "opportunity": opportunity,
                "style_preferences": style_preferences or {},
                "platform_optimization": True
            },
            quality_tier=self.quality_tier
        )
        
        return await self._generate_with_quality_control(request, self._generate_thumbnail_internal)

    async def _generate_thumbnail_internal(self, request: GenerationRequest) -> Dict[str, Any]:
        """สร้าง thumbnail concept แบบละเอียด"""
        
        opportunity = request.context["opportunity"]
        style_prefs = request.context.get("style_preferences", {})
        
        text_ai = self.service_registry.get_service("text_ai", request.quality_tier)
        
        prompt = self._build_thumbnail_prompt(opportunity, style_prefs)
        response = await text_ai.generate_content(prompt)
        
        concept = self._parse_thumbnail_response(response)
        concept = self._optimize_thumbnail_concept(concept, opportunity)
        
        return concept

    def _build_thumbnail_prompt(self, opportunity: ContentOpportunity, 
                              style_prefs: Dict) -> str:
        """สร้าง prompt สำหรับ thumbnail concept"""
        
        prompt = f"""
สร้างแนวคิด thumbnail ที่น่าคลิกสำหรับเนื้อหาต่อไปนี้:

หัวข้อ: {opportunity.content_idea.title}
ประเภท: {opportunity.content_idea.content_type}
กลุ่มเป้าหมาย: {opportunity.content_idea.target_audience}
Trend: {opportunity.trend_data.topic}

สร้าง thumbnail concept ที่:
1. ดึงดูดความสนใจและเพิ่ม click-through rate
2. สื่อเนื้อหาได้ชัดเจน
3. เหมาะสมกับกลุ่มเป้าหมาย
4. โดดเด่นในฟีด social media
5. ใช้สีและ composition ที่เหมาะสม

กรุณาตอบในรูปแบบ JSON:
{{
  "main_concept": "แนวคิดหลักของภาพ",
  "visual_elements": ["องค์ประกอบภาพ 1", "องค์ประกอบภาพ 2"],
  "color_scheme": ["สีหลัก", "สีรอง"],
  "text_overlay": {{
    "main_text": "ข้อความหลักบน thumbnail",
    "font_style": "รูปแบบฟอนต์",
    "text_placement": "ตำแหน่งข้อความ"
  }},
  "composition": "การจัดองค์ประกอบ",
  "mood": "อารมณ์ของภาพ",
  "style": "สไตล์การออกแบบ",
  "click_factors": ["ปัจจัยที่ทำให้คลิก 1", "ปัจจัยที่ทำให้คลิก 2"]
}}

ตัวอย่างแนวคิดที่ดี:
- ใช้ contrast สูงเพื่อให้โดดเด่น
- มีใบหน้าหรือ expression ที่น่าสนใจ
- ข้อความใหญ่และอ่านง่าย
- ใช้สีที่สดใสและดึงดูดสายตา
- มี visual hierarchy ที่ชัดเจน
"""
        
        return prompt.strip()

    def _parse_thumbnail_response(self, response: str) -> Dict[str, Any]:
        """แยกวิเคราะห์ response ของ thumbnail concept"""
        
        try:
            if response.strip().startswith('{'):
                concept = json.loads(response)
            else:
                # สร้าง concept จาก text
                concept = self._extract_thumbnail_concept(response)
            
            # ตรวจสอบ required fields
            required_fields = ["main_concept", "visual_elements", "color_scheme"]
            for field in required_fields:
                if field not in concept:
                    concept[field] = self._get_default_thumbnail_element(field)
            
            return concept
            
        except Exception as e:
            self.logger.warning(f"Failed to parse thumbnail response: {e}")
            return self._create_fallback_thumbnail_concept()

    def _extract_thumbnail_concept(self, response: str) -> Dict[str, Any]:
        """สกัดแนวคิด thumbnail จาก text response"""
        
        concept = {}
        
        # หาแนวคิดหลัก
        concept_patterns = [
            r"แนวคิด[หลัก]*:?\s*([^\n]+)",
            r"concept:?\s*([^\n]+)",
            r"หลัก:?\s*([^\n]+)"
        ]
        
        for pattern in concept_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                concept["main_concept"] = match.group(1).strip()
                break
        
        # หาสี
        color_pattern = r"สี[^:]*:?\s*([^\n]+)"
        color_match = re.search(color_pattern, response, re.IGNORECASE)
        if color_match:
            colors = [c.strip() for c in color_match.group(1).split(',')]
            concept["color_scheme"] = colors[:3]  # เอาแค่ 3 สีแรก
        
        # หา visual elements
        elements = []
        element_patterns = [
            r"องค์ประกอบ[^:]*:?\s*([^\n]+)",
            r"elements?[^:]*:?\s*([^\n]+)"
        ]
        
        for pattern in element_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                elements.extend([e.strip() for e in match.split(',')])
        
        concept["visual_elements"] = elements[:5]  # เอาแค่ 5 elements แรก
        
        return concept

    def _get_default_thumbnail_element(self, field: str) -> Any:
        """ได้ element เริ่มต้นสำหรับ thumbnail"""
        
        defaults = {
            "main_concept": "ภาพที่สื่อเนื้อหาชัดเจนและน่าสนใจ",
            "visual_elements": ["ใบหน้าที่แสดงอารมณ์", "ข้อความหลัก", "สัญลักษณ์ที่เกี่ยวข้อง"],
            "color_scheme": ["สีน้ำเงิน", "สีขาว", "สีเหลือง"],
            "text_overlay": {
                "main_text": "หัวข้อหลัก",
                "font_style": "ตัวหนา, ชัดเจน",
                "text_placement": "ส่วนบนหรือกลางภาพ"
            },
            "composition": "ใช้ rule of thirds และ visual hierarchy",
            "mood": "เป็นมิตร น่าเชื่อถือ น่าสนใจ",
            "style": "สีสดใส contrast สูง อ่านง่าย",
            "click_factors": ["ใบหน้าที่น่าสนใจ", "ข้อความที่ดึงดูด", "สีที่โดดเด่น"]
        }
        
        return defaults.get(field, "ไม่ระบุ")

    def _create_fallback_thumbnail_concept(self) -> Dict[str, Any]:
        """สร้าง thumbnail concept สำรอง"""
        
        return {
            "main_concept": "ภาพที่สื่อเนื้อหาชัดเจนและดึงดูดความสนใจ",
            "visual_elements": [
                "ใบหน้าที่แสดงอารมณ์เหมาะสม",
                "ข้อความหัวข้อขนาดใหญ่",
                "สัญลักษณ์หรือไอคอนที่เกี่ยวข้อง",
                "พื้นหลังที่ไม่รบกวนเนื้อหา"
            ],
            "color_scheme": ["สีน้ำเงิน", "สีขาว", "สีส้ม"],
            "text_overlay": {
                "main_text": "หัวข้อหลักที่อ่านง่าย",
                "font_style": "ตัวหนา Sans-serif",
                "text_placement": "ตำแหน่งที่เด่นชัด"
            },
            "composition": "ใช้ rule of thirds และจัดองค์ประกอบให้สมดุล",
            "mood": "เป็นมิตร น่าเชื่อถือ และน่าสนใจ",
            "style": "สีสดใส contrast สูง อ่านง่าย",
            "click_factors": [
                "ใบหน้าหรือการแสดงออกที่น่าสนใจ",
                "ข้อความที่สร้างความอยากรู้",
                "การใช้สีที่โดดเด่นในฟีด"
            ]
        }

    def _optimize_thumbnail_concept(self, concept: Dict[str, Any], 
                                  opportunity: ContentOpportunity) -> Dict[str, Any]:
        """ปรับปรุง thumbnail concept ให้เหมาะสม"""
        
        content_type = opportunity.content_idea.content_type
        
        # ปรับ mood ตามประเภทเนื้อหา
        type_moods = {
            "educational": "เป็นมิตร น่าเชื่อถือ ให้ความรู้",
            "entertainment": "สนุกสนาน เร้าใจ น่าติดตาม",
            "tutorial": "ชัดเจน เข้าใจง่าย น่าเรียนรู้",
            "news": "น่าเชื่อถือ ทันสมัย มืออาชีพ"
        }
        
        if content_type in type_moods:
            concept["mood"] = type_moods[content_type]
        
        # ปรับสีตามประเภท
        type_colors = {
            "educational": ["สีน้ำเงิน", "สีขาว", "สีเขียว"],
            "entertainment": ["สีแดง", "สีเหลือง", "สีม่วง"],
            "tutorial": ["สีเขียว", "สีขาว", "สีเทา"],
            "news": ["สีแดง", "สีดำ", "สีขาว"]
        }
        
        if content_type in type_colors:
            concept["color_scheme"] = type_colors[content_type]
        
        # เพิ่ม click factors เฉพาะ
        concept["click_factors"].append(f"เหมาะสมกับ{content_type}")
        concept["click_factors"].append(f"ดึงดูด{opportunity.content_idea.target_audience}")
        
        return concept

    # Quality control และ utility methods

    async def _generate_with_quality_control(self, request: GenerationRequest, 
                                           generator_func) -> GenerationResult:
        """สร้างเนื้อหาพร้อม quality control"""
        
        self.generation_stats["total_requests"] += 1
        start_time = datetime.now()
        
        settings = self.generation_settings.get(request.content_type, {})
        max_retries = settings.get("max_retries", 2)
        threshold = self.quality_thresholds[request.quality_tier]
        
        best_result = None
        best_score = 0.0
        
        for attempt in range(max_retries + 1):
            try:
                # สร้างเนื้อหา
                content = await generator_func(request)
                
                # ประเมินคุณภาพ
                quality_score = self._evaluate_content_quality(content, request)
                
                # ถ้าคุณภาพดีพอให้ใช้เลย
                if quality_score >= threshold["min_quality_score"]:
                    generation_time = (datetime.now() - start_time).total_seconds()
                    cost = self._calculate_generation_cost(request, generation_time)
                    
                    result = GenerationResult(
                        content_type=request.content_type,
                        generated_content=content,
                        quality_score=quality_score,
                        generation_time=generation_time,
                        ai_service_used=self._get_ai_service_name(request.quality_tier),
                        cost_estimate=cost,
                        metadata={
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "quality_threshold": threshold["min_quality_score"]
                        },
                        created_at=datetime.now()
                    )
                    
                    self.generation_stats["successful_generations"] += 1
                    self.generation_stats["total_cost"] += cost
                    self._update_quality_average(quality_score)
                    
                    return result
                
                # เก็บผลลัพธ์ที่ดีที่สุด
                if quality_score > best_score:
                    best_score = quality_score
                    best_result = content
                    
            except Exception as e:
                self.logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    self.generation_stats["failed_generations"] += 1
                    raise ContentGenerationError(f"Failed after {max_retries + 1} attempts: {e}")
        
        # ถ้าไม่มีผลลัพธ์ที่ผ่านเกณฑ์ ให้ใช้ที่ดีที่สุด
        if best_result:
            generation_time = (datetime.now() - start_time).total_seconds()
            cost = self._calculate_generation_cost(request, generation_time)
            
            result = GenerationResult(
                content_type=request.content_type,
                generated_content=best_result,
                quality_score=best_score,
                generation_time=generation_time,
                ai_service_used=self._get_ai_service_name(request.quality_tier),
                cost_estimate=cost,
                metadata={
                    "attempt": max_retries + 1,
                    "max_retries": max_retries,
                    "quality_threshold": threshold["min_quality_score"],
                    "warning": "Quality below threshold but best available"
                },
                created_at=datetime.now()
            )
            
            self.generation_stats["successful_generations"] += 1
            self.generation_stats["total_cost"] += cost
            self._update_quality_average(best_score)
            
            return result
        
        # ถ้าไม่มีผลลัพธ์เลย
        self.generation_stats["failed_generations"] += 1
        raise ContentGenerationError("Failed to generate any usable content")

    def _evaluate_content_quality(self, content: Any, request: GenerationRequest) -> float:
        """ประเมินคุณภาพเนื้อหา"""
        
        content_type = request.content_type
        score = 5.0  # คะแนนพื้นฐาน
        
        if content_type == "script":
            score = self._evaluate_script_quality(content)
        elif content_type == "title":
            score = self._evaluate_titles_quality(content)
        elif content_type == "description":
            score = self._evaluate_descriptions_quality(content)
        elif content_type == "hashtags":
            score = self._evaluate_hashtags_quality(content)
        elif content_type == "thumbnail_concept":
            score = self._evaluate_thumbnail_quality(content)
        
        return min(max(score, 0.0), 10.0)  # จำกัดระหว่าง 0-10

    def _evaluate_script_quality(self, script: Dict[str, str]) -> float:
        """ประเมินคุณภาพ script"""
        
        score = 5.0
        
        # ตรวจสอบครบองค์ประกอบ
        required_parts = ["hook", "main_content", "cta"]
        missing_parts = [part for part in required_parts if part not in script or not script[part]]
        
        if not missing_parts:
            score += 2.0
        else:
            score -= len(missing_parts) * 1.0
        
        # ตรวจสอบความยาว
        if "main_content" in script:
            word_count = len(script["main_content"].split())
            if 100 <= word_count <= 500:
                score += 1.0
            elif word_count < 50:
                score -= 1.0
        
        # ตรวจสอบการใช้ภาษา
        if "hook" in script:
            hook = script["hook"]
            if any(word in hook for word in ["น่าสนใจ", "มาดู", "เรียนรู้", "ไม่เคยเห็น"]):
                score += 0.5
        
        # ตรวจสอบ CTA
        if "cta" in script:
            cta = script["cta"]
            if any(word in cta for word in ["ไลค์", "ติดตาม", "แชร์", "คอมเมนต์"]):
                score += 0.5
        
        return score

    def _evaluate_titles_quality(self, titles: List[str]) -> float:
        """ประเมินคุณภาพ titles"""
        
        if not titles:
            return 0.0
        
        total_score = 0.0
        
        for title in titles:
            title_score = 5.0
            
            # ความยาวเหมาะสม
            if 20 <= len(title) <= 80:
                title_score += 1.0
            elif len(title) < 10 or len(title) > 100:
                title_score -= 1.0
            
            # มี keywords น่าสนใจ
            engaging_words = ["วิธี", "เคล็ดลับ", "ความลับ", "ไม่เคยเห็น", "น่าสนใจ", "เจ๋ง", "สุดยอด"]
            if any(word in title for word in engaging_words):
                title_score += 1.0
            
            # ไม่มีตัวอักษรพิเศษเกินไป
            special_chars = len([c for c in title if not c.isalnum() and c not in " .-"])
            if special_chars <= 3:
                title_score += 0.5
            
            total_score += title_score
        
        return total_score / len(titles)

    def _evaluate_descriptions_quality(self, descriptions: Dict[str, str]) -> float:
        """ประเมินคุณภาพ descriptions"""
        
        if not descriptions:
            return 0.0
        
        total_score = 0.0
        
        for platform, description in descriptions.items():
            desc_score = 5.0
            
            # ความยาวเหมาะสม
            if 50 <= len(description) <= 1000:
                desc_score += 1.0
            elif len(description) < 30:
                desc_score -= 1.0
            
            # มี call-to-action
            cta_words = ["ไลค์", "แชร์", "ติดตาม", "คอมเมนต์", "กด", "Subscribe"]
            if any(word in description for word in cta_words):
                desc_score += 1.0
            
            # มี hashtags (สำหรับ social media)
            if platform in ["instagram", "tiktok", "facebook"]:
                if "#" in description:
                    desc_score += 0.5
            
            # โครงสร้างดี (มีย่อหน้า)
            if "\n" in description:
                desc_score += 0.5
            
            total_score += desc_score
        
        return total_score / len(descriptions)

    def _evaluate_hashtags_quality(self, hashtags: List[str]) -> float:
        """ประเมินคุณภาพ hashtags"""
        
        if not hashtags:
            return 0.0
        
        score = 5.0
        
        # จำนวนเหมาะสม
        if 5 <= len(hashtags) <= 20:
            score += 1.0
        elif len(hashtags) < 3:
            score -= 2.0
        
        # มี # ครบ
        proper_hashtags = [tag for tag in hashtags if tag.startswith('#') and len(tag) > 1]
        if len(proper_hashtags) == len(hashtags):
            score += 1.0
        else:
            score -= 0.5
        
        # ความหลากหลาย (ไม่ซ้ำ)
        unique_hashtags = len(set(hashtags))
        if unique_hashtags == len(hashtags):
            score += 1.0
        else:
            score -= 0.5
        
        # มีทั้งภาษาไทยและอังกฤษ
        thai_tags = [tag for tag in hashtags if any('ก' <= c <= 'ฮ' for c in tag)]
        eng_tags = [tag for tag in hashtags if any('a' <= c.lower() <= 'z' for c in tag)]
        
        if thai_tags and eng_tags:
            score += 1.0
        
        return score

    def _evaluate_thumbnail_quality(self, concept: Dict[str, Any]) -> float:
        """ประเมินคุณภาพ thumbnail concept"""
        
        score = 5.0
        
        required_fields = ["main_concept", "visual_elements", "color_scheme"]
        
        # ตรวจสอบครบองค์ประกอบ
        for field in required_fields:
            if field in concept and concept[field]:
                score += 1.0
            else:
                score -= 1.0
        
        # ตรวจสอบ visual elements
        if "visual_elements" in concept:
            elements = concept["visual_elements"]
            if isinstance(elements, list) and len(elements) >= 3:
                score += 1.0
        
        # ตรวจสอบ color scheme
        if "color_scheme" in concept:
            colors = concept["color_scheme"]
            if isinstance(colors, list) and len(colors) >= 2:
                score += 1.0
        
        # ตรวจสอบ click factors
        if "click_factors" in concept:
            factors = concept["click_factors"]
            if isinstance(factors, list) and len(factors) >= 2:
                score += 0.5
        
        return score

    def _calculate_generation_cost(self, request: GenerationRequest, 
                                 generation_time: float) -> float:
        """คำนวณต้นทุนการสร้าง"""
        
        base_costs = {
            QualityTier.BUDGET: 2.0,
            QualityTier.BALANCED: 8.0,
            QualityTier.PREMIUM: 25.0
        }
        
        base_cost = base_costs.get(request.quality_tier, 5.0)
        
        # ปรับตามประเภทเนื้อหา
        type_multipliers = {
            "script": 2.0,
            "title": 0.5,
            "description": 1.0,
            "hashtags": 0.3,
            "thumbnail_concept": 1.5
        }
        
        multiplier = type_multipliers.get(request.content_type, 1.0)
        
        # ปรับตามเวลาที่ใช้
        time_factor = 1.0 + (generation_time / 60.0)  # เพิ่มตามนาที
        
        total_cost = base_cost * multiplier * time_factor
        
        return round(total_cost, 2)

    def _get_ai_service_name(self, quality_tier: QualityTier) -> str:
        """ได้ชื่อ AI service ที่ใช้"""
        
        service_names = {
            QualityTier.BUDGET: "Groq",
            QualityTier.BALANCED: "OpenAI GPT-3.5",
            QualityTier.PREMIUM: "Claude"
        }
        
        return service_names.get(quality_tier, "Unknown AI")

    def _update_quality_average(self, quality_score: float):
        """อัพเดทคะแนนคุณภาพเฉลี่ย"""
        
        total_generations = self.generation_stats["successful_generations"]
        
        if total_generations == 1:
            self.generation_stats["average_quality"] = quality_score
        else:
            current_avg = self.generation_stats["average_quality"]
            new_avg = ((current_avg * (total_generations - 1)) + quality_score) / total_generations
            self.generation_stats["average_quality"] = round(new_avg, 2)

    # Public utility methods

    def get_generation_statistics(self) -> Dict[str, Any]:
        """ดูสถิติการสร้างเนื้อหา"""
        
        stats = self.generation_stats.copy()
        
        if stats["total_requests"] > 0:
            stats["success_rate"] = round(
                (stats["successful_generations"] / stats["total_requests"]) * 100, 2
            )
        else:
            stats["success_rate"] = 0.0
        
        stats["quality_tier"] = self.quality_tier.value
        stats["average_cost_per_generation"] = (
            round(stats["total_cost"] / max(stats["successful_generations"], 1), 2)
        )
        
        return stats

    async def batch_generate_content(self, requests: List[GenerationRequest]) -> List[GenerationResult]:
        """สร้างเนื้อหาหลายรายการพร้อมกัน"""
        
        self.logger.info(f"Starting batch generation for {len(requests)} requests")
        
        # สร้าง tasks
        tasks = []
        for request in requests:
            if request.content_type == "script":
                task = self._generate_with_quality_control(request, self._generate_script_internal)
            elif request.content_type == "title":
                task = self._generate_with_quality_control(request, self._generate_titles_internal)
            elif request.content_type == "description":
                task = self._generate_with_quality_control(request, self._generate_descriptions_internal)
            elif request.content_type == "hashtags":
                task = self._generate_with_quality_control(request, self._generate_hashtags_internal)
            elif request.content_type == "thumbnail_concept":
                task = self._generate_with_quality_control(request, self._generate_thumbnail_internal)
            else:
                continue
            
            tasks.append(task)
        
        # รัน parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # แยก results และ errors
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "request_index": i,
                    "content_type": requests[i].content_type,
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        if errors:
            self.logger.warning(f"Batch generation completed with {len(errors)} errors")
        
        self.logger.info(f"Batch generation completed: {len(successful_results)} successful")
        
        return successful_results

    def reset_statistics(self):
        """รีเซ็ตสถิติ"""
        
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_cost": 0.0,
            "average_quality": 0.0
        }


# Utility functions สำหรับการใช้งาน

async def generate_complete_content_package(opportunity: ContentOpportunity,
                                          quality_tier: QualityTier = QualityTier.BUDGET,
                                          platforms: List[str] = None) -> Dict[str, GenerationResult]:
    """
    สร้างเนื้อหาครบชุดสำหรับ opportunity
    """
    
    generator = ContentGenerator(quality_tier)
    platforms = platforms or ["youtube"]
    
    # สร้าง content plan mock
    content_plan = ContentPlan(
        title=opportunity.content_idea.title,
        description=opportunity.content_idea.description,
        content_type=opportunity.content_idea.content_type,
        target_audience=opportunity.content_idea.target_audience,
        estimated_duration=opportunity.content_idea.estimated_duration,
        style="casual",
        platforms=platforms
    )
    
    results = {}
    
    try:
        # สร้าง script
        results["script"] = await generator.generate_script(opportunity, content_plan)
        
        # สร้าง titles
        results["titles"] = await generator.generate_titles(opportunity, count=5)
        
        # สร้าง descriptions
        results["descriptions"] = await generator.generate_descriptions(opportunity, platforms)
        
        # สร้าง hashtags
        results["hashtags"] = await generator.generate_hashtags(opportunity, platforms[0])
        
        # สร้าง thumbnail concept
        results["thumbnail"] = await generator.generate_thumbnail_concept(opportunity)
        
        return results
        
    except Exception as e:
        logging.error(f"Failed to generate complete content package: {e}")
        raise


if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    async def example_usage():
        from shared.models.content_opportunity import ContentOpportunity
        from shared.models.trend_data import TrendData
        from services.opportunity_engine import ContentIdea
        
        # สร้าง mock data
        trend_data = TrendData(
            id="trend_001",
            source="youtube",
            topic="AI สร้างคลิป",
            keywords=["AI", "วิดีโอ", "เทคโนโลยี", "สร้างเนื้อหา"],
            popularity_score=85.0,
            growth_rate=30.0,
            category="technology",
            region="TH",
            collected_at=datetime.now(),
            raw_data={}
        )
        
        content_idea = ContentIdea(
            title="สอนใช้ AI สร้างคลิปไวรัลง่ายๆ ที่บ้าน",
            description="คู่มือละเอียดสำหรับการใช้ AI ในการสร้างเนื้อหาวิดีโอ",
            content_type="educational",
            angle="มุมมองมือใหม่",
            target_audience="นักเรียน นักศึกษา คนรุ่นใหม่",
            estimated_duration=300,
            production_complexity="medium",
            viral_potential=8.5,
            monetization_potential=7.5
        )
        
        opportunity = ContentOpportunity(
            id="opp_001",
            trend_id="trend_001",
            trend_data=trend_data,
            content_idea=content_idea,
            market_analysis=None,
            estimated_roi=4.2,
            production_cost=85.0,
            competition_level="medium",
            priority_score=8.8,
            created_at=datetime.now(),
            status="pending"
        )
        
        # สร้างเนื้อหาครบชุด
        print("🚀 เริ่มสร้างเนื้อหาครบชุด...")
        
        results = await generate_complete_content_package(
            opportunity,
            quality_tier=QualityTier.BALANCED,
            platforms=["youtube", "tiktok"]
        )
        
        print("✅ สร้างเนื้อหาเสร็จแล้ว!")
        
        # แสดงผลลัพธ์
        for content_type, result in results.items():
            print(f"\n📋 {content_type.upper()}:")
            print(f"   Quality Score: {result.quality_score}/10")
            print(f"   Generation Time: {result.generation_time:.2f}s")
            print(f"   Cost: {result.cost_estimate} บาท")
            print(f"   AI Service: {result.ai_service_used}")
            
            if content_type == "script":
                script = result.generated_content
                print(f"   Hook: {script['hook'][:50]}...")
                print(f"   Main Content: {len(script['main_content'])} characters")
            elif content_type == "titles":
                titles = result.generated_content
                print(f"   Generated {len(titles)} titles")
                print(f"   Best Title: {titles[0]}")
            elif content_type == "descriptions":
                descriptions = result.generated_content
                print(f"   Platforms: {list(descriptions.keys())}")
            elif content_type == "hashtags":
                hashtags = result.generated_content
                print(f"   Generated {len(hashtags)} hashtags")
                print(f"   Sample: {', '.join(hashtags[:5])}")
            elif content_type == "thumbnail":
                concept = result.generated_content
                print(f"   Concept: {concept['main_concept'][:50]}...")
        
        # แสดงสถิติรวม
        generator = ContentGenerator(QualityTier.BALANCED)
        stats = generator.get_generation_statistics()
        print(f"\n📊 Generation Statistics:")
        print(f"   Success Rate: {stats['success_rate']}%")
        print(f"   Average Quality: {stats['average_quality']}/10")
        print(f"   Total Cost: {stats['total_cost']} บาท")
    
    # รัน example
    asyncio.run(example_usage())