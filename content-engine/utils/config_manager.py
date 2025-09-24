"""
Configuration Manager for AI Content Factory
Handles loading, saving, and managing configuration files

Features:
- Multiple configuration file formats (YAML, JSON, ENV)
- Environment variable substitution
- Configuration validation
- Hot reloading
- Configuration merging and overrides
- Secure handling of sensitive data
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from datetime import datetime
import re
from dataclasses import dataclass, asdict
from enum import Enum

class ConfigFormat(Enum):
    """Supported configuration file formats"""
    YAML = "yaml"
    JSON = "json"
    ENV = "env"

@dataclass
class ConfigFile:
    """Configuration file metadata"""
    path: Path
    format: ConfigFormat
    last_modified: datetime
    is_loaded: bool = False
    is_valid: bool = True
    error_message: str = None

class ConfigManager:
    """
    Configuration manager for AI Content Factory
    Handles multiple configuration sources and formats
    """
    
    def __init__(self, base_path: Union[str, Path] = None):
        """
        Initialize configuration manager
        
        Args:
            base_path: Base path for configuration files
        """
        self.base_path = Path(base_path) if base_path else Path("config")
        self.logger = logging.getLogger("ai_content_factory.config")
        
        # Configuration storage
        self._config: Dict[str, Any] = {}
        self._config_files: Dict[str, ConfigFile] = {}
        self._watchers: Dict[str, float] = {}  # File modification times
        
        # Default configuration
        self._defaults = self._get_default_config()
        
        # Environment variable prefix
        self.env_prefix = "ACF_"  # AI Content Factory prefix
        
        # Validation rules
        self._validation_rules = self._get_validation_rules()
        
        # Load initial configuration
        self._load_initial_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values
        
        Returns:
            Default configuration dictionary
        """
        return {
            "app": {
                "name": "AI Content Factory",
                "version": "1.0.0",
                "debug": False,
                "host": "localhost",
                "port": 5000,
                "secret_key": "change-this-in-production"
            },
            "database": {
                "url": "postgresql://localhost:5432/content_factory",
                "pool_size": 10,
                "max_overflow": 20,
                "echo": False
            },
            "services": {
                "default_tier": "budget",
                "timeout": 30,
                "retry_attempts": 3,
                "rate_limit": {
                    "requests_per_hour": 1000,
                    "burst_limit": 10
                }
            },
            "ai_services": {
                "text_ai": {
                    "groq": {
                        "api_key": None,
                        "model": "llama3-8b-8192",
                        "max_tokens": 8192,
                        "temperature": 0.7
                    },
                    "openai": {
                        "api_key": None,
                        "model": "gpt-3.5-turbo",
                        "max_tokens": 16000,
                        "temperature": 0.7
                    },
                    "claude": {
                        "api_key": None,
                        "model": "claude-3-sonnet",
                        "max_tokens": 100000,
                        "temperature": 0.7
                    }
                },
                "audio_ai": {
                    "gtts": {
                        "language": "th",
                        "slow": False
                    },
                    "azure": {
                        "api_key": None,
                        "region": "southeastasia",
                        "voice": "th-TH-AcharaNeural"
                    },
                    "elevenlabs": {
                        "api_key": None,
                        "model": "eleven_multilingual_v2",
                        "voice_id": "21m00Tcm4TlvDq8ikWAM"
                    }
                },
                "image_ai": {
                    "stable_diffusion": {
                        "model_path": "./models/stable-diffusion",
                        "steps": 20,
                        "guidance_scale": 7.5
                    },
                    "leonardo": {
                        "api_key": None,
                        "model": "leonardo_creative"
                    },
                    "midjourney": {
                        "api_key": None,
                        "version": "6"
                    }
                }
            },
            "platforms": {
                "youtube": {
                    "client_id": None,
                    "client_secret": None,
                    "refresh_token": None
                },
                "tiktok": {
                    "client_key": None,
                    "client_secret": None,
                    "access_token": None
                },
                "instagram": {
                    "client_id": None,
                    "client_secret": None,
                    "access_token": None
                },
                "facebook": {
                    "app_id": None,
                    "app_secret": None,
                    "access_token": None
                }
            },
            "storage": {
                "type": "local",  # local, s3, gcs
                "local": {
                    "base_path": "./storage",
                    "max_file_size": "100MB"
                },
                "s3": {
                    "bucket": None,
                    "region": "ap-southeast-1",
                    "access_key": None,
                    "secret_key": None
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "./logs/app.log",
                "max_file_size": "10MB",
                "backup_count": 5
            }
        }
    
    def _get_validation_rules(self) -> Dict[str, Any]:
        """
        Get configuration validation rules
        
        Returns:
            Validation rules dictionary
        """
        return {
            "required_fields": [
                "app.name",
                "app.version",
                "services.default_tier"
            ],
            "field_types": {
                "app.port": int,
                "app.debug": bool,
                "database.pool_size": int,
                "services.timeout": int,
                "services.retry_attempts": int
            },
            "valid_values": {
                "services.default_tier": ["budget", "balanced", "premium"],
                "storage.type": ["local", "s3", "gcs"],
                "logging.level": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            }
        }
    
    def _load_initial_config(self):
        """Load initial configuration from files and environment"""
        try:
            # Start with defaults
            self._config = self._defaults.copy()
            
            # Load configuration files
            self._load_config_files()
            
            # Override with environment variables
            self._load_environment_variables()
            
            # Validate configuration
            self._validate_config()
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            raise
    
    def _load_config_files(self):
        """Load configuration from files"""
        config_files = [
            "app_config.yaml",
            "ai_models.yaml", 
            "platform_configs.yaml",
            "local_config.yaml",  # Local overrides
            "production.yaml"     # Production overrides
        ]
        
        for filename in config_files:
            file_path = self.base_path / filename
            
            if file_path.exists():
                try:
                    config_data = self._load_config_file(file_path)
                    if config_data:
                        self._merge_config(config_data)
                        self.logger.debug(f"Loaded config from {filename}")
                except Exception as e:
                    self.logger.warning(f"Failed to load {filename}: {str(e)}")
    
    def _load_config_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load configuration from a single file
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Configuration data or None if failed
        """
        try:
            # Determine format from extension
            ext = file_path.suffix.lower()
            
            if ext in ['.yaml', '.yml']:
                format_type = ConfigFormat.YAML
            elif ext == '.json':
                format_type = ConfigFormat.JSON
            elif ext == '.env':
                format_type = ConfigFormat.ENV
            else:
                self.logger.warning(f"Unknown config file format: {ext}")
                return None
            
            # Load file content
            with open(file_path, 'r', encoding='utf-8') as f:
                if format_type == ConfigFormat.YAML:
                    data = yaml.safe_load(f)
                elif format_type == ConfigFormat.JSON:
                    data = json.load(f)
                elif format_type == ConfigFormat.ENV:
                    data = self._parse_env_file(f.read())
                else:
                    return None
            
            # Process environment variable substitution
            data = self._substitute_env_vars(data)
            
            # Register file for watching
            self._register_config_file(file_path, format_type)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading config file {file_path}: {str(e)}")
            return None
    
    def _parse_env_file(self, content: str) -> Dict[str, Any]:
        """
        Parse environment file content
        
        Args:
            content: File content
            
        Returns:
            Parsed configuration
        """
        config = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # Convert to nested structure
                self._set_nested_value(config, key, value)
        
        return config
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """
        Substitute environment variables in configuration data
        
        Args:
            data: Configuration data
            
        Returns:
            Data with environment variables substituted
        """
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Replace ${VAR} or $VAR patterns
            pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
            
            def replace_var(match):
                var_name = match.group(1) or match.group(2)
                return os.getenv(var_name, match.group(0))
            
            return re.sub(pattern, replace_var, data)
        else:
            return data
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Remove prefix and convert to config key
                config_key = key[len(self.env_prefix):].lower()
                
                # Convert underscores to dots for nested keys
                config_key = config_key.replace('_', '.')
                
                # Try to parse value as JSON, fallback to string
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value
                
                # Set nested value
                self._set_nested_value(self._config, config_key, parsed_value)
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """
        Merge new configuration into existing configuration
        
        Args:
            new_config: New configuration to merge
        """
        def merge_dicts(base: dict, update: dict) -> dict:
            """Recursively merge dictionaries"""
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dicts(base[key], value)
                else:
                    base[key] = value
            return base
        
        merge_dicts(self._config, new_config)
    
    def _set_nested_value(self, config: dict, key_path: str, value: Any):
        """
        Set nested value using dot notation
        
        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path
            value: Value to set
        """
        keys = key_path.split('.')
        current = config
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set final value
        current[keys[-1]] = value
    
    def _get_nested_value(self, config: dict, key_path: str, default: Any = None) -> Any:
        """
        Get nested value using dot notation
        
        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path
            default: Default value if not found
            
        Returns:
            Value or default
        """
        keys = key_path.split('.')
        current = config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def _validate_config(self):
        """Validate configuration against rules"""
        errors = []
        
        # Check required fields
        for field in self._validation_rules["required_fields"]:
            if self._get_nested_value(self._config, field) is None:
                errors.append(f"Required field missing: {field}")
        
        # Check field types
        for field, expected_type in self._validation_rules["field_types"].items():
            value = self._get_nested_value(self._config, field)
            if value is not None and not isinstance(value, expected_type):
                errors.append(f"Invalid type for {field}: expected {expected_type.__name__}, got {type(value).__name__}")
        
        # Check valid values
        for field, valid_values in self._validation_rules["valid_values"].items():
            value = self._get_nested_value(self._config, field)
            if value is not None and value not in valid_values:
                errors.append(f"Invalid value for {field}: {value}, must be one of {valid_values}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _register_config_file(self, file_path: Path, format_type: ConfigFormat):
        """Register configuration file for watching"""
        stat = file_path.stat()
        
        self._config_files[str(file_path)] = ConfigFile(
            path=file_path,
            format=format_type,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            is_loaded=True,
            is_valid=True
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._get_nested_value(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        self._set_nested_value(self._config, key, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section
        
        Args:
            section: Section name
            
        Returns:
            Section configuration
        """
        return self.get(section, {})
    
    def reload(self):
        """Reload configuration from files"""
        self.logger.info("Reloading configuration...")
        self._load_initial_config()
    
    def check_for_changes(self) -> bool:
        """
        Check if any configuration files have changed
        
        Returns:
            True if changes detected
        """
        changes_detected = False
        
        for file_path_str, config_file in self._config_files.items():
            file_path = Path(file_path_str)
            
            if file_path.exists():
                stat = file_path.stat()
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                
                if last_modified > config_file.last_modified:
                    self.logger.info(f"Configuration file changed: {file_path}")
                    changes_detected = True
            else:
                self.logger.warning(f"Configuration file no longer exists: {file_path}")
                changes_detected = True
        
        return changes_detected
    
    def save_to_file(self, file_path: Union[str, Path], section: str = None, format_type: ConfigFormat = ConfigFormat.YAML):
        """
        Save configuration to file
        
        Args:
            file_path: Output file path
            section: Optional section to save (saves all if None)
            format_type: Output format
        """
        file_path = Path(file_path)
        
        # Get data to save
        if section:
            data = self.get_section(section)
        else:
            data = self._config
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save based on format
        with open(file_path, 'w', encoding='utf-8') as f:
            if format_type == ConfigFormat.YAML:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            elif format_type == ConfigFormat.JSON:
                json.dump(data, f, indent=2, ensure_ascii=False)
            elif format_type == ConfigFormat.ENV:
                self._write_env_file(f, data)
        
        self.logger.info(f"Configuration saved to {file_path}")
    
    def _write_env_file(self, file_handle, data: dict, prefix: str = ""):
        """Write configuration as environment file"""
        for key, value in data.items():
            full_key = f"{prefix}{key}".upper()
            
            if isinstance(value, dict):
                self._write_env_file(file_handle, value, f"{full_key}_")
            else:
                if isinstance(value, str) and (' ' in value or '"' in value):
                    value = f'"{value}"'
                file_handle.write(f"{full_key}={value}\n")
    
    def export_config(self) -> Dict[str, Any]:
        """
        Export current configuration
        
        Returns:
            Current configuration dictionary
        """
        return self._config.copy()
    
    def import_config(self, config_data: Dict[str, Any], merge: bool = True):
        """
        Import configuration data
        
        Args:
            config_data: Configuration data to import
            merge: Whether to merge with existing config
        """
        if merge:
            self._merge_config(config_data)
        else:
            self._config = config_data.copy()
        
        self._validate_config()
        self.logger.info("Configuration imported successfully")

# Global configuration manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value using global manager"""
    return get_config_manager().get(key, default)

def set_config(key: str, value: Any):
    """Set configuration value using global manager"""
    get_config_manager().set(key, value)

def get_config_section(section: str) -> Dict[str, Any]:
    """Get configuration section using global manager"""
    return get_config_manager().get_section(section)

def load_config_file(file_path: Union[str, Path]) -> bool:
    """
    Load additional configuration file
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        True if loaded successfully
    """
    try:
        manager = get_config_manager()
        config_data = manager._load_config_file(Path(file_path))
        if config_data:
            manager._merge_config(config_data)
            return True
        return False
    except Exception:
        return False

def reload_config():
    """Reload configuration from files"""
    get_config_manager().reload()