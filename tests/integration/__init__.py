"""
Integration Tests Package
=========================

This package contains integration tests that verify the interaction between
different components of the AI Content Factory system.

Integration tests focus on:
- Data flow between services
- End-to-end workflows  
- Component interactions
- Real API integrations (when enabled)

Test Files:
- test_trend_to_content_flow.py: Tests trend collection → content generation
- test_content_to_upload_flow.py: Tests content generation → platform upload
- test_end_to_end.py: Tests complete workflow from trends to published content

Configuration:
Integration tests can run in two modes:
1. Mock mode (default): Uses mocked services for fast, reliable testing
2. Live mode: Uses real APIs for comprehensive integration testing

Usage:
    # Run all integration tests with mocks
    python -m pytest tests/integration/
    
    # Run with real APIs (requires API keys)
    ENABLE_LIVE_APIS=true python -m pytest tests/integration/
    
    # Run specific integration test
    python -m pytest tests/integration/test_end_to_end.py
"""

import pytest
import asyncio
import os
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, AsyncMock
import tempfile
import json
from datetime import datetime, timedelta

# Integration test configuration
INTEGRATION_CONFIG = {
    "enable_live_apis": os.getenv("ENABLE_LIVE_APIS", "false").lower() == "true",
    "test_timeout": 300,  # 5 minutes for integration tests
    "database_url": os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:"),
    "cleanup_test_data": True,
    "max_concurrent_tests": 3
}

# Common fixtures for integration tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async integration tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def integration_config():
    """Integration test configuration."""
    return INTEGRATION_CONFIG.copy()

@pytest.fixture
async def test_database():
    """Set up test database for integration tests."""
    if INTEGRATION_CONFIG["enable_live_apis"]:
        # Use real database for live testing
        from database.init_database import init_database
        db = await init_database(INTEGRATION_CONFIG["database_url"])
    else:
        # Use in-memory database for mock testing
        db = create_mock_database()
    
    yield db
    
    if INTEGRATION_CONFIG["cleanup_test_data"]:
        await cleanup_test_database(db)

@pytest.fixture
def mock_ai_services():
    """Mock AI services for integration testing."""
    services = {
        "text_ai": Mock(),
        "image_ai": Mock(), 
        "audio_ai": Mock()
    }
    
    # Configure text AI mock
    services["text_ai"].generate = AsyncMock(return_value=json.dumps({
        "content_type": "educational",
        "script": {
            "hook": "Integration test hook",
            "main_content": "Integration test content",
            "cta": "Integration test CTA"
        },
        "visual_plan": {
            "style": "modern",
            "scenes": ["intro", "main", "outro"],
            "text_overlays": ["Test Title"]
        },
        "audio_plan": {
            "voice_style": "professional",
            "background_music": "none",
            "sound_effects": []
        },
        "platform_optimization": {
            "title": "Integration Test Video",
            "description": "Test video for integration testing",
            "hashtags": ["#test", "#integration"],
            "thumbnail_concept": "Simple test design"
        },
        "production_estimate": {
            "time_minutes": 15,
            "cost_baht": 10.0,
            "complexity": "low"
        }
    }))
    
    # Configure image AI mock
    services["image_ai"].generate_image = AsyncMock(side_effect=lambda scene: f"/tmp/test_{scene}_image.jpg")
    
    # Configure audio AI mock
    services["audio_ai"].text_to_speech = AsyncMock(return_value="/tmp/test_audio.mp3")
    
    return services

@pytest.fixture
def mock_platform_services():
    """Mock platform services for integration testing."""
    platforms = {}
    
    for platform_name in ["youtube", "tiktok", "instagram", "facebook"]:
        platform = Mock()
        platform.upload = AsyncMock(return_value={
            "status": "success",
            "platform_id": f"test_{platform_name}_123",
            "url": f"https://{platform_name}.com/test_video_123"
        })
        platforms[platform_name] = platform
    
    return platforms

@pytest.fixture
def test_content_files():
    """Create temporary test content files."""
    files = {}
    
    # Create test video file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
        video_file.write(b'mock video content for integration testing')
        files['video'] = video_file.name
    
    # Create test image files
    for i, scene in enumerate(['intro', 'main', 'outro']):
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_file:
            img_file.write(b'mock image content for ' + scene.encode())
            files[f'image_{scene}'] = img_file.name
    
    # Create test audio file
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as audio_file:
        audio_file.write(b'mock audio content for integration testing')
        files['audio'] = audio_file.name
    
    yield files
    
    # Cleanup temporary files
    for file_path in files.values():
        if os.path.exists(file_path):
            os.unlink(file_path)

def create_mock_database():
    """Create mock database for integration testing."""
    mock_db = MagicMock()
    
    # Mock database operations
    mock_db.execute = AsyncMock(return_value={"rowcount": 1})
    mock_db.fetch_all = AsyncMock(return_value=[])
    mock_db.fetch_one = AsyncMock(return_value=None)
    mock_db.insert = AsyncMock(return_value="test_id_123")
    mock_db.update = AsyncMock(return_value={"rowcount": 1})
    mock_db.delete = AsyncMock(return_value={"rowcount": 1})
    
    # Mock transaction support
    mock_db.transaction = AsyncMock()
    mock_db.begin = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    
    return mock_db

async def cleanup_test_database(db):
    """Clean up test data from database."""
    if hasattr(db, 'execute'):
        # Clean up test records
        cleanup_queries = [
            "DELETE FROM trends WHERE topic LIKE '%integration test%'",
            "DELETE FROM content_opportunities WHERE suggested_angle LIKE '%integration test%'", 
            "DELETE FROM content_items WHERE title LIKE '%integration test%'",
            "DELETE FROM uploads WHERE url LIKE '%test_video%'"
        ]
        
        for query in cleanup_queries:
            try:
                await db.execute(query)
            except Exception:
                pass  # Ignore cleanup errors

class IntegrationTestHelper:
    """Helper class for integration testing utilities."""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout=30, interval=1):
        """Wait for a condition to be met within timeout."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        
        return False
    
    @staticmethod
    def create_test_trend_data():
        """Create test trend data for integration tests."""
        return {
            "topic": "Integration Test AI Trend",
            "source": "test_source",
            "popularity_score": 85.5,
            "growth_rate": 15.2,
            "category": "Technology",
            "region": "Global",
            "keywords": ["integration", "test", "AI", "content"],
            "collected_at": datetime.utcnow().isoformat(),
            "raw_data": {
                "search_volume": 50000,
                "competition": "medium",
                "related_topics": ["automation", "testing", "AI tools"]
            }
        }
    
    @staticmethod
    def create_test_content_opportunity():
        """Create test content opportunity for integration tests."""
        return {
            "trend_id": "test_trend_123",
            "suggested_angle": "How to Build Integration Tests for AI Systems",
            "estimated_views": 25000,
            "competition_level": "low",
            "production_cost": 15.00,
            "estimated_roi": 3.5,
            "priority_score": 7.8,
            "status": "pending",
            "content_type": "educational",
            "target_platforms": ["youtube", "tiktok"],
            "created_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def validate_content_flow_data(data: Dict[str, Any]) -> bool:
        """Validate that data has proper structure for content flow."""
        required_fields = ["trend_data", "opportunity_data", "content_plan", "generated_assets"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_upload_results(results: List[Dict[str, Any]]) -> bool:
        """Validate upload results structure."""
        for result in results:
            required_fields = ["status", "platform_id", "url"]
            if not all(field in result for field in required_fields):
                return False
            
            if result["status"] not in ["success", "error"]:
                return False
        
        return True

# Pytest markers for integration tests
pytest.mark.integration = pytest.mark.asyncio
pytest.mark.slow = pytest.mark.asyncio
pytest.mark.live_api = pytest.mark.skipif(
    not INTEGRATION_CONFIG["enable_live_apis"],
    reason="Live API testing disabled"
)

@pytest.fixture
def integration_helper():
    """Integration test helper instance."""
    return IntegrationTestHelper()

# Common test data
SAMPLE_USER_REQUEST = "Create an educational video about machine learning for beginners"

SAMPLE_TREND_DATA = {
    "topic": "Machine Learning Basics",
    "source": "youtube",
    "popularity_score": 82.3,
    "growth_rate": 12.5,
    "category": "Education",
    "region": "Global",
    "keywords": ["machine learning", "AI", "beginners", "tutorial"],
    "collected_at": datetime.utcnow().isoformat()
}

SAMPLE_UPLOAD_METADATA = {
    "title": "Machine Learning for Beginners - Complete Guide",
    "description": "Learn machine learning from scratch with this comprehensive tutorial",
    "tags": ["machine learning", "AI", "tutorial", "beginners", "education"],
    "category": "Education",
    "privacy": "public"
}