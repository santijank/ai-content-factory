# Content Engine API Documentation

## 📋 Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Core Endpoints](#core-endpoints)
- [AI Service Management](#ai-service-management)
- [Content Generation](#content-generation)
- [Quality Management](#quality-management)
- [Templates & Customization](#templates--customization)
- [Batch Operations](#batch-operations)
- [Performance & Monitoring](#performance--monitoring)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The Content Engine API is the heart of AI Content Factory's content generation capabilities. It orchestrates multiple AI services to create high-quality, multi-modal content including text, images, audio, and video. The API supports various quality tiers, customization options, and batch processing for efficient content production.

### Key Features
- **Multi-Modal Generation**: Text, image, audio, and video creation
- **AI Service Orchestration**: Seamless integration with multiple AI providers
- **Quality Tiers**: Budget, balanced, and premium quality options
- **Template System**: Reusable content templates and customization
- **Batch Processing**: Efficient bulk content generation
- **Real-time Monitoring**: Generation progress and performance tracking

## Authentication

All API requests require authentication using JWT tokens.

### Getting a Token
```http
POST /auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

### Using the Token
Include the token in the Authorization header:
```http
Authorization: Bearer <your_jwt_token>
```

## Base URL

- **Development**: `http://localhost:8002`
- **Staging**: `https://staging-api.ai-content-factory.com/content-engine`
- **Production**: `https://api.ai-content-factory.com/content-engine`

## Core Endpoints

### Health Check

#### GET /health
Check service health and AI service availability.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-09-15T10:30:00Z",
  "version": "1.0.0",
  "ai_services": {
    "text_generation": {
      "groq": "healthy",
      "openai": "healthy", 
      "claude": "healthy"
    },
    "image_generation": {
      "stable_diffusion": "healthy",
      "leonardo": "healthy",
      "midjourney": "healthy"
    },
    "audio_generation": {
      "gtts": "healthy",
      "azure_tts": "healthy",
      "elevenlabs": "healthy"
    }
  },
  "current_load": {
    "active_generations": 3,
    "queue_size": 7,
    "average_wait_time": "45s"
  }
}
```

### Service Configuration

#### GET /config
Get current service configuration and available AI models.

**Response:**
```json
{
  "current_tier": "balanced",
  "available_tiers": ["budget", "balanced", "premium"],
  "ai_services": {
    "text_generation": {
      "active_service": "openai",
      "available_services": ["groq", "openai", "claude"],
      "models": {
        "groq": "mixtral-8x7b-32768",
        "openai": "gpt-4-turbo-preview",
        "claude": "claude-3-opus-20240229"
      }
    },
    "image_generation": {
      "active_service": "leonardo",
      "available_services": ["stable_diffusion", "leonardo", "midjourney"]
    },
    "audio_generation": {
      "active_service": "azure_tts",
      "available_services": ["gtts", "azure_tts", "elevenlabs"]
    }
  },
  "limits": {
    "max_concurrent_generations": 5,
    "max_queue_size": 50,
    "max_content_length": 10000,
    "max_generation_time": 600
  }
}
```

#### PUT /config
Update service configuration.

**Request:**
```json
{
  "quality_tier": "premium",
  "ai_services": {
    "text_generation": "claude",
    "image_generation": "midjourney",
    "audio_generation": "elevenlabs"
  },
  "limits": {
    "max_concurrent_generations": 3
  }
}
```

## AI Service Management

### Service Status

#### GET /ai/status
Get detailed status of all AI services.

**Response:**
```json
{
  "services": {
    "text_generation": {
      "groq": {
        "status": "healthy",
        "response_time_ms": 1250,
        "success_rate": 98.5,
        "requests_today": 1247,
        "quota_remaining": 8753
      },
      "openai": {
        "status": "healthy",
        "response_time_ms": 2100,
        "success_rate": 99.2,
        "requests_today": 856,
        "quota_remaining": "unlimited"
      }
    }
  },
  "overall_health": "healthy",
  "recommendations": [
    "Consider using Groq for faster response times",
    "OpenAI showing excellent reliability"
  ]
}
```

#### POST /ai/test/{service_type}
Test specific AI service functionality.

**Path Parameters:**
- `service_type`: text, image, or audio

**Request:**
```json
{
  "service": "openai",
  "test_prompt": "Generate a brief test response"
}
```

**Response:**
```json
{
  "test_id": "test_123456789",
  "service": "openai",
  "status": "success",
  "response_time_ms": 1847,
  "test_output": "This is a test response from OpenAI GPT-4.",
  "quality_score": 9.2,
  "recommendations": []
}
```

### Service Switching

#### POST /ai/switch
Switch AI service for specific generation type.

**Request:**
```json
{
  "service_type": "text_generation",
  "target_service": "claude",
  "reason": "Better quality for creative content"
}
```

## Content Generation

### Single Content Generation

#### POST /generate
Generate single piece of content from opportunity or custom brief.

**Request:**
```json
{
  "opportunity_id": "opp_123456789",
  "customization": {
    "content_type": "educational_video",
    "target_length": "3-5 minutes",
    "tone": "professional",
    "style": "minimalist"
  },
  "quality_tier": "balanced",
  "priority": "normal"
}
```

**Response:**
```json
{
  "generation_id": "gen_123456789",
  "status": "started",
  "estimated_completion": "2024-09-15T10:35:00Z",
  "queue_position": 2,
  "content_plan": {
    "content_type": "educational_video",
    "script_length": 450,
    "scene_count": 5,
    "estimated_duration": "4:15"
  },
  "estimated_cost": 0.25
}
```

#### POST /generate/custom
Generate content from custom brief (not from opportunity).

**Request:**
```json
{
  "brief": {
    "topic": "AI in Healthcare",
    "target_audience": "healthcare professionals",
    "key_points": [
      "AI diagnostic tools",
      "Patient data privacy",
      "Implementation challenges"
    ],
    "call_to_action": "Schedule a consultation"
  },
  "content_specs": {
    "type": "explainer_video",
    "duration": "2-3 minutes",
    "style": "professional",
    "include_slides": true
  },
  "quality_tier": "premium"
}
```

### Generation Status & Results

#### GET /generate/{generation_id}
Get generation status and progress.

**Response:**
```json
{
  "generation_id": "gen_123456789",
  "status": "in_progress",
  "progress": {
    "overall_progress": 65,
    "current_stage": "image_generation",
    "stages": {
      "script_generation": "completed",
      "image_generation": "in_progress",
      "audio_generation": "pending",
      "video_assembly": "pending"
    }
  },
  "estimated_completion": "2024-09-15T10:40:00Z",
  "generation_details": {
    "script": {
      "word_count": 285,
      "estimated_reading_time": "1:30"
    },
    "images": {
      "total_required": 5,
      "completed": 3,
      "current_generation": "Scene 4: Healthcare dashboard"
    }
  }
}
```

#### GET /generate/{generation_id}/result
Get completed generation result.

**Response:**
```json
{
  "generation_id": "gen_123456789",
  "status": "completed",
  "content_item_id": "content_987654321",
  "result": {
    "script": {
      "full_text": "Welcome to our guide on AI in Healthcare...",
      "scenes": [
        {
          "scene_number": 1,
          "text": "Welcome to our guide on AI in Healthcare",
          "duration": "3s",
          "visual_description": "Title slide with medical AI imagery"
        }
      ],
      "word_count": 285,
      "estimated_reading_time": "1:30"
    },
    "visuals": {
      "images": [
        {
          "scene_number": 1,
          "image_url": "/uploads/gen_123456789/scene_1.png",
          "description": "Title slide with medical AI imagery",
          "style": "professional_minimalist"
        }
      ],
      "video_preview": "/uploads/gen_123456789/preview.mp4"
    },
    "audio": {
      "voice_track": "/uploads/gen_123456789/voice.mp3",
      "background_music": "/uploads/gen_123456789/background.mp3",
      "voice_style": "professional_female",
      "duration": "4:15"
    },
    "final_video": {
      "video_url": "/uploads/gen_123456789/final_video.mp4",
      "thumbnail_url": "/uploads/gen_123456789/thumbnail.jpg",
      "duration": "4:15",
      "file_size_mb": 15.8,
      "resolution": "1920x1080"
    }
  },
  "metadata": {
    "generation_time": "4m 23s",
    "total_cost": 0.25,
    "quality_score": 8.7,
    "ai_services_used": {
      "text": "openai_gpt4",
      "image": "leonardo_ai",
      "audio": "azure_tts"
    }
  },
  "platform_optimization": {
    "youtube": {
      "optimized_title": "AI in Healthcare: Complete Guide for Professionals",
      "description": "Comprehensive guide covering AI diagnostic tools...",
      "tags": ["AI", "Healthcare", "Medical Technology"],
      "thumbnail": "/uploads/gen_123456789/youtube_thumbnail.jpg"
    },
    "tiktok": {
      "vertical_video": "/uploads/gen_123456789/tiktok_vertical.mp4",
      "hashtags": ["#AIHealthcare", "#MedTech", "#Innovation"]
    }
  }
}
```

#### DELETE /generate/{generation_id}
Cancel ongoing generation.

**Response:**
```json
{
  "generation_id": "gen_123456789",
  "status": "cancelled",
  "message": "Generation cancelled successfully",
  "refund_amount": 0.15,
  "partial_results": {
    "script_completed": true,
    "images_completed": 2,
    "audio_completed": false
  }
}
```

## Quality Management

### Quality Tiers

#### GET /quality/tiers
Get available quality tiers and their specifications.

**Response:**
```json
{
  "tiers": {
    "budget": {
      "cost_per_generation": 0.05,
      "ai_services": {
        "text": "groq_mixtral",
        "image": "stable_diffusion_local",
        "audio": "google_tts"
      },
      "features": {
        "response_time": "fast",
        "quality_level": "basic",
        "customization": "limited"
      },
      "typical_generation_time": "2-3 minutes",
      "suitable_for": ["high_volume", "basic_content", "testing"]
    },
    "balanced": {
      "cost_per_generation": 0.25,
      "ai_services": {
        "text": "openai_gpt4",
        "image": "leonardo_ai", 
        "audio": "azure_tts"
      },
      "features": {
        "response_time": "moderate",
        "quality_level": "high",
        "customization": "extensive"
      },
      "typical_generation_time": "5-7 minutes",
      "suitable_for": ["regular_content", "business_use", "social_media"]
    },
    "premium": {
      "cost_per_generation": 1.50,
      "ai_services": {
        "text": "claude_opus",
        "image": "midjourney_v6",
        "audio": "elevenlabs_premium"
      },
      "features": {
        "response_time": "slower",
        "quality_level": "exceptional",
        "customization": "full"
      },
      "typical_generation_time": "10-15 minutes",
      "suitable_for": ["viral_content", "premium_brands", "marketing_campaigns"]
    }
  },
  "tier_comparison": {
    "text_quality": {
      "budget": 6.5,
      "balanced": 8.5,
      "premium": 9.5
    },
    "image_quality": {
      "budget": 6.0,
      "balanced": 8.0,
      "premium": 9.8
    },
    "audio_quality": {
      "budget": 5.5,
      "balanced": 8.2,
      "premium": 9.7
    }
  }
}
```

#### POST /quality/analyze
Analyze content quality and get improvement suggestions.

**Request:**
```json
{
  "content_item_id": "content_987654321",
  "analysis_type": "comprehensive"
}
```

**Response:**
```json
{
  "content_item_id": "content_987654321",
  "quality_scores": {
    "overall": 8.7,
    "script_quality": 9.2,
    "visual_appeal": 8.5,
    "audio_clarity": 8.9,
    "engagement_potential": 8.3
  },
  "strengths": [
    "Excellent script flow and narrative structure",
    "High-quality voice synthesis",
    "Professional visual design"
  ],
  "improvements": [
    "Consider more dynamic transitions",
    "Add more visual variety in scenes 3-4",
    "Enhance call-to-action visibility"
  ],
  "tier_recommendations": {
    "current_tier": "balanced",
    "suggested_upgrade": "premium",
    "upgrade_benefits": [
      "20% better image quality",
      "More natural voice synthesis", 
      "Advanced transition effects"
    ],
    "cost_difference": 1.25
  }
}
```

## Templates & Customization

### Template Management

#### GET /templates
Get available content templates.

**Query Parameters:**
- `category` (optional): Filter by category
- `content_type` (optional): Filter by content type
- `quality_tier` (optional): Filter by quality tier

**Response:**
```json
{
  "templates": [
    {
      "template_id": "template_educational_001",
      "name": "Educational Explainer",
      "description": "Perfect for educational content with clear structure",
      "category": "education",
      "content_type": "explainer_video",
      "preview_url": "/templates/educational_001/preview.mp4",
      "usage_count": 1247,
      "rating": 4.8,
      "structure": {
        "intro_duration": "10s",
        "main_content": "3-4 minutes",
        "conclusion": "15s",
        "scene_count": "5-7"
      },
      "customizable_elements": [
        "color_scheme",
        "typography",
        "transition_style",
        "background_music"
      ]
    }
  ],
  "categories": ["education", "marketing", "entertainment", "news", "tutorial"],
  "total_templates": 45
}
```

#### GET /templates/{template_id}
Get detailed template information.

**Response:**
```json
{
  "template_id": "template_educational_001",
  "name": "Educational Explainer",
  "description": "Perfect for educational content with clear structure",
  "version": "2.1",
  "last_updated": "2024-09-10T14:30:00Z",
  "structure": {
    "scenes": [
      {
        "scene_number": 1,
        "type": "title_slide",
        "duration": "3s",
        "elements": ["title", "subtitle", "logo"],
        "transition": "fade_in"
      },
      {
        "scene_number": 2,
        "type": "problem_introduction",
        "duration": "30s",
        "elements": ["text_overlay", "background_image", "icon"],
        "transition": "slide_left"
      }
    ]
  },
  "customization_options": {
    "color_schemes": [
      {"name": "professional_blue", "primary": "#2E86AB", "secondary": "#A23B72"},
      {"name": "warm_orange", "primary": "#F18F01", "secondary": "#C73E1D"}
    ],
    "typography": [
      {"name": "modern_sans", "font_family": "Inter"},
      {"name": "classic_serif", "font_family": "Merriweather"}
    ],
    "voice_styles": ["professional", "friendly", "authoritative"],
    "background_music": ["upbeat", "calm", "corporate", "none"]
  },
  "requirements": {
    "min_script_length": 200,
    "max_script_length": 1000,
    "recommended_scene_count": 6,
    "quality_tier": "balanced"
  }
}
```

#### POST /templates/{template_id}/generate
Generate content using specific template.

**Request:**
```json
{
  "template_id": "template_educational_001",
  "content_brief": {
    "topic": "Machine Learning Basics",
    "key_points": [
      "What is machine learning",
      "Types of ML algorithms",
      "Real-world applications"
    ],
    "target_audience": "beginners"
  },
  "customization": {
    "color_scheme": "professional_blue",
    "typography": "modern_sans",
    "voice_style": "friendly",
    "background_music": "upbeat"
  }
}
```

### Custom Templates

#### POST /templates
Create custom template from existing content.

**Request:**
```json
{
  "name": "My Custom Template",
  "description": "Template based on high-performing content",
  "base_content_id": "content_987654321",
  "customizable_elements": [
    "color_scheme",
    "voice_style",
    "background_music"
  ],
  "category": "marketing",
  "public": false
}
```

## Batch Operations

### Batch Generation

#### POST /generate/batch
Generate multiple content pieces simultaneously.

**Request:**
```json
{
  "batch_name": "Weekly Content Batch",
  "generations": [
    {
      "opportunity_id": "opp_001",
      "quality_tier": "balanced",
      "customization": {
        "style": "professional"
      }
    },
    {
      "opportunity_id": "opp_002",
      "quality_tier": "premium",
      "template_id": "template_marketing_001"
    },
    {
      "custom_brief": {
        "topic": "Product Launch Announcement",
        "content_type": "promotional_video"
      },
      "quality_tier": "premium"
    }
  ],
  "batch_settings": {
    "priority": "normal",
    "parallel_processing": true,
    "max_concurrent": 3,
    "notification_webhook": "https://your-app.com/webhook/batch-complete"
  }
}
```

**Response:**
```json
{
  "batch_id": "batch_123456789",
  "status": "started",
  "total_generations": 3,
  "estimated_completion": "2024-09-15T11:15:00Z",
  "estimated_total_cost": 2.00,
  "generations": [
    {
      "generation_id": "gen_001",
      "opportunity_id": "opp_001",
      "status": "queued",
      "queue_position": 1
    },
    {
      "generation_id": "gen_002", 
      "opportunity_id": "opp_002",
      "status": "queued",
      "queue_position": 2
    },
    {
      "generation_id": "gen_003",
      "custom_brief": true,
      "status": "queued",
      "queue_position": 3
    }
  ]
}
```

#### GET /generate/batch/{batch_id}
Get batch generation status and progress.

**Response:**
```json
{
  "batch_id": "batch_123456789",
  "status": "in_progress",
  "progress": {
    "completed": 1,
    "in_progress": 2,
    "pending": 0,
    "failed": 0,
    "overall_progress": 67
  },
  "started_at": "2024-09-15T10:30:00Z",
  "estimated_completion": "2024-09-15T11:10:00Z",
  "generations": [
    {
      "generation_id": "gen_001",
      "status": "completed",
      "content_item_id": "content_001",
      "completion_time": "4m 23s",
      "cost": 0.25
    },
    {
      "generation_id": "gen_002",
      "status": "in_progress",
      "progress": 45,
      "current_stage": "image_generation"
    },
    {
      "generation_id": "gen_003",
      "status": "in_progress", 
      "progress": 78,
      "current_stage": "video_assembly"
    }
  ],
  "total_cost": 0.75,
  "performance_stats": {
    "average_generation_time": "4m 12s",
    "success_rate": 100,
    "quality_scores": {
      "average": 8.6,
      "range": "8.2 - 9.1"
    }
  }
}
```

### Batch Templates

#### POST /generate/batch/template
Generate multiple content pieces using the same template with different data.

**Request:**
```json
{
  "template_id": "template_product_showcase_001",
  "batch_data": [
    {
      "product_name": "Smart Fitness Tracker",
      "key_features": ["heart rate monitoring", "sleep tracking", "waterproof"],
      "price": "$199",
      "target_audience": "fitness enthusiasts"
    },
    {
      "product_name": "Wireless Earbuds Pro",
      "key_features": ["noise cancellation", "30h battery", "premium sound"],
      "price": "$299", 
      "target_audience": "music lovers"
    }
  ],
  "global_customization": {
    "brand_colors": {"primary": "#007bff", "secondary": "#6c757d"},
    "voice_style": "enthusiastic",
    "quality_tier": "premium"
  }
}
```

## Performance & Monitoring

### Generation Analytics

#### GET /analytics/performance
Get content generation performance analytics.

**Query Parameters:**
- `timeframe` (optional): 1h, 24h, 7d, 30d (default: 24h)
- `quality_tier` (optional): Filter by quality tier
- `content_type` (optional): Filter by content type

**Response:**
```json
{
  "timeframe": "24h",
  "overview": {
    "total_generations": 156,
    "successful_generations": 152,
    "failed_generations": 4,
    "success_rate": 97.4,
    "average_generation_time": "5m 23s",
    "total_cost": 38.75
  },
  "performance_by_tier": {
    "budget": {
      "count": 89,
      "success_rate": 98.9,
      "avg_time": "2m 45s",
      "avg_quality_score": 6.8
    },
    "balanced": {
      "count": 52,
      "success_rate": 96.2,
      "avg_time": "6m 12s",
      "avg_quality_score": 8.4
    },
    "premium": {
      "count": 15,
      "success_rate": 93.3,
      "avg_time": "12m 8s",
      "avg_quality_score": 9.2
    }
  },
  "ai_service_performance": {
    "text_generation": {
      "groq": {"usage": 89, "avg_time": "1.2s", "success_rate": 99.1},
      "openai": {"usage": 52, "avg_time": "2.8s", "success_rate": 97.3},
      "claude": {"usage": 15, "avg_time": "4.1s", "success_rate": 93.3}
    },
    "image_generation": {
      "stable_diffusion": {"usage": 89, "avg_time": "45s", "success_rate": 98.9},
      "leonardo": {"usage": 52, "avg_time": "78s", "success_rate": 96.2},
      "midjourney": {"usage": 15, "avg_time": "125s", "success_rate": 93.3}
    }
  },
  "content_type_breakdown": {
    "explainer_video": 67,
    "promotional_video": 34,
    "educational_content": 28,
    "social_media_post": 27
  },
  "quality_trends": {
    "overall_quality_improvement": 5.2,
    "user_satisfaction": 4.6,
    "repeat_usage_rate": 78.3
  }
}
```

#### GET /analytics/costs
Get detailed cost analytics and breakdown.

**Response:**
```json
{
  "cost_summary": {
    "total_cost_today": 12.75,
    "total_cost_this_month": 387.50,
    "average_cost_per_generation": 0.28,
    "cost_by_tier": {
      "budget": 4.45,
      "balanced": 13.00,
      "premium": 22.50
    }
  },
  "cost_breakdown": {
    "ai_services": {
      "text_generation": 8.20,
      "image_generation": 18.90,
      "audio_generation": 11.40
    },
    "infrastructure": 2.15,
    "storage": 0.85
  },
  "optimization_suggestions": [
    "Consider using Budget tier for simple content to reduce costs by 80%",
    "Batch processing can reduce costs by up to 15%",
    "Template reuse can save 25% on generation time"
  ],
  "projected_monthly_cost": 465.00
}
```

### Queue Management

#### GET /queue/status
Get current generation queue status.

**Response:**
```json
{
  "queue_stats": {
    "total_items": 12,
    "processing": 3,
    "waiting": 9,
    "average_wait_time": "3m 45s",
    "estimated_queue_clear_time": "2024-09-15T10:45:00Z"
  },
  "processing_capacity": {
    "max_concurrent": 5,
    "current_utilization": 60,
    "available_slots": 2
  },
  "queue_items": [
    {
      "generation_id": "gen_active_001",
      "status": "processing",
      "progress": 78,
      "estimated_completion": "2024-09-15T10:35:00Z",
      "quality_tier": "premium"
    },
    {
      "generation_id": "gen_waiting_001",
      "status": "waiting",
      "queue_position": 1,
      "estimated_start": "2024-09-15T10:35:00Z",
      "quality_tier": "balanced"
    }
  ],
  "priority_breakdown": {
    "urgent": 2,
    "high": 4,
    "normal": 5,
    "low": 1
  }
}
```

#### POST /queue/priority
Modify generation priority.

**Request:**
```json
{
  "generation_id": "gen_123456789",
  "new_priority": "urgent",
  "reason": "Client deadline moved up"
}
```

## Data Models

### Content Plan Object
```json
{
  "content_plan_id": "plan_123456789",
  "content_type": "explainer_video",
  "structure": {
    "total_duration": "4:15",
    "scene_count": 5,
    "script_word_count": 285
  },
  "script": {
    "hook": "Did you know AI is revolutionizing healthcare?",
    "main_content": "...",
    "call_to_action": "Learn more at our website"
  },
  "visual_plan": {
    "style": "professional_minimalist",
    "color_scheme": {"primary": "#2E86AB", "secondary": "#A23B72"},
    "scenes": [
      {
        "scene_number": 1,
        "description": "Title slide with medical AI imagery",
        "duration": "3s",
        "elements": ["title", "subtitle", "background"]
      }
    ]
  },
  "audio_plan": {
    "voice_style": "professional_female",
    "speaking_pace": "moderate",
    "background_music": "subtle_corporate",
    "sound_effects": ["transition_whoosh", "notification_ping"]
  },
  "platform_optimization": {
    "youtube": {
      "title": "AI in Healthcare: Complete Professional Guide",
      "description": "Comprehensive guide covering...",
      "tags": ["AI", "Healthcare", "Medical Technology"],
      "thumbnail_concept": "Split screen: doctor and AI interface"
    },
    "tiktok": {
      "format": "vertical_video",
      "hook_duration": "2s",
      "hashtags": ["#AIHealthcare", "#MedTech", "#Innovation"]
    }
  }
}
```

### Generation Status Object
```json
{
  "generation_id": "gen_123456789",
  "status": "in_progress",
  "priority": "normal",
  "quality_tier": "balanced",
  "progress": {
    "overall_progress": 65,
    "current_stage": "image_generation",
    "stages": {
      "planning": "completed",
      "script_generation": "completed", 
      "image_generation": "in_progress",
      "audio_generation": "pending",
      "video_assembly": "pending",
      "optimization": "pending"
    }
  },
  "timing": {
    "created_at": "2024-09-15T10:30:00Z",
    "started_at": "2024-09-15T10:31:15Z",
    "estimated_completion": "2024-09-15T10:40:00Z",
    "actual_completion": null
  },
  "costs": {
    "estimated_cost": 0.25,
    "actual_cost": 0.15,
    "cost_breakdown": {
      "text_generation": 0.05,
      "image_generation": 0.08,
      "audio_generation": 0.02
    }
  },
  "metadata": {
    "user_id": "user_123",
    "opportunity_id": "opp_456",
    "template_id": null,
    "ai_services_used": {
      "text": "openai_gpt4",
      "image": "leonardo_ai",
      "audio": "azure_tts"
    }
  }
}
```

### Content Result Object
```json
{
  "generation_id": "gen_123456789",
  "content_item_id": "content_987654321",
  "status": "completed",
  "quality_score": 8.7,
  "assets": {
    "script": {
      "full_text": "Complete script content...",
      "scenes": [...],
      "word_count": 285,
      "reading_time": "1:30"
    },
    "images": [
      {
        "scene_number": 1,
        "url": "/uploads/gen_123456789/scene_1.png",
        "description": "Title slide with medical AI imagery",
        "dimensions": "1920x1080",
        "file_size_kb": 245
      }
    ],
    "audio": {
      "voice_track": "/uploads/gen_123456789/voice.mp3",
      "background_music": "/uploads/gen_123456789/background.mp3",
      "combined_audio": "/uploads/gen_123456789/final_audio.mp3",
      "duration": "4:15"
    },
    "video": {
      "final_video": "/uploads/gen_123456789/final_video.mp4",
      "preview": "/uploads/gen_123456789/preview.mp4",
      "thumbnail": "/uploads/gen_123456789/thumbnail.jpg",
      "duration": "4:15",
      "resolution": "1920x1080",
      "file_size_mb": 15.8
    }
  },
  "platform_variants": {
    "youtube": {
      "video": "/uploads/gen_123456789/youtube.mp4",
      "thumbnail": "/uploads/gen_123456789/youtube_thumb.jpg",
      "title": "AI in Healthcare: Complete Professional Guide",
      "description": "Comprehensive guide...",
      "tags": ["AI", "Healthcare"]
    },
    "tiktok": {
      "video": "/uploads/gen_123456789/tiktok.mp4",
      "format": "vertical",
      "duration": "0:58",
      "hashtags": ["#AIHealthcare", "#MedTech"]
    }
  }
}
```

## Error Handling

### HTTP Status Codes
| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Generation started successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Generation or resource not found |
| 409 | Conflict | Generation already in progress |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | AI service error |
| 503 | Service Unavailable | AI services temporarily unavailable |

### Error Response Format
```json
{
  "error": {
    "code": "GENERATION_FAILED",
    "message": "Content generation failed due to AI service error",
    "details": {
      "generation_id": "gen_123456789",
      "failed_stage": "image_generation",
      "ai_service": "leonardo_ai",
      "service_error": "API quota exceeded"
    },
    "suggestions": [
      "Try using a different quality tier",
      "Wait for quota reset in 2 hours",
      "Contact support for quota increase"
    ],
    "timestamp": "2024-09-15T10:30:00Z",
    "request_id": "req_987654321"
  }
}
```

### Common Error Codes
| Code | Description | Resolution |
|------|-------------|------------|
| INVALID_OPPORTUNITY | Opportunity ID not found | Verify opportunity exists |
| INSUFFICIENT_QUOTA | AI service quota exceeded | Wait or upgrade plan |
| GENERATION_TIMEOUT | Generation took too long | Retry with simpler content |
| INVALID_TEMPLATE | Template not compatible | Check template requirements |
| QUEUE_FULL | Generation queue at capacity | Wait or increase priority |
| QUALITY_TIER_UNAVAILABLE | Requested tier not accessible | Check subscription level |

## Rate Limiting

### Rate Limits
- **Free Tier**: 10 generations/hour, 50/day
- **Basic Plan**: 100 generations/hour, 500/day
- **Professional**: 500 generations/hour, 2000/day
- **Enterprise**: Custom limits

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1634567890
X-RateLimit-Type: generations
```

### Batch Operation Limits
- **Maximum batch size**: 50 generations
- **Concurrent batches**: 5 (Professional), 10 (Enterprise)
- **Batch timeout**: 2 hours

## Examples

### Python SDK Example
```python
import requests
import time

class ContentEngineClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def generate_content(self, opportunity_id, quality_tier='balanced'):
        """Generate content from opportunity"""
        response = requests.post(
            f'{self.base_url}/generate',
            headers=self.headers,
            json={
                'opportunity_id': opportunity_id,
                'quality_tier': quality_tier
            }
        )
        return response.json()
    
    def wait_for_completion(self, generation_id, timeout=600):
        """Wait for generation to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f'{self.base_url}/generate/{generation_id}',
                headers=self.headers
            )
            status = response.json()
            
            if status['status'] == 'completed':
                return self.get_result(generation_id)
            elif status['status'] == 'failed':
                raise Exception(f"Generation failed: {status.get('error')}")
            
            time.sleep(10)
        
        raise TimeoutError("Generation timeout")
    
    def get_result(self, generation_id):
        """Get completed generation result"""
        response = requests.get(
            f'{self.base_url}/generate/{generation_id}/result',
            headers=self.headers
        )
        return response.json()

# Usage
client = ContentEngineClient('http://localhost:8002', 'your_token')

# Start generation
generation = client.generate_content('opp_123456', 'premium')
print(f"Generation started: {generation['generation_id']}")

# Wait for completion
result = client.wait_for_completion(generation['generation_id'])
print(f"Content generated: {result['assets']['video']['final_video']}")
```

### JavaScript Example
```javascript
class ContentEngineAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async generateContent(opportunityId, qualityTier = 'balanced') {
        const response = await fetch(`${this.baseUrl}/generate`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                opportunity_id: opportunityId,
                quality_tier: qualityTier
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }

    async pollGenerationStatus(generationId, onProgress) {
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const response = await fetch(
                        `${this.baseUrl}/generate/${generationId}`,
                        { headers: this.headers }
                    );
                    
                    const status = await response.json();
                    
                    if (onProgress) {
                        onProgress(status);
                    }
                    
                    switch (status.status) {
                        case 'completed':
                            const result = await this.getResult(generationId);
                            resolve(result);
                            break;
                        case 'failed':
                            reject(new Error(status.error?.message || 'Generation failed'));
                            break;
                        default:
                            setTimeout(poll, 5000); // Poll every 5 seconds
                    }
                } catch (error) {
                    reject(error);
                }
            };
            
            poll();
        });
    }

    async getResult(generationId) {
        const response = await fetch(
            `${this.baseUrl}/generate/${generationId}/result`,
            { headers: this.headers }
        );
        
        return await response.json();
    }

    async batchGenerate(generations) {
        const response = await fetch(`${this.baseUrl}/generate/batch`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                generations: generations,
                batch_settings: {
                    parallel_processing: true,
                    max_concurrent: 3
                }
            })
        });
        
        return await response.json();
    }
}

// Usage
const api = new ContentEngineAPI('http://localhost:8002', 'your_token');

// Generate single content with progress tracking
api.generateContent('opp_123456', 'premium')
    .then(generation => {
        console.log('Generation started:', generation.generation_id);
        
        return api.pollGenerationStatus(
            generation.generation_id,
            (status) => {
                console.log(`Progress: ${status.progress.overall_progress}%`);
            }
        );
    })
    .then(result => {
        console.log('Content ready:', result.assets.video.final_video);
    })
    .catch(error => {
        console.error('Generation failed:', error);
    });

// Batch generation
const batchGenerations = [
    { opportunity_id: 'opp_001', quality_tier: 'balanced' },
    { opportunity_id: 'opp_002', quality_tier: 'premium' }
];

api.batchGenerate(batchGenerations)
    .then(batch => {
        console.log('Batch started:', batch.batch_id);
    });
```

### cURL Examples
```bash
# Generate content from opportunity
curl -X POST http://localhost:8002/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_id": "opp_123456789",
    "quality_tier": "balanced",
    "customization": {
      "style": "professional"
    }
  }'

# Check generation status
curl -X GET http://localhost:8002/generate/gen_123456789 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get completed result
curl -X GET http://localhost:8002/generate/gen_123456789/result \
  -H "Authorization: Bearer YOUR_TOKEN"

# Batch generation
curl -X POST http://localhost:8002/generate/batch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "generations": [
      {"opportunity_id": "opp_001", "quality_tier": "balanced"},
      {"opportunity_id": "opp_002", "quality_tier": "premium"}
    ],
    "batch_settings": {
      "parallel_processing": true
    }
  }'

# Get service health
curl -X GET http://localhost:8002/health \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get performance analytics
curl -X GET "http://localhost:8002/analytics/performance?timeframe=24h" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

This Content Engine API provides powerful content generation capabilities with flexible configuration, comprehensive monitoring, and efficient batch processing. The API is designed to handle high-volume content creation while maintaining quality and performance standards.

For platform-specific upload functionality, see [Platform Manager API](platform-manager-api.md). For trend data integration, see [Trend Monitor API](trend-monitor-api.md).