"""
Platform Configuration Manager
จัดการการตั้งค่าและข้อมูลเข้าสู่ระบบสำหรับ platforms ต่างๆ
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import base64
from cryptography.fernet import Fernet
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class PlatformConfig:
    """การตั้งค่าสำหรับ platform เฉพาะ"""
    
    platform_name: str
    enabled: bool
    api_credentials: Dict[str, Any]
    upload_settings: Dict[str, Any]
    rate_limits: Dict[str, Any]
    custom_settings: Dict[str, Any]
    last_updated: Optional[str] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()

class ConfigManager:
    """หลักการจัดการการตั้งค่าทั้งหมด"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or os.getenv('CONFIG_DIR', './config'))
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize encryption for sensitive data
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Configuration files
        self.main_config_file = self.config_dir / "app_config.yaml"
        self.platforms_config_dir = self.config_dir / "platform_configs"
        self.platforms_config_dir.mkdir(exist_ok=True)
        self.credentials_file = self.config_dir / "credentials.enc"
        
        # Load configurations
        self.main_config = self._load_main_config()
        self.platform_configs = self._load_platform_configs()
        self.credentials = self._load_credentials()
        
        logger.info("Configuration Manager initialized")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """สร้างหรือโหลด encryption key"""
        
        key_file = self.config_dir / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def _load_main_config(self) -> Dict[str, Any]:
        """โหลดการตั้งค่าหลัก"""
        
        if self.main_config_file.exists():
            try:
                with open(self.main_config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Error loading main config: {str(e)}")
                return self._get_default_main_config()
        else:
            # Create default config
            default_config = self._get_default_main_config()
            self._save_main_config(default_config)
            return default_config
    
    def _get_default_main_config(self) -> Dict[str, Any]:
        """ได้รับการตั้งค่าเริ่มต้น"""
        
        return {
            "app": {
                "name": "AI Content Factory - Platform Manager",
                "version": "1.0.0",
                "debug": False,
                "temp_dir": "./temp",
                "max_concurrent_uploads": 3
            },
            "optimization": {
                "default_quality": "medium",
                "auto_optimize": True,
                "keep_originals": True,
                "max_file_size_mb": 1024
            },
            "monitoring": {
                "enable_analytics": True,
                "log_level": "INFO",
                "metrics_retention_days": 30
            },
            "platforms": {
                "enabled": ["youtube", "tiktok", "instagram", "facebook"],
                "default_privacy": "public",
                "auto_schedule": False
            }
        }
    
    def _load_platform_configs(self) -> Dict[str, PlatformConfig]:
        """โหลดการตั้งค่าของ platforms ทั้งหมด"""
        
        configs = {}
        
        for platform_file in self.platforms_config_dir.glob("*.yaml"):
            platform_name = platform_file.stem
            
            try:
                with open(platform_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    
                configs[platform_name] = PlatformConfig(
                    platform_name=platform_name,
                    enabled=config_data.get("enabled", False),
                    api_credentials=config_data.get("api_credentials", {}),
                    upload_settings=config_data.get("upload_settings", {}),
                    rate_limits=config_data.get("rate_limits", {}),
                    custom_settings=config_data.get("custom_settings", {}),
                    last_updated=config_data.get("last_updated")
                )
                
            except Exception as e:
                logger.error(f"Error loading config for {platform_name}: {str(e)}")
        
        # Create default configs for missing platforms
        for platform in ["youtube", "tiktok", "instagram", "facebook"]:
            if platform not in configs:
                configs[platform] = self._create_default_platform_config(platform)
                self._save_platform_config(configs[platform])
        
        return configs
    
    def _create_default_platform_config(self, platform_name: str) -> PlatformConfig:
        """สร้างการตั้งค่าเริ่มต้นสำหรับ platform"""
        
        default_configs = {
            "youtube": {
                "enabled": False,
                "api_credentials": {
                    "client_id": "",
                    "client_secret": "",
                    "redirect_uri": "http://localhost:8080/oauth/callback"
                },
                "upload_settings": {
                    "default_privacy": "private",
                    "default_category": "22",  # People & Blogs
                    "auto_generate_thumbnail": True,
                    "enable_monetization": False
                },
                "rate_limits": {
                    "uploads_per_day": 6,
                    "api_quota_per_day": 10000
                },
                "custom_settings": {
                    "auto_add_to_playlist": False,
                    "enable_comments": True,
                    "enable_embed": True
                }
            },
            "tiktok": {
                "enabled": False,
                "api_credentials": {
                    "client_key": "",
                    "client_secret": "",
                    "redirect_uri": "http://localhost:8080/tiktok/callback"
                },
                "upload_settings": {
                    "default_privacy": "public",
                    "auto_add_music": False,
                    "allow_duet": True,
                    "allow_stitch": True
                },
                "rate_limits": {
                    "uploads_per_day": 50,
                    "api_calls_per_day": 1000
                },
                "custom_settings": {
                    "auto_hashtags": True,
                    "max_hashtags": 5
                }
            },
            "instagram": {
                "enabled": False,
                "api_credentials": {
                    "access_token": "",
                    "app_id": "",
                    "app_secret": ""
                },
                "upload_settings": {
                    "default_type": "reel",
                    "auto_location": False,
                    "enable_shopping": False
                },
                "rate_limits": {
                    "uploads_per_hour": 25,
                    "api_calls_per_hour": 200
                },
                "custom_settings": {
                    "auto_hashtags": True,
                    "max_hashtags": 30,
                    "default_location": None
                }
            },
            "facebook": {
                "enabled": False,
                "api_credentials": {
                    "access_token": "",
                    "page_id": "",
                    "app_id": "",
                    "app_secret": ""
                },
                "upload_settings": {
                    "default_privacy": "public",
                    "enable_crosspost": False,
                    "auto_boost": False
                },
                "rate_limits": {
                    "uploads_per_hour": 100,
                    "api_calls_per_hour": 600
                },
                "custom_settings": {
                    "targeting_enabled": False,
                    "call_to_action": None
                }
            }
        }
        
        config_data = default_configs.get(platform_name, {
            "enabled": False,
            "api_credentials": {},
            "upload_settings": {},
            "rate_limits": {},
            "custom_settings": {}
        })
        
        return PlatformConfig(
            platform_name=platform_name,
            **config_data
        )
    
    def _load_credentials(self) -> Dict[str, Any]:
        """โหลดข้อมูลเข้าสู่ระบบที่เข้ารหัส"""
        
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self.cipher.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode('utf-8'))
                
            except Exception as e:
                logger.error(f"Error loading credentials: {str(e)}")
                return {}
        
        return {}
    
    def _save_main_config(self, config: Dict[str, Any]) -> None:
        """บันทึกการตั้งค่าหลัก"""
        
        try:
            with open(self.main_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info("Main config saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving main config: {str(e)}")
    
    def _save_platform_config(self, platform_config: PlatformConfig) -> None:
        """บันทึกการตั้งค่าของ platform"""
        
        try:
            config_file = self.platforms_config_dir / f"{platform_config.platform_name}.yaml"
            
            # Remove sensitive data before saving
            safe_config = asdict(platform_config)
            safe_config['api_credentials'] = {
                key: "***ENCRYPTED***" if value else ""
                for key, value in safe_config['api_credentials'].items()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(safe_config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Platform config saved for {platform_config.platform_name}")
            
        except Exception as e:
            logger.error(f"Error saving platform config: {str(e)}")
    
    def _save_credentials(self, credentials: Dict[str, Any]) -> None:
        """บันทึกข้อมูลเข้าสู่ระบบแบบเข้ารหัส"""
        
        try:
            json_data = json.dumps(credentials).encode('utf-8')
            encrypted_data = self.cipher.encrypt(json_data)
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.credentials_file, 0o600)
            
            logger.info("Credentials saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
    
    # Public methods
    def get_main_config(self) -> Dict[str, Any]:
        """ได้รับการตั้งค่าหลัก"""
        return self.main_config.copy()
    
    def update_main_config(self, updates: Dict[str, Any]) -> None:
        """อัปเดตการตั้งค่าหลัก"""
        
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.main_config, updates)
        self._save_main_config(self.main_config)
    
    def get_platform_config(self, platform_name: str) -> Optional[PlatformConfig]:
        """ได้รับการตั้งค่าของ platform"""
        return self.platform_configs.get(platform_name)
    
    def update_platform_config(self, platform_name: str, updates: Dict[str, Any]) -> None:
        """อัปเดตการตั้งค่าของ platform"""
        
        if platform_name not in self.platform_configs:
            self.platform_configs[platform_name] = self._create_default_platform_config(platform_name)
        
        config = self.platform_configs[platform_name]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(config, key):
                if isinstance(getattr(config, key), dict) and isinstance(value, dict):
                    getattr(config, key).update(value)
                else:
                    setattr(config, key, value)
        
        config.last_updated = datetime.now().isoformat()
        self._save_platform_config(config)
    
    def set_platform_credentials(self, platform_name: str, credentials: Dict[str, Any]) -> None:
        """ตั้งค่าข้อมูลเข้าสู่ระบบสำหรับ platform"""
        
        # Update credentials in memory
        if platform_name not in self.credentials:
            self.credentials[platform_name] = {}
        
        self.credentials[platform_name].update(credentials)
        
        # Save encrypted credentials
        self._save_credentials(self.credentials)
        
        # Update platform config to mark as configured
        if platform_name in self.platform_configs:
            self.platform_configs[platform_name].api_credentials.update({
                key: "***SET***" for key in credentials.keys()
            })
    
    def get_platform_credentials(self, platform_name: str) -> Dict[str, Any]:
        """ได้รับข้อมูลเข้าสู่ระบบของ platform"""
        return self.credentials.get(platform_name, {})
    
    def is_platform_configured(self, platform_name: str) -> bool:
        """ตรวจสอบว่า platform ได้รับการตั้งค่าแล้วหรือไม่"""
        
        config = self.get_platform_config(platform_name)
        if not config or not config.enabled:
            return False
        
        credentials = self.get_platform_credentials(platform_name)
        
        # Platform-specific credential validation
        if platform_name == "youtube":
            return bool(credentials.get("client_id") and credentials.get("client_secret"))
        elif platform_name == "tiktok":
            return bool(credentials.get("client_key") and credentials.get("client_secret"))
        elif platform_name == "instagram":
            return bool(credentials.get("access_token"))
        elif platform_name == "facebook":
            return bool(credentials.get("access_token") and credentials.get("page_id"))
        
        return bool(credentials)
    
    def get_enabled_platforms(self) -> List[str]:
        """ได้รับรายการ platforms ที่เปิดใช้งาน"""
        
        enabled_platforms = []
        
        for platform_name, config in self.platform_configs.items():
            if config.enabled and self.is_platform_configured(platform_name):
                enabled_platforms.append(platform_name)
        
        return enabled_platforms
    
    def enable_platform(self, platform_name: str) -> None:
        """เปิดใช้งาน platform"""
        
        if platform_name in self.platform_configs:
            self.platform_configs[platform_name].enabled = True
            self.platform_configs[platform_name].last_updated = datetime.now().isoformat()
            self._save_platform_config(self.platform_configs[platform_name])
        
        logger.info(f"Platform {platform_name} enabled")
    
    def disable_platform(self, platform_name: str) -> None:
        """ปิดใช้งาน platform"""
        
        if platform_name in self.platform_configs:
            self.platform_configs[platform_name].enabled = False
            self.platform_configs[platform_name].last_updated = datetime.now().isoformat()
            self._save_platform_config(self.platform_configs[platform_name])
        
        logger.info(f"Platform {platform_name} disabled")
    
    def get_upload_settings(self, platform_name: str) -> Dict[str, Any]:
        """ได้รับการตั้งค่าการอัปโหลดของ platform"""
        
        config = self.get_platform_config(platform_name)
        if config:
            return config.upload_settings.copy()
        
        return {}
    
    def get_rate_limits(self, platform_name: str) -> Dict[str, Any]:
        """ได้รับข้อจำกัดอัตราของ platform"""
        
        config = self.get_platform_config(platform_name)
        if config:
            return config.rate_limits.copy()
        
        return {}
    
    def validate_configuration(self) -> Dict[str, Any]:
        """ตรวจสอบความถูกต้องของการตั้งค่าทั้งหมด"""
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "platform_status": {}
        }
        
        # Check main config
        if not self.main_config:
            validation_results["errors"].append("Main configuration is missing")
            validation_results["valid"] = False
        
        # Check each platform
        for platform_name in ["youtube", "tiktok", "instagram", "facebook"]:
            platform_status = {
                "configured": False,
                "enabled": False,
                "credentials_valid": False,
                "issues": []
            }
            
            config = self.get_platform_config(platform_name)
            if config:
                platform_status["enabled"] = config.enabled
                platform_status["configured"] = self.is_platform_configured(platform_name)
                
                # Check credentials
                credentials = self.get_platform_credentials(platform_name)
                if credentials:
                    platform_status["credentials_valid"] = True
                else:
                    platform_status["issues"].append("No credentials configured")
            else:
                platform_status["issues"].append("Configuration missing")
            
            validation_results["platform_status"][platform_name] = platform_status
        
        # Check if at least one platform is configured
        configured_platforms = [
            name for name, status in validation_results["platform_status"].items()
            if status["configured"] and status["enabled"]
        ]
        
        if not configured_platforms:
            validation_results["warnings"].append(
                "No platforms are fully configured and enabled"
            )
        
        return validation_results
    
    def export_config(self, include_credentials: bool = False) -> Dict[str, Any]:
        """ส่งออกการตั้งค่าทั้งหมด"""
        
        export_data = {
            "main_config": self.main_config,
            "platform_configs": {
                name: asdict(config) for name, config in self.platform_configs.items()
            },
            "exported_at": datetime.now().isoformat()
        }
        
        if include_credentials:
            export_data["credentials"] = self.credentials
        else:
            # Remove sensitive data
            for platform_config in export_data["platform_configs"].values():
                platform_config["api_credentials"] = {
                    key: "***REDACTED***" if value else ""
                    for key, value in platform_config["api_credentials"].items()
                }
        
        return export_data
    
    def import_config(self, config_data: Dict[str, Any]) -> None:
        """นำเข้าการตั้งค่า"""
        
        try:
            # Import main config
            if "main_config" in config_data:
                self.main_config = config_data["main_config"]
                self._save_main_config(self.main_config)
            
            # Import platform configs
            if "platform_configs" in config_data:
                for platform_name, config_dict in config_data["platform_configs"].items():
                    platform_config = PlatformConfig(**config_dict)
                    self.platform_configs[platform_name] = platform_config
                    self._save_platform_config(platform_config)
            
            # Import credentials if provided
            if "credentials" in config_data:
                self.credentials = config_data["credentials"]
                self._save_credentials(self.credentials)
            
            logger.info("Configuration imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing configuration: {str(e)}")
            raise
    
    def reset_to_defaults(self) -> None:
        """รีเซ็ตการตั้งค่าเป็นค่าเริ่มต้น"""
        
        logger.warning("Resetting configuration to defaults")
        
        # Reset main config
        self.main_config = self._get_default_main_config()
        self._save_main_config(self.main_config)
        
        # Reset platform configs
        for platform_name in ["youtube", "tiktok", "instagram", "facebook"]:
            self.platform_configs[platform_name] = self._create_default_platform_config(platform_name)
            self._save_platform_config(self.platform_configs[platform_name])
        
        # Clear credentials
        self.credentials = {}
        self._save_credentials(self.credentials)

# Utility functions
def get_config_template(platform_name: str) -> Dict[str, Any]:
    """ได้รับ template การตั้งค่าสำหรับ platform"""
    
    config_manager = ConfigManager()
    default_config = config_manager._create_default_platform_config(platform_name)
    return asdict(default_config)

def validate_credentials(platform_name: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """ตรวจสอบความถูกต้องของข้อมูลเข้าสู่ระบบ"""
    
    validation = {"valid": True, "errors": []}
    
    required_fields = {
        "youtube": ["client_id", "client_secret"],
        "tiktok": ["client_key", "client_secret"],
        "instagram": ["access_token"],
        "facebook": ["access_token", "page_id"]
    }
    
    if platform_name in required_fields:
        for field in required_fields[platform_name]:
            if not credentials.get(field):
                validation["errors"].append(f"Missing required field: {field}")
                validation["valid"] = False
    
    return validation