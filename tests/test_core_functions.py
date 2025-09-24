"""
Unit Tests for Core Functions
Test individual components and their functionality
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from content_engine.services.ai_director import AIDirector
from content_engine.services.trend_analyzer import TrendAnalyzer
from content_engine.services.opportunity_engine import OpportunityEngine
from content_engine.models.quality_tier import QualityTier
from trend_monitor.services.trend_collector import TrendCollector
from database.repositories.trend_repository import TrendRepository
from database.repositories.opportunity_repository import OpportunityRepository

class TestAIDirector:
    """Test AI Director functionality"""
    
    def test_ai_director_initialization(self):
        """Test AI Director initializes correctly"""
        director = AIDirector(quality_tier=QualityTier.BUDGET)
        
        assert director.quality_tier == QualityTier.BUDGET
        assert director.service_registry is not None
        assert director.config is not None
    
    def test_content_plan_creation(self, mock_ai_services):
        """Test content plan creation with mocked AI services"""
        director = AIDirector(quality_tier=QualityTier.BUDGET)
        
        opportunity_data = {
            'id': 'test-opp-123',
            'trend_topic': 'AI Technology',
            'suggested_angle': 'Top 10 AI Tools',
            'competition_level': 'medium',
            'estimated_views': 50000
        }
        
        # Test content plan creation
        content_plan = director.create_content_plan(opportunity_data)
        
        assert content_plan is not None
        assert 'content_type' in content_plan
        assert 'title' in content_plan
        assert 'script' in content_plan
        assert 'visual_plan' in content_plan
        assert 'audio_plan' in content_plan
        assert 'opportunity_context' in content_plan
        assert 'production_metadata' in content_plan
    
    def test_fallback_plan_creation(self):
        """Test fallback plan when AI service fails"""
        director = AIDirector(quality_tier=QualityTier.BUDGET)
        
        # Mock AI service to raise exception
        with patch.object(director.service_registry, 'get_service') as mock_service:
            mock_service.return_value = None
            
            opportunity_data = {
                'suggested_angle': 'Test Content',
                'id': 'test-123'
            }
            
            content_plan = director.create_content_plan(opportunity_data)
            
            assert content_plan is not None
            assert content_plan['opportunity_context']['is_fallback'] == True
    
    def test_platform_adaptations(self, mock_ai_services):
        """Test platform-specific adaptations"""
        director = AIDirector(quality_tier=QualityTier.BALANCED)
        
        opportunity_data = {
            'suggested_angle': 'Test Platform Content',
            'estimated_views': 25000
        }
        
        content_plan = director.create_content_plan(opportunity_data)
        
        assert 'platform_adaptations' in content_plan
        adaptations = content_plan['platform_adaptations']
        
        # Check all major platforms are included
        assert 'youtube_shorts' in adaptations
        assert 'tiktok' in adaptations
        assert 'instagram_reels' in adaptations
        assert 'facebook' in adaptations
        
        # Check platform-specific fields
        assert 'aspect_ratio' in adaptations['youtube_shorts']
        assert 'optimal_duration' in adaptations['tiktok']
    
    def test_seo_optimization(self, mock_ai_services):
        """Test SEO optimization generation"""
        director = AIDirector(quality_tier=QualityTier.PREMIUM)
        
        opportunity_data = {
            'suggested_angle': 'Educational Content About AI',
            'estimated_views': 100000
        }
        
        content_plan = director.create_content_plan(opportunity_data)
        
        assert 'seo_optimization' in content_plan
        seo = content_plan['seo_optimization']
        
        assert 'primary_keywords' in seo
        assert 'hashtag_strategy' in seo
        assert 'title_optimization' in seo
        assert 'timing_strategy' in seo

class TestTrendAnalyzer:
    """Test Trend Analyzer functionality"""
    
    def test_trend_analyzer_initialization(self):
        """Test trend analyzer initializes correctly"""
        analyzer = TrendAnalyzer()
        assert analyzer is not None
    
    def test_trend_potential_analysis(self, sample_trends, mock_ai_services):
        """Test trend potential analysis"""
        analyzer = TrendAnalyzer()
        trend = sample_trends[0]  # AI Technology trend
        
        # Mock the AI analysis response
        mock_analysis = {
            'viral_potential': 8,
            'content_saturation': 6,
            'audience_interest': 9,
            'monetization_opportunity': 7,
            'content_angles': [
                'Top 10 AI Tools for 2025',
                'How AI Will Change Your Job',
                'AI vs Human: The Ultimate Test'
            ]
        }
        
        with patch.object(analyzer, 'ai_service') as mock_ai:
            mock_ai.analyze.return_value = mock_analysis
            
            result = analyzer.analyze_trend_potential(trend)
            
            assert result is not None
            assert 'viral_potential' in result
            assert result['viral_potential'] == 8
            assert len(result['content_angles']) == 3
    
    def test_trend_scoring(self, sample_trends):
        """Test trend scoring algorithm"""
        analyzer = TrendAnalyzer()
        trend = sample_trends[0]
        
        # Test scoring calculation
        score = analyzer.calculate_trend_score(trend)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 10
    
    def test_competition_analysis(self, sample_trends):
        """Test competition level analysis"""
        analyzer = TrendAnalyzer()
        trend = sample_trends[0]
        
        competition_level = analyzer.analyze_competition_level(trend)
        
        assert competition_level in ['low', 'medium', 'high']

class TestOpportunityEngine:
    """Test Opportunity Engine functionality"""
    
    def test_opportunity_engine_initialization(self):
        """Test opportunity engine initializes correctly"""
        engine = OpportunityEngine()
        assert engine is not None
    
    def test_opportunity_generation(self, sample_trends, mock_ai_services):
        """Test opportunity generation from trends"""
        engine = OpportunityEngine()
        trend = sample_trends[0]
        
        mock_analysis = {
            'viral_potential': 8,
            'content_saturation': 5,
            'audience_interest': 9
        }
        
        opportunities = engine.generate_opportunities_for_trend(trend, mock_analysis)
        
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0
        
        # Check opportunity structure
        opp = opportunities[0]
        assert hasattr(opp, 'trend_id')
        assert hasattr(opp, 'suggested_angle')
        assert hasattr(opp, 'estimated_views')
        assert hasattr(opp, 'competition_level')
    
    def test_roi_calculation(self, sample_opportunities):
        """Test ROI calculation"""
        engine = OpportunityEngine()
        opportunity = sample_opportunities[0]
        
        roi = engine.calculate_estimated_roi(opportunity)
        
        assert isinstance(roi, (int, float))
        assert roi > 0
    
    def test_priority_scoring(self, sample_opportunities):
        """Test priority scoring"""
        engine = OpportunityEngine()
        opportunity = sample_opportunities[0]
        
        priority = engine.calculate_priority_score(opportunity)
        
        assert isinstance(priority, (int, float))
        assert 0 <= priority <= 10

class TestTrendCollector:
    """Test Trend Collector functionality"""
    
    def test_trend_collector_initialization(self):
        """Test trend collector initializes correctly"""
        collector = TrendCollector()
        assert collector is not None
        assert hasattr(collector, 'sources')
    
    @pytest.mark.asyncio
    async def test_trend_collection(self, mock_trend_sources):
        """Test trend collection from multiple sources"""
        collector = TrendCollector()
        
        trends = await collector.collect_all_trends()
        
        assert isinstance(trends, list)
        assert len(trends) > 0
        
        # Check trend data structure
        trend = trends[0]
        assert 'topic' in trend
        assert 'source' in trend
        assert 'popularity_score' in trend
    
    @pytest.mark.asyncio
    async def test_youtube_trend_collection(self, mock_trend_sources):
        """Test YouTube-specific trend collection"""
        collector = TrendCollector()
        
        youtube_trends = await collector.collect_youtube_trends()
        
        assert isinstance(youtube_trends, list)
        if youtube_trends:  # If mock data is available
            trend = youtube_trends[0]
            assert 'title' in trend
            assert 'views' in trend
    
    @pytest.mark.asyncio
    async def test_trend_filtering(self, mock_trend_sources):
        """Test trend filtering and validation"""
        collector = TrendCollector()
        
        raw_trends = [
            {'title': 'Valid Trend', 'views': 100000, 'category': 'tech'},
            {'title': 'Low Quality', 'views': 100, 'category': 'spam'},
            {'title': 'Another Valid Trend', 'views': 50000, 'category': 'education'}
        ]
        
        filtered_trends = collector.filter_trends(raw_trends)
        
        # Should filter out low-quality trends
        assert len(filtered_trends) < len(raw_trends)

class TestRepositories:
    """Test Repository functionality"""
    
    def test_trend_repository_create(self, db_session):
        """Test creating trends in repository"""
        repo = TrendRepository()
        
        trend_data = {
            'source': 'test',
            'topic': 'Test Repository Trend',
            'keywords': ['test', 'repository'],
            'popularity_score': 7.5,
            'growth_rate': 12.3,
            'category': 'test',
            'region': 'thailand'
        }
        
        trend = repo.create_trend(trend_data)
        
        assert trend is not None
        assert trend.topic == 'Test Repository Trend'
        assert trend.popularity_score == 7.5
    
    def test_trend_repository_get_recent(self, db_session, sample_trends):
        """Test getting recent trends"""
        repo = TrendRepository()
        
        recent_trends = repo.get_recent_trends(limit=5)
        
        assert isinstance(recent_trends, list)
        assert len(recent_trends) <= 5
        if recent_trends:
            assert hasattr(recent_trends[0], 'topic')
    
    def test_opportunity_repository_create(self, db_session, sample_trends):
        """Test creating opportunities in repository"""
        repo = OpportunityRepository()
        
        opportunity_data = {
            'trend_id': sample_trends[0].id,
            'suggested_angle': 'Test Repository Opportunity',
            'estimated_views': 25000,
            'competition_level': 'medium',
            'production_cost': 30.0,
            'estimated_roi': 2.5,
            'priority_score': 7.0,
            'status': 'pending'
        }
        
        opportunity = repo.create_opportunity(opportunity_data)
        
        assert opportunity is not None
        assert opportunity.suggested_angle == 'Test Repository Opportunity'
        assert opportunity.estimated_roi == 2.5
    
    def test_opportunity_repository_get_by_roi(self, db_session, sample_opportunities):
        """Test getting opportunities by ROI"""
        repo = OpportunityRepository()
        
        high_roi_opportunities = repo.get_opportunities(min_roi=3.0)
        
        assert isinstance(high_roi_opportunities, list)
        # All returned opportunities should have ROI >= 3.0
        for opp in high_roi_opportunities:
            assert opp.estimated_roi >= 3.0

class TestDataValidation:
    """Test data validation and sanitization"""
    
    def test_trend_data_validation(self):
        """Test trend data validation"""
        from shared.models.trend_model import TrendModel
        
        # Valid trend data
        valid_data = {
            'source': 'youtube',
            'topic': 'Valid Trend Topic',
            'keywords': ['valid', 'trend'],
            'popularity_score': 8.5,
            'growth_rate': 15.2,
            'category': 'technology'
        }
        
        trend = TrendModel(**valid_data)
        assert trend.is_valid()
        
        # Invalid trend data
        invalid_data = {
            'source': '',  # Empty source
            'topic': 'x' * 300,  # Too long
            'popularity_score': 15,  # Out of range
            'growth_rate': -5  # Negative growth
        }
        
        with pytest.raises(ValueError):
            TrendModel(**invalid_data)
    
    def test_content_plan_validation(self):
        """Test content plan validation"""
        valid_plan = {
            'content_type': 'educational',
            'title': 'Valid Title',
            'script': {
                'hook': 'Valid hook',
                'main_content': 'Valid main content',
                'cta': 'Valid CTA'
            },
            'visual_plan': {
                'style': 'realistic',
                'scenes': ['Scene 1', 'Scene 2']
            }
        }
        
        # Should not raise any exceptions
        from content_engine.utils.content_validator import ContentValidator
        validator = ContentValidator()
        
        assert validator.validate_content_plan(valid_plan) == True
    
    def test_api_input_sanitization(self):
        """Test API input sanitization"""
        from shared.utils.sanitizer import APISanitizer
        
        sanitizer = APISanitizer()
        
        # Test SQL injection prevention
        malicious_input = "'; DROP TABLE users; --"
        sanitized = sanitizer.sanitize_string(malicious_input)
        assert 'DROP TABLE' not in sanitized
        
        # Test XSS prevention
        xss_input = "<script>alert('xss')</script>"
        sanitized = sanitizer.sanitize_string(xss_input)
        assert '<script>' not in sanitized

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_ai_service_timeout(self, mock_ai_services):
        """Test handling of AI service timeouts"""
        director = AIDirector()
        
        # Mock timeout exception
        with patch.object(director.service_registry, 'get_service') as mock_service:
            mock_service.side_effect = TimeoutError("AI service timeout")
            
            opportunity_data = {'suggested_angle': 'Test Timeout'}
            
            # Should return fallback plan instead of crashing
            content_plan = director.create_content_plan(opportunity_data)
            
            assert content_plan is not None
            assert content_plan.get('opportunity_context', {}).get('is_fallback') == True
    
    def test_database_connection_failure(self, db_session):
        """Test handling of database connection failures"""
        repo = TrendRepository()
        
        # Mock database connection failure
        with patch.object(repo, 'Session') as mock_session:
            mock_session.side_effect = ConnectionError("Database connection failed")
            
            # Should handle gracefully without crashing
            trends = repo.get_recent_trends()
            assert trends == []  # Should return empty list, not crash
    
    def test_invalid_api_response(self, mock_ai_services):
        """Test handling of invalid AI API responses"""
        director = AIDirector()
        
        # Mock invalid JSON response
        with patch.object(director.service_registry, 'get_service') as mock_service:
            mock_ai = Mock()
            mock_ai.generate_content_plan.return_value = "invalid json response"
            mock_service.return_value = mock_ai
            
            opportunity_data = {'suggested_angle': 'Test Invalid Response'}
            
            # Should handle invalid response gracefully
            content_plan = director.create_content_plan(opportunity_data)
            assert content_plan is not None
    
    def test_rate_limit_handling(self):
        """Test handling of API rate limits"""
        from shared.utils.rate_limiter import RateLimiter
        
        rate_limiter = RateLimiter(max_requests=5, time_window=60)
        
        # Should allow requests under limit
        for i in range(5):
            assert rate_limiter.is_allowed('test_user') == True
        
        # Should block after limit exceeded
        assert rate_limiter.is_allowed('test_user') == False
    
    def test_empty_trend_data_handling(self):
        """Test handling of empty trend data"""
        analyzer = TrendAnalyzer()
        
        # Test with None trend
        result = analyzer.analyze_trend_potential(None)
        assert result is not None
        assert 'error' in result or 'viral_potential' in result
        
        # Test with empty trend object
        empty_trend = Mock()
        empty_trend.topic = ""
        empty_trend.keywords = []
        empty_trend.popularity_score = 0
        
        result = analyzer.analyze_trend_potential(empty_trend)
        assert result is not None

class TestPerformanceMetrics:
    """Test performance monitoring and metrics"""
    
    def test_response_time_measurement(self, client):
        """Test API response time measurement"""
        import time
        
        start_time = time.time()
        response = client.get('/api/trends')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # API should respond within reasonable time (adjust threshold as needed)
        assert response_time < 2.0  # 2 seconds max
        assert response.status_code in [200, 404, 500]  # Valid HTTP status
    
    def test_memory_usage(self):
        """Test memory usage during operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform memory-intensive operation
        director = AIDirector()
        
        # Create multiple content plans
        for i in range(10):
            opportunity_data = {
                'suggested_angle': f'Test Memory {i}',
                'estimated_views': 10000 + i * 1000
            }
            content_plan = director.create_content_plan(opportunity_data)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent API requests"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.get('/api/stats')
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0  # No errors should occur
        assert len(results) == 10  # All requests should complete
        assert all(status in [200, 404, 500] for status in results)

class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""
    
    def test_complete_content_creation_flow(self, client, db_session, mock_ai_services, mock_trend_sources):
        """Test complete flow from trend collection to content creation"""
        
        # Step 1: Collect trends
        response = client.post('/api/collect-trends')
        assert response.status_code == 200
        
        collect_result = response.get_json()
        assert collect_result['success'] == True
        assert collect_result['count'] > 0
        
        # Step 2: Analyze opportunities
        response = client.post('/api/analyze-opportunities')
        assert response.status_code == 200
        
        analyze_result = response.get_json()
        assert analyze_result['success'] == True
        assert analyze_result['count'] > 0
        
        # Step 3: Get opportunities
        response = client.get('/api/opportunities?limit=5')
        assert response.status_code == 200
        
        opportunities = response.get_json()
        assert len(opportunities) > 0
        
        # Step 4: Generate content
        opportunity_ids = [opp['id'] for opp in opportunities[:2]]
        
        response = client.post('/api/generate-content', 
                              json={'opportunity_ids': opportunity_ids})
        assert response.status_code == 200
        
        content_result = response.get_json()
        assert content_result['success'] == True
        assert content_result['count'] > 0
    
    def test_analytics_data_flow(self, client, sample_performance):
        """Test analytics data aggregation and presentation"""
        
        # Test KPIs endpoint
        response = client.get('/api/analytics/kpis?timeRange=7d')
        assert response.status_code == 200
        
        kpis = response.get_json()
        assert 'total_views' in kpis
        assert 'total_engagement' in kpis
        assert 'average_roi' in kpis
        
        # Test performance timeline
        response = client.get('/api/analytics/performance?timeRange=7d')
        assert response.status_code == 200
        
        performance = response.get_json()
        assert 'timeline' in performance
        assert isinstance(performance['timeline'], list)
        
        # Test platform metrics
        response = client.get('/api/analytics/platforms?timeRange=7d')
        assert response.status_code == 200
        
        platforms = response.get_json()
        assert 'platforms' in platforms
        assert isinstance(platforms['platforms'], list)
    
    def test_error_recovery_flow(self, client):
        """Test system recovery from various error scenarios"""
        
        # Test invalid API request
        response = client.post('/api/generate-content', 
                              json={'invalid_field': 'invalid_value'})
        
        # Should return error but not crash
        assert response.status_code in [400, 422, 500]
        
        # Test missing required fields
        response = client.post('/api/generate-content', json={})
        assert response.status_code in [400, 422]
        
        # Test system should still work after errors
        response = client.get('/api/stats')
        assert response.status_code == 200

class TestSecurityFeatures:
    """Test security features and protections"""
    
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection attacks"""
        
        # Attempt SQL injection in query parameters
        malicious_query = "'; DROP TABLE trends; --"
        
        response = client.get(f'/api/trends?category={malicious_query}')
        
        # Should not crash or return error indicating SQL injection worked
        assert response.status_code in [200, 400, 422]
        
        # System should still be functional
        response = client.get('/api/stats')
        assert response.status_code == 200
    
    def test_xss_protection(self, client):
        """Test protection against XSS attacks"""
        
        # Attempt XSS in POST data
        xss_payload = "<script>alert('xss')</script>"
        
        response = client.post('/api/generate-content', 
                              json={'opportunity_ids': [xss_payload]})
        
        # Should handle gracefully
        assert response.status_code in [400, 422, 500]
        
        if response.status_code == 200:
            # If successful, response should not contain unescaped script tags
            response_text = response.get_data(as_text=True)
            assert '<script>' not in response_text
    
    def test_rate_limiting(self, client):
        """Test API rate limiting protection"""
        
        # Make multiple rapid requests
        responses = []
        for i in range(20):
            response = client.get('/api/stats')
            responses.append(response.status_code)
        
        # Should either allow all requests or start rate limiting
        # (depending on configuration)
        successful_requests = sum(1 for status in responses if status == 200)
        rate_limited_requests = sum(1 for status in responses if status == 429)
        
        # At least some requests should be successful
        assert successful_requests > 0
        
        # If rate limiting is enabled, should see 429 status codes
        if rate_limited_requests > 0:
            assert rate_limited_requests < len(responses)

class TestDataConsistency:
    """Test data consistency and integrity"""
    
    def test_trend_opportunity_consistency(self, db_session, sample_trends, sample_opportunities):
        """Test consistency between trends and opportunities"""
        
        trend_repo = TrendRepository()
        opp_repo = OpportunityRepository()
        
        # Get trends and their opportunities
        trend = sample_trends[0]
        opportunities = opp_repo.get_opportunities_by_trend(trend.id)
        
        # All opportunities should reference valid trends
        for opp in opportunities:
            assert opp.trend_id == trend.id
            referenced_trend = trend_repo.get_by_id(opp.trend_id)
            assert referenced_trend is not None
    
    def test_content_upload_consistency(self, db_session, sample_content, sample_uploads):
        """Test consistency between content and uploads"""
        
        content_repo = ContentRepository()
        
        # Get content and its uploads
        content = sample_content[0]
        uploads = content_repo.get_uploads_for_content(content.id)
        
        # All uploads should reference valid content
        for upload in uploads:
            assert upload.content_id == content.id
    
    def test_performance_data_integrity(self, db_session, sample_uploads, sample_performance):
        """Test performance data integrity"""
        
        from database.repositories.performance_repository import PerformanceRepository
        perf_repo = PerformanceRepository()
        
        # Check that performance metrics reference valid uploads
        for metric in sample_performance:
            upload = db_session.query(Uploads).filter_by(id=metric.upload_id).first()
            assert upload is not None
            
            # Check data consistency
            assert metric.views >= 0
            assert metric.likes >= 0
            assert metric.comments >= 0
            assert metric.shares >= 0
            assert metric.cost >= 0
            assert metric.revenue >= 0

# Utility functions for testing
def run_all_tests():
    """Run all tests and return results"""
    pytest.main(['-v', '--tb=short', 'tests/'])

def run_specific_test_class(test_class_name):
    """Run specific test class"""
    pytest.main(['-v', f'tests/test_core_functions.py::{test_class_name}'])

def run_integration_tests_only():
    """Run only integration tests"""
    pytest.main(['-v', '-k', 'integration', 'tests/'])

if __name__ == '__main__':
    # Run tests if this file is executed directly
    run_all_tests()