#!/usr/bin/env python3
"""
JWT Token Handler for AI Content Factory
ใช้สำหรับสร้าง verify และจัดการ JWT tokens
"""

import os
import sys
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid
import hashlib
import secrets

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.logger import setup_logger
from shared.utils.error_handler import ErrorHandler

class JWTHandler:
    """JWT token management class"""
    
    def __init__(self, 
                 secret_key: str = None,
                 algorithm: str = 'HS256',
                 access_token_expire: int = 30,  # minutes
                 refresh_token_expire: int = 7):  # days
        
        self.logger = setup_logger("jwt_handler")
        self.error_handler = ErrorHandler()
        
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', self._generate_secret_key())
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire
        self.refresh_token_expire_days = refresh_token_expire
        
        # Validate configuration
        self._validate_config()
        
        self.logger.info("JWT Handler initialized")
    
    def _generate_secret_key(self) -> str:
        """Generate a random secret key"""
        self.logger.warning("No JWT_SECRET_KEY provided, generating random key")
        return secrets.token_urlsafe(64)
    
    def _validate_config(self):
        """Validate JWT configuration"""
        if len(self.secret_key) < 32:
            self.logger.warning("JWT secret key is too short, consider using a longer key")
        
        if self.algorithm not in ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']:
            raise ValueError(f"Unsupported JWT algorithm: {self.algorithm}")
    
    def create_access_token(self, 
                          user_id: int,
                          email: str,
                          role: str,
                          permissions: List[str] = None,
                          additional_claims: Dict[str, Any] = None) -> str:
        """Create access token with user information"""
        try:
            now = datetime.utcnow()
            expire_time = now + timedelta(minutes=self.access_token_expire_minutes)
            
            # Standard JWT claims
            payload = {
                'iss': 'ai-content-factory',  # issuer
                'sub': str(user_id),         # subject (user_id)
                'aud': 'ai-content-factory-api',  # audience
                'iat': now,                  # issued at
                'exp': expire_time,          # expiration
                'nbf': now,                  # not before
                'jti': str(uuid.uuid4()),    # JWT ID (unique identifier)
                'typ': 'access'              # token type
            }
            
            # User-specific claims
            payload.update({
                'user_id': user_id,
                'email': email,
                'role': role,
                'permissions': permissions or [],
                'token_version': 1  # for token versioning/invalidation
            })
            
            # Add additional claims if provided
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            self.logger.debug(f"Access token created for user {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to create access token: {str(e)}")
            raise
    
    def create_refresh_token(self, 
                           user_id: int,
                           token_family: str = None) -> str:
        """Create refresh token for token renewal"""
        try:
            now = datetime.utcnow()
            expire_time = now + timedelta(days=self.refresh_token_expire_days)
            
            # Generate token family if not provided (for refresh token rotation)
            if not token_family:
                token_family = str(uuid.uuid4())
            
            payload = {
                'iss': 'ai-content-factory',
                'sub': str(user_id),
                'aud': 'ai-content-factory-api',
                'iat': now,
                'exp': expire_time,
                'nbf': now,
                'jti': str(uuid.uuid4()),
                'typ': 'refresh',
                'user_id': user_id,
                'token_family': token_family,
                'token_version': 1
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            self.logger.debug(f"Refresh token created for user {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to create refresh token: {str(e)}")
            raise
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience='ai-content-factory-api',
                issuer='ai-content-factory'
            )
            
            # Additional validation
            if not self._validate_payload(payload):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.debug("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.debug(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Token decode error: {str(e)}")
            return None
    
    def _validate_payload(self, payload: Dict[str, Any]) -> bool:
        """Validate token payload structure"""
        required_fields = ['user_id', 'typ', 'jti']
        
        for field in required_fields:
            if field not in payload:
                self.logger.warning(f"Missing required field in token: {field}")
                return False
        
        # Validate token type
        if payload['typ'] not in ['access', 'refresh']:
            self.logger.warning(f"Invalid token type: {payload['typ']}")
            return False
        
        return True
    
    def refresh_access_token(self, 
                           refresh_token: str,
                           user_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Create new access token using refresh token"""
        try:
            # Decode refresh token
            payload = self.decode_token(refresh_token)
            if not payload:
                return None
            
            # Validate it's a refresh token
            if payload.get('typ') != 'refresh':
                self.logger.warning("Attempted to refresh with non-refresh token")
                return None
            
            # Create new access token
            new_access_token = self.create_access_token(
                user_id=payload['user_id'],
                email=user_data['email'],
                role=user_data['role'],
                permissions=user_data.get('permissions', [])
            )
            
            # Optionally create new refresh token (refresh token rotation)
            new_refresh_token = self.create_refresh_token(
                user_id=payload['user_id'],
                token_family=payload.get('token_family')
            )
            
            self.logger.debug(f"Tokens refreshed for user {payload['user_id']}")
            
            return {
                'access_token': new_access_token,
                'refresh_token': new_refresh_token,
                'token_type': 'Bearer'
            }
            
        except Exception as e:
            self.logger.error(f"Token refresh failed: {str(e)}")
            return None
    
    def get_token_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token payload without validation (for inspection)"""
        try:
            # Decode without verification for inspection
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            self.logger.error(f"Failed to get token payload: {str(e)}")
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired"""
        try:
            payload = self.get_token_payload(token)
            if not payload:
                return True
            
            exp_timestamp = payload.get('exp')
            if not exp_timestamp:
                return True
            
            # Convert to datetime and compare
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            return datetime.utcnow() > exp_datetime
            
        except Exception:
            return True
    
    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """Get token expiration datetime"""
        try:
            payload = self.get_token_payload(token)
            if not payload:
                return None
            
            exp_timestamp = payload.get('exp')
            if not exp_timestamp:
                return None
            
            return datetime.fromtimestamp(exp_timestamp)
            
        except Exception:
            return None
    
    def get_token_remaining_time(self, token: str) -> Optional[timedelta]:
        """Get remaining time before token expires"""
        try:
            exp_datetime = self.get_token_expiration(token)
            if not exp_datetime:
                return None
            
            now = datetime.utcnow()
            if now > exp_datetime:
                return timedelta(0)  # Already expired
            
            return exp_datetime - now
            
        except Exception:
            return None
    
    def create_password_reset_token(self, user_id: int, email: str) -> str:
        """Create token for password reset"""
        try:
            now = datetime.utcnow()
            expire_time = now + timedelta(hours=1)  # 1 hour expiration
            
            payload = {
                'iss': 'ai-content-factory',
                'sub': str(user_id),
                'aud': 'password-reset',
                'iat': now,
                'exp': expire_time,
                'nbf': now,
                'jti': str(uuid.uuid4()),
                'typ': 'password_reset',
                'user_id': user_id,
                'email': email,
                'purpose': 'password_reset'
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            self.logger.debug(f"Password reset token created for user {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to create password reset token: {str(e)}")
            raise
    
    def create_email_verification_token(self, user_id: int, email: str) -> str:
        """Create token for email verification"""
        try:
            now = datetime.utcnow()
            expire_time = now + timedelta(days=1)  # 24 hours expiration
            
            payload = {
                'iss': 'ai-content-factory',
                'sub': str(user_id),
                'aud': 'email-verification',
                'iat': now,
                'exp': expire_time,
                'nbf': now,
                'jti': str(uuid.uuid4()),
                'typ': 'email_verification',
                'user_id': user_id,
                'email': email,
                'purpose': 'email_verification'
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            self.logger.debug(f"Email verification token created for user {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to create email verification token: {str(e)}")
            raise
    
    def validate_special_token(self, 
                             token: str, 
                             token_type: str, 
                             audience: str) -> Optional[Dict[str, Any]]:
        """Validate special purpose tokens (password reset, email verification)"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=audience,
                issuer='ai-content-factory'
            )
            
            # Validate token type
            if payload.get('typ') != token_type:
                self.logger.warning(f"Invalid token type for {token_type}")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.debug(f"{token_type} token has expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.debug(f"Invalid {token_type} token: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"{token_type} token validation error: {str(e)}")
            return None
    
    def create_api_key_token(self, 
                           user_id: int, 
                           api_key_name: str,
                           permissions: List[str] = None,
                           expire_days: int = 365) -> str:
        """Create long-lived API key token"""
        try:
            now = datetime.utcnow()
            expire_time = now + timedelta(days=expire_days)
            
            payload = {
                'iss': 'ai-content-factory',
                'sub': str(user_id),
                'aud': 'ai-content-factory-api',
                'iat': now,
                'exp': expire_time,
                'nbf': now,
                'jti': str(uuid.uuid4()),
                'typ': 'api_key',
                'user_id': user_id,
                'api_key_name': api_key_name,
                'permissions': permissions or [],
                'token_version': 1
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            self.logger.debug(f"API key token created for user {user_id}: {api_key_name}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to create API key token: {str(e)}")
            raise
    
    def generate_token_fingerprint(self, token: str) -> str:
        """Generate fingerprint for token tracking"""
        try:
            # Create hash of token for tracking without storing full token
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            return token_hash[:16]  # First 16 characters
        except Exception as e:
            self.logger.error(f"Failed to generate token fingerprint: {str(e)}")
            return ""
    
    def create_token_pair(self, 
                         user_id: int,
                         email: str,
                         role: str,
                         permissions: List[str] = None) -> Dict[str, str]:
        """Create access and refresh token pair"""
        try:
            access_token = self.create_access_token(
                user_id=user_id,
                email=email,
                role=role,
                permissions=permissions
            )
            
            refresh_token = self.create_refresh_token(user_id=user_id)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': self.access_token_expire_minutes * 60,  # seconds
                'refresh_expires_in': self.refresh_token_expire_days * 24 * 60 * 60  # seconds
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create token pair: {str(e)}")
            raise

class TokenBlacklist:
    """Token blacklist management using Redis or in-memory storage"""
    
    def __init__(self, redis_client=None):
        self.logger = setup_logger("token_blacklist")
        self.redis_client = redis_client
        self.memory_blacklist = set()  # Fallback for when Redis is not available
    
    def add_token(self, token: str, expire_seconds: int = None):
        """Add token to blacklist"""
        try:
            if self.redis_client:
                # Use Redis for persistent blacklist
                expire_seconds = expire_seconds or (24 * 60 * 60)  # 24 hours default
                self.redis_client.setex(f"blacklist:{token}", expire_seconds, "1")
                self.logger.debug("Token added to Redis blacklist")
            else:
                # Use in-memory blacklist
                self.memory_blacklist.add(token)
                self.logger.debug("Token added to memory blacklist")
                
        except Exception as e:
            self.logger.error(f"Failed to add token to blacklist: {str(e)}")
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(f"blacklist:{token}"))
            else:
                return token in self.memory_blacklist
                
        except Exception as e:
            self.logger.error(f"Failed to check token blacklist: {str(e)}")
            return False
    
    def remove_token(self, token: str):
        """Remove token from blacklist"""
        try:
            if self.redis_client:
                self.redis_client.delete(f"blacklist:{token}")
                self.logger.debug("Token removed from Redis blacklist")
            else:
                self.memory_blacklist.discard(token)
                self.logger.debug("Token removed from memory blacklist")
                
        except Exception as e:
            self.logger.error(f"Failed to remove token from blacklist: {str(e)}")
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens from memory blacklist"""
        if not self.redis_client:
            # For memory blacklist, we can't easily track expiration
            # This would need additional logic to track expiration times
            pass

class TokenValidator:
    """Additional token validation utilities"""
    
    def __init__(self, jwt_handler: JWTHandler):
        self.jwt_handler = jwt_handler
        self.logger = setup_logger("token_validator")
    
    def validate_token_structure(self, token: str) -> Dict[str, Any]:
        """Validate token structure and return detailed information"""
        result = {
            'valid': False,
            'expired': False,
            'malformed': False,
            'payload': None,
            'error': None
        }
        
        try:
            # First check if token is structurally valid
            payload = self.jwt_handler.get_token_payload(token)
            if not payload:
                result['malformed'] = True
                result['error'] = 'Token is malformed'
                return result
            
            result['payload'] = payload
            
            # Check if expired
            if self.jwt_handler.is_token_expired(token):
                result['expired'] = True
                result['error'] = 'Token has expired'
                return result
            
            # Validate signature
            validated_payload = self.jwt_handler.decode_token(token)
            if validated_payload:
                result['valid'] = True
            else:
                result['error'] = 'Token signature is invalid'
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """Get comprehensive token information"""
        try:
            payload = self.jwt_handler.get_token_payload(token)
            if not payload:
                return {'error': 'Invalid token'}
            
            exp_datetime = self.jwt_handler.get_token_expiration(token)
            remaining_time = self.jwt_handler.get_token_remaining_time(token)
            
            return {
                'token_id': payload.get('jti'),
                'user_id': payload.get('user_id'),
                'email': payload.get('email'),
                'role': payload.get('role'),
                'permissions': payload.get('permissions', []),
                'token_type': payload.get('typ'),
                'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
                'expires_at': exp_datetime,
                'remaining_time_seconds': remaining_time.total_seconds() if remaining_time else 0,
                'is_expired': self.jwt_handler.is_token_expired(token)
            }
            
        except Exception as e:
            return {'error': str(e)}

# Utility functions for common JWT operations

def create_jwt_handler(config: Dict[str, Any] = None) -> JWTHandler:
    """Factory function to create JWT handler with configuration"""
    if not config:
        config = {}
    
    return JWTHandler(
        secret_key=config.get('secret_key'),
        algorithm=config.get('algorithm', 'HS256'),
        access_token_expire=config.get('access_token_expire_minutes', 30),
        refresh_token_expire=config.get('refresh_token_expire_days', 7)
    )

def extract_user_from_token(token: str, jwt_handler: JWTHandler) -> Optional[Dict[str, Any]]:
    """Extract user information from token"""
    try:
        payload = jwt_handler.decode_token(token)
        if not payload:
            return None
        
        return {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role'),
            'permissions': payload.get('permissions', [])
        }
    except Exception:
        return None

# Example usage
"""
# Initialize JWT handler
jwt_handler = JWTHandler(
    secret_key='your-secret-key',
    access_token_expire=30,  # 30 minutes
    refresh_token_expire=7   # 7 days
)

# Create tokens
tokens = jwt_handler.create_token_pair(
    user_id=123,
    email='user@example.com',
    role='user',
    permissions=['read_content', 'create_content']
)

# Validate token
payload = jwt_handler.decode_token(tokens['access_token'])
if payload:
    print(f"Valid token for user: {payload['email']}")

# Refresh tokens
user_data = {
    'email': 'user@example.com',
    'role': 'user',
    'permissions': ['read_content', 'create_content']
}
new_tokens = jwt_handler.refresh_access_token(
    tokens['refresh_token'], 
    user_data
)

# Create special purpose tokens
reset_token = jwt_handler.create_password_reset_token(123, 'user@example.com')
verify_token = jwt_handler.create_email_verification_token(123, 'user@example.com')

# Validate special tokens
reset_payload = jwt_handler.validate_special_token(
    reset_token, 
    'password_reset', 
    'password-reset'
)
"""