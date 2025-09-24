# ai-content-factory/content-engine/ai_services/real_ai_services.py

import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json
from datetime import datetime
import openai
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIAnalysisResult:
    trend_topic: str
    viral_potential: int  # 1-10
    content_saturation: int  # 1-10
    audience_interest: int  # 1-10
    monetization_opportunity: int  # 1-10
    overall_score: float
    content_angles: List[str]
    reasoning: str
    timestamp: datetime

@dataclass
class ContentPlan:
    content_type: str
    script: Dict[str, str]
    visual_plan: Dict[str, Any]
    audio_plan: Dict[str, str]
    platform_optimization: Dict[str, Any]
    production_estimate: Dict[str, Any]

class RealGroqService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama3-8b-8192"  # Fast and efficient model
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_trend_potential(self, 
                                    trend_topic: str, 
                                    popularity_score: int,
                                    growth_rate: float,
                                    related_keywords: List[str] = None) -> Optional[AIAnalysisResult]:
        """วิเคราะห์ศักยภาพของ trend ด้วย Groq AI"""
        
        if related_keywords is None:
            related_keywords = []
        
        prompt = f"""
        Analyze this trending topic for content creation opportunities in Thailand market:
        
        Topic: {trend_topic}
        Current popularity score: {popularity_score}/100
        Growth rate: {growth_rate}%
        Related keywords: {', '.join(related_keywords[:5])}
        
        Please analyze and rate each aspect from 1-10:
        
        1. Viral Potential: How likely is this trend to go viral?
        2. Content Saturation: How saturated is this topic with existing content? (1=oversaturated, 10=blue ocean)
        3. Audience Interest: How interested would Thai audiences be?
        4. Monetization Opportunity: How easy is it to monetize content around this topic?
        
        Also suggest 3 unique content angles that would work well for this trend.
        
        Respond in JSON format:
        {{
            "viral_potential": 1-10,
            "content_saturation": 1-10,
            "audience_interest": 1-10,
            "monetization_opportunity": 1-10,
            "content_angles": ["angle 1", "angle 2", "angle 3"],
            "reasoning": "detailed explanation of your analysis"
        }}
        """
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert content strategist specializing in viral content and Thai market trends."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Parse JSON response
                    try:
                        result_data = json.loads(content)
                        
                        # Calculate overall score
                        overall_score = (
                            result_data["viral_potential"] +
                            result_data["content_saturation"] +
                            result_data["audience_interest"] +
                            result_data["monetization_opportunity"]
                        ) / 4.0
                        
                        return AIAnalysisResult(
                            trend_topic=trend_topic,
                            viral_potential=result_data["viral_potential"],
                            content_saturation=result_data["content_saturation"],
                            audience_interest=result_data["audience_interest"],
                            monetization_opportunity=result_data["monetization_opportunity"],
                            overall_score=overall_score,
                            content_angles=result_data["content_angles"],
                            reasoning=result_data["reasoning"],
                            timestamp=datetime.now()
                        )
                        
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON response: {content}")
                        return None
                        
                else:
                    logger.error(f"Groq API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return None

class RealOpenAIService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"  # Cost-effective model
        
    async def create_content_plan(self, 
                                trend_topic: str,
                                content_angle: str,
                                target_platforms: List[str] = None) -> Optional[ContentPlan]:
        """สร้าง content plan ด้วย OpenAI"""
        
        if target_platforms is None:
            target_platforms = ["YouTube", "TikTok"]
        
        prompt = f"""
        Create a complete content production plan for this trending topic:
        
        Topic: {trend_topic}
        Content Angle: {content_angle}
        Target Platforms: {', '.join(target_platforms)}
        Target Audience: Thai audience aged 18-35
        
        Create a comprehensive plan in JSON format:
        {{
            "content_type": "educational/entertainment/news/tutorial",
            "script": {{
                "hook": "compelling first 3 seconds to grab attention",
                "main_content": "detailed middle section content",
                "cta": "strong call-to-action ending"
            }},
            "visual_plan": {{
                "style": "realistic/cartoon/minimalist/dynamic",
                "scenes": ["scene 1 description", "scene 2 description", "scene 3 description"],
                "text_overlays": ["key point 1", "key point 2"],
                "color_scheme": "vibrant/professional/dark/bright"
            }},
            "audio_plan": {{
                "voice_style": "energetic/calm/professional/friendly",
                "background_music": "upbeat/chill/none/dramatic",
                "sound_effects": ["effect 1", "effect 2"]
            }},
            "platform_optimization": {{
                "title": "SEO optimized title",
                "description": "platform specific description",
                "hashtags": ["#tag1", "#tag2", "#tag3"],
                "thumbnail_concept": "eye-catching thumbnail idea",
                "best_posting_time": "optimal time to post"
            }},
            "production_estimate": {{
                "time_minutes": 30,
                "cost_baht": 50,
                "complexity": "low/medium/high",
                "required_tools": ["tool1", "tool2"]
            }}
        }}
        
        Make sure the content is engaging, culturally appropriate for Thai audience, and optimized for viral potential.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert content creator and social media strategist specializing in viral content for Thai audiences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                plan_data = json.loads(content)
                
                return ContentPlan(
                    content_type=plan_data["content_type"],
                    script=plan_data["script"],
                    visual_plan=plan_data["visual_plan"],
                    audio_plan=plan_data["audio_plan"],
                    platform_optimization=plan_data["platform_optimization"],
                    production_estimate=plan_data["production_estimate"]
                )
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {content}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None
    
    async def generate_script(self, content_plan: ContentPlan, duration_seconds: int = 60) -> Optional[str]:
        """สร้าง script สำหรับวิดีโอ"""
        
        prompt = f"""
        Write a detailed video script based on this content plan:
        
        Content Type: {content_plan.content_type}
        Hook: {content_plan.script['hook']}
        Main Content: {content_plan.script['main_content']}
        CTA: {content_plan.script['cta']}
        Duration: {duration_seconds} seconds
        
        Format the script as:
        [0-3s] HOOK: (what viewer sees and hears)
        [4-{duration_seconds-10}s] MAIN CONTENT: (detailed content broken into scenes)
        [{duration_seconds-9}-{duration_seconds}s] CTA: (call to action)
        
        Include:
        - Specific dialogue/narration
        - Visual cues in parentheses
        - Timing for each section
        - Engagement hooks throughout
        - Thai cultural references where appropriate
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional scriptwriter specializing in viral social media content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None

class RealAIDirector:
    """AI Director ที่รวม Groq และ OpenAI เข้าด้วยกัน"""
    
    def __init__(self, groq_api_key: str, openai_api_key: str):
        self.groq_service = RealGroqService(groq_api_key)
        self.openai_service = RealOpenAIService(openai_api_key)
    
    async def __aenter__(self):
        await self.groq_service.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.groq_service.__aexit__(exc_type, exc_val, exc_tb)
    
    async def analyze_and_plan_content(self, 
                                     trend_topic: str,
                                     popularity_score: int,
                                     growth_rate: float,
                                     related_keywords: List[str] = None) -> Dict[str, Any]:
        """ครบวงจร: วิเคราะห์ trend + สร้าง content plan"""
        
        logger.info(f"Starting AI analysis for: {trend_topic}")
        
        # Step 1: วิเคราะห์ trend ด้วย Groq
        analysis = await self.groq_service.analyze_trend_potential(
            trend_topic, popularity_score, growth_rate, related_keywords
        )
        
        if not analysis:
            logger.error("Failed to analyze trend")
            return {"success": False, "error": "Trend analysis failed"}
        
        logger.info(f"Trend analysis complete - Overall score: {analysis.overall_score:.1f}")
        
        # Step 2: สร้าง content plans สำหรับแต่ละ angle ด้วย OpenAI
        content_plans = []
        
        for angle in analysis.content_angles:
            logger.info(f"Creating content plan for angle: {angle}")
            
            plan = await self.openai_service.create_content_plan(
                trend_topic, angle, ["YouTube", "TikTok", "Instagram"]
            )
            
            if plan:
                # Generate script for the plan
                script = await self.openai_service.generate_script(plan, 60)
                
                content_plans.append({
                    "angle": angle,
                    "plan": plan,
                    "script": script,
                    "estimated_score": analysis.overall_score
                })
        
        return {
            "success": True,
            "analysis": analysis,
            "content_plans": content_plans,
            "recommendations": {
                "top_plan": max(content_plans, key=lambda x: x["estimated_score"]) if content_plans else None,
                "priority_level": "High" if analysis.overall_score >= 7 else "Medium" if analysis.overall_score >= 5 else "Low"
            }
        }
    
    async def batch_analyze_trends(self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """วิเคราะห์หลาย trends พร้อมกัน"""
        
        results = []
        
        for trend in trends:
            try:
                result = await self.analyze_and_plan_content(
                    trend_topic=trend.get("topic", ""),
                    popularity_score=trend.get("popularity_score", 50),
                    growth_rate=trend.get("growth_rate", 0),
                    related_keywords=trend.get("keywords", [])
                )
                
                result["original_trend"] = trend
                results.append(result)
                
                # Rate limiting between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error analyzing trend {trend.get('topic')}: {e}")
                continue
        
        # Sort by analysis score
        successful_results = [r for r in results if r.get("success")]
        successful_results.sort(key=lambda x: x["analysis"].overall_score, reverse=True)
        
        return successful_results


# Testing และ Usage Example
async def test_real_ai_services():
    """ทดสอบ Real AI Services"""
    
    # API Keys (แทนที่ด้วย keys จริง)
    groq_key = "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"
    openai_key = "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"
    
    print("🤖 Testing Real AI Services Integration")
    
    async with RealAIDirector(groq_key, openai_key) as ai_director:
        
        # Test 1: Single trend analysis
        print("\n1. Analyzing single trend...")
        
        test_trend = {
            "topic": "AI สร้างวิดีโอ",
            "popularity_score": 85,
            "growth_rate": 150.0,
            "keywords": ["artificial intelligence", "video creation", "AI tools", "เทคโนโลยี"]
        }
        
        result = await ai_director.analyze_and_plan_content(
            test_trend["topic"],
            test_trend["popularity_score"],
            test_trend["growth_rate"],
            test_trend["keywords"]
        )
        
        if result["success"]:
            analysis = result["analysis"]
            print(f"✅ Analysis complete for: {analysis.trend_topic}")
            print(f"   Overall Score: {analysis.overall_score:.1f}/10")
            print(f"   Viral Potential: {analysis.viral_potential}/10")
            print(f"   Content Plans: {len(result['content_plans'])}")
            
            if result["content_plans"]:
                top_plan = result["content_plans"][0]
                print(f"   Top Content Angle: {top_plan['angle']}")
                print(f"   Content Type: {top_plan['plan'].content_type}")
        else:
            print("❌ Analysis failed")
        
        # Test 2: Batch analysis
        print("\n2. Batch analyzing multiple trends...")
        
        test_trends = [
            {"topic": "TikTok Viral Dance", "popularity_score": 75, "growth_rate": 200.0},
            {"topic": "Thai Street Food", "popularity_score": 60, "growth_rate": 50.0},
            {"topic": "Gaming Tips", "popularity_score": 80, "growth_rate": 100.0}
        ]
        
        batch_results = await ai_director.batch_analyze_trends(test_trends)
        
        print(f"✅ Batch analysis complete: {len(batch_results)} results")
        
        for i, result in enumerate(batch_results[:3]):
            if result.get("success"):
                analysis = result["analysis"]
                print(f"   {i+1}. {analysis.trend_topic}: {analysis.overall_score:.1f}/10")


# Integration with existing trend monitor
async def integrate_with_trend_monitor():
    """Integration example with trend monitor"""
    
    # Import existing services
    from real_youtube_trends import RealYouTubeTrendsService
    from real_google_trends import RealGoogleTrendsService
    
    # API Keys
    youtube_key = "YOUR_YOUTUBE_API_KEY"
    groq_key = "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"
    openai_key = "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"
    
    print("🔄 Full Pipeline Integration Test")
    
    # Step 1: Collect trends
    async with RealYouTubeTrendsService(youtube_key) as youtube_service:
        trending_videos = await youtube_service.get_trending_videos("TH", max_results=10)
        keywords = await youtube_service.analyze_trending_keywords(trending_videos)
    
    # Step 2: Get Google Trends data
    google_trends = RealGoogleTrendsService("TH")
    top_keywords = list(keywords.keys())[:5]
    google_data = await google_trends.analyze_multiple_keywords(top_keywords)
    
    # Step 3: AI analysis and content planning
    async with RealAIDirector(groq_key, openai_key) as ai_director:
        trends_for_analysis = []
        
        for trend_data in google_data:
            trends_for_analysis.append({
                "topic": trend_data.keyword,
                "popularity_score": trend_data.interest_score,
                "growth_rate": 50.0,  # Default growth rate
                "keywords": trend_data.related_queries
            })
        
        final_results = await ai_director.batch_analyze_trends(trends_for_analysis)
        
        print(f"🎯 Pipeline complete: {len(final_results)} analyzed opportunities")
        
        for result in final_results[:3]:
            if result.get("success"):
                analysis = result["analysis"]
                print(f"   📈 {analysis.trend_topic}: Score {analysis.overall_score:.1f}")
                print(f"      Best angle: {analysis.content_angles[0] if analysis.content_angles else 'N/A'}")


if __name__ == "__main__":
    # เลือกการทดสอบที่ต้องการ
    asyncio.run(test_real_ai_services())
    # asyncio.run(integrate_with_trend_monitor())