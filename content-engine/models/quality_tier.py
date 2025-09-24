"""
Quality Tier System for AI Content Factory
Defines service tiers and their associated costs, features, and limitations

This module provides:
- Quality tier enumeration and configuration
- Service mapping for each tier
- Cost calculations and limits
- Feature availability matrix
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union
import json

class QualityTier(Enum):
    """
    Quality tiers for AI services
    Each tier offers different quality, features, and pricing
    """
    BUDGET = "budget"
    BALANCED = "balanced"
    PREMIUM = "premium"
    
    @classmethod
    def from_string(cls, tier_str: str) -> 'QualityTier':
        """
        Create QualityTier from string
        
        Args:
            tier_str: String representation of tier
            
        Returns:
            QualityTier enum value
        """
        tier_map = {
            "budget": cls.BUDGET,
            "balanced": cls.BALANCED,
            "premium": cls.PREMIUM,
            "free": cls.BUDGET,  # Alias
            "standard": cls.BALANCED,  # Alias
            "pro": cls.PREMIUM  # Alias
        }
        
        tier_lower = tier_str.lower().strip()
        if tier_lower in tier_map:
            return tier_map[tier_lower]
        else:
            raise ValueError(f"Invalid tier: {tier_str}. Valid options: {list(tier_map.keys())}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"QualityTier.{self.name}"

@dataclass
class ServiceLimits:
    """
    Limits for a specific service and tier
    """
    max_requests_per_hour: int
    max_requests_per_day: int
    max_content_length: int  # Characters for text, seconds for audio, pixels for images
    max_file_size_mb: float
    concurrent_requests: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "max_requests_per_hour": self.max_requests_per_hour,
            "max_requests_per_day": self.max_requests_per_day,
            "max_content_length": self.max_content_length,
            "max_file_size_mb": self.max_file_size_mb,
            "concurrent_requests": self.concurrent_requests
        }

@dataclass
class ServiceConfig:
    """
    Configuration for a specific service and tier
    """
    service_name: str
    tier: QualityTier
    cost_per_unit: float  # Cost per character/pixel/second
    currency: str = "THB"
    limits: ServiceLimits = None
    features: List[str] = None
    api_endpoint: str = None
    model_name: str = None
    quality_score: int = 5  # 1-10 scale
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.limits is None:
            self.limits = ServiceLimits(100, 1000, 10000, 10.0, 3)
    
    def estimate_cost(self, content_length: int) -> float:
        """
        Estimate cost for given content length
        
        Args:
            content_length: Length of content (characters/pixels/seconds)
            
        Returns:
            Estimated cost in the specified currency
        """
        return content_length * self.cost_per_unit
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "service_name": self.service_name,
            "tier": self.tier.value,
            "cost_per_unit": self.cost_per_unit,
            "currency": self.currency,
            "limits": self.limits.to_dict() if self.limits else None,
            "features": self.features,
            "api_endpoint": self.api_endpoint,
            "model_name": self.model_name,
            "quality_score": self.quality_score
        }

class TierManager:
    """
    Manages quality tiers and service configurations
    """
    
    def __init__(self):
        """Initialize with default service configurations"""
        self.service_configs: Dict[str, Dict[QualityTier, ServiceConfig]] = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default service configurations for all tiers"""
        
        # Text AI Services
        self.register_service_config("text_ai", QualityTier.BUDGET, ServiceConfig(
            service_name="groq",
            tier=QualityTier.BUDGET,
            cost_per_unit=0.0001,  # 0.1 satang per character
            limits=ServiceLimits(
                max_requests_per_hour=100,
                max_requests_per_day=1000,
                max_content_length=8000,
                max_file_size_mb=1.0,
                concurrent_requests=2
            ),
            features=["basic_completion", "fast_response"],
            model_name="llama3-8b-8192",
            quality_score=6
        ))
        
        self.register_service_config("text_ai", QualityTier.BALANCED, ServiceConfig(
            service_name="openai",
            tier=QualityTier.BALANCED,
            cost_per_unit=0.0008,  # 0.8 satang per character
            limits=ServiceLimits(
                max_requests_per_hour=500,
                max_requests_per_day=5000,
                max_content_length=16000,
                max_file_size_mb=5.0,
                concurrent_requests=5
            ),
            features=["advanced_completion", "function_calling", "json_mode"],
            model_name="gpt-3.5-turbo",
            quality_score=8
        ))
        
        self.register_service_config("text_ai", QualityTier.PREMIUM, ServiceConfig(
            service_name="claude",
            tier=QualityTier.PREMIUM,
            cost_per_unit=0.003,  # 3 satang per character
            limits=ServiceLimits(
                max_requests_per_hour=1000,
                max_requests_per_day=10000,
                max_content_length=100000,
                max_file_size_mb=20.0,
                concurrent_requests=10
            ),
            features=["premium_completion", "long_context", "advanced_reasoning"],
            model_name="claude-3-sonnet",
            quality_score=10
        ))
        
        # Audio AI Services
        self.register_service_config("audio_ai", QualityTier.BUDGET, ServiceConfig(
            service_name="gtts",
            tier=QualityTier.BUDGET,
            cost_per_unit=0.0,  # Free
            limits=ServiceLimits(
                max_requests_per_hour=50,
                max_requests_per_day=200,
                max_content_length=5000,
                max_file_size_mb=5.0,
                concurrent_requests=1
            ),
            features=["basic_tts", "multiple_languages"],
            model_name="google_tts",
            quality_score=5
        ))
        
        self.register_service_config("audio_ai", QualityTier.BALANCED, ServiceConfig(
            service_name="azure",
            tier=QualityTier.BALANCED,
            cost_per_unit=0.000016,  # 16 satang per 1000 characters
            limits=ServiceLimits(
                max_requests_per_hour=200,
                max_requests_per_day=2000,
                max_content_length=10000,
                max_file_size_mb=10.0,
                concurrent_requests=3
            ),
            features=["neural_voices", "ssml_support", "voice_styles"],
            model_name="azure_neural",
            quality_score=8
        ))
        
        self.register_service_config("audio_ai", QualityTier.PREMIUM, ServiceConfig(
            service_name="elevenlabs",
            tier=QualityTier.PREMIUM,
            cost_per_unit=0.0003,  # 30 satang per 1000 characters
            limits=ServiceLimits(
                max_requests_per_hour=500,
                max_requests_per_day=5000,
                max_content_length=100000,
                max_file_size_mb=50.0,
                concurrent_requests=5
            ),
            features=["ai_voices", "emotional_control", "voice_cloning", "premium_quality"],
            model_name="eleven_multilingual_v2",
            quality_score=10
        ))
        
        # Image AI Services
        self.register_service_config("image_ai", QualityTier.BUDGET, ServiceConfig(
            service_name="stable_diffusion",
            tier=QualityTier.BUDGET,
            cost_per_unit=0.01,  # 1 satang per image
            limits=ServiceLimits(
                max_requests_per_hour=30,
                max_requests_per_day=100,
                max_content_length=512,  # Max resolution
                max_file_size_mb=2.0,
                concurrent_requests=1
            ),
            features=["basic_generation", "local_processing"],
            model_name="stable_diffusion_1_5",
            quality_score=6
        ))
        
        self.register_service_config("image_ai", QualityTier.BALANCED, ServiceConfig(
            service_name="leonardo",
            tier=QualityTier.BALANCED,
            cost_per_unit=0.05,  # 5 satang per image
            limits=ServiceLimits(
                max_requests_per_hour=100,
                max_requests_per_day=500,
                max_content_length=1024,  # Max resolution
                max_file_size_mb=10.0,
                concurrent_requests=3
            ),
            features=["high_quality", "style_presets", "fast_generation"],
            model_name="leonardo_creative",
            quality_score=8
        ))
        
        self.register_service_config("image_ai", QualityTier.PREMIUM, ServiceConfig(
            service_name="midjourney",
            tier=QualityTier.PREMIUM,
            cost_per_unit=0.20,  # 20 satang per image
            limits=ServiceLimits(
                max_requests_per_hour=200,
                max_requests_per_day=1000,
                max_content_length=2048,  # Max resolution
                max_file_size_mb=25.0,
                concurrent_requests=5
            ),
            features=["premium_quality", "artistic_styles", "upscaling", "variations"],
            model_name="midjourney_v6",
            quality_score=10
        ))
    
    def register_service_config(
        self, 
        service_type: str, 
        tier: QualityTier, 
        config: ServiceConfig
    ):
        """
        Register a service configuration
        
        Args:
            service_type: Type of service (text_ai, audio_ai, image_ai)
            tier: Quality tier
            config: Service configuration
        """
        if service_type not in self.service_configs:
            self.service_configs[service_type] = {}
        
        self.service_configs[service_type][tier] = config
    
    def get_service_config(
        self, 
        service_type: str, 
        tier: Union[QualityTier, str]
    ) -> Optional[ServiceConfig]:
        """
        Get service configuration for specific type and tier
        
        Args:
            service_type: Type of service
            tier: Quality tier
            
        Returns:
            ServiceConfig or None if not found
        """
        if isinstance(tier, str):
            tier = QualityTier.from_string(tier)
        
        return self.service_configs.get(service_type, {}).get(tier)
    
    def get_all_configs_for_service(self, service_type: str) -> Dict[QualityTier, ServiceConfig]:
        """
        Get all configurations for a service type
        
        Args:
            service_type: Type of service
            
        Returns:
            Dictionary of tier to config mappings
        """
        return self.service_configs.get(service_type, {})
    
    def get_available_tiers(self, service_type: str) -> List[QualityTier]:
        """
        Get available tiers for a service type
        
        Args:
            service_type: Type of service
            
        Returns:
            List of available tiers
        """
        return list(self.service_configs.get(service_type, {}).keys())
    
    def estimate_total_cost(
        self, 
        requests: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Estimate total cost for multiple requests
        
        Args:
            requests: List of request dictionaries with keys:
                     - service_type: str
                     - tier: str or QualityTier
                     - content_length: int
                     
        Returns:
            Dictionary with cost breakdown
        """
        total_cost = 0.0
        cost_breakdown = {}
        
        for request in requests:
            service_type = request["service_type"]
            tier = request["tier"]
            content_length = request["content_length"]
            
            config = self.get_service_config(service_type, tier)
            if config:
                cost = config.estimate_cost(content_length)
                total_cost += cost
                
                key = f"{service_type}_{tier}"
                if key not in cost_breakdown:
                    cost_breakdown[key] = 0.0
                cost_breakdown[key] += cost
        
        cost_breakdown["total"] = total_cost
        return cost_breakdown
    
    def get_tier_comparison(self, service_type: str) -> Dict[str, Any]:
        """
        Get comparison of all tiers for a service type
        
        Args:
            service_type: Type of service
            
        Returns:
            Comparison data
        """
        configs = self.get_all_configs_for_service(service_type)
        comparison = {
            "service_type": service_type,
            "tiers": {}
        }
        
        for tier, config in configs.items():
            comparison["tiers"][tier.value] = {
                "service_name": config.service_name,
                "cost_per_unit": config.cost_per_unit,
                "quality_score": config.quality_score,
                "features": config.features,
                "limits": config.limits.to_dict(),
                "model_name": config.model_name
            }
        
        return comparison
    
    def recommend_tier(
        self, 
        service_type: str, 
        budget_limit: float = None,
        quality_requirement: int = None,
        feature_requirements: List[str] = None
    ) -> Optional[QualityTier]:
        """
        Recommend best tier based on requirements
        
        Args:
            service_type: Type of service
            budget_limit: Maximum cost per unit (optional)
            quality_requirement: Minimum quality score 1-10 (optional)
            feature_requirements: Required features (optional)
            
        Returns:
            Recommended tier or None
        """
        configs = self.get_all_configs_for_service(service_type)
        suitable_tiers = []
        
        for tier, config in configs.items():
            # Check budget
            if budget_limit and config.cost_per_unit > budget_limit:
                continue
            
            # Check quality
            if quality_requirement and config.quality_score < quality_requirement:
                continue
            
            # Check features
            if feature_requirements:
                if not all(feature in config.features for feature in feature_requirements):
                    continue
            
            suitable_tiers.append((tier, config))
        
        if not suitable_tiers:
            return None
        
        # Return the best quality tier that meets requirements
        suitable_tiers.sort(key=lambda x: x[1].quality_score, reverse=True)
        return suitable_tiers[0][0]
    
    def export_config(self, filename: str = None) -> str:
        """
        Export all configurations to JSON
        
        Args:
            filename: Optional filename to save to
            
        Returns:
            JSON string of configurations
        """
        export_data = {}
        
        for service_type, tiers in self.service_configs.items():
            export_data[service_type] = {}
            for tier, config in tiers.items():
                export_data[service_type][tier.value] = config.to_dict()
        
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def load_config(self, json_data: Union[str, Dict[str, Any]]):
        """
        Load configurations from JSON data
        
        Args:
            json_data: JSON string or dictionary
        """
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        for service_type, tiers in data.items():
            for tier_str, config_dict in tiers.items():
                tier = QualityTier.from_string(tier_str)
                
                limits = ServiceLimits(**config_dict["limits"]) if config_dict.get("limits") else None
                
                config = ServiceConfig(
                    service_name=config_dict["service_name"],
                    tier=tier,
                    cost_per_unit=config_dict["cost_per_unit"],
                    currency=config_dict.get("currency", "THB"),
                    limits=limits,
                    features=config_dict.get("features", []),
                    api_endpoint=config_dict.get("api_endpoint"),
                    model_name=config_dict.get("model_name"),
                    quality_score=config_dict.get("quality_score", 5)
                )
                
                self.register_service_config(service_type, tier, config)

# Global tier manager instance
tier_manager = TierManager()

# Convenience functions
def get_service_config(service_type: str, tier: Union[QualityTier, str]) -> Optional[ServiceConfig]:
    """Get service configuration"""
    return tier_manager.get_service_config(service_type, tier)

def estimate_cost(service_type: str, tier: Union[QualityTier, str], content_length: int) -> float:
    """Estimate cost for service usage"""
    config = get_service_config(service_type, tier)
    return config.estimate_cost(content_length) if config else 0.0

def get_available_tiers(service_type: str) -> List[QualityTier]:
    """Get available tiers for service"""
    return tier_manager.get_available_tiers(service_type)

def recommend_tier(
    service_type: str, 
    budget_limit: float = None,
    quality_requirement: int = None,
    feature_requirements: List[str] = None
) -> Optional[QualityTier]:
    """Recommend best tier for requirements"""
    return tier_manager.recommend_tier(service_type, budget_limit, quality_requirement, feature_requirements)