"""
Application Configuration Management
ตำแหน่งไฟล์: config/app_config.py

จัดการ configuration ทั้งหมดของระบบ AI Content Factory
รองรับ multiple environments และ dynamic configuration loading
"""
import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import logging
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class QualityTier(Enum):
    """Quality tiers for content generation"""
    BUDGET = "budget"
    BALANCED = "balanced"
    PREMIUM = "premium"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: str = "sqlite"
    host: Optional[str] = "localhost"
    port: Optional[int] = 5432
    name: str = "content_factory"
    user: Optional[str] = "admin"
    password: Optional[str] = None
    path: Optional[str] = "data/content_factory.db"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    
    @property
    def url(self) -> str:
        """Generate database URL"""
        if self.type == "sqlite":
            return f"sqlite:///{self.path}"
        elif self.type == "postgresql":
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")

@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    url: Optional[str] = None
    
    @property
    def connection_url(self) -> str:
        """Generate Redis connection URL"""
        if self.url:
            return self.url
        
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

@dataclass
class AIServiceConfig:
    """AI service configuration"""
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_org_id: Optional[str] = None
    openai_model: str = "gpt-4"
    
    # Groq
    groq_api_key: Optional[str] = None
    groq_model: str = "mixtral-8x7b-32768"
    
    # Anthropic Claude
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-sonnet-20240229"
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2023-12-01-preview"
    
    # Default quality tier
    default_quality_tier: QualityTier = QualityTier.BALANCED
    
    # API timeouts
    api_timeout: int = 120
    max_retries: int = 3

@dataclass
class TTSConfig:
    """Text-to-Speech configuration"""
    # ElevenLabs
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    
    # Azure TTS
    azure_speech_key: Optional[str] = None
    azure_speech_region: str = "eastus"
    
    # Google TTS
    google_tts_key_file: Optional[str] = None

@dataclass
class ImageGenConfig:
    """Image generation configuration"""
    # Stable Diffusion
    stable_diffusion_api_key: Optional[str] = None
    stable_diffusion_engine: str = "stable-diffusion-xl-1024-v1-0"
    
    # Leonardo AI
    leonardo_api_key: Optional[str] = None
    
    # Midjourney
    midjourney_api_key: Optional[str] = None
    midjourney_server_id: Optional[str] = None
    midjourney_channel_id: Optional[str] = None

@dataclass
class PlatformConfig:
    """Social media platform configuration"""
    # YouTube
    youtube_api_key: Optional[str] = None
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None
    
    # TikTok
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    tiktok_access_token: Optional[str] = None
    
    # Instagram
    instagram_client_id: Optional[str] = None
    instagram_client_secret: Optional[str] = None
    instagram_access_token: Optional[str] = None
    
    # Facebook
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    facebook_access_token: Optional[str] = None
    facebook_page_id: Optional[str] = None
    
    # Twitter
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None

@dataclass
class TrendCollectionConfig:
    """Trend collection configuration"""
    # Google Trends
    google_trends_proxy: Optional[str] = None
    
    # Reddit
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "AIContentFactory/1.0"
    
    # News APIs
    news_api_key: Optional[str] = None
    bing_news_api_key: Optional[str] = None
    
    # Collection settings
    max_trends_per_source: int = 50
    collection_interval_hours: int = 6
    trend_retention_days: int = 30

@dataclass
class StorageConfig:
    """File storage configuration"""
    # Local storage
    upload_folder: str = "data/uploads"
    generated_content_path: str = "data/generated"
    temp_files_path: str = "data/temp"
    max_content_length: int = 16777216  # 16MB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        'mp4', 'mov', 'avi', 'mp3', 'wav', 'jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt'
    ])
    
    # Cloud storage
    use_cloud_storage: bool = False
    
    # AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_default_region: str = "us-west-2"
    aws_s3_bucket: Optional[str] = None
    
    # Google Cloud
    google_cloud_project_id: Optional[str] = None
    google_cloud_storage_bucket: Optional[str] = None
    google_application_credentials: Optional[str] = None
    
    # Azure
    azure_storage_account_name: Optional[str] = None
    azure_storage_account_key: Optional[str] = None
    azure_storage_container_name: Optional[str] = None

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = "dev-secret-key-change-in-production"
    
    # JWT
    jwt_secret_key: Optional[str] = None
    jwt_access_token_expires: int = 3600  # 1 hour
    jwt_refresh_token_expires: int = 2592000  # 30 days
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "1000 per hour"
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000", "http://localhost:8080"
    ])

@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5
    log_format: str = "json"
    
    # Sentry
    sentry_dsn: Optional[str] = None
    
    # Prometheus
    prometheus_metrics_enabled: bool = True
    prometheus_metrics_port: int = 8000
    
    # Health checks
    health_check_enabled: bool = True

@dataclass
class ContentGenerationConfig:
    """Content generation settings"""
    # Limits
    max_daily_content: int = 50
    max_concurrent_generation: int = 5
    
    # Default settings
    default_quality_tier: QualityTier = QualityTier.BALANCED
    
    # Model preferences
    preferred_text_model: str = "gpt-4"
    preferred_image_model: str = "dall-e-3"
    preferred_voice_model: str = "elevenlabs"
    
    # Generation timeouts
    generation_timeout: int = 300  # 5 minutes
    ai_api_timeout: int = 120  # 2 minutes

@dataclass
class FeatureFlagsConfig:
    """Feature flags configuration"""
    # Core features
    trend_collection: bool = True
    ai_generation: bool = True
    social_upload: bool = True
    analytics: bool = True
    user_management: bool = False
    
    # Beta features
    video_generation: bool = False
    voice_cloning: bool = False
    auto_scheduling: bool = False
    
    # Experimental features
    multi_language: bool = False
    advanced_analytics: bool = False

class AppConfig:
    """Main application configuration class"""
    
    def __init__(self, env: Optional[Environment] = None):
        self.env = env or self._detect_environment()
        self.config_dir = Path(__file__).parent
        self.root_dir = self.config_dir.parent
        
        # Initialize all configurations
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.ai_services = AIServiceConfig()
        self.tts = TTSConfig()
        self.image_gen = ImageGenConfig()
        self.platforms = PlatformConfig()
        self.trend_collection = TrendCollectionConfig()
        self.storage = StorageConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.content_generation = ContentGenerationConfig()
        self.feature_flags = FeatureFlagsConfig()
        
        # Load configuration
        self._load_config()
    
    def _detect_environment(self) -> Environment:
        """Detect current environment"""
        env_str = os.getenv('FLASK_ENV', 'development').lower()
        try:
            return Environment(env_str)
        except ValueError:
            logger.warning(f"Unknown environment '{env_str}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_config(self):
        """Load configuration from various sources"""
        # 1. Load from YAML files
        self._load_yaml_config()
        
        # 2. Load from environment variables
        self._load_env_config()
        
        # 3. Validate configuration
        self._validate_config()
        
        # 4. Create necessary directories
        self._create_directories()
    
    def _load_yaml_config(self):
        """Load configuration from YAML files"""
        config_files = [
            self.config_dir / "app_config.yaml",
            self.config_dir / f"{self.env.value}.yaml",
            self.config_dir / "local.yaml"  # Local overrides
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                        self._apply_config_data(config_data)
                        logger.info(f"Loaded config from {config_file}")
                except Exception as e:
                    logger.error(f"Error loading config from {config_file}: {e}")
    
    def _load_env_config(self):
        """Load configuration from environment variables"""
        # Database
        if os.getenv('DB_TYPE'):
            self.database.type = os.getenv('DB_TYPE')
        if os.getenv('DB_HOST'):
            self.database.host = os.getenv('DB_HOST')
        if os.getenv('DB_PORT'):
            self.database.port = int(os.getenv('DB_PORT'))
        if os.getenv('DB_NAME'):
            self.database.name = os.getenv('DB_NAME')
        if os.getenv('DB_USER'):
            self.database.user = os.getenv('DB_USER')
        if os.getenv('DB_PASSWORD'):
            self.database.password = os.getenv('DB_PASSWORD')
        if os.getenv('DB_PATH'):
            self.database.path = os.getenv('DB_PATH')
        
        # Redis
        if os.getenv('REDIS_URL'):
            self.redis.url = os.getenv('REDIS_URL')
        if os.getenv('REDIS_HOST'):
            self.redis.host = os.getenv('REDIS_HOST')
        if os.getenv('REDIS_PORT'):
            self.redis.port = int(os.getenv('REDIS_PORT'))
        if os.getenv('REDIS_PASSWORD'):
            self.redis.password = os.getenv('REDIS_PASSWORD')
        
        # AI Services
        if os.getenv('OPENAI_API_KEY'):
            self.ai_services.openai_api_key = os.getenv('OPENAI_API_KEY')
        if os.getenv('GROQ_API_KEY'):
            self.ai_services.groq_api_key = os.getenv('GROQ_API_KEY')
        if os.getenv('ANTHROPIC_API_KEY'):
            self.ai_services.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # TTS
        if os.getenv('ELEVENLABS_API_KEY'):
            self.tts.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        if os.getenv('AZURE_SPEECH_KEY'):
            self.tts.azure_speech_key = os.getenv('AZURE_SPEECH_KEY')
        
        # Image Generation
        if os.getenv('STABLE_DIFFUSION_API_KEY'):
            self.image_gen.stable_diffusion_api_key = os.getenv('STABLE_DIFFUSION_API_KEY')
        if os.getenv('LEONARDO_AI_API_KEY'):
            self.image_gen.leonardo_api_key = os.getenv('LEONARDO_AI_API_KEY')
        
        # Platforms
        if os.getenv('YOUTUBE_API_KEY'):
            self.platforms.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        if os.getenv('TIKTOK_CLIENT_KEY'):
            self.platforms.tiktok_client_key = os.getenv('TIKTOK_CLIENT_KEY')
        
        # Security
        if os.getenv('SECRET_KEY'):
            self.security.secret_key = os.getenv('SECRET_KEY')
        
        # Monitoring
        if os.getenv('LOG_LEVEL'):
            self.monitoring.log_level = os.getenv('LOG_LEVEL')
        if os.getenv('SENTRY_DSN'):
            self.monitoring.sentry_dsn = os.getenv('SENTRY_DSN')
        
        # Feature Flags
        if os.getenv('FEATURE_TREND_COLLECTION'):
            self.feature_flags.trend_collection = os.getenv('FEATURE_TREND_COLLECTION').lower() == 'true'
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data from YAML"""
        if not config_data:
            return
        
        # Database config
        if 'database' in config_data:
            db_config = config_data['database']
            for key, value in db_config.items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
        
        # Redis config
        if 'redis' in config_data:
            redis_config = config_data['redis']
            for key, value in redis_config.items():
                if hasattr(self.redis, key):
                    setattr(self.redis, key, value)
        
        # AI services config
        if 'ai_services' in config_data:
            ai_config = config_data['ai_services']
            for key, value in ai_config.items():
                if hasattr(self.ai_services, key):
                    setattr(self.ai_services, key, value)
        
        # Apply other configurations similarly...
    
    def _validate_config(self):
        """Validate configuration"""
        errors = []
        
        # Validate required settings for production
        if self.env == Environment.PRODUCTION:
            if self.security.secret_key == "dev-secret-key-change-in-production":
                errors.append("SECRET_KEY must be changed in production")
            
            if self.database.type == "sqlite":
                logger.warning("Using SQLite in production is not recommended")
            
            if not self.ai_services.openai_api_key and not self.ai_services.groq_api_key:
                errors.append("At least one AI service API key must be configured")
        
        # Validate database configuration
        if self.database.type == "postgresql":
            if not all([self.database.host, self.database.user, self.database.password]):
                errors.append("PostgreSQL requires host, user, and password")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.storage.upload_folder,
            self.storage.generated_content_path,
            self.storage.temp_files_path,
            os.path.dirname(self.monitoring.log_file),
        ]
        
        for directory in directories:
            if directory:
                os.makedirs(directory, exist_ok=True)
    
    def get_ai_service_config(self, quality_tier: QualityTier) -> Dict[str, Any]:
        """Get AI service configuration for quality tier"""
        if quality_tier == QualityTier.BUDGET:
            return {
                'text_service': 'groq',
                'image_service': 'stable_diffusion',
                'tts_service': 'gtts',
                'api_key': self.ai_services.groq_api_key,
                'model': self.ai_services.groq_model
            }
        elif quality_tier == QualityTier.BALANCED:
            return {
                'text_service': 'openai',
                'image_service': 'leonardo',
                'tts_service': 'azure',
                'api_key': self.ai_services.openai_api_key,
                'model': self.ai_services.openai_model
            }
        else:  # PREMIUM
            return {
                'text_service': 'anthropic',
                'image_service': 'midjourney',
                'tts_service': 'elevenlabs',
                'api_key': self.ai_services.anthropic_api_key,
                'model': self.ai_services.anthropic_model
            }
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        platform_configs = {
            'youtube': {
                'api_key': self.platforms.youtube_api_key,
                'client_id': self.platforms.youtube_client_id,
                'client_secret': self.platforms.youtube_client_secret
            },
            'tiktok': {
                'client_key': self.platforms.tiktok_client_key,
                'client_secret': self.platforms.tiktok_client_secret,
                'access_token': self.platforms.tiktok_access_token
            },
            'instagram': {
                'client_id': self.platforms.instagram_client_id,
                'client_secret': self.platforms.instagram_client_secret,
                'access_token': self.platforms.instagram_access_token
            },
            'facebook': {
                'app_id': self.platforms.facebook_app_id,
                'app_secret': self.platforms.facebook_app_secret,
                'access_token': self.platforms.facebook_access_token,
                'page_id': self.platforms.facebook_page_id
            }
        }
        
        return platform_configs.get(platform, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'environment': self.env.value,
            'database': self.database.__dict__,
            'redis': self.redis.__dict__,
            'ai_services': {k: v for k, v in self.ai_services.__dict__.items() if not k.endswith('_key')},
            'storage': self.storage.__dict__,
            'security': {k: v for k, v in self.security.__dict__.items() if 'key' not in k},
            'monitoring': self.monitoring.__dict__,
            'feature_flags': self.feature_flags.__dict__
        }
    
    def save_config(self, filename: Optional[str] = None):
        """Save current configuration to YAML file"""
        if not filename:
            filename = self.config_dir / f"generated_{self.env.value}.yaml"
        
        config_dict = self.to_dict()
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=True)
        
        logger.info(f"Configuration saved to {filename}")

# Global configuration instance
_config_instance: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance

def reload_config():
    """Reload configuration"""
    global _config_instance
    _config_instance = AppConfig()
    return _config_instance

def set_config(config: AppConfig):
    """Set global configuration instance"""
    global _config_instance
    _config_instance = config

# Convenience functions
def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return get_config().database

def get_redis_config() -> RedisConfig:
    """Get Redis configuration"""
    return get_config().redis

def get_ai_service_config(quality_tier: QualityTier = QualityTier.BALANCED) -> Dict[str, Any]:
    """Get AI service configuration"""
    return get_config().get_ai_service_config(quality_tier)

def get_platform_config(platform: str) -> Dict[str, Any]:
    """Get platform configuration"""
    return get_config().get_platform_config(platform)

def is_feature_enabled(feature: str) -> bool:
    """Check if feature is enabled"""
    return getattr(get_config().feature_flags, feature, False)

if __name__ == "__main__":
    # Test configuration loading
    config = AppConfig()
    print("Configuration loaded successfully!")
    print(f"Environment: {config.env.value}")
    print(f"Database URL: {config.database.url}")
    print(f"Redis URL: {config.redis.connection_url}")
    print(f"Feature flags: {config.feature_flags.__dict__}")