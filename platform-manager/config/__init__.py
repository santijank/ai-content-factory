"""
Configuration Package
Centralized configuration management for AI Content Factory
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or Path(__file__).parent)
        self._configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all configuration files"""
        config_files = {
            'ai_models': 'ai_models.yaml',
            'quality_tiers': 'quality_tiers.yaml', 
            'trend_sources': 'trend_sources.yaml',
            'platforms': {
                'youtube': 'platform_configs/youtube.yaml',
                'tiktok': 'platform_configs/tiktok.yaml',
                'instagram': 'platform_configs/instagram.yaml',
                'facebook': 'platform_configs/facebook.yaml'
            }
        }
        
        for config_name, file_path in config_files.items():
            if isinstance(file_path, dict):
                # Handle nested configs (like platforms)
                self._configs[config_name] = {}
                for sub_name, sub_path in file_path.items():
                    self._configs[config_name][sub_name] = self._load_config_file(sub_path)
            else:
                self._configs[config_name] = self._load_config_file(file_path)
    
    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """Load a single configuration file"""
        full_path = self.config_dir / file_path
        
        if not full_path.exists():
            logger.warning(f"Config file not found: {full_path}")
            return {}
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Apply environment variable substitution
            config = self._substitute_env_vars(config)
            
            # Apply environment-specific overrides
            config = self._apply_environment_overrides(config)
            
            logger.info(f"Loaded config: {file_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config {file_path}: {e}")
            return {}
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Substitute environment variables in config values"""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            # Extract env var name and default value
            env_expr = config[2:-1]  # Remove ${ and }
            
            if ':-' in env_expr:
                env_var, default = env_expr.split(':-', 1)
                return os.environ.get(env_var, default)
            else:
                return os.environ.get(env_expr, config)
        else:
            return config
    
    def _apply_environment_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment-specific configuration overrides"""
        if not isinstance(config, dict):
            return config
            
        current_env = os.environ.get('ENVIRONMENT', 'development')
        
        if 'environments' in config and current_env in config['environments']:
            env_overrides = config['environments'][current_env]
            config = self._deep_merge(config, env_overrides)
            
        return config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    # Public methods
    def get_ai_models_config(self) -> Dict[str, Any]:
        """Get AI models configuration"""
        return self._configs.get('ai_models', {})
    
    def get_quality_tiers_config(self) -> Dict[str, Any]:
        """Get quality tiers configuration"""
        return self._configs.get('quality_tiers', {})
    
    def get_trend_sources_config(self) -> Dict[str, Any]:
        """Get trend sources configuration"""
        return self._configs.get('trend_sources', {})
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        platforms_config = self._configs.get('platforms', {})
        return platforms_config.get(platform, {})
    
    def get_all_platform_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all platform configurations"""
        return self._configs.get('platforms', {})
    
    def get_service_config(self, service_type: str, quality_tier: str) -> Dict[str, Any]:
        """Get service configuration for specific quality tier"""
        ai_config = self.get_ai_models_config()
        
        if service_type in ai_config and quality_tier in ai_config[service_type]:
            return ai_config[service_type][quality_tier]
        
        return {}
    
    def get_tier_config(self, tier_name: str) -> Dict[str, Any]:
        """Get quality tier configuration"""
        tiers_config = self.get_quality_tiers_config()
        tiers = tiers_config.get('tiers', {})
        return tiers.get(tier_name, {})
    
    def reload_configs(self):
        """Reload all configuration files"""
        self._configs.clear()
        self._load_all_configs()
        logger.info("All configurations reloaded")

# Global config manager instance
config_manager = ConfigManager()

# Convenience functions
def get_ai_models_config() -> Dict[str, Any]:
    """Get AI models configuration"""
    return config_manager.get_ai_models_config()

def get_quality_tiers_config() -> Dict[str, Any]:
    """Get quality tiers configuration"""
    return config_manager.get_quality_tiers_config()

def get_trend_sources_config() -> Dict[str, Any]:
    """Get trend sources configuration"""
    return config_manager.get_trend_sources_config()

def get_platform_config(platform: str) -> Dict[str, Any]:
    """Get platform-specific configuration"""
    return config_manager.get_platform_config(platform)

def get_service_config(service_type: str, quality_tier: str) -> Dict[str, Any]:
    """Get service configuration for specific quality tier"""
    return config_manager.get_service_config(service_type, quality_tier)

def get_tier_config(tier_name: str) -> Dict[str, Any]:
    """Get quality tier configuration"""
    return config_manager.get_tier_config(tier_name)

def reload_configs():
    """Reload all configuration files"""
    config_manager.reload_configs()

# Export all configuration functions
__all__ = [
    'ConfigManager',
    'config_manager',
    'get_ai_models_config',
    'get_quality_tiers_config', 
    'get_trend_sources_config',
    'get_platform_config',
    'get_service_config',
    'get_tier_config',
    'reload_configs'
]