"""
Advanced Trend Analyzer - ระบบวิเคราะห์เทรนด์ขั้นสูง
รวม AI analysis, competitive intelligence, และ predictive modeling
สำหรับการตัดสินใจสร้างเนื้อหาที่แม่นยำ
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib

from .service_registry import ServiceRegistry, ServiceType, QualityTier, get_service_registry
from .models.content_plan import ContentOpportunity, ContentMetrics

logger = logging.getLogger(__name__)

class TrendLifecycle(Enum):
    """วงจรชีวิตเทรนด์"""
    EMERGING = "emerging"      # เพิ่งเกิดขึ้น, โอกาสสูง
    GROWING = "growing"        # กำลังโต, แข่งขันปานกลาง
    PEAK = "peak"             # จุดสูงสุด, แข่งขันสูง
    DECLINING = "declining"    # กำลังลด, ควรหลีกเลี่ยง
    STABLE = "stable"         # คงที่, evergreen content

class CompetitionLevel(Enum):
    """ระดับการแข่งขัน"""
    LOW = "low"               # แข่งขันน้อย, โอกาสดี
    MEDIUM = "medium"         # แข่งขันปานกลาง
    HIGH = "high"            # แข่งขันสูง, ต้องมีความเป็นเอกลักษณ์
    SATURATED = "saturated"   # อิ่มตัว, ยากเข้าสู่ตลาด

class TrendOrigin(Enum):
    """แหล่งที่มาของเทรนด์"""
    ORGANIC = "organic"           # เกิดขึ้นเอง
    ALGORITHM_DRIVEN = "algorithm_driven"  # ขับเคลื่อนโดย algorithm
    INFLUENCER_LED = "influencer_led"      # นำโดย influencers
    BRAND_SPONSORED = "brand_sponsored"    # สนับสนุนโดยแบรนด์
    NEWS_EVENT = "news_event"             # เหตุการณ์ข่าว
    SEASONAL = "seasonal"                 # ตามฤดูกาล

@dataclass
class TrendMetrics:
    """ตัวชี้วัดเทรนด์"""
    # Volume metrics
    search_volume: int = 0
    social_mentions: int = 0
    video_count: int = 0
    view_count: int = 0
    
    # Growth metrics
    growth_rate_daily: float = 0.0
    growth_rate_weekly: float = 0.0
    momentum_score: float = 0.0  # 0-10
    
    # Engagement metrics
    avg_engagement_rate: float = 0.0
    share_rate: float = 0.0
    comment_sentiment: float = 0.0  # -1 to 1
    
    # Competition metrics
    creator_count: int = 0
    top_creator_dominance: float = 0.0  # 0-1
    content_saturation: float = 0.0     # 0-10
    
    # Predictive metrics
    predicted_peak_date: Optional[str] = None
    estimated_lifespan_days: Optional[int] = None
    viral_coefficient: float = 0.0      # 0-10

@dataclass
class CompetitorAnalysis:
    """การวิเคราะห์คู่แข่ง"""
    competitor_name: str
    platform: str
    content_type: str
    view_count: int = 0
    engagement_rate: float = 0.0
    follower_count: int = 0
    content_angle: str = ""
    unique_elements: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    content_frequency: str = ""
    estimated_budget: str = "unknown"

@dataclass
class TrendAnalysisResult:
    """ผลการวิเคราะห์เทรนด์"""
    # Basic info
    trend_id: str
    trend_name: str
    keywords: List[str]
    platforms: List[str]
    detected_at: datetime
    
    # Classification
    lifecycle_stage: TrendLifecycle
    competition_level: CompetitionLevel
    trend_origin: TrendOrigin
    category: str
    
    # Metrics
    metrics: TrendMetrics
    
    # Opportunity analysis
    opportunity_score: float = 0.0       # 0-10, overall opportunity
    viral_potential: float = 0.0         # 0-10, viral potential
    monetization_potential: float = 0.0  # 0-10, money-making potential
    content_gap_score: float = 0.0       # 0-10, content gap opportunity
    
    # Competitive landscape
    competitors: List[CompetitorAnalysis] = field(default_factory=list)
    market_gaps: List[str] = field(default_factory=list)
    differentiation_opportunities: List[str] = field(default_factory=list)
    
    # Recommendations
    recommended_content_angles: List[Dict[str, Any]] = field(default_factory=list)
    platform_priorities: Dict[str, float] = field(default_factory=dict)  # platform: priority_score
    timing_recommendations: Dict[str, Any] = field(default_factory=dict)
    
    # Risk assessment
    risk_factors: List[str] = field(default_factory=list)
    success_probability: float = 0.0     # 0-1
    confidence_level: float = 0.0        # 0-1, confidence in analysis
    
    # Analysis metadata
    analysis_quality: str = "standard"   # basic, standard, premium
    data_sources: List[str] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

class TrendAnalyzer:
    """
    Advanced Trend Analyzer - ระบบวิเคราะห์เทรนด์ขั้นสูง
    ใช้ AI ร่วมกับ heuristics เพื่อวิเคราะห์โอกาสทางธุรกิจ
    """
    
    def __init__(self, service_registry: Optional[ServiceRegistry] = None):
        self.registry = service_registry or get_service_registry()
        self.analysis_cache = {}  # Cache for expensive analyses
        
        # Trend scoring weights
        self.scoring_weights = {
            "growth_momentum": 0.25,
            "engagement_quality": 0.20,
            "competition_gap": 0.20,
            "viral_indicators": 0.15,
            "monetization_signals": 0.10,
            "timing_advantage": 0.10
        }
        
        # Platform characteristics
        self.platform_characteristics = {
            "TikTok": {
                "optimal_lifecycle": [TrendLifecycle.EMERGING, TrendLifecycle.GROWING],
                "content_velocity": "very_high",
                "viral_coefficient": 1.5,
                "competition_threshold": 0.7
            },
            "YouTube": {
                "optimal_lifecycle": [TrendLifecycle.GROWING, TrendLifecycle.PEAK],
                "content_velocity": "medium",
                "viral_coefficient": 1.0,
                "competition_threshold": 0.5
            },
            "Instagram": {
                "optimal_lifecycle": [TrendLifecycle.GROWING, TrendLifecycle.STABLE],
                "content_velocity": "medium",
                "viral_coefficient": 1.2,
                "competition_threshold": 0.6
            }
        }
    
    async def analyze_trend_comprehensive(self, trend_data: str, 
                                        target_platforms: List[str],
                                        analysis_depth: str = "standard") -> TrendAnalysisResult:
        """การวิเคราะห์เทรนด์แบบครอบคลุม"""
        
        logger.info(f"Starting comprehensive trend analysis: {trend_data[:50]}...")
        
        # Generate unique trend ID
        trend_id = self._generate_trend_id(trend_data)
        
        # Check cache first
        cache_key = f"{trend_id}_{analysis_depth}_{'_'.join(sorted(target_platforms))}"
        if cache_key in self.analysis_cache:
            cached_result = self.analysis_cache[cache_key]
            if datetime.now() - cached_result.analysis_timestamp < timedelta(hours=6):
                logger.info("Returning cached trend analysis")
                return cached_result
        
        try:
            # Step 1: Basic AI Analysis
            ai_analysis = await self._perform_ai_analysis(trend_data, target_platforms, analysis_depth)
            
            # Step 2: Enhanced Analysis for higher tiers
            if analysis_depth in ["premium", "enterprise"]:
                competitive_analysis = await self._analyze_competitive_landscape(trend_data, target_platforms)
                market_gaps = await self._identify_market_gaps(ai_analysis, competitive_analysis)
                predictive_insights = await self._generate_predictive_insights(ai_analysis, trend_data)
            else:
                competitive_analysis = []
                market_gaps = []
                predictive_insights = {}
            
            # Step 3: Compile comprehensive result
            result = await self._compile_analysis_result(
                trend_id=trend_id,
                trend_data=trend_data,
                target_platforms=target_platforms,
                ai_analysis=ai_analysis,
                competitive_analysis=competitive_analysis,
                market_gaps=market_gaps,
                predictive_insights=predictive_insights,
                analysis_depth=analysis_depth
            )
            
            # Step 4: Calculate opportunity scores
            result = self._calculate_opportunity_scores(result)
            
            # Step 5: Generate actionable recommendations
            result = await self._generate_actionable_recommendations(result, target_platforms)
            
            # Cache the result
            result.expires_at = datetime.now() + timedelta(hours=12)
            self.analysis_cache[cache_key] = result
            
            logger.info(f"Trend analysis completed. Opportunity score: {result.opportunity_score:.1f}/10")
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive trend analysis: {str(e)}")
            return self._create_fallback_analysis(trend_data, target_platforms)
    
    async def _perform_ai_analysis(self, trend_data: str, platforms: List[str], depth: str) -> Dict[str, Any]:
        """การวิเคราะห์ด้วย AI"""
        
        # Select AI tier based on analysis depth
        ai_tier = {
            "basic": QualityTier.BUDGET,
            "standard": QualityTier.BALANCED,
            "premium": QualityTier.PREMIUM,
            "enterprise": QualityTier.PREMIUM
        }.get(depth, QualityTier.BALANCED)
        
        # Enhanced prompt for deeper analysis
        analysis_prompt = self._create_analysis_prompt(trend_data, platforms, depth)
        
        try:
            ai_result = await self.registry.process_with_best_service(
                ServiceType.TEXT_AI,
                analysis_prompt,
                task_type="trend_analysis" if ai_tier != QualityTier.PREMIUM else "strategic_analysis",
                quality_tier=ai_tier,
                context={
                    "platforms": platforms,
                    "analysis_depth": depth,
                    "market": "Thailand"
                }
            )
            
            if ai_result.get("success", False):
                return ai_result.get("result", {})
            else:
                logger.warning(f"AI analysis failed: {ai_result.get('error')}")
                return self._create_basic_analysis(trend_data, platforms)
                
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return self._create_basic_analysis(trend_data, platforms)
    
    def _create_analysis_prompt(self, trend_data: str, platforms: List[str], depth: str) -> str:
        """สร้าง prompt สำหรับการวิเคราะห์"""
        
        if depth == "premium":
            return f"""
ดำเนินการวิเคราะห์เทรนด์ระดับพรีเมียมสำหรับ:

TREND: {trend_data}
TARGET PLATFORMS: {', '.join(platforms)}
MARKET: Thailand

กรุณาวิเคราะห์อย่างลึกซึ้งและส่งมอบใน JSON format:
{{
  "trend_classification": {{
    "primary_category": "หมวดหมู่หลัก",
    "sub_categories": ["หมวดย่อย"],
    "lifecycle_stage": "emerging/growing/peak/declining/stable",
    "trend_origin": "organic/algorithm_driven/influencer_led/brand_sponsored/news_event/seasonal",
    "geographic_relevance": "ความเกี่ยวข้องกับไทย (1-10)"
  }},
  "market_dynamics": {{
    "current_momentum": "แรงโมเมนตัมปัจจุบัน (1-10)",
    "growth_trajectory": "predicted growth pattern",
    "peak_estimation": "predicted peak timeframe",
    "saturation_indicators": ["สัญญาณความอิ่มตัว"],
    "market_size_estimate": "ขนาดตลาดโดยประมาณ"
  }},
  "competitive_landscape": {{
    "competition_intensity": "low/medium/high/saturated",
    "dominant_players": ["ผู้เล่นหลัก"],
    "content_saturation": "ระดับความอิ่มตัวเนื้อหา (1-10)",
    "differentiation_opportunities": ["โอกาสสร้างความแตกต่าง"],
    "market_gaps": ["ช่องว่างในตลาด"]
  }},
  "platform_analysis": {{
    "platform_suitability": {{
      "TikTok": {{"score": 8, "reasons": ["เหตุผล"], "optimal_format": "รูปแบบที่เหมาะสม"}},
      "YouTube": {{"score": 6, "reasons": ["เหตุผล"], "optimal_format": "รูปแบบที่เหมาะสม"}},
      "Instagram": {{"score": 7, "reasons": ["เหตุผล"], "optimal_format": "รูปแบบที่เหมาะสม"}}
    }},
    "cross_platform_strategy": "กลยุทธ์ข้าม platform"
  }},
  "content_opportunities": [
    {{
      "angle": "มุมมองเนื้อหา",
      "unique_value_proposition": "ข้อเสนอคุณค่าเฉพาะ",
      "target_audience_segment": "กลุ่มเป้าหมายเฉพาะ",
      "content_format": "รูปแบบเนื้อหา",
      "viral_potential": "โอกาสไวรัล (1-10)",
      "production_complexity": "easy/medium/hard",
      "estimated_reach": "การเข้าถึงที่คาดหวัง",
      "monetization_potential": "โอกาสสร้างรายได้ (1-10)"
    }}
  ],
  "risk_assessment": {{
    "trend_longevity_risk": "ความเสี่ยงอายุสั้น",
    "competition_risk": "ความเสี่ยงจากคู่แข่ง",
    "platform_algorithm_risk": "ความเสี่ยง algorithm",
    "content_policy_risk": "ความเสี่ยงนโยบาย platform",
    "overall_risk_level": "low/medium/high"
  }},
  "timing_strategy": {{
    "immediate_opportunity_window": "หน้าต่างโอกาสทันที",
    "optimal_launch_timing": "เวลาเปิดตัวที่เหมาะสม",
    "content_frequency_recommendation": "ความถี่เนื้อหาที่แนะนำ",
    "seasonal_considerations": "ข้อพิจารณาตามฤดูกาล"
  }},
  "success_metrics": {{
    "primary_kpis": ["KPI หลัก"],
    "engagement_benchmarks": "มาตรฐาน engagement",
    "growth_targets": "เป้าหมายการเติบโต",
    "roi_expectations": "ความคาดหวัง ROI"
  }},
  "actionable_insights": {{
    "immediate_actions": ["การกระทำทันที (1-3 วัน)"],
    "short_term_strategy": ["กลยุทธ์ระยะสั้น (1-2 สัปดาห์)"],
    "long_term_positioning": ["การวางตำแหน่งระยะยาว"],
    "key_success_factors": ["ปัจจัยสำคัญต่อความสำเร็จ"]
  }}
}}
"""
        else:
            # Standard analysis prompt
            return f"""
วิเคราะห์เทรนด์นี้สำหรับการสร้างเนื้อหา:

เทรนด์: {trend_data}
แพลตฟอร์มเป้าหมาย: {', '.join(platforms)}

ให้ผลลัพธ์ใน JSON:
{{
  "trend_name": "ชื่อเทรนด์",
  "lifecycle_stage": "emerging/growing/peak/declining",
  "scores": {{
    "viral_potential": 8,
    "content_saturation": 3,
    "audience_interest": 9,
    "monetization_opportunity": 7,
    "competition_level": 5
  }},
  "content_angles": [
    "มุมมอง 1: ...",
    "มุมมอง 2: ...",
    "มุมมอง 3: ..."
  ],
  "platform_suitability": {{
    "TikTok": 8,
    "YouTube": 6,
    "Instagram": 7
  }},
  "risks": ["ความเสี่ยง"],
  "recommendations": ["คำแนะนำ"],
  "optimal_timing": "เวลาที่เหมาะสม"
}}
"""
    
    async def _analyze_competitive_landscape(self, trend_data: str, platforms: List[str]) -> List[CompetitorAnalysis]:
        """วิเคราะห์ภูมิทัศน์การแข่งขัน"""
        
        try:
            competitor_prompt = f"""
วิเคราะห์คู่แข่งในเทรนด์: {trend_data}
แพลตฟอร์ม: {', '.join(platforms)}

ให้รายชื่อและวิเคราะห์คู่แข่งหลัก 5-8 รายใน JSON:
{{
  "competitors": [
    {{
      "name": "ชื่อ creator/channel",
      "platform": "platform หลัก",
      "content_type": "ประเภทเนื้อหา",
      "estimated_views": 100000,
      "engagement_rate": 5.5,
      "content_angle": "มุมมองเนื้อหา",
      "strengths": ["จุดแข็ง"],
      "weaknesses": ["จุดอ่อน"],
      "unique_elements": ["องค์ประกอบเฉพาะตัว"],
      "posting_frequency": "ความถี่การโพสต์"
    }}
  ],
  "market_gaps": ["ช่องว่างที่พบ"],
  "opportunities": ["โอกาสที่สามารถใช้ประโยชน์ได้"]
}}
"""
            
            result = await self.registry.process_with_best_service(
                ServiceType.TEXT_AI,
                competitor_prompt,
                task_type="competition_analysis"
            )
            
            if result.get("success", False):
                competitor_data = result.get("result", {}).get("content", {})
                
                # Convert to CompetitorAnalysis objects
                competitors = []
                for comp_data in competitor_data.get("competitors", []):
                    competitor = CompetitorAnalysis(
                        competitor_name=comp_data.get("name", "Unknown"),
                        platform=comp_data.get("platform", "Unknown"),
                        content_type=comp_data.get("content_type", "video"),
                        view_count=comp_data.get("estimated_views", 0),
                        engagement_rate=comp_data.get("engagement_rate", 0.0),
                        content_angle=comp_data.get("content_angle", ""),
                        strengths=comp_data.get("strengths", []),
                        weaknesses=comp_data.get("weaknesses", []),
                        unique_elements=comp_data.get("unique_elements", []),
                        content_frequency=comp_data.get("posting_frequency", "unknown")
                    )
                    competitors.append(competitor)
                
                return competitors
                
        except Exception as e:
            logger.error(f"Competitive analysis error: {str(e)}")
        
        return []  # Return empty list if analysis fails
    
    async def _identify_market_gaps(self, ai_analysis: Dict[str, Any], 
                                  competitors: List[CompetitorAnalysis]) -> List[str]:
        """ระบุช่องว่างในตลาด"""
        
        gaps = []
        
        # Extract gaps from AI analysis
        if isinstance(ai_analysis, dict):
            content = ai_analysis.get("content", ai_analysis)
            
            # Look for market gaps in various formats
            gap_sources = [
                content.get("market_gaps", []),
                content.get("differentiation_opportunities", []),
                content.get("competitive_landscape", {}).get("market_gaps", [])
            ]
            
            for gap_list in gap_sources:
                if isinstance(gap_list, list):
                    gaps.extend(gap_list)
        
        # Analyze competitor weaknesses to find gaps
        competitor_weaknesses = []
        for competitor in competitors:
            competitor_weaknesses.extend(competitor.weaknesses)
        
        # Add insights from competitor analysis
        if competitor_weaknesses:
            gaps.append("โอกาสจากจุดอ่อนของคู่แข่ง: " + ", ".join(set(competitor_weaknesses[:3])))
        
        return list(set(gaps))  # Remove duplicates
    
    async def _generate_predictive_insights(self, ai_analysis: Dict[str, Any], trend_data: str) -> Dict[str, Any]:
        """สร้างข้อมูลเชิงลึกเชิงทำนาย"""
        
        try:
            prediction_prompt = f"""
สร้างการทำนายเชิงลึกสำหรับเทรนด์: {trend_data}

ข้อมูลที่มี: {json.dumps(ai_analysis, ensure_ascii=False)[:1000]}

ให้การทำนายใน JSON:
{{
  "trend_evolution": {{
    "current_stage": "ขั้นตอนปัจจุบัน",
    "next_stage_timeline": "กรอบเวลาไปขั้นตอนถัดไป",
    "peak_prediction": "การทำนายจุดสูงสุด",
    "decline_indicators": ["สัญญาณการลดลง"]
  }},
  "market_evolution": {{
    "emerging_sub_trends": ["sub-trends ที่จะเกิด"],
    "technology_impact": "ผลกระทบของเทคโนโลยี",
    "audience_behavior_shifts": ["การเปลี่ยนแปลงพฤติกรรมผู้ชม"]
  }},
  "opportunity_windows": [
    {{
      "window": "ช่วงเวลาโอกาส",
      "duration": "ระยะเวลา",
      "potential": "ศักยภาพ (1-10)",
      "recommended_action": "การกระทำที่แนะนำ"
    }}
  ],
  "risk_timeline": {{
    "immediate_risks": ["ความเสี่ยงทันที"],
    "medium_term_risks": ["ความเสี่ยงระยะกลาง"],
    "long_term_considerations": ["ข้อพิจารณาระยะยาว"]
  }}
}}
"""
            
            result = await self.registry.process_with_best_service(
                ServiceType.TEXT_AI,
                prediction_prompt,
                task_type="trend_prediction"
            )
            
            if result.get("success", False):
                return result.get("result", {}).get("content", {})
                
        except Exception as e:
            logger.error(f"Predictive insights error: {str(e)}")
        
        return {}
    
    async def _compile_analysis_result(self, trend_id: str, trend_data: str, 
                                     target_platforms: List[str], ai_analysis: Dict[str, Any],
                                     competitive_analysis: List[CompetitorAnalysis],
                                     market_gaps: List[str], predictive_insights: Dict[str, Any],
                                     analysis_depth: str) -> TrendAnalysisResult:
        """รวบรวมผลการวิเคราะห์"""
        
        # Extract data from AI analysis
        content = ai_analysis.get("content", ai_analysis) if isinstance(ai_analysis, dict) else {}
        
        # Determine lifecycle stage
        lifecycle_stage_str = content.get("lifecycle_stage", "growing")
        try:
            lifecycle_stage = TrendLifecycle(lifecycle_stage_str)
        except ValueError:
            lifecycle_stage = TrendLifecycle.GROWING
        
        # Determine competition level
        competition_str = content.get("competition_level", "medium")
        try:
            competition_level = CompetitionLevel(competition_str)
        except ValueError:
            competition_level = CompetitionLevel.MEDIUM
        
        # Extract scores
        scores = content.get("scores", {})
        
        # Create metrics
        metrics = TrendMetrics(
            momentum_score=scores.get("viral_potential", 5.0),
            content_saturation=scores.get("content_saturation", 5.0),
            avg_engagement_rate=scores.get("audience_interest", 5.0) / 10.0
        )
        
        # Extract content opportunities
        content_opportunities = content.get("content_opportunities", content.get("content_angles", []))
        if isinstance(content_opportunities, list) and content_opportunities:
            recommended_angles = []
            for opp in content_opportunities[:5]:  # Limit to top 5
                if isinstance(opp, str):
                    angle_data = {
                        "angle": opp,
                        "viral_potential": 6.0,
                        "difficulty": "medium",
                        "unique_value": "ไม่ระบุ"
                    }
                else:
                    angle_data = {
                        "angle": opp.get("angle", str(opp)),
                        "viral_potential": opp.get("viral_potential", 6.0),
                        "difficulty": opp.get("production_complexity", "medium"),
                        "unique_value": opp.get("unique_value_proposition", "ไม่ระบุ")
                    }
                recommended_angles.append(angle_data)
        else:
            recommended_angles = []
        
        # Platform priorities
        platform_suitability = content.get("platform_suitability", {})
        platform_priorities = {}
        for platform in target_platforms:
            if isinstance(platform_suitability.get(platform), dict):
                platform_priorities[platform] = platform_suitability[platform].get("score", 5.0)
            else:
                platform_priorities[platform] = float(platform_suitability.get(platform, 5.0))
        
        # Risk factors
        risk_factors = content.get("risks", content.get("risk_factors", []))
        if isinstance(risk_factors, str):
            risk_factors = [risk_factors]
        
        # Create result
        result = TrendAnalysisResult(
            trend_id=trend_id,
            trend_name=content.get("trend_name", trend_data[:100]),
            keywords=self._extract_keywords(trend_data),
            platforms=target_platforms,
            detected_at=datetime.now(),
            lifecycle_stage=lifecycle_stage,
            competition_level=competition_level,
            trend_origin=TrendOrigin.ORGANIC,  # Default
            category=content.get("primary_category", "general"),
            metrics=metrics,
            competitors=competitive_analysis,
            market_gaps=market_gaps,
            recommended_content_angles=recommended_angles,
            platform_priorities=platform_priorities,
            risk_factors=risk_factors,
            analysis_quality=analysis_depth,
            data_sources=["ai_analysis", "competitive_analysis"] if competitive_analysis else ["ai_analysis"]
        )
        
        return result
    
    def _calculate_opportunity_scores(self, result: TrendAnalysisResult) -> TrendAnalysisResult:
        """คำนวณคะแนนโอกาสต่างๆ"""
        
        # Base scores from metrics
        base_viral = result.metrics.momentum_score
        base_engagement = result.metrics.avg_engagement_rate * 10
        competition_penalty = result.metrics.content_saturation
        
        # Lifecycle stage impact
        lifecycle_multipliers = {
            TrendLifecycle.EMERGING: 1.5,
            TrendLifecycle.GROWING: 1.2,
            TrendLifecycle.PEAK: 0.8,
            TrendLifecycle.DECLINING: 0.3,
            TrendLifecycle.STABLE: 1.0
        }
        
        lifecycle_bonus = lifecycle_multipliers.get(result.lifecycle_stage, 1.0)
        
        # Competition level impact
        competition_multipliers = {
            CompetitionLevel.LOW: 1.4,
            CompetitionLevel.MEDIUM: 1.0,
            CompetitionLevel.HIGH: 0.7,
            CompetitionLevel.SATURATED: 0.4
        }
        
        competition_multiplier = competition_multipliers.get(result.competition_level, 1.0)
        
        # Calculate viral potential (0-10)
        result.viral_potential = min(10.0, 
            (base_viral * lifecycle_bonus * competition_multiplier) - (competition_penalty * 0.3)
        )
        
        # Calculate content gap score based on market gaps
        gap_score = min(10.0, len(result.market_gaps) * 2.0) if result.market_gaps else 5.0
        result.content_gap_score = gap_score
        
        # Calculate monetization potential
        monetization_base = 6.0  # Base score
        if result.lifecycle_stage in [TrendLifecycle.GROWING, TrendLifecycle.PEAK]:
            monetization_base += 2.0
        if result.competition_level in [CompetitionLevel.LOW, CompetitionLevel.MEDIUM]:
            monetization_base += 1.0
        
        result.monetization_potential = min(10.0, monetization_base)
        
        # Calculate overall opportunity score (weighted average)
        weights = self.scoring_weights
        result.opportunity_score = (
            result.viral_potential * weights["viral_indicators"] +
            base_engagement * weights["engagement_quality"] +
            result.content_gap_score * weights["competition_gap"] +
            (10 - competition_penalty) * weights["timing_advantage"] +
            result.monetization_potential * weights["monetization_signals"] +
            (base_viral * lifecycle_bonus) * weights["growth_momentum"]
        ) / sum(weights.values())
        
        result.opportunity_score = min(10.0, max(0.0, result.opportunity_score))
        
        # Calculate success probability (0-1)
        probability_factors = [
            result.opportunity_score / 10,
            lifecycle_bonus / 1.5,
            competition_multiplier,
            (10 - competition_penalty) / 10,
            min(1.0, len(result.recommended_content_angles) / 3)
        ]
        
        result.success_probability = sum(probability_factors) / len(probability_factors)
        result.confidence_level = min(1.0, result.success_probability * 1.1)
        
        return result
    
    async def _generate_actionable_recommendations(self, result: TrendAnalysisResult, 
                                                 platforms: List[str]) -> TrendAnalysisResult:
        """สร้างคำแนะนำที่นำไปปฏิบัติได้"""
        
        # Timing recommendations based on lifecycle
        timing_recommendations = {
            "immediate_action": False,
            "optimal_window": "unknown",
            "urgency_level": "medium"
        }
        
        if result.lifecycle_stage == TrendLifecycle.EMERGING:
            timing_recommendations = {
                "immediate_action": True,
                "optimal_window": "1-3 days",
                "urgency_level": "high",
                "reasoning": "เทรนด์เพิ่งเกิด โอกาสดีที่สุด"
            }
        elif result.lifecycle_stage == TrendLifecycle.GROWING:
            timing_recommendations = {
                "immediate_action": True,
                "optimal_window": "3-7 days", 
                "urgency_level": "medium",
                "reasoning": "เทรนด์กำลังโต ยังมีโอกาส"
            }
        elif result.lifecycle_stage == TrendLifecycle.PEAK:
            timing_recommendations = {
                "immediate_action": False,
                "optimal_window": "ระวัง แข่งขันสูง",
                "urgency_level": "low",
                "reasoning": "เทรนด์อยู่จุดสูงสุด แข่งขันสูง"
            }
        
        result.timing_recommendations = timing_recommendations
        
        # Enhanced differentiation opportunities
        if not result.differentiation_opportunities:
            differentiations = []
            
            # Based on competitor analysis
            if result.competitors:
                common_weaknesses = self._find_common_competitor_weaknesses(result.competitors)
                for weakness in common_weaknesses[:3]:
                    differentiations.append(f"ปรับปรุงจุดอ่อนของคู่แข่ง: {weakness}")
            
            # Based on market gaps
            for gap in result.market_gaps[:2]:
                differentiations.append(f"ใช้ประโยชน์จากช่องว่าง: {gap}")
            
            # Platform-specific opportunities
            for platform in platforms:
                if platform in result.platform_priorities:
                    score = result.platform_priorities[platform]
                    if score >= 7.0:
                        differentiations.append(f"โฟกัส {platform} เนื่องจากความเหมาะสมสูง")
            
            result.differentiation_opportunities = differentiations
        
        return result
    
    def _find_common_competitor_weaknesses(self, competitors: List[CompetitorAnalysis]) -> List[str]:
        """หาจุดอ่อนที่พบบ่อยในคู่แข่ง"""
        
        all_weaknesses = []
        for competitor in competitors:
            all_weaknesses.extend(competitor.weaknesses)
        
        # Count frequency
        weakness_counts = {}
        for weakness in all_weaknesses:
            weakness_counts[weakness] = weakness_counts.get(weakness, 0) + 1
        
        # Return common weaknesses (appears in 2+ competitors)
        common_weaknesses = [w for w, count in weakness_counts.items() if count >= 2]
        return common_weaknesses[:5]
    
    def _generate_trend_id(self, trend_data: str) -> str:
        """สร้าง unique ID สำหรับเทรนด์"""
        normalized = re.sub(r'[^\w\s]', '', trend_data.lower())
        hash_object = hashlib.md5(normalized.encode())
        return f"trend_{hash_object.hexdigest()[:12]}"
    
    def _extract_keywords(self, trend_data: str) -> List[str]:
        """สกัดคำสำคัญจากข้อมูลเทรนด์"""
        
        # Remove common words and extract meaningful terms
        common_words = {
            'และ', 'ที่', 'ใน', 'กับ', 'จาก', 'เป็น', 'มี', 'ได้', 'แล้ว', 'จะ',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'
        }
        
        words = re.findall(r'\b\w+\b', trend_data.lower())
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        return list(set(keywords))[:10]  # Return unique keywords, max 10
    
    def _create_basic_analysis(self, trend_data: str, platforms: List[str]) -> Dict[str, Any]:
        """สร้างการวิเคราะห์พื้นฐานเมื่อ AI ล้มเหลว"""
        
        return {
            "trend_name": trend_data[:100],
            "lifecycle_stage": "growing",
            "scores": {
                "viral_potential": 6.0,
                "content_saturation": 5.0,
                "audience_interest": 6.0,
                "monetization_opportunity": 5.0,
                "competition_level": 5.0
            },
            "content_angles": [
                f"สร้างเนื้อหาเกี่ยวกับ {trend_data}",
                "แชร์ประสบการณ์ส่วนตัว",
                "สอนหรืออธิบายแนวคิด"
            ],
            "platform_suitability": {platform: 6.0 for platform in platforms},
            "risks": ["การแข่งขันที่เพิ่มขึ้น", "อายุเทรนด์ที่สั้น"],
            "recommendations": ["สร้างเนื้อหาให้เร็ว", "หามุมมองที่เป็นเอกลักษณ์"]
        }
    
    def _create_fallback_analysis(self, trend_data: str, platforms: List[str]) -> TrendAnalysisResult:
        """สร้างการวิเคราะห์สำรองเมื่อเกิดข้อผิดพลาด"""
        
        basic_analysis = self._create_basic_analysis(trend_data, platforms)
        
        return TrendAnalysisResult(
            trend_id=self._generate_trend_id(trend_data),
            trend_name=basic_analysis["trend_name"],
            keywords=self._extract_keywords(trend_data),
            platforms=platforms,
            detected_at=datetime.now(),
            lifecycle_stage=TrendLifecycle.GROWING,
            competition_level=CompetitionLevel.MEDIUM,
            trend_origin=TrendOrigin.ORGANIC,
            category="general",
            metrics=TrendMetrics(
                momentum_score=6.0,
                content_saturation=5.0,
                avg_engagement_rate=0.06
            ),
            opportunity_score=6.0,
            viral_potential=6.0,
            monetization_potential=5.0,
            content_gap_score=5.0,
            platform_priorities={platform: 6.0 for platform in platforms},
            recommended_content_angles=[
                {"angle": angle, "viral_potential": 6.0, "difficulty": "medium"}
                for angle in basic_analysis["content_angles"]
            ],
            risk_factors=basic_analysis["risks"],
            success_probability=0.6,
            confidence_level=0.5,
            analysis_quality="fallback",
            data_sources=["fallback_heuristics"]
        )
    
    async def batch_analyze_trends(self, trends: List[str], platforms: List[str], 
                                 analysis_depth: str = "standard") -> List[TrendAnalysisResult]:
        """วิเคราะห์หลายเทรนด์พร้อมกัน"""
        
        logger.info(f"Starting batch analysis of {len(trends)} trends")
        
        # Create analysis tasks
        tasks = []
        for trend in trends:
            task = self.analyze_trend_comprehensive(trend, platforms, analysis_depth)
            tasks.append(task)
        
        # Execute with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Limit concurrent analyses
        
        async def analyze_with_semaphore(trend_task):
            async with semaphore:
                return await trend_task
        
        # Run analyses
        results = await asyncio.gather(
            *[analyze_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing trend '{trends[i]}': {result}")
                # Create fallback result
                fallback = self._create_fallback_analysis(trends[i], platforms)
                valid_results.append(fallback)
            else:
                valid_results.append(result)
        
        # Sort by opportunity score
        valid_results.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        logger.info(f"Batch analysis completed. Top trend: {valid_results[0].trend_name} (score: {valid_results[0].opportunity_score:.1f})")
        
        return valid_results
    
    def rank_trends_by_opportunity(self, analyses: List[TrendAnalysisResult], 
                                  user_preferences: Dict[str, Any] = None) -> List[TrendAnalysisResult]:
        """จัดอันดับเทรนด์ตามโอกาส"""
        
        if user_preferences:
            # Apply user preference weights
            preferred_platforms = user_preferences.get("preferred_platforms", [])
            risk_tolerance = user_preferences.get("risk_tolerance", "medium")  # low, medium, high
            content_types = user_preferences.get("preferred_content_types", [])
            
            for analysis in analyses:
                # Platform preference bonus
                platform_bonus = 0.0
                for platform in preferred_platforms:
                    if platform in analysis.platform_priorities:
                        platform_bonus += analysis.platform_priorities[platform] * 0.1
                
                # Risk tolerance adjustment
                risk_multiplier = 1.0
                if risk_tolerance == "low" and analysis.lifecycle_stage == TrendLifecycle.EMERGING:
                    risk_multiplier = 0.8  # Penalty for high-risk emerging trends
                elif risk_tolerance == "high" and analysis.lifecycle_stage == TrendLifecycle.EMERGING:
                    risk_multiplier = 1.3  # Bonus for risk-takers
                
                # Adjust opportunity score
                analysis.opportunity_score = min(10.0, 
                    (analysis.opportunity_score * risk_multiplier) + platform_bonus
                )
        
        # Sort by adjusted opportunity score
        return sorted(analyses, key=lambda x: x.opportunity_score, reverse=True)
    
    def get_analyzer_status(self) -> Dict[str, Any]:
        """สถานะของ Trend Analyzer"""
        
        return {
            "cache_size": len(self.analysis_cache),
            "scoring_weights": self.scoring_weights,
            "supported_platforms": list(self.platform_characteristics.keys()),
            "analysis_capabilities": [
                "trend_classification",
                "competitive_analysis", 
                "market_gap_identification",
                "predictive_insights",
                "actionable_recommendations"
            ],
            "cache_stats": {
                "total_cached": len(self.analysis_cache),
                "valid_cache_entries": len([
                    entry for entry in self.analysis_cache.values()
                    if entry.expires_at and entry.expires_at > datetime.now()
                ])
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def clear_expired_cache(self):
        """ล้าง cache ที่หมดอายุ"""
        
        current_time = datetime.now()
        expired_keys = [
            key for key, analysis in self.analysis_cache.items()
            if analysis.expires_at and analysis.expires_at <= current_time
        ]
        
        for key in expired_keys:
            del self.analysis_cache[key]
        
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    async def generate_trend_report(self, analyses: List[TrendAnalysisResult]) -> Dict[str, Any]:
        """สร้างรายงานสรุปเทรนด์"""
        
        if not analyses:
            return {"error": "No trend analyses provided"}
        
        # Calculate summary statistics
        avg_opportunity = sum(a.opportunity_score for a in analyses) / len(analyses)
        avg_viral_potential = sum(a.viral_potential for a in analyses) / len(analyses)
        avg_success_probability = sum(a.success_probability for a in analyses) / len(analyses)
        
        # Platform distribution
        platform_scores = {}
        for analysis in analyses:
            for platform, score in analysis.platform_priorities.items():
                platform_scores[platform] = platform_scores.get(platform, [])
                platform_scores[platform].append(score)
        
        platform_averages = {
            platform: sum(scores) / len(scores)
            for platform, scores in platform_scores.items()
        }
        
        # Lifecycle distribution
        lifecycle_counts = {}
        for analysis in analyses:
            stage = analysis.lifecycle_stage.value
            lifecycle_counts[stage] = lifecycle_counts.get(stage, 0) + 1
        
        # Competition analysis
        competition_counts = {}
        for analysis in analyses:
            level = analysis.competition_level.value
            competition_counts[level] = competition_counts.get(level, 0) + 1
        
        # Top opportunities
        top_opportunities = sorted(analyses, key=lambda x: x.opportunity_score, reverse=True)[:5]
        
        # Risk assessment
        high_risk_trends = [a for a in analyses if len(a.risk_factors) > 3]
        low_risk_trends = [a for a in analyses if len(a.risk_factors) <= 2]
        
        report = {
            "summary": {
                "total_trends_analyzed": len(analyses),
                "average_opportunity_score": round(avg_opportunity, 2),
                "average_viral_potential": round(avg_viral_potential, 2),
                "average_success_probability": round(avg_success_probability, 2)
            },
            "platform_analysis": {
                "platform_scores": platform_averages,
                "recommended_platform": max(platform_averages.items(), key=lambda x: x[1])[0] if platform_averages else None
            },
            "trend_distribution": {
                "lifecycle_stages": lifecycle_counts,
                "competition_levels": competition_counts
            },
            "top_opportunities": [
                {
                    "trend_name": opp.trend_name,
                    "opportunity_score": opp.opportunity_score,
                    "viral_potential": opp.viral_potential,
                    "lifecycle_stage": opp.lifecycle_stage.value,
                    "competition_level": opp.competition_level.value,
                    "recommended_platforms": sorted(
                        opp.platform_priorities.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:2]
                }
                for opp in top_opportunities
            ],
            "risk_assessment": {
                "high_risk_count": len(high_risk_trends),
                "low_risk_count": len(low_risk_trends),
                "common_risk_factors": self._get_common_risk_factors(analyses)
            },
            "actionable_insights": {
                "immediate_opportunities": len([a for a in analyses if a.timing_recommendations.get("immediate_action", False)]),
                "market_gaps_identified": sum(len(a.market_gaps) for a in analyses),
                "total_content_angles": sum(len(a.recommended_content_angles) for a in analyses)
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def _get_common_risk_factors(self, analyses: List[TrendAnalysisResult]) -> List[str]:
        """หาปัจจัยเสี่ยงที่พบบ่อย"""
        
        all_risks = []
        for analysis in analyses:
            all_risks.extend(analysis.risk_factors)
        
        # Count frequency
        risk_counts = {}
        for risk in all_risks:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        # Return risks that appear in multiple trends
        common_risks = [
            risk for risk, count in risk_counts.items() 
            if count >= max(2, len(analyses) * 0.3)
        ]
        
        return sorted(common_risks, key=lambda x: risk_counts[x], reverse=True)[:5]

# Example usage and testing
async def test_trend_analyzer():
    """ทดสอบ Trend Analyzer"""
    
    # Mock service registry
    from .text_ai.groq_service import GroqService
    
    registry = get_service_registry()
    registry.register_service(ServiceType.TEXT_AI, QualityTier.BUDGET, GroqService("mock-key"))
    
    # Initialize analyzer
    analyzer = TrendAnalyzer(registry)
    
    # Test single trend analysis
    print("Testing Trend Analyzer...")
    
    result = await analyzer.analyze_trend_comprehensive(
        "AI Video Generation Tools กำลังฮิตใน 2024",
        ["TikTok", "YouTube"],
        "standard"
    )
    
    print(f"Analysis completed: {result.trend_name}")
    print(f"Opportunity Score: {result.opportunity_score:.1f}/10")
    print(f"Viral Potential: {result.viral_potential:.1f}/10")
    print(f"Lifecycle: {result.lifecycle_stage.value}")
    print(f"Competition: {result.competition_level.value}")
    print(f"Success Probability: {result.success_probability:.1%}")
    
    # Test batch analysis
    trends = [
        "Sustainable Fashion ในหมู่วัยรุ่น",
        "Home Workout Routines",
        "Plant-based Cooking"
    ]
    
    batch_results = await analyzer.batch_analyze_trends(trends, ["TikTok", "YouTube"])
    print(f"\nBatch analysis: {len(batch_results)} trends")
    
    for i, result in enumerate(batch_results[:3]):
        print(f"{i+1}. {result.trend_name} - Score: {result.opportunity_score:.1f}")
    
    # Generate report
    report = await analyzer.generate_trend_report(batch_results)
    print(f"\nReport generated:")
    print(f"Average opportunity: {report['summary']['average_opportunity_score']}")
    print(f"Top platform: {report['platform_analysis']['recommended_platform']}")
    
    # Show analyzer status
    status = analyzer.get_analyzer_status()
    print(f"\nAnalyzer Status:")
    print(f"Cache size: {status['cache_size']}")
    print(f"Capabilities: {len(status['analysis_capabilities'])}")

if __name__ == "__main__":
    asyncio.run(test_trend_analyzer())