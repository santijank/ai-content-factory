# Trend Monitor Services
# Export all service classes for easy importing

from .trend_collector import TrendCollector
from .youtube_trends import YouTubeTrendsCollector  
from .google_trends import GoogleTrendsCollector
from .twitter_trends import TwitterTrendsCollector
from .reddit_trends import RedditTrendsCollector

__all__ = [
    'TrendCollector',
    'YouTubeTrendsCollector',
    'GoogleTrendsCollector', 
    'TwitterTrendsCollector',
    'RedditTrendsCollector'
]