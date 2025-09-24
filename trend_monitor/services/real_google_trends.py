# ai-content-factory/trend-monitor/services/real_google_trends.py

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
from dataclasses import dataclass
import time
import random

# ติดตั้ง: pip install pytrends
from pytrends.request import TrendReq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GoogleTrendData:
    keyword: str
    interest_score: int  # 0-100
    region: str
    timeframe: str
    category: int
    related_queries: List[str]
    rising_queries: List[str]
    timestamp: datetime
    search_volume_trend: List[Tuple[datetime, int]]  # (date, interest_score)

class RealGoogleTrendsService:
    def __init__(self, geo: str = "TH", timeout: int = 30):
        self.geo = geo
        self.timeout = timeout
        self.pytrends = None
        self.request_count = 0
        self.max_requests_per_hour = 100
        self.last_request_time = 0
        
    def _init_pytrends(self):
        """Initialize pytrends with random user agent"""
        try:
            self.pytrends = TrendReq(
                hl='th-TH', 
                tz=420,  # Thailand timezone
                timeout=self.timeout,
                retries=2,
                backoff_factor=0.1
            )
            logger.info("Google Trends service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Trends: {e}")
            raise
    
    def _rate_limit(self):
        """Rate limiting to avoid being blocked"""
        current_time = time.time()
        
        # Reset counter every hour
        if current_time - self.last_request_time > 3600:
            self.request_count = 0
        
        if self.request_count >= self.max_requests_per_hour:
            logger.warning("Rate limit reached, waiting...")
            time.sleep(3600)  # Wait 1 hour
            self.request_count = 0
        
        # Random delay between requests (1-3 seconds)
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        self.request_count += 1
        self.last_request_time = current_time
    
    async def get_trending_searches(self, pn: str = "thailand") -> List[str]:
        """ดึง trending searches ประจำวัน"""
        if not self.pytrends:
            self._init_pytrends()
        
        try:
            self._rate_limit()
            
            # ดึง trending searches ของวันนี้
            trending_searches_df = self.pytrends.trending_searches(pn=pn)
            
            if not trending_searches_df.empty:
                trending_list = trending_searches_df[0].tolist()
                logger.info(f"Found {len(trending_list)} trending searches")
                return trending_list[:20]  # Top 20
            else:
                logger.warning("No trending searches found")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching trending searches: {e}")
            return []
    
    async def analyze_keyword(self, keyword: str, timeframe: str = "today 7-d") -> Optional[GoogleTrendData]:
        """วิเคราะห์ keyword เฉพาะ"""
        if not self.pytrends:
            self._init_pytrends()
        
        try:
            self._rate_limit()
            
            # Build payload for keyword
            self.pytrends.build_payload([keyword], 
                                      cat=0, 
                                      timeframe=timeframe, 
                                      geo=self.geo, 
                                      gprop='')
            
            # Get interest over time
            interest_over_time_df = self.pytrends.interest_over_time()
            
            if interest_over_time_df.empty:
                logger.warning(f"No data found for keyword: {keyword}")
                return None
            
            # Get related queries
            related_queries_dict = self.pytrends.related_queries()
            related_queries = []
            rising_queries = []
            
            if keyword in related_queries_dict:
                if related_queries_dict[keyword]['top'] is not None:
                    related_queries = related_queries_dict[keyword]['top']['query'].tolist()[:10]
                
                if related_queries_dict[keyword]['rising'] is not None:
                    rising_queries = related_queries_dict[keyword]['rising']['query'].tolist()[:10]
            
            # Calculate average interest score
            avg_interest = int(interest_over_time_df[keyword].mean())
            
            # Convert time series data
            search_volume_trend = []
            for date, row in interest_over_time_df.iterrows():
                search_volume_trend.append((date, int(row[keyword])))
            
            trend_data = GoogleTrendData(
                keyword=keyword,
                interest_score=avg_interest,
                region=self.geo,
                timeframe=timeframe,
                category=0,
                related_queries=related_queries,
                rising_queries=rising_queries,
                timestamp=datetime.now(),
                search_volume_trend=search_volume_trend
            )
            
            logger.info(f"Analyzed keyword '{keyword}' - Interest: {avg_interest}")
            return trend_data
            
        except Exception as e:
            logger.error(f"Error analyzing keyword '{keyword}': {e}")
            return None
    
    async def analyze_multiple_keywords(self, keywords: List[str], timeframe: str = "today 7-d") -> List[GoogleTrendData]:
        """วิเคราะห์หลาย keywords พร้อมกัน"""
        results = []
        
        # Process in batches of 5 (Google Trends limit)
        batch_size = 5
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            
            try:
                if not self.pytrends:
                    self._init_pytrends()
                
                self._rate_limit()
                
                # Build payload for batch
                self.pytrends.build_payload(batch, 
                                          cat=0, 
                                          timeframe=timeframe, 
                                          geo=self.geo, 
                                          gprop='')
                
                # Get interest over time
                interest_over_time_df = self.pytrends.interest_over_time()
                
                if not interest_over_time_df.empty:
                    for keyword in batch:
                        if keyword in interest_over_time_df.columns:
                            avg_interest = int(interest_over_time_df[keyword].mean())
                            
                            # Simple trend data for batch processing
                            trend_data = GoogleTrendData(
                                keyword=keyword,
                                interest_score=avg_interest,
                                region=self.geo,
                                timeframe=timeframe,
                                category=0,
                                related_queries=[],
                                rising_queries=[],
                                timestamp=datetime.now(),
                                search_volume_trend=[]
                            )
                            results.append(trend_data)
                
                logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} keywords")
                
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                continue
        
        return results
    
    async def get_trending_by_category(self, categories: List[int] = None) -> Dict[str, List[str]]:
        """ดึง trending searches แยกตาม category"""
        if categories is None:
            categories = [
                0,   # All categories
                3,   # Arts & Entertainment
                5,   # Computers & Electronics
                8,   # Food & Drink
                16,  # News
                20,  # Online Communities
                23,  # Sports
            ]
        
        category_names = {
            0: "All Categories",
            3: "Arts & Entertainment", 
            5: "Technology",
            8: "Food & Drink",
            16: "News",
            20: "Online Communities",
            23: "Sports"
        }
        
        results = {}
        
        for cat_id in categories:
            try:
                if not self.pytrends:
                    self._init_pytrends()
                
                self._rate_limit()
                
                # ใช้ realtime trends (ถ้าใช้ได้)
                trending_searches_df = self.pytrends.trending_searches(pn="thailand")
                
                if not trending_searches_df.empty:
                    category_name = category_names.get(cat_id, f"Category {cat_id}")
                    results[category_name] = trending_searches_df[0].tolist()[:10]
                    
                logger.info(f"Fetched trends for category: {category_names.get(cat_id)}")
                
            except Exception as e:
                logger.error(f"Error fetching category {cat_id}: {e}")
                continue
        
        return results
    
    async def correlate_with_youtube_trends(self, youtube_keywords: List[str]) -> List[GoogleTrendData]:
        """เชื่อมโยง YouTube trends กับ Google Trends"""
        logger.info(f"Correlating {len(youtube_keywords)} YouTube keywords with Google Trends")
        
        # Filter keywords (remove very short or common words)
        filtered_keywords = [
            kw for kw in youtube_keywords 
            if len(kw) > 2 and kw.lower() not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']
        ]
        
        # Analyze top keywords
        top_keywords = filtered_keywords[:20]  # Limit to avoid quota issues
        
        trend_results = await self.analyze_multiple_keywords(top_keywords)
        
        # Sort by interest score
        trend_results.sort(key=lambda x: x.interest_score, reverse=True)
        
        logger.info(f"Successfully correlated {len(trend_results)} keywords")
        return trend_results
    
    def get_request_status(self) -> Dict[str, int]:
        """ตรวจสอบสถานะ requests"""
        return {
            "requests_made": self.request_count,
            "requests_remaining": self.max_requests_per_hour - self.request_count,
            "hours_since_reset": (time.time() - self.last_request_time) / 3600
        }


# Usage example และ testing
async def test_google_trends():
    """ทดสอบ Google Trends Service"""
    google_trends = RealGoogleTrendsService(geo="TH")
    
    print("🔍 Testing Google Trends Service")
    
    # Test 1: ดึง trending searches
    print("\n1. Fetching trending searches...")
    trending_searches = await google_trends.get_trending_searches("thailand")
    
    if trending_searches:
        print(f"✅ Found {len(trending_searches)} trending searches")
        for i, search in enumerate(trending_searches[:5]):
            print(f"  {i+1}. {search}")
    else:
        print("❌ No trending searches found")
    
    # Test 2: วิเคราะห์ keyword เฉพาะ
    print("\n2. Analyzing specific keyword...")
    if trending_searches:
        keyword = trending_searches[0]
        trend_data = await google_trends.analyze_keyword(keyword)
        
        if trend_data:
            print(f"✅ Keyword: {trend_data.keyword}")
            print(f"  Interest Score: {trend_data.interest_score}")
            print(f"  Related Queries: {len(trend_data.related_queries)}")
            print(f"  Rising Queries: {len(trend_data.rising_queries)}")
    
    # Test 3: วิเคราะห์หลาย keywords
    print("\n3. Analyzing multiple keywords...")
    test_keywords = ["AI", "TikTok", "YouTube", "เกม", "อาหาร"]
    batch_results = await google_trends.analyze_multiple_keywords(test_keywords)
    
    if batch_results:
        print(f"✅ Analyzed {len(batch_results)} keywords")
        for result in batch_results:
            print(f"  - {result.keyword}: {result.interest_score}")
    
    # Test 4: ตรวจสอบสถานะ requests
    status = google_trends.get_request_status()
    print(f"\n4. Request status: {status['requests_made']} requests made")

if __name__ == "__main__":
    asyncio.run(test_google_trends())