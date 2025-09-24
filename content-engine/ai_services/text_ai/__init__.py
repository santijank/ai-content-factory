"""
Text AI Services Package

This package contains all text-based AI services for content generation:
- Base class for text AI services
- Groq service implementation
- OpenAI service implementation  
- Claude service implementation
"""

from .base_text_ai import BaseTextAI
from .groq_service import GroqService
from .openai_service import OpenAIService
from .claude_service import ClaudeService

__all__ = [
    'BaseTextAI',
    'GroqService',
    'OpenAIService', 
    'ClaudeService'
]

# Service configuration mappings
SERVICE_CONFIGS = {
    'groq': {
        'name': 'Groq',
        'description': 'Fast inference language model service',
        'cost_tier': 'budget',
        'speed': 'very_fast',
        'quality': 'good'
    },
    'openai': {
        'name': 'OpenAI GPT',
        'description': 'OpenAI GPT models for balanced performance',
        'cost_tier': 'balanced',
        'speed': 'fast',
        'quality': 'high'
    },
    'claude': {
        'name': 'Anthropic Claude', 
        'description': 'High-quality reasoning and content generation',
        'cost_tier': 'premium',
        'speed': 'medium',
        'quality': 'very_high'
    }
}

# Model mappings for each service
MODEL_CONFIGS = {
    'groq': {
        'default': 'mixtral-8x7b-32768',
        'fast': 'llama2-70b-4096',
        'creative': 'mixtral-8x7b-32768'
    },
    'openai': {
        'default': 'gpt-3.5-turbo',
        'fast': 'gpt-3.5-turbo', 
        'creative': 'gpt-4'
    },
    'claude': {
        'default': 'claude-3-sonnet-20240229',
        'fast': 'claude-3-haiku-20240307',
        'creative': 'claude-3-opus-20240229'
    }
}

def get_service_info(service_name: str) -> dict:
    """Get service configuration information"""
    return SERVICE_CONFIGS.get(service_name, {})

def get_model_for_task(service_name: str, task_type: str = 'default') -> str:
    """Get appropriate model for specific task"""
    service_models = MODEL_CONFIGS.get(service_name, {})
    return service_models.get(task_type, service_models.get('default', ''))

# Common prompt templates
PROMPT_TEMPLATES = {
    'trend_analysis': """
    Analyze this trending topic for content opportunities:
    
    Topic: {topic}
    Current popularity: {popularity_score}
    Growth rate: {growth_rate}
    Source: {source}
    
    Provide analysis in JSON format:
    {{
        "viral_potential": 1-10,
        "content_saturation": 1-10, 
        "audience_interest": 1-10,
        "monetization_opportunity": 1-10,
        "content_angles": ["angle1", "angle2", "angle3"],
        "target_demographics": ["demo1", "demo2"],
        "recommended_platforms": ["platform1", "platform2"]
    }}
    """,
    
    'content_script': """
    Create a {duration}-second video script for {platform}:
    
    Topic: {topic}
    Angle: {angle}
    Target audience: {audience}
    Style: {style}
    
    Format:
    {{
        "hook": "First 3 seconds to grab attention",
        "main_content": "Main message and value",
        "cta": "Clear call-to-action",
        "estimated_duration": {duration}
    }}
    """,
    
    'content_optimization': """
    Optimize this content for {platform}:
    
    Original content: {content}
    Platform requirements: {requirements}
    
    Provide:
    {{
        "optimized_title": "SEO and engagement optimized",
        "description": "Platform-specific description", 
        "hashtags": ["#tag1", "#tag2", "#tag3"],
        "thumbnail_concept": "Eye-catching thumbnail idea"
    }}
    """
}