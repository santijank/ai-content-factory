"""
AI Content Factory - Tests Package
==================================

This package contains comprehensive test suites for the AI Content Factory system.

Test Structure:
- unit/: Unit tests for individual components
- integration/: Integration tests for component interactions
- fixtures/: Test data and mock objects

Test Categories:
- Trend Collection & Analysis
- Content Generation Pipeline
- Platform Management & Upload
- End-to-End Workflows

Usage:
    # Run all tests
    python -m pytest tests/
    
    # Run only unit tests
    python -m pytest tests/unit/
    
    # Run only integration tests
    python -m pytest tests/integration/
    
    # Run with coverage
    python -m pytest tests/ --cov=./ --cov-report=html
"""

__version__ = "1.0.0"
__author__ = "AI Content Factory Team"

# Test configuration constants
TEST_CONFIG = {
    "database_url": "sqlite:///:memory:",
    "test_timeout": 30,
    "mock_api_responses": True,
    "enable_real_api_calls": False,  # Set to True for integration testing with real APIs
}

# Common test utilities
import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
import json
import os

def get_test_data_path(filename: str) -> str:
    """Get path to test data file."""
    return os.path.join(os.path.dirname(__file__), 'fixtures', filename)

def load_fixture(filename: str) -> Dict[Any, Any]:
    """Load JSON fixture data."""
    with open(get_test_data_path(filename), 'r', encoding='utf-8') as f:
        return json.load(f)

def create_mock_database():
    """Create mock database for testing."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.fetch_all = AsyncMock()
    mock_db.fetch_one = AsyncMock()
    return mock_db

class AsyncMock(MagicMock):
    """Async version of MagicMock for testing async functions."""
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)

# Test markers
pytest_plugins = ["pytest_asyncio"]

# Common test fixtures available to all tests
@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return {
        "database": {
            "url": TEST_CONFIG["database_url"]
        },
        "ai_models": {
            "text_ai": {"budget": "groq", "balanced": "openai", "premium": "claude"},
            "image_ai": {"budget": "stable_diffusion", "balanced": "leonardo", "premium": "midjourney"},
            "audio_ai": {"budget": "gtts", "balanced": "azure", "premium": "elevenlabs"}
        },
        "platforms": {
            "youtube": {"enabled": True},
            "tiktok": {"enabled": True},
            "instagram": {"enabled": False},
            "facebook": {"enabled": False}
        }
    }

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()