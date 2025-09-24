"""
Advanced Logging System for AI Content Factory
รองรับ structured logging, multiple outputs และ log analysis
"""

import logging
import logging.handlers
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
from enum import Enum


class LogLevel(Enum):
    """Log levels with emoji indicators"""
    DEBUG = ("DEBUG", "🔍")
    INFO = ("INFO", "ℹ️")
    WARNING = ("WARNING", "⚠️")
    ERROR = ("ERROR", "❌")
    CRITICAL = ("CRITICAL", "💥")


class StructuredFormatter(logging.Formatter):
    """Custom formatter สำหรับ structured logging"""
    
    def __init__(self, use_color: bool = True, use_emoji: bool = True):
        super().__init__()
        self.use_color = use_color
        self.use_emoji = use_emoji
        
        # Color codes
        self.colors = {
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Green  
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[35m',  # Magenta
            'RESET': '\033[0m'       # Reset
        }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structure and color"""
        
        # เพิ่ม correlation ID ถ้าไม่มี
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = str(uuid.uuid4())[:8]
        
        # เพิ่ม component name
        if not hasattr(record, 'component'):
            record.component = record.name
        
        # Get emoji for level
        emoji = ""
        if self.use_emoji:
            for level in LogLevel:
                if level.value[0] == record.levelname:
                    emoji = level.value[1] + " "
                    break
        
        # Get color for level
        color_start = ""
        color_end = ""
        if self.use_color and sys.stdout.isatty():
            color_start = self.colors.get(record.levelname, '')
            color_end = self.colors['RESET']
        
        # Build structured message
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Base format
        formatted = (
            f"{color_start}{emoji}"
            f"[{timestamp}] "
            f"{record.levelname:8} "
            f"[{record.component}] "
            f"[{record.correlation_id}] "
            f"{record.getMessage()}"
            f"{color_end}"
        )
        
        # เพิ่ม exception info ถ้ามี
        if record.exc_info:
            formatted += f"\n{color_start}Exception: {self.formatException(record.exc_info)}{color_end}"
        
        # เพิ่ม extra fields ถ้ามี
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            formatted += f"\n{color_start}Extra: {json.dumps(extra_fields, indent=2)}{color_end}"
        
        return formatted
    
    def _get_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """ดึง extra fields จาก log record"""
        skip_keys = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'message', 'exc_info',
            'exc_text', 'stack_info', 'correlation_id', 'component'
        }
        
        extra = {}
        for key, value in record.__dict__.items():
            if key not in skip_keys and not key.startswith('_'):
                extra[key] = value
        
        return extra


class JSONFormatter(logging.Formatter):
    """JSON formatter สำหรับ machine-readable logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format record as JSON"""
        
        # เพิ่ม correlation ID ถ้าไม่มี
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = str(uuid.uuid4())[:8]
        
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'component': getattr(record, 'component', record.name),
            'correlation_id': record.correlation_id,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # เพิ่ม exception info ถ้ามี
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # เพิ่ม extra fields
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            log_data['extra'] = extra_fields
        
        return json.dumps(log_data, ensure_ascii=False)
    
    def _get_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """ดึง extra fields จาก log record"""
        skip_keys = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'message', 'exc_info',
            'exc_text', 'stack_info', 'correlation_id', 'component'
        }
        
        extra = {}
        for key, value in record.__dict__.items():
            if key not in skip_keys and not key.startswith('_'):
                try:
                    # ตรวจสอบว่า value serializable ไหม
                    json.dumps(value)
                    extra[key] = value
                except (TypeError, ValueError):
                    extra[key] = str(value)
        
        return extra


class PerformanceFilter(logging.Filter):
    """Filter สำหรับ track performance metrics"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """เพิ่ม performance metrics ใน log record"""
        
        # เพิ่ม memory usage ถ้ามี psutil
        try:
            import psutil
            process = psutil.Process()
            record.memory_mb = round(process.memory_info().rss / 1024 / 1024, 2)
        except ImportError:
            record.memory_mb = None
        
        return True


class ContentFactoryLogger:
    """Main logger class สำหรับ AI Content Factory"""
    
    def __init__(self, 
                 name: str,
                 level: str = "INFO",
                 log_dir: str = "logs",
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 use_json: bool = False,
                 use_color: bool = True,
                 use_emoji: bool = True):
        
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # สร้าง logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # เคลียร์ handlers เก่า
        self.logger.handlers.clear()
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if use_json:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                StructuredFormatter(use_color=use_color, use_emoji=use_emoji)
            )
        
        self.logger.addHandler(console_handler)
        
        # File Handler (Always JSON for files)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / f"{name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JSONFormatter())
        
        # Error File Handler
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / f"{name}.error.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        
        # เพิ่ม Performance Filter
        perf_filter = PerformanceFilter()
        console_handler.addFilter(perf_filter)
        file_handler.addFilter(perf_filter)
        error_handler.addFilter(perf_filter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def get_logger(self) -> logging.Logger:
        """ดึง logger instance"""
        return self.logger
    
    def debug(self, message: str, **kwargs):
        """Log debug message with extra fields"""
        self._log_with_extra(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with extra fields"""
        self._log_with_extra(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with extra fields"""
        self._log_with_extra(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with extra fields"""
        self._log_with_extra(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with extra fields"""
        self._log_with_extra(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        kwargs['exc_info'] = True
        self._log_with_extra(logging.ERROR, message, **kwargs)
    
    def _log_with_extra(self, level: int, message: str, **kwargs):
        """Log message with extra fields"""
        
        # แยก correlation_id และ component ออก
        correlation_id = kwargs.pop('correlation_id', None)
        component = kwargs.pop('component', None)
        exc_info = kwargs.pop('exc_info', None)
        
        # สร้าง extra dict สำหรับ fields อื่นๆ
        extra = {}
        if correlation_id:
            extra['correlation_id'] = correlation_id
        if component:
            extra['component'] = component
        
        # เพิ่ม kwargs อื่นๆ เข้า extra
        extra.update(kwargs)
        
        self.logger.log(level, message, extra=extra, exc_info=exc_info)


# Global logger instances
_loggers: Dict[str, ContentFactoryLogger] = {}


def setup_logger(name: str, 
                level: str = "INFO",
                log_dir: str = "logs",
                use_json: bool = False,
                use_color: bool = True,
                use_emoji: bool = True) -> ContentFactoryLogger:
    """Setup หรือดึง logger instance"""
    
    if name not in _loggers:
        _loggers[name] = ContentFactoryLogger(
            name=name,
            level=level,
            log_dir=log_dir,
            use_json=use_json,
            use_color=use_color,
            use_emoji=use_emoji
        )
    
    return _loggers[name]


def get_logger(name: str) -> Optional[ContentFactoryLogger]:
    """ดึง existing logger"""
    return _loggers.get(name)


class LogContext:
    """Context manager สำหรับ correlation ID"""
    
    def __init__(self, logger: ContentFactoryLogger, correlation_id: str = None, **context):
        self.logger = logger
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]
        self.context = context
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.error(f"Exception in context: {exc_val}", exception_type=exc_type.__name__)
    
    def debug(self, message: str, **kwargs):
        kwargs.update(self.context)
        self.logger.debug(message, correlation_id=self.correlation_id, **kwargs)
    
    def info(self, message: str, **kwargs):
        kwargs.update(self.context)
        self.logger.info(message, correlation_id=self.correlation_id, **kwargs)
    
    def warning(self, message: str, **kwargs):
        kwargs.update(self.context)
        self.logger.warning(message, correlation_id=self.correlation_id, **kwargs)
    
    def error(self, message: str, **kwargs):
        kwargs.update(self.context)
        self.logger.error(message, correlation_id=self.correlation_id, **kwargs)
    
    def critical(self, message: str, **kwargs):
        kwargs.update(self.context)
        self.logger.critical(message, correlation_id=self.correlation_id, **kwargs)


# Performance logging utilities
class PerformanceLogger:
    """Logger สำหรับ performance metrics"""
    
    def __init__(self, logger: ContentFactoryLogger):
        self.logger = logger
    
    def log_api_call(self, 
                    endpoint: str, 
                    method: str, 
                    duration_ms: float,
                    status_code: int = None,
                    **kwargs):
        """Log API call performance"""
        self.logger.info(
            f"API call completed",
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
            status_code=status_code,
            **kwargs
        )
    
    def log_ai_generation(self,
                         model: str,
                         prompt_tokens: int,
                         completion_tokens: int,
                         duration_ms: float,
                         cost_usd: float = None,
                         **kwargs):
        """Log AI generation performance"""
        self.logger.info(
            f"AI generation completed",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
            **kwargs
        )
    
    def log_content_creation(self,
                           content_type: str,
                           assets_generated: int,
                           total_duration_ms: float,
                           total_cost_usd: float = None,
                           **kwargs):
        """Log content creation performance"""
        self.logger.info(
            f"Content creation completed",
            content_type=content_type,
            assets_generated=assets_generated,
            total_duration_ms=total_duration_ms,
            total_cost_usd=total_cost_usd,
            **kwargs
        )


# Utility functions
def log_function_call(logger: ContentFactoryLogger):
    """Decorator สำหรับ log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            correlation_id = str(uuid.uuid4())[:8]
            
            logger.debug(
                f"Calling {func.__name__}",
                correlation_id=correlation_id,
                function=func.__name__,
                module=func.__module__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                start_time = datetime.now()
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                logger.debug(
                    f"Function {func.__name__} completed",
                    correlation_id=correlation_id,
                    function=func.__name__,
                    duration_ms=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                logger.error(
                    f"Function {func.__name__} failed",
                    correlation_id=correlation_id,
                    function=func.__name__,
                    duration_ms=duration,
                    error=str(e),
                    success=False,
                    exc_info=True
                )
                
                raise
                
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    # ทดสอบ logging system
    logger = setup_logger("test", use_emoji=True, use_color=True)
    
    logger.info("🚀 Starting test...")
    logger.debug("Debug message", user_id=123, action="test")
    logger.warning("Warning message", memory_usage="high")
    logger.error("Error message", error_code=500)
    
    # ทดสอบ context
    with LogContext(logger, component="test-component") as ctx:
        ctx.info("Info in context", data={"test": True})
        ctx.warning("Warning in context")
    
    # ทดสอบ performance logging
    perf_logger = PerformanceLogger(logger)
    perf_logger.log_api_call("https://api.test.com", "GET", 150.5, 200)
    perf_logger.log_ai_generation("gpt-3.5-turbo", 100, 50, 2000.0, 0.001)
    
    print("✅ Logging test completed")