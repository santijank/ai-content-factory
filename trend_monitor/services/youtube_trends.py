import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import re
from urllib.parse import quote

from models.trend_data import TrendData, TrendSource, TrendCategory

logger = logging.getLogger(__name__)

class YouTubeTrendsCollector:
    """Collect trending data from YouTube"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self._get_api_key()
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        # Configuration
        self.max_trends = self.config.get('max_trends', 50)
        self.regions = self.config.get('regions', ['US', 'TH'])
        self.categories = self._get_category_ids()
        
        logger.info(f"YouTube collector initialized for regions: {self.regions}")
    
    def _get_api_key(self) -> Optional[str]:
        """Get YouTube API key from environment or config"""
        # Try environment variable first
        api_key = os.environ.get('YOUTUBE_API_KEY')
        
        if not api_key:
            # Try config
            api_key = self.config.get('api_key')
        
        if not api_key:
            logger.warning("YouTube API key not found. Will use fallback methods.")
        
        return api_key
    
    def _get_category_ids(self) -> Dict[str, str]:
        """YouTube category IDs mapping"""
        return {
            'film_animation': '1',
            'autos_vehicles': '2',
            'music': '10',
            'pets_animals': '15',
            'sports': '17',
            'travel_events': '19',
            'gaming': '20',
            'people_blogs': '22',
            'comedy': '23',
            'entertainment': '24',
            'news_politics': '25',
            'howto_style': '26',
            'education': '27',
            'science_technology': '28',
            'nonprofits_activism': '29'
        }
    
    async def collect_trends(self) -> List[TrendData]:
        """Collect trending videos from YouTube"""
        if not self.api_key:
            logger.info("No API key available, using fallback trending collection")
            return await self._collect_trends_fallback()
        
        all_trends = []
        
        for region in self.regions:
            try:
                logger.debug(f"Collecting YouTube trends for region: {region}")
                
                # Collect from different categories
                region_trends = await self._collect_region_trends(region)
                
                if region_trends:
                    all_trends.extend(region_trends)
                    logger.info(f"Collected {len(region_trends)} trends from YouTube {region}")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting YouTube trends for region {region}: {e}")
                continue
        
        # Remove duplicates and process
        unique_trends = self._deduplicate_trends(all_trends)
        return unique_trends[:self.max_trends]
    
    async def _collect_region_trends(self, region: str) -> List[TrendData]:
        """Collect trending videos for a specific region"""
        trends = []
        
        try:
            # Get trending videos
            trending_videos = await self._get_trending_videos(region)
            
            for video in trending_videos:
                try:
                    trend_data = self._video_to_trend_data(video, region)
                    if trend_data:
                        trends.append(trend_data)
                except Exception as e:
                    logger.debug(f"Error processing video {video.get('id', 'unknown')}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error collecting region trends for {region}: {e}")
        
        return trends
    
    async def _get_trending_videos(self, region: str) -> List[Dict[str, Any]]:
        """Get trending videos from YouTube API"""
        url = f"{self.base_url}/videos"
        
        params = {
            'part': 'snippet,statistics,contentDetails',
            'chart': 'mostPopular',
            'regionCode': region,
            'maxResults': min(50, self.max_trends),
            'key': self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                elif response.status == 403:
                    logger.warning(f"YouTube API quota exceeded or invalid key")
                    return []
                else:
                    logger.error(f"YouTube API error: {response.status}")
                    return []
    
    def _video_to_trend_data(self, video: Dict[str, Any], region: str) -> Optional[TrendData]:
        """Convert YouTube video data to TrendData"""
        try:
            snippet = video.get('snippet', {})
            statistics = video.get('statistics', {})
            
            # Basic video info
            title = snippet.get('title', '')
            channel_title = snippet.get('channelTitle', '')
            category_id = snippet.get('categoryId', '')
            published_at = snippet.get('publishedAt', '')
            
            # Statistics
            view_count = int(statistics.get('viewCount', 0))
            like_count = int(statistics.get('likeCount', 0))
            comment_count = int(statistics.get('commentCount', 0))
            
            # Calculate popularity score (0-100)
            popularity_score = self._calculate_popularity_score(
                view_count, like_count, comment_count, published_at
            )
            
            # Generate keywords
            keywords = self._extract_keywords(title, channel_title)
            
            # Determine category
            category = self._map_youtube_category(category_id)
            
            # Calculate growth rate (simplified)
            growth_rate = self._estimate_growth_rate(view_count, published_at)
            
            return TrendData(
                topic=title,
                source=TrendSource.YOUTUBE,
                keywords=keywords,
                popularity_score=popularity_score,
                growth_rate=growth_rate,
                category=category,
                region=region,
                raw_data={
                    'video_id': video.get('id'),
                    'channel_title': channel_title,
                    'published_at': published_at,
                    'view_count': view_count,
                    'like_count': like_count,
                    'comment_count': comment_count,
                    'category_id': category_id,
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                    'duration': video.get('contentDetails', {}).get('duration'),
                    'video_url': f"https://www.youtube.com/watch?v={video.get('id')}"
                }
            )
            
        except Exception as e:
            logger.error(f"Error converting video to trend data: {e}")
            return None
    
    def _calculate_popularity_score(self, view_count: int, like_count: int, comment_count: int, published_at: str) -> float:
        """Calculate popularity score based on engagement metrics"""
        try:
            # Parse published date
            published = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            hours_since_published = (datetime.now(published.tzinfo) - published).total_seconds() / 3600
            
            # Avoid division by zero
            hours_since_published = max(1, hours_since_published)
            
            # Calculate engagement rate
            engagement_rate = (like_count + comment_count * 2) / max(view_count, 1) * 100
            
            # Views per hour
            views_per_hour = view_count / hours_since_published
            
            # Base score from views per hour (logarithmic scale)
            import math
            if views_per_hour > 0:
                base_score = min(50, math.log10(views_per_hour + 1) * 10)
            else:
                base_score = 0
            
            # Engagement bonus
            engagement_bonus = min(30, engagement_rate * 10)
            
            # Recency bonus (higher score for newer videos)
            if hours_since_published <= 24:
                recency_bonus = 20 * (1 - hours_since_published / 24)
            else:
                recency_bonus = 0
            
            total_score = base_score + engagement_bonus + recency_bonus
            
            return min(100, max(0, total_score))
            
        except Exception as e:
            logger.debug(f"Error calculating popularity score: {e}")
            # Fallback to simple view-based score
            return min(100, math.log10(view_count + 1) * 10)
    
    def _extract_keywords(self, title: str, channel_title: str) -> List[str]:
        """Extract keywords from video title and channel"""
        keywords = []
        
        # Clean and split title
        clean_title = re.sub(r'[^\w\s]', ' ', title.lower())
        title_words = [word.strip() for word in clean_title.split() if len(word.strip()) > 2]
        
        # Add significant words from title
        keywords.extend(title_words[:8])  # First 8 words
        
        # Add channel name
        clean_channel = re.sub(r'[^\w\s]', ' ', channel_title.lower())
        if clean_channel and len(clean_channel) > 2:
            keywords.append(clean_channel.strip())
        
        # Common YouTube trend keywords
        trend_indicators = ['viral', 'trending', 'challenge', 'reaction', 'review', 'tutorial', 'vs', 'new', 'latest']
        title_lower = title.lower()
        
        for indicator in trend_indicators:
            if indicator in title_lower:
                keywords.append(indicator)
        
        return list(dict.fromkeys(keywords))[:10]  # Remove duplicates, limit to 10
    
    def _map_youtube_category(self, category_id: str) -> TrendCategory:
        """Map YouTube category ID to our TrendCategory"""
        category_mapping = {
            '1': TrendCategory.ENTERTAINMENT,    # Film & Animation
            '2': TrendCategory.OTHER,           # Autos & Vehicles
            '10': TrendCategory.MUSIC,          # Music
            '15': TrendCategory.LIFESTYLE,      # Pets & Animals
            '17': TrendCategory.SPORTS,         # Sports
            '19': TrendCategory.LIFESTYLE,      # Travel & Events
            '20': TrendCategory.GAMING,         # Gaming
            '22': TrendCategory.LIFESTYLE,      # People & Blogs
            '23': TrendCategory.ENTERTAINMENT,  # Comedy
            '24': TrendCategory.ENTERTAINMENT,  # Entertainment
            '25': TrendCategory.NEWS,           # News & Politics
            '26': TrendCategory.LIFESTYLE,      # Howto & Style
            '27': TrendCategory.EDUCATION,      # Education
            '28': TrendCategory.TECHNOLOGY,     # Science & Technology
            '29': TrendCategory.OTHER           # Nonprofits & Activism
        }
        
        return category_mapping.get(category_id, TrendCategory.OTHER)
    
    def _estimate_growth_rate(self, view_count: int, published_at: str) -> Optional[float]:
        """Estimate growth rate based on views and publish time"""
        try:
            published = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            hours_since_published = (datetime.now(published.tzinfo) - published).total_seconds() / 3600
            
            if hours_since_published <= 0:
                return None
            
            # Views per hour as growth rate
            growth_rate = view_count / hours_since_published
            
            # Normalize to percentage (rough estimate)
            normalized_rate = min(1000, growth_rate / 1000 * 100)
            
            return normalized_rate
            
        except Exception:
            return None
    
    def _deduplicate_trends(self, trends: List[TrendData]) -> List[TrendData]:
        """Remove duplicate trends based on video ID or similar titles"""
        seen_ids = set()
        seen_titles = set()
        unique_trends = []
        
        for trend in trends:
            video_id = trend.raw_data.get('video_id') if trend.raw_data else None
            title_lower = trend.topic.lower()
            
            # Check for duplicate video ID
            if video_id and video_id in seen_ids:
                continue
            
            # Check for very similar titles
            is_similar = False
            for seen_title in seen_titles:
                similarity = self._calculate_title_similarity(title_lower, seen_title)
                if similarity > 0.8:  # 80% similarity threshold
                    is_similar = True
                    break
            
            if is_similar:
                continue
            
            # Add to unique collection
            unique_trends.append(trend)
            if video_id:
                seen_ids.add(video_id)
            seen_titles.add(title_lower)
        
        return unique_trends
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _collect_trends_fallback(self) -> List[TrendData]:
        """Fallback method when API key is not available"""
        logger.info("Using fallback YouTube trending collection (web scraping)")
        
        # This is a simplified fallback - in a real implementation,
        # you might scrape YouTube trending page or use unofficial APIs
        
        fallback_trends = [
            TrendData(
                topic="Sample YouTube Trend 1",
                source=TrendSource.YOUTUBE,
                keywords=["sample", "trending", "youtube"],
                popularity_score=75.0,
                category=TrendCategory.ENTERTAINMENT,
                region="global",
                raw_data={"fallback": True}
            ),
            TrendData(
                topic="Sample YouTube Trend 2",
                source=TrendSource.YOUTUBE,
                keywords=["example", "viral", "video"],
                popularity_score=65.0,
                category=TrendCategory.MUSIC,
                region="global",
                raw_data={"fallback": True}
            )
        ]
        
        logger.warning("Returned fallback trends. Configure YouTube API key for real data.")
        return fallback_trends
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        if not self.api_key:
            return {
                'status': 'warning',
                'message': 'No API key configured, using fallback methods'
            }
        
        try:
            # Test API with a simple request
            url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet',
                'chart': 'mostPopular',
                'maxResults': 1,
                'key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'message': 'YouTube API is accessible'
                        }
                    elif response.status == 403:
                        return {
                            'status': 'unhealthy',
                            'message': 'YouTube API quota exceeded or invalid key'
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'message': f'YouTube API returned status {response.status}'
                        }
                        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {str(e)}'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get collector status information"""
        return {
            'api_key_configured': bool(self.api_key),
            'max_trends': self.max_trends,
            'regions': self.regions,
            'categories_supported': len(self.categories),
            'last_collection': None  # Would be tracked in a real implementation
        }