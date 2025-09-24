"""
Unit Tests Package
==================

This package contains unit tests for individual components of the AI Content Factory system.

Each test file focuses on testing a single service or component in isolation,
using mocks and fixtures to eliminate external dependencies.

Test Files:
- test_trend_collector.py: Tests for trend collection services
- test_ai_director.py: Tests for AI director and content planning
- test_content_pipeline.py: Tests for content generation pipeline
- test_platform_manager.py: Tests for platform upload management

Testing Principles:
1. Each test should be independent and isolated
2. Use mocks for external services (APIs, databases)
3. Test both success and failure scenarios
4. Include edge cases and error conditions
5. Focus on business logic validation

Usage:
    # Run all unit tests
    python -m pytest tests/unit/
    
    # Run specific test file
    python -m pytest tests/unit/test_trend_collector.py
    
    # Run with verbose output
    python -m pytest tests/unit/ -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

# Common test utilities for unit tests
class MockAIService:
    """Mock AI service for testing."""
    
    def __init__(self, service_type: str = "text"):
        self.service_type = service_type
        self.call_count = 0
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """Mock generate method."""
        self.call_count += 1
        if self.service_type == "text":
            return f"Generated content for: {prompt[:50]}..."
        elif self.service_type == "image":
            return f"https://mock-image-url.com/generated-{self.call_count}.jpg"
        elif self.service_type == "audio":
            return f"https://mock-audio-url.com/generated-{self.call_count}.mp3"

class MockDatabase:
    """Mock database for unit testing."""
    
    def __init__(self):
        self.data = {}
        self.call_log = []
        
    async def execute(self, query: str, values: Dict = None):
        """Mock execute method."""
        self.call_log.append({"method": "execute", "query": query, "values": values})
        return {"rowcount": 1}
        
    async def fetch_all(self, query: str, values: Dict = None):
        """Mock fetch_all method."""
        self.call_log.append({"method": "fetch_all", "query": query, "values": values})
        return []
        
    async def fetch_one(self, query: str, values: Dict = None):
        """Mock fetch_one method."""
        self.call_log.append({"method": "fetch_one", "query": query, "values": values})
        return None

def create_mock_trend_data():
    """Create mock trend data for testing."""
    return {
        "id": "test-trend-1",
        "topic": "AI Content Creation",
        "keywords": ["AI", "content", "automation", "video"],
        "popularity_score": 85.5,
        "growth_rate": 15.2,
        "category": "Technology",
        "region": "Global",
        "source": "youtube",
        "collected_at": datetime.utcnow().isoformat(),
        "raw_data": {
            "search_volume": 10000,
            "competition": "medium",
            "related_topics": ["machine learning", "automation tools"]
        }
    }

def create_mock_content_opportunity():
    """Create mock content opportunity for testing."""
    return {
        "id": "test-opportunity-1",
        "trend_id": "test-trend-1",
        "suggested_angle": "How AI is Revolutionizing Content Creation",
        "estimated_views": 50000,
        "competition_level": "medium",
        "production_cost": 25.00,
        "estimated_roi": 4.2,
        "priority_score": 8.7,
        "status": "pending",
        "content_type": "educational",
        "target_platforms": ["youtube", "tiktok"],
        "created_at": datetime.utcnow().isoformat()
    }

# Common fixtures for unit tests
@pytest.fixture
def mock_ai_service():
    """Mock AI service fixture."""
    return MockAIService()

@pytest.fixture
def mock_database():
    """Mock database fixture."""
    return MockDatabase()

@pytest.fixture
def sample_trend():
    """Sample trend data fixture."""
    return create_mock_trend_data()

@pytest.fixture
def sample_opportunity():
    """Sample content opportunity fixture."""
    return create_mock_content_opportunity()