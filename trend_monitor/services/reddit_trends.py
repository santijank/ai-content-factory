import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
import json

from models.trend_data import TrendData, TrendSource, TrendCategory

logger = logging.getLogger(__name__)

class RedditTrendsCollector:
    """Collect trending data from Reddit"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configuration
        self.max_trends = self.config.get('max_trends', 25)
        self.subreddits = self.config.get('subreddits', ['all', 'popular', 'trending'])
        self.time_periods = self.config.get('time_periods', ['hour', 'day'])
        self.sort_types = ['hot', 'top', 'rising']
        
        # Reddit API settings
        self.base_url = "https://www.reddit.com"
        self.user_agent = "TrendMonitor/1.0 (by /u/trendmonitor)"
        
        # Rate limiting
        self.requests_per_minute = 60  # Reddit's rate limit
        self.last_request_time = 0
        
        logger.info(f"Reddit collector initialized for subreddits: {self.subreddits}")
    
    async def collect_trends(self) -> List[TrendData]:
        """Collect trending posts from Reddit"""
        all_trends = []
        
        for subreddit in self.subreddits:
            try:
                logger.debug(f"Collecting Reddit trends from r/{subreddit}")
                
                # Collect from different sorting methods
                subreddit_trends = await self._collect_subreddit_trends(subreddit)
                
                if subreddit_trends:
                    all_trends.extend(subreddit_trends)
                    logger.info(f"Collected {len(subreddit_trends)} trends from r/{subreddit}")
                
                # Rate limiting
                await self._rate_limit()
                
            except Exception as e:
                logger.error(f"Error collecting Reddit trends from r/{subreddit}: {e}")
                continue
        
        # Remove duplicates and process
        unique_trends = self._deduplicate_trends(all_trends)
        return unique_trends[:self.max_trends]
    
    async def _collect_subreddit_trends(self, subreddit: str) -> List[TrendData]:
        """Collect trending posts from a specific subreddit"""
        trends = []
        
        for sort_type in self.sort_types:
            try:
                # Get posts from this subreddit with this sorting
                posts = await self._get_subreddit_posts(subreddit, sort_type)
                
                # Convert posts to trend data
                for post in posts:
                    trend_data = self._post_to_trend_data(post, subreddit)
                    if trend_data:
                        trends.append(trend_data)
                
                # Rate limiting between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.debug(f"Error collecting {sort_type} posts from r/{subreddit}: {e}")
                continue
        
        return trends
    
    async def _get_subreddit_posts(self, subreddit: str, sort_type: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Get posts from a subreddit"""
        try:
            url = f"{self.base_url}/r/{subreddit}/{sort_type}.json"
            
            params = {
                'limit': limit,
                'raw_json': 1  # Prevent HTML escaping
            }
            
            # Add time parameter for 'top' sorting
            if sort_type == 'top':
                params['t'] = 'day'  # Top posts from last day
            
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'data' in data and 'children' in data['data']:
                            return [child['data'] for child in data['data']['children']]
                        else:
                            logger.warning(f"Unexpected Reddit API response structure for r/{subreddit}")
                            return []
                            
                    elif response.status == 429:
                        logger.warning("Reddit API rate limit exceeded")
                        await asyncio.sleep(60)  # Wait a minute
                        return []
                        
                    elif response.status == 403:
                        logger.warning(f"Access forbidden to r/{subreddit}")
                        return []
                        
                    elif response.status == 404:
                        logger.warning(f"Subreddit r/{subreddit} not found")
                        return []
                        
                    else:
                        logger.warning(f"Reddit API returned status {response.status} for r/{subreddit}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting posts from r/{subreddit}: {e}")
            return []
    
    def _post_to_trend_data(self, post: Dict[str, Any], subreddit: str) -> Optional[TrendData]:
        """Convert Reddit post to TrendData"""
        try:
            # Basic post information
            title = post.get('title', '')
            author = post.get('author', '')
            created_utc = post.get('created_utc', 0)
            subreddit_name = post.get('subreddit', subreddit)
            
            # Engagement metrics
            score = post.get('score', 0)
            upvote_ratio = post.get('upvote_ratio', 0.5)
            num_comments = post.get('num_comments', 0)
            
            # Post metadata
            post_id = post.get('id', '')
            permalink = post.get('permalink', '')
            url = post.get('url', '')
            is_video = post.get('is_video', False)
            is_self = post.get('is_self', False)
            
            if not title or score < 10:  # Filter low-engagement posts
                return None
            
            # Calculate popularity score
            popularity_score = self._calculate_popularity_score(
                score, num_comments, upvote_ratio, created_utc
            )
            
            # Extract keywords
            keywords = self._extract_keywords(title, subreddit_name)
            
            # Categorize based on subreddit and content
            category = self._categorize_post(title, subreddit_name, keywords)
            
            # Calculate growth rate
            growth_rate = self._estimate_growth_rate(score, created_utc)
            
            return TrendData(
                topic=title,
                source=TrendSource.REDDIT,
                keywords=keywords,
                popularity_score=popularity_score,
                growth_rate=growth_rate,
                category=category,
                region="global",  # Reddit is global
                raw_data={
                    'post_id': post_id,
                    'subreddit': subreddit_name,
                    'author': author,
                    'score': score,
                    'upvote_ratio': upvote_ratio,
                    'num_comments': num_comments,
                    'created_utc': created_utc,
                    'permalink': f"https://reddit.com{permalink}",
                    'url': url,
                    'is_video': is_video,
                    'is_self': is_self,
                    'collected_from': f'reddit_r_{subreddit}'
                }
            )
            
        except Exception as e:
            logger.debug(f"Error converting Reddit post to trend data: {e}")
            return None
    
    def _calculate_popularity_score(self, score: int, num_comments: int, upvote_ratio: float, created_utc: float) -> float:
        """Calculate popularity score based on Reddit metrics"""
        try:
            # Time-based scoring (fresher posts get bonus)
            post_time = datetime.fromtimestamp(created_utc)
            hours_old = (datetime.utcnow() - post_time).total_seconds() / 3600
            
            # Base score from upvotes
            base_score = min(40, score / 100)  # Scale to max 40 points
            
            # Comment engagement bonus
            comment_bonus = min(20, num_comments / 10)  # Scale to max 20 points
            
            # Upvote ratio bonus
            ratio_bonus = upvote_ratio * 20  # Max 20 points for 100% upvote ratio
            
            # Freshness bonus (higher for recent posts)
            if hours_old <= 1:
                freshness_bonus = 20
            elif hours_old <= 6:
                freshness_bonus = 15
            elif hours_old <= 24:
                freshness_bonus = 10
            else:
                freshness_bonus = 5
            
            total_score = base_score + comment_bonus + ratio_bonus + freshness_bonus
            
            return min(100.0, max(10.0, total_score))
            
        except Exception:
            # Fallback to simple score-based calculation
            return min(100.0, max(10.0, score / 50))
    
    def _extract_keywords(self, title: str, subreddit: str) -> List[str]:
        """Extract keywords from post title and subreddit"""
        keywords = []
        
        # Add subreddit as primary keyword
        if subreddit and subreddit not in ['all', 'popular']:
            keywords.append(subreddit.lower())
        
        # Clean and extract from title
        clean_title = re.sub(r'[^\w\s]', ' ', title.lower())
        words = [word.strip() for word in clean_title.split() if len(word.strip()) > 2]
        
        # Remove common Reddit words
        reddit_stopwords = {
            'reddit', 'post', 'title', 'question', 'help', 'please', 'thanks',
            'edit', 'update', 'meta', 'discussion', 'opinion'
        }
        
        filtered_words = [word for word in words if word not in reddit_stopwords]
        keywords.extend(filtered_words[:6])  # Limit title keywords
        
        # Look for trending indicators
        trending_indicators = ['viral', 'trending', 'hot', 'breaking', 'new', 'latest']
        title_lower = title.lower()
        
        for indicator in trending_indicators:
            if indicator in title_lower and indicator not in keywords:
                keywords.append(indicator)
        
        return list(dict.fromkeys(keywords))[:8]  # Remove duplicates, limit to 8
    
    def _categorize_post(self, title: str, subreddit: str, keywords: List[str]) -> TrendCategory:
        """Categorize Reddit post based on subreddit and content"""
        subreddit_lower = subreddit.lower()
        title_lower = title.lower()
        keywords_lower = [k.lower() for k in keywords]
        all_text = ' '.join([title_lower, subreddit_lower] + keywords_lower)
        
        # Subreddit-based categorization (most reliable)
        subreddit_categories = {
            TrendCategory.TECHNOLOGY: [
                'technology', 'programming', 'coding', 'tech', 'gadgets', 'apple', 
                'android', 'microsoft', 'google', 'ai', 'machinelearning'
            ],
            TrendCategory.GAMING: [
                'gaming', 'games', 'steam', 'xbox', 'playstation', 'nintendo',
                'mobilegaming', 'esports', 'gamedev'
            ],
            TrendCategory.ENTERTAINMENT: [
                'movies', 'television', 'tv', 'entertainment', 'celebrity',
                'netflix', 'marvel', 'starwars', 'anime'
            ],
            TrendCategory.MUSIC: [
                'music', 'hiphop', 'rock', 'pop', 'edm', 'spotify', 'musicians'
            ],
            TrendCategory.NEWS: [
                'news', 'worldnews', 'politics', 'breakingnews', 'currentevents'
            ],
            TrendCategory.SPORTS: [
                'sports', 'football', 'basketball', 'soccer', 'baseball',
                'nfl', 'nba', 'olympics'
            ],
            TrendCategory.EDUCATION: [
                'education', 'university', 'college', 'students', 'teachers',
                'todayilearned', 'explainlikeimfive'
            ],
            TrendCategory.LIFESTYLE: [
                'lifestyle', 'food', 'cooking', 'fitness', 'fashion', 'travel',
                'relationships', 'lifeprotips'
            ],
            TrendCategory.BUSINESS: [
                'business', 'entrepreneur', 'investing', 'stocks', 'finance',
                'cryptocurrency', 'economics'
            ],
            TrendCategory.HEALTH: [
                'health', 'medical', 'fitness', 'mentalhealth', 'psychology'
            ]
        }
        
        # Check subreddit matches first
        for category, subreddits in subreddit_categories.items():
            if any(sub in subreddit_lower for sub in subreddits):
                return category
        
        # Content-based categorization
        content_keywords = {
            TrendCategory.TECHNOLOGY: ['tech', 'software', 'app', 'computer', 'internet', 'digital'],
            TrendCategory.GAMING: ['game', 'player', 'gaming', 'play', 'level', 'character'],
            TrendCategory.ENTERTAINMENT: ['movie', 'show', 'actor', 'series', 'film', 'watch'],
            TrendCategory.MUSIC: ['song', 'music', 'artist', 'album', 'listen', 'band'],
            TrendCategory.NEWS: ['news', 'breaking', 'report', 'happened', 'today', 'update'],
            TrendCategory.SPORTS: ['team', 'game', 'player', 'win', 'match', 'season'],
            TrendCategory.EDUCATION: ['learn', 'study', 'school', 'question', 'explain', 'how'],
            TrendCategory.LIFESTYLE: ['life', 'people', 'daily', 'personal', 'experience', 'story']
        }
        
        # Count content keyword matches
        category_scores = {}
        for category, content_words in content_keywords.items():
            score = sum(1 for word in content_words if word in all_text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return TrendCategory.OTHER
    
    def _estimate_growth_rate(self, score: int, created_utc: float) -> Optional[float]:
        """Estimate growth rate based on score and post age"""
        try:
            post_time = datetime.fromtimestamp(created_utc)
            hours_old = (datetime.utcnow() - post_time).total_seconds() / 3600
            
            if hours_old <= 0:
                return None
            
            # Calculate score per hour as growth indicator
            score_per_hour = score / hours_old
            
            # Convert to percentage-like scale
            growth_rate = min(300, score_per_hour * 2)  # Scale and cap at 300
            
            return max(5.0, growth_rate)
            
        except Exception:
            return 20.0  # Default growth rate
    
    async def _rate_limit(self):
        """Apply rate limiting to respect Reddit's limits"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        min_interval = 60 / self.requests_per_minute  # Minimum seconds between requests
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    def _deduplicate_trends(self, trends: List[TrendData]) -> List[TrendData]:
        """Remove duplicate trends based on title similarity"""
        seen_titles = set()
        unique_trends = []
        
        for trend in trends:
            # Normalize title for comparison
            normalized_title = trend.topic.lower().strip()
            
            # Check for exact matches first
            if normalized_title in seen_titles:
                continue
            
            # Check for similar titles (>80% similarity)
            is_similar = False
            for seen_title in seen_titles:
                similarity = self._calculate_title_similarity(normalized_title, seen_title)
                if similarity > 0.8:
                    is_similar = True
                    break
            
            if not is_similar:
                unique_trends.append(trend)
                seen_titles.add(normalized_title)
        
        # Sort by popularity score
        return sorted(unique_trends, key=lambda t: t.popularity_score, reverse=True)
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles using Jaccard similarity"""
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def get_subreddit_info(self, subreddit: str) -> Dict[str, Any]:
        """Get information about a specific subreddit"""
        try:
            url = f"{self.base_url}/r/{subreddit}/about.json"
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'data' in data:
                            subreddit_data = data['data']
                            return {
                                'name': subreddit_data.get('display_name', subreddit),
                                'subscribers': subreddit_data.get('subscribers', 0),
                                'description': subreddit_data.get('public_description', ''),
                                'created_utc': subreddit_data.get('created_utc', 0),
                                'over18': subreddit_data.get('over18', False),
                                'active_users': subreddit_data.get('active_user_count', 0)
                            }
                    
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting subreddit info for r/{subreddit}: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test with a simple request to r/popular
            url = f"{self.base_url}/r/popular/hot.json"
            params = {'limit': 1}
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'message': 'Reddit API is accessible'
                        }
                    elif response.status == 429:
                        return {
                            'status': 'warning',
                            'message': 'Reddit API rate limited but accessible'
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'message': f'Reddit API returned status {response.status}'
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
            'subreddits': self.subreddits,
            'time_periods': self.time_periods,
            'sort_types': self.sort_types,
            'rate_limit': {
                'requests_per_minute': self.requests_per_minute
            },
            'last_collection': None  # Would be tracked in a real implementation
        }