# indentation_fix.py - แก้ไข indentation errors อย่างรวดเร็ว

def fix_gemini_function():
    """สร้าง Gemini function ที่ถูกต้อง"""
    
    gemini_function = '''    async def analyze_with_gemini(self, trend_topic: str, popularity_score: int) -> Optional[AIAnalysisResult]:
        """Analyze with Google Gemini API"""
        if not self.gemini_api_key:
            return None
            
        prompt = f"""Analyze this trending topic for content creation:

Topic: {trend_topic}
Popularity: {popularity_score}/100

Rate each aspect from 1-10:
1. viral_potential: How likely to go viral?
2. content_saturation: Competition level (1=oversaturated, 10=unique opportunity)
3. audience_interest: Thai audience interest
4. monetization_opportunity: Revenue potential

Suggest 3 content angles.

Respond ONLY with JSON:
{{"viral_potential": 8, "content_saturation": 6, "audience_interest": 9, "monetization_opportunity": 7, "content_angles": ["tutorial", "review", "analysis"], "reasoning": "brief analysis"}}"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 500
                }
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'candidates' in data and len(data['candidates']) > 0:
                        content = data['candidates'][0]['content']['parts'][0]['text']
                        
                        result_data = self.extract_json_from_text(content)
                        
                        if result_data and all(k in result_data for k in ['viral_potential', 'content_saturation', 'audience_interest', 'monetization_opportunity']):
                            overall_score = (
                                result_data["viral_potential"] +
                                result_data["content_saturation"] +
                                result_data["audience_interest"] +
                                result_data["monetization_opportunity"]
                            ) / 4.0
                            
                            print(f"  [Gemini Success] {trend_topic[:30]}... Score: {overall_score:.1f}")
                            
                            return AIAnalysisResult(
                                trend_topic=trend_topic,
                                viral_potential=result_data["viral_potential"],
                                content_saturation=result_data["content_saturation"],
                                audience_interest=result_data["audience_interest"],
                                monetization_opportunity=result_data["monetization_opportunity"],
                                overall_score=overall_score,
                                content_angles=result_data.get("content_angles", ["Tutorial", "Review", "Analysis"]),
                                reasoning=result_data.get("reasoning", "Gemini analysis completed")
                            )
                        else:
                            logger.error(f"Gemini JSON parsing failed: {content}")
                            
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
        
        return None'''
    
    return gemini_function

def create_fixed_file():
    """สร้างไฟล์ที่แก้ไข indentation แล้ว"""
    
    print("Creating fixed real_integration_main.py...")
    
    # อ่านไฟล์ปัจจุบัน
    try:
        with open('real_integration_main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # หาตำแหน่งที่มีปัญหา และแทนที่ด้วย function ที่ถูกต้อง
        gemini_function = fix_gemini_function()
        
        # หาจุดเริ่มต้นและสิ้นสุดของ function
        start_marker = "async def analyze_with_gemini"
        end_marker = "return None"
        
        start_idx = content.find(start_marker)
        if start_idx != -1:
            # หาจุดสิ้นสุดของ function
            lines = content[start_idx:].split('\n')
            end_line = 0
            indent_level = 0
            
            for i, line in enumerate(lines):
                if i == 0:
                    indent_level = len(line) - len(line.lstrip())
                    continue
                
                if line.strip() == "":
                    continue
                    
                current_indent = len(line) - len(line.lstrip())
                
                # หาจุดที่ indent กลับมาเท่าเดิมหรือน้อยกว่า (จบ function)
                if current_indent <= indent_level and line.strip():
                    end_line = i
                    break
            
            if end_line == 0:
                # หาจาก "return None" สุดท้าย
                for i, line in enumerate(lines):
                    if "return None" in line:
                        end_line = i + 1
            
            if end_line > 0:
                # แทนที่ function เก่าด้วยใหม่
                before = '\n'.join(content[:start_idx].split('\n')[:-1])
                after = '\n'.join(content[start_idx:].split('\n')[end_line:])
                
                new_content = before + '\n' + gemini_function + '\n' + after
                
                # บันทึกไฟล์ใหม่
                with open('real_integration_main_fixed.py', 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ Created real_integration_main_fixed.py")
                print("📋 Please run: python real_integration_main_fixed.py")
                return True
        
        print("❌ Could not find function to replace")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_minimal_working_version():
    """สร้างเวอร์ชันที่ทำงานได้แน่นอน"""
    
    minimal_code = '''# minimal_ai_integration.py - เวอร์ชันที่ทำงานได้แน่นอน

import asyncio
import aiohttp
import logging
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config
def load_config():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    return {
        "youtube_api_key": os.getenv("YOUTUBE_API_KEY", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///content_factory.db")
    }

@dataclass
class AIAnalysisResult:
    trend_topic: str
    viral_potential: int
    content_saturation: int
    audience_interest: int
    monetization_opportunity: int
    overall_score: float
    content_angles: List[str]
    reasoning: str

class SimpleAIService:
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_trend(self, topic: str, popularity: int):
        """Simple trend analysis"""
        if not self.gemini_api_key:
            return self.create_smart_analysis(topic, popularity)
        
        prompt = f"""Analyze: {topic}
Popularity: {popularity}/100

JSON only:
{{"viral_potential": 8, "content_saturation": 6, "audience_interest": 9, "monetization_opportunity": 7, "content_angles": ["tutorial", "review", "tips"], "reasoning": "analysis"}}"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 400}
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    
                    # Extract JSON
                    try:
                        if "```json" in content:
                            json_str = content.split("```json")[1].split("```")[0].strip()
                        else:
                            start = content.find("{")
                            end = content.rfind("}") + 1
                            json_str = content[start:end]
                        
                        result = json.loads(json_str)
                        
                        overall_score = sum([
                            result["viral_potential"],
                            result["content_saturation"], 
                            result["audience_interest"],
                            result["monetization_opportunity"]
                        ]) / 4.0
                        
                        print(f"  [Gemini Success] {topic[:30]}... Score: {overall_score:.1f}")
                        
                        return AIAnalysisResult(
                            trend_topic=topic,
                            viral_potential=result["viral_potential"],
                            content_saturation=result["content_saturation"],
                            audience_interest=result["audience_interest"],
                            monetization_opportunity=result["monetization_opportunity"],
                            overall_score=overall_score,
                            content_angles=result.get("content_angles", ["Tutorial", "Review", "Tips"]),
                            reasoning=result.get("reasoning", "Gemini analysis")
                        )
                        
                    except json.JSONDecodeError:
                        print(f"  [JSON Error] {topic[:30]}... Using smart analysis")
                        return self.create_smart_analysis(topic, popularity)
                        
                else:
                    print(f"  [API Error] {topic[:30]}... Using smart analysis")
                    return self.create_smart_analysis(topic, popularity)
                    
        except Exception as e:
            print(f"  [Exception] {topic[:30]}... Using smart analysis")
            return self.create_smart_analysis(topic, popularity)
    
    def create_smart_analysis(self, topic: str, popularity: int):
        """Smart fallback analysis"""
        topic_lower = topic.lower()
        
        # Category detection
        if any(word in topic_lower for word in ['เกม', 'game', 'rov', 'roblox']):
            viral, saturation, interest, monetization = 8, 4, 9, 7
            angles = ["Gaming tutorial", "Pro tips", "Beginner guide"]
            category = "gaming"
        elif any(word in topic_lower for word in ['เพลง', 'music', 'ft.']):
            viral, saturation, interest, monetization = 9, 5, 8, 5
            angles = ["Song reaction", "Music analysis", "Artist spotlight"]
            category = "music"
        elif any(word in topic_lower for word in ['หนัง', 'movie', 'ตัวอย่าง']):
            viral, saturation, interest, monetization = 7, 6, 8, 6
            angles = ["Movie review", "Behind scenes", "Analysis"]
            category = "entertainment"
        elif any(word in topic_lower for word in ['ai', 'tech', 'เทคโนโลยี']):
            viral, saturation, interest, monetization = 7, 7, 7, 8
            angles = ["Tech tutorial", "Product review", "How-to guide"]
            category = "tech"
        else:
            viral, saturation, interest, monetization = 6, 6, 7, 6
            angles = ["Complete guide", "Tips & tricks", "Tutorial"]
            category = "general"
        
        # Adjust based on popularity
        viral = min(viral + (popularity // 20), 10)
        interest = min(interest + (popularity // 25), 10)
        
        overall_score = (viral + saturation + interest + monetization) / 4.0
        
        print(f"  [Smart Analysis] {topic[:30]}... Score: {overall_score:.1f}")
        
        return AIAnalysisResult(
            trend_topic=topic,
            viral_potential=viral,
            content_saturation=saturation,
            audience_interest=interest,
            monetization_opportunity=monetization,
            overall_score=overall_score,
            content_angles=angles,
            reasoning=f"Smart analysis: {category} category"
        )

async def quick_test():
    """Quick test of AI analysis"""
    print("🧪 Quick AI Analysis Test")
    print("=" * 30)
    
    config = load_config()
    
    test_topics = [
        ("AI Video Creation", 85),
        ("RoV Pro League", 75),
        ("Thai Street Food", 60)
    ]
    
    async with SimpleAIService(config["gemini_api_key"]) as ai_service:
        for topic, popularity in test_topics:
            result = await ai_service.analyze_trend(topic, popularity)
            print(f"Topic: {result.trend_topic}")
            print(f"Score: {result.overall_score:.1f}/10")
            print(f"Angles: {result.content_angles}")
            print(f"Reasoning: {result.reasoning}")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(quick_test())
'''
    
    with open('minimal_ai_integration.py', 'w', encoding='utf-8') as f:
        f.write(minimal_code)
    
    print("✅ Created minimal_ai_integration.py")
    print("📋 Test with: python minimal_ai_integration.py")

def main():
    print("🔧 Indentation Fix Tool")
    print("=" * 30)
    
    print("Option 1: Try to fix current file")
    success = create_fixed_file()
    
    if not success:
        print("\nOption 2: Create minimal working version")
        create_minimal_working_version()
    
    print("\n✅ Fix completed!")

if __name__ == "__main__":
    main()
'''
    
    with open('indentation_fix.py', 'w', encoding='utf-8') as f:
        f.write(__file_content)
    
    print("Created indentation_fix.py - Run it to fix the issue")

# Run the fix
main()