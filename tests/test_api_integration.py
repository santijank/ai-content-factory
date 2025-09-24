"""
API Integration Tests
Test all API endpoints and their interactions
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

class TestMainAPIEndpoints:
    """Test main API endpoints functionality"""
    
    def test_stats_endpoint(self, client, sample_performance):
        """Test /api/stats endpoint"""
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'trends_today' in data
        assert 'opportunities_count' in data
        assert 'content_today' in data
        assert 'cost_today' in data
        assert 'last_updated' in data
        
        # Validate data types
        assert isinstance(data['trends_today'], int)
        assert isinstance(data['opportunities_count'], int)
        assert isinstance(data['content_today'], int)
        assert isinstance(data['cost_today'], (int, float))
    
    def test_trends_endpoint(self, client, sample_trends):
        """Test /api/trends endpoint"""
        
        # Test basic trends retrieval
        response = client.get('/api/trends')
        assert response.status_code == 200
        
        trends = response.get_json()
        assert isinstance(trends, list)
        
        if trends:
            trend = trends[0]
            required_fields = ['id', 'topic', 'popularity_score', 'growth_rate', 
                             'category', 'source', 'keywords']
            for field in required_fields:
                assert field in trend
        
        # Test with limit parameter
        response = client.get('/api/trends?limit=5')
        assert response.status_code == 200
        
        limited_trends = response.get_json()
        assert len(limited_trends) <= 5
        
        # Test with category filter
        response = client.get('/api/trends?category=technology')
        assert response.status_code == 200
        
        filtered_trends = response.get_json()
        for trend in filtered_trends:
            assert trend['category'] == 'technology'
    
    def test_opportunities_endpoint(self, client, sample_opportunities):
        """Test /api/opportunities endpoint"""
        
        # Test basic opportunities retrieval
        response = client.get('/api/opportunities')
        assert response.status_code == 200
        
        opportunities = response.get_json()
        assert isinstance(opportunities, list)
        
        if opportunities:
            opp = opportunities[0]
            required_fields = ['id', 'trend_id', 'suggested_angle', 'estimated_views',
                             'competition_level', 'production_cost', 'estimated_roi']
            for field in required_fields:
                assert field in opp
        
        # Test with status filter
        response = client.get('/api/opportunities?status=pending')
        assert response.status_code == 200
        
        # Test with ROI filter
        response = client.get('/api/opportunities?min_roi=2.0')
        assert response.status_code == 200
        
        high_roi_opps = response.get_json()
        for opp in high_roi_opps:
            assert opp['estimated_roi'] >= 2.0
    
    def test_content_endpoint(self, client, sample_content):
        """Test /api/content endpoint"""
        
        # Test basic content retrieval
        response = client.get('/api/content')
        assert response.status_code == 200
        
        content_items = response.get_json()
        assert isinstance(content_items, list)
        
        if content_items:
            item = content_items[0]
            required_fields = ['id', 'title', 'description', 'status', 'created_at']
            for field in required_fields:
                assert field in item
        
        # Test with status filter
        response = client.get('/api/content?status=completed')
        assert response.status_code == 200
        
        completed_content = response.get_json()
        for item in completed_content:
            assert item['status'] == 'completed'

class TestActionAPIEndpoints:
    """Test action-based API endpoints"""
    
    @patch('trend_monitor.services.trend_collector.TrendCollector.collect_all_trends')
    def test_collect_trends_endpoint(self, mock_collect, client):
        """Test /api/collect-trends endpoint"""
        
        # Mock successful trend collection
        mock_collect.return_value = [
            {
                'source': 'youtube',
                'topic': 'Test Trend 1',
                'keywords': ['test', 'trend'],
                'popularity_score': 8.0,
                'growth_rate': 15.0,
                'category': 'test'
            },
            {
                'source': 'google',
                'topic': 'Test Trend 2',
                'keywords': ['another', 'test'],
                'popularity_score': 7.5,
                'growth_rate': 12.0,
                'category': 'test'
            }
        ]
        
        response = client.post('/api/collect-trends')
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['success'] == True
        assert 'count' in result
        assert result['count'] > 0
        assert 'message' in result
        
        # Verify the collector was called
        mock_collect.assert_called_once()
    
    @patch('content_engine.services.trend_analyzer.TrendAnalyzer.analyze_trend_potential')
    @patch('content_engine.services.opportunity_engine.OpportunityEngine.generate_opportunities_for_trend')
    def test_analyze_opportunities_endpoint(self, mock_generate, mock_analyze, client, sample_trends):
        """Test /api/analyze-opportunities endpoint"""
        
        # Mock AI analysis
        mock_analyze.return_value = {
            'viral_potential': 8,
            'content_saturation': 5,
            'audience_interest': 9,
            'monetization_opportunity': 7
        }
        
        # Mock opportunity generation
        mock_opportunity = Mock()
        mock_opportunity.trend_id = sample_trends[0].id if sample_trends else 'test-id'
        mock_opportunity.suggested_angle = 'Test Opportunity'
        mock_opportunity.estimated_views = 50000
        mock_generate.return_value = [mock_opportunity]
        
        response = client.post('/api/analyze-opportunities')
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['success'] == True
        assert 'count' in result
        assert 'message' in result
    
    @patch('content_engine.services.ai_director.AIDirector.create_content_plan')
    @patch('content_engine.services.content_generator.ContentGenerator.generate_content')
    def test_generate_content_endpoint(self, mock_generate, mock_plan, client, sample_opportunities):
        """Test /api/generate-content endpoint"""
        
        if not sample_opportunities:
            pytest.skip("No sample opportunities available")
        
        # Mock content plan generation
        mock_plan.return_value = {
            'content_type': 'educational',
            'title': 'Test Generated Content',
            'script': {
                'hook': 'Test hook',
                'main_content': 'Test content',
                'cta': 'Test CTA'
            }
        }
        
        # Mock content generation
        mock_generate.return_value = {
            'assets': {
                'scripts': ['script.txt'],
                'images': ['image1.jpg'],
                'audio': ['audio.mp3']
            }
        }
        
        opportunity_ids = [str(sample_opportunities[0].id)]
        
        response = client.post('/api/generate-content', 
                              json={'opportunity_ids': opportunity_ids})
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['success'] == True
        assert 'count' in result
    
    def test_generate_content_endpoint_no_opportunities(self, client):
        """Test generate content endpoint with no opportunities selected"""
        
        response = client.post('/api/generate-content', json={})
        assert response.status_code == 400
        
        result = response.get_json()
        assert result['success'] == False
        assert 'error' in result
    
    @patch('platform_manager.services.platform_manager.PlatformManager.upload_content')
    def test_upload_content_endpoint(self, mock_upload, client, sample_content):
        """Test /api/upload-content endpoint"""
        
        if not sample_content:
            pytest.skip("No sample content available")
        
        # Mock successful upload
        mock_upload.return_value = {
            'success': True,
            'platform_id': 'test123',
            'url': 'https://platform.com/test123'
        }
        
        content_ids = [str(sample_content[0].id)]
        
        response = client.post('/api/upload-content',
                              json={'content_ids': content_ids})
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['success'] == True
        assert 'count' in result

class TestAnalyticsAPIEndpoints:
    """Test analytics API endpoints"""
    
    def test_analytics_kpis_endpoint(self, client, sample_performance):
        """Test /api/analytics/kpis endpoint"""
        
        response = client.get('/api/analytics/kpis?timeRange=7d')
        assert response.status_code == 200
        
        kpis = response.get_json()
        required_fields = ['total_views', 'total_engagement', 'average_roi', 
                          'total_spent', 'views_growth', 'engagement_growth']
        
        for field in required_fields:
            assert field in kpis
            assert isinstance(kpis[field], (int, float))
    
    def test_analytics_performance_endpoint(self, client, sample_performance):
        """Test /api/analytics/performance endpoint"""
        
        response = client.get('/api/analytics/performance?timeRange=30d')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'timeline' in data
        assert isinstance(data['timeline'], list)
        
        if data['timeline']:
            day_data = data['timeline'][0]
            assert 'date' in day_data
            assert 'views' in day_data
            assert 'engagement' in day_data
    
    def test_analytics_platforms_endpoint(self, client, sample_performance):
        """Test /api/analytics/platforms endpoint"""
        
        response = client.get('/api/analytics/platforms?timeRange=7d')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'platforms' in data
        assert isinstance(data['platforms'], list)
        
        if data['platforms']:
            platform = data['platforms'][0]
            assert 'name' in platform
            assert 'views' in platform
            assert 'engagement' in platform
    
    def test_analytics_content_performance_endpoint(self, client, sample_performance):
        """Test /api/analytics/content-performance endpoint"""
        
        response = client.get('/api/analytics/content-performance?limit=10&sort=views')
        assert response.status_code == 200
        
        content_data = response.get_json()
        assert isinstance(content_data, list)
        
        if content_data:
            item = content_data[0]
            required_fields = ['title', 'platform', 'views', 'engagement', 'roi']
            for field in required_fields:
                assert field in item
    
    def test_analytics_categories_endpoint(self, client, sample_performance):
        """Test /api/analytics/categories endpoint"""
        
        response = client.get('/api/analytics/categories?timeRange=30d')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'categories' in data
        assert isinstance(data['categories'], list)
    
    def test_analytics_hourly_endpoint(self, client, sample_performance):
        """Test /api/analytics/hourly endpoint"""
        
        response = client.get('/api/analytics/hourly?timeRange=7d')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'hourly_success' in data
        assert isinstance(data['hourly_success'], list)
        assert len(data['hourly_success']) == 24  # 24 hours
    
    def test_analytics_ai_metrics_endpoint(self, client):
        """Test /api/analytics/ai-metrics endpoint"""
        
        response = client.get('/api/analytics/ai-metrics?timeRange=7d')
        assert response.status_code == 200
        
        metrics = response.get_json()
        required_fields = ['prediction_accuracy', 'trend_success_rate', 
                          'content_quality_score', 'automation_efficiency']
        
        for field in required_fields:
            assert field in metrics
            assert 0 <= metrics[field] <= 100  # Percentage values
    
    def test_analytics_recommendations_endpoint(self, client, sample_performance):
        """Test /api/analytics/recommendations endpoint"""
        
        response = client.get('/api/analytics/recommendations?timeRange=7d')
        assert response.status_code == 200
        
        recommendations = response.get_json()
        assert isinstance(recommendations, list)
        
        if recommendations:
            rec = recommendations[0]
            required_fields = ['type', 'priority', 'title', 'description', 'expected_impact']
            for field in required_fields:
                assert field in rec

class TestAPIErrorHandling:
    """Test API error handling and edge cases"""
    
    def test_invalid_endpoints(self, client):
        """Test invalid endpoint requests"""
        
        # Test non-existent endpoint
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        # Test invalid method
        response = client.delete('/api/stats')
        assert response.status_code == 405  # Method not allowed
    
    def test_invalid_parameters(self, client):
        """Test invalid parameter handling"""
        
        # Test invalid limit parameter
        response = client.get('/api/trends?limit=invalid')
        assert response.status_code in [200, 400, 422]  # Should handle gracefully
        
        # Test negative limit
        response = client.get('/api/trends?limit=-5')
        assert response.status_code in [200, 400, 422]
        
        # Test extremely large limit
        response = client.get('/api/trends?limit=999999')
        assert response.status_code in [200, 400, 422]
    
    def test_malformed_json_requests(self, client):
        """Test malformed JSON request handling"""
        
        # Test invalid JSON
        response = client.post('/api/generate-content',
                              data='{"invalid": json}',
                              content_type='application/json')
        assert response.status_code == 400
        
        # Test missing content type
        response = client.post('/api/generate-content',
                              data='{"opportunity_ids": ["test"]}')
        assert response.status_code in [400, 415, 422]
    
    def test_large_request_handling(self, client):
        """Test handling of large requests"""
        
        # Create a large list of opportunity IDs
        large_opportunity_list = [f"opp-{i}" for i in range(1000)]
        
        response = client.post('/api/generate-content',
                              json={'opportunity_ids': large_opportunity_list})
        
        # Should either handle it or return appropriate error
        assert response.status_code in [200, 400, 413, 422, 500]
    
    @patch('database.repositories.trend_repository.TrendRepository.get_recent_trends')
    def test_database_error_handling(self, mock_get_trends, client):
        """Test database error handling"""
        
        # Mock database error
        mock_get_trends.side_effect = Exception("Database connection failed")
        
        response = client.get('/api/trends')
        assert response.status_code == 500
        
        error_data = response.get_json()
        assert 'error' in error_data

class TestAPIPerformance:
    """Test API performance and reliability"""
    
    def test_response_times(self, client):
        """Test API response times"""
        import time
        
        endpoints = [
            '/api/stats',
            '/api/trends?limit=10',
            '/api/opportunities?limit=5',
            '/api/content?limit=5'
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Each endpoint should respond within reasonable time
            assert response_time < 3.0, f"Endpoint {endpoint} took {response_time:.2f}s"
            assert response.status_code in [200, 404, 500]
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(endpoint):
            try:
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                results.append({
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                })
            except Exception as e:
                errors.append({
                    'endpoint': endpoint,
                    'error': str(e)
                })
        
        # Create multiple threads for different endpoints
        endpoints = ['/api/stats', '/api/trends', '/api/opportunities'] * 5
        threads = []
        
        for endpoint in endpoints:
            thread = threading.Thread(target=make_request, args=(endpoint,))
            threads.append(thread)
        
        # Start all threads simultaneously
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Analyze results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == len(endpoints)
        
        # Check response times
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        assert avg_response_time < 5.0, f"Average response time too high: {avg_response_time:.2f}s"
        
        # Check that most requests succeeded
        successful_requests = sum(1 for r in results if r['status_code'] == 200)
        success_rate = successful_requests / len(results)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2%}"
    
    def test_memory_usage_during_requests(self, client):
        """Test memory usage during API requests"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests to test memory usage
        for i in range(50):
            response = client.get('/api/trends?limit=20')
            assert response.status_code in [200, 404, 500]
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        # Allow up to 50MB increase for 50 requests
        assert memory_increase < 50 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f}MB"

class TestAPIDataConsistency:
    """Test API data consistency and integrity"""
    
    def test_trends_opportunities_consistency(self, client, sample_trends, sample_opportunities):
        """Test consistency between trends and opportunities APIs"""
        
        # Get trends
        trends_response = client.get('/api/trends')
        assert trends_response.status_code == 200
        trends = trends_response.get_json()
        
        # Get opportunities
        opportunities_response = client.get('/api/opportunities')
        assert opportunities_response.status_code == 200
        opportunities = opportunities_response.get_json()
        
        # Check that all opportunities reference valid trends
        trend_ids = {trend['id'] for trend in trends}
        
        for opp in opportunities:
            if 'trend_id' in opp:
                assert opp['trend_id'] in trend_ids, f"Opportunity {opp['id']} references non-existent trend {opp['trend_id']}"
    
    def test_content_uploads_consistency(self, client, sample_content, sample_uploads):
        """Test consistency between content and upload data"""
        
        # Get content items
        content_response = client.get('/api/content')
        assert content_response.status_code == 200
        content_items = content_response.get_json()
        
        # Verify data structure consistency
        for item in content_items:
            # Check required fields exist
            assert 'id' in item
            assert 'title' in item
            assert 'status' in item
            
            # Check data types
            assert isinstance(item['id'], str)
            assert isinstance(item['title'], str)
            assert item['status'] in ['pending', 'processing', 'completed', 'failed', 'uploaded']
    
    def test_analytics_data_consistency(self, client, sample_performance):
        """Test analytics data consistency across endpoints"""
        
        # Get KPIs
        kpis_response = client.get('/api/analytics/kpis?timeRange=7d')
        assert kpis_response.status_code == 200
        kpis = kpis_response.get_json()
        
        # Get detailed performance data
        performance_response = client.get('/api/analytics/performance?timeRange=7d')
        assert performance_response.status_code == 200
        performance = performance_response.get_json()
        
        # KPI totals should be consistent with detailed data
        if performance['timeline']:
            timeline_total_views = sum(day['views'] for day in performance['timeline'])
            
            # Allow for some variance due to different aggregation methods
            variance_threshold = 0.1  # 10% variance allowed
            
            if kpis['total_views'] > 0:
                variance = abs(timeline_total_views - kpis['total_views']) / kpis['total_views']
                assert variance <= variance_threshold, f"Views variance too high: {variance:.2%}"

class TestAPISecurityFeatures:
    """Test API security features"""
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention in API endpoints"""
        
        sql_injection_payloads = [
            "'; DROP TABLE trends; --",
            "' OR 1=1 --",
            "' UNION SELECT * FROM users --",
            "'; DELETE FROM content_items; --"
        ]
        
        for payload in sql_injection_payloads:
            # Test in query parameters
            response = client.get(f'/api/trends?category={payload}')
            assert response.status_code in [200, 400, 422]
            
            # Should not return database error indicating SQL injection worked
            if response.status_code == 500:
                error_data = response.get_json()
                error_message = error_data.get('error', '').lower()
                assert 'syntax error' not in error_message
                assert 'sql' not in error_message
    
    def test_xss_prevention(self, client):
        """Test XSS prevention in API responses"""
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            # Test in POST data
            response = client.post('/api/generate-content',
                                  json={'opportunity_ids': [payload]})
            
            # Response should not contain unescaped script tags
            if response.status_code == 200:
                response_text = response.get_data(as_text=True)
                assert '<script>' not in response_text
                assert 'javascript:' not in response_text
                assert 'onerror=' not in response_text
    
    def test_input_validation(self, client):
        """Test input validation and sanitization"""
        
        # Test extremely long inputs
        long_string = 'x' * 10000
        response = client.get(f'/api/trends?category={long_string}')
        assert response.status_code in [200, 400, 422]
        
        # Test special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        response = client.get(f'/api/trends?category={special_chars}')
        assert response.status_code in [200, 400, 422]
        
        # Test unicode characters
        unicode_string = "測試中文字符 🚀 🎯 ñáéíóú"
        response = client.get(f'/api/trends?source={unicode_string}')
        assert response.status_code in [200, 400, 422]
    
    def test_rate_limiting_behavior(self, client):
        """Test rate limiting behavior"""
        
        # Make rapid requests to test rate limiting
        request_count = 30
        responses = []
        
        for i in range(request_count):
            response = client.get('/api/stats')
            responses.append(response.status_code)
        
        # Analyze response patterns
        success_count = responses.count(200)
        rate_limited_count = responses.count(429)
        
        # Should either allow all requests or implement rate limiting
        assert success_count > 0, "No successful requests"
        
        if rate_limited_count > 0:
            # If rate limiting is implemented, should see 429 responses
            assert rate_limited_count < request_count, "All requests rate limited"
            assert success_count + rate_limited_count >= request_count * 0.8

class TestAPIEdgeCases:
    """Test API edge cases and boundary conditions"""
    
    def test_empty_database_handling(self, client):
        """Test API behavior with empty database"""
        
        # These endpoints should handle empty data gracefully
        endpoints = [
            '/api/trends',
            '/api/opportunities',
            '/api/content',
            '/api/stats'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            data = response.get_json()
            
            if isinstance(data, list):
                # List endpoints should return empty arrays
                assert data == []
            elif isinstance(data, dict):
                # Stats endpoints should return zero values
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        assert value >= 0
    
    def test_boundary_value_parameters(self, client):
        """Test boundary values for parameters"""
        
        # Test limit parameter boundaries
        boundary_limits = [0, 1, 100, 1000, -1]
        
        for limit in boundary_limits:
            response = client.get(f'/api/trends?limit={limit}')
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.get_json()
                if limit > 0:
                    assert len(data) <= limit
    
    def test_datetime_parameter_handling(self, client):
        """Test datetime parameter handling"""
        
        datetime_values = [
            '2024-01-01',
            '2024-13-01',  # Invalid month
            '2024-01-32',  # Invalid day
            'invalid-date',
            '2024-01-01T25:00:00',  # Invalid hour
            ''  # Empty string
        ]
        
        for date_value in datetime_values:
            response = client.get(f'/api/analytics/kpis?startDate={date_value}')
            assert response.status_code in [200, 400, 422]
    
    def test_large_response_handling(self, client, test_database):
        """Test handling of large response data"""
        
        # Create many test records to test large responses
        from tests.conftest import TestDataGenerator
        
        # Generate large dataset
        trends = TestDataGenerator.generate_trends(100)
        
        # Request large dataset
        response = client.get('/api/trends?limit=100')
        assert response.status_code == 200
        
        data = response.get_json()
        
        # Should handle large responses without timing out
        assert isinstance(data, list)
        assert len(data) <= 100

class TestAPIDocumentationCompliance:
    """Test API compliance with expected behavior"""
    
    def test_response_format_consistency(self, client):
        """Test that API responses follow consistent format"""
        
        # Test successful responses
        endpoints = [
            ('/api/stats', dict),
            ('/api/trends', list),
            ('/api/opportunities', list),
            ('/api/content', list)
        ]
        
        for endpoint, expected_type in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            data = response.get_json()
            assert isinstance(data, expected_type)
            
            # Check response headers
            assert 'Content-Type' in response.headers
            assert 'application/json' in response.headers['Content-Type']
    
    def test_error_response_format(self, client):
        """Test error response format consistency"""
        
        # Trigger various error conditions
        error_requests = [
            ('POST', '/api/generate-content', {}),  # Missing required field
            ('GET', '/api/trends?limit=invalid', None),  # Invalid parameter
            ('POST', '/api/nonexistent', {}),  # Nonexistent endpoint
        ]
        
        for method, endpoint, data in error_requests:
            if method == 'POST':
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)
            
            # Should return appropriate error status
            assert response.status_code >= 400
            
            # Error responses should be JSON
            try:
                error_data = response.get_json()
                assert error_data is not None
                
                # Should contain error information
                assert 'error' in error_data or 'message' in error_data or 'success' in error_data
            except:
                # Some errors might return plain text, which is also acceptable
                pass
    
    def test_http_methods_compliance(self, client):
        """Test HTTP methods compliance"""
        
        # Test that endpoints respond to correct HTTP methods
        method_tests = [
            ('GET', '/api/stats', True),
            ('POST', '/api/stats', False),
            ('PUT', '/api/stats', False),
            ('DELETE', '/api/stats', False),
            
            ('POST', '/api/collect-trends', True),
            ('GET', '/api/collect-trends', False),
            
            ('POST', '/api/generate-content', True),
            ('GET', '/api/generate-content', False),
        ]
        
        for method, endpoint, should_be_allowed in method_tests:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, json={})
            elif method == 'PUT':
                response = client.put(endpoint, json={})
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            if should_be_allowed:
                assert response.status_code != 405  # Method Not Allowed
            else:
                assert response.status_code == 405  # Method Not Allowed

# Utility functions for integration testing
def run_api_health_check(client):
    """Run basic health check on all API endpoints"""
    
    endpoints = [
        '/api/stats',
        '/api/trends',
        '/api/opportunities',
        '/api/content',
        '/api/analytics/kpis',
        '/api/analytics/performance',
        '/api/analytics/platforms'
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            results[endpoint] = {
                'status_code': response.status_code,
                'response_time': 'measured_in_test',
                'success': response.status_code == 200
            }
        except Exception as e:
            results[endpoint] = {
                'status_code': 500,
                'error': str(e),
                'success': False
            }
    
    return results

def run_stress_test(client, duration_seconds=30):
    """Run stress test on API endpoints"""
    
    import time
    import threading
    
    start_time = time.time()
    results = []
    errors = []
    
    def make_requests():
        endpoints = ['/api/stats', '/api/trends', '/api/opportunities']
        
        while time.time() - start_time < duration_seconds:
            for endpoint in endpoints:
                try:
                    response = client.get(endpoint)
                    results.append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'timestamp': time.time()
                    })
                except Exception as e:
                    errors.append({
                        'endpoint': endpoint,
                        'error': str(e),
                        'timestamp': time.time()
                    })
                
                time.sleep(0.1)  # Small delay between requests
    
    # Run multiple threads
    threads = []
    for i in range(3):  # 3 concurrent threads
        thread = threading.Thread(target=make_requests)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    return {
        'total_requests': len(results),
        'total_errors': len(errors),
        'success_rate': len(results) / (len(results) + len(errors)) if (len(results) + len(errors)) > 0 else 0,
        'requests_per_second': len(results) / duration_seconds,
        'errors': errors[:10]  # First 10 errors for analysis
    }

if __name__ == '__main__':
    # Run API integration tests
    pytest.main(['-v', '--tb=short', 'tests/test_api_integration.py'])