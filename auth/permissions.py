#!/usr/bin/env python3
"""
Permissions and Role Management System for AI Content Factory
ใช้สำหรับจัดการสิทธิ์และบทบาทของผู้ใช้ในระบบ
"""

import os
import sys
import logging
from enum import Enum
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.logger import setup_logger

class Permission(Enum):
    """System permissions enumeration"""
    
    # Content Management
    CREATE_CONTENT = "create_content"
    READ_CONTENT = "read_content"
    UPDATE_CONTENT = "update_content"
    DELETE_CONTENT = "delete_content"
    PUBLISH_CONTENT = "publish_content"
    
    # Trend Management
    VIEW_TRENDS = "view_trends"
    ANALYZE_TRENDS = "analyze_trends"
    COLLECT_TRENDS = "collect_trends"
    
    # Platform Management
    UPLOAD_TO_PLATFORMS = "upload_to_platforms"
    MANAGE_PLATFORM_ACCOUNTS = "manage_platform_accounts"
    VIEW_PLATFORM_ANALYTICS = "view_platform_analytics"
    
    # User Management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    MANAGE_USER_ROLES = "manage_user_roles"
    
    # System Administration
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM_CONFIG = "manage_system_config"
    BACKUP_SYSTEM = "backup_system"
    RESTORE_SYSTEM = "restore_system"
    
    # Analytics and Reporting
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    VIEW_PERFORMANCE_METRICS = "view_performance_metrics"
    
    # API Access
    API_ACCESS = "api_access"
    ADMIN_API_ACCESS = "admin_api_access"
    
    # Content Quality Control
    REVIEW_CONTENT = "review_content"
    APPROVE_CONTENT = "approve_content"
    REJECT_CONTENT = "reject_content"
    
    # Financial
    VIEW_BILLING = "view_billing"
    MANAGE_BILLING = "manage_billing"
    VIEW_REVENUE = "view_revenue"

class UserRole(Enum):
    """User roles with hierarchical permissions"""
    
    GUEST = "guest"
    USER = "user"
    CREATOR = "creator"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class RoleDefinition:
    """Role definition with permissions and metadata"""
    name: str
    description: str
    permissions: Set[Permission]
    inherits_from: Optional['RoleDefinition'] = None
    is_system_role: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PermissionManager:
    """Main class for managing permissions and roles"""
    
    def __init__(self):
        self.logger = setup_logger("permission_manager")
        self.roles: Dict[UserRole, RoleDefinition] = {}
        self.custom_roles: Dict[str, RoleDefinition] = {}
        
        # Initialize default roles
        self._initialize_default_roles()
        
        self.logger.info("Permission Manager initialized")
    
    def _initialize_default_roles(self):
        """Initialize default system roles with their permissions"""
        
        # Guest Role - Very limited access
        guest_permissions = {
            Permission.VIEW_TRENDS,
            Permission.API_ACCESS
        }
        
        self.roles[UserRole.GUEST] = RoleDefinition(
            name="Guest",
            description="Limited access for unauthenticated users",
            permissions=guest_permissions,
            is_system_role=True
        )
        
        # User Role - Basic authenticated user
        user_permissions = guest_permissions | {
            Permission.READ_CONTENT,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_PERFORMANCE_METRICS
        }
        
        self.roles[UserRole.USER] = RoleDefinition(
            name="User",
            description="Basic authenticated user with read access",
            permissions=user_permissions,
            inherits_from=self.roles[UserRole.GUEST],
            is_system_role=True
        )
        
        # Creator Role - Content creation access
        creator_permissions = user_permissions | {
            Permission.CREATE_CONTENT,
            Permission.UPDATE_CONTENT,
            Permission.DELETE_CONTENT,
            Permission.ANALYZE_TRENDS,
            Permission.UPLOAD_TO_PLATFORMS,
            Permission.VIEW_PLATFORM_ANALYTICS
        }
        
        self.roles[UserRole.CREATOR] = RoleDefinition(
            name="Creator",
            description="Content creator with full content management access",
            permissions=creator_permissions,
            inherits_from=self.roles[UserRole.USER],
            is_system_role=True
        )
        
        # Moderator Role - Content review and moderation
        moderator_permissions = creator_permissions | {
            Permission.PUBLISH_CONTENT,
            Permission.REVIEW_CONTENT,
            Permission.APPROVE_CONTENT,
            Permission.REJECT_CONTENT,
            Permission.COLLECT_TRENDS,
            Permission.MANAGE_PLATFORM_ACCOUNTS,
            Permission.EXPORT_DATA
        }
        
        self.roles[UserRole.MODERATOR] = RoleDefinition(
            name="Moderator",
            description="Content moderator with review and publishing rights",
            permissions=moderator_permissions,
            inherits_from=self.roles[UserRole.CREATOR],
            is_system_role=True
        )
        
        # Admin Role - System administration
        admin_permissions = moderator_permissions | {
            Permission.CREATE_USER,
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.DELETE_USER,
            Permission.MANAGE_USER_ROLES,
            Permission.VIEW_SYSTEM_LOGS,
            Permission.MANAGE_SYSTEM_CONFIG,
            Permission.ADMIN_API_ACCESS,
            Permission.VIEW_BILLING,
            Permission.MANAGE_BILLING,
            Permission.VIEW_REVENUE
        }
        
        self.roles[UserRole.ADMIN] = RoleDefinition(
            name="Admin",
            description="System administrator with full access except super admin functions",
            permissions=admin_permissions,
            inherits_from=self.roles[UserRole.MODERATOR],
            is_system_role=True
        )
        
        # Super Admin Role - Ultimate access
        super_admin_permissions = admin_permissions | {
            Permission.BACKUP_SYSTEM,
            Permission.RESTORE_SYSTEM
        }
        
        self.roles[UserRole.SUPER_ADMIN] = RoleDefinition(
            name="Super Admin",
            description="Ultimate system access with all permissions",
            permissions=super_admin_permissions,
            inherits_from=self.roles[UserRole.ADMIN],
            is_system_role=True
        )
    
    def get_role_permissions(self, role: UserRole) -> Set[Permission]:
        """Get all permissions for a role"""
        if role not in self.roles:
            return set()
        
        return self.roles[role].permissions.copy()
    
    def has_permission(self, role: UserRole, permission: Permission) -> bool:
        """Check if role has specific permission"""
        if role not in self.roles:
            return False
        
        return permission in self.roles[role].permissions
    
    def has_permissions(self, role: UserRole, permissions: List[Permission], require_all: bool = True) -> bool:
        """Check if role has multiple permissions"""
        if role not in self.roles:
            return False
        
        role_permissions = self.roles[role].permissions
        required_permissions = set(permissions)
        
        if require_all:
            return required_permissions.issubset(role_permissions)
        else:
            return bool(required_permissions.intersection(role_permissions))
    
    @staticmethod
    def has_role_hierarchy(user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role has sufficient hierarchy level"""
        role_hierarchy = {
            UserRole.GUEST: 0,
            UserRole.USER: 1,
            UserRole.CREATOR: 2,
            UserRole.MODERATOR: 3,
            UserRole.ADMIN: 4,
            UserRole.SUPER_ADMIN: 5
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def get_available_roles(self) -> Dict[str, Dict[str, Any]]:
        """Get all available roles with their information"""
        result = {}
        
        for role, definition in self.roles.items():
            result[role.value] = {
                'name': definition.name,
                'description': definition.description,
                'permission_count': len(definition.permissions),
                'is_system_role': definition.is_system_role,
                'inherits_from': definition.inherits_from.name if definition.inherits_from else None
            }
        
        # Add custom roles
        for role_name, definition in self.custom_roles.items():
            result[role_name] = {
                'name': definition.name,
                'description': definition.description,
                'permission_count': len(definition.permissions),
                'is_system_role': definition.is_system_role,
                'inherits_from': definition.inherits_from.name if definition.inherits_from else None
            }
        
        return result
    
    def create_custom_role(self, 
                          name: str,
                          description: str,
                          permissions: List[Permission],
                          inherits_from: Optional[UserRole] = None) -> bool:
        """Create a custom role"""
        try:
            if name in self.custom_roles:
                self.logger.warning(f"Custom role {name} already exists")
                return False
            
            # Convert permissions list to set
            permission_set = set(permissions)
            
            # Add inherited permissions if specified
            base_role = None
            if inherits_from and inherits_from in self.roles:
                base_role = self.roles[inherits_from]
                permission_set = permission_set | base_role.permissions
            
            self.custom_roles[name] = RoleDefinition(
                name=name,
                description=description,
                permissions=permission_set,
                inherits_from=base_role,
                is_system_role=False
            )
            
            self.logger.info(f"Custom role created: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create custom role {name}: {str(e)}")
            return False
    
    def update_custom_role(self, 
                          name: str,
                          permissions: List[Permission] = None,
                          description: str = None) -> bool:
        """Update a custom role"""
        try:
            if name not in self.custom_roles:
                self.logger.warning(f"Custom role {name} does not exist")
                return False
            
            role = self.custom_roles[name]
            
            if permissions is not None:
                permission_set = set(permissions)
                # Add inherited permissions if the role inherits from another
                if role.inherits_from:
                    permission_set = permission_set | role.inherits_from.permissions
                role.permissions = permission_set
            
            if description is not None:
                role.description = description
            
            self.logger.info(f"Custom role updated: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update custom role {name}: {str(e)}")
            return False
    
    def delete_custom_role(self, name: str) -> bool:
        """Delete a custom role"""
        try:
            if name not in self.custom_roles:
                self.logger.warning(f"Custom role {name} does not exist")
                return False
            
            del self.custom_roles[name]
            self.logger.info(f"Custom role deleted: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete custom role {name}: {str(e)}")
            return False
    
    def get_permissions_by_category(self) -> Dict[str, List[str]]:
        """Get permissions organized by category"""
        categories = {
            'Content Management': [
                Permission.CREATE_CONTENT,
                Permission.READ_CONTENT,
                Permission.UPDATE_CONTENT,
                Permission.DELETE_CONTENT,
                Permission.PUBLISH_CONTENT,
                Permission.REVIEW_CONTENT,
                Permission.APPROVE_CONTENT,
                Permission.REJECT_CONTENT
            ],
            'Trend Management': [
                Permission.VIEW_TRENDS,
                Permission.ANALYZE_TRENDS,
                Permission.COLLECT_TRENDS
            ],
            'Platform Management': [
                Permission.UPLOAD_TO_PLATFORMS,
                Permission.MANAGE_PLATFORM_ACCOUNTS,
                Permission.VIEW_PLATFORM_ANALYTICS
            ],
            'User Management': [
                Permission.CREATE_USER,
                Permission.READ_USER,
                Permission.UPDATE_USER,
                Permission.DELETE_USER,
                Permission.MANAGE_USER_ROLES
            ],
            'System Administration': [
                Permission.VIEW_SYSTEM_LOGS,
                Permission.MANAGE_SYSTEM_CONFIG,
                Permission.BACKUP_SYSTEM,
                Permission.RESTORE_SYSTEM
            ],
            'Analytics and Reporting': [
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
                Permission.VIEW_PERFORMANCE_METRICS
            ],
            'API Access': [
                Permission.API_ACCESS,
                Permission.ADMIN_API_ACCESS
            ],
            'Financial': [
                Permission.VIEW_BILLING,
                Permission.MANAGE_BILLING,
                Permission.VIEW_REVENUE
            ]
        }
        
        result = {}
        for category, permissions in categories.items():
            result[category] = [perm.value for perm in permissions]
        
        return result
    
    def export_role_configuration(self) -> Dict[str, Any]:
        """Export current role configuration to JSON-serializable format"""
        result = {
            'system_roles': {},
            'custom_roles': {},
            'permissions': [perm.value for perm in Permission]
        }
        
        # Export system roles
        for role, definition in self.roles.items():
            result['system_roles'][role.value] = {
                'name': definition.name,
                'description': definition.description,
                'permissions': [perm.value for perm in definition.permissions],
                'inherits_from': definition.inherits_from.name if definition.inherits_from else None
            }
        
        # Export custom roles
        for role_name, definition in self.custom_roles.items():
            result['custom_roles'][role_name] = {
                'name': definition.name,
                'description': definition.description,
                'permissions': [perm.value for perm in definition.permissions],
                'inherits_from': definition.inherits_from.name if definition.inherits_from else None,
                'created_at': definition.created_at,
                'updated_at': definition.updated_at
            }
        
        return result
    
    def import_role_configuration(self, config: Dict[str, Any]) -> bool:
        """Import role configuration from JSON data"""
        try:
            # Import custom roles
            custom_roles_data = config.get('custom_roles', {})
            
            for role_name, role_data in custom_roles_data.items():
                permissions = [Permission(perm) for perm in role_data['permissions']]
                
                inherits_from = None
                if role_data.get('inherits_from'):
                    # Find the base role
                    for role in UserRole:
                        if self.roles[role].name == role_data['inherits_from']:
                            inherits_from = role
                            break
                
                self.create_custom_role(
                    name=role_name,
                    description=role_data['description'],
                    permissions=permissions,
                    inherits_from=inherits_from
                )
            
            self.logger.info("Role configuration imported successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import role configuration: {str(e)}")
            return False

class UserPermissionChecker:
    """Utility class for checking user permissions in application context"""
    
    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self.logger = setup_logger("user_permission_checker")
    
    def check_user_permission(self, 
                            user_role: str, 
                            required_permission: Permission,
                            user_permissions: List[str] = None) -> bool:
        """Check if user has specific permission"""
        try:
            # Check role-based permission
            role = UserRole(user_role)
            if self.permission_manager.has_permission(role, required_permission):
                return True
            
            # Check individual user permissions if provided
            if user_permissions and required_permission.value in user_permissions:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Permission check failed: {str(e)}")
            return False
    
    def get_user_effective_permissions(self, 
                                     user_role: str,
                                     user_permissions: List[str] = None) -> Set[str]:
        """Get all effective permissions for a user"""
        try:
            effective_permissions = set()
            
            # Add role-based permissions
            role = UserRole(user_role)
            role_permissions = self.permission_manager.get_role_permissions(role)
            effective_permissions.update(perm.value for perm in role_permissions)
            
            # Add individual user permissions
            if user_permissions:
                effective_permissions.update(user_permissions)
            
            return effective_permissions
            
        except Exception as e:
            self.logger.error(f"Failed to get effective permissions: {str(e)}")
            return set()
    
    def can_access_resource(self, 
                          user_role: str,
                          resource_type: str,
                          action: str,
                          user_permissions: List[str] = None) -> bool:
        """Check if user can perform action on resource type"""
        
        # Map resource types and actions to permissions
        permission_map = {
            'content': {
                'create': Permission.CREATE_CONTENT,
                'read': Permission.READ_CONTENT,
                'update': Permission.UPDATE_CONTENT,
                'delete': Permission.DELETE_CONTENT,
                'publish': Permission.PUBLISH_CONTENT
            },
            'trend': {
                'view': Permission.VIEW_TRENDS,
                'analyze': Permission.ANALYZE_TRENDS,
                'collect': Permission.COLLECT_TRENDS
            },
            'user': {
                'create': Permission.CREATE_USER,
                'read': Permission.READ_USER,
                'update': Permission.UPDATE_USER,
                'delete': Permission.DELETE_USER
            },
            'platform': {
                'upload': Permission.UPLOAD_TO_PLATFORMS,
                'manage': Permission.MANAGE_PLATFORM_ACCOUNTS,
                'analytics': Permission.VIEW_PLATFORM_ANALYTICS
            }
        }
        
        required_permission = permission_map.get(resource_type, {}).get(action)
        if not required_permission:
            self.logger.warning(f"Unknown resource/action: {resource_type}/{action}")
            return False
        
        return self.check_user_permission(user_role, required_permission, user_permissions)

# Utility functions for common permission operations

def create_permission_manager() -> PermissionManager:
    """Factory function to create permission manager"""
    return PermissionManager()

def get_user_role_level(role: UserRole) -> int:
    """Get numeric level for role comparison"""
    role_levels = {
        UserRole.GUEST: 0,
        UserRole.USER: 1,
        UserRole.CREATOR: 2,
        UserRole.MODERATOR: 3,
        UserRole.ADMIN: 4,
        UserRole.SUPER_ADMIN: 5
    }
    return role_levels.get(role, 0)

def get_minimum_role_for_permission(permission: Permission) -> UserRole:
    """Get the minimum role required for a specific permission"""
    pm = PermissionManager()
    
    for role in [UserRole.GUEST, UserRole.USER, UserRole.CREATOR, 
                 UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if pm.has_permission(role, permission):
            return role
    
    return UserRole.SUPER_ADMIN  # Default to highest role if not found

def validate_permission_string(permission_str: str) -> bool:
    """Validate if string is a valid permission"""
    try:
        Permission(permission_str)
        return True
    except ValueError:
        return False

def validate_role_string(role_str: str) -> bool:
    """Validate if string is a valid role"""
    try:
        UserRole(role_str)
        return True
    except ValueError:
        return False

class PermissionContext:
    """Context manager for permission checking"""
    
    def __init__(self, user_role: str, user_permissions: List[str] = None):
        self.user_role = user_role
        self.user_permissions = user_permissions or []
        self.permission_manager = PermissionManager()
        self.checker = UserPermissionChecker(self.permission_manager)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if context user has permission"""
        return self.checker.check_user_permission(
            self.user_role, 
            permission, 
            self.user_permissions
        )
    
    def has_role(self, role: UserRole) -> bool:
        """Check if context user has role or higher"""
        try:
            current_role = UserRole(self.user_role)
            return PermissionManager.has_role_hierarchy(current_role, role)
        except ValueError:
            return False
    
    def can_access(self, resource_type: str, action: str) -> bool:
        """Check if context user can access resource"""
        return self.checker.can_access_resource(
            self.user_role,
            resource_type,
            action,
            self.user_permissions
        )
    
    def get_effective_permissions(self) -> Set[str]:
        """Get all effective permissions for context user"""
        return self.checker.get_user_effective_permissions(
            self.user_role,
            self.user_permissions
        )

class ResourcePermissionChecker:
    """Advanced permission checker for resource-specific permissions"""
    
    def __init__(self):
        self.logger = setup_logger("resource_permission_checker")
        self.permission_manager = PermissionManager()
    
    def check_content_access(self, 
                           user_role: str,
                           content_owner_id: int,
                           current_user_id: int,
                           action: str) -> bool:
        """Check content-specific access permissions"""
        try:
            role = UserRole(user_role)
            
            # Content owners can always access their own content
            if content_owner_id == current_user_id:
                owner_permissions = {
                    'read': True,
                    'update': True,
                    'delete': True
                }
                return owner_permissions.get(action, False)
            
            # Check role-based permissions for other users' content
            permission_map = {
                'read': Permission.READ_CONTENT,
                'update': Permission.UPDATE_CONTENT,
                'delete': Permission.DELETE_CONTENT,
                'publish': Permission.PUBLISH_CONTENT,
                'review': Permission.REVIEW_CONTENT
            }
            
            required_permission = permission_map.get(action)
            if not required_permission:
                return False
            
            return self.permission_manager.has_permission(role, required_permission)
            
        except Exception as e:
            self.logger.error(f"Content access check failed: {str(e)}")
            return False
    
    def check_user_management_access(self,
                                   manager_role: str,
                                   target_user_role: str,
                                   action: str) -> bool:
        """Check user management permissions with role hierarchy"""
        try:
            manager = UserRole(manager_role)
            target = UserRole(target_user_role)
            
            # Can't manage users of equal or higher role
            if get_user_role_level(target) >= get_user_role_level(manager):
                return False
            
            # Check if manager has user management permissions
            permission_map = {
                'read': Permission.READ_USER,
                'update': Permission.UPDATE_USER,
                'delete': Permission.DELETE_USER,
                'change_role': Permission.MANAGE_USER_ROLES
            }
            
            required_permission = permission_map.get(action)
            if not required_permission:
                return False
            
            return self.permission_manager.has_permission(manager, required_permission)
            
        except Exception as e:
            self.logger.error(f"User management access check failed: {str(e)}")
            return False

class PermissionAuditLogger:
    """Logger for permission-related events and access attempts"""
    
    def __init__(self):
        self.logger = setup_logger("permission_audit")
    
    def log_permission_check(self,
                           user_id: int,
                           user_role: str,
                           permission: str,
                           granted: bool,
                           resource: str = None,
                           context: Dict[str, Any] = None):
        """Log permission check event"""
        log_data = {
            'event': 'permission_check',
            'user_id': user_id,
            'user_role': user_role,
            'permission': permission,
            'granted': granted,
            'resource': resource,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        
        if granted:
            self.logger.info(f"Permission granted: {json.dumps(log_data)}")
        else:
            self.logger.warning(f"Permission denied: {json.dumps(log_data)}")
    
    def log_role_change(self,
                       admin_user_id: int,
                       target_user_id: int,
                       old_role: str,
                       new_role: str,
                       reason: str = None):
        """Log role change event"""
        log_data = {
            'event': 'role_change',
            'admin_user_id': admin_user_id,
            'target_user_id': target_user_id,
            'old_role': old_role,
            'new_role': new_role,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Role changed: {json.dumps(log_data)}")
    
    def log_unauthorized_access(self,
                              user_id: int,
                              attempted_action: str,
                              resource: str,
                              ip_address: str = None):
        """Log unauthorized access attempt"""
        log_data = {
            'event': 'unauthorized_access',
            'user_id': user_id,
            'attempted_action': attempted_action,
            'resource': resource,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.error(f"Unauthorized access attempt: {json.dumps(log_data)}")

# Example usage and integration
"""
# Initialize permission system
permission_manager = PermissionManager()

# Check basic permissions
user_role = UserRole.CREATOR
has_create_permission = permission_manager.has_permission(user_role, Permission.CREATE_CONTENT)
print(f"Creator can create content: {has_create_permission}")

# Create custom role
permission_manager.create_custom_role(
    name="Content Reviewer",
    description="Can review and approve content but not create",
    permissions=[
        Permission.READ_CONTENT,
        Permission.REVIEW_CONTENT,
        Permission.APPROVE_CONTENT,
        Permission.REJECT_CONTENT
    ],
    inherits_from=UserRole.USER
)

# Use permission context
with PermissionContext("creator", ["special_feature_access"]) as ctx:
    if ctx.has_permission(Permission.CREATE_CONTENT):
        print("User can create content")
    
    if ctx.can_access("content", "create"):
        print("User can create content via resource check")

# Resource-specific permission checking
resource_checker = ResourcePermissionChecker()
can_edit_content = resource_checker.check_content_access(
    user_role="moderator",
    content_owner_id=123,
    current_user_id=456,
    action="update"
)

# Permission auditing
audit_logger = PermissionAuditLogger()
audit_logger.log_permission_check(
    user_id=123,
    user_role="creator",
    permission="create_content",
    granted=True,
    resource="content/video"
)

# Export/Import role configuration
config = permission_manager.export_role_configuration()
with open('roles_config.json', 'w') as f:
    json.dump(config, f, indent=2)

# Import configuration
with open('roles_config.json', 'r') as f:
    imported_config = json.load(f)
permission_manager.import_role_configuration(imported_config)
"""