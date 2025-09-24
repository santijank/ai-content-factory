#!/usr/bin/env python3
"""
Authentication Middleware for AI Content Factory
ใช้สำหรับตรวจสอบ authentication และ authorization ในทุก API requests
"""

import os
import sys
import functools
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from flask import Flask, request, jsonify, g, current_app
from werkzeug.exceptions import Unauthorized, Forbidden
import jwt
import redis
from functools import wraps

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.logger import setup_logger
from shared.utils.error_handler import ErrorHandler
from auth.jwt_handler import JWTHandler
from auth.permissions import PermissionManager, UserRole, Permission

class AuthenticationMiddleware:
    """Main authentication middleware class"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.logger = setup_logger("auth_middleware")
        self.error_handler = ErrorHandler()
        self.jwt_handler = None
        self.permission_manager = None
        self.redis_client = None
        
        if app:
            self.init_app(app, config)
    
    def init_app(self, app: Flask, config: Dict[str, Any] = None):
        """Initialize middleware with Flask app"""
        self.app = app
        self.config = config or self._load_default_config()
        
        # Initialize components
        self.jwt_handler = JWTHandler(
            secret_key=self.config['jwt']['secret_key'],
            algorithm=self.config['jwt']['algorithm'],
            access_token_expire=self.config['jwt']['access_token_expire_minutes'],
            refresh_token_expire=self.config['jwt']['refresh_token_expire_days']
        )
        
        self.permission_manager = PermissionManager()
        
        # Initialize Redis for token blacklist (optional)
        if self.config['redis']['enabled']:
            try:
                self.redis_client = redis.Redis(
                    host=self.config['redis']['host'],
                    port=self.config['redis']['port'],
                    db=self.config['redis']['db'],
                    decode_responses=True
                )
                self.redis_client.ping()
                self.logger.info("Redis connected for token blacklist")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {str(e)} - token blacklist disabled")
                self.redis_client = None
        
        # Register middleware
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Add error handlers
        app.errorhandler(401)(self.handle_unauthorized)
        app.errorhandler(403)(self.handle_forbidden)
        
        self.logger.info("Authentication middleware initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'jwt': {
                'secret_key': os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production'),
                'algorithm': 'HS256',
                'access_token_expire_minutes': 30,
                'refresh_token_expire_days': 7
            },
            'redis': {
                'enabled': os.getenv('REDIS_ENABLED', 'false').lower() == 'true',
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0))
            },
            'auth': {
                'public_endpoints': [
                    '/auth/login',
                    '/auth/register',
                    '/auth/refresh',
                    '/health',
                    '/docs',
                    '/static'
                ],
                'require_auth_by_default': True,
                'token_header': 'Authorization',
                'token_prefix': 'Bearer',
                'rate_limiting': {
                    'enabled': True,
                    'max_requests_per_minute': 60
                }
            }
        }
    
    def before_request(self):
        """Process request before handling"""
        try:
            # Skip authentication for public endpoints
            if self._is_public_endpoint(request.endpoint, request.path):
                return
            
            # Rate limiting
            if self.config['auth']['rate_limiting']['enabled']:
                if not self._check_rate_limit():
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': 'Too many requests'
                    }), 429
            
            # Extract and validate token
            token = self._extract_token()
            if not token:
                return jsonify({
                    'error': 'Missing token',
                    'message': 'Authorization token is required'
                }), 401
            
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Token has been revoked'
                }), 401
            
            # Decode and validate token
            payload = self.jwt_handler.decode_token(token)
            if not payload:
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Token is invalid or expired'
                }), 401
            
            # Set current user context
            g.current_user = payload
            g.user_id = payload.get('user_id')
            g.user_role = payload.get('role', UserRole.USER.value)
            g.permissions = payload.get('permissions', [])
            
            # Log successful authentication
            self.logger.debug(f"Authenticated user {g.user_id} with role {g.user_role}")
            
        except Exception as e:
            self.logger.error(f"Authentication middleware error: {str(e)}")
            return jsonify({
                'error': 'Authentication error',
                'message': 'Internal authentication error'
            }), 500
    
    def after_request(self, response):
        """Process response after handling"""
        try:
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Add CORS headers if needed
            if hasattr(g, 'current_user'):
                response.headers['X-User-ID'] = str(g.user_id)
            
            return response
            
        except Exception as e:
            self.logger.error(f"After request middleware error: {str(e)}")
            return response
    
    def _is_public_endpoint(self, endpoint: str, path: str) -> bool:
        """Check if endpoint is public (doesn't require authentication)"""
        public_endpoints = self.config['auth']['public_endpoints']
        
        # Check exact endpoint match
        if endpoint in public_endpoints:
            return True
        
        # Check path prefix match
        for public_path in public_endpoints:
            if path.startswith(public_path):
                return True
        
        return False
    
    def _extract_token(self) -> Optional[str]:
        """Extract JWT token from request headers"""
        auth_header = request.headers.get(self.config['auth']['token_header'])
        
        if not auth_header:
            return None
        
        # Check for Bearer token format
        token_prefix = self.config['auth']['token_prefix']
        if not auth_header.startswith(f"{token_prefix} "):
            return None
        
        return auth_header[len(token_prefix) + 1:]
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is in blacklist (Redis)"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(f"blacklist:{token}")
        except Exception as e:
            self.logger.warning(f"Redis blacklist check failed: {str(e)}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check rate limiting per IP"""
        if not self.redis_client:
            return True  # Skip rate limiting if Redis not available
        
        try:
            client_ip = request.remote_addr
            key = f"rate_limit:{client_ip}"
            
            # Get current request count
            current_requests = self.redis_client.get(key)
            max_requests = self.config['auth']['rate_limiting']['max_requests_per_minute']
            
            if current_requests is None:
                # First request from this IP
                self.redis_client.setex(key, 60, 1)
                return True
            
            if int(current_requests) >= max_requests:
                return False
            
            # Increment counter
            self.redis_client.incr(key)
            return True
            
        except Exception as e:
            self.logger.warning(f"Rate limiting check failed: {str(e)}")
            return True  # Allow request if rate limiting fails
    
    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'code': 401
        }), 401
    
    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'Insufficient permissions',
            'code': 403
        }), 403
    
    def blacklist_token(self, token: str, expire_seconds: int = None):
        """Add token to blacklist"""
        if not self.redis_client:
            self.logger.warning("Cannot blacklist token: Redis not available")
            return False
        
        try:
            expire_seconds = expire_seconds or (24 * 60 * 60)  # 24 hours default
            self.redis_client.setex(f"blacklist:{token}", expire_seconds, "1")
            self.logger.info("Token blacklisted successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to blacklist token: {str(e)}")
            return False

# Decorators for authentication and authorization

def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this resource'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def require_role(required_role: UserRole):
    """Decorator to require specific role for a route"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401
            
            user_role = UserRole(g.user_role)
            if not PermissionManager.has_role_hierarchy(user_role, required_role):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'This action requires {required_role.value} role'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permission(required_permission: Permission):
    """Decorator to require specific permission for a route"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401
            
            user_permissions = g.permissions
            if required_permission.value not in user_permissions:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'This action requires {required_permission.value} permission'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permissions(required_permissions: List[Permission], require_all: bool = True):
    """Decorator to require multiple permissions for a route"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401
            
            user_permissions = set(g.permissions)
            required_perms = set(perm.value for perm in required_permissions)
            
            if require_all:
                # User must have ALL required permissions
                if not required_perms.issubset(user_permissions):
                    missing_perms = required_perms - user_permissions
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'Missing required permissions: {", ".join(missing_perms)}'
                    }), 403
            else:
                # User must have AT LEAST ONE required permission
                if not required_perms.intersection(user_permissions):
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'Requires one of: {", ".join(required_perms)}'
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_own_resource(resource_user_id_param: str = 'user_id'):
    """Decorator to ensure user can only access their own resources"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401
            
            # Allow admins to access any resource
            user_role = UserRole(g.user_role)
            if user_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                return f(*args, **kwargs)
            
            # Check if user is accessing their own resource
            resource_user_id = kwargs.get(resource_user_id_param) or request.json.get(resource_user_id_param)
            
            if resource_user_id and str(resource_user_id) != str(g.user_id):
                return jsonify({
                    'error': 'Access denied',
                    'message': 'You can only access your own resources'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage examples and helper functions

def get_current_user() -> Dict[str, Any]:
    """Get current authenticated user from request context"""
    if hasattr(g, 'current_user'):
        return g.current_user
    return None

def get_current_user_id() -> Optional[int]:
    """Get current user ID from request context"""
    if hasattr(g, 'user_id'):
        return g.user_id
    return None

def get_current_user_role() -> Optional[UserRole]:
    """Get current user role from request context"""
    if hasattr(g, 'user_role'):
        return UserRole(g.user_role)
    return None

def get_current_user_permissions() -> List[str]:
    """Get current user permissions from request context"""
    if hasattr(g, 'permissions'):
        return g.permissions
    return []

def has_permission(permission: Permission) -> bool:
    """Check if current user has specific permission"""
    user_permissions = get_current_user_permissions()
    return permission.value in user_permissions

def has_role(role: UserRole) -> bool:
    """Check if current user has specific role or higher"""
    current_role = get_current_user_role()
    if not current_role:
        return False
    return PermissionManager.has_role_hierarchy(current_role, role)

# Security utilities

def generate_csrf_token() -> str:
    """Generate CSRF token for form protection"""
    import secrets
    return secrets.token_urlsafe(32)

def validate_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token"""
    import hmac
    return hmac.compare_digest(token, session_token)

# Example Flask app integration
"""
from flask import Flask
from auth.middleware import AuthenticationMiddleware

app = Flask(__name__)

# Initialize authentication middleware
auth_config = {
    'jwt': {
        'secret_key': 'your-secret-key',
        'access_token_expire_minutes': 30
    },
    'auth': {
        'public_endpoints': ['/auth/login', '/auth/register', '/health']
    }
}

auth_middleware = AuthenticationMiddleware(app, auth_config)

@app.route('/protected')
@require_auth
def protected_route():
    return jsonify({'message': 'This is a protected route'})

@app.route('/admin-only')
@require_role(UserRole.ADMIN)
def admin_only_route():
    return jsonify({'message': 'Admin only route'})

@app.route('/create-content')
@require_permission(Permission.CREATE_CONTENT)
def create_content_route():
    return jsonify({'message': 'Content creation route'})
"""