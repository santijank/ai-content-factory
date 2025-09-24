"""
Test Fixtures Package
=====================

This package contains test data, mock objects, and helper utilities
used across different test suites.

Fixtures include:
- Sample trend data
- Sample content data
- Mock API responses
- Test database data
- Helper functions for test setup
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import random

def load_json_fixture(filename: str) -> Dict[str, Any]:
    """Load JSON fixture file."""
    fixture_path = os.path.join(os.path.dirname(__file__), filename)
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_fixture(data: Dict[str, Any], filename: str):
    """Save data as JSON fixture file."""
    fixture_path = os.path.join(os.path.dirname(__file__), filename)
    with open(fixture_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_fixture_path(filename: str) -> str:
    """Get full path to fixture file."""
    return os.path.join(os.path.dirname(__file__), filename)

# Common test data generators
def generate_test_trends(count: int = 5) -> List[Dict[str, Any]]:
    """Generate test trend data."""
    trends = []
    
    topics = [
        "AI Content Creation Tools 2025",
        "Machine Learning for Beginners", 
        "Python Programming Tips",
        "Data Science Tutorial Complete Guide",
        "Web Development Trends",
        "Productivity Hacks for Remote Work",
        "Digital Marketing Strategies",
        "Cryptocurrency Investment Guide",
        "Fitness Workout at Home",
        "Cooking Recipes Easy"
    ]
    
    categories = ["Technology", "Education", "Business", "Health", "Entertainment"]
    sources = ["youtube", "google_trends", "twitter", "reddit"]
    
    for i in range(count):
        trend_id = f"test_trend_{uuid.uuid4().hex[:8]}"
        topic = topics[i % len(topics)]
        
        # Generate keywords from topic
        keywords = topic.lower().replace(" ", "").split() + ["tutorial", "guide", "tips"]
        keywords = list(set(keywords))[:8]  # Limit to 8 unique keywords
        
        trend = {
            "id": trend_id,
            "topic": topic,
            "source": sources[i % len(sources)],
            "popularity_score": round(60.0 + random.uniform(0, 35), 1),
            "growth_rate": round(5.0 + random.uniform(0, 20), 1),
            "category": categories[i % len(categories)],
            "region": random.choice(["Global", "US", "Europe", "Asia"]),
            "keywords": keywords,
            "collected_at": (datetime.utcnow() - timedelta(hours=random.randint(0, 72))).isoformat(),
            "raw_data": {
                "search_volume": random.randint(1000, 200000),
                "competition": random.choice(["low", "medium", "high"]),
                "related_topics": [f"related_topic_{j}" for j in range(3)],
                "engagement_rate": round(random.uniform(2.0, 8.0), 2)
            }
        }
        trends.append(trend)
    
    return trends

def generate_test_opportunities(trend_ids: List[str] = None, count: int = 3) -> List[Dict[str, Any]]:
    """Generate test content opportunities."""
    if trend_ids is None:
        trend_ids = [f"trend_{i}" for i in range(count)]
    
    opportunities = []
    
    angles = [
        "How AI is Revolutionizing Content Creation in 2025",
        "5 Machine Learning Concepts Every Beginner Must Know",
        "Python Automation Scripts That Will Save You Hours",
        "Data Science Project Ideas for Your Portfolio",
        "Web Development Framework Comparison Guide",
        "Remote Work Productivity System That Actually Works",
        "Digital Marketing Trends You Can't Ignore",
        "Cryptocurrency Investment Strategy for Beginners",
        "Home Workout Routine Without Equipment",
        "Quick and Easy Meal Prep Ideas"
    ]
    
    content_types = ["educational", "tutorial", "entertainment", "news", "review"]
    platforms = ["youtube", "tiktok", "instagram", "facebook"]
    
    for i in range(count):
        opportunity_id = f"test_opportunity_{uuid.uuid4().hex[:8]}"
        trend_id = trend_ids[i % len(trend_ids)]
        
        opportunity = {
            "id": opportunity_id,
            "trend_id": trend_id,
            "suggested_angle": angles[i % len(angles)],
            "estimated_views": random.randint(10000, 500000),
            "competition_level": random.choice(["low", "medium", "high"]),
            "production_cost": round(random.uniform(10.0, 100.0), 2),
            "estimated_roi": round(random.uniform(1.5, 8.0), 1),
            "priority_score": round(random.uniform(5.0, 10.0), 1),
            "status": random.choice(["pending", "selected", "in_progress", "completed"]),
            "content_type": random.choice(content_types),
            "target_platforms": random.sample(platforms, random.randint(1, 3)),
            "created_at": (datetime.utcnow() - timedelta(hours=random.randint(0, 48))).isoformat(),
            "difficulty_level": random.choice(["beginner", "intermediate", "advanced"]),
            "estimated_duration": random.randint(30, 600)  # seconds
        }
        opportunities.append(opportunity)
    
    return opportunities

def generate_test_content_plans(opportunity_ids: List[str] = None, count: int = 2) -> List[Dict[str, Any]]:
    """Generate test content plans."""
    if opportunity_ids is None:
        opportunity_ids = [f"opportunity_{i}" for i in range(count)]
    
    content_plans = []
    
    content_types = ["educational", "tutorial", "entertainment", "review", "news"]
    styles = ["modern", "minimalist", "professional", "creative", "cinematic"]
    voice_styles = ["energetic", "calm", "professional", "casual", "authoritative"]
    music_types = ["upbeat", "calm", "cinematic", "none", "subtle"]
    
    for i in range(count):
        plan_id = f"test_content_plan_{uuid.uuid4().hex[:8]}"
        opportunity_id = opportunity_ids[i % len(opportunity_ids)]
        
        content_plan = {
            "id": plan_id,
            "opportunity_id": opportunity_id,
            "content_type": random.choice(content_types),
            "script": {
                "hook": f"Test hook for content plan {i+1} - grab attention immediately!",
                "main_content": f"This is the main educational content for plan {i+1}. It provides valuable information and actionable insights that viewers can implement right away.",
                "cta": f"If this helped you with plan {i+1}, subscribe and hit the notification bell!"
            },
            "visual_plan": {
                "style": random.choice(styles),
                "scenes": [f"scene_{j}" for j in range(random.randint(3, 6))],
                "text_overlays": [f"overlay_{j}" for j in range(random.randint(2, 5))]
            },
            "audio_plan": {
                "voice_style": random.choice(voice_styles),
                "background_music": random.choice(music_types),
                "sound_effects": [f"effect_{j}" for j in range(random.randint(0, 4))]
            },
            "platform_optimization": {
                "title": f"Test Content Plan {i+1} - Ultimate Guide",
                "description": f"Complete guide for test content plan {i+1} with step-by-step instructions",
                "hashtags": [f"#tag{j}" for j in range(random.randint(3, 8))],
                "thumbnail_concept": f"Eye-catching design for plan {i+1}"
            },
            "production_estimate": {
                "time_minutes": random.randint(15, 120),
                "cost_baht": round(random.uniform(10.0, 80.0), 2),
                "complexity": random.choice(["low", "medium", "high"])
            },
            "created_at": (datetime.utcnow() - timedelta(hours=random.randint(0, 24))).isoformat()
        }
        content_plans.append(content_plan)
    
    return content_plans

def generate_test_upload_results(content_ids: List[str] = None, count: int = 2) -> List[Dict[str, Any]]:
    """Generate test upload results."""
    if content_ids is None:
        content_ids = [f"content_{i}" for i in range(count)]
    
    platforms = ["youtube", "tiktok", "instagram", "facebook"]
    statuses = ["success", "error", "pending", "processing"]
    
    upload_results = []
    
    for i in range(count):
        content_id = content_ids[i % len(content_ids)]
        platform = random.choice(platforms)
        status = random.choice(statuses)
        
        result = {
            "id": f"upload_{uuid.uuid4().hex[:8]}",
            "content_id": content_id,
            "platform": platform,
            "status": status,
            "platform_id": f"{platform}_{uuid.uuid4().hex[:8]}" if status == "success" else None,
            "url": f"https://{platform}.com/video/{uuid.uuid4().hex[:8]}" if status == "success" else None,
            "uploaded_at": datetime.utcnow().isoformat() if status in ["success", "error"] else None,
            "metadata": {
                "title": f"Test Upload {i+1}",
                "description": f"Description for test upload {i+1}",
                "tags": [f"tag{j}" for j in range(3)],
                "privacy": "public"
            }
        }
        
        if status == "error":
            result["error"] = f"Test error message for upload {i+1}"
        
        upload_results.append(result)
    
    return upload_results

class TestDataFactory:
    """Factory class for creating various test data objects."""
    
    @staticmethod
    def create_trend(
        topic: str = "Test AI Trend",
        popularity_score: float = 75.0,
        source: str = "youtube",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a single trend object with custom parameters."""
        default_trend = {
            "id": f"trend_{uuid.uuid4().hex[:8]}",
            "topic": topic,
            "source": source,
            "popularity_score": popularity_score,
            "growth_rate": popularity_score / 5,  # Rough correlation
            "category": "Technology",
            "region": "Global",
            "keywords": topic.lower().split(),
            "collected_at": datetime.utcnow().isoformat(),
            "raw_data": {
                "search_volume": int(popularity_score * 1000),
                "competition": "medium"
            }
        }
        
        # Override with any provided kwargs
        default_trend.update(kwargs)
        return default_trend
    
    @staticmethod
    def create_opportunity(
        trend_id: str = "test_trend",
        suggested_angle: str = "Test Content Angle",
        estimated_roi: float = 3.5,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a single opportunity object with custom parameters."""
        default_opportunity = {
            "id": f"opportunity_{uuid.uuid4().hex[:8]}",
            "trend_id": trend_id,
            "suggested_angle": suggested_angle,
            "estimated_views": int(estimated_roi * 10000),
            "competition_level": "medium",
            "production_cost": 25.0,
            "estimated_roi": estimated_roi,
            "priority_score": estimated_roi + 2.0,
            "status": "pending",
            "content_type": "educational",
            "target_platforms": ["youtube", "tiktok"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        default_opportunity.update(kwargs)
        return default_opportunity
    
    @staticmethod
    def create_content_plan(
        opportunity_id: str = "test_opportunity",
        content_type: str = "educational",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a single content plan object with custom parameters."""
        default_plan = {
            "id": f"plan_{uuid.uuid4().hex[:8]}",
            "opportunity_id": opportunity_id,
            "content_type": content_type,
            "script": {
                "hook": "Engaging test hook",
                "main_content": "Informative test content",
                "cta": "Test call to action"
            },
            "visual_plan": {
                "style": "modern",
                "scenes": ["intro", "main", "outro"],
                "text_overlays": ["Test Title"]
            },
            "audio_plan": {
                "voice_style": "professional",
                "background_music": "subtle",
                "sound_effects": ["transition"]
            },
            "platform_optimization": {
                "title": "Test Content Title",
                "description": "Test content description",
                "hashtags": ["#test", "#content"],
                "thumbnail_concept": "Test thumbnail"
            },
            "production_estimate": {
                "time_minutes": 30,
                "cost_baht": 20.0,
                "complexity": "medium"
            },
            "created_at": datetime.utcnow().isoformat()
        }
        
        default_plan.update(kwargs)
        return default_plan

# Predefined test datasets
TEST_TRENDS = generate_test_trends(10)
TEST_OPPORTUNITIES = generate_test_opportunities(
    trend_ids=[t["id"] for t in TEST_TRENDS[:5]], 
    count=8
)
TEST_CONTENT_PLANS = generate_test_content_plans(
    opportunity_ids=[o["id"] for o in TEST_OPPORTUNITIES[:3]], 
    count=5
)

# Helper functions for test assertions
def validate_trend_structure(trend: Dict[str, Any]) -> bool:
    """Validate trend data structure."""
    required_fields = [
        "id", "topic", "source", "popularity_score", 
        "growth_rate", "category", "keywords", "collected_at"
    ]
    return all(field in trend for field in required_fields)

def validate_opportunity_structure(opportunity: Dict[str, Any]) -> bool:
    """Validate opportunity data structure."""
    required_fields = [
        "id", "trend_id", "suggested_angle", "estimated_views",
        "competition_level", "production_cost", "estimated_roi",
        "priority_score", "status", "content_type", "target_platforms"
    ]
    return all(field in opportunity for field in required_fields)

def validate_content_plan_structure(plan: Dict[str, Any]) -> bool:
    """Validate content plan data structure."""
    required_fields = ["id", "content_type", "script", "visual_plan", "audio_plan"]
    script_fields = ["hook", "main_content", "cta"]
    
    if not all(field in plan for field in required_fields):
        return False
    
    if not all(field in plan["script"] for field in script_fields):
        return False
    
    return True

# Utility functions for test cleanup
def cleanup_test_files():
    """Clean up any temporary test files."""
    import glob
    import os
    
    # Clean up temporary files
    temp_patterns = [
        "/tmp/test_*",
        "/tmp/mock_*", 
        "test_*.tmp",
        "mock_*.tmp"
    ]
    
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
            except OSError:
                pass

def reset_test_database():
    """Reset test database to clean state."""
    # This would implement database reset logic
    pass

# Export commonly used items
__all__ = [
    'load_json_fixture',
    'save_json_fixture', 
    'get_fixture_path',
    'generate_test_trends',
    'generate_test_opportunities',
    'generate_test_content_plans',
    'generate_test_upload_results',
    'TestDataFactory',
    'TEST_TRENDS',
    'TEST_OPPORTUNITIES', 
    'TEST_CONTENT_PLANS',
    'validate_trend_structure',
    'validate_opportunity_structure',
    'validate_content_plan_structure',
    'cleanup_test_files',
    'reset_test_database'
]