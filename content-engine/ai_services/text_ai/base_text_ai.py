"""
Base Text AI Service

Abstract base class for all text-based AI services in the Content Engine.
Provides common interface and functionality for text generation, analysis, and optimization.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of text AI tasks"""
    TREND_ANALYSIS = "trend_analysis"
    CONTENT_SCRIPT = "content_script"
    CONTENT_OPTIMIZATION = "content_optimization"
    TITLE_GENERATION = "title_generation"
    DESCRIPTION_GENERATION = "description_generation"
    HASHTAG_GENERATION = "hashtag_generation"
    HOOK_GENERATION = "hook_generation"
    CTA_GENERATION = "cta_generation"
    BRAINSTORM = "brainstorm"
    SUMMARIZATION = "summarization"


class QualityTier(Enum):
    """Quality tiers for different use cases"""
    BUDGET = "budget"
    BALANCED = "balanced"
    PREMIUM = "premium"


@dataclass
class TextAIRequest:
    """Request object for text AI operations"""
    task_type: TaskType
    prompt: str
    context: Dict[str, Any] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    quality_tier: QualityTier = QualityTier.BALANCED
    platform: Optional[str] = None
    audience: Optional[str] = None
    style: Optional[str] = None
    language: str = "en"


@dataclass
class TextAIResponse:
    """Response object from text AI operations"""
    content: str
    metadata: Dict[str, Any]
    tokens_used: int
    cost: float
    processing_time: float
    quality_score: Optional[float] = None
    confidence: Optional[float] = None
    service_name: str = ""
    model_used: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseTextAI(ABC):
    """
    Abstract base class for text AI services.
    
    All text AI implementations must inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, 
                 service_name: str,
                 api_key: str = None,
                 model: str = None,
                 quality_tier: QualityTier = QualityTier.BALANCED,
                 config: Dict[str, Any] = None):
        """
        Initialize the text AI service.
        
        Args:
            service_name: Name of the AI service
            api_key: API key for the service
            model: Default model to use
            quality_tier: Quality tier for this instance
            config: Additional configuration parameters
        """
        self.service_name = service_name
        self.api_key = api_key
        self.model = model or self._get_default_model()
        self.quality_tier = quality_tier
        self.config = config or {}
        
        # Metrics tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.last_request_time = None
        
        # Rate limiting
        self.rate_limit_requests = self.config.get('rate_limit_requests', 100)
        self.rate_limit_window = self.config.get('rate_limit_window', 60)  # seconds
        self.request_timestamps = []
        
        logger.info(f"Initialized {service_name} text AI service with model {self.model}")

    @abstractmethod
    async def generate_text(self, request: TextAIRequest) -> TextAIResponse:
        """
        Generate text based on the request.
        
        Args:
            request: TextAIRequest containing prompt and parameters
            
        Returns:
            TextAIResponse with generated content and metadata
        """
        pass

    @abstractmethod
    def _get_default_model(self) -> str:
        """Get the default model for this service"""
        pass

    @abstractmethod
    def _calculate_cost(self, tokens_used: int, model: str) -> float:
        """Calculate cost based on tokens used and model"""
        pass

    @abstractmethod
    def _validate_api_key(self) -> bool:
        """Validate that the API key is properly configured"""
        pass

    async def analyze_trend(self, 
                          topic: str, 
                          popularity_score: float,
                          growth_rate: float,
                          source: str = "unknown") -> TextAIResponse:
        """
        Analyze a trend for content opportunities.
        
        Args:
            topic: The trending topic
            popularity_score: Current popularity (1-10)
            growth_rate: Growth rate percentage
            source: Source of the trend data
            
        Returns:
            TextAIResponse with trend analysis
        """
        prompt = f"""
        Analyze this trending topic for content opportunities:
        
        Topic: {topic}
        Current popularity: {popularity_score}/10
        Growth rate: {growth_rate}%
        Source: {source}
        
        Provide analysis in JSON format:
        {{
            "viral_potential": 1-10,
            "content_saturation": 1-10,
            "audience_interest": 1-10,
            "monetization_opportunity": 1-10,
            "content_angles": ["angle1", "angle2", "angle3"],
            "target_demographics": ["demo1", "demo2"],
            "recommended_platforms": ["platform1", "platform2"],
            "suggested_timeline": "immediate/this_week/this_month",
            "competition_level": "low/medium/high",
            "trending_keywords": ["keyword1", "keyword2", "keyword3"]
        }}
        """
        
        request = TextAIRequest(
            task_type=TaskType.TREND_ANALYSIS,
            prompt=prompt,
            context={
                "topic": topic,
                "popularity_score": popularity_score,
                "growth_rate": growth_rate,
                "source": source
            },
            max_tokens=800,
            temperature=0.3
        )
        
        return await self.generate_text(request)

    async def generate_content_script(self,
                                    topic: str,
                                    angle: str,
                                    platform: str,
                                    duration: int = 60,
                                    audience: str = "general",
                                    style: str = "engaging") -> TextAIResponse:
        """
        Generate a content script for video/audio content.
        
        Args:
            topic: Main topic of content
            angle: Specific angle or approach
            platform: Target platform (youtube, tiktok, etc.)
            duration: Duration in seconds
            audience: Target audience
            style: Content style
            
        Returns:
            TextAIResponse with content script
        """
        prompt = f"""
        Create a {duration}-second video script for {platform}:
        
        Topic: {topic}
        Angle: {angle}
        Target audience: {audience}
        Style: {style}
        
        Format the response as JSON:
        {{
            "hook": "First 3 seconds to grab attention",
            "main_content": "Main message and value proposition",
            "supporting_points": ["point1", "point2", "point3"],
            "cta": "Clear call-to-action",
            "estimated_duration": {duration},
            "tone": "conversational/professional/energetic",
            "key_phrases": ["phrase1", "phrase2"],
            "visual_cues": ["visual1", "visual2"]
        }}
        """
        
        request = TextAIRequest(
            task_type=TaskType.CONTENT_SCRIPT,
            prompt=prompt,
            context={
                "topic": topic,
                "angle": angle,
                "platform": platform,
                "duration": duration,
                "audience": audience,
                "style": style
            },
            platform=platform,
            audience=audience,
            style=style,
            max_tokens=1000,
            temperature=0.7
        )
        
        return await self.generate_text(request)

    async def optimize_for_platform(self,
                                   content: str,
                                   platform: str,
                                   content_type: str = "video") -> TextAIResponse:
        """
        Optimize content for specific platform requirements.
        
        Args:
            content: Original content to optimize
            platform: Target platform
            content_type: Type of content (video, post, story, etc.)
            
        Returns:
            TextAIResponse with optimized content
        """
        platform_requirements = self._get_platform_requirements(platform, content_type)
        
        prompt = f"""
        Optimize this content for {platform}:
        
        Original content: {content}
        Platform: {platform}
        Content type: {content_type}
        Platform requirements: {platform_requirements}
        
        Provide optimized content in JSON format:
        {{
            "optimized_title": "SEO and engagement optimized title",
            "optimized_description": "Platform-specific description",
            "hashtags": ["#tag1", "#tag2", "#tag3"],
            "thumbnail_concept": "Eye-catching thumbnail idea",
            "posting_time": "optimal posting time",
            "engagement_hooks": ["hook1", "hook2"],
            "platform_specific_tips": ["tip1", "tip2"]
        }}
        """
        
        request = TextAIRequest(
            task_type=TaskType.CONTENT_OPTIMIZATION,
            prompt=prompt,
            context={
                "original_content": content,
                "platform": platform,
                "content_type": content_type
            },
            platform=platform,
            max_tokens=800,
            temperature=0.5
        )
        
        return await self.generate_text(request)

    async def generate_titles(self,
                            topic: str,
                            platform: str,
                            count: int = 5,
                            style: str = "clickbait") -> TextAIResponse:
        """
        Generate multiple title options for content.
        
        Args:
            topic: Content topic
            platform: Target platform
            count: Number of titles to generate
            style: Title style (clickbait, professional, educational, etc.)
            
        Returns:
            TextAIResponse with title options
        """
        prompt = f"""
        Generate {count} {style} titles for {platform} content about: {topic}
        
        Requirements:
        - Platform: {platform}
        - Style: {style}
        - Count: {count}
        
        Return as JSON:
        {{
            "titles": [
                {{
                    "title": "Title text",
                    "estimated_ctr": "percentage",
                    "target_audience": "audience type",
                    "seo_score": 1-10
                }}
            ],
            "best_title": "title with highest potential",
            "reasoning": "why this title is best"
        }}
        """
        
        request = TextAIRequest(
            task_type=TaskType.TITLE_GENERATION,
            prompt=prompt,
            context={
                "topic": topic,
                "platform": platform,
                "count": count,
                "style": style
            },
            platform=platform,
            style=style,
            max_tokens=600,
            temperature=0.8
        )
        
        return await self.generate_text(request)

    async def generate_hashtags(self,
                              content: str,
                              platform: str,
                              max_hashtags: int = 10) -> TextAIResponse:
        """
        Generate relevant hashtags for content.
        
        Args:
            content: Content to generate hashtags for
            platform: Target platform
            max_hashtags: Maximum number of hashtags
            
        Returns:
            TextAIResponse with hashtag suggestions
        """
        prompt = f"""
        Generate relevant hashtags for this content on {platform}:
        
        Content: {content}
        Platform: {platform}
        Max hashtags: {max_hashtags}
        
        Return as JSON:
        {{
            "trending_hashtags": ["#tag1", "#tag2"],
            "niche_hashtags": ["#tag3", "#tag4"],
            "branded_hashtags": ["#tag5", "#tag6"],
            "recommended_combination": ["#tag1", "#tag2", "#tag3"],
            "hashtag_strategy": "explanation of strategy"
        }}
        """
        
        request = TextAIRequest(
            task_type=TaskType.HASHTAG_GENERATION,
            prompt=prompt,
            context={
                "content": content,
                "platform": platform,
                "max_hashtags": max_hashtags
            },
            platform=platform,
            max_tokens=400,
            temperature=0.6
        )
        
        return await self.generate_text(request)

    def _get_platform_requirements(self, platform: str, content_type: str) -> Dict[str, Any]:
        """Get platform-specific requirements"""
        requirements = {
            "youtube": {
                "video": {
                    "title_length": "60 characters max",
                    "description_length": "5000 characters max",
                    "hashtags": "3-5 recommended",
                    "optimal_duration": "8-12 minutes",
                    "thumbnail": "1280x720px"
                }
            },
            "tiktok": {
                "video": {
                    "title_length": "150 characters max",
                    "hashtags": "3-5 trending hashtags",
                    "optimal_duration": "15-60 seconds",
                    "format": "vertical 9:16"
                }
            },
            "instagram": {
                "post": {
                    "caption_length": "2200 characters max",
                    "hashtags": "up to 30, use 5-10",
                    "format": "square 1:1 or 4:5"
                },
                "reel": {
                    "title_length": "125 characters",
                    "hashtags": "3-5 trending",
                    "duration": "15-90 seconds"
                }
            },
            "facebook": {
                "post": {
                    "text_length": "500 characters recommended",
                    "hashtags": "1-2 hashtags max",
                    "optimal_time": "1-3 PM weekdays"
                }
            }
        }
        
        return requirements.get(platform, {}).get(content_type, {})

    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        
        # Remove old timestamps outside the window
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < self.rate_limit_window
        ]
        
        # Check if we're under the limit
        if len(self.request_timestamps) >= self.rate_limit_requests:
            wait_time = self.rate_limit_window - (now - self.request_timestamps[0])
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                return await self._check_rate_limit()
        
        self.request_timestamps.append(now)
        return True

    def _update_metrics(self, response: TextAIResponse):
        """Update service metrics"""
        self.total_requests += 1
        self.total_tokens += response.tokens_used
        self.total_cost += response.cost
        self.last_request_time = response.timestamp

    def get_metrics(self) -> Dict[str, Any]:
        """Get service usage metrics"""
        return {
            "service_name": self.service_name,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "last_request_time": self.last_request_time,
            "average_cost_per_request": self.total_cost / max(1, self.total_requests),
            "average_tokens_per_request": self.total_tokens / max(1, self.total_requests)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the service"""
        try:
            # Simple test request
            test_request = TextAIRequest(
                task_type=TaskType.SUMMARIZATION,
                prompt="Summarize: This is a test",
                max_tokens=50,
                temperature=0.1
            )
            
            start_time = time.time()
            response = await self.generate_text(test_request)
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "service_name": self.service_name,
                "model": self.model,
                "response_time": response_time,
                "api_key_valid": self._validate_api_key(),
                "last_request": self.last_request_time,
                "total_requests": self.total_requests
            }
            
        except Exception as e:
            logger.error(f"Health check failed for {self.service_name}: {e}")
            return {
                "status": "unhealthy",
                "service_name": self.service_name,
                "error": str(e),
                "api_key_valid": self._validate_api_key()
            }

    def __str__(self) -> str:
        return f"{self.service_name} TextAI (model: {self.model}, tier: {self.quality_tier.value})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(service='{self.service_name}', model='{self.model}')>"