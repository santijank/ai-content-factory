"""
Trends Database Model
Store trending topics and their metadata
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON, Boolean
from database.models.base import BaseModel

class Trends(BaseModel):
    """Model for storing trending topics"""
    __tablename__ = 'trends'
    
    # Basic trend information
    source = Column(String(50), nullable=False, index=True)  # youtube, google, tiktok, etc.
    topic = Column(String(255), nullable=False, index=True)
    keywords = Column(JSON)  # List of related keywords
    
    # Metrics
    popularity_score = Column(Float, default=0.0)  # 1-10 scale
    growth_rate = Column(Float, default=0.0)  # Percentage growth
    
    # Categorization
    category = Column(String(100), index=True)  # technology, entertainment, etc.
    region = Column(String(50), default='global')  # geographic region
    
    # Timestamps
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Raw data storage
    raw_data = Column(JSON)  # Store original API response
    
    # Analysis flags
    is_analyzed = Column(Boolean, default=False)
    analysis_score = Column(Float)  # AI analysis score
    
    # Search optimization
    search_volume = Column(Integer)  # Monthly search volume
    competition_level = Column(String(20))  # low, medium, high
    
    def __repr__(self):
        return f"<Trend(id='{self.id}', topic='{self.topic}', score={self.popularity_score})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'source': self.source,
            'topic': self.topic,
            'keywords': self.keywords,
            'popularity_score': self.popularity_score,
            'growth_rate': self.growth_rate,
            'category': self.category,
            'region': self.region,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_analyzed': self.is_analyzed,
            'analysis_score': self.analysis_score,
            'search_volume': self.search_volume,
            'competition_level': self.competition_level
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create instance from dictionary"""
        # Remove non-model fields
        model_data = {k: v for k, v in data.items() 
                     if k in cls.__table__.columns.keys()}
        
        # Handle datetime fields
        if 'collected_at' in model_data and isinstance(model_data['collected_at'], str):
            model_data['collected_at'] = datetime.fromisoformat(model_data['collected_at'])
        
        return cls(**model_data)
    
    def is_hot_trend(self):
        """Check if this is a hot trend"""
        return (self.popularity_score >= 7.0 and 
                self.growth_rate >= 15.0 and 
                self.competition_level in ['low', 'medium'])
    
    def get_opportunity_score(self):
        """Calculate opportunity score for content creation"""
        base_score = self.popularity_score
        
        # Boost for high growth
        if self.growth_rate >= 20:
            base_score += 1.0
        elif self.growth_rate >= 10:
            base_score += 0.5
        
        # Reduce for high competition
        if self.competition_level == 'high':
            base_score -= 1.0
        elif self.competition_level == 'medium':
            base_score -= 0.3
        
        # Boost for good analysis score
        if self.analysis_score:
            base_score += (self.analysis_score - 5) * 0.2
        
        return min(max(base_score, 0), 10)  # Keep between 0-10