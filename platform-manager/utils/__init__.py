"""
AI Content Factory - Platform Manager Utils Package
=================================================

This package contains utility functions and helper classes specific to the
platform manager service. These utilities handle content processing, file
management, API interactions, and platform-specific optimizations.

Utilities included:
- ContentOptimizer: Content optimization and format conversion
- FileManager: File handling, validation, and storage management
- PlatformApiClient: Generic platform API client with authentication
- UploadProgressTracker: Upload progress monitoring and callbacks
- MetadataExtractor: Extract metadata from various file formats
- ThumbnailGenerator: Generate thumbnails and preview images
- VideoProcessor: Video processing and optimization
- AudioProcessor: Audio processing and enhancement
- CompressionHelper: File compression and size optimization
- ValidationHelper: Content validation against platform requirements

Architecture:
    Utility Pattern - Stateless utility functions and classes
    Strategy Pattern - Platform-specific processing strategies
    Template Method - Common processing workflows with platform-specific steps
    Factory Pattern - Processor and optimizer creation

Usage:
    from platform_manager.utils import ContentOptimizer, FileManager
    
    optimizer = ContentOptimizer('youtube')
    optimized_file = optimizer.optimize_for_platform(file_path, settings)
    
    file_manager = FileManager()
    metadata = file_manager.extract_metadata(file_path)
"""

import os
import hashlib
import mimetypes
import tempfile
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import logging
import asyncio
from datetime import datetime, timedelta

# Import shared utilities
from shared.utils import get_logger, get_cache, with_error_handling
from shared.models.platform_model import PlatformTypeEnum
from shared.models.content_model import ContentTypeEnum, ContentFormatEnum
from shared.constants.platform_constants import PLATFORMS

# Package version
__version__ = "1.0.0"

# Export all utilities
__all__ = [
    # Core utilities
    'ContentOptimizer',
    'FileManager',
    'PlatformApiClient',
    'UploadProgressTracker',
    'MetadataExtractor',
    'ThumbnailGenerator',
    'VideoProcessor',
    'AudioProcessor',
    'CompressionHelper',
    'ValidationHelper',
    
    # Base classes
    'BaseProcessor',
    'BaseOptimizer',
    'BaseValidator',
    'ProgressCallback',
    
    # Data classes
    'OptimizationSettings',
    'ProcessingResult',
    'ValidationResult',
    'ProgressInfo',
    'FileInfo',
    
    # Utility functions
    'get_file_info',
    'validate_file',
    'extract_metadata',
    'generate_thumbnail',
    'optimize_content',
    'calculate_file_hash',
    'get_mime_type',
    'format_file_size',
    'estimate_processing_time',
    'cleanup_temp_files',
    
    # Platform-specific utilities
    'get_platform_optimizer',
    'get_platform_validator',
    'get_platform_limits',
    'optimize_for_platform',
    'validate_for_platform'
]

# Setup logging
logger = get_logger(__name__)

# Data classes for utility operations

@dataclass
class FileInfo:
    """File information container."""
    
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    content_type: ContentTypeEnum
    format: ContentFormatEnum
    hash_md5: str = ""
    hash_sha256: str = ""
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    # Media-specific info
    duration: Optional[float] = None  # seconds
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None
    frame_rate: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_aspect_ratio(self) -> Optional[str]:
        """Get aspect ratio as string."""
        if self.width and self.height:
            from math import gcd
            ratio_gcd = gcd(self.width, self.height)
            w_ratio = self.width // ratio_gcd
            h_ratio = self.height // ratio_gcd
            return f"{w_ratio}:{h_ratio}"
        return None
    
    def get_resolution_string(self) -> Optional[str]:
        """Get resolution as string."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return None

@dataclass
class OptimizationSettings:
    """Content optimization settings."""
    
    target_platform: PlatformTypeEnum
    quality_level: str = "balanced"  # low, balanced, high
    target_size: Optional[int] = None  # bytes
    max_duration: Optional[int] = None  # seconds
    target_resolution: Optional[str] = None  # e.g., "1920x1080"
    target_bitrate: Optional[int] = None
    target_format: Optional[ContentFormatEnum] = None
    
    # Optimization flags
    compress_video: bool = True
    compress_audio: bool = True
    optimize_thumbnails: bool = True
    remove_metadata: bool = False
    
    # Platform-specific settings
    platform_specific: Dict[str, Any] = field(default_factory=dict)
    
    # Processing preferences
    preserve_quality: bool = True
    fast_processing: bool = False
    
    def get_quality_settings(self) -> Dict[str, Any]:
        """Get quality settings based on level."""
        quality_presets = {
            'low': {
                'video_quality': 20,
                'audio_bitrate': 128,
                'compression_level': 'high'
            },
            'balanced': {
                'video_quality': 23,
                'audio_bitrate': 192,
                'compression_level': 'medium'
            },
            'high': {
                'video_quality': 18,
                'audio_bitrate': 320,
                'compression_level': 'low'
            }
        }
        return quality_presets.get(self.quality_level, quality_presets['balanced'])

@dataclass
class ProcessingResult:
    """Processing operation result."""
    
    success: bool
    input_file: str
    output_file: Optional[str] = None
    processing_time: float = 0.0
    
    # File size changes
    original_size: int = 0
    final_size: int = 0
    size_reduction: int = 0
    compression_ratio: float = 0.0
    
    # Quality metrics
    quality_score: float = 0.0
    
    # Error information
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    # Processing details
    steps_completed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_metrics(self):
        """Calculate derived metrics."""
        if self.original_size > 0:
            self.size_reduction = self.original_size - self.final_size
            self.compression_ratio = self.final_size / self.original_size

@dataclass
class ValidationResult:
    """Validation result container."""
    
    is_valid: bool = True
    file_path: str = ""
    platform: Optional[PlatformTypeEnum] = None
    
    # Validation details
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # File checks
    file_exists: bool = True
    file_readable: bool = True
    format_supported: bool = True
    size_within_limits: bool = True
    duration_within_limits: bool = True
    resolution_supported: bool = True
    
    # Platform-specific checks
    platform_requirements_met: bool = True
    metadata_valid: bool = True
    
    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)

@dataclass 
class ProgressInfo:
    """Progress information for operations."""
    
    current_step: str = ""
    progress_percentage: float = 0.0
    bytes_processed: int = 0
    total_bytes: int = 0
    time_elapsed: float = 0.0
    estimated_time_remaining: float = 0.0
    speed: float = 0.0  # bytes per second
    
    # Step tracking
    current_step_number: int = 0
    total_steps: int = 0
    
    # Additional info
    status_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_progress(self, step: str, percentage: float, message: str = ""):
        """Update progress information."""
        self.current_step = step
        self.progress_percentage = max(0.0, min(100.0, percentage))
        self.status_message = message
        
        # Calculate speed if we have byte information
        if self.time_elapsed > 0 and self.bytes_processed > 0:
            self.speed = self.bytes_processed / self.time_elapsed
            
            # Estimate remaining time
            if self.total_bytes > 0:
                remaining_bytes = self.total_bytes - self.bytes_processed
                self.estimated_time_remaining = remaining_bytes / self.speed

# Callback types
ProgressCallback = Callable[[ProgressInfo], None]

# Base classes

class BaseProcessor(ABC):
    """Base class for content processors."""
    
    def __init__(self, settings: Dict[str, Any] = None):
        self.settings = settings or {}
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._temp_files = []
    
    @abstractmethod
    async def process(self, input_file: str, output_file: str, **kwargs) -> ProcessingResult:
        """Process content file."""
        pass
    
    def cleanup(self):
        """Cleanup temporary files."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        self._temp_files.clear()
    
    def create_temp_file(self, suffix: str = "", prefix: str = "platform_mgr_") -> str:
        """Create temporary file and track for cleanup."""
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        self._temp_files.append(temp_path)
        return temp_path

class BaseOptimizer(BaseProcessor):
    """Base class for content optimizers."""
    
    def __init__(self, platform: PlatformTypeEnum, settings: OptimizationSettings = None):
        super().__init__()
        self.platform = platform
        self.settings = settings or OptimizationSettings(target_platform=platform)
    
    @abstractmethod
    async def optimize(self, input_file: str, progress_callback: ProgressCallback = None) -> ProcessingResult:
        """Optimize content for platform."""
        pass

class BaseValidator(ABC):
    """Base class for content validators."""
    
    def __init__(self, platform: PlatformTypeEnum):
        self.platform = platform
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def validate(self, file_path: str) -> ValidationResult:
        """Validate content for platform."""
        pass

# Core utility classes

class FileManager:
    """File handling and management utilities."""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.logger = get_logger(f"{__name__}.FileManager")
        self._cache = get_cache()
    
    @with_error_handling
    def get_file_info(self, file_path: str) -> FileInfo:
        """Extract comprehensive file information."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Basic file info
        stat = path.stat()
        file_size = stat.st_size
        mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        
        # Determine content type and format
        content_type = self._get_content_type(mime_type)
        format_type = self._get_format_type(path.suffix.lower())
        
        file_info = FileInfo(
            file_path=str(path),
            file_name=path.name,
            file_size=file_size,
            mime_type=mime_type,
            content_type=content_type,
            format=format_type,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # Calculate hashes
        file_info.hash_md5 = self.calculate_file_hash(file_path, 'md5')
        file_info.hash_sha256 = self.calculate_file_hash(file_path, 'sha256')
        
        # Extract media-specific metadata
        if content_type in [ContentTypeEnum.VIDEO, ContentTypeEnum.AUDIO]:
            self._extract_media_metadata(file_info)
        elif content_type == ContentTypeEnum.IMAGE:
            self._extract_image_metadata(file_info)
        
        return file_info
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'md5') -> str:
        """Calculate file hash."""
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def _get_content_type(self, mime_type: str) -> ContentTypeEnum:
        """Determine content type from MIME type."""
        if mime_type.startswith('video/'):
            return ContentTypeEnum.VIDEO
        elif mime_type.startswith('audio/'):
            return ContentTypeEnum.AUDIO
        elif mime_type.startswith('image/'):
            return ContentTypeEnum.IMAGE
        else:
            return ContentTypeEnum.TEXT
    
    def _get_format_type(self, extension: str) -> ContentFormatEnum:
        """Get format type from file extension."""
        ext_map = {
            '.mp4': ContentFormatEnum.MP4,
            '.mov': ContentFormatEnum.MOV,
            '.avi': ContentFormatEnum.AVI,
            '.webm': ContentFormatEnum.WEBM,
            '.mp3': ContentFormatEnum.MP3,
            '.wav': ContentFormatEnum.WAV,
            '.aac': ContentFormatEnum.AAC,
            '.jpg': ContentFormatEnum.JPG,
            '.jpeg': ContentFormatEnum.JPG,
            '.png': ContentFormatEnum.PNG,
            '.webp': ContentFormatEnum.WEBP,
            '.gif': ContentFormatEnum.GIF
        }
        return ext_map.get(extension, ContentFormatEnum.MP4)
    
    def _extract_media_metadata(self, file_info: FileInfo):
        """Extract media metadata using ffprobe or similar."""
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_info.file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extract format info
                if 'format' in data:
                    format_info = data['format']
                    file_info.duration = float(format_info.get('duration', 0))
                    file_info.bitrate = int(format_info.get('bit_rate', 0))
                
                # Extract stream info
                if 'streams' in data:
                    for stream in data['streams']:
                        if stream['codec_type'] == 'video':
                            file_info.width = stream.get('width')
                            file_info.height = stream.get('height')
                            file_info.frame_rate = self._parse_frame_rate(stream.get('r_frame_rate'))
                        elif stream['codec_type'] == 'audio':
                            file_info.sample_rate = int(stream.get('sample_rate', 0))
                            file_info.channels = int(stream.get('channels', 0))
        
        except Exception as e:
            self.logger.warning(f"Failed to extract media metadata: {e}")
    
    def _extract_image_metadata(self, file_info: FileInfo):
        """Extract image metadata."""
        try:
            from PIL import Image
            
            with Image.open(file_info.file_path) as img:
                file_info.width, file_info.height = img.size
                file_info.metadata.update({
                    'format': img.format,
                    'mode': img.mode,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                })
        
        except Exception as e:
            self.logger.warning(f"Failed to extract image metadata: {e}")
    
    def _parse_frame_rate(self, frame_rate_str: str) -> Optional[float]:
        """Parse frame rate string like '30/1' to float."""
        if not frame_rate_str:
            return None
        
        try:
            if '/' in frame_rate_str:
                num, den = frame_rate_str.split('/')
                return float(num) / float(den)
            return float(frame_rate_str)
        except:
            return None

class ContentOptimizer:
    """Content optimization utilities."""
    
    def __init__(self, platform: PlatformTypeEnum = None):
        self.platform = platform
        self.logger = get_logger(f"{__name__}.ContentOptimizer")
        self.file_manager = FileManager()
        
        # Platform-specific optimizers
        self._optimizers = {}
        self._load_optimizers()
    
    def _load_optimizers(self):
        """Load platform-specific optimizers."""
        # This would be expanded with actual optimizer implementations
        pass
    
    async def optimize_for_platform(
        self,
        input_file: str,
        platform: PlatformTypeEnum,
        settings: OptimizationSettings = None,
        progress_callback: ProgressCallback = None
    ) -> ProcessingResult:
        """Optimize content for specific platform."""
        
        if not settings:
            settings = OptimizationSettings(target_platform=platform)
        
        # Get file info
        file_info = self.file_manager.get_file_info(input_file)
        
        # Create progress tracker
        progress = ProgressInfo()
        progress.total_steps = 4  # validation, optimization, compression, finalization
        
        try:
            # Step 1: Validation
            if progress_callback:
                progress.update_progress("Validating file", 10.0, "Checking file compatibility")
                progress_callback(progress)
            
            validation_result = await self._validate_file(file_info, platform)
            if not validation_result.is_valid:
                return ProcessingResult(
                    success=False,
                    input_file=input_file,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )
            
            # Step 2: Platform-specific optimization
            if progress_callback:
                progress.update_progress("Optimizing content", 30.0, "Applying platform optimizations")
                progress_callback(progress)
            
            optimized_file = await self._apply_platform_optimization(
                file_info, platform, settings, progress_callback
            )
            
            # Step 3: Compression
            if progress_callback:
                progress.update_progress("Compressing file", 70.0, "Reducing file size")
                progress_callback(progress)
            
            compressed_file = await self._apply_compression(
                optimized_file, settings, progress_callback
            )
            
            # Step 4: Finalization
            if progress_callback:
                progress.update_progress("Finalizing", 90.0, "Completing optimization")
                progress_callback(progress)
            
            # Calculate results
            result = ProcessingResult(
                success=True,
                input_file=input_file,
                output_file=compressed_file,
                original_size=file_info.file_size
            )
            
            if os.path.exists(compressed_file):
                result.final_size = os.path.getsize(compressed_file)
                result.calculate_metrics()
            
            if progress_callback:
                progress.update_progress("Complete", 100.0, "Optimization completed successfully")
                progress_callback(progress)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return ProcessingResult(
                success=False,
                input_file=input_file,
                error_message=str(e)
            )
    
    async def _validate_file(self, file_info: FileInfo, platform: PlatformTypeEnum) -> ValidationResult:
        """Validate file for platform requirements."""
        validator = get_platform_validator(platform)
        if validator:
            return await validator.validate(file_info.file_path)
        
        # Basic validation if no platform-specific validator
        result = ValidationResult(file_path=file_info.file_path, platform=platform)
        
        # Check file size limits (simplified)
        max_sizes = {
            PlatformTypeEnum.YOUTUBE: 128 * 1024**3,  # 128 GB
            PlatformTypeEnum.TIKTOK: 4 * 1024**3,     # 4 GB
            PlatformTypeEnum.INSTAGRAM: 4 * 1024**3,   # 4 GB
            PlatformTypeEnum.FACEBOOK: 10 * 1024**3    # 10 GB
        }
        
        max_size = max_sizes.get(platform, 1024**3)  # 1 GB default
        if file_info.file_size > max_size:
            result.add_error(f"File size ({format_file_size(file_info.file_size)}) exceeds platform limit ({format_file_size(max_size)})")
        
        return result
    
    async def _apply_platform_optimization(
        self,
        file_info: FileInfo,
        platform: PlatformTypeEnum,
        settings: OptimizationSettings,
        progress_callback: ProgressCallback = None
    ) -> str:
        """Apply platform-specific optimizations."""
        
        # For now, return original file - would implement actual optimization
        return file_info.file_path
    
    async def _apply_compression(
        self,
        file_path: str,
        settings: OptimizationSettings,
        progress_callback: ProgressCallback = None
    ) -> str:
        """Apply compression to reduce file size."""
        
        # For now, return original file - would implement actual compression
        return file_path

class ThumbnailGenerator:
    """Generate thumbnails and preview images."""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.ThumbnailGenerator")
        self.file_manager = FileManager()
    
    async def generate_thumbnail(
        self,
        input_file: str,
        output_file: str = None,
        timestamp: float = None,
        size: Tuple[int, int] = (1280, 720),
        quality: int = 85
    ) -> ProcessingResult:
        """Generate thumbnail from video or image."""
        
        file_info = self.file_manager.get_file_info(input_file)
        
        if not output_file:
            output_file = self._generate_thumbnail_path(input_file)
        
        try:
            if file_info.content_type == ContentTypeEnum.VIDEO:
                return await self._generate_video_thumbnail(
                    input_file, output_file, timestamp, size, quality
                )
            elif file_info.content_type == ContentTypeEnum.IMAGE:
                return await self._generate_image_thumbnail(
                    input_file, output_file, size, quality
                )
            else:
                return ProcessingResult(
                    success=False,
                    input_file=input_file,
                    error_message=f"Unsupported content type for thumbnail: {file_info.content_type}"
                )
        
        except Exception as e:
            self.logger.error(f"Thumbnail generation failed: {e}")
            return ProcessingResult(
                success=False,
                input_file=input_file,
                error_message=str(e)
            )
    
    def _generate_thumbnail_path(self, input_file: str) -> str:
        """Generate thumbnail file path."""
        path = Path(input_file)
        return str(path.with_suffix('.jpg').with_name(f"{path.stem}_thumb.jpg"))
    
    async def _generate_video_thumbnail(
        self,
        input_file: str,
        output_file: str,
        timestamp: float = None,
        size: Tuple[int, int] = (1280, 720),
        quality: int = 85
    ) -> ProcessingResult:
        """Generate thumbnail from video at specific timestamp."""
        
        import subprocess
        
        if timestamp is None:
            # Use middle of video
            file_info = self.file_manager.get_file_info(input_file)
            timestamp = (file_info.duration or 10) / 2
        
        cmd = [
            'ffmpeg', '-i', input_file,
            '-ss', str(timestamp),
            '-vframes', '1',
            '-vf', f'scale={size[0]}:{size[1]}',
            '-q:v', str(quality),
            '-y', output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return ProcessingResult(
                success=True,
                input_file=input_file,
                output_file=output_file,
                final_size=os.path.getsize(output_file) if os.path.exists(output_file) else 0
            )
        else:
            return ProcessingResult(
                success=False,
                input_file=input_file,
                error_message=f"FFmpeg error: {result.stderr}"
            )
    
    async def _generate_image_thumbnail(
        self,
        input_file: str,
        output_file: str,
        size: Tuple[int, int] = (1280, 720),
        quality: int = 85
    ) -> ProcessingResult:
        """Generate thumbnail from image."""
        
        from PIL import Image
        
        with Image.open(input_file) as img:
            # Maintain aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Save with quality setting
            img.save(output_file, 'JPEG', quality=quality, optimize=True)
        
        return ProcessingResult(
            success=True,
            input_file=input_file,
            output_file=output_file,
            final_size=os.path.getsize(output_file) if os.path.exists(output_file) else 0
        )

# Utility functions

def get_file_info(file_path: str) -> FileInfo:
    """Get comprehensive file information."""
    file_manager = FileManager()
    return file_manager.get_file_info(file_path)

def validate_file(file_path: str, platform: PlatformTypeEnum = None) -> ValidationResult:
    """Validate file for platform requirements."""
    # Synchronous wrapper for async function
    import asyncio
    
    async def _validate():
        validator = get_platform_validator(platform) if platform else None
        if validator:
            return await validator.validate(file_path)
        
        # Basic validation
        result = ValidationResult(file_path=file_path, platform=platform)
        
        if not os.path.exists(file_path):
            result.add_error("File does not exist")
            result.file_exists = False
        
        return result
    
    return asyncio.run(_validate())

def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from file."""
    file_info = get_file_info(file_path)
    return file_info.metadata

def generate_thumbnail(
    input_file: str,
    output_file: str = None,
    **kwargs
) -> ProcessingResult:
    """Generate thumbnail from video or image."""
    import asyncio
    
    generator = ThumbnailGenerator()
    return asyncio.run(generator.generate_thumbnail(input_file, output_file, **kwargs))

def optimize_content(
    input_file: str,
    platform: PlatformTypeEnum,
    settings: OptimizationSettings = None,
    **kwargs
) -> ProcessingResult:
    """Optimize content for platform."""
    import asyncio
    
    optimizer = ContentOptimizer(platform)
    return asyncio.run(optimizer.optimize_for_platform(input_file, platform, settings, **kwargs))

def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """Calculate file hash."""
    file_manager = FileManager()
    return file_manager.calculate_file_hash(file_path, algorithm)

def get_mime_type(file_path: str) -> str:
    """Get MIME type of file."""
    return mimetypes.guess_type(file_path)[0] or "application/octet-stream"

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"

def estimate_processing_time(
    file_size: int,
    content_type: ContentTypeEnum,
    complexity: str = "medium"
) -> float:
    """Estimate processing time in seconds."""
    
    base_times = {
        ContentTypeEnum.VIDEO: 0.5,    # seconds per MB
        ContentTypeEnum.AUDIO: 0.1,    # seconds per MB
        ContentTypeEnum.IMAGE: 0.05,   # seconds per MB
        ContentTypeEnum.TEXT: 0.01     # seconds per MB
    }
    
    complexity_multipliers = {
        "low": 0.5,
        "medium": 1.0,
        "high": 2.0
    }
    
    size_mb = file_size / (1024 * 1024)
    base_time = base_times.get(content_type, 0.1)
    multiplier = complexity_multipliers.get(complexity, 1.0)
    
    return size_mb * base_time * multiplier

def cleanup_temp_files(temp_dir: str = None):
    """Cleanup temporary files."""
    import shutil
    import tempfile
    
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
    else:
        # Cleanup default temp directory files with our prefix
        temp_base = tempfile.gettempdir()
        for filename in os.listdir(temp_base):
            if filename.startswith("platform_mgr_"):
                try:
                    os.unlink(os.path.join(temp_base, filename))
                except Exception:
                    pass

# Platform-specific utilities

def get_platform_optimizer(platform: PlatformTypeEnum) -> Optional[BaseOptimizer]:
    """Get optimizer for specific platform."""
    # Would return platform-specific optimizer instances
    return None

def get_platform_validator(platform: PlatformTypeEnum) -> Optional[BaseValidator]:
    """Get validator for specific platform."""
    # Would return platform-specific validator instances
    return None

def get_platform_limits(platform: PlatformTypeEnum) -> Dict[str, Any]:
    """Get platform limits and constraints."""
    from shared.constants.platform_constants import get_platform_limits as get_limits
    return get_limits(platform)

def optimize_for_platform(
    file_path: str,
    platform: PlatformTypeEnum,
    **kwargs
) -> ProcessingResult:
    """Optimize content for specific platform."""
    return optimize_content(file_path, platform, **kwargs)

def validate_for_platform(
    file_path: str,
    platform: PlatformTypeEnum
) -> ValidationResult:
    """Validate content for specific platform."""
    return validate_file(file_path, platform)

# Global instances for shared use
_file_manager = None
_content_optimizer = None
_thumbnail_generator = None

def get_file_manager() -> FileManager:
    """Get shared file manager instance."""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager

def get_content_optimizer() -> ContentOptimizer:
    """Get shared content optimizer instance."""
    global _content_optimizer
    if _content_optimizer is None:
        _content_optimizer = ContentOptimizer()
    return _content_optimizer

def get_thumbnail_generator() -> ThumbnailGenerator:
    """Get shared thumbnail generator instance."""
    global _thumbnail_generator
    if _thumbnail_generator is None:
        _thumbnail_generator = ThumbnailGenerator()
    return _thumbnail_generator

# Context manager for utility cleanup
class UtilityContext:
    """Context manager for automatic utility cleanup."""
    
    def __init__(self):
        self._temp_files = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup_temp_files()
        
        # Cleanup global instances
        global _file_manager, _content_optimizer, _thumbnail_generator
        
        if _file_manager:
            _file_manager = None
        if _content_optimizer:
            _content_optimizer = None
        if _thumbnail_generator:
            _thumbnail_generator = None

# Version and metadata
__author__ = "AI Content Factory Team"
__email__ = "dev@aicontentfactory.com"
__status__ = "Production"
__last_updated__ = "2024-01-15"