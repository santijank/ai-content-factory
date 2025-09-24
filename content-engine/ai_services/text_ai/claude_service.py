"""
Claude Service - Premium Tier
คุณภาพสูงสุด สำหรับงานที่ต้องการการคิดวิเคราะห์เชิงลึก
เหมาะสำหรับ Strategic planning, Complex analysis, High-quality content creation
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
import aiohttp
import time
from datetime import datetime
import base64

from ..service_registry import BaseAIService

logger = logging.getLogger(__name__)

class ClaudeService(BaseAIService):
    """
    Claude Service - Premium Tier คุณภาพสูงสุด
    เหมาะสำหรับ: Strategic analysis, Premium content, Complex reasoning tasks
    """
    
    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        super().__init__(api_key, model_name)
        self.base_url = "https://api.anthropic.com/v1"
        self.max_retries = 3
        self.retry_delay = 3.0
        
        # Model configurations with Thai Baht pricing (approximate)
        self.models = {
            "claude-3-5-sonnet-20241022": {
                "context": 200000,
                "input_cost_per_1k": 0.108,    # ~3.89 บาท
                "output_cost_per_1k": 0.432,   # ~15.55 บาท
                "intelligence": "highest",
                "speed": "fast",
                "quality": "excellent"
            },
            "claude-3-5-haiku-20241022": {
                "context": 200000,
                "input_cost_per_1k": 0.03,     # ~1.08 บาท
                "output_cost_per_1k": 0.15,    # ~5.40 บาท
                "intelligence": "high",
                "speed": "very_fast",
                "quality": "very_good"
            },
            "claude-3-opus-20240229": {
                "context": 200000,
                "input_cost_per_1k": 0.54,     # ~19.44 บาท
                "output_cost_per_1k": 2.70,    # ~97.20 บาท
                "intelligence": "maximum",
                "speed": "slow",
                "quality": "exceptional"
            }
        }
        
        # Exchange rate USD to THB
        self.usd_to_thb = 36.0
        
        # Premium features
        self.thinking_patterns = {
            "analytical": "วิเคราะห์อย่างเป็นระบบและลึกซึ้ง",
            "creative": "คิดสร้างสรรค์และมองหาแนวทางใหม่",
            "strategic": "มองภาพใหญ่และวางแผนระยะยาว",
            "critical": "ตั้งคำถามและประเมินอย่างรอบคอบ"
        }
        
    async def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """ประมวลผลด้วย Claude AI ระดับพรีเมียม"""
        
        task_type = kwargs.get('task_type', 'strategic_analysis')
        thinking_mode = kwargs.get('thinking_mode', 'analytical')
        complexity_level = kwargs.get('complexity_level', 'high')
        temperature = kwargs.get('temperature', 0.3)  # Lower for more focused output
        max_tokens = kwargs.get('max_tokens', 4000)  # Higher for detailed responses
        
        # Auto-select best model for task
        selected_model = self._select_optimal_model(task_type, complexity_level)
        
        # Get sophisticated prompts
        system_prompt = self._get_premium_system_prompt(task_type, thinking_mode)
        user_prompt = self._format_premium_user_prompt(input_data, task_type, **kwargs)
        
        try:
            response = await self._make_api_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=selected_model
            )
            
            # Advanced parsing with deep validation
            parsed_result = self._deep_parse_and_analyze(response, task_type)
            
            # Comprehensive cost analysis
            usage = response.get("usage", {})
            cost_analysis = self._calculate_premium_cost(usage, selected_model)
            
            # Quality and insight scoring
            quality_metrics = self._assess_premium_quality(parsed_result, task_type)
            
            return {
                "success": True,
                "result": parsed_result,
                "model": selected_model,
                "usage": usage,
                "cost_analysis": cost_analysis,
                "quality_metrics": quality_metrics,
                "task_type": task_type,
                "thinking_mode": thinking_mode,
                "insights_level": self._measure_insight_depth(parsed_result),
                "actionability_score": self._assess_actionability(parsed_result),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model": selected_model if 'selected_model' in locals() else self.model_name,
                "task_type": task_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def _select_optimal_model(self, task_type: str, complexity_level: str) -> str:
        """เลือก Claude model ที่เหมาะสมที่สุด"""
        
        # Ultra-complex tasks requiring maximum intelligence
        opus_tasks = [
            "business_strategy",
            "market_entry_analysis", 
            "competitive_intelligence",
            "risk_assessment_advanced"
        ]
        
        if task_type in opus_tasks or complexity_level == "maximum":
            return "claude-3-opus-20240229"
        
        # Speed-critical tasks
        if complexity_level == "fast_turnaround":
            return "claude-3-5-haiku-20241022"
        
        # Default to Sonnet for balanced premium performance
        return "claude-3-5-sonnet-20241022"
    
    def _get_premium_system_prompt(self, task_type: str, thinking_mode: str) -> str:
        """Premium system prompts with sophisticated instructions"""
        
        thinking_instruction = self.thinking_patterns.get(thinking_mode, self.thinking_patterns["analytical"])
        
        base_instruction = f"""คุณคือ AI ระดับพรีเมียมที่มีความเชี่ยวชาญเฉพาะทางสูง
รูปแบบการคิด: {thinking_instruction}
ให้การวิเคราะห์ที่ลึกซึ้ง มีข้อมูลอ้างอิง และแนวทางปฏิบัติที่ชัดเจน
ใช้หลักการ First Principles Thinking และ Systems Thinking ในการวิเคราะห์"""
        
        specific_prompts = {
            "strategic_analysis": f"""{base_instruction}
คุณคือ Strategic Analyst ระดับ C-Suite ที่มีประสบการณ์กว่า 20 ปี
เชี่ยวชาญใน: Market dynamics, Competitive positioning, Growth strategies
วิเคราะห์อย่างเป็นระบบด้วย SWOT, Porter's Five Forces, Blue Ocean Strategy
ให้ insights ที่ actionable และมี measurable outcomes""",
            
            "content_masterplan": f"""{base_instruction}
คุณคือ Content Strategy Director ที่ได้รับการยอมรับระดับโลก
เชี่ยวชาญใน: Content ecosystem design, Audience psychology, Platform algorithms
ใช้ data-driven approach ร่วมกับ creative intuition
สร้าง content strategies ที่ scalable และ sustainable""",
            
            "market_intelligence": f"""{base_instruction}
คุณคือ Market Intelligence Expert ที่เชี่ยวชาญการวิเคราะห์ตลาดเชิงลึก
เชี่ยวชาญใน: Consumer behavior, Market trends, Competitive dynamics
ใช้ quantitative และ qualitative analysis
ให้ market insights ที่มี predictive value""",
            
            "business_model_innovation": f"""{base_instruction}
คุณคือ Business Model Innovation Consultant
เชี่ยวชาญใน: Value proposition design, Revenue model optimization, Ecosystem thinking
ใช้ Canvas methodologies และ Design thinking
สร้าง business models ที่ innovative และ sustainable""",
            
            "risk_assessment_advanced": f"""{base_instruction}
คุณคือ Risk Management Expert ระดับองค์กร
เชี่ยวชาญใน: Risk identification, Impact assessment, Mitigation strategies
ใช้ probabilistic thinking และ scenario planning
ให้ risk frameworks ที่ comprehensive และ practical"""
        }
        
        return specific_prompts.get(task_type, specific_prompts["strategic_analysis"])
    
    def _format_premium_user_prompt(self, input_data: str, task_type: str, **kwargs) -> str:
        """Premium prompt formatting with advanced structure"""
        
        if task_type == "strategic_analysis":
            context = kwargs.get('context', {})
            industry = context.get('industry', 'Digital Content')
            market = context.get('market', 'Thailand')
            timeframe = context.get('timeframe', '12 months')
            resources = context.get('resources', 'Medium budget')
            
            return f"""
ดำเนินการวิเคราะห์เชิงกลยุทธ์ระดับพรีเมียมสำหรับ:

CONTEXT:
• หัวข้อ/โอกาส: {input_data}
• อุตสาหกรรม: {industry}
• ตลาดเป้าหมาย: {market}
• ระยะเวลา: {timeframe}
• ทรัพยากร: {resources}

กรุณาวิเคราะห์และส่งมอบในรูปแบบ JSON:
{{
  "executive_summary": {{
    "opportunity_overview": "สรุปโอกาสทางธุรกิจ",
    "key_insights": ["insight สำคัญ 3-5 ข้อ"],
    "recommended_approach": "แนวทางที่แนะนำ",
    "success_probability": "ความน่าจะเป็นของความสำเร็จ (%)",
    "roi_estimate": "ประมาณการ ROI"
  }},
  "market_analysis": {{
    "market_size": {{
      "total_addressable_market": "TAM ในตลาด{market}",
      "serviceable_addressable_market": "SAM ที่เข้าถึงได้",
      "serviceable_obtainable_market": "SOM ที่คาดหวัง"
    }},
    "trend_dynamics": {{
      "growth_drivers": ["ปัจจัยขับเคลื่อนการเติบโต"],
      "headwinds": ["อุปสรรคที่อาจเจอ"],
      "inflection_points": ["จุดเปลี่ยนสำคัญ"]
    }},
    "competitive_landscape": {{
      "direct_competitors": ["คู่แข่งโดยตรง"],
      "indirect_competitors": ["คู่แข่งทางอ้อม"],
      "competitive_advantages": ["จุดแข็งที่สามารถใช้ได้"],
      "barriers_to_entry": ["อุปสรรคการเข้าสู่ตลาด"]
    }}
  }},
  "strategic_options": [
    {{
      "strategy_name": "ชื่อกลยุทธ์",
      "description": "รายละเอียดกลยุทธ์",
      "investment_required": "การลงทุนที่ต้องการ",
      "timeline": "ระยะเวลาดำเนินการ",
      "expected_outcomes": ["ผลลัพธ์ที่คาดหวัง"],
      "risk_level": "ระดับความเสี่ยง (ต่ำ/กลาง/สูง)",
      "success_metrics": ["KPIs วัดความสำเร็จ"]
    }}
  ],
  "implementation_roadmap": {{
    "phase_1": {{
      "duration": "ระยะเวลา",
      "objectives": ["วัตถุประสงค์"],
      "key_activities": ["กิจกรรมหลัก"],
      "resources_needed": ["ทรัพยากรที่ต้องการ"],
      "success_criteria": ["เกณฑ์ความสำเร็จ"]
    }},
    "phase_2": {{"duration": "...", "objectives": ["..."], "key_activities": ["..."], "resources_needed": ["..."], "success_criteria": ["..."]}},
    "phase_3": {{"duration": "...", "objectives": ["..."], "key_activities": ["..."], "resources_needed": ["..."], "success_criteria": ["..."]}}
  }},
  "risk_assessment": {{
    "high_impact_risks": [
      {{
        "risk": "ความเสี่ยงที่มีผลกระทบสูง",
        "probability": "ความน่าจะเป็น (%)",
        "impact": "ระดับผลกระทบ (1-10)",
        "mitigation_strategy": "กลยุทธ์ลดความเสี่ยง"
      }}
    ],
    "contingency_plans": ["แผนสำรอง"]
  }},
  "financial_projections": {{
    "revenue_forecast": {{
      "year_1": "รายได้ปีที่ 1",
      "year_2": "รายได้ปีที่ 2",
      "year_3": "รายได้ปีที่ 3"
    }},
    "cost_structure": ["โครงสร้างค่าใช้จ่าย"],
    "break_even_analysis": "จุดคุ้มทุน",
    "sensitivity_analysis": "การวิเคราะห์ความไว"
  }},
  "success_factors": {{
    "critical_success_factors": ["ปัจจัยสำคัญต่อความสำเร็จ"],
    "key_assumptions": ["ข้อสมมติฐานสำคัญ"],
    "monitoring_framework": ["กรอบการติดตาม"]
  }},
  "next_steps": {{
    "immediate_actions": ["การกระทำที่ต้องทำทันที (1-2 สัปดาห์)"],
    "short_term_priorities": ["ลำดับความสำคัญระยะสั้น (1-3 เดือน)"],
    "decision_points": ["จุดตัดสินใจสำคัญ"]
  }}
}}
"""
        
        elif task_type == "content_masterplan":
            brand_context = kwargs.get('brand_context', {})
            budget_range = kwargs.get('budget_range', 'medium')
            goals = kwargs.get('goals', ['brand_awareness', 'engagement'])
            
            return f"""
สร้าง Content Master Plan ระดับพรีเมียมสำหรับ:

BRIEF:
• หัวข้อ/ธีม: {input_data}
• เป้าหมาย: {', '.join(goals)}
• งบประมาณ: {budget_range}
• บริบทแบรนด์: {brand_context}

ส่งมอบ Comprehensive Plan ในรูปแบบ JSON:
{{
  "content_strategy_overview": {{
    "strategic_positioning": "การวางตำแหน่งเชิงกลยุทธ์",
    "unique_value_proposition": "ข้อเสนอคุณค่าที่เป็นเอกลักษณ์",
    "content_philosophy": "ปรัชญาการสร้างเนื้อหา",
    "success_definition": "นิยามความสำเร็จ"
  }},
  "audience_intelligence": {{
    "primary_personas": [
      {{
        "persona_name": "ชื่อ Persona",
        "demographics": "ข้อมูลประชากรศาสตร์",
        "psychographics": "ลักษณะทางจิตวิทยา",
        "content_preferences": "ความชอบเนื้อหา",
        "platform_behavior": "พฤติกรรมบน Platform",
        "pain_points": ["จุดเจ็บปวด"],
        "content_journey": "เส้นทางการบริโภคเนื้อหา"
      }}
    ],
    "audience_insights": ["ข้อมูลเชิงลึกเกี่ยวกับผู้ชม"]
  }},
  "content_ecosystem": {{
    "content_pillars": [
      {{
        "pillar_name": "เสาหลักเนื้อหา",
        "purpose": "วัตถุประสงค์",
        "content_types": ["ประเภทเนื้อหา"],
        "tone_and_style": "โทนและสไตล์",
        "success_metrics": ["ตัวชี้วัดความสำเร็จ"],
        "percentage_allocation": 30
      }}
    ],
    "content_mix_strategy": {{
      "educational": 40,
      "entertainment": 30,
      "inspirational": 20,
      "promotional": 10
    }}
  }},
  "platform_strategy": {{
    "platform_priorities": [
      {{
        "platform": "ชื่อ Platform",
        "strategic_role": "บทบาทเชิงกลยุทธ์",
        "content_adaptation": "การปรับเนื้อหา",
        "posting_frequency": "ความถี่การโพสต์",
        "engagement_tactics": ["กลยุทธ์ Engagement"],
        "growth_targets": "เป้าหมายการเติบโต"
      }}
    ],
    "cross_platform_synergy": "การประสานงานข้าม Platform"
  }},
  "content_calendar_framework": {{
    "quarterly_themes": [
      {{
        "quarter": "Q1",
        "theme": "ธีมหลัก",
        "key_campaigns": ["แคมเปญสำคัญ"],
        "seasonal_opportunities": ["โอกาสตามฤดูกาล"]
      }}
    ],
    "monthly_content_flow": {{
      "week_1": "โฟกัสสัปดาห์ที่ 1",
      "week_2": "โฟกัสสัปดาห์ที่ 2", 
      "week_3": "โฟกัสสัปดาห์ที่ 3",
      "week_4": "โฟกัสสัปดาห์ที่ 4"
    }}
  }},
  "content_production_system": {{
    "content_workflows": [
      {{
        "content_type": "ประเภทเนื้อหา",
        "production_process": ["ขั้นตอนการผลิต"],
        "timeline": "ระยะเวลาผลิต",
        "resources_required": ["ทรัพยากรที่ต้องการ"],
        "quality_checkpoints": ["จุดตรวจสอบคุณภาพ"]
      }}
    ],
    "content_repurposing_matrix": "แผนการนำเนื้อหากลับมาใช้ใหม่"
  }},
  "engagement_amplification": {{
    "community_building_tactics": ["กลยุทธ์สร้างชุมชน"],
    "influencer_collaboration_strategy": "กลยุทธ์ร่วมงาน Influencer",
    "user_generated_content_framework": "กรอบการสร้าง UGC",
    "viral_content_principles": ["หลักการสร้างเนื้อหาไวรัล"]
  }},
  "performance_measurement": {{
    "kpi_framework": [
      {{
        "category": "หมวดหมู่ KPI",
        "metrics": ["ตัวชี้วัด"],
        "targets": ["เป้าหมาย"],
        "measurement_frequency": "ความถี่การวัด"
      }}
    ],
    "attribution_model": "โมเดลการกำหนดส่วนแบ่ง",
    "optimization_triggers": ["จุดที่ต้อง Optimize"]
  }},
  "budget_allocation": {{
    "content_production": "สัดส่วนงบผลิตเนื้อหา (%)",
    "paid_promotion": "สัดส่วนงบโฆษณา (%)",
    "tools_and_software": "สัดส่วนงบเครื่องมือ (%)",
    "talent_and_resources": "สัดส่วนงบบุคลากร (%)"
  }},
  "innovation_opportunities": {{
    "emerging_formats": ["รูปแบบเนื้อหาใหม่"],
    "technology_integration": ["การใช้เทคโนโลยี"],
    "experimental_initiatives": ["โครงการทดลอง"]
  }}
}}
"""
        
        return input_data
    
    async def _make_api_call(self, system_prompt: str, user_prompt: str,
                           temperature: float = 0.3, max_tokens: int = 4000,
                           model: str = None) -> Dict[str, Any]:
        """เรียก Claude API with premium configuration"""
        
        if model is None:
            model = self.model_name
            
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/messages",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=90)  # Longer timeout for complex tasks
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
                            raise Exception(f"Claude API error {response.status}: {error_text}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise Exception("Claude API timeout after all retries")
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Claude API call failed (attempt {attempt + 1}): {str(e)}")
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise
        
        raise Exception("Claude API call failed after all retries")
    
    def _deep_parse_and_analyze(self, response: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Advanced parsing with deep content analysis"""
        
        try:
            content = response["content"][0]["text"]
            
            # Try JSON parsing
            try:
                parsed = json.loads(content)
                
                # Deep structure validation
                structure_score = self._validate_deep_structure(parsed, task_type)
                
                # Content richness analysis
                richness_score = self._analyze_content_richness(parsed)
                
                # Actionability assessment
                actionability_score = self._assess_content_actionability(parsed)
                
                return {
                    "content": parsed,
                    "parsing_success": True,
                    "structure_score": structure_score,
                    "richness_score": richness_score,
                    "actionability_score": actionability_score,
                    "total_words": len(content.split()),
                    "json_complexity": self._measure_json_complexity(parsed)
                }
                
            except json.JSONDecodeError:
                # Advanced text analysis for non-JSON
                return {
                    "content": content,
                    "parsing_success": False,
                    "text_analysis": self._analyze_text_quality(content),
                    "total_words": len(content.split()),
                    "readability_score": self._assess_readability(content)
                }
                
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Claude response structure: {e}")
            return {
                "error": "Unexpected response structure",
                "raw_response": response,
                "parsing_success": False
            }
    
    def _validate_deep_structure(self, parsed: Dict[str, Any], task_type: str) -> int:
        """Deep validation of response structure (0-100)"""
        
        expected_structures = {
            "strategic_analysis": [
                "executive_summary", "market_analysis", "strategic_options",
                "implementation_roadmap", "risk_assessment", "financial_projections"
            ],
            "content_masterplan": [
                "content_strategy_overview", "audience_intelligence", "content_ecosystem",
                "platform_strategy", "performance_measurement"
            ]
        }
        
        expected = expected_structures.get(task_type, [])
        if not expected:
            return 50  # Default score for unknown task types
        
        score = 0
        for field in expected:
            if field in parsed:
                score += (100 // len(expected))
                
                # Bonus for nested complexity
                if isinstance(parsed[field], dict) and len(parsed[field]) > 2:
                    score += 5
                elif isinstance(parsed[field], list) and len(parsed[field]) > 0:
                    score += 5
        
        return min(score, 100)
    
    def _analyze_content_richness(self, content: Union[Dict, str]) -> int:
        """Analyze richness and depth of content (0-100)"""
        
        if isinstance(content, str):
            words = len(content.split())
            return min(words // 10, 100)  # Simple word count for text
        
        if not isinstance(content, dict):
            return 20
        
        richness = 0
        
        # Count nested levels
        def count_depth(obj, current_depth=0):
            if current_depth > 10:  # Prevent infinite recursion
                return current_depth
            if isinstance(obj, dict):
                return max([count_depth(v, current_depth + 1) for v in obj.values()] + [current_depth])
            elif isinstance(obj, list) and obj:
                return max([count_depth(item, current_depth + 1) for item in obj] + [current_depth])
            return current_depth
        
        depth = count_depth(content)
        richness += min(depth * 10, 40)
        
        # Count total fields
        total_fields = self._count_all_fields(content)
        richness += min(total_fields * 2, 30)
        
        # Check for lists and detailed content
        list_bonus = self._count_lists_and_arrays(content)
        richness += min(list_bonus * 3, 30)
        
        return min(richness, 100)
    
    def _assess_content_actionability(self, content: Union[Dict, str]) -> int:
        """Assess how actionable the content is (0-100)"""
        
        if isinstance(content, str):
            actionable_keywords = ["step", "action", "implement", "execute", "plan", "strategy", "วิธี", "แผน", "กลยุทธ์"]
            found_keywords = sum(1 for keyword in actionable_keywords if keyword.lower() in content.lower())
            return min(found_keywords * 10, 100)
        
        if not isinstance(content, dict):
            return 20
        
        actionability = 0
        
        # Look for implementation-related sections
        actionable_sections = [
            "implementation", "roadmap", "next_steps", "action_plan", 
            "recommendations", "strategy", "tactics"
        ]
        
        content_str = str(content).lower()
        for section in actionable_sections:
            if section in content_str:
                actionability += 15
        
        # Look for specific actionable elements
        actionable_elements = [
            "timeline", "budget", "resources", "metrics", "kpi",
            "deliverable", "milestone", "target", "goal"
        ]
        
        for element in actionable_elements:
            if element in content_str:
                actionability += 8
        
        return min(actionability, 100)
    
    def _calculate_premium_cost(self, usage: Dict[str, Any], model: str) -> Dict[str, Any]:
        """คำนวณต้นทุนพรีเมียมแบบละเอียด"""
        
        model_config = self.models.get(model, self.models["claude-3-5-sonnet-20241022"])
        
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        # Calculate costs in USD
        input_cost_usd = (input_tokens / 1000) * model_config["input_cost_per_1k"]
        output_cost_usd = (output_tokens / 1000) * model_config["output_cost_per_1k"]
        total_cost_usd = input_cost_usd + output_cost_usd
        
        # Convert to THB
        input_cost_thb = input_cost_usd * self.usd_to_thb
        output_cost_thb = output_cost_usd * self.usd_to_thb
        total_cost_thb = total_cost_usd * self.usd_to_thb
        
        # Value analysis
        cost_per_word = total_cost_thb / max(output_tokens * 0.75, 1)  # Approximate words
        value_tier = "high" if cost_per_word < 0.1 else "premium" if cost_per_word < 0.5 else "ultra_premium"
        
        return {
            "model": model,
            "model_tier": model_config.get("intelligence", "high"),
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "costs": {
                "input_usd": round(input_cost_usd, 6),
                "output_usd": round(output_cost_usd, 6),
                "total_usd": round(total_cost_usd, 6),
                "input_thb": round(input_cost_thb, 4),
                "output_thb": round(output_cost_thb, 4),
                "total_thb": round(total_cost_thb, 4)
            },
            "value_metrics": {
                "cost_per_word_thb": round(cost_per_word, 4),
                "value_tier": value_tier,
                "cost_efficiency": "excellent" if cost_per_word < 0.2 else "good"
            },
            "rate_usd_to_thb": self.usd_to_thb
        }
    
    def _assess_premium_quality(self, result: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """ประเมินคุณภาพระดับพรีเมียม"""
        
        quality_metrics = {
            "parsing_quality": 0,
            "content_depth": 0,
            "structure_quality": 0,
            "actionability": 0,
            "insight_level": 0,
            "overall_quality": 0
        }
        
        if not result.get("parsing_success", False):
            quality_metrics["parsing_quality"] = 30
            quality_metrics["overall_quality"] = 30
            return quality_metrics
        
        # Parsing quality
        quality_metrics["parsing_quality"] = 95 if result.get("parsing_success") else 20
        
        # Content depth (from richness score)
        quality_metrics["content_depth"] = result.get("richness_score", 50)
        
        # Structure quality
        quality_metrics["structure_quality"] = result.get("structure_score", 50)
        
        # Actionability
        quality_metrics["actionability"] = result.get("actionability_score", 50)
        
        # Insight level (premium feature)
        quality_metrics["insight_level"] = self._measure_insight_depth(result)
        
        # Overall quality (weighted average)
        weights = {
            "parsing_quality": 0.1,
            "content_depth": 0.25,
            "structure_quality": 0.2,
            "actionability": 0.25,
            "insight_level": 0.2
        }
        
        overall = sum(quality_metrics[key] * weights[key] for key in weights)
        quality_metrics["overall_quality"] = round(overall, 1)
        
        # Quality tier
        if overall >= 85:
            tier = "exceptional"
        elif overall >= 75:
            tier = "excellent"
        elif overall >= 65:
            tier = "very_good"
        elif overall >= 50:
            tier = "good"
        else:
            tier = "needs_improvement"
        
        quality_metrics["quality_tier"] = tier
        
        return quality_metrics
    
    def _measure_insight_depth(self, result: Dict[str, Any]) -> int:
        """วัดระดับความลึกซึ้งของ insights (0-100)"""
        
        if not result.get("parsing_success", False):
            return 20
        
        content = result.get("content", {})
        if isinstance(content, str):
            # Count insight indicators in text
            insight_keywords = [
                "insight", "analysis", "pattern", "trend", "implication",
                "opportunity", "risk", "strategy", "recommendation",
                "ข้อมูลเชิงลึก", "การวิเคราะห์", "แนวโน้ม", "โอกาส", "ความเสี่ยง"
            ]
            
            content_lower = content.lower()
            found_insights = sum(1 for keyword in insight_keywords if keyword in content_lower)
            return min(found_insights * 8, 100)
        
        if not isinstance(content, dict):
            return 30
        
        insight_score = 0
        
        # Look for analytical sections
        analytical_sections = [
            "analysis", "insights", "implications", "recommendations",
            "strategic_options", "market_analysis", "competitive_landscape"
        ]
        
        content_str = str(content).lower()
        for section in analytical_sections:
            if section in content_str:
                insight_score += 12
        
        # Look for forward-looking elements
        strategic_elements = [
            "forecast", "prediction", "scenario", "opportunity", "risk",
            "trend", "future", "roadmap", "strategy"
        ]
        
        for element in strategic_elements:
            if element in content_str:
                insight_score += 8
        
        return min(insight_score, 100)
    
    def _assess_actionability(self, result: Dict[str, Any]) -> int:
        """ประเมินความสามารถในการนำไปปฏิบัติ (0-100)"""
        
        if not result.get("parsing_success", False):
            return 25
        
        return result.get("actionability_score", 50)
    
    def _count_all_fields(self, obj: Any) -> int:
        """นับจำนวน fields ทั้งหมดใน nested object"""
        
        if isinstance(obj, dict):
            return len(obj) + sum(self._count_all_fields(v) for v in obj.values())
        elif isinstance(obj, list):
            return sum(self._count_all_fields(item) for item in obj)
        return 0
    
    def _count_lists_and_arrays(self, obj: Any) -> int:
        """นับจำนวน lists และ arrays"""
        
        count = 0
        if isinstance(obj, dict):
            for v in obj.values():
                if isinstance(v, list):
                    count += len(v)
                count += self._count_lists_and_arrays(v)
        elif isinstance(obj, list):
            count += len(obj)
            for item in obj:
                count += self._count_lists_and_arrays(item)
        return count
    
    def _measure_json_complexity(self, obj: Any) -> Dict[str, int]:
        """วัดความซับซ้อนของ JSON structure"""
        
        def get_max_depth(obj, depth=0):
            if isinstance(obj, dict):
                return max([get_max_depth(v, depth + 1) for v in obj.values()] + [depth])
            elif isinstance(obj, list) and obj:
                return max([get_max_depth(item, depth + 1) for item in obj] + [depth])
            return depth
        
        return {
            "max_depth": get_max_depth(obj),
            "total_fields": self._count_all_fields(obj),
            "total_arrays": self._count_lists_and_arrays(obj),
            "complexity_score": min(get_max_depth(obj) * 10 + self._count_all_fields(obj), 100)
        }
    
    def _analyze_text_quality(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์คุณภาพของข้อความ"""
        
        words = text.split()
        sentences = text.split('.')
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_words_per_sentence": round(len(words) / max(len(sentences), 1), 1),
            "has_structure": "##" in text or "**" in text or "•" in text,
            "detail_level": "high" if len(words) > 500 else "medium" if len(words) > 200 else "low"
        }
    
    def _assess_readability(self, text: str) -> int:
        """ประเมินความสามารถในการอ่าน (0-100)"""
        
        words = text.split()
        sentences = text.split('.')
        
        if not sentences:
            return 50
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Simple readability score
        if avg_sentence_length < 15:
            return 85
        elif avg_sentence_length < 25:
            return 70
        elif avg_sentence_length < 35:
            return 55
        else:
            return 40
    
    async def strategic_deep_dive(self, topic: str, **kwargs) -> Dict[str, Any]:
        """การวิเคราะห์เชิงกลยุทธ์แบบลึกพิเศษ"""
        
        return await self.process(
            topic,
            task_type="strategic_analysis",
            thinking_mode="strategic",
            complexity_level="maximum",
            temperature=0.2,  # More focused
            max_tokens=4000,
            **kwargs
        )
    
    async def content_masterplan_creation(self, theme: str, **kwargs) -> Dict[str, Any]:
        """สร้าง Content Master Plan ระดับมืออาชีพ"""
        
        return await self.process(
            theme,
            task_type="content_masterplan",
            thinking_mode="creative",
            complexity_level="high",
            temperature=0.4,  # More creative
            max_tokens=4000,
            **kwargs
        )
    
    async def competitive_intelligence_analysis(self, market_context: str, **kwargs) -> Dict[str, Any]:
        """การวิเคราะห์คู่แข่งระดับ Intelligence"""
        
        return await self.process(
            market_context,
            task_type="market_intelligence", 
            thinking_mode="analytical",
            complexity_level="high",
            temperature=0.3,
            max_tokens=3500,
            **kwargs
        )
    
    def get_premium_capabilities(self) -> Dict[str, Any]:
        """ความสามารถระดับพรีเมียมของ Claude"""
        
        return {
            "model_capabilities": {
                "context_window": "200K tokens",
                "reasoning_depth": "Advanced multi-step reasoning",
                "analysis_quality": "Strategic-level insights",
                "language_understanding": "Nuanced context comprehension"
            },
            "premium_features": {
                "strategic_analysis": "C-level strategic planning",
                "content_masterplanning": "Enterprise content strategy",
                "market_intelligence": "Deep market analysis",
                "risk_assessment": "Comprehensive risk modeling",
                "innovation_consulting": "Business model innovation"
            },
            "quality_guarantees": {
                "insight_depth": "90%+ actionable insights",
                "structure_completeness": "95%+ comprehensive frameworks",
                "strategic_value": "Executive-ready deliverables",
                "implementation_focus": "Practical action plans"
            },
            "cost_value_proposition": {
                "cost_per_insight": "Premium pricing for premium quality",
                "roi_potential": "High-value strategic guidance",
                "expertise_level": "Consultant-grade analysis",
                "time_savings": "Weeks of research in minutes"
            }
        }
    
    def optimize_for_task(self, task_type: str) -> Dict[str, Any]:
        """เลือกการตั้งค่าที่เหมาะสมสำหรับแต่ละงาน"""
        
        optimizations = {
            "strategic_analysis": {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.2,
                "thinking_mode": "strategic",
                "max_tokens": 4000
            },
            "content_masterplan": {
                "model": "claude-3-5-sonnet-20241022", 
                "temperature": 0.4,
                "thinking_mode": "creative",
                "max_tokens": 4000
            },
            "market_intelligence": {
                "model": "claude-3-opus-20240229",  # Use most powerful for complex analysis
                "temperature": 0.1,
                "thinking_mode": "analytical",
                "max_tokens": 3500
            },
            "business_model_innovation": {
                "model": "claude-3-opus-20240229",
                "temperature": 0.5,
                "thinking_mode": "creative",
                "max_tokens": 4000
            }
        }
        
        return optimizations.get(task_type, optimizations["strategic_analysis"])

# Example usage
async def test_claude_premium():
    """ทดสอบ Claude Premium Service"""
    service = ClaudeService("your-claude-api-key")
    
    # Test strategic analysis
    strategic_result = await service.strategic_deep_dive(
        "การเข้าสู่ตลาด Short Video Content ในประเทศไทย",
        context={
            "industry": "Digital Media",
            "market": "Thailand", 
            "timeframe": "18 months",
            "resources": "2M THB budget"
        }
    )
    
    print("Strategic Deep Dive Result:")
    print(f"Quality Score: {strategic_result['quality_metrics']['overall_quality']}/100")
    print(f"Cost: ฿{strategic_result['cost_analysis']['costs']['total_thb']}")
    print(f"Insight Level: {strategic_result['insights_level']}/100")
    
    # Test content masterplan
    content_plan = await service.content_masterplan_creation(
        "Sustainable Living สำหรับคนรุ่นใหม่",
        brand_context={"values": "sustainability", "target": "Gen Z"},
        budget_range="high",
        goals=["brand_awareness", "community_building", "thought_leadership"]
    )
    
    print("\nContent Masterplan Result:")
    print(f"Quality Score: {content_plan['quality_metrics']['overall_quality']}/100")
    print(f"Actionability: {content_plan['actionability_score']}/100")
    
    # Show capabilities
    print("\nPremium Capabilities:")
    capabilities = service.get_premium_capabilities()
    print(json.dumps(capabilities, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_claude_premium())