from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import uuid
import json

class TrendSource(Enum):
    YOUTUBE = "youtube"
    GOOGLE = "google"
    TWITTER = "twitter"
    REDDIT = "reddit"
    TIKTOK = "tiktok"

class TrendCategory(Enum):
    ENTERTAINMENT = "entertainment"
    TECHNOLOGY = "technology"
    NEWS = "news"
    SPORTS = "sports"
    MUSIC = "music"
    GAMING = "gaming"
    EDUCATION = "education"
    LIFESTYLE = "lifestyle"
    BUSINESS = "business"
    HEALTH = "health"
    OTHER = "other"

@dataclass
class TrendData:
    """Main trend data model"""
    topic: str
    source: TrendSource
    keywords: List[str]
    popularity_score: float
    growth_rate: Optional[float] = None
    category: Optional[TrendCategory] = TrendCategory.OTHER
    region: Optional[str] = "global"
    collected_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    
    def __post_init__(self):
        """Initialize after creation"""
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        if self.collected_at is None:
            self.collected_at = datetime.utcnow()
            
        # Ensure source is enum
        if isinstance(self.source, str):
            self.source = TrendSource(self.source.lower())
            
        # Ensure category is enum
        if isinstance(self.category, str):
            try:
                self.category = TrendCategory(self.category.lower())
            except ValueError:
                self.category = TrendCategory.OTHER
                
        # Clean and validate keywords
        if self.keywords:
            self.keywords = [kw.strip().lower() for kw in self.keywords if kw.strip()]
        else:
            self.keywords = [self.topic.lower()]
            
        # Ensure popularity score is within reasonable range
        self.popularity_score = max(0.0, min(100.0, float(self.popularity_score)))
        
        # Ensure growth rate is reasonable if provided
        if self.growth_rate is not None:
            self.growth_rate = max(-100.0, min(1000.0, float(self.growth_rate)))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        
        # Convert enums to strings
        data['source'] = self.source.value
        data['category'] = self.category.value
        
        # Convert datetime to ISO string
        if self.collected_at:
            data['collected_at'] = self.collected_at.isoformat()
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendData':
        """Create TrendData from dictionary"""
        # Handle datetime
        if 'collected_at' in data and isinstance(data['collected_at'], str):
            data['collected_at'] = datetime.fromisoformat(data['collected_at'].replace('Z', '+00:00'))
        
        # Handle enums
        if 'source' in data and isinstance(data['source'], str):
            data['source'] = TrendSource(data['source'])
            
        if 'category' in data and isinstance(data['category'], str):
            try:
                data['category'] = TrendCategory(data['category'])
            except ValueError:
                data['category'] = TrendCategory.OTHER
        
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TrendData':
        """Create TrendData from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_content_potential_score(self) -> float:
        """Calculate content creation potential score"""
        base_score = self.popularity_score
        
        # Boost score based on growth rate
        if self.growth_rate and self.growth_rate > 0:
            growth_bonus = min(20, self.growth_rate * 2)  # Max 20 bonus points
            base_score += growth_bonus
        
        # Category-based adjustments
        category_multipliers = {
            TrendCategory.ENTERTAINMENT: 1.2,
            TrendCategory.TECHNOLOGY: 1.1,
            TrendCategory.GAMING: 1.3,
            TrendCategory.MUSIC: 1.2,
            TrendCategory.LIFESTYLE: 1.1,
            TrendCategory.EDUCATION: 1.0,
            TrendCategory.NEWS: 0.9,  # News can be competitive
            TrendCategory.BUSINESS: 0.8,  # Less viral potential
            TrendCategory.HEALTH: 0.9,
            TrendCategory.SPORTS: 1.1,
            TrendCategory.OTHER: 1.0
        }
        
        multiplier = category_multipliers.get(self.category, 1.0)
        final_score = base_score * multiplier
        
        # Ensure score is within 0-100 range
        return max(0.0, min(100.0, final_score))
    
    def get_hashtags(self) -> List[str]:
        """Generate potential hashtags from keywords"""
        hashtags = []
        
        # Add main topic as hashtag
        clean_topic = ''.join(c for c in self.topic if c.isalnum() or c.isspace()).strip()
        if clean_topic:
            hashtags.append('#' + clean_topic.replace(' ', ''))
        
        # Add keywords as hashtags
        for keyword in self.keywords[:5]:  # Limit to 5 keywords
            clean_keyword = ''.join(c for c in keyword if c.isalnum() or c.isspace()).strip()
            if clean_keyword and len(clean_keyword) > 2:
                hashtag = '#' + clean_keyword.replace(' ', '')
                if hashtag not in hashtags:
                    hashtags.append(hashtag)
        
        # Add category hashtag
        hashtags.append('#' + self.category.value)
        
        # Add source-specific hashtags
        source_hashtags = {
            TrendSource.YOUTUBE: ['#YouTubeTrends', '#Trending'],
            TrendSource.GOOGLE: ['#GoogleTrends', '#SearchTrends'],
            TrendSource.TWITTER: ['#TwitterTrends', '#Viral'],
            TrendSource.REDDIT: ['#Reddit', '#RedditTrends'],
            TrendSource.TIKTOK: ['#TikTokTrends', '#ForYou']
        }
        
        hashtags.extend(source_hashtags.get(self.source, []))
        
        # Remove duplicates and return
        return list(dict.fromkeys(hashtags))[:10]  # Max 10 hashtags
    
    def is_fresh(self, max_age_hours: int = 24) -> bool:
        """Check if trend is still fresh"""
        if not self.collected_at:
            return False
            
        age = datetime.utcnow() - self.collected_at
        return age.total_seconds() < (max_age_hours * 3600)
    
    def __str__(self) -> str:
        return f"TrendData(topic='{self.topic}', source={self.source.value}, score={self.popularity_score:.1f})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class TrendBatch:
    """Batch of trends collected together"""
    trends: List[TrendData]
    source: TrendSource
    collected_at: datetime
    batch_id: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.batch_id:
            self.batch_id = str(uuid.uuid4())
            
        if not self.collected_at:
            self.collected_at = datetime.utcnow()
    
    def get_top_trends(self, limit: int = 10) -> List[TrendData]:
        """Get top trends by popularity score"""
        return sorted(self.trends, key=lambda t: t.popularity_score, reverse=True)[:limit]
    
    def get_trends_by_category(self, category: TrendCategory) -> List[TrendData]:
        """Get trends filtered by category"""
        return [trend for trend in self.trends if trend.category == category]
    
    def get_average_score(self) -> float:
        """Get average popularity score of all trends"""
        if not self.trends:
            return 0.0
        return sum(trend.popularity_score for trend in self.trends) / len(self.trends)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert batch to dictionary"""
        return {
            'batch_id': self.batch_id,
            'source': self.source.value,
            'collected_at': self.collected_at.isoformat(),
            'trend_count': len(self.trends),
            'average_score': self.get_average_score(),
            'trends': [trend.to_dict() for trend in self.trends],
            'metadata': self.metadata
        }

# Helper functions for trend data processing
def merge_similar_trends(trends: List[TrendData], similarity_threshold: float = 0.8) -> List[TrendData]:
    """Merge trends with similar topics"""
    merged_trends = []
    processed_indices = set()
    
    for i, trend1 in enumerate(trends):
        if i in processed_indices:
            continue
            
        similar_trends = [trend1]
        processed_indices.add(i)
        
        for j, trend2 in enumerate(trends[i+1:], start=i+1):
            if j in processed_indices:
                continue
                
            # Simple similarity check based on keywords overlap
            keywords1 = set(trend1.keywords)
            keywords2 = set(trend2.keywords)
            
            if keywords1 and keywords2:
                intersection = len(keywords1.intersection(keywords2))
                union = len(keywords1.union(keywords2))
                similarity = intersection / union if union > 0 else 0
                
                if similarity >= similarity_threshold:
                    similar_trends.append(trend2)
                    processed_indices.add(j)
        
        # Merge similar trends
        if len(similar_trends) > 1:
            merged_trend = merge_trend_group(similar_trends)
            merged_trends.append(merged_trend)
        else:
            merged_trends.append(trend1)
    
    return merged_trends

def merge_trend_group(trends: List[TrendData]) -> TrendData:
    """Merge a group of similar trends into one"""
    if not trends:
        raise ValueError("Cannot merge empty trend group")
    
    if len(trends) == 1:
        return trends[0]
    
    # Use the trend with highest popularity as base
    base_trend = max(trends, key=lambda t: t.popularity_score)
    
    # Combine keywords from all trends
    all_keywords = []
    for trend in trends:
        all_keywords.extend(trend.keywords)
    
    # Remove duplicates while preserving order
    unique_keywords = list(dict.fromkeys(all_keywords))
    
    # Calculate weighted average popularity score
    total_weight = sum(t.popularity_score for t in trends)
    avg_popularity = total_weight / len(trends)
    
    # Merge raw data
    merged_raw_data = {
        'merged_from': [t.id for t in trends],
        'source_count': len(trends),
        'original_data': [t.raw_data for t in trends if t.raw_data]
    }
    
    return TrendData(
        topic=base_trend.topic,
        source=base_trend.source,
        keywords=unique_keywords[:10],  # Limit keywords
        popularity_score=avg_popularity,
        growth_rate=max((t.growth_rate for t in trends if t.growth_rate), default=None),
        category=base_trend.category,
        region=base_trend.region,
        collected_at=min(t.collected_at for t in trends if t.collected_at),
        raw_data=merged_raw_data
    )