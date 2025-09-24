"""
AI Content Factory - Shared Base Model
====================================

Base model classes and utilities shared across all services.
These models provide common functionality and data validation.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel as PydanticBaseModel, Field, validator
import json


class StatusEnum(str, Enum):
    """Common status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PriorityEnum(str, Enum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class QualityTierEnum(str, Enum):
    """Quality tier levels."""
    BUDGET = "budget"
    BALANCED = "balanced"
    PREMIUM = "premium"


@dataclass
class BaseDataClass:
    """
    Base dataclass with common functionality.
    
    Provides JSON serialization, validation, and common fields
    for all dataclass models in the system.
    """
    
    id: Optional[Union[UUID, str]] = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        
        # Convert UUID and datetime to strings for JSON serialization
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
                
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary."""
        # Convert string IDs back to UUID if needed
        if 'id' in data and isinstance(data['id'], str):
            try:
                data['id'] = UUID(data['id'])
            except ValueError:
                pass  # Keep as string if not valid UUID
                
        # Convert ISO datetime strings back to datetime objects
        for field_name in ['created_at', 'updated_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except ValueError:
                    pass  # Keep as string if not valid datetime
                    
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()


class BasePydanticModel(PydanticBaseModel):
    """
    Base Pydantic model with common functionality.
    
    Provides validation, serialization, and common fields
    for all Pydantic models in the system.
    """
    
    id: Optional[Union[UUID, str]] = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
    
    @validator('id', pre=True, always=True)
    def validate_id(cls, v):
        """Validate and convert ID field."""
        if v is None:
            return uuid4()
        if isinstance(v, str):
            try:
                return UUID(v)
            except ValueError:
                return v  # Keep as string if not valid UUID
        return v
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        return self.dict(by_alias=True)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.json(by_alias=True)
    
    @classmethod
    def from_orm_dict(cls, data: Dict[str, Any]):
        """Create instance from ORM dictionary."""
        return cls(**data)


@dataclass
class MetricsData(BaseDataClass):
    """Base class for metrics and analytics data."""
    
    value: float
    metric_type: str
    unit: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_tag(self, key: str, value: str):
        """Add a tag to the metrics."""
        self.tags[key] = value
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata value."""
        self.metadata[key] = value


@dataclass 
class ErrorInfo(BaseDataClass):
    """Error information container."""
    
    error_type: str
    message: str
    code: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    traceback: Optional[str] = None
    
    def to_exception(self) -> Exception:
        """Convert to exception object."""
        exception_class = globals().get(self.error_type, Exception)
        return exception_class(self.message)


@dataclass
class ValidationResult(BaseDataClass):
    """Validation result container."""
    
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are validation warnings."""
        return len(self.warnings) > 0


class BaseAPIResponse(BasePydanticModel):
    """Base API response model."""
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def add_error(self, error: str):
        """Add error to response."""
        self.errors.append(error)
        self.success = False
    
    def set_data(self, data: Any):
        """Set response data."""
        self.data = data
    
    def set_message(self, message: str):
        """Set response message."""
        self.message = message


class BaseAPIRequest(BasePydanticModel):
    """Base API request model."""
    
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class ConfigurationData(BaseDataClass):
    """Base configuration data container."""
    
    name: str
    version: str = "1.0.0"
    environment: str = "development"
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set configuration setting."""
        self.settings[key] = value
        self.update_timestamp()
    
    def merge_settings(self, settings: Dict[str, Any]):
        """Merge additional settings."""
        self.settings.update(settings)
        self.update_timestamp()


# Utility functions for model operations

def serialize_model(model: Union[BaseDataClass, BasePydanticModel]) -> Dict[str, Any]:
    """
    Serialize any base model to dictionary.
    
    Args:
        model: Model instance to serialize
        
    Returns:
        Dictionary representation
    """
    if isinstance(model, BaseDataClass):
        return model.to_dict()
    elif isinstance(model, BasePydanticModel):
        return model.to_dict()
    else:
        raise TypeError(f"Unsupported model type: {type(model)}")


def deserialize_model(model_class: type, data: Dict[str, Any]):
    """
    Deserialize dictionary to model instance.
    
    Args:
        model_class: Target model class
        data: Dictionary data
        
    Returns:
        Model instance
    """
    if issubclass(model_class, BaseDataClass):
        return model_class.from_dict(data)
    elif issubclass(model_class, BasePydanticModel):
        return model_class(**data)
    else:
        raise TypeError(f"Unsupported model class: {model_class}")


def validate_model_data(model_class: type, data: Dict[str, Any]) -> ValidationResult:
    """
    Validate data against model schema.
    
    Args:
        model_class: Model class to validate against
        data: Data to validate
        
    Returns:
        ValidationResult instance
    """
    result = ValidationResult()
    
    try:
        if issubclass(model_class, BasePydanticModel):
            # Use Pydantic validation
            model_class(**data)
            result.is_valid = True
        else:
            # Basic validation for dataclasses
            instance = deserialize_model(model_class, data)
            result.is_valid = True
            
    except Exception as e:
        result.add_error(str(e))
    
    return result


# Common field validators

def validate_uuid(value: Union[str, UUID]) -> UUID:
    """Validate UUID field."""
    if isinstance(value, UUID):
        return value
    try:
        return UUID(value)
    except ValueError:
        raise ValueError(f"Invalid UUID: {value}")


def validate_positive_number(value: Union[int, float]) -> Union[int, float]:
    """Validate positive number."""
    if value <= 0:
        raise ValueError("Value must be positive")
    return value


def validate_non_empty_string(value: str) -> str:
    """Validate non-empty string."""
    if not value or not value.strip():
        raise ValueError("String cannot be empty")
    return value.strip()


def validate_url(value: str) -> str:
    """Validate URL format."""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(value):
        raise ValueError(f"Invalid URL: {value}")
    return value


# Model registry for dynamic model creation
MODEL_REGISTRY: Dict[str, type] = {}

def register_model(name: str, model_class: type):
    """Register model class in global registry."""
    MODEL_REGISTRY[name] = model_class

def get_registered_model(name: str) -> Optional[type]:
    """Get registered model class by name."""
    return MODEL_REGISTRY.get(name)

def list_registered_models() -> List[str]:
    """List all registered model names."""
    return list(MODEL_REGISTRY.keys())