"""
Test Configuration and Fixtures
Setup for comprehensive testing of AI Content Factory
"""

import pytest
import os
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import Flask

# Import our modules
from app import app as flask_app
from database.models.base import Base
from database.models.trends import Trends
from database.models.content_opportunities import ContentOpportunities
from database.models.content_items import ContentItems
from database.models.uploads import Uploads
from database.models.performance_metrics import PerformanceMetrics

@pytest.fixture(scope="session")
def test_database():
    """Create a temporary test database"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Create engine and tables
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def app(test_database):
    """Create test Flask application"""
    flask_app.config.update({
        'TESTING': True,
        'DATABASE_URL': str(test_database.url),
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    with flask_app.app_context():
        yield flask_app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def db_session(test_database):
    """Create database session for tests"""
    Session = sessionmaker(bind=test_database)
    session = Session()
    
    yield session
    
    session.close()

@pytest.fixture
def sample_trends(db_session):
    """Create sample trend data"""
    trends = [
        Trends(
            source='youtube',
            topic='AI Technology Trends 2025',
            keywords=['AI', 'technology', 'trends', '2025'],
            popularity_score=8.5,
            growth_rate=15.2,
            category='technology',
            region='thailand',
            collected_at=datetime.now()
        ),
        Trends(
            source='google',
            topic='Thai Street Food Guide',
            keywords=['thai', 'food', 'street', 'guide'],
            popularity_score=7.2,
            growth_rate=12.8,
            category='food',
            region='thailand',
            collected_at=datetime.now()
        ),
        Trends(
            source='tiktok',
            topic='Dance Challenge 2025',
            keywords=['dance', 'challenge', 'viral'],
            popularity_score=9.1,
            growth_rate=25.6,
            category='entertainment',
            region='global',
            collected_at=datetime.now()
        )
    ]
    
    for trend in trends:
        db_session.add(trend)
    db_session.commit()
    
    return trends

@pytest.fixture
def sample_opportunities(db_session, sample_trends):
    """Create sample opportunity data"""
    opportunities = [
        ContentOpportunities(
            trend_id=sample_trends[0].id,
            suggested_angle='10 AI Tools That Will Change Your Life',
            estimated_views=50000,
            competition_level='medium',
            production_cost=25.00,
            estimated_roi=3.2,
            priority_score=8.5,
            status='pending',
            created_at=datetime.now()
        ),
        ContentOpportunities(
            trend_id=sample_trends[1].id,
            suggested_angle='Best Street Food in Bangkok Under 50 Baht',
            estimated_views=35000,
            competition_level='high',
            production_cost=40.00,
            estimated_roi=2.8,
            priority_score=7.2,
            status='pending',
            created_at=datetime.now()
        )
    ]
    
    for opp in opportunities:
        db_session.add(opp)
    db_session.commit()
    
    return opportunities

@pytest.fixture
def sample_content(db_session, sample_opportunities):
    """Create sample content data"""
    content_items = [
        ContentItems(
            opportunity_id=sample_opportunities[0].id,
            title='10 AI Tools That Will Change Your Life in 2025',
            description='Discover the most powerful AI tools for productivity',
            content_plan={
                'content_type': 'educational',
                'script': {
                    'hook': 'These AI tools will blow your mind!',
                    'main_content': 'Let me show you 10 incredible AI tools...',
                    'cta': 'Which tool will you try first? Comment below!'
                }
            },
            production_status='completed',
            created_at=datetime.now()
        ),
        ContentItems(
            opportunity_id=sample_opportunities[1].id,
            title='Bangkok Street Food Under 50 Baht',
            description='Amazing street food you can afford every day',
            content_plan={
                'content_type': 'entertainment',
                'script': {
                    'hook': 'Cheap and delicious? Yes, please!',
                    'main_content': 'Here are my top picks for budget street food...',
                    'cta': 'What\'s your favorite cheap eat? Let me know!'
                }
            },
            production_status='processing',
            created_at=datetime.now()
        )
    ]
    
    for content in content_items:
        db_session.add(content)
    db_session.commit()
    
    return content_items

@pytest.fixture
def sample_uploads(db_session, sample_content):
    """Create sample upload data"""
    uploads = [
        Uploads(
            content_id=sample_content[0].id,
            platform='youtube',
            platform_id='abc123xyz',
            url='https://youtube.com/watch?v=abc123xyz',
            metadata={
                'title': '10 AI Tools That Will Change Your Life in 2025',
                'description': 'Discover the most powerful AI tools...',
                'tags': ['AI', 'productivity', 'tools']
            },
            uploaded_at=datetime.now()
        ),
        Uploads(
            content_id=sample_content[0].id,
            platform='tiktok',
            platform_id='tiktok789',
            url='https://tiktok.com/@user/video/tiktok789',
            metadata={
                'caption': '10 AI Tools That Will Change Your Life #AI #productivity',
                'hashtags': ['AI', 'productivity', 'viral']
            },
            uploaded_at=datetime.now()
        )
    ]
    
    for upload in uploads:
        db_session.add(upload)
    db_session.commit()
    
    return uploads

@pytest.fixture
def sample_performance(db_session, sample_uploads):
    """Create sample performance data"""
    performance_metrics = [
        PerformanceMetrics(
            upload_id=sample_uploads[0].id,
            views=15420,
            likes=892,
            comments=156,
            shares=78,
            revenue=65.50,
            cost=25.00,
            measured_at=datetime.now()
        ),
        PerformanceMetrics(
            upload_id=sample_uploads[1].id,
            views=8930,
            likes=445,
            comments=89,
            shares=123,
            revenue=42.30,
            cost=25.00,
            measured_at=datetime.now()
        )
    ]
    
    for metric in performance_metrics:
        db_session.add(metric)
    db_session.commit()
    
    return performance_metrics

@pytest.fixture
def mock_ai_services():
    """Mock AI services for testing"""
    with patch('content_engine.ai_services.text_ai.groq_service.GroqService') as mock_groq, \
         patch('content_engine.ai_services.text_ai.openai_service.OpenAIService') as mock_openai, \
         patch('content_engine.ai_services.image_ai.stable_diffusion.StableDiffusionService') as mock_sd:
        
        # Mock Groq service
        mock_groq_instance = Mock()
        mock_groq_instance.generate_content_plan.return_value = {
            "content_type": "educational",
            "title": "Test AI Generated Title",
            "script": {
                "hook": "Test hook",
                "main_content": "Test content",
                "cta": "Test CTA"
            },
            "visual_plan": {
                "style": "realistic",
                "scenes": ["Scene 1", "Scene 2"]
            }
        }
        mock_groq.return_value = mock_groq_instance
        
        # Mock OpenAI service
        mock_openai_instance = Mock()
        mock_openai_instance.generate_content_plan.return_value = {
            "content_type": "entertainment",
            "title": "Premium AI Generated Title",
            "script": {
                "hook": "Premium hook",
                "main_content": "Premium content",
                "cta": "Premium CTA"
            }
        }
        mock_openai.return_value = mock_openai_instance
        
        # Mock Stable Diffusion service
        mock_sd_instance = Mock()
        mock_sd_instance.generate_image.return_value = "mock_image_data"
        mock_sd.return_value = mock_sd_instance
        
        yield {
            'groq': mock_groq_instance,
            'openai': mock_openai_instance,
            'stable_diffusion': mock_sd_instance
        }

@pytest.fixture
def mock_trend_sources():
    """Mock external trend data sources"""
    youtube_trends = [
        {
            'title': 'Viral Video Trend',
            'views': 1000000,
            'growth_rate': 15.5,
            'category': 'entertainment'
        },
        {
            'title': 'Tech Review Trend',
            'views': 500000,
            'growth_rate': 8.2,
            'category': 'technology'
        }
    ]
    
    google_trends = [
        {
            'query': 'AI tools 2025',
            'interest': 85,
            'region': 'thailand',
            'category': 'technology'
        },
        {
            'query': 'bangkok food',
            'interest': 72,
            'region': 'thailand',
            'category': 'food'
        }
    ]
    
    with patch('trend_monitor.services.youtube_trends.YouTubeTrends.get_trending') as mock_yt, \
         patch('trend_monitor.services.google_trends.GoogleTrends.get_trending') as mock_gt:
        
        mock_yt.return_value = youtube_trends
        mock_gt.return_value = google_trends
        
        yield {
            'youtube': youtube_trends,
            'google': google_trends
        }

@pytest.fixture
def api_headers():
    """Common headers for API requests"""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

@pytest.fixture
def test_config():
    """Test configuration values"""
    return {
        'DATABASE_URL': 'sqlite:///:memory:',
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'API_RATE_LIMIT': 1000,
        'GROQ_API_KEY': 'test-groq-key',
        'OPENAI_API_KEY': 'test-openai-key',
        'YOUTUBE_API_KEY': 'test-youtube-key'
    }

# Helper functions for tests
def create_test_trend(db_session, **kwargs):
    """Helper to create test trend"""
    defaults = {
        'source': 'test',
        'topic': 'Test Trend',
        'keywords': ['test'],
        'popularity_score': 5.0,
        'growth_rate': 10.0,
        'category': 'test',
        'region': 'test',
        'collected_at': datetime.now()
    }
    defaults.update(kwargs)
    
    trend = Trends(**defaults)
    db_session.add(trend)
    db_session.commit()
    return trend

def create_test_opportunity(db_session, trend_id, **kwargs):
    """Helper to create test opportunity"""
    defaults = {
        'trend_id': trend_id,
        'suggested_angle': 'Test Angle',
        'estimated_views': 10000,
        'competition_level': 'medium',
        'production_cost': 20.0,
        'estimated_roi': 2.0,
        'priority_score': 5.0,
        'status': 'pending',
        'created_at': datetime.now()
    }
    defaults.update(kwargs)
    
    opportunity = ContentOpportunities(**defaults)
    db_session.add(opportunity)
    db_session.commit()
    return opportunity

def assert_api_response(response, expected_status=200, expected_keys=None):
    """Helper to assert API response"""
    assert response.status_code == expected_status
    
    if expected_keys:
        data = response.get_json()
        assert data is not None
        for key in expected_keys:
            assert key in data

# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_trends(count=10):
        """Generate multiple test trends"""
        categories = ['technology', 'entertainment', 'food', 'travel', 'education']
        sources = ['youtube', 'google', 'tiktok', 'twitter']
        
        trends = []
        for i in range(count):
            trend = {
                'source': sources[i % len(sources)],
                'topic': f'Test Trend {i+1}',
                'keywords': [f'keyword{i}', f'test{i}'],
                'popularity_score': 1 + (i % 10),
                'growth_rate': 5 + (i % 20),
                'category': categories[i % len(categories)],
                'region': 'thailand',
                'collected_at': datetime.now() - timedelta(days=i)
            }
            trends.append(trend)
        
        return trends
    
    @staticmethod
    def generate_performance_data(upload_id, days=7):
        """Generate performance data over time"""
        performance_data = []
        base_views = 1000
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            views = base_views + (i * 200) + (i * i * 10)  # Simulated growth
            
            performance = {
                'upload_id': upload_id,
                'views': views,
                'likes': int(views * 0.05),  # 5% like rate
                'comments': int(views * 0.01),  # 1% comment rate
                'shares': int(views * 0.005),  # 0.5% share rate
                'revenue': views * 0.001,  # $0.001 per view
                'cost': 25.0,  # Fixed cost
                'measured_at': date
            }
            performance_data.append(performance)
        
        return performance_data