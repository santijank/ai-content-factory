"""
Error Handler Module
จัดการ errors, exceptions และ retry logic สำหรับระบบ AI Content Factory
"""

import logging
import traceback
import asyncio
import functools
from typing import Dict, Any, Optional, Callable, Union, Type
from datetime import datetime, timedelta
from enum import Enum
import json
import time

# Custom Exception Classes
class ContentFactoryError(Exception):
    """Base exception สำหรับ AI Content Factory"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

class AIServiceError(ContentFactoryError):
    """Exception สำหรับ AI Service errors"""
    pass

class TrendCollectionError(ContentFactoryError):
    """Exception สำหรับ Trend Collection errors"""
    pass

class ContentGenerationError(ContentFactoryError):
    """Exception สำหรับ Content Generation errors"""
    pass

class PlatformUploadError(ContentFactoryError):
    """Exception สำหรับ Platform Upload errors"""
    pass

class DatabaseError(ContentFactoryError):
    """Exception สำหรับ Database errors"""
    pass

class RateLimitError(ContentFactoryError):
    """Exception สำหรับ Rate Limit errors"""
    pass

class ConfigurationError(ContentFactoryError):
    """Exception สำหรับ Configuration errors"""
    pass

# Error Severity Levels
class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorHandler:
    """
    Centralized Error Handler สำหรับระบบ AI Content Factory
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.last_errors = {}
        self.recovery_strategies = {}
        self._setup_recovery_strategies()
    
    def _setup_recovery_strategies(self):
        """กำหนด recovery strategies สำหรับแต่ละประเภท error"""
        self.recovery_strategies = {
            "RATE_LIMIT": self._handle_rate_limit,
            "API_TIMEOUT": self._handle_api_timeout,
            "AUTH_ERROR": self._handle_auth_error,
            "QUOTA_EXCEEDED": self._handle_quota_exceeded,
            "NETWORK_ERROR": self._handle_network_error,
            "DATABASE_ERROR": self._handle_database_error,
            "CONTENT_GENERATION_FAILED": self._handle_content_generation_error
        }
    
    def handle_error(self, 
                    error: Exception, 
                    context: Dict[str, Any] = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    should_retry: bool = True,
                    max_retries: int = 3) -> Dict[str, Any]:
        """
        หลัก method สำหรับจัดการ error
        """
        context = context or {}
        error_info = self._extract_error_info(error, context, severity)
        
        # Log error
        self._log_error(error_info)
        
        # Track error statistics
        self._track_error(error_info)
        
        # พยายาม recover ถ้าทำได้
        recovery_result = None
        if should_retry and error_info['error_code'] in self.recovery_strategies:
            recovery_result = self._attempt_recovery(error_info, max_retries)
        
        # Return structured error response
        return {
            "success": False,
            "error": {
                "code": error_info['error_code'],
                "message": error_info['message'],
                "severity": severity.value,
                "timestamp": error_info['timestamp'].isoformat(),
                "context": context,
                "recovery_attempted": recovery_result is not None,
                "recovery_success": recovery_result.get('success', False) if recovery_result else False
            }
        }
    
    def _extract_error_info(self, error: Exception, context: Dict, severity: ErrorSeverity) -> Dict:
        """แยกข้อมูล error ออกมาเป็น structured format"""
        error_code = "UNKNOWN_ERROR"
        message = str(error)
        
        # Determine error code from exception type and message
        if isinstance(error, AIServiceError):
            error_code = "AI_SERVICE_ERROR"
        elif isinstance(error, TrendCollectionError):
            error_code = "TREND_COLLECTION_ERROR"
        elif isinstance(error, ContentGenerationError):
            error_code = "CONTENT_GENERATION_ERROR"
        elif isinstance(error, PlatformUploadError):
            error_code = "PLATFORM_UPLOAD_ERROR"
        elif isinstance(error, DatabaseError):
            error_code = "DATABASE_ERROR"
        elif isinstance(error, RateLimitError):
            error_code = "RATE_LIMIT"
        elif isinstance(error, ConfigurationError):
            error_code = "CONFIGURATION_ERROR"
        elif "timeout" in message.lower():
            error_code = "API_TIMEOUT"
        elif "unauthorized" in message.lower() or "auth" in message.lower():
            error_code = "AUTH_ERROR"
        elif "quota" in message.lower() or "limit" in message.lower():
            error_code = "QUOTA_EXCEEDED"
        elif "network" in message.lower() or "connection" in message.lower():
            error_code = "NETWORK_ERROR"
        
        return {
            "error_code": error_code,
            "message": message,
            "exception_type": type(error).__name__,
            "traceback": traceback.format_exc(),
            "context": context,
            "severity": severity,
            "timestamp": datetime.utcnow()
        }
    
    def _log_error(self, error_info: Dict):
        """Log error ตาม severity level"""
        log_message = f"[{error_info['error_code']}] {error_info['message']}"
        
        if error_info['severity'] == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=error_info)
        elif error_info['severity'] == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=error_info)
        elif error_info['severity'] == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=error_info)
        else:
            self.logger.info(log_message, extra=error_info)
    
    def _track_error(self, error_info: Dict):
        """Track error statistics"""
        error_code = error_info['error_code']
        
        # Count errors
        if error_code not in self.error_counts:
            self.error_counts[error_code] = 0
        self.error_counts[error_code] += 1
        
        # Store last occurrence
        self.last_errors[error_code] = error_info['timestamp']
    
    def _attempt_recovery(self, error_info: Dict, max_retries: int) -> Dict:
        """พยายาม recover จาก error"""
        error_code = error_info['error_code']
        recovery_func = self.recovery_strategies.get(error_code)
        
        if not recovery_func:
            return {"success": False, "message": "No recovery strategy available"}
        
        try:
            return recovery_func(error_info, max_retries)
        except Exception as e:
            self.logger.error(f"Recovery failed for {error_code}: {str(e)}")
            return {"success": False, "message": f"Recovery failed: {str(e)}"}
    
    # Recovery Strategy Methods
    def _handle_rate_limit(self, error_info: Dict, max_retries: int) -> Dict:
        """Handle rate limit errors"""
        wait_time = self._extract_wait_time(error_info['message'])
        if wait_time:
            self.logger.info(f"Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            return {"success": True, "action": f"waited_{wait_time}s"}
        return {"success": False, "message": "Could not determine wait time"}
    
    def _handle_api_timeout(self, error_info: Dict, max_retries: int) -> Dict:
        """Handle API timeout errors"""
        # Exponential backoff
        wait_time = min(60, 2 ** (max_retries - 1))
        self.logger.info(f"API timeout. Retrying after {wait_time}s...")
        time.sleep(wait_time)
        return {"success": True, "action": f"backoff_{wait_time}s"}
    
    def _handle_auth_error(self, error_info: Dict, max_retries: int) -> Dict:
        """Handle authentication errors"""
        # Log for manual intervention
        self.logger.error("Authentication error detected. Manual intervention required.")
        return {"success": False, "message": "Manual authentication required"}
    
    def _handle_quota_exceeded(self, error_info: Dict, max_retries: int) -> Dict:
        """Handle quota exceeded errors"""
        # Switch to lower tier service if possible
        context = error_info['context']
        if 'service_tier' in context and context['service_tier'] != 'budget':
            self.logger.info("Quota exceeded. Switching to budget tier...")
            return {"success": True, "action": "switched_to_budget_tier"}
        return {"success": False, "message": "No fallback service available"}
    
    def _handle_network_error(self, error_info: Dict, max_retries: int) -> Dict:
        """Handle network errors"""
        wait_time = min(30, 5 * max_retries)
        self.logger.info(f"Network error. Retrying after {wait_time}s...")
        time.sleep(wait_time)
        return {"success": True, "action": f"network_retry_{wait_time}s"}
    
    def _handle_database_error(self, error_info: Dict, max_retries: int) -> Dict:
        """Handle database errors"""
        # Basic retry with exponential backoff
        wait_time = min(10, 2 ** (max_retries - 1))
        time.sleep(wait_time)
        return {"success": True, "action": f"db_retry_{wait_time}s"}
    
    def _handle_content_generation_error(self, error_info: Dict, max_retries: int) -> Dict:
        """Handle content generation errors"""
        context = error_info['context']
        if 'fallback_prompt' in context:
            self.logger.info("Content generation failed. Trying fallback prompt...")
            return {"success": True, "action": "fallback_prompt"}
        return {"success": False, "message": "No fallback strategy"}
    
    def _extract_wait_time(self, error_message: str) -> Optional[int]:
        """Extract wait time from rate limit error message"""
        import re
        # Try to find numbers in error message
        numbers = re.findall(r'\d+', error_message.lower())
        if numbers:
            # Return the first number found (usually retry-after seconds)
            return min(int(numbers[0]), 300)  # Cap at 5 minutes
        return None
    
    def get_error_statistics(self) -> Dict:
        """Get error statistics"""
        return {
            "error_counts": dict(self.error_counts),
            "last_errors": {
                code: timestamp.isoformat() 
                for code, timestamp in self.last_errors.items()
            },
            "total_errors": sum(self.error_counts.values())
        }
    
    def reset_error_statistics(self):
        """Reset error statistics"""
        self.error_counts.clear()
        self.last_errors.clear()

# Decorator Functions
def handle_errors(error_handler: ErrorHandler = None, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 max_retries: int = 3):
    """
    Decorator สำหรับ handle errors automatically
    """
    if error_handler is None:
        error_handler = ErrorHandler()
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        # Last attempt - handle error and re-raise
                        context = {
                            "function": func.__name__,
                            "args": str(args),
                            "kwargs": str(kwargs),
                            "attempt": attempt + 1
                        }
                        error_result = error_handler.handle_error(
                            e, context, severity, should_retry=False
                        )
                        raise e
                    else:
                        # Retry attempt
                        context = {
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries
                        }
                        error_handler.handle_error(
                            e, context, ErrorSeverity.LOW, should_retry=True
                        )
                        time.sleep(2 ** attempt)  # Exponential backoff
            
        return wrapper
    return decorator

def handle_async_errors(error_handler: ErrorHandler = None,
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                       max_retries: int = 3):
    """
    Decorator สำหรับ handle async errors automatically
    """
    if error_handler is None:
        error_handler = ErrorHandler()
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        context = {
                            "function": func.__name__,
                            "args": str(args),
                            "kwargs": str(kwargs),
                            "attempt": attempt + 1
                        }
                        error_result = error_handler.handle_error(
                            e, context, severity, should_retry=False
                        )
                        raise e
                    else:
                        context = {
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries
                        }
                        error_handler.handle_error(
                            e, context, ErrorSeverity.LOW, should_retry=True
                        )
                        await asyncio.sleep(2 ** attempt)
            
        return wrapper
    return decorator

# Global Error Handler Instance
global_error_handler = ErrorHandler()

# Convenience Functions
def handle_error(error: Exception, 
                context: Dict = None,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict:
    """Convenience function สำหรับ handle error"""
    return global_error_handler.handle_error(error, context, severity)

def get_error_stats() -> Dict:
    """Convenience function สำหรับ get error statistics"""
    return global_error_handler.get_error_statistics()

def reset_error_stats():
    """Convenience function สำหรับ reset error statistics"""
    global_error_handler.reset_error_statistics()

# Example Usage
if __name__ == "__main__":
    # Test error handling
    handler = ErrorHandler()
    
    try:
        raise AIServiceError("Test AI service error", "AI_TEST_ERROR")
    except Exception as e:
        result = handler.handle_error(e, {"test": True}, ErrorSeverity.HIGH)
        print(json.dumps(result, indent=2))
    
    print("Error Statistics:", handler.get_error_statistics())