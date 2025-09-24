"""
AI Content Factory - Database Models Package
==========================================

This package contains all database model definitions for the AI Content Factory system.

Models included:
- Base: Common base model with shared functionality
- Trends: Trending topics and their metadata
- ContentOpportunities: Content opportunities derived from trends
- ContentItems: Generated content items and their production data
- Uploads: Platform upload records and metadata
- PerformanceMetrics: Performance tracking and analytics data

Usage:
    from database.models import Trend, ContentOpportunity, ContentItem
    
    # Create a new trend
    trend = Trend(
        topic="AI Tools 2025",
        popularity_score=9.2,
        source="youtube"
    )
"""

# Import base model first (required for inheritance)
from .base import Base, BaseModel, TimestampMixin

# Import all models
from .trends import Trend
from .content_opportunities import ContentOpportunity  
from .content_items import ContentItem
from .uploads import Upload
from .performance_metrics import PerformanceMetric

# Model registry for easy access
MODEL_REGISTRY = {
    'trend': Trend,
    'content_opportunity': ContentOpportunity,
    'content_item': ContentItem,
    'upload': Upload,
    'performance_metric': PerformanceMetric
}

# Export all models
__all__ = [
    # Base classes
    'Base',
    'BaseModel', 
    'TimestampMixin',
    
    # Core models
    'Trend',
    'ContentOpportunity',
    'ContentItem',
    'Upload',
    'PerformanceMetric',
    
    # Utilities
    'MODEL_REGISTRY',
    'get_model',
    'create_all_tables',
    'drop_all_tables'
]

def get_model(model_name: str):
    """
    Get model class by name.
    
    Args:
        model_name: Name of the model (e.g., 'trend', 'content_opportunity')
        
    Returns:
        Model class if found, None otherwise
        
    Example:
        TrendModel = get_model('trend')
        trend = TrendModel(topic="AI News")
    """
    return MODEL_REGISTRY.get(model_name.lower())

def create_all_tables(engine):
    """
    Create all database tables.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Example:
        from sqlalchemy import create_engine
        from database.models import create_all_tables
        
        engine = create_engine('postgresql://user:pass@localhost/db')
        create_all_tables(engine)
    """
    Base.metadata.create_all(bind=engine)

def drop_all_tables(engine):
    """
    Drop all database tables. USE WITH CAUTION!
    
    Args:
        engine: SQLAlchemy engine instance
        
    Warning:
        This will delete all data in the database!
    """
    Base.metadata.drop_all(bind=engine)

# Model validation and integrity checks
def validate_models():
    """
    Validate all models for common issues.
    
    Returns:
        list: List of validation issues found
    """
    issues = []
    
    for name, model in MODEL_REGISTRY.items():
        # Check if model has required attributes
        if not hasattr(model, '__tablename__'):
            issues.append(f"Model {name} missing __tablename__")
            
        if not hasattr(model, 'id'):
            issues.append(f"Model {name} missing id field")
            
        # Check if model inherits from BaseModel
        if not issubclass(model, BaseModel):
            issues.append(f"Model {name} should inherit from BaseModel")
    
    return issues

# Database initialization helper
def init_database(engine, drop_existing=False):
    """
    Initialize database with all tables.
    
    Args:
        engine: SQLAlchemy engine
        drop_existing: Whether to drop existing tables first
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if drop_existing:
            print("🗑️  Dropping existing tables...")
            drop_all_tables(engine)
            
        print("📊 Creating database tables...")
        create_all_tables(engine)
        
        # Validate models
        issues = validate_models()
        if issues:
            print("⚠️  Model validation issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
            
        print("✅ Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

# Version and compatibility info
__version__ = "1.0.0"
__db_version__ = "1.0.0"

# Model metadata
MODEL_INFO = {
    'Trend': {
        'description': 'Trending topics from various sources',
        'primary_key': 'id',
        'indexes': ['topic', 'source', 'collected_at'],
        'relationships': ['content_opportunities']
    },
    'ContentOpportunity': {
        'description': 'Content opportunities derived from trends',
        'primary_key': 'id',
        'indexes': ['trend_id', 'priority_score', 'status'],
        'relationships': ['trend', 'content_items']
    },
    'ContentItem': {
        'description': 'Generated content items and production data',
        'primary_key': 'id',
        'indexes': ['opportunity_id', 'production_status'],
        'relationships': ['opportunity', 'uploads']
    },
    'Upload': {
        'description': 'Platform upload records and metadata',
        'primary_key': 'id',
        'indexes': ['content_id', 'platform', 'uploaded_at'],
        'relationships': ['content_item', 'performance_metrics']
    },
    'PerformanceMetric': {
        'description': 'Performance tracking and analytics',
        'primary_key': 'id',
        'indexes': ['upload_id', 'measured_at'],
        'relationships': ['upload']
    }
}