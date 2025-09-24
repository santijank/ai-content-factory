"""
Unit Tests for Trend Collector
==============================

Tests for the trend collection services including:
- TrendCollector main class
- YouTube trends collection
- Google trends collection
- Twitter trends collection
- Reddit trends collection
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio
from datetime import datetime, timedelta
import json

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from trend_monitor.services.trend_collector import TrendCollector
from trend_monitor.services.youtube_trends import YouTubeTrendsService
from trend_monitor.services.google_trends import GoogleTrendsService
from trend_monitor.models.trend_data import TrendData


class TestTrendCollector:
    """Test cases for TrendCollector main class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for trend collector."""
        return {
            'sources': {
                'youtube': {'enabled': True, 'api_key': 'test_key'},
                'google_trends': {'enabled': True},
                'twitter': {'enabled': False},
                'reddit': {'enabled': True}
            }
        }
    
    @pytest.fixture
    def trend_collector(self, mock_config):
        """Create TrendCollector instance with mocked config."""
        with patch('trend_monitor.services.trend_collector.ConfigManager') as mock_config_manager:
            mock_config_manager.return_value.get_trend_sources.return_value = mock_config
            return TrendCollector()
    
    @pytest.mark.asyncio
    async def test_collect_trends_success(self, trend_collector):
        """Test successful trend collection from multiple sources."""
        # Mock individual collection methods
        youtube_trends = [TrendData(
            topic="AI Tutorial",
            source="youtube",
            popularity_score=85.5,
            keywords=["AI", "tutorial", "beginner"]
        )]
        
        google_trends = [TrendData(
            topic="Machine Learning",
            source="google_trends",
            popularity_score=75.2,
            keywords=["ML", "data science", "python"]
        )]
        
        with patch.object(trend_collector, 'collect_youtube_trends', new_callable=AsyncMock) as mock_youtube, \
             patch.object(trend_collector, 'collect_google_trends', new_callable=AsyncMock) as mock_google, \
             patch.object(trend_collector, 'collect_twitter_trends', new_callable=AsyncMock) as mock_twitter, \
             patch.object(trend_collector, 'collect_reddit_trends', new_callable=AsyncMock) as mock_reddit:
            
            mock_youtube.return_value = youtube_trends
            mock_google.return_value = google_trends
            mock_twitter.return_value = []
            mock_reddit.return_value = []
            
            results = await trend_collector.collect_trends()
            
            # Assertions
            assert len(results) == 4  # All sources called
            assert mock_youtube.called
            assert mock_google.called
            assert mock_twitter.called
            assert mock_reddit.called
    
    @pytest.mark.asyncio
    async def test_collect_trends_with_failure(self, trend_collector):
        """Test trend collection with one source failing."""
        with patch.object(trend_collector, 'collect_youtube_trends', new_callable=AsyncMock) as mock_youtube, \
             patch.object(trend_collector, 'collect_google_trends', new_callable=AsyncMock) as mock_google, \
             patch.object(trend_collector, 'collect_twitter_trends', new_callable=AsyncMock) as mock_twitter, \
             patch.object(trend_collector, 'collect_reddit_trends', new_callable=AsyncMock) as mock_reddit:
            
            # Mock YouTube to raise exception
            mock_youtube.side_effect = Exception("API Error")
            mock_google.return_value = []
            mock_twitter.return_value = []
            mock_reddit.return_value = []
            
            results = await trend_collector.collect_trends()
            
            # Should handle exception gracefully
            assert len(results) == 4
            assert mock_youtube.called
    
    @pytest.mark.asyncio
    async def test_filter_and_deduplicate(self, trend_collector):
        """Test filtering and deduplication of collected trends."""
        trends = [
            TrendData(topic="AI Tutorial", source="youtube", popularity_score=85.5),
            TrendData(topic="AI Tutorial", source="google", popularity_score=70.0),  # Duplicate
            TrendData(topic="Cooking Tips", source="youtube", popularity_score=45.0),  # Low score
            TrendData(topic="Tech News", source="reddit", popularity_score=80.0)
        ]
        
        filtered = trend_collector.filter_and_deduplicate(trends, min_score=50.0)
        
        # Should keep only high-scoring unique trends
        assert len(filtered) == 2
        topics = [t.topic for t in filtered]
        assert "AI Tutorial" in topics
        assert "Tech News" in topics
        assert "Cooking Tips" not in topics


class TestYouTubeTrendsService:
    """Test cases for YouTube trends collection."""
    
    @pytest.fixture
    def youtube_service(self):
        """Create YouTubeTrendsService instance."""
        with patch('googleapiclient.discovery.build'):
            return YouTubeTrendsService(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_get_trending_videos_success(self, youtube_service):
        """Test successful retrieval of trending videos."""
        mock_response = {
            'items': [
                {
                    'snippet': {
                        'title': 'AI Content Creation Tutorial',
                        'description': 'Learn how to create content with AI',
                        'tags': ['AI', 'tutorial', 'content'],
                        'categoryId': '28'
                    },
                    'statistics': {
                        'viewCount': '100000',
                        'likeCount': '5000',
                        'commentCount': '500'
                    }
                }
            ]
        }
        
        with patch.object(youtube_service.youtube.videos(), 'list') as mock_list:
            mock_list.return_value.execute.return_value = mock_response
            
            trends = await youtube_service.get_trending_videos(region='US', max_results=10)
            
            assert len(trends) == 1
            assert trends[0].topic == 'AI Content Creation Tutorial'
            assert trends[0].source == 'youtube'
            assert 'AI' in trends[0].keywords
    
    @pytest.mark.asyncio
    async def test_get_trending_videos_api_error(self, youtube_service):
        """Test handling of YouTube API errors."""
        with patch.object(youtube_service.youtube.videos(), 'list') as mock_list:
            mock_list.return_value.execute.side_effect = Exception("Quota exceeded")
            
            trends = await youtube_service.get_trending_videos(region='US')
            
            # Should return empty list on error
            assert trends == []
    
    def test_calculate_popularity_score(self, youtube_service):
        """Test popularity score calculation."""
        video_data = {
            'statistics': {
                'viewCount': '100000',
                'likeCount': '5000',
                'commentCount': '500'
            }
        }
        
        score = youtube_service.calculate_popularity_score(video_data)
        
        assert isinstance(score, float)
        assert score > 0
        assert score <= 100
    
    def test_extract_keywords_from_video(self, youtube_service):
        """Test keyword extraction from video data."""
        video_data = {
            'snippet': {
                'title': 'AI Content Creation Tutorial for Beginners',
                'description': 'Learn artificial intelligence and machine learning',
                'tags': ['AI', 'tutorial', 'beginners', 'content']
            }
        }
        
        keywords = youtube_service.extract_keywords(video_data)
        
        assert 'AI' in keywords
        assert 'tutorial' in keywords
        assert 'content' in keywords
        assert len(keywords) <= 10  # Should limit keywords


class TestGoogleTrendsService:
    """Test cases for Google Trends collection."""
    
    @pytest.fixture
    def google_service(self):
        """Create GoogleTrendsService instance."""
        return GoogleTrendsService()
    
    @pytest.mark.asyncio
    async def test_get_trending_searches_success(self, google_service):
        """Test successful retrieval of trending searches."""
        mock_trending_data = [
            {
                'title': 'AI chatbot',
                'formattedTraffic': '200K+',
                'relatedQueries': ['chatbot AI', 'artificial intelligence']
            },
            {
                'title': 'video editing AI',
                'formattedTraffic': '150K+',
                'relatedQueries': ['AI video editor', 'automated editing']
            }
        ]
        
        with patch('pytrends.request.TrendReq') as mock_pytrends:
            mock_instance = Mock()
            mock_pytrends.return_value = mock_instance
            mock_instance.trending_searches.return_value = mock_trending_data
            
            trends = await google_service.get_trending_searches(region='US')
            
            assert len(trends) == 2
            assert any(t.topic == 'AI chatbot' for t in trends)
            assert all(t.source == 'google_trends' for t in trends)
    
    @pytest.mark.asyncio
    async def test_get_related_topics(self, google_service):
        """Test retrieval of related topics for a keyword."""
        mock_related_data = {
            'default': {
                'df': {
                    'topic_title': ['Machine Learning', 'Deep Learning', 'Neural Networks'],
                    'value': [100, 85, 70]
                }
            }
        }
        
        with patch('pytrends.request.TrendReq') as mock_pytrends:
            mock_instance = Mock()
            mock_pytrends.return_value = mock_instance
            mock_instance.related_topics.return_value = mock_related_data
            
            related = await google_service.get_related_topics('AI')
            
            assert len(related) == 3
            assert 'Machine Learning' in related
    
    def test_parse_traffic_volume(self, google_service):
        """Test parsing of traffic volume strings."""
        assert google_service.parse_traffic_volume('200K+') == 200000
        assert google_service.parse_traffic_volume('1.5M+') == 1500000
        assert google_service.parse_traffic_volume('500+') == 500
        assert google_service.parse_traffic_volume('unknown') == 0


class TestTrendDataModel:
    """Test cases for TrendData model."""
    
    def test_trend_data_creation(self):
        """Test creating TrendData instance."""
        trend = TrendData(
            topic="AI Tutorial",
            source="youtube",
            popularity_score=85.5,
            keywords=["AI", "tutorial", "education"]
        )
        
        assert trend.topic == "AI Tutorial"
        assert trend.source == "youtube"
        assert trend.popularity_score == 85.5
        assert len(trend.keywords) == 3
        assert isinstance(trend.id, str)
        assert trend.collected_at is not None
    
    def test_trend_data_validation(self):
        """Test TrendData validation."""
        # Should raise error for invalid popularity_score
        with pytest.raises(ValueError):
            TrendData(
                topic="Test",
                source="youtube",
                popularity_score=150.0,  # Invalid: > 100
                keywords=["test"]
            )
    
    def test_trend_data_serialization(self):
        """Test TrendData to_dict method."""
        trend = TrendData(
            topic="AI Tutorial",
            source="youtube",
            popularity_score=85.5,
            keywords=["AI", "tutorial"]
        )
        
        data = trend.to_dict()
        
        assert data['topic'] == "AI Tutorial"
        assert data['source'] == "youtube"
        assert data['popularity_score'] == 85.5
        assert 'id' in data
        assert 'collected_at' in data
    
    def test_trend_data_from_dict(self):
        """Test creating TrendData from dictionary."""
        data = {
            'topic': 'Test Topic',
            'source': 'test',
            'popularity_score': 75.0,
            'keywords': ['test', 'data'],
            'category': 'Technology',
            'region': 'US'
        }
        
        trend = TrendData.from_dict(data)
        
        assert trend.topic == 'Test Topic'
        assert trend.source == 'test'
        assert trend.popularity_score == 75.0
        assert trend.category == 'Technology'


# Integration tests for trend collection workflow
class TestTrendCollectionWorkflow:
    """Integration tests for the complete trend collection workflow."""
    
    @pytest.mark.asyncio
    async def test_full_collection_cycle(self):
        """Test a complete trend collection cycle."""
        with patch('trend_monitor.services.trend_collector.ConfigManager') as mock_config:
            mock_config.return_value.get_trend_sources.return_value = {
                'sources': {'youtube': {'enabled': True, 'api_key': 'test'}}
            }
            
            collector = TrendCollector()
            
            # Mock the collection process
            with patch.object(collector, 'collect_youtube_trends', new_callable=AsyncMock) as mock_collect:
                mock_trends = [
                    TrendData(topic=f"Trend {i}", source="youtube", popularity_score=80.0 + i)
                    for i in range(5)
                ]
                mock_collect.return_value = mock_trends
                
                # Execute collection
                all_trends = await collector.collect_trends()
                
                # Verify results
                assert len(all_trends) >= 1  # At least YouTube results
                mock_collect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery in trend collection."""
        collector = TrendCollector()
        
        # Mock services with mixed success/failure
        with patch.object(collector, 'collect_youtube_trends', new_callable=AsyncMock) as mock_yt, \
             patch.object(collector, 'collect_google_trends', new_callable=AsyncMock) as mock_gt:
            
            # YouTube fails, Google succeeds
            mock_yt.side_effect = Exception("Network error")
            mock_gt.return_value = [TrendData(topic="Test", source="google", popularity_score=70.0)]
            
            results = await collector.collect_trends()
            
            # Should continue despite YouTube failure
            assert len(results) > 0
            # Should have attempted both services
            assert mock_yt.called
            assert mock_gt.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])