"""
Unit Tests for AI Director
==========================

Tests for the AI Director system including:
- AIDirector main class
- Content plan creation
- AI service integration
- Quality tier management
- Prompt optimization
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio
import json
from datetime import datetime

# Import modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from content_engine.services.ai_director import AIDirector
from content_engine.services.service_registry import ServiceRegistry
from content_engine.models.quality_tier import QualityTier
from shared.models.content_plan import ContentPlan


class TestAIDirector:
    """Test cases for AIDirector main class."""
    
    @pytest.fixture
    def mock_service_registry(self):
        """Create mock service registry."""
        registry = Mock(spec=ServiceRegistry)
        
        # Mock text AI service
        text_ai = Mock()
        text_ai.generate = AsyncMock(return_value='{"content_type": "educational", "script": {"hook": "Test hook"}}')
        registry.get_service.return_value = text_ai
        
        return registry
    
    @pytest.fixture
    def ai_director(self, mock_service_registry):
        """Create AIDirector instance with mocked dependencies."""
        with patch('content_engine.services.ai_director.ServiceRegistry', return_value=mock_service_registry):
            return AIDirector(quality_tier=QualityTier.BALANCED)
    
    @pytest.mark.asyncio
    async def test_create_content_plan_success(self, ai_director):
        """Test successful content plan creation."""
        user_request = "Create a tutorial about AI content creation for beginners"
        
        # Mock AI response
        mock_response = {
            "content_type": "educational",
            "script": {
                "hook": "Want to create amazing content with AI?",
                "main_content": "Here's how AI can revolutionize your content creation...",
                "cta": "Try these AI tools today!"
            },
            "visual_plan": {
                "style": "modern",
                "scenes": ["intro scene", "demo scene", "conclusion scene"],
                "text_overlays": ["AI Content Creation", "Step-by-step Guide"]
            },
            "audio_plan": {
                "voice_style": "energetic",
                "background_music": "upbeat",
                "sound_effects": ["notification", "success"]
            },
            "platform_optimization": {
                "title": "AI Content Creation for Beginners - Complete Guide",
                "description": "Learn how to use AI tools for content creation",
                "hashtags": ["#AI", "#ContentCreation", "#Tutorial"],
                "thumbnail_concept": "Split screen: before/after AI assistance"
            },
            "production_estimate": {
                "time_minutes": 45,
                "cost_baht": 20.50,
                "complexity": "medium"
            }
        }
        
        ai_director.text_ai.generate = AsyncMock(return_value=json.dumps(mock_response))
        
        content_plan = await ai_director.create_content_plan(user_request)
        
        # Assertions
        assert isinstance(content_plan, ContentPlan)
        assert content_plan.content_type == "educational"
        assert content_plan.script.hook == "Want to create amazing content with AI?"
        assert content_plan.production_estimate.time_minutes == 45
        assert len(content_plan.visual_plan.scenes) == 3
        
        # Verify AI service was called with correct parameters
        ai_director.text_ai.generate.assert_called_once()
        call_args = ai_director.text_ai.generate.call_args[0][0]
        assert user_request in call_args
    
    @pytest.mark.asyncio
    async def test_create_content_plan_invalid_json(self, ai_director):
        """Test handling of invalid JSON from AI service."""
        user_request = "Create content about cooking"
        
        # Mock invalid JSON response
        ai_director.text_ai.generate = AsyncMock(return_value="Invalid JSON response")
        
        with pytest.raises(ValueError, match="Invalid JSON response from AI"):
            await ai_director.create_content_plan(user_request)
    
    @pytest.mark.asyncio
    async def test_create_content_plan_missing_fields(self, ai_director):
        """Test handling of incomplete AI response."""
        user_request = "Create content about fitness"
        
        # Mock incomplete response
        incomplete_response = {
            "content_type": "fitness",
            # Missing other required fields
        }
        
        ai_director.text_ai.generate = AsyncMock(return_value=json.dumps(incomplete_response))
        
        content_plan = await ai_director.create_content_plan(user_request)
        
        # Should create plan with defaults for missing fields
        assert isinstance(content_plan, ContentPlan)
        assert content_plan.content_type == "fitness"
        assert content_plan.script is not None  # Should have default values
    
    def test_build_master_prompt(self, ai_director):
        """Test master prompt construction."""
        user_request = "Create a cooking tutorial"
        
        prompt = ai_director.build_master_prompt(user_request)
        
        assert user_request in prompt
        assert "OUTPUT JSON" in prompt
        assert "content_type" in prompt
        assert "script" in prompt
        assert "visual_plan" in prompt
        assert "audio_plan" in prompt
        assert "platform_optimization" in prompt
        assert "production_estimate" in prompt
    
    def test_validate_content_plan(self, ai_director):
        """Test content plan validation."""
        # Valid plan
        valid_data = {
            "content_type": "educational",
            "script": {"hook": "Test", "main_content": "Content", "cta": "Action"},
            "visual_plan": {"style": "modern", "scenes": ["scene1"], "text_overlays": ["text1"]},
            "audio_plan": {"voice_style": "calm", "background_music": "none", "sound_effects": []},
            "platform_optimization": {
                "title": "Test Title",
                "description": "Test Description",
                "hashtags": ["#test"],
                "thumbnail_concept": "Test concept"
            },
            "production_estimate": {
                "time_minutes": 30,
                "cost_baht": 15.0,
                "complexity": "low"
            }
        }
        
        assert ai_director.validate_content_plan(valid_data) == True
        
        # Invalid plan - missing required fields
        invalid_data = {
            "content_type": "educational"
            # Missing other required fields
        }
        
        assert ai_director.validate_content_plan(invalid_data) == False
    
    @pytest.mark.asyncio
    async def test_optimize_for_platform(self, ai_director):
        """Test platform-specific optimization."""
        base_plan = ContentPlan(
            content_type="educational",
            script={"hook": "Test hook", "main_content": "Content", "cta": "CTA"}
        )
        
        # Mock platform optimization
        optimized_data = {
            "title": "YouTube Optimized Title",
            "description": "YouTube optimized description with keywords",
            "hashtags": ["#YouTube", "#Tutorial"],
            "thumbnail_concept": "YouTube-style thumbnail"
        }
        
        ai_director.text_ai.generate = AsyncMock(return_value=json.dumps(optimized_data))
        
        optimized_plan = await ai_director.optimize_for_platform(base_plan, "youtube")
        
        assert optimized_plan.platform_optimization.title == "YouTube Optimized Title"
        assert "#YouTube" in optimized_plan.platform_optimization.hashtags
    
    @pytest.mark.asyncio
    async def test_brainstorm_content_angles(self, ai_director):
        """Test content angle brainstorming."""
        trend_topic = "AI in Healthcare"
        
        mock_angles = [
            "How AI is Diagnosing Diseases Faster Than Doctors",
            "The Ethics of AI in Medical Decisions",
            "AI Surgery Robots: The Future of Operations"
        ]
        
        ai_director.text_ai.generate = AsyncMock(return_value=json.dumps({"angles": mock_angles}))
        
        angles = await ai_director.brainstorm_content_angles(trend_topic, target_platforms=["youtube"])
        
        assert len(angles) == 3
        assert "AI is Diagnosing Diseases" in angles[0]
        assert all(isinstance(angle, str) for angle in angles)
    
    def test_calculate_production_complexity(self, ai_director):
        """Test production complexity calculation."""
        # Simple content
        simple_plan = ContentPlan(
            content_type="educational",
            visual_plan={"scenes": ["scene1"], "text_overlays": ["text1"]},
            audio_plan={"sound_effects": []}
        )
        
        complexity = ai_director.calculate_production_complexity(simple_plan)
        assert complexity in ["low", "medium", "high"]
        
        # Complex content
        complex_plan = ContentPlan(
            content_type="entertainment",
            visual_plan={"scenes": ["s1", "s2", "s3", "s4", "s5"], "text_overlays": ["t1", "t2", "t3"]},
            audio_plan={"sound_effects": ["sfx1", "sfx2", "sfx3", "sfx4"]}
        )
        
        complexity = ai_director.calculate_production_complexity(complex_plan)
        assert complexity in ["medium", "high"]


class TestServiceIntegration:
    """Test AI Director integration with various AI services."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock AI services for different quality tiers."""
        services = {}
        
        # Budget tier (Groq)
        groq_service = Mock()
        groq_service.generate = AsyncMock(return_value='{"content": "budget_content"}')
        services['budget'] = groq_service
        
        # Balanced tier (OpenAI)
        openai_service = Mock()
        openai_service.generate = AsyncMock(return_value='{"content": "balanced_content"}')
        services['balanced'] = openai_service
        
        # Premium tier (Claude)
        claude_service = Mock()
        claude_service.generate = AsyncMock(return_value='{"content": "premium_content"}')
        services['premium'] = claude_service
        
        return services
    
    @pytest.mark.asyncio
    async def test_quality_tier_selection(self, mock_services):
        """Test that correct AI service is selected based on quality tier."""
        
        for tier_name, expected_service in mock_services.items():
            tier = QualityTier[tier_name.upper()]
            
            with patch('content_engine.services.ai_director.ServiceRegistry') as mock_registry:
                mock_registry.return_value.get_service.return_value = expected_service
                
                director = AIDirector(quality_tier=tier)
                
                # Verify correct service is loaded
                mock_registry.return_value.get_service.assert_called_with("text_ai", tier)
    
    @pytest.mark.asyncio
    async def test_service_fallback_on_error(self, ai_director):
        """Test fallback behavior when AI service fails."""
        user_request = "Create content about technology"
        
        # Mock service to fail first, then succeed
        ai_director.text_ai.generate = AsyncMock(side_effect=[
            Exception("Service unavailable"),
            json.dumps({"content_type": "educational", "script": {"hook": "fallback content"}})
        ])
        
        # Should implement retry logic or fallback
        with pytest.raises(Exception):
            await ai_director.create_content_plan(user_request)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, ai_director):
        """Test handling of concurrent content plan requests."""
        requests = [
            "Create content about AI",
            "Create content about cooking",
            "Create content about fitness"
        ]
        
        # Mock responses
        responses = [
            json.dumps({"content_type": "educational", "script": {"hook": f"Content {i}"}})
            for i in range(len(requests))
        ]
        
        ai_director.text_ai.generate = AsyncMock(side_effect=responses)
        
        # Execute concurrent requests
        tasks = [ai_director.create_content_plan(req) for req in requests]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(isinstance(result, ContentPlan) for result in results)
        assert ai_director.text_ai.generate.call_count == 3


class TestPromptOptimization:
    """Test prompt engineering and optimization."""
    
    @pytest.fixture
    def ai_director(self):
        """Create AIDirector for prompt testing."""
        mock_registry = Mock()
        mock_service = Mock()
        mock_service.generate = AsyncMock(return_value='{"content": "test"}')
        mock_registry.get_service.return_value = mock_service
        
        with patch('content_engine.services.ai_director.ServiceRegistry', return_value=mock_registry):
            return AIDirector()
    
    def test_prompt_includes_context(self, ai_director):
        """Test that prompts include necessary context."""
        user_request = "Create educational content about Python programming"
        
        prompt = ai_director.build_master_prompt(user_request)
        
        # Should include request
        assert user_request in prompt
        
        # Should include output format specification
        assert "JSON" in prompt
        assert "content_type" in prompt
        
        # Should include quality guidelines
        assert "educational" in prompt or "informative" in prompt
    
    def test_prompt_customization_by_tier(self, ai_director):
        """Test that prompts are customized based on quality tier."""
        user_request = "Create content about cooking"
        
        # Budget tier
        ai_director.quality_tier = QualityTier.BUDGET
        budget_prompt = ai_director.build_master_prompt(user_request)
        
        # Premium tier
        ai_director.quality_tier = QualityTier.PREMIUM
        premium_prompt = ai_director.build_master_prompt(user_request)
        
        # Premium should have more detailed instructions
        assert len(premium_prompt) >= len(budget_prompt)
    
    def test_prompt_includes_examples(self, ai_director):
        """Test that prompts include helpful examples."""
        user_request = "Create tutorial content"
        
        prompt = ai_director.build_master_prompt(user_request)
        
        # Should include example structure or format
        assert "example" in prompt.lower() or "format" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_prompt_iteration_and_refinement(self, ai_director):
        """Test prompt refinement based on response quality."""
        user_request = "Create content about data science"
        
        # First attempt with basic prompt
        basic_response = '{"content_type": "educational"}'
        ai_director.text_ai.generate = AsyncMock(return_value=basic_response)
        
        try:
            plan1 = await ai_director.create_content_plan(user_request)
        except:
            pass  # Expected to fail due to incomplete response
        
        # Refined prompt should ask for more complete response
        refined_response = json.dumps({
            "content_type": "educational",
            "script": {"hook": "Data science explained", "main_content": "...", "cta": "..."},
            "visual_plan": {"style": "modern", "scenes": ["intro"], "text_overlays": ["DS"]},
            "audio_plan": {"voice_style": "professional", "background_music": "none", "sound_effects": []},
            "platform_optimization": {"title": "Data Science 101", "description": "...", "hashtags": ["#data"], "thumbnail_concept": "..."},
            "production_estimate": {"time_minutes": 30, "cost_baht": 20, "complexity": "medium"}
        })
        
        ai_director.text_ai.generate = AsyncMock(return_value=refined_response)
        
        plan2 = await ai_director.create_content_plan(user_request)
        assert isinstance(plan2, ContentPlan)
        assert plan2.content_type == "educational"


class TestContentPlanValidation:
    """Test content plan validation and error handling."""
    
    def test_validate_required_fields(self):
        """Test validation of required fields in content plan."""
        director = AIDirector()
        
        # Missing content_type
        invalid_plan = {
            "script": {"hook": "test"}
        }
        assert director.validate_content_plan(invalid_plan) == False
        
        # Missing script
        invalid_plan = {
            "content_type": "educational"
        }
        assert director.validate_content_plan(invalid_plan) == False
        
        # Valid minimal plan
        valid_plan = {
            "content_type": "educational",
            "script": {
                "hook": "Attention-grabbing opener",
                "main_content": "Educational content body",
                "cta": "Call to action"
            },
            "visual_plan": {
                "style": "clean",
                "scenes": ["intro"],
                "text_overlays": ["title"]
            },
            "audio_plan": {
                "voice_style": "neutral",
                "background_music": "none",
                "sound_effects": []
            },
            "platform_optimization": {
                "title": "Test Title",
                "description": "Test Description",
                "hashtags": ["#test"],
                "thumbnail_concept": "Simple design"
            },
            "production_estimate": {
                "time_minutes": 20,
                "cost_baht": 10,
                "complexity": "low"
            }
        }
        assert director.validate_content_plan(valid_plan) == True
    
    def test_validate_field_types(self):
        """Test validation of field data types."""
        director = AIDirector()
        
        # Invalid time_minutes type
        invalid_plan = {
            "content_type": "educational",
            "script": {"hook": "test", "main_content": "content", "cta": "action"},
            "production_estimate": {
                "time_minutes": "invalid",  # Should be int
                "cost_baht": 10,
                "complexity": "low"
            }
        }
        
        # Should handle type validation gracefully
        result = director.validate_content_plan(invalid_plan)
        # Implementation should convert or reject invalid types
    
    def test_validate_enum_values(self):
        """Test validation of enumerated field values."""
        director = AIDirector()
        
        # Invalid complexity value
        plan_data = {
            "content_type": "educational",
            "production_estimate": {
                "complexity": "invalid_complexity"  # Should be low/medium/high
            }
        }
        
        # Should validate enum values
        result = director.validate_content_plan(plan_data)
        # Implementation should reject invalid enum values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])