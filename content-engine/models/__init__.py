"""
Models Package for AI Content Factory
Contains all data models and configurations for the content engine

This package includes:
- Quality tier management
- Content plan models
- Content opportunity models
- Database models (when implemented)
- Configuration models
"""

# Import core models
from .quality_tier import (
    QualityTier,
    ServiceConfig,
    ServiceLimits,
    TierManager,
    tier_manager,
    get_service_config,
    estimate_cost,
    get_available_tiers,
    recommend_tier
)

# Import shared models from the shared package
try:
    from ..shared.models.content_plan import (
        ContentPlan,
        ScriptPlan,
        VisualPlan,
        AudioPlan,
        PlatformOptimization,
        ProductionEstimate
    )
except ImportError:
    # Models not yet created
    ContentPlan = None
    ScriptPlan = None
    VisualPlan = None
    AudioPlan = None
    PlatformOptimization = None
    ProductionEstimate = None

try:
    from .content_opportunity import (
        ContentOpportunity,
        OpportunityStatus,
        OpportunityPriority
    )
except ImportError:
    # Model not yet created
    ContentOpportunity = None
    OpportunityStatus = None
    OpportunityPriority = None

# Model registry for dynamic loading
MODEL_REGISTRY = {}

def register_model(name: str, model_class: type):
    """
    Register a model class in the registry
    
    Args:
        name: Model name
        model_class: Model class
    """
    MODEL_REGISTRY[name] = model_class

def get_model(name: str) -> type:
    """
    Get a model class from the registry
    
    Args:
        name: Model name
        
    Returns:
        Model class or None if not found
    """
    return MODEL_REGISTRY.get(name)

def list_models() -> list:
    """
    Get list of all registered model names
    
    Returns:
        List of model names
    """
    return list(MODEL_REGISTRY.keys())

# Register available models
if QualityTier:
    register_model("QualityTier", QualityTier)
if ServiceConfig:
    register_model("ServiceConfig", ServiceConfig)
if ServiceLimits:
    register_model("ServiceLimits", ServiceLimits)
if TierManager:
    register_model("TierManager", TierManager)

if ContentPlan:
    register_model("ContentPlan", ContentPlan)
if ScriptPlan:
    register_model("ScriptPlan", ScriptPlan)
if VisualPlan:
    register_model("VisualPlan", VisualPlan)
if AudioPlan:
    register_model("AudioPlan", AudioPlan)
if PlatformOptimization:
    register_model("PlatformOptimization", PlatformOptimization)
if ProductionEstimate:
    register_model("ProductionEstimate", ProductionEstimate)

if ContentOpportunity:
    register_model("ContentOpportunity", ContentOpportunity)
if OpportunityStatus:
    register_model("OpportunityStatus", OpportunityStatus)
if OpportunityPriority:
    register_model("OpportunityPriority", OpportunityPriority)

# Quality tier shortcuts for easy access
BUDGET = QualityTier.BUDGET
BALANCED = QualityTier.BALANCED  
PREMIUM = QualityTier.PREMIUM

# Service type constants
SERVICE_TYPES = {
    "TEXT_AI": "text_ai",
    "AUDIO_AI": "audio_ai", 
    "IMAGE_AI": "image_ai",
    "VIDEO_AI": "video_ai"
}

# Default configurations
DEFAULT_TIER = QualityTier.BUDGET
DEFAULT_CURRENCY = "THB"

# Validation functions
def validate_tier(tier) -> bool:
    """
    Validate if tier is a valid QualityTier
    
    Args:
        tier: Tier to validate
        
    Returns:
        True if valid
    """
    if isinstance(tier, QualityTier):
        return True
    if isinstance(tier, str):
        try:
            QualityTier.from_string(tier)
            return True
        except ValueError:
            return False
    return False

def validate_service_type(service_type: str) -> bool:
    """
    Validate if service type is supported
    
    Args:
        service_type: Service type to validate
        
    Returns:
        True if valid
    """
    return service_type in SERVICE_TYPES.values()

# Helper functions for model creation
def create_service_config(
    service_name: str,
    tier: str,
    cost_per_unit: float,
    **kwargs
) -> ServiceConfig:
    """
    Create a ServiceConfig with validation
    
    Args:
        service_name: Name of the service
        tier: Quality tier (string)
        cost_per_unit: Cost per unit
        **kwargs: Additional configuration
        
    Returns:
        ServiceConfig instance
    """
    tier_enum = QualityTier.from_string(tier)
    
    return ServiceConfig(
        service_name=service_name,
        tier=tier_enum,
        cost_per_unit=cost_per_unit,
        **kwargs
    )

def create_service_limits(
    max_requests_per_hour: int = 100,
    max_requests_per_day: int = 1000,
    max_content_length: int = 10000,
    max_file_size_mb: float = 10.0,
    concurrent_requests: int = 3
) -> ServiceLimits:
    """
    Create ServiceLimits with defaults
    
    Args:
        max_requests_per_hour: Hourly request limit
        max_requests_per_day: Daily request limit
        max_content_length: Max content length
        max_file_size_mb: Max file size in MB
        concurrent_requests: Max concurrent requests
        
    Returns:
        ServiceLimits instance
    """
    return ServiceLimits(
        max_requests_per_hour=max_requests_per_hour,
        max_requests_per_day=max_requests_per_day,
        max_content_length=max_content_length,
        max_file_size_mb=max_file_size_mb,
        concurrent_requests=concurrent_requests
    )

# Cost calculation utilities
def calculate_content_cost(
    content_requests: list,
    tier: str = "budget"
) -> dict:
    """
    Calculate total cost for multiple content requests
    
    Args:
        content_requests: List of content requests
        tier: Quality tier to use
        
    Returns:
        Cost breakdown dictionary
    """
    total_cost = 0.0
    breakdown = {}
    
    for request in content_requests:
        service_type = request.get("service_type")
        content_length = request.get("content_length", 0)
        
        if service_type and content_length > 0:
            cost = estimate_cost(service_type, tier, content_length)
            total_cost += cost
            
            if service_type not in breakdown:
                breakdown[service_type] = 0.0
            breakdown[service_type] += cost
    
    breakdown["total"] = total_cost
    breakdown["currency"] = DEFAULT_CURRENCY
    
    return breakdown

def get_tier_recommendations(
    service_type: str,
    requirements: dict = None
) -> dict:
    """
    Get tier recommendations for a service type
    
    Args:
        service_type: Type of service
        requirements: Requirements dictionary with optional keys:
                     - budget_limit: float
                     - quality_requirement: int
                     - feature_requirements: list
        
    Returns:
        Recommendations dictionary
    """
    if not requirements:
        requirements = {}
    
    recommended_tier = recommend_tier(
        service_type=service_type,
        budget_limit=requirements.get("budget_limit"),
        quality_requirement=requirements.get("quality_requirement"),
        feature_requirements=requirements.get("feature_requirements", [])
    )
    
    comparison = tier_manager.get_tier_comparison(service_type)
    
    return {
        "recommended_tier": recommended_tier.value if recommended_tier else None,
        "all_tiers": comparison["tiers"],
        "service_type": service_type,
        "requirements": requirements
    }

# Model validation
def validate_models():
    """
    Validate that all critical models are available
    
    Returns:
        Dictionary with validation results
    """
    critical_models = ["QualityTier", "ServiceConfig", "ServiceLimits", "TierManager"]
    optional_models = ["ContentPlan", "ContentOpportunity"]
    
    results = {
        "critical_missing": [],
        "optional_missing": [],
        "available": [],
        "total_registered": len(MODEL_REGISTRY)
    }
    
    # Check critical models
    for model_name in critical_models:
        if model_name in MODEL_REGISTRY:
            results["available"].append(model_name)
        else:
            results["critical_missing"].append(model_name)
    
    # Check optional models
    for model_name in optional_models:
        if model_name not in MODEL_REGISTRY:
            results["optional_missing"].append(model_name)
        else:
            results["available"].append(model_name)
    
    results["is_valid"] = len(results["critical_missing"]) == 0
    
    return results

# Package information
__version__ = "1.0.0"
__author__ = "AI Content Factory Team"
__description__ = "Data models and configurations for AI Content Factory"

# Package exports
__all__ = [
    # Core models
    "QualityTier",
    "ServiceConfig", 
    "ServiceLimits",
    "TierManager",
    "tier_manager",
    
    # Content models (when available)
    "ContentPlan",
    "ScriptPlan",
    "VisualPlan", 
    "AudioPlan",
    "PlatformOptimization",
    "ProductionEstimate",
    "ContentOpportunity",
    "OpportunityStatus",
    "OpportunityPriority",
    
    # Utility functions
    "get_service_config",
    "estimate_cost",
    "get_available_tiers",
    "recommend_tier",
    "register_model",
    "get_model",
    "list_models",
    "validate_tier",
    "validate_service_type",
    "create_service_config",
    "create_service_limits",
    "calculate_content_cost",
    "get_tier_recommendations",
    "validate_models",
    
    # Constants
    "BUDGET",
    "BALANCED", 
    "PREMIUM",
    "SERVICE_TYPES",
    "DEFAULT_TIER",
    "DEFAULT_CURRENCY",
    
    # Registry
    "MODEL_REGISTRY"
]

# Initialize validation on import
_validation_results = validate_models()
if not _validation_results["is_valid"]:
    import warnings
    warnings.warn(
        f"Critical models missing: {_validation_results['critical_missing']}",
        ImportWarning
    )