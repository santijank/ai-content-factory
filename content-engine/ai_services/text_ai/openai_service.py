"""
OpenAI Service - Balanced Tier
สมดุลระหว่างคุณภาพและราคา เหมาะสำหรับงานที่ต้องการความแม่นยำปานกลาง
รองรับ GPT-4o mini และ GPT-4o สำหรับงานที่ซับซ้อน
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
import aiohttp
import time
from datetime import datetime
import base64
from io import BytesIO

from ..service_registry import BaseAIService

logger = logging.getLogger(__name__)

class OpenAIService(BaseAIService):
    """
    OpenAI Service - สมดุลระหว่างคุณภาพและราคา
    เหมาะสำหรับ: Content creation, Advanced analysis, Multi-modal tasks
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        super().__init__(api_key, model_name)
        self.base_url = "https://api.openai.com/v1"
        self.max_retries = 3
        self.retry_delay = 2.0
        
        # Model configurations with Thai Baht pricing
        self.models = {
            "gpt-4o-mini": {
                "context": 128000,
                "input_cost_per_1k": 0.005,  # ~0.18 บาท
                "output_cost_per_1k": 0.02,  # ~0.72 บาท
                "multimodal": True,
                "speed": "fast",
                "quality": "good"
            },
            "gpt-4o": {
                "context": 128000,
                "input_cost_per_1k": 0.15,   # ~5.4 บาท
                "output_cost_per_1k": 0.60,  # ~21.6 บาท
                "multimodal": True,
                "speed": "medium",
                "quality": "excellent"
            },
            "gpt-3.5-turbo": {
                "context": 16385,
                "input_cost_per_1k": 0.0015, # ~0.054 บาท
                "output_cost_per_1k": 0.002, # ~0.072 บาท
                "multimodal": False,
                "speed": "very_fast",
                "quality": "decent"
            }
        }
        
        # Exchange rate USD to THB (approximate)
        self.usd_to_thb = 36.0
        
    async def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """ประมวลผลข้อมูลด้วย OpenAI"""
        
        task_type = kwargs.get('task_type', 'general')
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 2000)
        images = kwargs.get('images', None)  # For multimodal tasks
        use_advanced_model = kwargs.get('use_advanced_model', False)
        
        # Auto-select model based on task complexity
        selected_model = self._select_model(task_type, use_advanced_model, images)
        
        # Get optimized prompts
        system_prompt = self._get_system_prompt(task_type)
        user_prompt = self._format_user_prompt(input_data, task_type, **kwargs)
        
        try:
            response = await self._make_api_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=selected_model,
                images=images
            )
            
            # Enhanced parsing with validation
            parsed_result = self._parse_and_validate_response(response, task_type)
            
            # Calculate accurate cost
            usage = response.get("usage", {})
            cost = self._calculate_detailed_cost(usage, selected_model)
            
            return {
                "success": True,
                "result": parsed_result,
                "model": selected_model,
                "usage": usage,
                "cost_breakdown": cost,
                "task_type": task_type,
                "quality_score": self._assess_quality(parsed_result, task_type),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model": selected_model if 'selected_model' in locals() else self.model_name,
                "task_type": task_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def _select_model(self, task_type: str, use_advanced: bool, has_images: bool) -> str:
        """เลือก model ที่เหมาะสมตาม task"""
        
        # Force GPT-4o for multimodal tasks
        if has_images:
            return "gpt-4o" if use_advanced else "gpt-4o-mini"
        
        # Complex tasks that benefit from advanced reasoning
        complex_tasks = [
            "content_strategy", 
            "competitor_analysis", 
            "trend_prediction",
            "script_advanced"
        ]
        
        if task_type in complex_tasks or use_advanced:
            return "gpt-4o"
        
        # Use mini for most tasks (balanced approach)
        return "gpt-4o-mini"
    
    def _get_system_prompt(self, task_type: str) -> str:
        """Enhanced system prompts with better instructions"""
        
        prompts = {
            "trend_analysis": """คุณคือผู้เชี่ยวชาญวิเคราะห์เทรนด์และการตลาดดิจิทัล
ใช้ความรู้เกี่ยวกับพฤติกรรมผู้บริโภค, วงจรชีวิตเทรนด์, และ platform algorithms
วิเคราะห์อย่างละเอียดและให้คะแนนที่แม่นยำพร้อมเหตุผล
ตอบในรูปแบบ JSON ที่มีโครงสร้างชัดเจน""",
            
            "content_strategy": """คุณคือ Content Strategist มืออาชีพที่เข้าใจ content ecosystems
สร้างกลยุทธ์เนื้อหาที่ครอบคลุม: hook psychology, audience journey, engagement tactics
คำนึงถึง platform-specific algorithms และ current content trends
ให้ actionable insights ที่สามารถนำไปปฏิบัติได้จริง""",
            
            "script_advanced": """คุณคือ Scriptwriter มืออาชีพที่เชี่ยวชาญการเขียนสำหรับดิจิทัลแพลตฟอร์ม
เข้าใจ pacing, retention curves, และ psychological triggers
เขียนสคริปต์ที่มี strong narrative arc และ optimized สำหรับ engagement metrics
รวม visual storytelling และ audio design considerations""",
            
            "hashtag_strategy": """คุณคือ Social Media Strategist ผู้เชี่ยวชาญ hashtag ecosystems
เข้าใจ hashtag algorithms, community behaviors, และ trending patterns
สร้างกลยุทธ์ hashtag ที่ balance reach, engagement, และ community building
วิเคราะห์ hashtag performance และ competitive landscape""",
            
            "competitor_analysis": """คุณคือ Market Intelligence Analyst
วิเคราะห์คู่แข่งอย่างลึกซึ้ง: content strategies, audience engagement, performance patterns
หา content gaps และ differentiation opportunities
ให้ competitive insights ที่ actionable และมี strategic value""",
            
            "roi_optimization": """คุณคือ Performance Marketing Specialist
คำนวณและ optimize ROI ของ content investments
วิเคราะห์ cost-benefit, conversion funnels, และ lifetime value
ให้คำแนะนำที่เน้น measurable results และ sustainable growth"""
        }
        
        return prompts.get(task_type, prompts["trend_analysis"])
    
    def _format_user_prompt(self, input_data: str, task_type: str, **kwargs) -> str:
        """Advanced prompt formatting with context"""
        
        if task_type == "trend_analysis":
            context = kwargs.get('context', {})
            region = context.get('region', 'Thailand')
            platform_focus = context.get('platforms', ['YouTube', 'TikTok'])
            
            return f"""
วิเคราะห์เทรนด์นี้อย่างละเอียดสำหรับตลาด{region}:

เทรนด์: {input_data}
แพลตฟอร์มเป้าหมาย: {', '.join(platform_focus)}

ให้การวิเคราะห์ในรูปแบบ JSON:
{{
  "trend_analysis": {{
    "trend_name": "ชื่อเทรนด์ที่แม่นยำ",
    "lifecycle_stage": "emerging/growing/peak/declining",
    "regional_relevance": "ความเกี่ยวข้องกับ{region} (1-10)",
    "scores": {{
      "viral_potential": 8,
      "content_saturation": 3,
      "audience_engagement": 9,
      "monetization_opportunity": 7,
      "longevity": 6
    }},
    "audience_segments": [
      {{
        "segment": "กลุ่มหลัก",
        "size_estimate": "จำนวนประมาณ",
        "engagement_level": "สูง/กลาง/ต่ำ",
        "content_preferences": ["ประเภทเนื้อหาที่ชอบ"]
      }}
    ],
    "content_opportunities": [
      {{
        "angle": "มุมมองเนื้อหา",
        "difficulty": "ง่าย/กลาง/ยาก",
        "estimated_reach": "การเข้าถึงที่คาดหวัง",
        "unique_value": "จุดเด่นที่แตกต่าง"
      }}
    ],
    "platform_optimization": {{
      "YouTube": {{"format": "รูปแบบที่เหมาะสม", "duration": "ความยาว", "focus": "จุดเน้น"}},
      "TikTok": {{"format": "รูปแบบที่เหมาะสม", "duration": "ความยาว", "focus": "จุดเน้น"}}
    }},
    "timing_strategy": {{
      "optimal_launch": "เวลาที่เหมาะสมที่สุด",
      "content_frequency": "ความถี่การโพสต์",
      "seasonal_factors": "ปัจจัยตามฤดูกาล"
    }},
    "risks_and_considerations": [
      "ความเสี่ยงที่ควรระวัง"
    ],
    "success_metrics": [
      "ตัวชี้วัดความสำเร็จ"
    ],
    "overall_recommendation": "คำแนะนำโดยรวม",
    "confidence_level": 85
  }}
}}
"""
        
        elif task_type == "content_strategy":
            goal = kwargs.get('goal', 'increase_engagement')
            budget = kwargs.get('budget', 'medium')
            timeline = kwargs.get('timeline', '1 month')
            
            return f"""
สร้างกลยุทธ์เนื้อหาสำหรับ:

หัวข้อ/เทรนด์: {input_data}
เป้าหมาย: {goal}
งบประมาณ: {budget}
ระยะเวลา: {timeline}

รูปแบบ JSON:
{{
  "content_strategy": {{
    "overview": "ภาพรวมกลยุทธ์",
    "content_pillars": [
      {{
        "pillar": "เสาหลักเนื้อหา",
        "percentage": 30,
        "content_types": ["ประเภทเนื้อหา"],
        "goals": ["เป้าหมายเฉพาะ"]
      }}
    ],
    "content_calendar": [
      {{
        "week": 1,
        "themes": ["ธีมประจำสัปดาห์"],
        "content_mix": {{"educational": 40, "entertainment": 40, "promotional": 20}},
        "key_posts": ["โพสต์สำคัญ"]
      }}
    ],
    "engagement_tactics": [
      {{
        "tactic": "วิธีการ",
        "implementation": "การนำไปใช้",
        "expected_impact": "ผลที่คาดหวัง"
      }}
    ],
    "resource_requirements": {{
      "time_per_week": "เวลาที่ต้องใช้",
      "tools_needed": ["เครื่องมือที่ต้องการ"],
      "skill_requirements": ["ทักษะที่ต้องการ"]
    }},
    "success_kpis": [
      {{
        "metric": "ตัวชี้วัด",
        "target": "เป้าหมาย",
        "measurement": "วิธีการวัด"
      }}
    ]
  }}
}}
"""
        
        elif task_type == "script_advanced":
            platform = kwargs.get('platform', 'YouTube')
            duration = kwargs.get('duration', '3-5 minutes')
            style = kwargs.get('style', 'educational')
            
            return f"""
เขียนสคริปต์วิดีโอระดับมืออาชีพสำหรับ:

หัวข้อ: {input_data}
แพลตฟอร์ม: {platform}
ความยาว: {duration}
สไตล์: {style}

รูปแบบ JSON:
{{
  "script": {{
    "title_options": ["ตัวเลือกหัวข้อ 3 แบบ"],
    "hook": {{
      "text": "สคริปต์ 15 วินาทีแรก",
      "duration": "0-15s",
      "visual_direction": "คำแนะนำการถ่ายภาพ",
      "audio_notes": "คำแนะนำเสียง",
      "retention_strategy": "กลยุทธ์กักเก็บผู้ชม"
    }},
    "introduction": {{
      "text": "แนะนำหัวข้อและสร้าง expectation",
      "duration": "15-30s",
      "visual_direction": "คำแนะนำการถ่ายภาพ",
      "key_promises": ["สิ่งที่ผู้ชมจะได้เรียนรู้"]
    }},
    "main_sections": [
      {{
        "section_title": "หัวข้อย่อย",
        "text": "เนื้อหาหลัก",
        "duration": "30s-1m",
        "visual_direction": "คำแนะนำการถ่ายภาพ",
        "engagement_moments": ["จุดที่ต้องมี interaction"],
        "transitions": "การเชื่อมต่อไปส่วนถัดไป"
      }}
    ],
    "conclusion": {{
      "text": "สรุปและ strong CTA",
      "duration": "30s",
      "visual_direction": "คำแนะนำการถ่ายภาพ",
      "call_to_actions": ["การกระทำที่ต้องการ"]
    }}
  }},
  "production_notes": {{
    "total_word_count": 500,
    "speaking_pace": "คำต่อนาที",
    "visual_requirements": ["ความต้องการด้านภาพ"],
    "audio_requirements": ["ความต้องการด้านเสียง"],
    "editing_suggestions": ["คำแนะนำการตัดต่อ"]
  }},
  "optimization": {{
    "seo_keywords": ["คำสำคัญ"],
    "thumbnail_concepts": ["ไอเดีย thumbnail"],
    "description_points": ["จุดสำคัญในรายละเอียด"]
  }}
}}
"""
        
        return input_data
    
    async def _make_api_call(self, system_prompt: str, user_prompt: str, 
                           temperature: float = 0.7, max_tokens: int = 2000,
                           model: str = None, images: List[str] = None) -> Dict[str, Any]:
        """เรียก OpenAI API with enhanced features"""
        
        if model is None:
            model = self.model_name
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Handle multimodal input
        if images and self.models[model].get("multimodal", False):
            user_content = [
                {"type": "text", "text": user_prompt}
            ]
            
            for image_data in images:
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}",
                        "detail": "low"  # For cost optimization
                    }
                })
                
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": user_prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"} if "JSON" in user_prompt else {"type": "text"}
        }
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            return result
                        
                        elif response.status == 429:  # Rate limit
                            wait_time = self.retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limit hit, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                            
                        else:
                            error_text = await response.text()
                            raise Exception(f"API error {response.status}: {error_text}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise Exception("API timeout after all retries")
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"API call failed (attempt {attempt + 1}): {str(e)}")
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise
        
        raise Exception("API call failed after all retries")
    
    def _parse_and_validate_response(self, response: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Enhanced parsing with validation"""
        
        try:
            content = response["choices"][0]["message"]["content"]
            
            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                
                # Validate structure based on task type
                is_valid = self._validate_response_structure(parsed, task_type)
                
                return {
                    "content": parsed,
                    "is_valid": is_valid,
                    "parsing_success": True
                }
                
            except json.JSONDecodeError:
                # Return structured text response
                return {
                    "content": content,
                    "is_valid": False,
                    "parsing_success": False,
                    "note": "Response was not in JSON format"
                }
                
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response structure: {e}")
            return {
                "error": "Unexpected response structure",
                "raw_response": response,
                "is_valid": False,
                "parsing_success": False
            }
    
    def _validate_response_structure(self, parsed: Dict[str, Any], task_type: str) -> bool:
        """Validate response structure"""
        
        required_fields = {
            "trend_analysis": ["trend_analysis"],
            "content_strategy": ["content_strategy"],
            "script_advanced": ["script", "production_notes"],
            "hashtag_strategy": ["hashtags", "strategy"]
        }
        
        required = required_fields.get(task_type, [])
        
        for field in required:
            if field not in parsed:
                logger.warning(f"Missing required field '{field}' in {task_type} response")
                return False
        
        return True
    
    def _calculate_detailed_cost(self, usage: Dict[str, Any], model: str) -> Dict[str, Any]:
        """คำนวณค่าใช้จ่ายละเอียด"""
        
        model_config = self.models.get(model, self.models["gpt-4o-mini"])
        
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        # Calculate in USD first
        input_cost_usd = (prompt_tokens / 1000) * model_config["input_cost_per_1k"]
        output_cost_usd = (completion_tokens / 1000) * model_config["output_cost_per_1k"]
        total_cost_usd = input_cost_usd + output_cost_usd
        
        # Convert to THB
        input_cost_thb = input_cost_usd * self.usd_to_thb
        output_cost_thb = output_cost_usd * self.usd_to_thb
        total_cost_thb = total_cost_usd * self.usd_to_thb
        
        return {
            "model": model,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            "costs": {
                "input_usd": round(input_cost_usd, 6),
                "output_usd": round(output_cost_usd, 6),
                "total_usd": round(total_cost_usd, 6),
                "input_thb": round(input_cost_thb, 4),
                "output_thb": round(output_cost_thb, 4),
                "total_thb": round(total_cost_thb, 4)
            },
            "rate_usd_to_thb": self.usd_to_thb
        }
    
    def _assess_quality(self, result: Dict[str, Any], task_type: str) -> int:
        """ประเมินคุณภาพผลลัพธ์ (1-10)"""
        
        if not result.get("is_valid", False):
            return 3
        
        content = result.get("content", {})
        
        # Basic quality indicators
        score = 5  # Base score
        
        # Check for completeness
        if isinstance(content, dict) and len(content) > 2:
            score += 2
        
        # Check for structured data
        if result.get("parsing_success", False):
            score += 1
        
        # Task-specific quality checks
        if task_type == "trend_analysis":
            if "scores" in str(content) and "content_opportunities" in str(content):
                score += 2
        elif task_type == "content_strategy":
            if "content_calendar" in str(content) and "success_kpis" in str(content):
                score += 2
        
        return min(score, 10)
    
    async def analyze_with_images(self, text: str, images: List[str], task_type: str = "multimodal_analysis") -> Dict[str, Any]:
        """วิเคราะห์ร่วมกับรูปภาพ"""
        
        return await self.process(
            text,
            task_type=task_type,
            images=images,
            use_advanced_model=True,  # Force GPT-4o for multimodal
            temperature=0.3  # Lower temperature for analysis
        )
    
    def get_model_comparison(self) -> Dict[str, Any]:
        """เปรียบเทียบ models ที่มี"""
        
        comparison = {}
        for model, config in self.models.items():
            comparison[model] = {
                "context_window": config["context"],
                "cost_per_1k_input_thb": config["input_cost_per_1k"] * self.usd_to_thb,
                "cost_per_1k_output_thb": config["output_cost_per_1k"] * self.usd_to_thb,
                "features": {
                    "multimodal": config["multimodal"],
                    "speed": config["speed"],
                    "quality": config["quality"]
                },
                "best_for": self._get_model_use_cases(model)
            }
        
        return comparison
    
    def _get_model_use_cases(self, model: str) -> List[str]:
        """Use cases แต่ละ model"""
        
        use_cases = {
            "gpt-4o-mini": [
                "การวิเคราะห์เทรนด์ทั่วไป",
                "การสร้างเนื้อหาพื้นฐาน",
                "การประมวลผลจำนวนมาก"
            ],
            "gpt-4o": [
                "การวิเคราะห์ซับซ้อน",
                "การสร้างกลยุทธ์",
                "การวิเคราะห์รูปภาพ",
                "งานที่ต้องการความแม่นยำสูง"
            ],
            "gpt-3.5-turbo": [
                "งานพื้นฐานที่ต้องการความเร็ว",
                "การประมวลผลราคาประหยัด"
            ]
        }
        
        return use_cases.get(model, ["งานทั่วไป"])

# Example usage
async def test_openai_service():
    """ทดสอบ OpenAI Service"""
    service = OpenAIService("your-openai-api-key")
    
    # Test advanced trend analysis
    result = await service.process(
        "Sustainable Fashion กำลังเป็นเทรนด์ในหมู่วัยรุ่นไทย",
        task_type="trend_analysis",
        context={
            "region": "Thailand",
            "platforms": ["TikTok", "Instagram"]
        }
    )
    
    print("Advanced Trend Analysis:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Test content strategy
    strategy_result = await service.process(
        "การทำอาหารไทยแบบ healthy",
        task_type="content_strategy",
        goal="increase_brand_awareness",
        budget="medium",
        timeline="3 months"
    )
    
    print("\nContent Strategy:")
    print(json.dumps(strategy_result, indent=2, ensure_ascii=False))
    
    # Show model comparison
    print("\nModel Comparison:")
    print(json.dumps(service.get_model_comparison(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_openai_service())