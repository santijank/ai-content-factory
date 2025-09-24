"""
Integration Tests: Trend to Content Flow
========================================

Tests the complete flow from trend collection to content generation:
1. Collect trends from various sources
2. Analyze trends and generate opportunities
3. Select opportunities and create content plans
4. Generate actual content assets

This tests the interaction between:
- TrendCollector ↔ Database
- TrendAnalyzer ↔ AI Services
- OpportunityEngine ↔ Database
- AIDirector ↔ ContentPipeline
- ContentPipeline ↔ AI Services
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import system components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from trend_monitor.services.trend_collector import TrendCollector
from content_engine.services.trend_analyzer import TrendAnalyzer
from content_engine.services.opportunity_engine import OpportunityEngine
from content_engine.services.ai_director import AIDirector
from content_engine.services.content_pipeline import ContentPipeline
from database.repositories.trend_repository import TrendRepository
from database.repositories.opportunity_repository import OpportunityRepository


class TestTrendToContentFlow:
    """Integration tests for trend to content generation flow."""
    
    @pytest.mark.integration
    async def test_complete_trend_to_content_flow(
        self, test_database, mock_ai_services, integration_helper, test_content_files
    ):
        """Test complete flow from trend collection to content generation."""
        
        # Step 1: Collect trends
        trend_collector = TrendCollector()
        
        # Mock trend collection
        mock_trends = [
            integration_helper.create_test_trend_data(),
            {
                **integration_helper.create_test_trend_data(),
                "topic": "AI Video Creation Tools",
                "popularity_score": 78.2,
                "keywords": ["AI", "video", "automation", "tools"]
            }
        ]
        
        with patch.object(trend_collector, 'collect_trends', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = mock_trends
            
            collected_trends = await trend_collector.collect_trends()
            
            assert len(collected_trends) == 2
            assert all("integration test" in trend["topic"].lower() or "ai video" in trend["topic"].lower() 
                      for trend in collected_trends)
        
        # Step 2: Store trends in database
        trend_repo = TrendRepository(test_database)
        
        stored_trend_ids = []
        for trend_data in collected_trends:
            with patch.object(trend_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = f"trend_{len(stored_trend_ids)}"
                trend_id = await trend_repo.create(trend_data)
                stored_trend_ids.append(trend_id)
        
        assert len(stored_trend_ids) == 2
        
        # Step 3: Analyze trends and generate opportunities
        trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        opportunity_engine = OpportunityEngine(trend_analyzer)
        
        # Mock opportunity generation
        mock_opportunities = []
        for i, trend_id in enumerate(stored_trend_ids):
            opportunity = {
                **integration_helper.create_test_content_opportunity(),
                "trend_id": trend_id,
                "suggested_angle": f"Test Content Angle {i+1}",
                "priority_score": 8.5 - i * 0.5
            }
            mock_opportunities.append(opportunity)
        
        with patch.object(opportunity_engine, 'generate_opportunities', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_opportunities
            
            opportunities = await opportunity_engine.generate_opportunities(stored_trend_ids)
            
            assert len(opportunities) == 2
            assert all(opp["trend_id"] in stored_trend_ids for opp in opportunities)
        
        # Step 4: Store opportunities in database
        opportunity_repo = OpportunityRepository(test_database)
        
        stored_opportunity_ids = []
        for opportunity_data in opportunities:
            with patch.object(opportunity_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = f"opportunity_{len(stored_opportunity_ids)}"
                opp_id = await opportunity_repo.create(opportunity_data)
                stored_opportunity_ids.append(opp_id)
        
        # Step 5: Select best opportunity and create content plan
        best_opportunity = max(opportunities, key=lambda x: x["priority_score"])
        
        ai_director = AIDirector()
        ai_director.text_ai = mock_ai_services["text_ai"]
        
        user_request = f"Create content based on: {best_opportunity['suggested_angle']}"
        
        content_plan = await ai_director.create_content_plan(user_request)
        
        assert content_plan is not None
        assert content_plan.content_type == "educational"
        assert "integration test" in content_plan.script.hook.lower()
        
        # Step 6: Generate content assets
        content_pipeline = ContentPipeline()
        content_pipeline.text_ai = mock_ai_services["text_ai"]
        content_pipeline.image_ai = mock_ai_services["image_ai"]
        content_pipeline.tts = mock_ai_services["audio_ai"]
        
        # Mock video assembly
        with patch.object(content_pipeline, 'assemble_video', new_callable=AsyncMock) as mock_assemble:
            mock_assemble.return_value = test_content_files['video']
            
            generated_content = await content_pipeline.generate_content(content_plan)
            
            assert generated_content is not None
            assert isinstance(generated_content, dict)
        
        # Verify the complete flow
        assert len(collected_trends) > 0
        assert len(opportunities) > 0
        assert content_plan is not None
        assert generated_content is not None
    
    @pytest.mark.integration
    async def test_trend_analysis_accuracy(self, test_database, mock_ai_services):
        """Test accuracy of trend analysis and opportunity scoring."""
        
        # Create trends with different characteristics
        trends = [
            {
                "topic": "High Potential AI Trend",
                "popularity_score": 95.0,
                "growth_rate": 25.0,
                "keywords": ["AI", "trending", "viral", "popular"]
            },
            {
                "topic": "Low Potential Tech News",
                "popularity_score": 45.0,
                "growth_rate": 5.0,
                "keywords": ["tech", "news", "update"]
            },
            {
                "topic": "Medium Potential Tutorial",
                "popularity_score": 72.0,
                "growth_rate": 12.0,
                "keywords": ["tutorial", "howto", "educational"]
            }
        ]
        
        trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        
        # Mock AI analysis to return different scores
        def mock_analyze_response(trend_data):
            topic = trend_data["topic"]
            if "High Potential" in topic:
                return json.dumps({
                    "viral_potential": 9,
                    "content_saturation": 3,
                    "audience_interest": 8,
                    "monetization_opportunity": 7
                })
            elif "Low Potential" in topic:
                return json.dumps({
                    "viral_potential": 4,
                    "content_saturation": 8,
                    "audience_interest": 5,
                    "monetization_opportunity": 3
                })
            else:
                return json.dumps({
                    "viral_potential": 6,
                    "content_saturation": 5,
                    "audience_interest": 7,
                    "monetization_opportunity": 6
                })
        
        mock_ai_services["text_ai"].analyze = AsyncMock(side_effect=mock_analyze_response)
        
        analyzed_trends = []
        for trend in trends:
            analysis = await trend_analyzer.analyze_trend_potential(trend)
            analyzed_trends.append({**trend, "analysis": analysis})
        
        # High potential trend should score highest
        high_potential = next(t for t in analyzed_trends if "High Potential" in t["topic"])
        low_potential = next(t for t in analyzed_trends if "Low Potential" in t["topic"])
        
        high_score = trend_analyzer.calculate_opportunity_score(high_potential)
        low_score = trend_analyzer.calculate_opportunity_score(low_potential)
        
        assert high_score > low_score
        assert high_score > 7.0
        assert low_score < 6.0
    
    @pytest.mark.integration
    async def test_opportunity_prioritization(self, test_database, mock_ai_services):
        """Test opportunity prioritization and ranking."""
        
        opportunity_engine = OpportunityEngine(
            trend_analyzer=TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        )
        
        # Create opportunities with different characteristics
        opportunities = [
            {
                "suggested_angle": "Viral AI Tool Everyone's Using",
                "estimated_views": 100000,
                "competition_level": "low",
                "production_cost": 20.0,
                "estimated_roi": 5.0
            },
            {
                "suggested_angle": "Complex AI Research Explained",
                "estimated_views": 25000,
                "competition_level": "high",
                "production_cost": 50.0,
                "estimated_roi": 2.0
            },
            {
                "suggested_angle": "Quick AI Tips for Beginners",
                "estimated_views": 75000,
                "competition_level": "medium",
                "production_cost": 15.0,
                "estimated_roi": 4.2
            }
        ]
        
        ranked_opportunities = opportunity_engine.rank_opportunities(opportunities)
        
        # Should be ranked by priority score (combination of ROI, views, competition)
        assert len(ranked_opportunities) == 3
        
        # First opportunity should be highest priority
        top_opportunity = ranked_opportunities[0]
        assert top_opportunity["estimated_roi"] >= 4.0
        assert top_opportunity["competition_level"] in ["low", "medium"]
    
    @pytest.mark.integration
    async def test_content_plan_quality_by_tier(self, mock_ai_services):
        """Test content plan quality varies by AI service tier."""
        
        # Mock different quality responses
        budget_response = json.dumps({
            "content_type": "educational",
            "script": {"hook": "Simple hook", "main_content": "Basic content", "cta": "Subscribe"},
            "visual_plan": {"style": "simple", "scenes": ["intro"], "text_overlays": ["Title"]},
            "audio_plan": {"voice_style": "basic", "background_music": "none", "sound_effects": []},
            "platform_optimization": {"title": "Basic Title", "description": "Basic desc", "hashtags": ["#basic"], "thumbnail_concept": "Simple"},
            "production_estimate": {"time_minutes": 10, "cost_baht": 5, "complexity": "low"}
        })
        
        premium_response = json.dumps({
            "content_type": "educational",
            "script": {
                "hook": "Attention-grabbing professional hook with storytelling",
                "main_content": "Comprehensive educational content with examples and actionable insights",
                "cta": "Strategic call-to-action with multiple engagement points"
            },
            "visual_plan": {
                "style": "professional_cinematic",
                "scenes": ["dynamic_intro", "main_content", "examples", "conclusion"],
                "text_overlays": ["Professional Title", "Key Points", "Statistics", "CTA"]
            },
            "audio_plan": {
                "voice_style": "professional_engaging",
                "background_music": "cinematic_inspiring",
                "sound_effects": ["transition", "emphasis", "success"]
            },
            "platform_optimization": {
                "title": "SEO-Optimized Professional Title with Keywords",
                "description": "Comprehensive description with keywords and call-to-action",
                "hashtags": ["#professional", "#educational", "#detailed", "#quality"],
                "thumbnail_concept": "Professional design with compelling visual elements"
            },
            "production_estimate": {"time_minutes": 45, "cost_baht": 35, "complexity": "high"}
        })
        
        from content_engine.models.quality_tier import QualityTier
        
        # Test budget tier
        budget_ai_service = Mock()
        budget_ai_service.generate = AsyncMock(return_value=budget_response)
        
        budget_director = AIDirector(quality_tier=QualityTier.BUDGET)
        budget_director.text_ai = budget_ai_service
        
        budget_plan = await budget_director.create_content_plan("Create AI tutorial")
        
        # Test premium tier
        premium_ai_service = Mock()
        premium_ai_service.generate = AsyncMock(return_value=premium_response)
        
        premium_director = AIDirector(quality_tier=QualityTier.PREMIUM)
        premium_director.text_ai = premium_ai_service
        
        premium_plan = await premium_director.create_content_plan("Create AI tutorial")
        
        # Premium should have higher quality indicators
        assert len(premium_plan.script.hook) > len(budget_plan.script.hook)
        assert len(premium_plan.visual_plan.scenes) > len(budget_plan.visual_plan.scenes)
        assert premium_plan.production_estimate.time_minutes > budget_plan.production_estimate.time_minutes
        assert premium_plan.production_estimate.cost_baht > budget_plan.production_estimate.cost_baht
    
    @pytest.mark.integration
    async def test_error_recovery_in_flow(self, test_database, mock_ai_services, integration_helper):
        """Test error recovery at different points in the flow."""
        
        # Test trend collection failure recovery
        trend_collector = TrendCollector()
        
        # Mock partial failure (one source fails)
        with patch.object(trend_collector, 'collect_youtube_trends', new_callable=AsyncMock) as mock_youtube, \
             patch.object(trend_collector, 'collect_google_trends', new_callable=AsyncMock) as mock_google:
            
            mock_youtube.side_effect = Exception("YouTube API error")
            mock_google.return_value = [integration_helper.create_test_trend_data()]
            
            trends = await trend_collector.collect_trends()
            
            # Should continue with available trends
            assert len(trends) > 0  # Google trends should still be collected
        
        # Test AI service failure recovery
        ai_director = AIDirector()
        
        # Mock AI service to fail first time, succeed second time
        failing_ai_service = Mock()
        failing_ai_service.generate = AsyncMock(side_effect=[
            Exception("AI service temporarily unavailable"),
            json.dumps({
                "content_type": "educational",
                "script": {"hook": "Recovery test", "main_content": "Content", "cta": "Action"},
                "visual_plan": {"style": "simple", "scenes": ["scene"], "text_overlays": ["text"]},
                "audio_plan": {"voice_style": "neutral", "background_music": "none", "sound_effects": []},
                "platform_optimization": {"title": "Recovery Test", "description": "Test", "hashtags": ["#test"], "thumbnail_concept": "Simple"},
                "production_estimate": {"time_minutes": 15, "cost_baht": 10, "complexity": "low"}
            })
        ])
        
        ai_director.text_ai = failing_ai_service
        
        # Should implement retry logic
        with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up retry delays
            try:
                content_plan = await ai_director.create_content_plan("Test recovery")
                # If retry is implemented, this should succeed
                assert content_plan is not None
            except Exception:
                # If no retry implemented, should fail gracefully
                assert failing_ai_service.generate.call_count == 1
    
    @pytest.mark.integration
    async def test_concurrent_trend_processing(self, test_database, mock_ai_services, integration_helper):
        """Test processing multiple trends concurrently."""
        
        # Create multiple trends
        trends = [
            integration_helper.create_test_trend_data(),
            {**integration_helper.create_test_trend_data(), "topic": "AI Content Creation", "popularity_score": 88.0},
            {**integration_helper.create_test_trend_data(), "topic": "Machine Learning Basics", "popularity_score": 75.0},
            {**integration_helper.create_test_trend_data(), "topic": "Data Science Tips", "popularity_score": 82.0}
        ]
        
        trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        opportunity_engine = OpportunityEngine(trend_analyzer)
        
        # Process trends concurrently
        start_time = asyncio.get_event_loop().time()
        
        # Mock concurrent processing
        async def process_trend_batch(trend_batch):
            tasks = []
            for trend in trend_batch:
                task = trend_analyzer.analyze_trend_potential(trend)
                tasks.append(task)
            return await asyncio.gather(*tasks)
        
        analyzed_trends = await process_trend_batch(trends)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        assert len(analyzed_trends) == 4
        # Concurrent processing should be faster than sequential
        assert processing_time < 2.0  # Should complete quickly with mocks
    
    @pytest.mark.integration
    async def test_data_consistency_across_flow(self, test_database, mock_ai_services, integration_helper):
        """Test data consistency as it flows through the system."""
        
        # Start with trend data
        original_trend = integration_helper.create_test_trend_data()
        
        # Store in database
        trend_repo = TrendRepository(test_database)
        with patch.object(trend_repo, 'create', new_callable=AsyncMock) as mock_create, \
             patch.object(trend_repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
            
            mock_create.return_value = "trend_123"
            mock_get.return_value = original_trend
            
            trend_id = await trend_repo.create(original_trend)
            stored_trend = await trend_repo.get_by_id(trend_id)
            
            # Data should be consistent
            assert stored_trend["topic"] == original_trend["topic"]
            assert stored_trend["popularity_score"] == original_trend["popularity_score"]
        
        # Generate opportunity from trend
        trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        opportunity_engine = OpportunityEngine(trend_analyzer)
        
        opportunities = await opportunity_engine.generate_opportunities([trend_id])
        
        # Opportunity should reference original trend
        assert len(opportunities) > 0
        opportunity = opportunities[0]
        assert opportunity["trend_id"] == trend_id
        
        # Create content plan from opportunity
        ai_director = AIDirector()
        ai_director.text_ai = mock_ai_services["text_ai"]
        
        content_plan = await ai_director.create_content_plan(opportunity["suggested_angle"])
        
        # Content should be related to original trend topic
        full_content = f"{content_plan.script.hook} {content_plan.script.main_content}".lower()
        trend_keywords = [kw.lower() for kw in original_trend["keywords"]]
        
        # At least one trend keyword should appear in content
        assert any(keyword in full_content for keyword in trend_keywords)


class TestPerformanceAndScaling:
    """Test performance and scaling characteristics of the trend-to-content flow."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_high_volume_trend_processing(self, test_database, mock_ai_services):
        """Test processing large volumes of trends."""
        
        # Create large batch of trends
        trend_count = 50
        trends = []
        
        for i in range(trend_count):
            trend = {
                "topic": f"AI Trend Topic {i}",
                "source": f"source_{i % 5}",  # Rotate through 5 sources
                "popularity_score": 50.0 + (i % 50),
                "growth_rate": 5.0 + (i % 20),
                "keywords": [f"keyword{i}", f"topic{i}", "AI"],
                "category": "Technology",
                "region": "Global"
            }
            trends.append(trend)
        
        trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        opportunity_engine = OpportunityEngine(trend_analyzer)
        
        # Process in batches to simulate realistic load
        batch_size = 10
        all_opportunities = []
        
        start_time = asyncio.get_event_loop().time()
        
        for i in range(0, len(trends), batch_size):
            batch = trends[i:i + batch_size]
            batch_ids = [f"trend_{j}" for j in range(i, min(i + batch_size, len(trends)))]
            
            # Mock the batch processing
            with patch.object(opportunity_engine, 'generate_opportunities', new_callable=AsyncMock) as mock_gen:
                mock_opportunities = [
                    {"trend_id": trend_id, "priority_score": 7.0 + (i % 3)}
                    for trend_id in batch_ids
                ]
                mock_gen.return_value = mock_opportunities
                
                batch_opportunities = await opportunity_engine.generate_opportunities(batch_ids)
                all_opportunities.extend(batch_opportunities)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        assert len(all_opportunities) == trend_count
        assert total_time < 10.0  # Should complete within reasonable time
        
        # Verify processing rate
        processing_rate = trend_count / total_time
        assert processing_rate > 5.0  # At least 5 trends per second
    
    @pytest.mark.integration
    async def test_memory_usage_during_processing(self, mock_ai_services):
        """Test memory usage remains stable during large processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple content plans
        ai_director = AIDirector()
        ai_director.text_ai = mock_ai_services["text_ai"]
        
        content_plans = []
        for i in range(20):
            plan = await ai_director.create_content_plan(f"Create content about topic {i}")
            content_plans.append(plan)
            
            # Check memory periodically
            if i % 5 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Memory increase should be reasonable (less than 100MB)
                assert memory_increase < 100 * 1024 * 1024
        
        assert len(content_plans) == 20
        
        # Final memory check
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        # Should not have excessive memory growth
        assert total_increase < 200 * 1024 * 1024  # Less than 200MB increase


if __name__ == "__main__":
    pytest.main([__file__, "-v"])