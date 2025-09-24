import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import random
import time

from models.trend_data import TrendData, TrendSource, TrendCategory

logger = logging.getLogger(__name__)

class GoogleTrendsCollector:
    """Collect trending data from Google Trends"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configuration
        self.max_trends = self.config.get('max_trends', 25)
        self.regions = self.config.get('regions', ['US', 'TH'])
        self.timeframe = self.config.get('timeframe', 'now 1-d')
        self.categories = self.config.get('categories', ['all'])
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2  # seconds between requests
        
        logger.info(f"Google Trends collector initialized for regions: {self.regions}")
    
    async def collect_trends(self) -> List[TrendData]:
        """Collect trending searches from Google Trends"""
        all_trends = []
        
        for region in self.regions:
            try:
                logger.debug(f"Collecting Google Trends for region: {region}")
                
                # Apply rate limiting
                await self._rate_limit()
                
                # Collect trending searches
                region_trends = await self._collect_region_trends(region)
                
                if region_trends:
                    all_trends.extend(region_trends)
                    logger.info(f"Collected {len(region_trends)} trends from Google Trends {region}")
                
            except Exception as e:
                logger.error(f"Error collecting Google Trends for region {region}: {e}")
                continue
        
        # Process and deduplicate
        unique_trends = self._deduplicate_trends(all_trends)
        return unique_trends[:self.max_trends]
    
    async def _collect_region_trends(self, region: str) -> List[TrendData]:
        """Collect trending searches for a specific region"""
        trends = []
        
        try:
            # Get trending searches (realtime trends)
            realtime_trends = await self._get_realtime_trends(region)
            trends.extend(realtime_trends)
            
            # Get daily search trends
            await asyncio.sleep(1)  # Additional rate limiting
            daily_trends = await self._get_daily_trends(region)
            trends.extend(daily_trends)
            
        except Exception as e:
            logger.error(f"Error collecting Google Trends for region {region}: {e}")
        
        return trends
    
    async def _get_realtime_trends(self, region: str) -> List[TrendData]:
        """Get real-time trending searches"""
        trends = []
        
        try:
            # Google Trends Real-time API endpoint (unofficial)
            url = "https://trends.google.com/trends/api/realtimetrends"
            
            params = {
                'hl': 'en-US',
                'tz': '-480',
                'geo': region,
                'cat': 'all',
                'fi': '0',
                'fs': '0',
                'ri': '300',
                'rs': '20',
                'sort': '0'
            }
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://trends.google.com/'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Remove the leading characters that Google adds
                        if content.startswith(')]}\''):
                            content = content[5:]
                        
                        data = json.loads(content)
                        trends.extend(self._parse_realtime_trends(data, region))
                        
                    elif response.status == 429:
                        logger.warning("Google Trends rate limit hit")
                        await asyncio.sleep(5)
                    else:
                        logger.warning(f"Google Trends realtime API returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"Error getting realtime trends: {e}")
            # Return fallback trends if API fails
            return self._get_fallback_trends(region, 'realtime')
        
        return trends
    
    async def _get_daily_trends(self, region: str) -> List[TrendData]:
        """Get daily trending searches"""
        trends = []
        
        try:
            # Google Trends Daily API endpoint (unofficial)
            url = "https://trends.google.com/trends/api/dailytrends"
            
            params = {
                'hl': 'en-US',
                'tz': '-480',
                'geo': region,
                'ns': '15'
            }
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://trends.google.com/'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Remove the leading characters
                        if content.startswith(')]}\''):
                            content = content[5:]
                        
                        data = json.loads(content)
                        trends.extend(self._parse_daily_trends(data, region))
                        
                    elif response.status == 429:
                        logger.warning("Google Trends rate limit hit for daily trends")
                        await asyncio.sleep(5)
                    else:
                        logger.warning(f"Google Trends daily API returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"Error getting daily trends: {e}")
            # Return fallback trends if API fails
            return self._get_fallback_trends(region, 'daily')
        
        return trends
    
    def _parse_realtime_trends(self, data: Dict[str, Any], region: str) -> List[TrendData]:
        """Parse real-time trends data from Google"""
        trends = []
        
        try:
            trending_searches = data.get('storySummaries', {}).get('trendingStories', [])
            
            for story in trending_searches[:15]:  # Limit to top 15
                try:
                    # Extract story information
                    title = story.get('title', '')
                    entities = story.get('entities', [])
                    traffic = story.get('traffic', 0)
                    
                    if not title:
                        continue
                    
                    # Extract keywords from entities
                    keywords = [entity.get('title', '') for entity in entities if entity.get('title')]
                    if not keywords:
                        keywords = self._extract_keywords_from_title(title)
                    
                    # Calculate popularity score based on traffic
                    popularity_score = self._calculate_popularity_from_traffic(traffic)
                    
                    # Determine category
                    category = self._categorize_trend(title, keywords)
                    
                    # Estimate growth rate for realtime trends
                    growth_rate = self._estimate_realtime_growth_rate(traffic)
                    
                    trend_data = TrendData(
                        topic=title,
                        source=TrendSource.GOOGLE,
                        keywords=keywords[:8],  # Limit keywords
                        popularity_score=popularity_score,
                        growth_rate=growth_rate,
                        category=category,
                        region=region,
                        raw_data={
                            'traffic': traffic,
                            'entities': entities,
                            'type': 'realtime',
                            'articles': story.get('articles', []),
                            'image_url': story.get('image', {}).get('imgUrl', ''),
                            'collected_from': 'google_realtime_trends'
                        }
                    )
                    
                    trends.append(trend_data)
                    
                except Exception as e:
                    logger.debug(f"Error parsing realtime trend: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing realtime trends data: {e}")
        
        return trends
    
    def _parse_daily_trends(self, data: Dict[str, Any], region: str) -> List[TrendData]:
        """Parse daily trends data from Google"""
        trends = []
        
        try:
            default_data = data.get('default', {})
            trending_searches_days = default_data.get('trendingSearchesDays', [])
            
            # Get the most recent day
            if trending_searches_days:
                recent_day = trending_searches_days[0]
                trending_searches = recent_day.get('trendingSearches', [])
                
                for search in trending_searches[:10]:  # Limit to top 10
                    try:
                        # Extract search information
                        title = search.get('title', {}).get('query', '')
                        formattedTraffic = search.get('formattedTraffic', '')
                        related_queries = search.get('relatedQueries', [])
                        
                        if not title:
                            continue
                        
                        # Extract keywords
                        keywords = [title.lower()]
                        keywords.extend([q.get('query', '') for q in related_queries[:5]])
                        
                        # Calculate popularity score from formatted traffic
                        popularity_score = self._calculate_popularity_from_formatted_traffic(formattedTraffic)
                        
                        # Determine category
                        category = self._categorize_trend(title, keywords)
                        
                        # Growth rate for daily trends (lower than realtime)
                        growth_rate = popularity_score * 0.3  # Rough estimate
                        
                        trend_data = TrendData(
                            topic=title,
                            source=TrendSource.GOOGLE,
                            keywords=list(dict.fromkeys([k for k in keywords if k]))[:8],
                            popularity_score=popularity_score,
                            growth_rate=growth_rate,
                            category=category,
                            region=region,
                            raw_data={
                                'formatted_traffic': formattedTraffic,
                                'related_queries': related_queries,
                                'type': 'daily',
                                'articles': search.get('articles', []),
                                'image_url': search.get('image', {}).get('imgUrl', ''),
                                'collected_from': 'google_daily_trends'
                            }
                        )
                        
                        trends.append(trend_data)
                        
                    except Exception as e:
                        logger.debug(f"Error parsing daily trend: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error parsing daily trends data: {e}")
        
        return trends
    
    def _calculate_popularity_from_traffic(self, traffic: int) -> float:
        """Calculate popularity score from traffic number"""
        if traffic <= 0:
            return 10.0
        
        # Logarithmic scale for traffic
        import math
        score = min(100, math.log10(traffic + 1) * 15)
        return max(10.0, score)
    
    def _calculate_popularity_from_formatted_traffic(self, formatted_traffic: str) -> float:
        """Calculate popularity score from formatted traffic string (e.g., '100K+')"""
        if not formatted_traffic:
            return 20.0
        
        # Parse formatted traffic
        traffic_str = formatted_traffic.replace('+', '').replace(',', '').lower()
        
        try:
            if 'k' in traffic_str:
                number = float(traffic_str.replace('k', ''))
                traffic = int(number * 1000)
            elif 'm' in traffic_str:
                number = float(traffic_str.replace('m', ''))
                traffic = int(number * 1000000)
            elif 'b' in traffic_str:
                number = float(traffic_str.replace('b', ''))
                traffic = int(number * 1000000000)
            else:
                traffic = int(traffic_str)
                
            return self._calculate_popularity_from_traffic(traffic)
            
        except ValueError:
            return 30.0  # Default score if parsing fails
    
    def _categorize_trend(self, title: str, keywords: List[str]) -> TrendCategory:
        """Categorize trend based on title and keywords"""
        title_lower = title.lower()
        keywords_lower = [k.lower() for k in keywords]
        all_text = ' '.join([title_lower] + keywords_lower)
        
        # Category keywords mapping
        category_keywords = {
            TrendCategory.TECHNOLOGY: ['tech', 'software', 'app', 'ai', 'robot', 'computer', 'internet', 'phone', 'digital'],
            TrendCategory.ENTERTAINMENT: ['movie', 'film', 'actor', 'actress', 'celebrity', 'tv', 'show', 'series', 'netflix'],
            TrendCategory.MUSIC: ['song', 'album', 'singer', 'band', 'music', 'concert', 'artist', 'spotify'],
            TrendCategory.SPORTS: ['football', 'soccer', 'basketball', 'tennis', 'olympics', 'world cup', 'match', 'player'],
            TrendCategory.NEWS: ['news', 'breaking', 'election', 'politics', 'government', 'president', 'minister'],
            TrendCategory.HEALTH: ['health', 'medical', 'doctor', 'hospital', 'vaccine', 'covid', 'virus', 'disease'],
            TrendCategory.BUSINESS: ['stock', 'market', 'company', 'business', 'economy', 'finance', 'investment'],
            TrendCategory.GAMING: ['game', 'gaming', 'player', 'xbox', 'playstation', 'nintendo', 'steam', 'esports'],
            TrendCategory.EDUCATION: ['school', 'university', 'education', 'student', 'teacher', 'exam', 'course'],
            TrendCategory.LIFESTYLE: ['fashion', 'food', 'recipe', 'travel', 'lifestyle', 'home', 'beauty', 'fitness']
        }
        
        # Count matches for each category
        category_scores = {}
        for category, keywords_list in category_keywords.items():
            score = sum(1 for keyword in keywords_list if keyword in all_text)
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return TrendCategory.OTHER
    
    def _estimate_realtime_growth_rate(self, traffic: int) -> Optional[float]:
        """Estimate growth rate for realtime trends"""
        if traffic <= 0:
            return None
        
        # Higher traffic = higher estimated growth rate
        import math
        growth_rate = min(500, math.log10(traffic + 1) * 30)
        return max(10.0, growth_rate)
    
    def _extract_keywords_from_title(self, title: str) -> List[str]:
        """Extract keywords from trend title"""
        import re
        
        # Remove special characters and split
        clean_title = re.sub(r'[^\w\s]', ' ', title.lower())
        words = [word.strip() for word in clean_title.split() if len(word.strip()) > 2]
        
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words]
        
        return keywords[:6]  # Limit to 6 keywords
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent to avoid blocking"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        return random.choice(user_agents)
    
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _deduplicate_trends(self, trends: List[TrendData]) -> List[TrendData]:
        """Remove duplicate trends"""
        seen_topics = set()
        unique_trends = []
        
        for trend in trends:
            topic_lower = trend.topic.lower().strip()
            
            if topic_lower not in seen_topics:
                unique_trends.append(trend)
                seen_topics.add(topic_lower)
        
        # Sort by popularity score
        return sorted(unique_trends, key=lambda t: t.popularity_score, reverse=True)
    
    def _get_fallback_trends(self, region: str, trend_type: str) -> List[TrendData]:
        """Get fallback trends when API fails"""
        logger.info(f"Using fallback Google Trends data for {region} ({trend_type})")
        
        fallback_trends = [
            TrendData(
                topic="Sample Google Trend 1",
                source=TrendSource.GOOGLE,
                keywords=["sample", "trending", "google"],
                popularity_score=80.0,
                growth_rate=45.0,
                category=TrendCategory.TECHNOLOGY,
                region=region,
                raw_data={"fallback": True, "type": trend_type}
            ),
            TrendData(
                topic="Sample Google Trend 2",
                source=TrendSource.GOOGLE,
                keywords=["example", "search", "popular"],
                popularity_score=70.0,
                growth_rate=35.0,
                category=TrendCategory.NEWS,
                region=region,
                raw_data={"fallback": True, "type": trend_type}
            )
        ]
        
        return fallback_trends
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test with a simple request
            url = "https://trends.google.com/trends/api/dailytrends"
            params = {
                'hl': 'en-US',
                'tz': '-480',
                'geo': 'US',
                'ns': '15'
            }
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'message': 'Google Trends is accessible'
                        }
                    elif response.status == 429:
                        return {
                            'status': 'warning',
                            'message': 'Rate limited but service is accessible'
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'message': f'Google Trends returned status {response.status}'
                        }
                        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {str(e)}'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get collector status information"""
        return {
            'max_trends': self.max_trends,
            'regions': self.regions,
            'timeframe': self.timeframe,
            'categories': self.categories,
            'rate_limit_interval': self.min_request_interval,
            'last_collection': None  # Would be tracked in a real implementation
        }