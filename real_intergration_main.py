# ai-content-factory/real_integration_main.py

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os
from dataclasses import asdict

# Real services imports
from trend_monitor.services.real_youtube_trends import RealYouTubeTrendsService, YouTubeTrendData
from trend_monitor.services.real_google_trends import RealGoogleTrendsService, GoogleTrendData
from content_engine.ai_services.real_ai_services import RealAIDirector, AIAnalysisResult

# Database imports (existing)
from database.repositories.trend_repository import TrendRepository
from database.repositories.opportunity_repository import OpportunityRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealContentFactory:
    """Main orchestrator for Real Data Integration"""
    
    def __init__(self, config: Dict[str, str]):
        # API Keys from config
        self.youtube_api_key = config.get("youtube_api_key")
        self.groq_api_key = config.get("groq_api_key") 
        self.openai_api_key = config.get("openai_api_key")
        
        # Services
        self.youtube_service = None
        self.google_trends_service = None
        self.ai_director = None
        
        # Database repositories
        self.trend_repo = TrendRepository()
        self.opportunity_repo = OpportunityRepository()
        
        # Tracking
        self.session_stats = {
            "trends_collected": 0,
            "opportunities_generated": 0,
            "api_calls_made": 0,
            "start_time": datetime.now()
        }
    
    async def __aenter__(self):
        """Initialize all services"""
        try:
            # Initialize YouTube service
            if self.youtube_api_key:
                self.youtube_service = RealYouTubeTrendsService(self.youtube_api_key)
                await self.youtube_service.__aenter__()
                logger.info("✅ YouTube API service initialized")
            else:
                logger.warning("❌ YouTube API key not provided")
            
            # Initialize Google Trends service
            self.google_trends_service = RealGoogleTrendsService(geo="TH")
            logger.info("✅ Google Trends service initialized")
            
            # Initialize AI Director
            if self.groq_api_key and self.openai_api_key:
                self.ai_director = RealAIDirector(self.groq_api_key, self.openai_api_key)
                await self.ai_director.__aenter__()
                logger.info("✅ AI Director initialized")
            else:
                logger.warning("❌ AI API keys not provided")
            
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all services"""
        if self.youtube_service:
            await self.youtube_service.__aexit__(exc_type, exc_val, exc_tb)
        if self.ai_director:
            await self.ai_director.__aexit__(exc_type, exc_val, exc_tb)
    
    async def collect_youtube_trends(self, region: str = "TH", max_results: int = 50) -> List[YouTubeTrendData]:
        """Collect trending videos from YouTube"""
        if not self.youtube_service:
            logger.error("YouTube service not available")
            return []
        
        try:
            logger.info(f"🔥 Collecting YouTube trends for region: {region}")
            trending_videos = await self.youtube_service.get_trending_videos(
                region_code=region, 
                max_results=max_results
            )
            
            self.session_stats["trends_collected"] += len(trending_videos)
            self.session_stats["api_calls_made"] += 1
            
            # Save to database
            for video in trending_videos:
                trend_data = {
                    "source": "youtube",
                    "topic": video.title,
                    "keywords": video.tags,
                    "popularity_score": min(video.view_count / 10000, 100),  # Normalize to 0-100
                    "growth_rate": 0.0,  # Will be calculated over time
                    "category": video.category_id,
                    "region": video.region,
                    "raw_data": {
                        "video_id": video.video_id,
                        "channel": video.channel_title,
                        "views": video.view_count,
                        "likes": video.like_count,
                        "comments": video.comment_count,
                        "published_at": video.published_at.isoformat(),
                        "trending_rank": video.trending_rank
                    }
                }
                await self.trend_repo.create_trend(trend_data)
            
            logger.info(f"✅ Collected {len(trending_videos)} YouTube trends")
            return trending_videos
            
        except Exception as e:
            logger.error(f"Error collecting YouTube trends: {e}")
            return []
    
    async def collect_google_trends(self, youtube_keywords: List[str] = None) -> List[GoogleTrendData]:
        """Collect Google Trends data"""
        if not self.google_trends_service:
            logger.error("Google Trends service not available")
            return []
        
        try:
            logger.info("🔍 Collecting Google Trends data")
            
            # Get trending searches
            trending_searches = await self.google_trends_service.get_trending_searches("thailand")
            
            # Correlate with YouTube keywords if provided
            if youtube_keywords:
                logger.info("🔗 Correlating with YouTube keywords")
                correlation_data = await self.google_trends_service.correlate_with_youtube_trends(youtube_keywords)
                trending_searches.extend([data.keyword for data in correlation_data])
            
            # Analyze top keywords
            top_keywords = list(set(trending_searches[:20]))  # Remove duplicates
            trend_data = await self.google_trends_service.analyze_multiple_keywords(top_keywords)
            
            self.session_stats["api_calls_made"] += len(top_keywords) // 5 + 1  # Batch processing
            
            # Save to database
            for data in trend_data:
                trend_entry = {
                    "source": "google_trends",
                    "topic": data.keyword,
                    "keywords": data.related_queries,
                    "popularity_score": data.interest_score,
                    "growth_rate": 0.0,  # Will be calculated over time
                    "category": "general",
                    "region": data.region,
                    "raw_data": {
                        "timeframe": data.timeframe,
                        "related_queries": data.related_queries,
                        "rising_queries": data.rising_queries,
                        "search_volume_trend": [(t.isoformat(), v) for t, v in data.search_volume_trend]
                    }
                }
                await self.trend_repo.create_trend(trend_entry)
            
            logger.info(f"✅ Collected {len(trend_data)} Google Trends")
            return trend_data
            
        except Exception as e:
            logger.error(f"Error collecting Google Trends: {e}")
            return []
    
    async def analyze_trends_with_ai(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Analyze recent trends with AI and generate opportunities"""
        if not self.ai_director:
            logger.error("AI Director not available")
            return []
        
        try:
            logger.info("🤖 Starting AI analysis of trends")
            
            # Get recent trends from database
            recent_trends = await self.trend_repo.get_recent_trends(hours=24, limit=limit)
            
            if not recent_trends:
                logger.warning("No recent trends found for analysis")
                return []
            
            # Convert to format for AI analysis
            trends_for_analysis = []
            for trend in recent_trends:
                trends_for_analysis.append({
                    "topic": trend.topic,
                    "popularity_score": int(trend.popularity_score),
                    "growth_rate": trend.growth_rate,
                    "keywords": trend.keywords or [],
                    "source": trend.source,
                    "trend_id": str(trend.id)
                })
            
            # AI batch analysis
            ai_results = await self.ai_director.batch_analyze_trends(trends_for_analysis)
            
            self.session_stats["opportunities_generated"] = len(ai_results)
            self.session_stats["api_calls_made"] += len(trends_for_analysis) * 2  # Groq + OpenAI
            
            # Save opportunities to database
            for result in ai_results:
                if result.get("success"):
                    analysis = result["analysis"]
                    
                    # Create opportunity for each content plan
                    for plan_data in result["content_plans"]:
                        opportunity = {
                            "trend_id": result["original_trend"]["trend_id"],
                            "suggested_angle": plan_data["angle"],
                            "estimated_views": int(analysis.overall_score * 10000),  # Rough estimate
                            "competition_level": "low" if analysis.content_saturation >= 7 else "medium" if analysis.content_saturation >= 4 else "high",
                            "production_cost": plan_data["plan"].production_estimate.get("cost_baht", 50),
                            "estimated_roi": analysis.overall_score,
                            "priority_score": analysis.overall_score,
                            "status": "pending",
                            "ai_analysis": {
                                "viral_potential": analysis.viral_potential,
                                "content_saturation": analysis.content_saturation,
                                "audience_interest": analysis.audience_interest,
                                "monetization_opportunity": analysis.monetization_opportunity,
                                "reasoning": analysis.reasoning,
                                "content_plan": asdict(plan_data["plan"]),
                                "script": plan_data.get("script")
                            }
                        }
                        await self.opportunity_repo.create_opportunity(opportunity)
            
            logger.info(f"✅ AI analysis complete: {len(ai_results)} opportunities generated")
            return ai_results
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return []
    
    async def run_full_pipeline(self, region: str = "TH") -> Dict[str, Any]:
        """Run the complete real data pipeline"""
        logger.info("🚀 Starting Full Real Data Pipeline")
        
        pipeline_start = datetime.now()
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
            logger.info("📺 Step 1: Collecting YouTube trends...")
            youtube_trends = await self.collect_youtube_trends(region=region, max_results=30)
            results["youtube_trends"] = [asdict(trend) for trend in youtube_trends]
            
            if not youtube_trends:
                results["errors"].append("Failed to collect YouTube trends")
            
            # Step 2: Extract keywords from YouTube trends
            youtube_keywords = []
            if youtube_trends:
                for video in youtube_trends:
                    youtube_keywords.extend(video.tags)
                    # Add title words
                    youtube_keywords.extend(video.title.split())
                
                # Clean and deduplicate
                youtube_keywords = list(set([kw.lower() for kw in youtube_keywords if len(kw) > 2]))[:50]
            
            # Step 3: Collect Google Trends
            logger.info("🔍 Step 2: Collecting Google trends...")
            google_trends = await self.collect_google_trends(youtube_keywords)
            results["google_trends"] = [asdict(trend) for trend in google_trends]
            
            if not google_trends:
                results["errors"].append("Failed to collect Google trends")
            
            # Step 4: AI Analysis
            logger.info("🤖 Step 3: AI analysis and opportunity generation...")
            ai_opportunities = await self.analyze_trends_with_ai(limit=15)
            results["ai_opportunities"] = ai_opportunities
            
            if not ai_opportunities:
                results["errors"].append("Failed to generate AI opportunities")
            
            # Compile statistics
            pipeline_duration = (datetime.now() - pipeline_start).total_seconds()
            results["statistics"] = {
                "pipeline_duration_seconds": round(pipeline_duration, 2),
                "youtube_trends_collected": len(youtube_trends),
                "google_trends_collected": len(google_trends),
                "ai_opportunities_generated": len(ai_opportunities),
                "total_api_calls": self.session_stats["api_calls_made"],
                "youtube_quota_used": self.youtube_service.daily_quota_used if self.youtube_service else 0,
                "google_requests_made": self.google_trends_service.request_count if self.google_trends_service else 0
            }
            
            logger.info("✅ Full pipeline completed successfully!")
            logger.info(f"   📊 Stats: {results['statistics']}")
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            results["success"] = False
            results["errors"].append(f"Pipeline error: {str(e)}")
        
        return results
    
    async def get_top_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top opportunities from database"""
        try:
            opportunities = await self.opportunity_repo.get_top_opportunities(limit=limit)
            
            result = []
            for opp in opportunities:
                result.append({
                    "id": str(opp.id),
                    "trend_topic": opp.trend.topic if opp.trend else "Unknown",
                    "suggested_angle": opp.suggested_angle,
                    "priority_score": opp.priority_score,
                    "estimated_roi": opp.estimated_roi,
                    "competition_level": opp.competition_level,
                    "production_cost": opp.production_cost,
                    "status": opp.status,
                    "created_at": opp.created_at.isoformat(),
                    "ai_analysis": opp.ai_analysis
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting top opportunities: {e}")
            return []


# Configuration and main execution
def load_config() -> Dict[str, str]:
    """Load configuration from environment or config file"""
    config = {
        "youtube_api_key": os.getenv("YOUTUBE_API_KEY", ""),
        "groq_api_key": os.getenv("GROQ_API_KEY", "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"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", "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")
    }
    
    # Validate required keys
    missing_keys = [key for key, value in config.items() if not value]
    if missing_keys:
        logger.warning(f"Missing API keys: {missing_keys}")
    
    return config


async def test_real_integration():
    """Test the real integration pipeline"""
    print("🚀 Testing Real Data Integration Pipeline")
    print("=" * 50)
    
    config = load_config()
    
    async with RealContentFactory(config) as factory:
        
        # Test 1: Run full pipeline
        print("\n🔄 Running full pipeline...")
        results = await factory.run_full_pipeline("TH")
        
        if results["success"]:
            stats = results["statistics"]
            print(f"✅ Pipeline completed in {stats['pipeline_duration_seconds']}s")
            print(f"   📺 YouTube trends: {stats['youtube_trends_collected']}")
            print(f"   🔍 Google trends: {stats['google_trends_collected']}")
            print(f"   🤖 AI opportunities: {stats['ai_opportunities_generated']}")
            print(f"   📊 Total API calls: {stats['total_api_calls']}")
            
            if results["errors"]:
                print(f"   ⚠️  Errors: {results['errors']}")
        else:
            print(f"❌ Pipeline failed: {results['errors']}")
        
        # Test 2: Get top opportunities
        print("\n🎯 Top opportunities:")
        opportunities = await factory.get_top_opportunities(5)
        
        for i, opp in enumerate(opportunities):
            print(f"   {i+1}. {opp['trend_topic']}")
            print(f"      Angle: {opp['suggested_angle']}")
            print(f"      Score: {opp['priority_score']:.1f}/10")
            print(f"      ROI: {opp['estimated_roi']:.1f}")
            print(f"      Cost: ฿{opp['production_cost']}")
            print()


async def run_scheduled_pipeline():
    """Run pipeline for scheduled execution"""
    logger.info("🕒 Starting scheduled pipeline execution")
    
    config = load_config()
    
    try:
        async with RealContentFactory(config) as factory:
            results = await factory.run_full_pipeline("TH")
            
            # Log results
            if results["success"]:
                stats = results["statistics"]
                logger.info(f"Scheduled pipeline completed successfully:")
                logger.info(f"  - Duration: {stats['pipeline_duration_seconds']}s")
                logger.info(f"  - YouTube trends: {stats['youtube_trends_collected']}")
                logger.info(f"  - Google trends: {stats['google_trends_collected']}")
                logger.info(f"  - AI opportunities: {stats['ai_opportunities_generated']}")
                
                # Save results to file for monitoring
                with open(f"pipeline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                    json.dump(results, f, indent=2, default=str)
                    
            else:
                logger.error(f"Scheduled pipeline failed: {results['errors']}")
                
    except Exception as e:
        logger.error(f"Scheduled pipeline error: {e}")


class RealDataAPI:
    """FastAPI integration for real data pipeline"""
    
    def __init__(self):
        self.factory = None
        self.config = load_config()
    
    async def initialize(self):
        """Initialize the factory"""
        self.factory = RealContentFactory(self.config)
        await self.factory.__aenter__()
    
    async def shutdown(self):
        """Shutdown the factory"""
        if self.factory:
            await self.factory.__aexit__(None, None, None)
    
    async def trigger_pipeline(self, region: str = "TH") -> Dict[str, Any]:
        """API endpoint to trigger pipeline"""
        if not self.factory:
            await self.initialize()
        
        return await self.factory.run_full_pipeline(region)
    
    async def get_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """API endpoint to get opportunities"""
        if not self.factory:
            await self.initialize()
        
        return await self.factory.get_top_opportunities(limit)
    
    async def get_recent_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        """API endpoint to get recent trends"""
        if not self.factory:
            await self.initialize()
        
        try:
            trends = await self.factory.trend_repo.get_recent_trends(hours=hours, limit=50)
            
            result = []
            for trend in trends:
                result.append({
                    "id": str(trend.id),
                    "source": trend.source,
                    "topic": trend.topic,
                    "keywords": trend.keywords,
                    "popularity_score": trend.popularity_score,
                    "growth_rate": trend.growth_rate,
                    "category": trend.category,
                    "region": trend.region,
                    "collected_at": trend.collected_at.isoformat(),
                    "raw_data": trend.raw_data
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent trends: {e}")
            return []


# Requirements for new dependencies
REQUIREMENTS_ADDITION = """
# Add these to requirements.txt for real integration:

# YouTube API
google-api-python-client>=2.100.0

# Google Trends
pytrends>=4.9.2

# AI Services
openai>=1.0.0
groq>=0.4.0

# Additional async support
aiofiles>=23.0.0
asyncpg>=0.28.0  # if using PostgreSQL instead of SQLite

# Rate limiting and caching
aioredis>=2.0.0  # optional for advanced caching
"""

# Updated Docker configuration
DOCKER_COMPOSE_UPDATE = """
# Add to docker-compose.yml for real integration:

version: '3.8'
services:
  # ... existing services ...
  
  real-content-factory:
    build: 
      context: .
      dockerfile: Dockerfile.real
    environment:
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    
  # Scheduler for automated pipeline runs
  pipeline-scheduler:
    image: mcuadros/ofelia:latest
    depends_on:
      - real-content-factory
    command: daemon --docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      ofelia.job-run.pipeline.schedule: "0 */6 * * *"  # Every 6 hours
      ofelia.job-run.pipeline.container: "real-content-factory"
      ofelia.job-run.pipeline.command: "python real_integration_main.py --scheduled"
"""

# Environment variables template
ENV_TEMPLATE = """
# .env file template for real integration

# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key_here

# AI Services
GROQ_API_KEY=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
OPENAI_API_KEY=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

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/content_factory

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
"""


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        # Scheduled execution
        asyncio.run(run_scheduled_pipeline())
    else:
        # Interactive testing
        asyncio.run(test_real_integration())