"""
Content Opportunity Model
Represents content creation opportunities derived from trending topics

This module defines:
- ContentOpportunity class with all opportunity data
- OpportunityStatus and OpportunityPriority enums
- Opportunity scoring and ranking algorithms
- Content angle suggestions
- ROI estimation
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json
import uuid

class OpportunityStatus(Enum):
    """Status of a content opportunity"""
    PENDING = "pending"
    ANALYZED = "analyzed"
    SELECTED = "selected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PUBLISHED = "published"
    REJECTED = "rejected"
    EXPIRED = "expired"
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, status_str: str) -> 'OpportunityStatus':
        """Create status from string"""
        for status in cls:
            if status.value == status_str.lower():
                return status
        raise ValueError(f"Invalid status: {status_str}")

class OpportunityPriority(Enum):
    """Priority level of content opportunity"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_score(cls, score: float) -> 'OpportunityPriority':
        """Convert numeric score to priority"""
        if score >= 9.0:
            return cls.CRITICAL
        elif score >= 7.5:
            return cls.URGENT
        elif score >= 6.0:
            return cls.HIGH
        elif score >= 4.0:
            return cls.MEDIUM
        else:
            return cls.LOW

@dataclass
class TrendData:
    """Trend information associated with opportunity"""
    topic: str
    source: str  # youtube, google_trends, twitter, reddit
    keywords: List[str]
    popularity_score: float
    growth_rate: float
    region: str = "TH"
    category: Optional[str] = None
    search_volume: Optional[int] = None
    competition_level: str = "medium"  # low, medium, high
    trend_duration: Optional[int] = None  # Days trending
    peak_time: Optional[datetime] = None
    related_topics: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "topic": self.topic,
            "source": self.source,
            "keywords": self.keywords,
            "popularity_score": self.popularity_score,
            "growth_rate": self.growth_rate,
            "region": self.region,
            "category": self.category,
            "search_volume": self.search_volume,
            "competition_level": self.competition_level,
            "trend_duration": self.trend_duration,
            "peak_time": self.peak_time.isoformat() if self.peak_time else None,
            "related_topics": self.related_topics
        }

@dataclass
class ContentAngle:
    """Suggested content angle for the opportunity"""
    title: str
    description: str
    target_audience: str
    content_type: str  # educational, entertainment, news, review, tutorial
    estimated_engagement: float  # 1-10 scale
    difficulty_level: str = "medium"  # easy, medium, hard
    required_resources: List[str] = field(default_factory=list)
    unique_selling_point: str = ""
    hook_suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "description": self.description,
            "target_audience": self.target_audience,
            "content_type": self.content_type,
            "estimated_engagement": self.estimated_engagement,
            "difficulty_level": self.difficulty_level,
            "required_resources": self.required_resources,
            "unique_selling_point": self.unique_selling_point,
            "hook_suggestions": self.hook_suggestions
        }

@dataclass
class ROIEstimate:
    """Return on Investment estimation"""
    estimated_views: int
    estimated_engagement_rate: float
    estimated_revenue: float
    production_cost: float
    time_investment_hours: float
    roi_ratio: float = 0.0
    confidence_level: float = 0.5  # 0-1 scale
    break_even_views: int = 0
    
    def __post_init__(self):
        """Calculate derived values"""
        if self.production_cost > 0:
            self.roi_ratio = (self.estimated_revenue - self.production_cost) / self.production_cost
        
        if self.estimated_revenue > 0 and self.estimated_views > 0:
            revenue_per_view = self.estimated_revenue / self.estimated_views
            if revenue_per_view > 0:
                self.break_even_views = int(self.production_cost / revenue_per_view)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "estimated_views": self.estimated_views,
            "estimated_engagement_rate": self.estimated_engagement_rate,
            "estimated_revenue": self.estimated_revenue,
            "production_cost": self.production_cost,
            "time_investment_hours": self.time_investment_hours,
            "roi_ratio": self.roi_ratio,
            "confidence_level": self.confidence_level,
            "break_even_views": self.break_even_views
        }

@dataclass
class OpportunityMetrics:
    """Metrics for scoring and ranking opportunities"""
    viral_potential: float  # 1-10 scale
    content_saturation: float  # 1-10 scale (lower is better)
    audience_interest: float  # 1-10 scale
    monetization_potential: float  # 1-10 scale
    production_feasibility: float  # 1-10 scale
    time_sensitivity: float  # 1-10 scale
    brand_alignment: float = 5.0  # 1-10 scale
    competitive_advantage: float = 5.0  # 1-10 scale
    
    @property
    def overall_score(self) -> float:
        """Calculate overall opportunity score"""
        # Weighted scoring algorithm
        weights = {
            "viral_potential": 0.20,
            "audience_interest": 0.20,
            "monetization_potential": 0.15,
            "production_feasibility": 0.15,
            "time_sensitivity": 0.10,
            "brand_alignment": 0.10,
            "competitive_advantage": 0.05,
            "content_saturation_penalty": -0.05  # Penalty for high saturation
        }
        
        score = (
            self.viral_potential * weights["viral_potential"] +
            self.audience_interest * weights["audience_interest"] +
            self.monetization_potential * weights["monetization_potential"] +
            self.production_feasibility * weights["production_feasibility"] +
            self.time_sensitivity * weights["time_sensitivity"] +
            self.brand_alignment * weights["brand_alignment"] +
            self.competitive_advantage * weights["competitive_advantage"] +
            (10 - self.content_saturation) * weights["content_saturation_penalty"]
        ) * 10  # Scale to 1-10
        
        return min(10.0, max(1.0, score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "viral_potential": self.viral_potential,
            "content_saturation": self.content_saturation,
            "audience_interest": self.audience_interest,
            "monetization_potential": self.monetization_potential,
            "production_feasibility": self.production_feasibility,
            "time_sensitivity": self.time_sensitivity,
            "brand_alignment": self.brand_alignment,
            "competitive_advantage": self.competitive_advantage,
            "overall_score": self.overall_score
        }

class ContentOpportunity:
    """
    Represents a content creation opportunity derived from trending data
    """
    
    def __init__(
        self,
        trend_data: TrendData,
        content_angles: List[ContentAngle] = None,
        roi_estimate: ROIEstimate = None,
        metrics: OpportunityMetrics = None,
        opportunity_id: str = None
    ):
        """
        Initialize content opportunity
        
        Args:
            trend_data: Associated trend information
            content_angles: Suggested content angles
            roi_estimate: ROI estimation
            metrics: Opportunity metrics
            opportunity_id: Unique opportunity ID
        """
        self.id = opportunity_id or str(uuid.uuid4())
        self.trend_data = trend_data
        self.content_angles = content_angles or []
        self.roi_estimate = roi_estimate
        self.metrics = metrics
        
        # Status and metadata
        self.status = OpportunityStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=7)  # Default 7-day expiry
        
        # User interaction
        self.is_bookmarked = False
        self.user_rating: Optional[float] = None
        self.user_notes: str = ""
        self.tags: List[str] = []
        
        # Production tracking
        self.selected_angle_index: Optional[int] = None
        self.production_started_at: Optional[datetime] = None
        self.production_completed_at: Optional[datetime] = None
        self.published_at: Optional[datetime] = None
        
        # Performance tracking
        self.actual_performance: Dict[str, Any] = {}
    
    @property
    def priority(self) -> OpportunityPriority:
        """Get opportunity priority based on metrics"""
        if self.metrics:
            return OpportunityPriority.from_score(self.metrics.overall_score)
        return OpportunityPriority.MEDIUM
    
    @property
    def is_expired(self) -> bool:
        """Check if opportunity has expired"""
        return datetime.now() > self.expires_at
    
    @property
    def time_remaining(self) -> timedelta:
        """Get time remaining before expiry"""
        return max(timedelta(0), self.expires_at - datetime.now())
    
    @property
    def selected_angle(self) -> Optional[ContentAngle]:
        """Get selected content angle"""
        if self.selected_angle_index is not None and 0 <= self.selected_angle_index < len(self.content_angles):
            return self.content_angles[self.selected_angle_index]
        return None
    
    def add_content_angle(self, angle: ContentAngle):
        """Add a content angle suggestion"""
        self.content_angles.append(angle)
        self.updated_at = datetime.now()
    
    def select_angle(self, angle_index: int):
        """Select a content angle for production"""
        if 0 <= angle_index < len(self.content_angles):
            self.selected_angle_index = angle_index
            self.status = OpportunityStatus.SELECTED
            self.updated_at = datetime.now()
        else:
            raise IndexError("Invalid angle index")
    
    def start_production(self):
        """Mark opportunity as in production"""
        self.status = OpportunityStatus.IN_PROGRESS
        self.production_started_at = datetime.now()
        self.updated_at = datetime.now()
    
    def complete_production(self):
        """Mark production as completed"""
        self.status = OpportunityStatus.COMPLETED
        self.production_completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def publish(self):
        """Mark content as published"""
        self.status = OpportunityStatus.PUBLISHED
        self.published_at = datetime.now()
        self.updated_at = datetime.now()
    
    def reject(self, reason: str = ""):
        """Reject the opportunity"""
        self.status = OpportunityStatus.REJECTED
        if reason:
            self.user_notes = f"Rejected: {reason}"
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str):
        """Add a tag to the opportunity"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str):
        """Remove a tag from the opportunity"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def bookmark(self):
        """Bookmark the opportunity"""
        self.is_bookmarked = True
        self.updated_at = datetime.now()
    
    def unbookmark(self):
        """Remove bookmark from opportunity"""
        self.is_bookmarked = False
        self.updated_at = datetime.now()
    
    def rate(self, rating: float):
        """Rate the opportunity (1-10 scale)"""
        if 1 <= rating <= 10:
            self.user_rating = rating
            self.updated_at = datetime.now()
        else:
            raise ValueError("Rating must be between 1 and 10")
    
    def update_performance(self, performance_data: Dict[str, Any]):
        """Update actual performance data"""
        self.actual_performance.update(performance_data)
        self.updated_at = datetime.now()
    
    def calculate_performance_accuracy(self) -> Optional[float]:
        """
        Calculate accuracy of ROI predictions vs actual performance
        
        Returns:
            Accuracy score (0-1) or None if insufficient data
        """
        if not self.roi_estimate or not self.actual_performance:
            return None
        
        actual_views = self.actual_performance.get("views")
        actual_revenue = self.actual_performance.get("revenue")
        
        if actual_views is None or actual_revenue is None:
            return None
        
        # Calculate prediction accuracy
        view_accuracy = 1 - abs(actual_views - self.roi_estimate.estimated_views) / max(actual_views, self.roi_estimate.estimated_views)
        revenue_accuracy = 1 - abs(actual_revenue - self.roi_estimate.estimated_revenue) / max(actual_revenue, self.roi_estimate.estimated_revenue)
        
        return (view_accuracy + revenue_accuracy) / 2
    
    def extend_expiry(self, days: int):
        """Extend opportunity expiry by specified days"""
        self.expires_at += timedelta(days=days)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert opportunity to dictionary"""
        return {
            "id": self.id,
            "trend_data": self.trend_data.to_dict(),
            "content_angles": [angle.to_dict() for angle in self.content_angles],
            "roi_estimate": self.roi_estimate.to_dict() if self.roi_estimate else None,
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "status": self.status.value,
            "priority": self.priority.name.lower(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired,
            "time_remaining_hours": self.time_remaining.total_seconds() / 3600,
            "is_bookmarked": self.is_bookmarked,
            "user_rating": self.user_rating,
            "user_notes": self.user_notes,
            "tags": self.tags,
            "selected_angle_index": self.selected_angle_index,
            "production_started_at": self.production_started_at.isoformat() if self.production_started_at else None,
            "production_completed_at": self.production_completed_at.isoformat() if self.production_completed_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "actual_performance": self.actual_performance
        }
    
    def to_json(self) -> str:
        """Convert opportunity to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentOpportunity':
        """Create opportunity from dictionary"""
        # Reconstruct trend data
        trend_data = TrendData(**data["trend_data"])
        
        # Reconstruct content angles
        content_angles = [ContentAngle(**angle_data) for angle_data in data.get("content_angles", [])]
        
        # Reconstruct ROI estimate
        roi_estimate = None
        if data.get("roi_estimate"):
            roi_estimate = ROIEstimate(**data["roi_estimate"])
        
        # Reconstruct metrics
        metrics = None
        if data.get("metrics"):
            metrics = OpportunityMetrics(**data["metrics"])
        
        # Create opportunity
        opportunity = cls(
            trend_data=trend_data,
            content_angles=content_angles,
            roi_estimate=roi_estimate,
            metrics=metrics,
            opportunity_id=data["id"]
        )
        
        # Set additional fields
        opportunity.status = OpportunityStatus.from_string(data["status"])
        opportunity.created_at = datetime.fromisoformat(data["created_at"])
        opportunity.updated_at = datetime.fromisoformat(data["updated_at"])
        opportunity.expires_at = datetime.fromisoformat(data["expires_at"])
        opportunity.is_bookmarked = data.get("is_bookmarked", False)
        opportunity.user_rating = data.get("user_rating")
        opportunity.user_notes = data.get("user_notes", "")
        opportunity.tags = data.get("tags", [])
        opportunity.selected_angle_index = data.get("selected_angle_index")
        opportunity.actual_performance = data.get("actual_performance", {})
        
        # Set datetime fields
        if data.get("production_started_at"):
            opportunity.production_started_at = datetime.fromisoformat(data["production_started_at"])
        if data.get("production_completed_at"):
            opportunity.production_completed_at = datetime.fromisoformat(data["production_completed_at"])
        if data.get("published_at"):
            opportunity.published_at = datetime.fromisoformat(data["published_at"])
        
        return opportunity
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ContentOpportunity':
        """Create opportunity from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        return f"ContentOpportunity(id={self.id[:8]}, topic='{self.trend_data.topic}', status={self.status}, priority={self.priority})"
    
    def __repr__(self) -> str:
        return f"ContentOpportunity(id='{self.id}', topic='{self.trend_data.topic}', angles={len(self.content_angles)}, status='{self.status}')"

# Utility functions for opportunity management
def rank_opportunities(opportunities: List[ContentOpportunity]) -> List[ContentOpportunity]:
    """
    Rank opportunities by overall score and priority
    
    Args:
        opportunities: List of opportunities to rank
        
    Returns:
        Sorted list of opportunities (best first)
    """
    def score_key(opp):
        base_score = opp.metrics.overall_score if opp.metrics else 5.0
        priority_bonus = opp.priority.value * 0.5
        time_penalty = 1.0 if opp.is_expired else 0.0
        bookmark_bonus = 0.5 if opp.is_bookmarked else 0.0
        
        return base_score + priority_bonus - time_penalty + bookmark_bonus
    
    return sorted(opportunities, key=score_key, reverse=True)

def filter_opportunities(
    opportunities: List[ContentOpportunity],
    status: Optional[OpportunityStatus] = None,
    priority: Optional[OpportunityPriority] = None,
    tags: Optional[List[str]] = None,
    bookmarked_only: bool = False,
    exclude_expired: bool = True
) -> List[ContentOpportunity]:
    """
    Filter opportunities based on criteria
    
    Args:
        opportunities: List of opportunities to filter
        status: Filter by status
        priority: Filter by priority
        tags: Filter by tags (must have at least one)
        bookmarked_only: Only bookmarked opportunities
        exclude_expired: Exclude expired opportunities
        
    Returns:
        Filtered list of opportunities
    """
    filtered = opportunities
    
    if exclude_expired:
        filtered = [opp for opp in filtered if not opp.is_expired]
    
    if status:
        filtered = [opp for opp in filtered if opp.status == status]
    
    if priority:
        filtered = [opp for opp in filtered if opp.priority == priority]
    
    if bookmarked_only:
        filtered = [opp for opp in filtered if opp.is_bookmarked]
    
    if tags:
        filtered = [opp for opp in filtered if any(tag in opp.tags for tag in tags)]
    
    return filtered