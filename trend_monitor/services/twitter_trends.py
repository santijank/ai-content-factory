import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import base64
import json

from models.trend_data import TrendData, TrendSource, TrendCategory

logger = logging.getLogger(__name__)

class TwitterTrendsCollector:
    """Collect trending data from Twitter/X"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # API credentials
        self.bearer_token = self._get_bearer_token()
        self.api_key = os.environ.get('TWITTER_API_KEY')
        self.api_secret = os.environ.get('TWITTER_API_SECRET')
        
        # Configuration
        self.max_trends = self.config.get('max_trends', 30)
        self.locations = self.config.get('locations', [1, 23424977])  # Worldwide, USA
        self.base_url = "https://api.twitter.com/1.1"
        
        # Rate limiting
        self.requests_per_window = 15  # Twitter API limit
        self.window_duration = 15 * 60  # 15 minutes in seconds
        
        logger.info(f"Twitter collector initialized for locations: {self.locations}")
        if not self.bearer_token and not (self.api_key and self.api_secret):
            logger.warning("Twitter API credentials not found. Will use fallback methods.")
    
    def _get_bearer_token(self) -> Optional[str]:
        """Get Twitter Bearer Token from environment or config"""
        # Try environment variable first
        bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
        
        if not bearer_token:
            # Try config
            bearer_token = self.config.get('bearer_token')
        
        return bearer_token
    
    async def collect_trends(self) -> List[TrendData]:
        """Collect trending topics from Twitter"""
        if not self.bearer_token and not (self.api_key and self.api_secret):
            logger.info("No Twitter API credentials available, using fallback")
            return await self._collect_trends_fallback()
        
        all_trends = []
        
        for location in self.locations:
            try:
                logger.debug(f"Collecting Twitter trends for location: {location}")
                
                # Get trending topics for this location
                location_trends = await self._get_location_trends(location)
                
                if location_trends:
                    all_trends.extend(location_trends)
                    logger.info(f"Collected {len(location_trends)} trends from Twitter location {location}")
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error collecting Twitter trends for location {location}: {e}")
                continue
        
        # Remove duplicates and process
        unique_trends = self._deduplicate_trends(all_trends)
        return unique_trends[:self.max_trends]
    
    async def _get_location_trends(self, location_id: int) -> List[TrendData]:
        """Get trending topics for a specific location"""
        trends = []
        
        try:
            url = f"{self.base_url}/trends/place.json"
            params = {
                'id': location_id,
                'exclude': 'hashtags'  # Focus on topics, not hashtags
            }
            
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        trends.extend(self._parse_twitter_trends(data, location_id))
                        
                    elif response.status == 429:
                        logger.warning("Twitter API rate limit exceeded")
                        await asyncio.sleep(15 * 60)  # Wait for rate limit reset
                        
                    elif response.status == 401:
                        logger.error("Twitter API authentication failed")
                        
                    else:
                        logger.warning(f"Twitter API returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"Error getting Twitter trends for location {location_id}: {e}")
        
        return trends
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Twitter API"""
        if self.bearer_token:
            return {
                'Authorization': f'Bearer {self.bearer_token}',
                'User-Agent': 'TrendMonitorBot/1.0'
            }
        
        elif self.api_key and self.api_secret:
            # Generate Bearer token from API key and secret
            bearer_token = await self._generate_bearer_token()
            if bearer_token:
                return {
                    'Authorization': f'Bearer {bearer_token}',
                    'User-Agent': 'TrendMonitorBot/1.0'
                }
        
        return {}
    
    async def _generate_bearer_token(self) -> Optional[str]:
        """Generate Bearer token from API key and secret"""
        try:
            # Encode credentials
            credentials = f"{self.api_key}:{self.api_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            url = "https://api.twitter.com/oauth2/token"
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
            }
            data = 'grant_type=client_credentials'
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return token_data.get('access_token')
                    else:
                        logger.error(f"Failed to generate bearer token: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error generating bearer token: {e}")
            return None
    
    def _parse_twitter_trends(self, data: List[Dict[str, Any]], location_id: int) -> List[TrendData]:
        """Parse Twitter trends data"""
        trends = []
        
        try:
            if not data or not data[0].get('trends'):
                return trends
            
            location_name = self._get_location_name(location_id)
            twitter_trends = data[0]['trends']
            
            for trend_item in twitter_trends:
                try:
                    name = trend_item.get('name', '')
                    url = trend_item.get('url', '')
                    tweet_volume = trend_item.get('tweet_volume')
                    
                    if not name:
                        continue
                    
                    # Calculate popularity score
                    popularity_score = self._calculate_popularity_score(tweet_volume, name)
                    
                    # Extract keywords
                    keywords = self._extract_keywords(name)
                    
                    # Categorize trend
                    category = self._categorize_trend(name, keywords)
                    
                    # Estimate growth rate
                    growth_rate = self._estimate_growth_rate(tweet_volume)
                    
                    trend_data = TrendData(
                        topic=name,
                        source=TrendSource.TWITTER,
                        keywords=keywords,
                        popularity_score=popularity_score,
                        growth_rate=growth_rate,
                        category=category,
                        region=location_name,
                        raw_data={
                            'tweet_volume': tweet_volume,
                            'url': url,
                            'location_id': location_id,
                            'location_name': location_name,
                            'collected_from': 'twitter_trends_api'
                        }
                    )
                    
                    trends.append(trend_data)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Twitter trend: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing Twitter trends data: {e}")
        
        return trends
    
    def _calculate_popularity_score(self, tweet_volume: Optional[int], name: str) -> float:
        """Calculate popularity score based on tweet volume"""
        base_score = 30.0  # Base score for trending topics
        
        if tweet_volume and tweet_volume > 0:
            # Logarithmic scale for tweet volume
            import math
            volume_score = min(60, math.log10(tweet_volume) * 8)
            base_score += volume_score
        else:
            # If no volume data, estimate based on trend characteristics
            if name.startswith('#'):
                base_score += 20  # Hashtags tend to be more viral
            if any(word in name.lower() for word in ['breaking', 'urgent', 'live', 'now']):
                base_score += 15  # News-related trends
        
        return min(100.0, max(10.0, base_score))
    
    def _extract_keywords(self, trend_name: str) -> List[str]:
        """Extract keywords from trend name"""
        import re
        
        keywords = []
        
        # Handle hashtags
        if trend_name.startswith('#'):
            # Remove # and split camelCase or underscores
            clean_name = trend_name[1:]
            # Split on capital letters, underscores, numbers
            parts = re.findall(r'[A-Z][a-z]*|[a-z]+|\d+', clean_name)
            keywords.extend([part.lower() for part in parts if len(part) > 1])
        else:
            # Regular text processing
            clean_text = re.sub(r'[^\w\s]', ' ', trend_name.lower())
            words = [word.strip() for word in clean_text.split() if len(word.strip()) > 2]
            keywords.extend(words)
        
        # Add original trend name as primary keyword
        keywords.insert(0, trend_name.lower())
        
        # Remove duplicates while preserving order
        unique_keywords = list(dict.fromkeys(keywords))
        
        return unique_keywords[:8]  # Limit to 8 keywords
    
    def _categorize_trend(self, name: str, keywords: List[str]) -> TrendCategory:
        """Categorize Twitter trend"""
        name_lower = name.lower()
        keywords_lower = [k.lower() for k in keywords]
        all_text = ' '.join([name_lower] + keywords_lower)
        
        # Twitter-specific category patterns
        category_patterns = {
            TrendCategory.NEWS: [
                'breaking', 'news', 'alert', 'update', 'report', 'announce',
                'election', 'vote', 'politics', 'government', 'president'
            ],
            TrendCategory.ENTERTAINMENT: [
                'movie', 'film', 'tv', 'show', 'actor', 'actress', 'celebrity',
                'premiere', 'trailer', 'netflix', 'disney', 'marvel'
            ],
            TrendCategory.MUSIC: [
                'song', 'album', 'artist', 'singer', 'band', 'concert',
                'spotify', 'music', 'listen', 'single', 'release'
            ],
            TrendCategory.SPORTS: [
                'game', 'match', 'team', 'player', 'win', 'score', 'season',
                'football', 'basketball', 'soccer', 'baseball', 'olympics'
            ],
            TrendCategory.TECHNOLOGY: [
                'tech', 'app', 'software', 'update', 'launch', 'iphone',
                'android', 'ai', 'robot', 'crypto', 'bitcoin', 'nft'
            ],
            TrendCategory.GAMING: [
                'game', 'gaming', 'player', 'stream', 'twitch', 'xbox',
                'playstation', 'nintendo', 'esports', 'tournament'
            ]
        }
        
        # Count matches
        category_scores = {}
        for category, patterns in category_patterns.items():
            score = sum(1 for pattern in patterns if pattern in all_text)
            if score > 0:
                category_scores[category] = score
        
        # Special handling for hashtags
        if name.startswith('#'):
            # Hashtag patterns
            hashtag_lower = name.lower()
            if any(word in hashtag_lower for word in ['news', 'breaking', 'alert']):
                category_scores[TrendCategory.NEWS] = category_scores.get(TrendCategory.NEWS, 0) + 2
            elif any(word in hashtag_lower for word in ['music', 'song', 'artist']):
                category_scores[TrendCategory.MUSIC] = category_scores.get(TrendCategory.MUSIC, 0) + 2
            elif any(word in hashtag_lower for word in ['game', 'gaming', 'esports']):
                category_scores[TrendCategory.GAMING] = category_scores.get(TrendCategory.GAMING, 0) + 2
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return TrendCategory.OTHER
    
    def _estimate_growth_rate(self, tweet_volume: Optional[int]) -> Optional[float]:
        """Estimate growth rate based on tweet volume"""
        if not tweet_volume or tweet_volume <= 0:
            return 25.0  # Default growth rate for trending topics
        
        # Higher tweet volume suggests higher growth rate
        import math
        growth_rate = min(200, math.log10(tweet_volume) * 25)
        return max(10.0, growth_rate)
    
    def _get_location_name(self, location_id: int) -> str:
        """Get location name from location ID"""
        location_mapping = {
            1: "Worldwide",
            23424977: "United States",
            23424848: "Thailand",
            23424975: "United Kingdom",
            23424856: "Japan",
            23424829: "Germany",
            23424819: "France",
            23424833: "India",
            23424775: "Canada",
            23424748: "Australia",
            23424768: "Brazil"
        }
        
        return location_mapping.get(location_id, f"Location_{location_id}")
    
    def _deduplicate_trends(self, trends: List[TrendData]) -> List[TrendData]:
        """Remove duplicate trends"""
        seen_topics = set()
        unique_trends = []
        
        for trend in trends:
            # Normalize topic for comparison
            topic_normalized = trend.topic.lower().strip().replace('#', '')
            
            if topic_normalized not in seen_topics:
                unique_trends.append(trend)
                seen_topics.add(topic_normalized)
        
        # Sort by popularity score
        return sorted(unique_trends, key=lambda t: t.popularity_score, reverse=True)
    
    async def _collect_trends_fallback(self) -> List[TrendData]:
        """Fallback method when API is not available"""
        logger.info("Using fallback Twitter trends collection")
        
        # This would normally scrape Twitter or use alternative data sources
        # For now, return sample data
        fallback_trends = [
            TrendData(
                topic="#SampleTrend",
                source=TrendSource.TWITTER,
                keywords=["sample", "trending", "twitter"],
                popularity_score=85.0,
                growth_rate=60.0,
                category=TrendCategory.ENTERTAINMENT,
                region="Worldwide",
                raw_data={"fallback": True, "tweet_volume": None}
            ),
            TrendData(
                topic="Breaking News Sample",
                source=TrendSource.TWITTER,
                keywords=["breaking", "news", "sample"],
                popularity_score=75.0,
                growth_rate=45.0,
                category=TrendCategory.NEWS,
                region="Worldwide",
                raw_data={"fallback": True, "tweet_volume": None}
            )
        ]
        
        logger.warning("Returned fallback Twitter trends. Configure API credentials for real data.")
        return fallback_trends
    
    async def get_trending_hashtags(self, location_id: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        """Get specifically hashtag trends"""
        try:
            url = f"{self.base_url}/trends/place.json"
            params = {
                'id': location_id,
                'exclude': 'topics'  # Only get hashtags
            }
            
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        hashtags = []
                        if data and data[0].get('trends'):
                            for trend in data[0]['trends'][:limit]:
                                if trend.get('name', '').startswith('#'):
                                    hashtags.append({
                                        'hashtag': trend.get('name'),
                                        'tweet_volume': trend.get('tweet_volume'),
                                        'url': trend.get('url')
                                    })
                        
                        return hashtags
                    else:
                        logger.warning(f"Failed to get hashtags: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting trending hashtags: {e}")
            return []
    
    async def search_tweets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search recent tweets for a topic (if API v2 is available)"""
        # This would require Twitter API v2 and additional authentication
        # For now, return empty list
        logger.info(f"Tweet search not implemented for query: {query}")
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        if not self.bearer_token and not (self.api_key and self.api_secret):
            return {
                'status': 'warning',
                'message': 'No API credentials configured, using fallback methods'
            }
        
        try:
            # Test API with a simple request
            url = f"{self.base_url}/trends/available.json"
            headers = await self._get_auth_headers()
            
            if not headers:
                return {
                    'status': 'unhealthy',
                    'message': 'Failed to generate authentication headers'
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'message': 'Twitter API is accessible'
                        }
                    elif response.status == 401:
                        return {
                            'status': 'unhealthy',
                            'message': 'Twitter API authentication failed'
                        }
                    elif response.status == 429:
                        return {
                            'status': 'warning',
                            'message': 'Twitter API rate limited but accessible'
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'message': f'Twitter API returned status {response.status}'
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
            'bearer_token_configured': bool(self.bearer_token),
            'max_trends': self.max_trends,
            'locations': self.locations,
            'rate_limit': {
                'requests_per_window': self.requests_per_window,
                'window_duration_minutes': self.window_duration / 60
            },
            'last_collection': None  # Would be tracked in a real implementation
        }
    
    async def get_available_locations(self) -> List[Dict[str, Any]]:
        """Get available trend locations from Twitter API"""
        try:
            url = f"{self.base_url}/trends/available.json"
            headers = await self._get_auth_headers()
            
            if not headers:
                return []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        locations = await response.json()
                        return locations
                    else:
                        logger.warning(f"Failed to get available locations: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting available locations: {e}")
            return []
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get rate limit status (would need to track requests in real implementation)"""
        return {
            'window_duration': self.window_duration,
            'max_requests': self.requests_per_window,
            'remaining_requests': self.requests_per_window,  # Would track actual usage
            'reset_time': None  # Would track actual reset time
        }