"""
AI Content Factory - Quality Constants
=====================================

Quality tier definitions, AI service configurations, cost calculations,
and performance metrics for the AI Content Factory system.
"""

from typing import Dict, List, Any
from dataclasses import dataclass

# Quality tier enumeration
QUALITY_TIERS = ['budget', 'balanced', 'premium']

# Base costs per tier (in THB)
BASE_COSTS = {
    'budget': 15.0,
    'balanced': 45.0,
    'premium': 150.0
}

# AI Service Configurations by Tier
AI_SERVICE_CONFIGS = {
    'budget': {
        'text_ai': {
            'primary': 'groq',
            'fallback': 'openai_gpt3',
            'model': 'mixtral-8x7b-32768',
            'max_tokens': 2000,
            'temperature': 0.7,
            'cost_per_1k_tokens': 0.20
        },
        'image_ai': {
            'primary': 'stable_diffusion_local',
            'fallback': 'dall_e_2',
            'model': 'sd_1_5',
            'resolution': '512x512',
            'steps': 20,
            'cost_per_image': 0.50
        },
        'audio_ai': {
            'primary': 'gtts',
            'fallback': 'azure_tts_standard',
            'voice': 'th-TH-PremwadeeNeural',
            'speed': 1.0,
            'cost_per_minute': 2.0
        },
        'video_ai': {
            'primary': 'ffmpeg_local',
            'fallback': 'cloudinary',
            'codec': 'h264',
            'bitrate': 1500,
            'fps': 24,
            'cost_per_minute': 5.0
        }
    },
    
    'balanced': {
        'text_ai': {
            'primary': 'openai_gpt4',
            'fallback': 'claude_sonnet',
            'model': 'gpt-4o-mini',
            'max_tokens': 4000,
            'temperature': 0.8,
            'cost_per_1k_tokens': 1.50
        },
        'image_ai': {
            'primary': 'leonardo_ai',
            'fallback': 'dall_e_3',
            'model': 'leonardo_creative',
            'resolution': '1024x1024',
            'steps': 30,
            'cost_per_image': 3.00
        },
        'audio_ai': {
            'primary': 'azure_tts_neural',
            'fallback': 'aws_polly_neural',
            'voice': 'th-TH-PremwadeeNeural',
            'speed': 1.0,
            'cost_per_minute': 6.0
        },
        'video_ai': {
            'primary': 'runway_ml',
            'fallback': 'pika_labs',
            'model': 'gen2',
            'resolution': '1280x720',
            'fps': 30,
            'cost_per_minute': 25.0
        }
    },
    
    'premium': {
        'text_ai': {
            'primary': 'claude_opus',
            'fallback': 'gpt4_turbo',
            'model': 'claude-3-opus-20240229',
            'max_tokens': 8000,
            'temperature': 0.9,
            'cost_per_1k_tokens': 15.00
        },
        'image_ai': {
            'primary': 'midjourney_api',
            'fallback': 'dall_e_3_hd',
            'model': 'midjourney_v6',
            'resolution': '2048x2048',
            'steps': 50,
            'cost_per_image': 12.00
        },
        'audio_ai': {
            'primary': 'elevenlabs_premium',
            'fallback': 'azure_tts_premium',
            'voice': 'Thai_Female_Premium',
            'speed': 1.0,
            'cost_per_minute': 20.0
        },
        'video_ai': {
            'primary': 'sora_openai',
            'fallback': 'runway_premium',
            'model': 'sora_turbo',
            'resolution': '1920x1080',
            'fps': 60,
            'cost_per_minute': 100.0
        }
    }
}

# Quality metrics and thresholds
QUALITY_METRICS = {
    'budget': {
        'min_content_score': 6.0,
        'max_generation_time': 300,  # 5 minutes
        'target_accuracy': 0.75,
        'min_uniqueness': 0.60,
        'max_errors_per_content': 3,
        'performance_target': {
            'views': 500,
            'engagement_rate': 2.0,
            'retention_rate': 0.40
        }
    },
    'balanced': {
        'min_content_score': 7.5,
        'max_generation_time': 600,  # 10 minutes
        'target_accuracy': 0.85,
        'min_uniqueness': 0.75,
        'max_errors_per_content': 2,
        'performance_target': {
            'views': 2000,
            'engagement_rate': 4.0,
            'retention_rate': 0.60
        }
    },
    'premium': {
        'min_content_score': 9.0,
        'max_generation_time': 1200,  # 20 minutes
        'target_accuracy': 0.95,
        'min_uniqueness': 0.90,
        'max_errors_per_content': 1,
        'performance_target': {
            'views': 10000,
            'engagement_rate': 8.0,
            'retention_rate': 0.80
        }
    }
}

# Content specifications by tier
CONTENT_SPECIFICATIONS = {
    'budget': {
        'video': {
            'max_resolution': '1280x720',
            'max_fps': 24,
            'max_bitrate': 2500,
            'max_duration': 600,  # 10 minutes
            'codec': 'h264',
            'audio_bitrate': 128,
            'formats': ['mp4', 'webm']
        },
        'image': {
            'max_resolution': '1024x1024',
            'max_file_size': 2 * 1024**2,  # 2 MB
            'formats': ['jpg', 'png', 'webp'],
            'quality': 80,
            'compression': 'medium'
        },
        'audio': {
            'max_bitrate': 128,
            'max_duration': 1800,  # 30 minutes
            'sample_rate': 44100,
            'formats': ['mp3', 'aac']
        }
    },
    'balanced': {
        'video': {
            'max_resolution': '1920x1080',
            'max_fps': 30,
            'max_bitrate': 5000,
            'max_duration': 2400,  # 40 minutes
            'codec': 'h264',
            'audio_bitrate': 192,
            'formats': ['mp4', 'mov', 'webm']
        },
        'image': {
            'max_resolution': '2048x2048',
            'max_file_size': 8 * 1024**2,  # 8 MB
            'formats': ['jpg', 'png', 'webp', 'tiff'],
            'quality': 90,
            'compression': 'low'
        },
        'audio': {
            'max_bitrate': 320,
            'max_duration': 3600,  # 1 hour
            'sample_rate': 48000,
            'formats': ['mp3', 'wav', 'aac', 'flac']
        }
    },
    'premium': {
        'video': {
            'max_resolution': '3840x2160',
            'max_fps': 60,
            'max_bitrate': 15000,
            'max_duration': 14400,  # 4 hours
            'codec': 'h265',
            'audio_bitrate': 320,
            'formats': ['mp4', 'mov', 'avi', 'mkv']
        },
        'image': {
            'max_resolution': '4096x4096',
            'max_file_size': 50 * 1024**2,  # 50 MB
            'formats': ['jpg', 'png', 'webp', 'tiff', 'raw'],
            'quality': 100,
            'compression': 'none'
        },
        'audio': {
            'max_bitrate': 320,
            'max_duration': 14400,  # 4 hours
            'sample_rate': 96000,
            'formats': ['wav', 'flac', 'aiff', 'dsd']
        }
    }
}

# Processing time estimates (in seconds)
PROCESSING_TIME_ESTIMATES = {
    'budget': {
        'script_generation': 30,
        'image_generation': 60,
        'audio_generation': 90,
        'video_assembly': 180,
        'optimization': 60,
        'total_overhead': 60
    },
    'balanced': {
        'script_generation': 60,
        'image_generation': 120,
        'audio_generation': 180,
        'video_assembly': 300,
        'optimization': 120,
        'total_overhead': 120
    },
    'premium': {
        'script_generation': 120,
        'image_generation': 300,
        'audio_generation': 360,
        'video_assembly': 600,
        'optimization': 240,
        'total_overhead': 180
    }
}

# Resource limits by tier
RESOURCE_LIMITS = {
    'budget': {
        'max_concurrent_generations': 2,
        'max_daily_generations': 50,
        'max_monthly_cost': 1500,  # THB
        'cpu_cores': 2,
        'memory_gb': 4,
        'storage_gb': 50,
        'bandwidth_gb': 100
    },
    'balanced': {
        'max_concurrent_generations': 5,
        'max_daily_generations': 200,
        'max_monthly_cost': 10000,  # THB
        'cpu_cores': 4,
        'memory_gb': 16,
        'storage_gb': 200,
        'bandwidth_gb': 500
    },
    'premium': {
        'max_concurrent_generations': 10,
        'max_daily_generations': 1000,
        'max_monthly_cost': 50000,  # THB
        'cpu_cores': 16,
        'memory_gb': 64,
        'storage_gb': 1000,
        'bandwidth_gb': 2000
    }
}

# API rate limits by tier
API_RATE_LIMITS = {
    'budget': {
        'requests_per_minute': 20,
        'requests_per_hour': 500,
        'requests_per_day': 5000,
        'max_request_size': 10 * 1024**2,  # 10 MB
        'max_response_size': 50 * 1024**2  # 50 MB
    },
    'balanced': {
        'requests_per_minute': 100,
        'requests_per_hour': 2000,
        'requests_per_day': 20000,
        'max_request_size': 100 * 1024**2,  # 100 MB
        'max_response_size': 500 * 1024**2  # 500 MB
    },
    'premium': {
        'requests_per_minute': 500,
        'requests_per_hour': 10000,
        'requests_per_day': 100000,
        'max_request_size': 1 * 1024**3,  # 1 GB
        'max_response_size': 5 * 1024**3   # 5 GB
    }
}

# Feature availability by tier
FEATURE_AVAILABILITY = {
    'budget': {
        'basic_content_generation': True,
        'single_platform_upload': True,
        'basic_analytics': True,
        'standard_templates': True,
        'email_support': True,
        'api_access': False,
        'custom_branding': False,
        'advanced_analytics': False,
        'priority_support': False,
        'white_label': False
    },
    'balanced': {
        'basic_content_generation': True,
        'multi_platform_upload': True,
        'advanced_analytics': True,
        'premium_templates': True,
        'email_support': True,
        'api_access': True,
        'custom_branding': True,
        'a_b_testing': True,
        'priority_support': False,
        'white_label': False
    },
    'premium': {
        'basic_content_generation': True,
        'multi_platform_upload': True,
        'advanced_analytics': True,
        'custom_templates': True,
        'priority_support': True,
        'api_access': True,
        'custom_branding': True,
        'white_label': True,
        'dedicated_account_manager': True,
        'custom_integrations': True
    }
}

# Tier definitions for easy access
@dataclass
class QualityTier:
    """Quality tier definition."""
    name: str
    display_name: str
    base_cost: float
    ai_services: Dict[str, Any]
    metrics: Dict[str, Any]
    specifications: Dict[str, Any]
    processing_times: Dict[str, int]
    resource_limits: Dict[str, Any]
    rate_limits: Dict[str, Any]
    features: Dict[str, bool]

# Create tier instances
BUDGET_TIER = QualityTier(
    name='budget',
    display_name='Budget',
    base_cost=BASE_COSTS['budget'],
    ai_services=AI_SERVICE_CONFIGS['budget'],
    metrics=QUALITY_METRICS['budget'],
    specifications=CONTENT_SPECIFICATIONS['budget'],
    processing_times=PROCESSING_TIME_ESTIMATES['budget'],
    resource_limits=RESOURCE_LIMITS['budget'],
    rate_limits=API_RATE_LIMITS['budget'],
    features=FEATURE_AVAILABILITY['budget']
)

BALANCED_TIER = QualityTier(
    name='balanced',
    display_name='Balanced',
    base_cost=BASE_COSTS['balanced'],
    ai_services=AI_SERVICE_CONFIGS['balanced'],
    metrics=QUALITY_METRICS['balanced'],
    specifications=CONTENT_SPECIFICATIONS['balanced'],
    processing_times=PROCESSING_TIME_ESTIMATES['balanced'],
    resource_limits=RESOURCE_LIMITS['balanced'],
    rate_limits=API_RATE_LIMITS['balanced'],
    features=FEATURE_AVAILABILITY['balanced']
)

PREMIUM_TIER = QualityTier(
    name='premium',
    display_name='Premium',
    base_cost=BASE_COSTS['premium'],
    ai_services=AI_SERVICE_CONFIGS['premium'],
    metrics=QUALITY_METRICS['premium'],
    specifications=CONTENT_SPECIFICATIONS['premium'],
    processing_times=PROCESSING_TIME_ESTIMATES['premium'],
    resource_limits=RESOURCE_LIMITS['premium'],
    rate_limits=API_RATE_LIMITS['premium'],
    features=FEATURE_AVAILABILITY['premium']
)

# Tier registry for programmatic access
TIER_REGISTRY = {
    'budget': BUDGET_TIER,
    'balanced': BALANCED_TIER,
    'premium': PREMIUM_TIER
}

# Cost calculation functions
def calculate_content_cost(tier_name: str, content_type: str, duration_minutes: float = 1.0, 
                          complexity_multiplier: float = 1.0) -> float:
    """
    Calculate estimated cost for content generation.
    
    Args:
        tier_name: Quality tier name
        content_type: Type of content (video, audio, image, text)
        duration_minutes: Content duration in minutes
        complexity_multiplier: Complexity multiplier (0.5 - 3.0)
        
    Returns:
        Estimated cost in THB
    """
    if tier_name not in TIER_REGISTRY:
        raise ValueError(f"Unknown tier: {tier_name}")
    
    tier = TIER_REGISTRY[tier_name]
    base_cost = tier.base_cost
    
    # Content type multipliers
    type_multipliers = {
        'video': 1.0,
        'audio': 0.3,
        'image': 0.2,
        'text': 0.1
    }
    
    type_multiplier = type_multipliers.get(content_type, 1.0)
    duration_cost = max(duration_minutes / 5.0, 1.0)  # Minimum 1, increase every 5 minutes
    
    total_cost = base_cost * type_multiplier * duration_cost * complexity_multiplier
    
    return round(total_cost, 2)

def calculate_monthly_limits(tier_name: str) -> Dict[str, Any]:
    """
    Calculate monthly usage limits for a tier.
    
    Args:
        tier_name: Quality tier name
        
    Returns:
        Dictionary with monthly limits
    """
    if tier_name not in TIER_REGISTRY:
        raise ValueError(f"Unknown tier: {tier_name}")
    
    tier = TIER_REGISTRY[tier_name]
    daily_limit = tier.resource_limits['max_daily_generations']
    monthly_cost_limit = tier.resource_limits['max_monthly_cost']
    
    return {
        'max_content_items': daily_limit * 30,
        'max_video_hours': daily_limit * 30 * 0.1,  # Assume 6 min average
        'max_images': daily_limit * 30 * 5,  # Assume 5 images per content
        'max_cost_thb': monthly_cost_limit,
        'max_api_calls': tier.rate_limits['requests_per_day'] * 30
    }

def get_tier_comparison() -> Dict[str, Any]:
    """
    Get comparison of all tiers.
    
    Returns:
        Dictionary comparing all tiers
    """
    comparison = {
        'tiers': [],
        'features_matrix': {},
        'cost_comparison': {}
    }
    
    all_features = set()
    for tier in TIER_REGISTRY.values():
        all_features.update(tier.features.keys())
    
    for tier_name, tier in TIER_REGISTRY.items():
        # Basic tier info
        tier_info = {
            'name': tier.name,
            'display_name': tier.display_name,
            'base_cost': tier.base_cost,
            'max_concurrent': tier.resource_limits['max_concurrent_generations'],
            'daily_limit': tier.resource_limits['max_daily_generations']
        }
        comparison['tiers'].append(tier_info)
        
        # Features matrix
        comparison['features_matrix'][tier_name] = tier.features
        
        # Cost examples
        comparison['cost_comparison'][tier_name] = {
            'short_video': calculate_content_cost(tier_name, 'video', 1.0),
            'medium_video': calculate_content_cost(tier_name, 'video', 5.0),
            'long_video': calculate_content_cost(tier_name, 'video', 20.0),
            'image_set': calculate_content_cost(tier_name, 'image', 0.1) * 10,
            'audio_content': calculate_content_cost(tier_name, 'audio', 10.0)
        }
    
    return comparison

def validate_tier_config(tier_name: str) -> List[str]:
    """
    Validate tier configuration for completeness and consistency.
    
    Args:
        tier_name: Quality tier name
        
    Returns:
        List of validation issues
    """
    issues = []
    
    if tier_name not in TIER_REGISTRY:
        issues.append(f"Tier '{tier_name}' not found")
        return issues
    
    tier = TIER_REGISTRY[tier_name]
    
    # Check required AI services
    required_services = ['text_ai', 'image_ai', 'audio_ai']
    for service in required_services:
        if service not in tier.ai_services:
            issues.append(f"Missing {service} configuration for {tier_name}")
        else:
            service_config = tier.ai_services[service]
            if 'primary' not in service_config:
                issues.append(f"Missing primary service for {service} in {tier_name}")
    
    # Check cost consistency
    if tier.base_cost <= 0:
        issues.append(f"Base cost for {tier_name} must be positive")
    
    # Check resource limits
    limits = tier.resource_limits
    if limits['max_concurrent_generations'] <= 0:
        issues.append(f"Max concurrent generations for {tier_name} must be positive")
    
    if limits['max_daily_generations'] < limits['max_concurrent_generations']:
        issues.append(f"Daily limit should be >= concurrent limit for {tier_name}")
    
    return issues

def get_recommended_tier(requirements: Dict[str, Any]) -> str:
    """
    Recommend a tier based on user requirements.
    
    Args:
        requirements: Dictionary with user requirements
        
    Returns:
        Recommended tier name
    """
    daily_content = requirements.get('daily_content', 5)
    quality_priority = requirements.get('quality_priority', 'medium')  # low, medium, high
    budget_limit = requirements.get('monthly_budget_thb', 5000)
    feature_needs = requirements.get('features', [])
    
    scores = {}
    
    for tier_name, tier in TIER_REGISTRY.items():
        score = 0
        
        # Budget fit (higher score for staying within budget)
        monthly_estimate = tier.base_cost * daily_content * 30
        if monthly_estimate <= budget_limit:
            score += 30
        elif monthly_estimate <= budget_limit * 1.5:
            score += 15
        
        # Capacity fit
        if tier.resource_limits['max_daily_generations'] >= daily_content:
            score += 20
        
        # Quality priority
        quality_scores = {'budget': 5, 'balanced': 15, 'premium': 25}
        if quality_priority == 'low' and tier_name == 'budget':
            score += quality_scores[tier_name] + 10
        elif quality_priority == 'medium' and tier_name == 'balanced':
            score += quality_scores[tier_name] + 10
        elif quality_priority == 'high' and tier_name == 'premium':
            score += quality_scores[tier_name] + 10
        else:
            score += quality_scores.get(tier_name, 0)
        
        # Feature availability
        available_features = sum(1 for feature in feature_needs if tier.features.get(feature, False))
        feature_score = (available_features / len(feature_needs) * 15) if feature_needs else 15
        score += feature_score
        
        scores[tier_name] = score
    
    return max(scores, key=scores.get)

# Export main constants
__all__ = [
    'QUALITY_TIERS',
    'BASE_COSTS',
    'AI_SERVICE_CONFIGS',
    'QUALITY_METRICS',
    'CONTENT_SPECIFICATIONS',
    'PROCESSING_TIME_ESTIMATES',
    'RESOURCE_LIMITS',
    'API_RATE_LIMITS',
    'FEATURE_AVAILABILITY',
    'BUDGET_TIER',
    'BALANCED_TIER',
    'PREMIUM_TIER',
    'TIER_REGISTRY',
    'calculate_content_cost',
    'calculate_monthly_limits',
    'get_tier_comparison',
    'validate_tier_config',
    'get_recommended_tier'
]