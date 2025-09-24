"""
Content Opportunities Database Model
Store AI-generated content opportunities from trends
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.models.base import BaseModel

class ContentOpportunities(BaseModel):
    """Model for storing content opportunities"""
    __tablename__ = 'content_opportunities'
    
    # Foreign key to trends
    trend_id = Column(String, ForeignKey('trends.id'), nullable=False, index=True)
    
    # Content idea
    suggested_angle = Column(Text, nullable=False)
    description = Column(Text)
    content_type = Column(String(50))  # educational, entertainment, news, etc.
    
    # Predictions
    estimated_views = Column(Integer, default=0)
    estimated_engagement = Column(Float, default=0.0)  # Expected engagement rate
    viral_potential = Column(Float, default=0.0)  # 1-10 scale
    
    # Competition analysis
    competition_level = Column(String(20), default='medium')  # low, medium, high
    competitor_count = Column(Integer, default=0)
    
    # Production estimates
    production_cost = Column(Float, default=0.0)  # Estimated cost in local currency
    production_time = Column(Integer, default=30)  # Estimated time in minutes
    difficulty_level = Column(String(20), default='medium')  # easy, medium, hard
    
    # ROI calculations
    estimated_roi = Column(Float, default=0.0)  # Return on investment multiplier
    revenue_potential = Column(Float, default=0.0)  # Estimated revenue
    
    # Scoring
    priority_score = Column(Float, default=0.0)  # Overall priority score 1-10
    ai_confidence = Column(Float, default=0.0)  # AI confidence in prediction
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, selected, produced, published, rejected
    assigned_to = Column(String(100))  # Who is working on this
    
    # Platform optimization
    target_platforms = Column(JSON)  # List of target platforms
    platform_optimization = Column(JSON)  # Platform-specific optimization data
    
    # Content details from AI
    suggested_title = Column(String(255))
    suggested_tags = Column(JSON)  # List of hashtags/tags
    suggested_duration = Column(Integer)  # Suggested duration in seconds
    
    # Timing
    best_publish_time = Column(DateTime)  # Optimal publishing time
    trending_window = Column(Integer, default=7)  # Days this trend will be relevant
    urgency_level = Column(String(20), default='medium')  # low, medium, high, urgent
    
    # Relationships
    trend = relationship("Trends", backref="opportunities")
    
    def __repr__(self):
        return f"<ContentOpportunity(id='{self.id}', angle='{self.suggested_angle[:50]}...', priority={self.priority_score})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'trend_id': self.trend_id,
            'suggested_angle': self.suggested_angle,
            'description': self.description,
            'content_type': self.content_type,
            'estimated_views': self.estimated_views,
            'estimated_engagement': self.estimated_engagement,
            'viral_potential': self.viral_potential,
            'competition_level': self.competition_level,
            'competitor_count': self.competitor_count,
            'production_cost': self.production_cost,
            'production_time': self.production_time,
            'difficulty_level': self.difficulty_level,
            'estimated_roi': self.estimated_roi,
            'revenue_potential': self.revenue_potential,
            'priority_score': self.priority_score,
            'ai_confidence': self.ai_confidence,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'target_platforms': self.target_platforms,
            'suggested_title': self.suggested_title,
            'suggested_tags': self.suggested_tags,
            'suggested_duration': self.suggested_duration,
            'best_publish_time': self.best_publish_time.isoformat() if self.best_publish_time else None,
            'trending_window': self.trending_window,
            'urgency_level': self.urgency_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create instance from dictionary"""
        # Remove non-model fields
        model_data = {k: v for k, v in data.items() 
                     if k in cls.__table__.columns.keys()}
        
        # Handle datetime fields
        if 'best_publish_time' in model_data and isinstance(model_data['best_publish_time'], str):
            model_data['best_publish_time'] = datetime.fromisoformat(model_data['best_publish_time'])
        
        return cls(**model_data)
    
    def calculate_priority_score(self):
        """Calculate and update priority score"""
        score = 0.0
        
        # Base score from viral potential
        score += self.viral_potential * 0.3
        
        # ROI factor
        score += min(self.estimated_roi * 2, 4.0) * 0.25
        
        # View potential factor (normalize to 1-10 scale)
        view_score = min(self.estimated_views / 10000, 10) * 0.2
        score += view_score
        
        # Competition factor (lower competition = higher score)
        competition_scores = {'low': 3, 'medium': 2, 'high': 1}
        score += competition_scores.get(self.competition_level, 2) * 0.15
        
        # AI confidence factor
        score += self.ai_confidence * 0.1
        
        # Normalize to 1-10 scale
        self.priority_score = min(max(score, 1.0), 10.0)
        return self.priority_score
    
    def is_urgent(self):
        """Check if this opportunity is urgent"""
        return (self.urgency_level == 'urgent' or 
                (self.trending_window <= 2 and self.viral_potential >= 7))
    
    def is_high_value(self):
        """Check if this is a high-value opportunity"""
        return (self.estimated_roi >= 3.0 and 
                self.viral_potential >= 6.0 and 
                self.competition_level in ['low', 'medium'])
    
    def get_effort_score(self):
        """Calculate effort required (lower is better)"""
        difficulty_scores = {'easy': 1, 'medium': 2, 'hard': 3}
        base_effort = difficulty_scores.get(self.difficulty_level, 2)
        
        # Factor in production time
        time_factor = min(self.production_time / 60, 3)  # Normalize to max 3 hours
        
        return base_effort + time_factor
    
    def get_value_effort_ratio(self):
        """Get value-to-effort ratio (higher is better)"""
        effort = self.get_effort_score()
        if effort == 0:
            return 0
        return self.priority_score / effort