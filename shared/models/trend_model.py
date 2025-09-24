"""
AI Content Factory - Trend Models
================================

Shared models for trend data and analysis across all services.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator

from .base_model import BaseDataClass, BasePydanticModel, StatusEnum, validate_positive_number, validate_non_empty_string


class TrendSourceEnum(str, Enum):
    """Trend data sources."""
    YOUTUBE = "youtube"
    GOOGLE_TRENDS = "google_trends" 
    TWITTER = "twitter"
    REDDIT = "reddit"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    NEWS_API = "news_api"
    CUSTOM = "custom"


class TrendCategoryEnum(str, Enum):
    """Trend categories."""
    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    NEWS = "news"
    GAMING = "gaming"
    LIFESTYLE = "lifestyle"
    EDUCATION = "education"
    BUSINESS = "business"
    HEALTH = "health"
    TRAVEL = "travel"
    FOOD = "food"
    FASHION = "fashion"
    MUSIC = "music"
    MOVIES = "movies"
    POLITICS = "politics"
    SCIENCE = "science"
    OTHER = "other"


class TrendRegionEnum(str, Enum):
    """Geographic regions for trends."""
    GLOBAL = "global"
    THAILAND = "TH"
    UNITED_STATES = "US"
    UNITED_KINGDOM = "GB"
    JAPAN = "JP"
    SOUTH_KOREA = "KR"
    SINGAPORE = "SG"
    MALAYSIA = "MY"
    INDONESIA = "ID"
    PHILIPPINES = "PH"
    VIETNAM = "VN"
    INDIA = "IN"
    AUSTRALIA = "AU"


@dataclass
class TrendKeyword(BaseDataClass):
    """Individual trend keyword data."""
    
    keyword: str
    score: float
    volume: Optional[int] = None
    competition: Optional[str] = None  # low, medium, high
    related_keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.keyword = validate_non_empty_string(self.keyword)
        self.score = validate_positive_number(self.score)


@dataclass
class TrendMetrics(BaseDataClass):
    """Trend performance metrics."""
    
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    mentions: int = 0
    search_volume: int = 0
    engagement_rate: float = 0.0
    growth_rate: float = 0.0
    virality_score: float = 0.0
    
    def calculate_engagement_rate(self) -> float:
        """Calculate engagement rate based on metrics."""
        if self.views == 0:
            return 0.0
        
        total_engagement = self.likes + self.comments + self.shares
        self.engagement_rate = (total_engagement / self.views) * 100
        return self.engagement_rate
    
    def calculate_virality_score(self) -> float:
        """Calculate virality score based on multiple factors."""
        # Weighted scoring algorithm
        weights = {
            'shares': 0.4,
            'comments': 0.3,
            'likes': 0.2,
            'growth_rate': 0.1
        }
        
        normalized_shares = min(self.shares / 1000, 1.0)  # Normalize to 0-1
        normalized_comments = min(self.comments / 500, 1.0)
        normalized_likes = min(self.likes / 5000, 1.0)
        normalized_growth = min(abs(self.growth_rate) / 100, 1.0)
        
        self.virality_score = (
            normalized_shares * weights['shares'] +
            normalized_comments * weights['comments'] +
            normalized_likes * weights['likes'] +
            normalized_growth * weights['growth_rate']
        ) * 10  # Scale to 0-10
        
        return self.virality_score


@dataclass
class TrendData(BaseDataClass):
    """Core trend data model."""
    
    topic: str
    source: TrendSourceEnum
    popularity_score: float
    keywords: List[TrendKeyword] = field(default_factory=list)
    category: TrendCategoryEnum = TrendCategoryEnum.OTHER
    region: TrendRegionEnum = TrendRegionEnum.GLOBAL
    metrics: Optional[TrendMetrics] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        self.topic = validate_non_empty_string(self.topic)
        self.popularity_score = validate_positive_number(self.popularity_score)
        
        if self.metrics is None:
            self.metrics = TrendMetrics()
    
    def add_keyword(self, keyword: str, score: float, **kwargs):
        """Add a keyword to the trend."""
        trend_keyword = TrendKeyword(
            keyword=keyword,
            score=score,
            **kwargs
        )
        self.keywords.append(trend_keyword)
    
    def get_top_keywords(self, limit: int = 5) -> List[TrendKeyword]:
        """Get top keywords by score."""
        return sorted(self.keywords, key=lambda k: k.score, reverse=True)[:limit]
    
    def is_expired(self) -> bool:
        """Check if trend data has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def calculate_overall_score(self) -> float:
        """Calculate overall trend score combining multiple factors."""
        base_score = self.popularity_score
        
        if self.metrics:
            # Factor in metrics
            virality_bonus = self.metrics.virality_score * 0.1
            engagement_bonus = self.metrics.engagement_rate * 0.05
            growth_bonus = max(self.metrics.growth_rate, 0) * 0.02
            
            total_score = base_score + virality_bonus + engagement_bonus + growth_bonus
        else:
            total_score = base_score
        
        return min(total_score, 10.0)  # Cap at 10


class TrendAnalysisRequest(BasePydanticModel):
    """Request model for trend analysis."""
    
    sources: List[TrendSourceEnum] = Field(default_factory=lambda: [TrendSourceEnum.YOUTUBE])
    categories: List[TrendCategoryEnum] = Field(default_factory=list)
    regions: List[TrendRegionEnum] = Field(default=[TrendRegionEnum.GLOBAL])
    time_range: int = Field(default=24, description="Hours to look back")
    min_popularity_score: float = Field(default=5.0, ge=0.0, le=10.0)
    max_results: int = Field(default=50, ge=1, le=1000)
    include_keywords: bool = Field(default=True)
    include_metrics: bool = Field(default=True)


@dataclass
class TrendAnalysisResult(BaseDataClass):
    """Result of trend analysis."""
    
    trends: List[TrendData] = field(default_factory=list)
    total_trends_found: int = 0
    analysis_duration: float = 0.0
    sources_analyzed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_top_trends(self, limit: int = 10) -> List[TrendData]:
        """Get top trends by overall score."""
        scored_trends = [(trend, trend.calculate_overall_score()) for trend in self.trends]
        sorted_trends = sorted(scored_trends, key=lambda x: x[1], reverse=True)
        return [trend for trend, _ in sorted_trends[:limit]]
    
    def get_trends_by_category(self, category: TrendCategoryEnum) -> List[TrendData]:
        """Get trends filtered by category."""
        return [trend for trend in self.trends if trend.category == category]
    
    def get_trends_by_source(self, source: TrendSourceEnum) -> List[TrendData]:
        """Get trends filtered by source."""
        return [trend for trend in self.trends if trend.source == source]
    
    def get_trend_statistics(self) -> Dict[str, Any]:
        """Get statistical summary of trends."""
        if not self.trends:
            return {}
        
        scores = [trend.calculate_overall_score() for trend in self.trends]
        popularity_scores = [trend.popularity_score for trend in self.trends]
        
        # Category distribution
        category_counts = {}
        for trend in self.trends:
            category_counts[trend.category.value] = category_counts.get(trend.category.value, 0) + 1
        
        # Source distribution
        source_counts = {}
        for trend in self.trends:
            source_counts[trend.source.value] = source_counts.get(trend.source.value, 0) + 1
        
        return {
            'total_trends': len(self.trends),
            'average_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'average_popularity': sum(popularity_scores) / len(popularity_scores),
            'category_distribution': category_counts,
            'source_distribution': source_counts,
            'analysis_duration': self.analysis_duration
        }


class TrendCollectionConfig(BasePydanticModel):
    """Configuration for trend collection."""
    
    enabled_sources: List[TrendSourceEnum] = Field(
        default_factory=lambda: [TrendSourceEnum.YOUTUBE, TrendSourceEnum.GOOGLE_TRENDS]
    )
    collection_interval: int = Field(default=3600, description="Collection interval in seconds")
    max_trends_per_source: int = Field(default=100, ge=1, le=1000)
    trend_ttl: int = Field(default=86400, description="Trend TTL in seconds")
    auto_categorize: bool = Field(default=True)
    auto_analyze: bool = Field(default=True)
    quality_threshold: float = Field(default=3.0, ge=0.0, le=10.0)
    
    @validator('collection_interval')
    def validate_interval(cls, v):
        if v < 300:  # Minimum 5 minutes
            raise ValueError("Collection interval must be at least 300 seconds")
        return v


@dataclass
class TrendAlert(BaseDataClass):
    """Trend alert configuration and data."""
    
    name: str
    keywords: List[str]
    min_score_threshold: float = 7.0
    categories: List[TrendCategoryEnum] = field(default_factory=list)
    sources: List[TrendSourceEnum] = field(default_factory=list)
    is_active: bool = True
    notification_sent: bool = False
    matched_trends: List[TrendData] = field(default_factory=list)
    
    def matches_trend(self, trend: TrendData) -> bool:
        """Check if trend matches alert criteria."""
        if not self.is_active:
            return False
        
        # Check score threshold
        if trend.calculate_overall_score() < self.min_score_threshold:
            return False
        
        # Check categories
        if self.categories and trend.category not in self.categories:
            return False
        
        # Check sources
        if self.sources and trend.source not in self.sources:
            return False
        
        # Check keywords
        if self.keywords:
            trend_text = f"{trend.topic} {' '.join([kw.keyword for kw in trend.keywords])}"
            for keyword in self.keywords:
                if keyword.lower() in trend_text.lower():
                    return True
            return False
        
        return True
    
    def add_matched_trend(self, trend: TrendData):
        """Add a matching trend to the alert."""
        if self.matches_trend(trend):
            self.matched_trends.append(trend)
            return True
        return False


# Utility functions for trend operations

def merge_trend_data(trends: List[TrendData], merge_similar: bool = True) -> List[TrendData]:
    """
    Merge similar trends to avoid duplicates.
    
    Args:
        trends: List of trend data
        merge_similar: Whether to merge similar trends
        
    Returns:
        List of merged trends
    """
    if not merge_similar:
        return trends
    
    merged = []
    processed = set()
    
    for i, trend in enumerate(trends):
        if i in processed:
            continue
        
        # Find similar trends
        similar = [trend]
        for j, other_trend in enumerate(trends[i+1:], i+1):
            if j in processed:
                continue
            
            # Simple similarity check based on keywords
            similarity = calculate_trend_similarity(trend, other_trend)
            if similarity > 0.7:  # 70% similarity threshold
                similar.append(other_trend)
                processed.add(j)
        
        # Merge similar trends
        if len(similar) > 1:
            merged_trend = merge_similar_trends(similar)
            merged.append(merged_trend)
        else:
            merged.append(trend)
        
        processed.add(i)
    
    return merged


def calculate_trend_similarity(trend1: TrendData, trend2: TrendData) -> float:
    """Calculate similarity between two trends."""
    # Simple keyword-based similarity
    keywords1 = set(kw.keyword.lower() for kw in trend1.keywords)
    keywords2 = set(kw.keyword.lower() for kw in trend2.keywords)
    
    if not keywords1 and not keywords2:
        return 0.0
    
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    return len(intersection) / len(union) if union else 0.0


def merge_similar_trends(trends: List[TrendData]) -> TrendData:
    """Merge multiple similar trends into one."""
    if len(trends) == 1:
        return trends[0]
    
    # Use the trend with highest score as base
    base_trend = max(trends, key=lambda t: t.calculate_overall_score())
    
    # Merge keywords
    all_keywords = {}
    for trend in trends:
        for kw in trend.keywords:
            if kw.keyword in all_keywords:
                # Average the scores
                all_keywords[kw.keyword].score = (
                    all_keywords[kw.keyword].score + kw.score
                ) / 2
            else:
                all_keywords[kw.keyword] = kw
    
    base_trend.keywords = list(all_keywords.values())
    
    # Merge metrics
    if base_trend.metrics:
        for trend in trends[1:]:
            if trend.metrics:
                base_trend.metrics.views += trend.metrics.views
                base_trend.metrics.likes += trend.metrics.likes
                base_trend.metrics.comments += trend.metrics.comments
                base_trend.metrics.shares += trend.metrics.shares
                base_trend.metrics.mentions += trend.metrics.mentions
    
    # Update scores
    base_trend.popularity_score = sum(t.popularity_score for t in trends) / len(trends)
    
    return base_trend