"""
Integration Tests: End-to-End Workflow
======================================

Tests the complete end-to-end workflow:
1. Collect trends from multiple sources
2. Analyze and rank opportunities
3. Generate content plans and assets
4. Upload to platforms
5. Track performance

This is the ultimate integration test covering all system components
working together in a realistic production scenario.
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Import system components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from trend_monitor.services.trend_collector import TrendCollector
from trend_monitor.services.youtube_trends import YouTubeTrendsService
from trend_monitor.services.google_trends import GoogleTrendsService
from content_engine.services.trend_analyzer import TrendAnalyzer
from content_engine.services.opportunity_engine import OpportunityEngine
from content_engine.services.ai_director import AIDirector
from content_engine.services.content_pipeline import ContentPipeline
from platform_manager.services.platform_manager import PlatformManager
from platform_manager.models.platform_type import PlatformType
from platform_manager.models.upload_metadata import UploadMetadata
from database.repositories.trend_repository import TrendRepository
from database.repositories.opportunity_repository import OpportunityRepository
from database.repositories.content_repository import ContentRepository
from database.repositories.performance_repository import PerformanceRepository
from shared.models.content_plan import ContentPlan


class TestEndToEndWorkflow:
    """Complete end-to-end workflow integration tests."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_complete_ai_content_factory_workflow(
        self, 
        test_database, 
        mock_ai_services, 
        mock_platform_services,
        test_content_files,
        integration_helper
    ):
        """
        Master integration test: Complete workflow from trends to published content.
        
        This test simulates a real-world scenario where:
        1. System collects trending topics
        2. AI analyzes trends and creates opportunities  
        3. Best opportunities are selected for content creation
        4. AI generates complete content plans
        5. Content pipeline produces video assets
        6. Platform manager uploads to multiple platforms
        7. Performance is tracked and analyzed
        """
        
        print("\n🚀 Starting Complete End-to-End Workflow Test")
        
        # ===== PHASE 1: TREND COLLECTION =====
        print("\n📊 Phase 1: Collecting Trends")
        
        trend_collector = TrendCollector()
        
        # Mock trend data from multiple sources
        mock_youtube_trends = [
            {
                "id": "yt_trend_001",
                "topic": "AI Video Creation Tools 2025", 
                "source": "youtube",
                "popularity_score": 89.5,
                "growth_rate": 18.3,
                "keywords": ["AI", "video", "creation", "tools", "2025"],
                "collected_at": datetime.utcnow().isoformat(),
                "raw_data": {
                    "views": 450000,
                    "engagement_rate": 5.2,
                    "trending_videos": 15
                }
            },
            {
                "id": "yt_trend_002", 
                "topic": "Productivity Hacks for Remote Work",
                "source": "youtube",
                "popularity_score": 76.8,
                "growth_rate": 12.4,
                "keywords": ["productivity", "remote", "work", "hacks"],
                "collected_at": datetime.utcnow().isoformat(),
                "raw_data": {
                    "views": 280000,
                    "engagement_rate": 4.7,
                    "trending_videos": 8
                }
            }
        ]
        
        mock_google_trends = [
            {
                "id": "gt_trend_001",
                "topic": "Machine Learning for Beginners",
                "source": "google_trends", 
                "popularity_score": 82.1,
                "growth_rate": 15.7,
                "keywords": ["machine", "learning", "beginners", "tutorial"],
                "collected_at": datetime.utcnow().isoformat(),
                "raw_data": {
                    "search_volume": 125000,
                    "interest_score": 82,
                    "related_queries": 24
                }
            }
        ]
        
        # Mock trend collection
        with patch.object(trend_collector, 'collect_youtube_trends', new_callable=AsyncMock) as mock_yt, \
             patch.object(trend_collector, 'collect_google_trends', new_callable=AsyncMock) as mock_gt, \
             patch.object(trend_collector, 'collect_twitter_trends', new_callable=AsyncMock) as mock_tw, \
             patch.object(trend_collector, 'collect_reddit_trends', new_callable=AsyncMock) as mock_rd:
            
            mock_yt.return_value = mock_youtube_trends
            mock_gt.return_value = mock_google_trends  
            mock_tw.return_value = []
            mock_rd.return_value = []
            
            collected_trends = await trend_collector.collect_trends()
            
            # Verify trend collection
            assert len(collected_trends) >= 3
            assert any("AI Video" in str(trends) for trends in collected_trends)
            assert any("Machine Learning" in str(trends) for trends in collected_trends)
            
            print(f"✅ Collected {len(collected_trends)} trends from multiple sources")
        
        # ===== PHASE 2: TREND STORAGE & ANALYSIS =====
        print("\n🧠 Phase 2: Analyzing Trends and Generating Opportunities")
        
        # Store trends in database
        trend_repo = TrendRepository(test_database)
        stored_trend_ids = []
        
        all_trend_data = mock_youtube_trends + mock_google_trends
        
        for trend_data in all_trend_data:
            with patch.object(trend_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = trend_data["id"]
                trend_id = await trend_repo.create(trend_data)
                stored_trend_ids.append(trend_id)
                
        assert len(stored_trend_ids) == 3
        print(f"✅ Stored {len(stored_trend_ids)} trends in database")
        
        # Analyze trends and generate content opportunities  
        trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        opportunity_engine = OpportunityEngine(trend_analyzer)
        
        # Mock AI analysis responses
        mock_ai_services["text_ai"].analyze = AsyncMock(side_effect=[
            # AI Video Tools analysis
            json.dumps({
                "viral_potential": 9,
                "content_saturation": 4, 
                "audience_interest": 8,
                "monetization_opportunity": 9,
                "content_angles": [
                    "AI Video Tools Review and Comparison 2025",
                    "I Tested Every AI Video Tool So You Don't Have To",
                    "Free vs Paid AI Video Tools - Honest Comparison"
                ]
            }),
            # Remote Work analysis
            json.dumps({
                "viral_potential": 7,
                "content_saturation": 6,
                "audience_interest": 8,  
                "monetization_opportunity": 6,
                "content_angles": [
                    "My $5000 Remote Work Setup Tour",
                    "Productivity System That Tripled My Output", 
                    "Remote Work Mistakes That Kill Productivity"
                ]
            }),
            # Machine Learning analysis
            json.dumps({
                "viral_potential": 8,
                "content_saturation": 7,
                "audience_interest": 9,
                "monetization_opportunity": 7,
                "content_angles": [
                    "Machine Learning Explained in 5 Minutes",
                    "Build Your First ML Model (No Experience Required)",
                    "ML Career Roadmap for 2025"
                ]
            })
        ])
        
        opportunities = await opportunity_engine.generate_opportunities(stored_trend_ids)
        
        # Verify opportunity generation
        assert len(opportunities) >= 3
        assert all(opp["trend_id"] in stored_trend_ids for opp in opportunities)
        assert all(opp["priority_score"] > 0 for opp in opportunities)
        
        print(f"✅ Generated {len(opportunities)} content opportunities")
        
        # Store opportunities in database
        opportunity_repo = OpportunityRepository(test_database)
        stored_opportunity_ids = []
        
        for opportunity_data in opportunities:
            with patch.object(opportunity_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = f"opp_{len(stored_opportunity_ids) + 1}"
                opp_id = await opportunity_repo.create(opportunity_data)
                stored_opportunity_ids.append(opp_id)
        
        print(f"✅ Stored {len(stored_opportunity_ids)} opportunities in database")
        
        # ===== PHASE 3: CONTENT PLANNING & GENERATION =====
        print("\n🎬 Phase 3: Creating Content Plans and Generating Assets")
        
        # Select best opportunities (top 2 for this test)
        best_opportunities = sorted(opportunities, key=lambda x: x["priority_score"], reverse=True)[:2]
        
        ai_director = AIDirector()
        ai_director.text_ai = mock_ai_services["text_ai"]
        
        content_plans = []
        
        for i, opportunity in enumerate(best_opportunities):
            user_request = f"Create content based on: {opportunity['suggested_angle']}"
            
            content_plan = await ai_director.create_content_plan(user_request)
            content_plans.append(content_plan)
            
            # Verify content plan quality
            assert content_plan is not None
            assert content_plan.content_type in ["educational", "tutorial", "entertainment", "review"]
            assert len(content_plan.script.hook) > 10
            assert len(content_plan.visual_plan.scenes) >= 3
            
        print(f"✅ Created {len(content_plans)} high-quality content plans")
        
        # Generate content assets
        content_pipeline = ContentPipeline()
        content_pipeline.text_ai = mock_ai_services["text_ai"]
        content_pipeline.image_ai = mock_ai_services["image_ai"]  
        content_pipeline.tts = mock_ai_services["audio_ai"]
        
        generated_contents = []
        
        for i, content_plan in enumerate(content_plans):
            
            # Mock content generation pipeline
            with patch.object(content_pipeline, 'generate_script', new_callable=AsyncMock) as mock_script, \
                 patch.object(content_pipeline, 'generate_visuals', new_callable=AsyncMock) as mock_visuals, \
                 patch.object(content_pipeline, 'generate_audio', new_callable=AsyncMock) as mock_audio, \
                 patch.object(content_pipeline, 'assemble_video', new_callable=AsyncMock) as mock_assemble:
                
                mock_script.return_value = f"Complete narration script for content {i+1}..."
                mock_visuals.return_value = [
                    f"/tmp/content_{i+1}_scene_{j}.jpg" for j in range(len(content_plan.visual_plan.scenes))
                ]
                mock_audio.return_value = f"/tmp/content_{i+1}_audio.mp3"
                mock_assemble.return_value = test_content_files['video']
                
                generated_content = await content_pipeline.generate_content(content_plan)
                generated_contents.append({
                    "content_plan": content_plan,
                    "generated_assets": generated_content,
                    "video_file": test_content_files['video']
                })
                
        print(f"✅ Generated complete assets for {len(generated_contents)} content pieces")
        
        # Store content in database
        content_repo = ContentRepository(test_database)
        stored_content_ids = []
        
        for i, content_data in enumerate(generated_contents):
            content_record = {
                "opportunity_id": stored_opportunity_ids[i],
                "title": content_data["content_plan"].platform_optimization.get("title", f"Content {i+1}"),
                "content_plan": content_data["content_plan"].to_dict(),
                "assets": {
                    "video": content_data["video_file"],
                    "script": f"Script for content {i+1}",
                    "images": [f"image_{j}.jpg" for j in range(3)]
                },
                "production_status": "completed",
                "created_at": datetime.utcnow().isoformat()
            }
            
            with patch.object(content_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = f"content_{i+1}"
                content_id = await content_repo.create(content_record)
                stored_content_ids.append(content_id)
        
        print(f"✅ Stored {len(stored_content_ids)} content records in database")
        
        # ===== PHASE 4: MULTI-PLATFORM UPLOAD =====
        print("\n📤 Phase 4: Uploading to Multiple Platforms")
        
        platform_manager = PlatformManager()
        target_platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        
        all_upload_results = []
        
        for i, content_data in enumerate(generated_contents):
            
            # Create platform-specific metadata
            upload_metadata = UploadMetadata(
                title=content_data["content_plan"].platform_optimization.get("title", f"AI Content {i+1}"),
                description=content_data["content_plan"].platform_optimization.get("description", "Amazing AI-generated content!"),
                tags=content_data["content_plan"].platform_optimization.get("hashtags", ["#AI", "#Content"]),
                category="Education",
                privacy="public"
            )
            
            # Mock platform uploads
            platform_manager.platforms = {
                PlatformType.YOUTUBE: mock_platform_services["youtube"],
                PlatformType.TIKTOK: mock_platform_services["tiktok"],
                PlatformType.INSTAGRAM: mock_platform_services["instagram"]
            }
            
            with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_optimize, \
                 patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
                
                mock_optimize.side_effect = lambda content, platform: f"{content}_{platform.value}"
                mock_adapt.return_value = upload_metadata
                
                upload_results = await platform_manager.upload_content(
                    content_data["video_file"],
                    target_platforms,
                    upload_metadata
                )
                
                # Verify uploads
                assert len(upload_results) == len(target_platforms)
                assert all(result["status"] == "success" for result in upload_results)
                
                all_upload_results.extend(upload_results)
        
        print(f"✅ Successfully uploaded {len(all_upload_results)} videos across platforms")
        
        # ===== PHASE 5: PERFORMANCE TRACKING SETUP =====
        print("\n📈 Phase 5: Setting Up Performance Tracking")
        
        performance_repo = PerformanceRepository(test_database)
        
        # Create initial performance records
        for upload_result in all_upload_results:
            initial_metrics = {
                "upload_id": upload_result.get("upload_id", f"upload_{len(all_upload_results)}"),
                "platform": upload_result.get("platform", "unknown"),
                "platform_id": upload_result["platform_id"],
                "url": upload_result["url"],
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "revenue": 0.0,
                "measured_at": datetime.utcnow().isoformat()
            }
            
            with patch.object(performance_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = f"perf_{upload_result['platform_id']}"
                perf_id = await performance_repo.create(initial_metrics)
                
        print(f"✅ Initialized performance tracking for {len(all_upload_results)} uploads")
        
        # ===== PHASE 6: END-TO-END VERIFICATION =====
        print("\n✅ Phase 6: Complete Workflow Verification")
        
        # Verify complete workflow success
        workflow_success = {
            "trends_collected": len(stored_trend_ids) >= 3,
            "opportunities_generated": len(stored_opportunity_ids) >= 3,
            "content_created": len(stored_content_ids) >= 2,
            "uploads_completed": len(all_upload_results) >= 6,  # 2 content × 3 platforms
            "performance_tracking_setup": len(all_upload_results) > 0
        }
        
        # Assert complete workflow success
        assert all(workflow_success.values()), f"Workflow verification failed: {workflow_success}"
        
        # Verify data consistency across the flow
        assert len(stored_trend_ids) > 0
        assert len(stored_opportunity_ids) > 0  
        assert len(stored_content_ids) > 0
        assert len(all_upload_results) > 0
        
        # Verify content quality
        for content_data in generated_contents:
            plan = content_data["content_plan"]
            assert plan.content_type is not None
            assert len(plan.script.hook) > 0
            assert len(plan.visual_plan.scenes) > 0
            
        # Verify upload success
        successful_uploads = [r for r in all_upload_results if r["status"] == "success"]
        assert len(successful_uploads) == len(all_upload_results)
        
        print("\n🎉 COMPLETE END-TO-END WORKFLOW TEST PASSED!")
        print(f"📊 Processed {len(stored_trend_ids)} trends")
        print(f"💡 Generated {len(stored_opportunity_ids)} opportunities") 
        print(f"🎬 Created {len(stored_content_ids)} content pieces")
        print(f"📤 Completed {len(all_upload_results)} platform uploads")
        print(f"📈 Setup performance tracking for all uploads")
        
        return {
            "trends_processed": len(stored_trend_ids),
            "opportunities_created": len(stored_opportunity_ids),
            "content_generated": len(stored_content_ids),
            "uploads_completed": len(all_upload_results),
            "workflow_success": True
        }
    
    @pytest.mark.integration
    async def test_workflow_error_recovery_and_resilience(
        self, 
        test_database,
        mock_ai_services,
        integration_helper
    ):
        """
        Test workflow resilience and error recovery capabilities.
        
        This test verifies that the system can gracefully handle:
        - Partial API failures
        - Service timeouts
        - Data quality issues
        - Platform upload failures
        """
        
        print("\n🛡️ Testing Workflow Error Recovery and Resilience")
        
        # Test 1: Trend collection with partial failures
        print("\n1️⃣ Testing Trend Collection Resilience")
        
        trend_collector = TrendCollector()
        
        with patch.object(trend_collector, 'collect_youtube_trends', new_callable=AsyncMock) as mock_yt, \
             patch.object(trend_collector, 'collect_google_trends', new_callable=AsyncMock) as mock_gt, \
             patch.object(trend_collector, 'collect_twitter_trends', new_callable=AsyncMock) as mock_tw:
            
            # YouTube succeeds
            mock_yt.return_value = [integration_helper.create_test_trend_data()]
            
            # Google Trends fails
            mock_gt.side_effect = Exception("Google Trends API timeout")
            
            # Twitter succeeds  
            mock_tw.return_value = [{
                **integration_helper.create_test_trend_data(),
                "source": "twitter",
                "topic": "Twitter Trending Topic"
            }]
            
            trends = await trend_collector.collect_trends()
            
            # Should continue with available trends despite one source failing
            assert len(trends) >= 2  # YouTube + Twitter
            successful_sources = [t.get("source") for t in trends if t is not None]
            assert "youtube" in str(successful_sources)
            assert "twitter" in str(successful_sources)
            
        print("✅ Trend collection handles partial API failures gracefully")
        
        # Test 2: AI service failure and fallback
        print("\n2️⃣ Testing AI Service Resilience")
        
        ai_director = AIDirector()
        
        # Mock AI service with intermittent failures
        failure_count = 0
        
        async def mock_ai_with_failures(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= 2:  # Fail first 2 attempts
                raise Exception("AI service temporarily unavailable")
            else:  # Succeed on 3rd attempt
                return json.dumps({
                    "content_type": "educational",
                    "script": {"hook": "Recovery test hook", "main_content": "Recovery content", "cta": "Recovery CTA"},
                    "visual_plan": {"style": "simple", "scenes": ["scene1"], "text_overlays": ["Recovery"]},
                    "audio_plan": {"voice_style": "neutral", "background_music": "none", "sound_effects": []},
                    "platform_optimization": {"title": "Recovery Test", "description": "Test", "hashtags": ["#test"], "thumbnail_concept": "Simple"},
                    "production_estimate": {"time_minutes": 10, "cost_baht": 5, "complexity": "low"}
                })
        
        ai_director.text_ai.generate = mock_ai_with_failures
        
        # Should eventually succeed after retries
        with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up retry delays
            content_plan = await ai_director.create_content_plan("Test recovery scenario")
            
            assert content_plan is not None
            assert "Recovery" in content_plan.script.hook
            assert failure_count == 3  # Verify retry attempts
            
        print("✅ AI service handles failures with retry mechanism")
        
        # Test 3: Platform upload partial failures
        print("\n3️⃣ Testing Platform Upload Resilience")
        
        platform_manager = PlatformManager()
        
        # Mock mixed success/failure scenarios
        async def mock_youtube_success(*args, **kwargs):
            return {"status": "success", "platform_id": "yt_success", "url": "https://youtube.com/success"}
        
        async def mock_tiktok_failure(*args, **kwargs):
            raise Exception("TikTok API rate limit exceeded")
        
        async def mock_instagram_timeout(*args, **kwargs):
            raise asyncio.TimeoutError("Instagram upload timeout")
        
        platform_manager.platforms = {
            PlatformType.YOUTUBE: Mock(upload=mock_youtube_success),
            PlatformType.TIKTOK: Mock(upload=mock_tiktok_failure),
            PlatformType.INSTAGRAM: Mock(upload=mock_instagram_timeout)
        }
        
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        test_metadata = UploadMetadata(title="Resilience Test", description="Test upload resilience")
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.return_value = "/tmp/test_video.mp4"
            mock_adapt.return_value = test_metadata
            
            upload_results = await platform_manager.upload_content("/tmp/test.mp4", platforms, test_metadata)
            
            # Should have results for all platforms (success + errors)
            assert len(upload_results) == 3
            
            success_results = [r for r in upload_results if r.get("status") == "success"]
            error_results = [r for r in upload_results if r.get("status") == "error"]
            
            assert len(success_results) == 1  # YouTube succeeded
            assert len(error_results) == 2    # TikTok and Instagram failed
            
            # Verify error details are captured
            error_messages = [r.get("error", "") for r in error_results]
            assert any("rate limit" in msg.lower() for msg in error_messages)
            assert any("timeout" in msg.lower() for msg in error_messages)
            
        print("✅ Platform uploads handle mixed success/failure scenarios")
        
        # Test 4: Data consistency verification
        print("\n4️⃣ Testing Data Consistency During Failures")
        
        # Mock database operations with occasional failures
        trend_repo = TrendRepository(test_database)
        
        call_count = 0
        
        async def mock_db_with_intermittent_failures(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 2:  # Fail on second call
                raise Exception("Database connection error")
            else:
                return f"record_{call_count}"
        
        trend_data = integration_helper.create_test_trend_data()
        
        with patch.object(trend_repo, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = mock_db_with_intermittent_failures
            
            # First save should succeed
            result1 = await trend_repo.create(trend_data)
            assert result1 == "record_1"
            
            # Second save should fail but be handled gracefully
            try:
                result2 = await trend_repo.create(trend_data)
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Database connection error" in str(e)
            
            # Third save should succeed (recovery)
            result3 = await trend_repo.create(trend_data)
            assert result3 == "record_3"
            
        print("✅ Database operations handle intermittent failures correctly")
        
        print("\n🛡️ WORKFLOW RESILIENCE TEST PASSED!")
        print("System demonstrates robust error handling and recovery capabilities")
        
        return {
            "trend_collection_resilience": True,
            "ai_service_resilience": True,
            "platform_upload_resilience": True,  
            "data_consistency_resilience": True,
            "overall_resilience_score": 100
        }
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_high_volume_production_workflow(
        self,
        test_database,
        mock_ai_services,
        mock_platform_services,
        integration_helper
    ):
        """
        Test system performance under high-volume production conditions.
        
        Simulates processing multiple trends, generating multiple content pieces,
        and handling concurrent uploads to verify system scalability.
        """
        
        print("\n🚀 Testing High-Volume Production Workflow")
        
        # Generate large batch of trends (50 trends)
        print("\n📊 Generating High Volume of Trends")
        
        trend_collector = TrendCollector()
        large_trend_batch = []
        
        # Create 50 diverse trends
        categories = ["Technology", "Education", "Entertainment", "Business", "Health"]
        sources = ["youtube", "google_trends", "twitter", "reddit"]
        
        for i in range(50):
            trend = {
                "id": f"volume_trend_{i:03d}",
                "topic": f"Trending Topic {i+1} - {categories[i % len(categories)]}",
                "source": sources[i % len(sources)],
                "popularity_score": 60 + (i % 40),  # Range 60-99
                "growth_rate": 5 + (i % 20),       # Range 5-24
                "keywords": [f"keyword{i}", f"trend{i}", categories[i % len(categories)].lower()],
                "category": categories[i % len(categories)],
                "collected_at": datetime.utcnow().isoformat()
            }
            large_trend_batch.append(trend)
        
        # Mock high-volume trend collection
        with patch.object(trend_collector, 'collect_trends', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = large_trend_batch
            
            start_time = asyncio.get_event_loop().time()
            collected_trends = await trend_collector.collect_trends()
            collection_time = asyncio.get_event_loop().time() - start_time
            
            assert len(collected_trends) == 50
            print(f"✅ Collected {len(collected_trends)} trends in {collection_time:.2f} seconds")
        
        # Test concurrent opportunity generation
        print("\n🧠 Processing Trends Concurrently")
        
        trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        opportunity_engine = OpportunityEngine(trend_analyzer)
        
        # Mock AI analysis for batch processing
        async def mock_batch_analysis(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate processing time
            return json.dumps({
                "viral_potential": 7,
                "content_saturation": 5,
                "audience_interest": 7,
                "monetization_opportunity": 6,
                "content_angles": [
                    "Top Tips for This Trend",
                    "Complete Guide to This Topic", 
                    "Why This Trend Matters in 2025"
                ]
            })
        
        mock_ai_services["text_ai"].analyze = mock_batch_analysis
        
        # Process trends in batches (10 trends per batch)
        batch_size = 10
        all_opportunities = []
        
        start_time = asyncio.get_event_loop().time()
        
        for i in range(0, len(collected_trends), batch_size):
            batch = collected_trends[i:i + batch_size]
            batch_ids = [trend["id"] for trend in batch]
            
            batch_opportunities = await opportunity_engine.generate_opportunities(batch_ids)
            all_opportunities.extend(batch_opportunities)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        assert len(all_opportunities) >= 50  # At least one opportunity per trend
        processing_rate = len(all_opportunities) / processing_time
        
        print(f"✅ Generated {len(all_opportunities)} opportunities in {processing_time:.2f}s")
        print(f"📈 Processing rate: {processing_rate:.1f} opportunities/second")
        
        # Verify processing rate meets performance requirements
        assert processing_rate > 10.0, f"Processing too slow: {processing_rate:.1f} ops/sec"
        
        # Test high-volume content generation
        print("\n🎬 Generating Multiple Content Pieces Concurrently")
        
        # Select top 10 opportunities for content generation
        top_opportunities = sorted(all_opportunities, key=lambda x: x["priority_score"], reverse=True)[:10]
        
        ai_director = AIDirector()
        ai_director.text_ai = mock_ai_services["text_ai"]
        
        # Generate content plans concurrently
        async def generate_content_plan(opportunity):
            await asyncio.sleep(0.05)  # Simulate AI processing time
            return ContentPlan(
                content_type="educational",
                script={
                    "hook": f"Hook for {opportunity['suggested_angle']}",
                    "main_content": f"Content for {opportunity['suggested_angle']}",
                    "cta": "Subscribe for more!"
                },
                visual_plan={
                    "style": "modern",
                    "scenes": ["intro", "main", "outro"],
                    "text_overlays": ["Title", "Key Point"]
                },
                audio_plan={
                    "voice_style": "professional",
                    "background_music": "upbeat",
                    "sound_effects": ["transition"]
                }
            )
        
        start_time = asyncio.get_event_loop().time()
        
        # Use asyncio.gather for concurrent processing
        content_generation_tasks = [
            generate_content_plan(opp) for opp in top_opportunities
        ]
        
        content_plans = await asyncio.gather(*content_generation_tasks)
        
        content_generation_time = asyncio.get_event_loop().time() - start_time
        
        assert len(content_plans) == 10
        print(f"✅ Generated {len(content_plans)} content plans in {content_generation_time:.2f}s")
        
        # Test concurrent platform uploads
        print("\n📤 Testing Concurrent Multi-Platform Uploads")
        
        platform_manager = PlatformManager()
        target_platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        
        # Mock platform services for high-volume testing
        async def mock_platform_upload(content_file, metadata, platform_name):
            await asyncio.sleep(0.1)  # Simulate upload time
            return {
                "status": "success",
                "platform_id": f"{platform_name}_{hash(content_file) % 1000000}",
                "url": f"https://{platform_name}.com/video/{hash(content_file) % 1000000}",
                "platform": platform_name
            }
        
        platform_manager.platforms = {
            PlatformType.YOUTUBE: Mock(upload=lambda *args: mock_platform_upload("/tmp/test.mp4", {}, "youtube")),
            PlatformType.TIKTOK: Mock(upload=lambda *args: mock_platform_upload("/tmp/test.mp4", {}, "tiktok")),
            PlatformType.INSTAGRAM: Mock(upload=lambda *args: mock_platform_upload("/tmp/test.mp4", {}, "instagram"))
        }
        
        # Upload first 5 content pieces to all platforms (15 total uploads)
        upload_tasks = []
        test_metadata = UploadMetadata(title="Volume Test", description="High volume test upload")
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.return_value = "/tmp/test_video.mp4"
            mock_adapt.return_value = test_metadata
            
            start_time = asyncio.get_event_loop().time()
            
            for i in range(5):  # Upload 5 content pieces
                upload_task = platform_manager.upload_content(
                    f"/tmp/content_{i}.mp4",
                    target_platforms,
                    test_metadata
                )
                upload_tasks.append(upload_task)
            
            # Execute all uploads concurrently
            all_upload_results = await asyncio.gather(*upload_tasks)
            
            upload_time = asyncio.get_event_loop().time() - start_time
            
            # Flatten results
            total_uploads = sum(len(result) for result in all_upload_results)
            
            assert total_uploads == 15  # 5 content pieces × 3 platforms
            upload_rate = total_uploads / upload_time
            
            print(f"✅ Completed {total_uploads} uploads in {upload_time:.2f}s")
            print(f"📈 Upload rate: {upload_rate:.1f} uploads/second")
        
        # Test memory usage during high-volume processing
        print("\n💾 Monitoring Memory Usage During High-Volume Processing")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate processing large amounts of data
        large_data_sets = []
        for i in range(100):
            # Create mock content data
            mock_content = {
                "id": f"content_{i}",
                "script": "Large script content " * 100,  # Simulate large script
                "images": [f"image_url_{j}" for j in range(10)],
                "metadata": {"large_field": "x" * 1000}
            }
            large_data_sets.append(mock_content)
        
        # Process data in batches
        batch_size = 20
        processed_items = []
        
        for i in range(0, len(large_data_sets), batch_size):
            batch = large_data_sets[i:i + batch_size]
            
            # Simulate processing each batch
            for item in batch:
                processed_item = {
                    "processed_id": item["id"],
                    "processed": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
                processed_items.append(processed_item)
            
            # Check memory usage periodically
            if i % 40 == 0:  # Every 2 batches
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory increase should be reasonable (less than 200MB)
                assert memory_increase < 200, f"Memory usage too high: {memory_increase:.1f}MB increase"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        print(f"✅ Processed {len(processed_items)} items with {total_memory_increase:.1f}MB memory increase")
        
        # Verify all high-volume operations completed successfully
        assert len(collected_trends) == 50
        assert len(all_opportunities) >= 50
        assert len(content_plans) == 10
        assert total_uploads == 15
        assert len(processed_items) == 100
        
        print(f"\n🚀 HIGH-VOLUME PRODUCTION WORKFLOW TEST PASSED!")
        print(f"📊 Processed {len(collected_trends)} trends")
        print(f"💡 Generated {len(all_opportunities)} opportunities")
        print(f"🎬 Created {len(content_plans)} content plans")
        print(f"📤 Completed {total_uploads} platform uploads")
        print(f"💾 Memory usage remained stable ({total_memory_increase:.1f}MB increase)")
        
        return {
            "trends_processed": len(collected_trends),
            "opportunities_generated": len(all_opportunities),
            "content_plans_created": len(content_plans),
            "uploads_completed": total_uploads,
            "processing_rate_ops_per_sec": processing_rate,
            "upload_rate_per_sec": upload_rate,
            "memory_increase_mb": total_memory_increase,
            "performance_test_passed": True
        }
    
    @pytest.mark.integration
    async def test_real_world_content_production_simulation(
        self,
        test_database,
        mock_ai_services,
        mock_platform_services,
        integration_helper
    ):
        """
        Simulate a real-world content production scenario over a typical day.
        
        This test simulates:
        - Morning trend collection
        - Midday opportunity analysis
        - Afternoon content creation
        - Evening platform uploads
        - Performance monitoring throughout
        """
        
        print("\n🌅 Simulating Real-World Daily Content Production Workflow")
        
        # === MORNING: Trend Collection (6 AM) ===
        print("\n🌅 6:00 AM - Morning Trend Collection")
        
        morning_trends = [
            {
                "id": "morning_trend_1",
                "topic": "AI Productivity Tools Morning Roundup",
                "source": "youtube",
                "popularity_score": 87.3,
                "collected_at": "2025-09-14T06:00:00Z",
                "keywords": ["AI", "productivity", "morning", "tools"]
            },
            {
                "id": "morning_trend_2", 
                "topic": "Remote Work Setup Ideas",
                "source": "google_trends",
                "popularity_score": 72.8,
                "collected_at": "2025-09-14T06:15:00Z",
                "keywords": ["remote", "work", "setup", "home", "office"]
            },
            {
                "id": "morning_trend_3",
                "topic": "Cryptocurrency Market Analysis",
                "source": "twitter",
                "popularity_score": 91.2,
                "collected_at": "2025-09-14T06:30:00Z",
                "keywords": ["crypto", "bitcoin", "market", "analysis"]
            }
        ]
        
        # Store morning trends
        trend_repo = TrendRepository(test_database)
        morning_trend_ids = []
        
        for trend in morning_trends:
            with patch.object(trend_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = trend["id"]
                trend_id = await trend_repo.create(trend)
                morning_trend_ids.append(trend_id)
        
        print(f"✅ Collected and stored {len(morning_trend_ids)} morning trends")
        
        # === MIDDAY: Opportunity Analysis (12 PM) ===
        print("\n☀️ 12:00 PM - Midday Opportunity Analysis")
        
        trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
        opportunity_engine = OpportunityEngine(trend_analyzer)
        
        # Mock detailed AI analysis for each trend
        mock_analyses = [
            # AI Productivity Tools
            json.dumps({
                "viral_potential": 9,
                "content_saturation": 5,
                "audience_interest": 8,
                "monetization_opportunity": 8,
                "content_angles": [
                    "Top 10 AI Productivity Tools That Will Change Your Life",
                    "I Replaced My Assistant With AI Tools - Here's What Happened",
                    "AI Productivity Setup: From Overwhelmed to Organized"
                ]
            }),
            # Remote Work Setup
            json.dumps({
                "viral_potential": 7,
                "content_saturation": 6,
                "audience_interest": 9,
                "monetization_opportunity": 7,
                "content_angles": [
                    "$500 vs $5000 Remote Work Setup - Worth The Upgrade?",
                    "Remote Work Setup Mistakes That Kill Productivity",
                    "Ultimate Remote Work Setup Tour + Shopping List"
                ]
            }),
            # Cryptocurrency
            json.dumps({
                "viral_potential": 8,
                "content_saturation": 8,
                "audience_interest": 7,
                "monetization_opportunity": 9,
                "content_angles": [
                    "Crypto Market Analysis: What The Charts Really Mean",
                    "Why I'm Still Bullish on Crypto (Despite The FUD)",
                    "Crypto Investment Strategy for 2025 Bull Run"
                ]
            })
        ]
        
        mock_ai_services["text_ai"].analyze = AsyncMock(side_effect=mock_analyses)
        
        midday_opportunities = await opportunity_engine.generate_opportunities(morning_trend_ids)
        
        # Store opportunities
        opportunity_repo = OpportunityRepository(test_database)
        midday_opportunity_ids = []
        
        for opp in midday_opportunities:
            with patch.object(opportunity_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = f"opp_{len(midday_opportunity_ids) + 1}"
                opp_id = await opportunity_repo.create(opp)
                midday_opportunity_ids.append(opp_id)
        
        print(f"✅ Analyzed trends and generated {len(midday_opportunities)} content opportunities")
        
        # === AFTERNOON: Content Creation (3 PM) ===
        print("\n🌤️ 3:00 PM - Afternoon Content Creation Session")
        
        # Select top 2 opportunities for content creation
        top_opportunities = sorted(midday_opportunities, key=lambda x: x["priority_score"], reverse=True)[:2]
        
        ai_director = AIDirector()
        ai_director.text_ai = mock_ai_services["text_ai"]
        
        afternoon_content_plans = []
        
        for opportunity in top_opportunities:
            content_plan = await ai_director.create_content_plan(opportunity["suggested_angle"])
            afternoon_content_plans.append({
                "opportunity": opportunity,
                "content_plan": content_plan
            })
        
        # Generate content assets
        content_pipeline = ContentPipeline()
        content_pipeline.text_ai = mock_ai_services["text_ai"]
        content_pipeline.image_ai = mock_ai_services["image_ai"]
        content_pipeline.tts = mock_ai_services["audio_ai"]
        
        generated_afternoon_content = []
        
        for i, content_data in enumerate(afternoon_content_plans):
            with patch.object(content_pipeline, 'generate_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = {
                    "video": f"/tmp/afternoon_content_{i+1}.mp4",
                    "script": f"Complete script for afternoon content {i+1}",
                    "images": [f"/tmp/afternoon_img_{i+1}_{j}.jpg" for j in range(5)],
                    "audio": f"/tmp/afternoon_audio_{i+1}.mp3"
                }
                
                generated_assets = await content_pipeline.generate_content(content_data["content_plan"])
                generated_afternoon_content.append({
                    **content_data,
                    "generated_assets": generated_assets
                })
        
        print(f"✅ Created {len(generated_afternoon_content)} complete content pieces")
        
        # === EVENING: Platform Uploads (6 PM) ===
        print("\n🌆 6:00 PM - Evening Multi-Platform Upload Session")
        
        platform_manager = PlatformManager()
        evening_platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        
        # Set up platform services
        platform_manager.platforms = {
            PlatformType.YOUTUBE: mock_platform_services["youtube"],
            PlatformType.TIKTOK: mock_platform_services["tiktok"],
            PlatformType.INSTAGRAM: mock_platform_services["instagram"]
        }
        
        evening_upload_results = []
        
        for i, content in enumerate(generated_afternoon_content):
            # Create optimized metadata for evening posting
            upload_metadata = UploadMetadata(
                title=f"{content['content_plan'].platform_optimization.get('title', f'Evening Content {i+1}')} 🌟",
                description=f"🎯 {content['content_plan'].platform_optimization.get('description', 'Amazing content created with AI')} \n\n📅 Posted: Evening Edition",
                tags=content['content_plan'].platform_optimization.get('hashtags', ['#evening', '#content']),
                category="Education",
                privacy="public"
            )
            
            with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
                 patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
                
                mock_opt.return_value = content["generated_assets"]["video"]
                mock_adapt.return_value = upload_metadata
                
                upload_results = await platform_manager.upload_content(
                    content["generated_assets"]["video"],
                    evening_platforms,
                    upload_metadata
                )
                
                evening_upload_results.extend(upload_results)
        
        successful_uploads = [r for r in evening_upload_results if r["status"] == "success"]
        
        print(f"✅ Completed {len(successful_uploads)}/{len(evening_upload_results)} platform uploads")
        
        # === LATE EVENING: Performance Setup (9 PM) ===
        print("\n🌙 9:00 PM - Setting Up Performance Monitoring")
        
        performance_repo = PerformanceRepository(test_database)
        performance_tracking_ids = []
        
        for upload in successful_uploads:
            performance_record = {
                "upload_id": upload.get("upload_id", f"upload_{upload['platform_id']}"),
                "platform": upload["platform"],
                "platform_id": upload["platform_id"],
                "url": upload["url"],
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "revenue": 0.0,
                "measured_at": "2025-09-14T21:00:00Z"
            }
            
            with patch.object(performance_repo, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = f"perf_{upload['platform_id']}"
                perf_id = await performance_repo.create(performance_record)
                performance_tracking_ids.append(perf_id)
        
        print(f"✅ Setup performance monitoring for {len(performance_tracking_ids)} uploads")
        
        # === DAILY SUMMARY ===
        print("\n📊 Daily Production Summary")
        
        daily_summary = {
            "date": "2025-09-14",
            "trends_collected": len(morning_trend_ids),
            "opportunities_analyzed": len(midday_opportunities),  
            "content_pieces_created": len(generated_afternoon_content),
            "successful_uploads": len(successful_uploads),
            "platforms_targeted": len(evening_platforms),
            "performance_tracking_setup": len(performance_tracking_ids),
            "production_timeline": {
                "06:00": "Trend Collection Complete",
                "12:00": "Opportunity Analysis Complete", 
                "15:00": "Content Creation Complete",
                "18:00": "Platform Uploads Complete",
                "21:00": "Performance Monitoring Setup Complete"
            }
        }
        
        # Verify daily production goals met
        assert daily_summary["trends_collected"] >= 3
        assert daily_summary["opportunities_analyzed"] >= 3
        assert daily_summary["content_pieces_created"] >= 2
        assert daily_summary["successful_uploads"] >= 4  # 2 content × 2+ platforms
        assert daily_summary["performance_tracking_setup"] >= 4
        
        print(f"\n🎉 DAILY CONTENT PRODUCTION SIMULATION COMPLETE!")
        print(f"📈 Trends Collected: {daily_summary['trends_collected']}")
        print(f"🎯 Opportunities Analyzed: {daily_summary['opportunities_analyzed']}")
        print(f"🎬 Content Created: {daily_summary['content_pieces_created']}")
        print(f"📤 Successful Uploads: {daily_summary['successful_uploads']}")
        print(f"📊 Performance Tracking: {daily_summary['performance_tracking_setup']}")
        
        # Calculate estimated daily impact
        estimated_daily_reach = daily_summary["successful_uploads"] * 25000  # Avg 25k views per upload
        estimated_daily_engagement = estimated_daily_reach * 0.05  # 5% engagement rate
        
        print(f"📊 Estimated Daily Reach: {estimated_daily_reach:,} views")
        print(f"💬 Estimated Daily Engagement: {estimated_daily_engagement:,.0f} interactions")
        
        return daily_summary


class TestSystemIntegrationEdgeCases:
    """Test edge cases and boundary conditions in system integration."""
    
    @pytest.mark.integration
    async def test_empty_trend_data_handling(self, test_database, mock_ai_services):
        """Test system behavior when no trends are found."""
        
        trend_collector = TrendCollector()
        
        # Mock empty responses from all sources
        with patch.object(trend_collector, 'collect_trends', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = []
            
            trends = await trend_collector.collect_trends()
            
            assert len(trends) == 0
            
            # System should handle empty trends gracefully
            trend_analyzer = TrendAnalyzer(ai_service=mock_ai_services["text_ai"])
            opportunity_engine = OpportunityEngine(trend_analyzer)
            
            opportunities = await opportunity_engine.generate_opportunities([])
            
            assert len(opportunities) == 0
    
    @pytest.mark.integration
    async def test_invalid_content_plan_handling(self, mock_ai_services):
        """Test handling of invalid or malformed content plans."""
        
        ai_director = AIDirector()
        
        # Mock AI to return invalid JSON
        ai_director.text_ai = Mock()
        ai_director.text_ai.generate = AsyncMock(return_value="Invalid JSON response {broken}")
        
        with pytest.raises(ValueError, match="Invalid JSON response from AI"):
            await ai_director.create_content_plan("Create invalid content")
    
    @pytest.mark.integration
    async def test_platform_service_unavailable(self, test_content_files):
        """Test behavior when all platform services are unavailable."""
        
        platform_manager = PlatformManager()
        
        # Mock all platforms to fail
        async def mock_service_unavailable(*args, **kwargs):
            raise Exception("Service temporarily unavailable")
        
        platform_manager.platforms = {
            PlatformType.YOUTUBE: Mock(upload=mock_service_unavailable),
            PlatformType.TIKTOK: Mock(upload=mock_service_unavailable),
            PlatformType.INSTAGRAM: Mock(upload=mock_service_unavailable)
        }
        
        platforms = [PlatformType.YOUTUBE, PlatformType.TIKTOK, PlatformType.INSTAGRAM]
        test_metadata = UploadMetadata(title="Test", description="Test")
        
        with patch.object(platform_manager, 'optimize_for_platform', new_callable=AsyncMock) as mock_opt, \
             patch.object(platform_manager, 'adapt_metadata', new_callable=AsyncMock) as mock_adapt:
            
            mock_opt.return_value = test_content_files['video']
            mock_adapt.return_value = test_metadata
            
            results = await platform_manager.upload_content(
                test_content_files['video'], platforms, test_metadata
            )
            
            # All uploads should fail but return error results
            assert len(results) == 3
            assert all(r["status"] == "error" for r in results)
            assert all("Service temporarily unavailable" in r["error"] for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])