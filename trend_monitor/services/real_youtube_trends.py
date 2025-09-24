# ai-content-factory/trend-monitor/services/real_youtube_trends.py

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from dataclasses import dataclass

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class YouTubeTrendData:
    video_id: str
    title: str
    channel_title: str
    view_count: int
    like_count: int
    comment_count: int
    published_at: datetime
    category_id: str
    tags: List[str]
    description: str
    trending_rank: int
    region: str = "TH"

class RealYouTubeTrendsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.session = None
        self.daily_quota_used = 0
        self.max_daily_quota = 9000  # ปลอดภัยต่ำกว่า limit
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def check_quota(self, estimated_cost: int = 100) -> bool:
        """ตรวจสอบ quota ก่อนทำ API call"""
        if self.daily_quota_used + estimated_cost > self.max_daily_quota:
            logger.warning(f"Quota limit reached: {self.daily_quota_used}/{self.max_daily_quota}")
            return False
        return True
    
    async def get_trending_videos(self, 
                                region_code: str = "TH", 
                                category_id: Optional[str] = None,
                                max_results: int = 50) -> List[YouTubeTrendData]:
        """ดึง trending videos จาก YouTube"""
        
        if not self.check_quota(100):
            logger.error("API quota exceeded")
            return []
            
        try:
            # Build API URL
            url = f"{self.base_url}/videos"
            params = {
                "part": "snippet,statistics,contentDetails",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": min(max_results, 50),
                "key": self.api_key
            }
            
            if category_id:
                params["videoCategoryId"] = category_id
            
            logger.info(f"Fetching trending videos for region: {region_code}")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.daily_quota_used += 100  # YouTube API quota cost
                    
                    trending_videos = []
                    for i, item in enumerate(data.get("items", [])):
                        try:
                            video_data = self._parse_video_data(item, i + 1, region_code)
                            trending_videos.append(video_data)
                        except Exception as e:
                            logger.error(f"Error parsing video data: {e}")
                            continue
                    
                    logger.info(f"Successfully fetched {len(trending_videos)} trending videos")
                    return trending_videos
                    
                elif response.status == 403:
                    logger.error("API key invalid or quota exceeded")
                    return []
                else:
                    logger.error(f"API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching trending videos: {e}")
            return []
    
    def _parse_video_data(self, item: Dict, rank: int, region: str) -> YouTubeTrendData:
        """แปลง YouTube API response เป็น YouTubeTrendData"""
        snippet = item["snippet"]
        statistics = item.get("statistics", {})
        
        # Parse published date
        published_at = datetime.fromisoformat(
            snippet["publishedAt"].replace("Z", "+00:00")
        )
        
        return YouTubeTrendData(
            video_id=item["id"],
            title=snippet["title"],
            channel_title=snippet["channelTitle"],
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            published_at=published_at,
            category_id=snippet.get("categoryId", "0"),
            tags=snippet.get("tags", []),
            description=snippet.get("description", ""),
            trending_rank=rank,
            region=region
        )
    
    async def get_trending_by_category(self, region_code: str = "TH") -> Dict[str, List[YouTubeTrendData]]:
        """ดึง trending videos แยกตาม category"""
        
        # YouTube category IDs ที่น่าสนใจ
        categories = {
            "Entertainment": "24",
            "Gaming": "20", 
            "Music": "10",
            "Comedy": "23",
            "Education": "27",
            "Science & Technology": "28",
            "Sports": "17"
        }
        
        results = {}
        
        for category_name, category_id in categories.items():
            if not self.check_quota(100):
                logger.warning(f"Quota limit reached, skipping category: {category_name}")
                break
                
            logger.info(f"Fetching trending videos for category: {category_name}")
            videos = await self.get_trending_videos(
                region_code=region_code,
                category_id=category_id,
                max_results=20
            )
            results[category_name] = videos
            
            # Rate limiting - หน่วงเวลาระหว่าง requests
            await asyncio.sleep(0.5)
        
        return results
    
    async def analyze_trending_keywords(self, trending_videos: List[YouTubeTrendData]) -> Dict[str, int]:
        """วิเคราะห์ keywords ที่ trending"""
        keyword_counts = {}
        
        for video in trending_videos:
            # Extract keywords from title
            title_words = video.title.lower().split()
            for word in title_words:
                # กรองคำที่มีความหมาย (ยาวกว่า 2 ตัวอักษร)
                if len(word) > 2:
                    keyword_counts[word] = keyword_counts.get(word, 0) + 1
            
            # Extract from tags
            for tag in video.tags:
                if len(tag) > 2:
                    keyword_counts[tag.lower()] = keyword_counts.get(tag.lower(), 0) + 1
        
        # เรียงตามความถี่
        sorted_keywords = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True))
        return dict(list(sorted_keywords.items())[:50])  # top 50 keywords
    
    def get_quota_status(self) -> Dict[str, int]:
        """ตรวจสอบสถานะ quota"""
        return {
            "used": self.daily_quota_used,
            "remaining": self.max_daily_quota - self.daily_quota_used,
            "percentage": (self.daily_quota_used / self.max_daily_quota) * 100
        }


# Usage example และ testing
async def test_youtube_trends():
    """ทดสอบ YouTube Trends Service"""
    api_key = "YOUR_YOUTUBE_API_KEY"  # แทนที่ด้วย API key จริง
    
    async with RealYouTubeTrendsService(api_key) as youtube_service:
        print("🔥 Testing YouTube Trends Service")
        
        # Test 1: ดึง trending videos ทั่วไป
        print("\n1. Fetching general trending videos...")
        trending_videos = await youtube_service.get_trending_videos("TH", max_results=10)
        
        if trending_videos:
            print(f"✅ Found {len(trending_videos)} trending videos")
            for i, video in enumerate(trending_videos[:3]):
                print(f"  {i+1}. {video.title} - {video.view_count:,} views")
        else:
            print("❌ No trending videos found")
        
        # Test 2: ดึง trending แยกตาม category
        print("\n2. Fetching trending by category...")
        category_trends = await youtube_service.get_trending_by_category("TH")
        
        for category, videos in category_trends.items():
            print(f"  📁 {category}: {len(videos)} videos")
        
        # Test 3: วิเคราะห์ keywords
        if trending_videos:
            print("\n3. Analyzing trending keywords...")
            keywords = await youtube_service.analyze_trending_keywords(trending_videos)
            top_keywords = list(keywords.items())[:10]
            
            print("  🔍 Top trending keywords:")
            for keyword, count in top_keywords:
                print(f"    - {keyword}: {count} occurrences")
        
        # Test 4: ตรวจสอบ quota
        quota_status = youtube_service.get_quota_status()
        print(f"\n4. Quota status: {quota_status['used']}/{quota_status['percentage']:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_youtube_trends())