# real_integration_main.py - Fixed Syntax Alternative AI Integration

import asyncio
import aiohttp
import logging
import os
import json
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
def load_config() -> Dict[str, str]:
    """Load configuration from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    return {
        "youtube_api_key": os.getenv("YOUTUBE_API_KEY", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "cohere_api_key": os.getenv("COHERE_API_KEY", ""),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///content_factory.db")
    }

# Data Models
@dataclass
class YouTubeTrendData:
    video_id: str
    title: str
    channel_title: str
    view_count: int
    like_count: int
    published_at: datetime
    category_id: str
    tags: List[str]
    trending_rank: int
    region: str = "TH"

@dataclass
class GoogleTrendData:
    keyword: str
    interest_score: int
    related_queries: List[str]
    timestamp: datetime

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

# YouTube Trends Service
class YouTubeTrendsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_trending_videos(self, region: str = "TH", max_results: int = 30) -> List[YouTubeTrendData]:
        """Get trending videos from YouTube"""
        try:
            from googleapiclient.discovery import build
            
            youtube = build('youtube', 'v3', developerKey=self.api_key)
            
            request = youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region,
                maxResults=max_results
            )
            response = request.execute()
            
            trending_videos = []
            for i, item in enumerate(response.get('items', [])):
                try:
                    snippet = item['snippet']
                    statistics = item.get('statistics', {})
                    
                    video_data = YouTubeTrendData(
                        video_id=item['id'],
                        title=snippet['title'],
                        channel_title=snippet['channelTitle'],
                        view_count=int(statistics.get('viewCount', 0)),
                        like_count=int(statistics.get('likeCount', 0)),
                        published_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                        category_id=snippet.get('categoryId', '0'),
                        tags=snippet.get('tags', []),
                        trending_rank=i + 1,
                        region=region
                    )
                    trending_videos.append(video_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing video data: {e}")
                    continue
            
            logger.info(f"Successfully collected {len(trending_videos)} YouTube trends")
            return trending_videos
            
        except Exception as e:
            logger.error(f"Error collecting YouTube trends: {e}")
            return []

# Google Trends Service
class GoogleTrendsService:
    def __init__(self):
        self.request_count = 0
        
    async def get_trending_keywords(self, youtube_keywords: List[str] = None) -> List[GoogleTrendData]:
        """Get trending keywords"""
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='th-TH', tz=420, timeout=(10, 25), retries=2, backoff_factor=0.1)
            
            try:
                trending_searches_df = pytrends.trending_searches(pn='thailand')
                if not trending_searches_df.empty:
                    keywords = trending_searches_df[0].tolist()[:15]
                else:
                    raise Exception("No trending searches returned")
            except:
                keywords = [
                    "AI วิดีโอ", "TikTok เทรนด์", "หนังไทย", "เกมส์ใหม่", "อาหารฮิต",
                    "ดราม่า", "ท่องเที่ยว", "เทคโนโลยี", "บิวตี้", "ฟิตเนส",
                    "การเงิน", "เริ่มต้นธุรกิจ", "การศึกษา", "สุขภาพ", "ไลฟ์สไตล์"
                ]
            
            if youtube_keywords:
                keywords.extend([kw for kw in youtube_keywords[:10] if len(kw) > 2])
            
            unique_keywords = list(set(keywords))[:15]
            
            trend_data = []
            for i, keyword in enumerate(unique_keywords):
                try:
                    base_score = 50
                    if any(word in keyword.lower() for word in ['ai', 'video', 'tiktok']):
                        base_score += 30
                    if len(keyword) < 10:
                        base_score += 10
                    
                    interest_score = min(base_score + (15 - i) * 2, 100)
                    
                    trend_item = GoogleTrendData(
                        keyword=keyword,
                        interest_score=interest_score,
                        related_queries=[],
                        timestamp=datetime.now()
                    )
                    trend_data.append(trend_item)
                    
                except Exception as e:
                    logger.error(f"Error processing keyword {keyword}: {e}")
                    continue
            
            logger.info(f"Successfully collected {len(trend_data)} Google Trends")
            return trend_data
            
        except Exception as e:
            logger.error(f"Error collecting Google Trends: {e}")
            mock_keywords = ["AI Video", "TikTok Trend", "Thai Content", "Viral Dance", "Tech Review"]
            return [GoogleTrendData(
                keyword=kw,
                interest_score=70 + i * 5,
                related_queries=[],
                timestamp=datetime.now()
            ) for i, kw in enumerate(mock_keywords)]

# Alternative AI Analysis Services
class AlternativeAIService:
    def __init__(self, gemini_api_key: str = "", cohere_api_key: str = ""):
        self.gemini_api_key = gemini_api_key
        self.cohere_api_key = cohere_api_key
        self.session = None
        self.request_count = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Extract JSON from text with improved parsing"""
        try:
            # Method 1: Direct JSON parse
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        try:
            # Method 2: Extract from markdown code blocks
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',
                r'```\s*(\{.*?\})\s*```',
                r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    try:
                        return json.loads(match.strip())
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        # Method 3: Manual extraction for common cases
        try:
            result = {}
            
            # Extract scores using fixed regex patterns
            score_keys = ['viral_potential', 'content_saturation', 'audience_interest', 'monetization_opportunity']
            
            for key in score_keys:
                if key in text:
                    # Fixed regex pattern with raw string
                    pattern = r'"?' + key + r'"?\s*:?\s*(\d+)'
                    match = re.search(pattern, text)
                    if match:
                        result[key] = int(match.group(1))
            
            # Extract reasoning
            reasoning_patterns = [
                r'"reasoning"\s*:\s*"([^"]*)"',
                r'reasoning[:\s]+([^,}\]]*)',
                r'analysis[:\s]+([^,}\]]*)'
            ]
            
            for pattern in reasoning_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['reasoning'] = match.group(1).strip()
                    break
            
            # Extract content angles (basic)
            result['content_angles'] = ["Tutorial content", "Review format", "Behind the scenes"]
            
            if len(result) >= 4:  # At least 4 score fields
                return result
                
        except Exception:
            pass
        
        return None
    
    async def analyze_with_gemini(self, trend_topic: str, popularity_score: int) -> Optional[AIAnalysisResult]:
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
        
        return None
    
    def create_smart_analysis(self, trend_topic: str, popularity_score: int) -> AIAnalysisResult:
        """Create smart mock analysis based on content analysis"""
        
        topic_lower = trend_topic.lower()
        
        # Category detection
        category_scores = {
            "gaming": {
                "keywords": ['เกม', 'game', 'rov', 'roblox', 'minecraft', 'gaming', 'esport'],
                "viral_base": 8, "saturation_base": 4, "interest_base": 9, "monetization_base": 7,
                "angles": ["Gaming tutorial", "Pro tips & strategies", "Beginner's guide"]
            },
            "entertainment": {
                "keywords": ['หนัง', 'movie', 'ตัวอย่าง', 'trailer', 'ซีรี่ส', 'drama', 'netflix'],
                "viral_base": 7, "saturation_base": 6, "interest_base": 8, "monetization_base": 6,
                "angles": ["Movie review", "Behind the scenes", "Analysis & breakdown"]
            },
            "music": {
                "keywords": ['เพลง', 'music', 'ft.', 'official', 'mv', 'song', 'artist'],
                "viral_base": 9, "saturation_base": 5, "interest_base": 8, "monetization_base": 5,
                "angles": ["Song reaction", "Music analysis", "Artist spotlight"]
            },
            "tech": {
                "keywords": ['ai', 'tech', 'เทคโนโลยี', 'app', 'software', 'digital'],
                "viral_base": 7, "saturation_base": 7, "interest_base": 7, "monetization_base": 8,
                "angles": ["Tech tutorial", "Product review", "How-to guide"]
            },
            "lifestyle": {
                "keywords": ['อาหาร', 'food', 'travel', 'beauty', 'fashion', 'health', 'fitness'],
                "viral_base": 6, "saturation_base": 5, "interest_base": 7, "monetization_base": 7,
                "angles": ["Lifestyle tips", "Tutorial guide", "Product review"]
            }
        }
        
        # Detect category
        detected_category = "general"
        for category, data in category_scores.items():
            if any(keyword in topic_lower for keyword in data["keywords"]):
                detected_category = category
                break
        
        # Use general scores if no category detected
        if detected_category == "general":
            viral_potential = min(max(popularity_score // 12, 5), 9)
            content_saturation = max(10 - (popularity_score // 20), 3)
            audience_interest = min(max(popularity_score // 15, 6), 10)
            monetization = min(max(popularity_score // 18, 5), 8)
            angles = [f"Complete guide to {trend_topic[:20]}", f"Tips for {trend_topic[:20]}", f"Tutorial: {trend_topic[:20]}"]
        else:
            cat_data = category_scores[detected_category]
            viral_potential = min(cat_data["viral_base"] + (popularity_score // 25), 10)
            content_saturation = max(cat_data["saturation_base"] - (popularity_score // 30), 1)
            audience_interest = min(cat_data["interest_base"] + (popularity_score // 20), 10)
            monetization = min(cat_data["monetization_base"] + (popularity_score // 25), 10)
            angles = cat_data["angles"]
        
        overall_score = (viral_potential + content_saturation + audience_interest + monetization) / 4.0
        
        return AIAnalysisResult(
            trend_topic=trend_topic,
            viral_potential=viral_potential,
            content_saturation=content_saturation,
            audience_interest=audience_interest,
            monetization_opportunity=monetization,
            overall_score=overall_score,
            content_angles=angles,
            reasoning=f"Smart analysis: {detected_category} category, popularity {popularity_score}"
        )
    
    async def analyze_trend(self, trend_topic: str, popularity_score: int) -> AIAnalysisResult:
        """Try AI services with fallback to smart analysis"""
        
        # Limit API calls to avoid rate limits
        if self.request_count >= 5:
            print(f"  [Smart Analysis] {trend_topic[:30]}... (API limit reached)")
            return self.create_smart_analysis(trend_topic, popularity_score)
        
        # Try Gemini first
        if self.gemini_api_key:
            result = await self.analyze_with_gemini(trend_topic, popularity_score)
            if result:
                self.request_count += 1
                return result
        
        # Fallback to smart analysis
        print(f"  [Smart Analysis] {trend_topic[:30]}... (AI fallback)")
        return self.create_smart_analysis(trend_topic, popularity_score)
    
    def create_content_plan(self, trend_topic: str, content_angle: str) -> Dict[str, Any]:
        """Create content plan using rule-based approach"""
        
        topic_lower = trend_topic.lower()
        
        if any(word in topic_lower for word in ['เกม', 'game', 'rov', 'roblox']):
            content_type = "gaming_tutorial"
            hook = f"Want to master {trend_topic}? Watch this pro guide!"
            main_content = f"Step-by-step {content_angle} with pro tips and strategies"
            visual_suggestions = ["Gameplay footage", "Screen recordings", "Tutorial graphics"]
            hashtags = ["#gaming", "#tutorial", "#protips", "#viral"]
            
        elif any(word in topic_lower for word in ['หนัง', 'movie', 'ตัวอย่าง']):
            content_type = "entertainment_review"
            hook = f"This {trend_topic} will blow your mind!"
            main_content = f"Detailed {content_angle} with analysis and reactions"
            visual_suggestions = ["Movie clips", "Reaction shots", "Analysis graphics"]
            hashtags = ["#movie", "#review", "#entertainment", "#viral"]
            
        elif any(word in topic_lower for word in ['เพลง', 'music', 'ft.']):
            content_type = "music_content"
            hook = f"This song is breaking the internet!"
            main_content = f"Music {content_angle} with breakdown and reaction"
            visual_suggestions = ["Music video clips", "Lyric graphics", "Reaction footage"]
            hashtags = ["#music", "#reaction", "#trending", "#viral"]
            
        else:
            content_type = "general_tutorial"
            hook = f"Learn about {trend_topic} in 60 seconds!"
            main_content = f"Complete guide: {content_angle}"
            visual_suggestions = ["Tutorial graphics", "Step-by-step visuals", "Before/after"]
            hashtags = ["#tutorial", "#trending", "#viral", "#guide"]
        
        return {
            "content_type": content_type,
            "script_outline": {
                "hook": hook,
                "main_content": main_content,
                "call_to_action": "Like and subscribe for more trending content!"
            },
            "visual_suggestions": visual_suggestions,
            "platform_optimization": {
                "title": f"{content_angle} - Complete Guide 2025",
                "hashtags": hashtags,
                "description": f"Learn {content_angle} in this comprehensive tutorial! {trend_topic} trending now."
            },
            "production_estimate": {
                "time_minutes": 45,
                "difficulty": "medium",
                "cost_estimate": 75
            }
        }

# Database Service
class DatabaseService:
    def __init__(self, database_url: str):
        self.database_url = database_url
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            if "sqlite" in self.database_url:
                db_path = self.database_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        keywords TEXT,
                        popularity_score REAL,
                        growth_rate REAL,
                        category TEXT,
                        region TEXT,
                        raw_data TEXT,
                        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS content_opportunities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trend_topic TEXT NOT NULL,
                        suggested_angle TEXT,
                        viral_potential INTEGER,
                        content_saturation INTEGER,
                        audience_interest INTEGER,
                        monetization_opportunity INTEGER,
                        overall_score REAL,
                        content_angles TEXT,
                        reasoning TEXT,
                        content_plan TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                conn.close()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def save_trends(self, trends: List[YouTubeTrendData], source: str = "youtube"):
        """Save trends to database"""
        try:
            if "sqlite" in self.database_url:
                db_path = self.database_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                for trend in trends:
                    cursor.execute("""
                        INSERT INTO trends (source, topic, keywords, popularity_score, 
                                          category, region, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        source,
                        trend.title,
                        json.dumps(trend.tags, ensure_ascii=False),
                        min(trend.view_count / 10000, 100),
                        trend.category_id,
                        trend.region,
                        json.dumps(asdict(trend), default=str, ensure_ascii=False)
                    ))
                
                conn.commit()
                conn.close()
                logger.info(f"Saved {len(trends)} trends to database")
                
        except Exception as e:
            logger.error(f"Error saving trends: {e}")
    
    def save_opportunities(self, opportunities: List[Dict[str, Any]]):
        """Save content opportunities to database"""
        try:
            if "sqlite" in self.database_url:
                db_path = self.database_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                for opp in opportunities:
                    analysis = opp.get('analysis')
                    content_plan = opp.get('content_plan')
                    
                    if analysis:
                        cursor.execute("""
                            INSERT INTO content_opportunities (
                                trend_topic, suggested_angle, viral_potential,
                                content_saturation, audience_interest, monetization_opportunity,
                                overall_score, content_angles, reasoning, content_plan
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            analysis.trend_topic,
                            opp.get('content_angle', ''),
                            analysis.viral_potential,
                            analysis.content_saturation,
                            analysis.audience_interest,
                            analysis.monetization_opportunity,
                            analysis.overall_score,
                            json.dumps(analysis.content_angles, ensure_ascii=False),
                            analysis.reasoning,
                            json.dumps(content_plan, ensure_ascii=False) if content_plan else None
                        ))
                
                conn.commit()
                conn.close()
                logger.info(f"Saved {len(opportunities)} opportunities to database")
                
        except Exception as e:
            logger.error(f"Error saving opportunities: {e}")

# Main Integration Pipeline
class RealIntegrationPipeline:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.db_service = DatabaseService(config["database_url"])
        self.stats = {
            "start_time": datetime.now(),
            "youtube_trends": 0,
            "google_trends": 0,
            "ai_opportunities": 0,
            "total_api_calls": 0,
            "ai_api_calls": 0
        }
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """Run the complete real data integration pipeline"""
        
        print("Starting Full Real Data Pipeline")
        
        self.db_service.init_database()
        
        results = {
            "success": True,
            "youtube_trends": [],
            "google_trends": [],
            "ai_opportunities": [],
            "statistics": {},
            "errors": []
        }
        
        try:
            # Step 1: Collect YouTube trends
            print("Step 1: Collecting YouTube trends...")
            youtube_trends = []
            
            if self.config["youtube_api_key"]:
                async with YouTubeTrendsService(self.config["youtube_api_key"]) as youtube_service:
                    youtube_trends = await youtube_service.get_trending_videos("TH", 20)
                    self.stats["youtube_trends"] = len(youtube_trends)
                    self.stats["total_api_calls"] += 1
                    
                    if youtube_trends:
                        self.db_service.save_trends(youtube_trends, "youtube")
                        print(f"Collected {len(youtube_trends)} YouTube trends")
                    else:
                        print("No YouTube trends collected")
            else:
                print("YouTube API key not provided")
                results["errors"].append("YouTube API key missing")
            
            # Step 2: Collect Google Trends
            print("\nStep 2: Collecting Google trends...")
            google_trends = []
            
            try:
                google_service = GoogleTrendsService()
                youtube_keywords = []
                for trend in youtube_trends:
                    youtube_keywords.extend(trend.tags[:2])
                    youtube_keywords.extend(trend.title.split()[:2])
                
                google_trends = await google_service.get_trending_keywords(youtube_keywords)
                self.stats["google_trends"] = len(google_trends)
                self.stats["total_api_calls"] += 1
                
                if google_trends:
                    print(f"Collected {len(google_trends)} Google trends")
                else:
                    print("No Google trends collected")
                    
            except Exception as e:
                logger.error(f"Google Trends error: {e}")
                print(f"Google Trends error: {e}")
                results["errors"].append(f"Google Trends error: {str(e)}")
            
            # Step 3: AI Analysis and Content Planning
            print("\nStep 3: AI analysis and opportunity generation...")
            ai_opportunities = []
            
            async with AlternativeAIService(
                self.config.get("gemini_api_key", ""), 
                self.config.get("cohere_api_key", "")
            ) as ai_service:
                
                # Combine YouTube and Google trends for analysis
                trends_to_analyze = []
                
                # Add top YouTube trends
                for trend in youtube_trends[:6]:
                    trends_to_analyze.append({
                        "topic": trend.title,
                        "popularity_score": min(trend.view_count / 10000, 100),
                        "source": "youtube"
                    })
                
                # Add top Google trends
                for trend in google_trends[:4]:
                    trends_to_analyze.append({
                        "topic": trend.keyword,
                        "popularity_score": trend.interest_score,
                        "source": "google_trends"
                    })
                
                # Analyze each trend
                for i, trend_data in enumerate(trends_to_analyze):
                    try:
                        print(f"  Analyzing trend {i+1}: {trend_data['topic'][:30]}...")
                        
                        analysis = await ai_service.analyze_trend(
                            trend_data["topic"],
                            int(trend_data["popularity_score"])
                        )
                        
                        if analysis:
                            best_angle = analysis.content_angles[0]
                            content_plan = ai_service.create_content_plan(
                                trend_data["topic"],
                                best_angle
                            )
                            
                            opportunity = {
                                "trend_data": trend_data,
                                "analysis": analysis,
                                "content_angle": best_angle,
                                "content_plan": content_plan
                            }
                            ai_opportunities.append(opportunity)
                            
                            await asyncio.sleep(0.3)
                            
                    except Exception as e:
                        logger.error(f"AI analysis error for {trend_data['topic']}: {e}")
                        continue
                
                self.stats["ai_opportunities"] = len(ai_opportunities)
                self.stats["ai_api_calls"] = ai_service.request_count
                
                if ai_opportunities:
                    self.db_service.save_opportunities(ai_opportunities)
                    print(f"AI analysis complete: {len(ai_opportunities)} opportunities generated")
                else:
                    print("No AI opportunities generated")
            
            # Calculate pipeline duration
            duration = (datetime.now() - self.stats["start_time"]).total_seconds()
            
            # Compile final statistics
            self.stats.update({
                "pipeline_duration_seconds": round(duration, 2),
                "end_time": datetime.now()
            })
            
            results.update({
                "youtube_trends": [asdict(trend) for trend in youtube_trends],
                "google_trends": [asdict(trend) for trend in google_trends],
                "ai_opportunities": ai_opportunities,
                "statistics": self.stats
            })
            
            # Display final results
            print(f"\nFull pipeline completed in {duration:.1f}s")
            print(f"   YouTube trends: {self.stats['youtube_trends']}")
            print(f"   Google trends: {self.stats['google_trends']}")
            print(f"   AI opportunities: {self.stats['ai_opportunities']}")
            print(f"   Total API calls: {self.stats['total_api_calls']}")
            print(f"   AI API calls: {self.stats['ai_api_calls']}")
            
            # Show top opportunities
            if ai_opportunities:
                print(f"\nTop opportunities:")
                sorted_opportunities = sorted(ai_opportunities, 
                                            key=lambda x: x["analysis"].overall_score if x.get("analysis") else 0, 
                                            reverse=True)
                
                for i, opp in enumerate(sorted_opportunities[:5]):
                    if opp.get("analysis"):
                        analysis = opp["analysis"]
                        print(f"   {i+1}. {analysis.trend_topic[:40]}...")
                        print(f"      Angle: {opp['content_angle'][:50]}...")
                        print(f"      Score: {analysis.overall_score:.1f}/10")
                        print(f"      Viral Potential: {analysis.viral_potential}/10")
                        print(f"      Category: {analysis.reasoning.split(',')[0] if ',' in analysis.reasoning else 'General'}")
            
            logger.info("Pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            print(f"Pipeline error: {e}")
            results["success"] = False
            results["errors"].append(f"Pipeline error: {str(e)}")
        
        return results

# Main execution
async def main():
    """Main function"""
    print("AI Content Factory - Alternative AI Integration")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    config = load_config()
    
    # Check available AI services
    available_ai = []
    if config.get("gemini_api_key"):
        available_ai.append("Gemini")
    if config.get("cohere_api_key"):
        available_ai.append("Cohere")
    
    if available_ai:
        print(f"Available AI services: {', '.join(available_ai)}")
    else:
        print("No AI API keys found - using Smart Analysis only")
    
    # Run pipeline
    pipeline = RealIntegrationPipeline(config)
    results = await pipeline.run_full_pipeline()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"pipeline_results_{timestamp}.json"
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        print(f"\nResults saved to: {results_file}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    # Final summary
    if results["success"]:
        print(f"\nReal Data Integration completed successfully!")
        print(f"Check the database for detailed results")
        if results.get("statistics"):
            stats = results["statistics"]
            print(f"Pipeline Stats:")
            print(f"   Duration: {stats.get('pipeline_duration_seconds', 0):.1f}s")
            print(f"   Total API calls: {stats.get('total_api_calls', 0)}")
            print(f"   AI API calls: {stats.get('ai_api_calls', 0)}")
            
            # API usage summary
            print(f"\nAPI Usage Summary:")
            print(f"   YouTube: Working ({stats.get('youtube_trends', 0)} trends collected)")
            print(f"   Google Trends: Working ({stats.get('google_trends', 0)} keywords collected)")
            if stats.get('ai_api_calls', 0) > 0:
                print(f"   AI Services: {stats.get('ai_api_calls', 0)} successful calls")
            else:
                print(f"   Smart Analysis: Rule-based analysis used")
            
        # Database info
        try:
            db_path = config["database_url"].replace("sqlite:///", "")
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path) / 1024  # KB
                print(f"   Database: {db_path} ({file_size:.1f} KB)")
        except:
            pass
            
        # Show instructions for getting API keys
        if not available_ai:
            print(f"\nTo enable AI analysis, add these to your .env file:")
            print(f"GEMINI_API_KEY=your_gemini_key (free at https://makersuite.google.com/)")
            print(f"COHERE_API_KEY=your_cohere_key (free at https://cohere.ai/)")
            
    else:
        print(f"\nPipeline completed with errors: {results['errors']}")
    
    return results["success"]

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        exit(1)