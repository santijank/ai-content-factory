"""
Content Engine Services Package

This package contains core services for the AI Content Factory:
- AI Director: Main orchestrator for content creation
- Content Pipeline: Content generation workflow
- Trend Analyzer: Trend analysis and scoring
- Opportunity Engine: Content opportunity generation
- Content Generator: Actual content creation
- Service Registry: Service management and configuration
"""

from .ai_director import AIDirector
from .content_pipeline import ContentPipeline
from .trend_analyzer import TrendAnalyzer
from .opportunity_engine import OpportunityEngine
from .content_generator import ContentGenerator
from .service_registry import ServiceRegistry

__all__ = [
    'AIDirector',
    'ContentPipeline', 
    'TrendAnalyzer',
    'OpportunityEngine',
    'ContentGenerator',
    'ServiceRegistry'
]

# Version info
__version__ = "1.0.0"
__author__ = "AI Content Factory Team"