### Platform Authentication

#### GET /platforms/{platform}/auth
Initiate OAuth authentication for a platform.

**Response:**
```json
{
  "platform": "youtube",
  "auth_url": "https://accounts.google.com/oauth2/auth?client_id=...",
  "state": "random_state_string",
  "expires_in": 600,
  "instructions": "Visit the auth_url to authorize the application"
}
```

#### POST /platforms/{platform}/auth/callback
Handle OAuth callback after user authorization.

**Request:**
```json
{
  "code": "oauth_authorization_code",
  "state": "random_state_string"
}
```

**Response:**
```json
{
  "platform": "youtube",
  "status": "connected",
  "message": "Successfully connected to YouTube",
  "account_info": {
    "channel_name": "AI Content Factory",
    "channel_id": "UC1234567890"
  },
  "permissions": ["upload", "read", "analytics"]
}
```

#### DELETE /platforms/{platform}/auth
Disconnect platform authentication.

**Response:**
```json
{
  "platform": "youtube",
  "status": "disconnected",
  "message": "Successfully disconnected from YouTube"
}
```

### Platform Settings

#### GET /platforms/{platform}/settings
Get platform-specific upload settings.

**Response:**
```json
{
  "platform": "youtube",
  "settings": {
    "default_privacy": "public",
    "default_category": "Science & Technology",
    "default_tags": ["AI", "Technology", "Content Creation"],
    "monetization": {
      "enabled": true,
      "ad_breaks": true,
      "mid_roll_ads": true
    },
    "seo_optimization": {
      "title_optimization": true,
      "description_enhancement": true,
      "tag_suggestions": true,
      "thumbnail_optimization": true
    },
    "upload_defaults": {
      "comments_enabled": true,
      "ratings_enabled": true,
      "notifications_enabled": true,
      "made_for_kids": false
    },
    "scheduling": {
      "optimal_times": ["14:00", "18:00", "20:00"],
      "timezone": "UTC",
      "auto_schedule": false
    }
  }
}
```

#### PUT /platforms/{platform}/settings
Update platform-specific settings.

**Request:**
```json
{
  "default_privacy": "public",
  "default_category": "Education",
  "monetization": {
    "enabled": true,
    "ad_breaks": false
  },
  "seo_optimization": {
    "title_optimization": true,
    "description_enhancement": true
  }
}
```

## Content Upload

### Single Upload

#### POST /upload
Upload content to specified platforms.

**Request:**
```json
{
  "content_item_id": "content_123456789",
  "platforms": ["youtube", "tiktok"],
  "upload_settings": {
    "youtube": {
      "title": "AI in Healthcare: Complete Professional Guide",
      "description": "Comprehensive guide covering AI diagnostic tools, patient data privacy, and implementation challenges in modern healthcare.",
      "tags": ["AI", "Healthcare", "Medical Technology", "Innovation"],
      "category": "Science & Technology",
      "privacy": "public",
      "thumbnail": "custom",
      "playlist_id": "PLxxx",
      "scheduled_publish_time": "2024-09-15T18:00:00Z"
    },
    "tiktok": {
      "description": "AI is revolutionizing healthcare! 🏥🤖 #AIHealthcare #MedTech #Innovation #TechTalk",
      "privacy": "public",
      "allows_comments": true,
      "allows_duet": true,
      "allows_stitch": true
    }
  },
  "optimization": {
    "auto_optimize": true,
    "generate_variants": true,
    "seo_enhance": true
  }
}
```

**Response:**
```json
{
  "upload_id": "upload_123456789",
  "status": "started",
  "platforms": {
    "youtube": {
      "upload_id": "yt_upload_001",
      "status": "uploading",
      "progress": 0,
      "estimated_completion": "2024-09-15T10:45:00Z"
    },
    "tiktok": {
      "upload_id": "tt_upload_001", 
      "status": "queued",
      "queue_position": 2,
      "estimated_start": "2024-09-15T10:35:00Z"
    }
  },
  "created_at": "2024-09-15T10:30:00Z",
  "estimated_total_time": "8-12 minutes"
}
```

#### GET /upload/{upload_id}
Get upload status and progress.

**Response:**
```json
{
  "upload_id": "upload_123456789",
  "overall_status": "in_progress",
  "progress": 65,
  "platforms": {
    "youtube": {
      "platform_upload_id": "yt_upload_001",
      "status": "processing",
      "progress": 85,
      "stage": "video_processing",
      "video_id": "dQw4w9WgXcQ",
      "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "upload_time": "6m 23s",
      "processing_info": {
        "hd_processing": "completed",
        "thumbnail_generation": "in_progress",
        "monetization_review": "pending"
      }
    },
    "tiktok": {
      "platform_upload_id": "tt_upload_001",
      "status": "completed",
      "progress": 100,
      "video_id": "7284756389",
      "url": "https://tiktok.com/@username/video/7284756389",
      "upload_time": "2m 45s",
      "views": 127,
      "likes": 23,
      "shares": 5
    }
  },
  "started_at": "2024-09-15T10:30:00Z",
  "completed_platforms": 1,
  "total_platforms": 2,
  "errors": [],
  "warnings": [
    "YouTube monetization review may take 24-48 hours"
  ]
}
```

### Upload with Custom Content

#### POST /upload/custom
Upload custom files directly (not from content engine).

**Request (multipart/form-data):**
```
POST /upload/custom
Content-Type: multipart/form-data

video_file: [video file]
thumbnail_file: [thumbnail file]
platforms: ["youtube", "facebook"]
metadata: {
  "title": "Custom Video Upload",
  "description": "Custom content uploaded directly",
  "tags": ["custom", "upload", "test"]
}
```

**Response:**
```json
{
  "upload_id": "upload_custom_001",
  "status": "processing",
  "file_info": {
    "video_file": {
      "filename": "custom_video.mp4",
      "size_mb": 45.7,
      "duration": "5:23",
      "resolution": "1920x1080",
      "format": "mp4"
    },
    "thumbnail_file": {
      "filename": "custom_thumb.jpg",
      "size_kb": 234,
      "resolution": "1280x720"
    }
  },
  "platforms": ["youtube", "facebook"],
  "estimated_upload_time": "8-12 minutes"
}
```

## Platform-Specific Features

### YouTube Features

#### POST /platforms/youtube/optimize
Optimize content specifically for YouTube.

**Request:**
```json
{
  "content_item_id": "content_123456789",
  "optimization_options": {
    "title_seo": true,
    "description_enhancement": true,
    "tag_research": true,
    "thumbnail_generation": true,
    "chapter_markers": true,
    "end_screen": true
  }
}
```

**Response:**
```json
{
  "optimization_id": "yt_opt_001",
  "original": {
    "title": "AI in Healthcare Guide",
    "description": "Learn about AI in healthcare...",
    "tags": ["AI", "Healthcare"]
  },
  "optimized": {
    "title": "AI in Healthcare: Complete 2024 Guide for Medical Professionals",
    "description": "🏥 Complete guide to AI in healthcare covering diagnostic tools, patient privacy, and implementation strategies. Perfect for medical professionals looking to understand AI integration.\n\n📋 Chapters:\n0:00 Introduction\n1:30 AI Diagnostic Tools\n3:45 Patient Data Privacy\n6:20 Implementation Challenges\n\n🔗 Resources: https://example.com/resources",
    "tags": ["AI Healthcare", "Medical AI", "Healthcare Technology", "Medical Innovation", "AI Diagnostics", "Healthcare AI 2024", "Medical Professionals", "Healthcare Automation"]
  },
  "seo_score": {
    "original": 6.2,
    "optimized": 8.9,
    "improvement": 2.7
  },
  "thumbnail_variants": [
    "/uploads/thumbnails/yt_opt_001_variant_1.jpg",
    "/uploads/thumbnails/yt_opt_001_variant_2.jpg",
    "/uploads/thumbnails/yt_opt_001_variant_3.jpg"
  ]
}
```

#### GET /platforms/youtube/analytics/{video_id}
Get YouTube-specific analytics for uploaded video.

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "analytics": {
    "views": 15420,
    "likes": 892,
    "dislikes": 23,
    "comments": 156,
    "shares": 78,
    "watch_time_minutes": 45670,
    "average_view_duration": "2:58",
    "click_through_rate": 6.7,
    "audience_retention": [
      {"time": "0:00", "retention": 100},
      {"time": "0:30", "retention": 87},
      {"time": "1:00", "retention": 74},
      {"time": "2:00", "retention": 65},
      {"time": "3:00", "retention": 58}
    ],
    "traffic_sources": {
      "youtube_search": 45.2,
      "browse_features": 23.8,
      "external": 15.6,
      "suggested_videos": 12.4,
      "playlists": 3.0
    },
    "demographics": {
      "age_groups": {
        "18-24": 15.2,
        "25-34": 32.8,
        "35-44": 28.4,
        "45-54": 16.9,
        "55+": 6.7
      },
      "gender": {
        "male": 62.3,
        "female": 37.7
      }
    },
    "revenue": {
      "estimated_revenue": 23.45,
      "rpm": 1.52,
      "ad_impressions": 8540
    }
  }
}
```

### TikTok Features

#### POST /platforms/tiktok/optimize
Optimize content for TikTok.

**Request:**
```json
{
  "content_item_id": "content_123456789",
  "optimization_options": {
    "hashtag_research": true,
    "trending_sounds": true,
    "vertical_optimization": true,
    "captions": true
  }
}
```

**Response:**
```json
{
  "optimization_id": "tt_opt_001",
  "optimized_content": {
    "description": "AI is revolutionizing healthcare! 🏥🤖 From diagnostic tools to patient care, the future is here! What's your take? 💭 #AIHealthcare #MedTech #Innovation #TechTalk #FutureMedicine #HealthTech #AI2024 #MedicalInnovation",
    "hashtags": {
      "trending": ["#AIHealthcare", "#MedTech", "#Innovation"],
      "niche": ["#HealthTech", "#MedicalInnovation", "#AI2024"],
      "broad": ["#TechTalk", "#FutureMedicine"],
      "total_reach": 15600000
    },
    "trending_sounds": [
      {
        "sound_id": "7284756389",
        "sound_name": "Tech Innovation Beat",
        "usage_count": 45600,
        "trend_score": 8.7
      }
    ],
    "captions": {
      "auto_generated": true,
      "language": "en",
      "accuracy": 96.8
    }
  },
  "format_optimization": {
    "aspect_ratio": "9:16",
    "resolution": "1080x1920",
    "duration": "58s",
    "hook_timing": "0-3s",
    "cta_timing": "52-58s"
  }
}
```

### Instagram Features

#### POST /platforms/instagram/optimize
Optimize content for Instagram.

**Request:**
```json
{
  "content_item_id": "content_123456789",
  "content_type": "reel",
  "optimization_options": {
    "hashtag_research": true,
    "story_adaptation": true,
    "carousel_creation": true
  }
}
```

**Response:**
```json
{
  "optimization_id": "ig_opt_001",
  "content_variants": {
    "reel": {
      "video_url": "/uploads/ig_opt_001_reel.mp4",
      "duration": "60s",
      "aspect_ratio": "9:16",
      "cover_image": "/uploads/ig_opt_001_cover.jpg"
    },
    "story": {
      "slides": [
        "/uploads/ig_opt_001_story_1.jpg",
        "/uploads/ig_opt_001_story_2.jpg",
        "/uploads/ig_opt_001_story_3.jpg"
      ],
      "duration_per_slide": "5s"
    },
    "carousel": {
      "images": [
        "/uploads/ig_opt_001_carousel_1.jpg",
        "/uploads/ig_opt_001_carousel_2.jpg",
        "/uploads/ig_opt_001_carousel_3.jpg"
      ],
      "captions": [
        "🏥 AI is transforming healthcare",
        "🤖 Diagnostic tools getting smarter",
        "📊 Patient data more secure than ever"
      ]
    }
  },
  "hashtags": {
    "recommended": "#AIHealthcare #MedTech #Innovation #HealthTech #TechNews #MedicalAI #Healthcare2024 #FutureMedicine #AIInnovation #MedicalTechnology",
    "reach_estimate": 750000,
    "engagement_estimate": 4.2
  },
  "posting_strategy": {
    "optimal_times": ["12:00", "17:00", "20:00"],
    "best_days": ["Tuesday", "Wednesday", "Thursday"],
    "content_pillars": ["Educational", "Innovation", "Behind-the-scenes"]
  }
}
```

## Upload Monitoring

### Real-time Status

#### GET /uploads/active
Get all active uploads across platforms.

**Response:**
```json
{
  "active_uploads": [
    {
      "upload_id": "upload_001",
      "content_title": "AI in Healthcare Guide",
      "platforms": {
        "youtube": {
          "status": "processing",
          "progress": 78,
          "eta": "2m 15s"
        },
        "tiktok": {
          "status": "completed",
          "progress": 100,
          "video_id": "7284756389"
        }
      },
      "started_at": "2024-09-15T10:30:00Z"
    }
  ],
  "queue_status": {
    "total_queued": 5,
    "processing": 2,
    "waiting": 3,
    "estimated_queue_time": "15m 30s"
  },
  "system_status": {
    "upload_capacity": 85,
    "api_health": {
      "youtube": "healthy",
      "tiktok": "healthy", 
      "instagram": "degraded",
      "facebook": "healthy"
    }
  }
}
```

#### GET /uploads/history
Get upload history with filtering options.

**Query Parameters:**
- `platform` (optional): Filter by platform
- `status` (optional): Filter by status (completed, failed, cancelled)
- `date_from` (optional): Start date filter
- `date_to` (optional): End date filter
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset

**Response:**
```json
{
      "uploads": [
    {
      "upload_id": "upload_batch_001",
      "content_item_id": "content_001",
      "platforms": ["youtube", "tiktok"],
      "status": "queued",
      "priority": "high"
    },
    {
      "upload_id": "upload_batch_002",
      "content_item_id": "content_002", 
      "platforms": ["instagram", "facebook"],
      "status": "scheduled",
      "scheduled_time": "2024-09-15T18:00:00Z"
    },
    {
      "upload_id": "upload_batch_003",
      "content_item_id": "content_003",
      "platforms": ["youtube"],
      "status": "queued"
    }
  ]
}
```

#### GET /upload/batch/{batch_id}
Get batch upload status and progress.

**Response:**
```json
{
  "batch_id": "batch_123456789",
  "status": "in_progress",
  "progress": {
    "completed": 2,
    "in_progress": 1,
    "pending": 0,
    "failed": 0,
    "overall_progress": 67
  },
  "started_at": "2024-09-15T10:30:00Z",
  "estimated_completion": "2024-09-15T11:15:00Z",
  "uploads": [
    {
      "upload_id": "upload_batch_001",
      "status": "completed",
      "platforms": {
        "youtube": {
          "video_id": "dQw4w9WgXcQ",
          "status": "live",
          "url": "https://youtube.com/watch?v=dQw4w9WgXcQ"
        },
        "tiktok": {
          "video_id": "7284756389",
          "status": "live",
          "url": "https://tiktok.com/@username/video/7284756389"
        }
      },
      "completion_time": "8m 45s"
    },
    {
      "upload_id": "upload_batch_002",
      "status": "in_progress",
      "platforms": {
        "instagram": {
          "status": "uploading",
          "progress": 65
        },
        "facebook": {
          "status": "processing",
          "progress": 78
        }
      }
    },
    {
      "upload_id": "upload_batch_003",
      "status": "completed",
      "platforms": {
        "youtube": {
          "video_id": "xyz789abc",
          "status": "premiere_scheduled",
          "premiere_time": "2024-09-15T20:00:00Z"
        }
      }
    }
  ],
  "statistics": {
    "total_platforms": 6,
    "successful_uploads": 5,
    "failed_uploads": 0,
    "average_upload_time": "7m 23s"
  }
}
```

### Scheduled Uploads

#### GET /uploads/scheduled
Get all scheduled uploads.

**Response:**
```json
{
  "scheduled_uploads": [
    {
      "upload_id": "upload_scheduled_001",
      "content_title": "Weekly Tech News",
      "platforms": ["youtube", "facebook"],
      "scheduled_time": "2024-09-15T18:00:00Z",
      "status": "scheduled",
      "created_at": "2024-09-15T10:30:00Z",
      "time_until_upload": "7h 30m"
    },
    {
      "upload_id": "upload_scheduled_002",
      "content_title": "Product Launch Announcement",
      "platforms": ["youtube"],
      "scheduled_time": "2024-09-16T12:00:00Z",
      "status": "scheduled",
      "upload_type": "premiere"
    }
  ],
  "next_upload": {
    "upload_id": "upload_scheduled_001",
    "time": "2024-09-15T18:00:00Z",
    "countdown": "7h 30m 15s"
  }
}
```

#### POST /uploads/schedule
Schedule upload for later.

**Request:**
```json
{
  "content_item_id": "content_123456789",
  "platforms": ["youtube", "tiktok"],
  "scheduled_time": "2024-09-15T18:00:00Z",
  "timezone": "UTC",
  "upload_settings": {
    "youtube": {
      "premiere": true,
      "chat_enabled": true
    }
  }
}
```

#### PUT /uploads/schedule/{upload_id}
Modify scheduled upload.

**Request:**
```json
{
  "scheduled_time": "2024-09-15T20:00:00Z",
  "platforms": ["youtube", "tiktok", "instagram"]
}
```

#### DELETE /uploads/schedule/{upload_id}
Cancel scheduled upload.

**Response:**
```json
{
  "upload_id": "upload_scheduled_001",
  "status": "cancelled",
  "message": "Scheduled upload cancelled successfully"
}
```

## Data Models

### Upload Object
```json
{
  "upload_id": "upload_123456789",
  "content_item_id": "content_123456789",
  "user_id": "user_456",
  "status": "completed",
  "platforms": ["youtube", "tiktok", "instagram"],
  "created_at": "2024-09-15T10:30:00Z",
  "started_at": "2024-09-15T10:31:15Z",
  "completed_at": "2024-09-15T10:42:30Z",
  "total_duration": "11m 15s",
  "priority": "normal",
  "retry_count": 0,
  "metadata": {
    "content_title": "AI in Healthcare Guide",
    "content_type": "educational_video",
    "duration": "4:15",
    "file_size_mb": 45.7
  }
}
```

### Platform Upload Object
```json
{
  "platform_upload_id": "yt_upload_001",
  "upload_id": "upload_123456789",
  "platform": "youtube",
  "status": "completed",
  "progress": 100,
  "started_at": "2024-09-15T10:31:15Z",
  "completed_at": "2024-09-15T10:42:30Z",
  "duration": "11m 15s",
  "platform_video_id": "dQw4w9WgXcQ",
  "platform_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "upload_settings": {
    "title": "AI in Healthcare: Complete Professional Guide",
    "description": "Comprehensive guide...",
    "tags": ["AI", "Healthcare", "Medical Technology"],
    "privacy": "public",
    "category": "Science & Technology"
  },
  "optimization_applied": {
    "title_seo": true,
    "description_enhancement": true,
    "thumbnail_optimization": true
  },
  "initial_metrics": {
    "views": 23,
    "likes": 5,
    "comments": 2
  },
  "processing_info": {
    "upload_stage": "completed",
    "processing_stage": "completed",
    "monetization_review": "approved"
  }
}
```

### Platform Account Object
```json
{
  "platform": "youtube",
  "account_id": "UC1234567890",
  "status": "connected",
  "account_info": {
    "name": "AI Content Factory",
    "username": "@aicontentfactory",
    "verified": true,
    "follower_count": 15420,
    "following_count": 89,
    "bio": "Creating the future of AI content",
    "profile_image": "https://...",
    "account_type": "business"
  },
  "authentication": {
    "connected_at": "2024-09-10T09:30:00Z",
    "expires_at": "2024-10-10T09:30:00Z",
    "scopes": ["upload", "read", "analytics"],
    "refresh_token_valid": true
  },
  "settings": {
    "auto_upload": true,
    "default_privacy": "public",
    "notifications": true,
    "optimization": true
  },
  "limits": {
    "daily_uploads": 100,
    "used_today": 12,
    "remaining_today": 88,
    "file_size_limit_mb": 256
  }
}
```

### Performance Metrics Object
```json
{
  "upload_id": "upload_123456789",
  "platform": "youtube",
  "video_id": "dQw4w9WgXcQ",
  "metrics": {
    "views": 15420,
    "likes": 892,
    "dislikes": 23,
    "comments": 156,
    "shares": 78,
    "saves": 234,
    "click_through_rate": 6.7,
    "watch_time_minutes": 45670,
    "average_view_duration": "2:58",
    "audience_retention": 67.8,
    "engagement_rate": 8.4,
    "reach": 18900,
    "impressions": 34500
  },
  "revenue": {
    "estimated_revenue": 23.45,
    "rpm": 1.52,
    "ad_impressions": 8540,
    "monetization_status": "enabled"
  },
  "demographics": {
    "top_countries": ["US", "UK", "CA", "AU", "DE"],
    "age_groups": {
      "18-24": 15.2,
      "25-34": 32.8,
      "35-44": 28.4,
      "45-54": 16.9,
      "55+": 6.7
    },
    "gender": {
      "male": 62.3,
      "female": 37.7
    }
  },
  "traffic_sources": {
    "search": 45.2,
    "browse": 23.8,
    "external": 15.6,
    "suggested": 12.4,
    "playlists": 3.0
  },
  "measured_at": "2024-09-15T15:30:00Z"
}
```

## Error Handling

### HTTP Status Codes
| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Upload started successfully |
| 202 | Accepted | Upload queued for processing |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Platform not authorized |
| 404 | Not Found | Upload or content not found |
| 409 | Conflict | Upload already in progress |
| 422 | Unprocessable Entity | Content validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Platform API error |
| 502 | Bad Gateway | Platform service unavailable |
| 503 | Service Unavailable | Upload service temporarily down |

### Error Response Format
```json
{
  "error": {
    "code": "UPLOAD_FAILED",
    "message": "Upload to YouTube failed due to quota exceeded",
    "details": {
      "upload_id": "upload_123456789",
      "platform": "youtube",
      "platform_error": "quotaExceeded",
      "quota_reset_time": "2024-09-16T00:00:00Z"
    },
    "suggestions": [
      "Wait for quota reset at midnight UTC",
      "Try uploading to other platforms first",
      "Consider upgrading YouTube API quota"
    ],
    "retry_info": {
      "retryable": true,
      "retry_after": 3600,
      "max_retries": 3,
      "current_retry": 1
    },
    "timestamp": "2024-09-15T10:30:00Z",
    "request_id": "req_987654321"
  }
}
```

### Platform-Specific Error Codes

#### YouTube Errors
| Code | Description | Action |
|------|-------------|--------|
| QUOTA_EXCEEDED | Daily quota limit reached | Wait for reset |
| UPLOAD_TOO_LARGE | File size exceeds limit | Compress video |
| INVALID_VIDEO_FORMAT | Unsupported file format | Convert format |
| COPYRIGHT_CLAIM | Content ID match found | Review content |
| COMMUNITY_GUIDELINES | Violates guidelines | Modify content |

#### TikTok Errors
| Code | Description | Action |
|------|-------------|--------|
| DAILY_LIMIT_REACHED | Daily upload limit reached | Wait 24 hours |
| VIDEO_TOO_LONG | Video exceeds duration limit | Trim video |
| INAPPROPRIATE_CONTENT | Content flagged | Review content |
| DUPLICATE_VIDEO | Video already exists | Use different content |

## Rate Limiting

### Platform Rate Limits

#### YouTube
- **Quota Units**: 10,000 per day (default)
- **Upload Cost**: 1,600 units per upload
- **Max Uploads/Day**: ~6 videos
- **File Size Limit**: 256GB or 12 hours

#### TikTok
- **Daily Uploads**: 10 per day
- **Hourly Limit**: 3 per hour  
- **File Size Limit**: 4GB
- **Duration Limit**: 10 minutes

#### Instagram
- **Hourly Limit**: 5 posts per hour
- **Daily Limit**: 25 posts per day
- **Story Limit**: 100 per day
- **File Size Limit**: 4GB

#### Facebook
- **Hourly Limit**: 10 posts per hour
- **Daily Limit**: 50 posts per day
- **File Size Limit**: 4GB
- **Duration Limit**: 240 minutes

### API Rate Limiting
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1634567890
X-RateLimit-Platform: youtube
X-Platform-Quota-Remaining: 7660
```

## Examples

### Python SDK Example
```python
import requests
import time
from typing import List, Dict

class PlatformManagerClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def upload_content(self, content_id: str, platforms: List[str], 
                      settings: Dict = None) -> Dict:
        """Upload content to specified platforms"""
        payload = {
            'content_item_id': content_id,
            'platforms': platforms,
            'optimization': {
                'auto_optimize': True,
                'generate_variants': True,
                'seo_enhance': True
            }
        }
        
        if settings:
            payload['upload_settings'] = settings
        
        response = requests.post(
            f'{self.base_url}/upload',
            headers=self.headers,
            json=payload
        )
        
        if response.status_code != 201:
            raise Exception(f"Upload failed: {response.text}")
        
        return response.json()
    
    def monitor_upload(self, upload_id: str, callback=None) -> Dict:
        """Monitor upload progress until completion"""
        while True:
            response = requests.get(
                f'{self.base_url}/upload/{upload_id}',
                headers=self.headers
            )
            
            status = response.json()
            
            if callback:
                callback(status)
            
            if status['overall_status'] in ['completed', 'failed', 'cancelled']:
                return status
            
            time.sleep(10)
    
    def batch_upload(self, uploads: List[Dict]) -> Dict:
        """Upload multiple content items"""
        payload = {
            'uploads': uploads,
            'batch_settings': {
                'parallel_uploads': True,
                'max_concurrent': 3,
                'retry_failed': True
            }
        }
        
        response = requests.post(
            f'{self.base_url}/upload/batch',
            headers=self.headers,
            json=payload
        )
        
        return response.json()
    
    def get_platform_status(self, platform: str = None) -> Dict:
        """Get platform connection status"""
        url = f'{self.base_url}/platforms'
        if platform:
            url += f'/{platform}'
        url += '/status'
        
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def get_upload_analytics(self, timeframe: str = '7d') -> Dict:
        """Get upload performance analytics"""
        response = requests.get(
            f'{self.base_url}/analytics/uploads',
            headers=self.headers,
            params={'timeframe': timeframe}
        )
        return response.json()

# Usage Example
client = PlatformManagerClient('http://localhost:8003', 'your_token')

# Upload to multiple platforms
upload_result = client.upload_content(
    content_id='content_123',
    platforms=['youtube', 'tiktok'],
    settings={
        'youtube': {
            'title': 'AI Revolution in Healthcare',
            'privacy': 'public',
            'tags': ['AI', 'Healthcare', 'Technology']
        },
        'tiktok': {
            'description': 'AI is changing healthcare! 🤖🏥 #AI #Healthcare #Tech'
        }
    }
)

print(f"Upload started: {upload_result['upload_id']}")

# Monitor progress
def progress_callback(status):
    print(f"Progress: {status['progress']}%")
    for platform, details in status['platforms'].items():
        print(f"  {platform}: {details['status']}")

final_status = client.monitor_upload(
    upload_result['upload_id'], 
    callback=progress_callback
)

print("Upload completed!")
for platform, details in final_status['platforms'].items():
    if 'url' in details:
        print(f"{platform}: {details['url']}")
```

### JavaScript Example
```javascript
class PlatformManagerAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async uploadContent(contentId, platforms, settings = {}) {
        const response = await fetch(`${this.baseUrl}/upload`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                content_item_id: contentId,
                platforms: platforms,
                upload_settings: settings,
                optimization: {
                    auto_optimize: true,
                    generate_variants: true,
                    seo_enhance: true
                }
            })
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async monitorUpload(uploadId, onProgress) {
        return new Promise((resolve, reject) => {
            const checkStatus = async () => {
                try {
                    const response = await fetch(
                        `${this.baseUrl}/upload/${uploadId}`,
                        { headers: this.headers }
                    );
                    
                    const status = await response.json();
                    
                    if (onProgress) {
                        onProgress(status);
                    }
                    
                    switch (status.overall_status) {
                        case 'completed':
                            resolve(status);
                            break;
                        case 'failed':
                        case 'cancelled':
                            reject(new Error(`Upload ${status.overall_status}`));
                            break;
                        default:
                            setTimeout(checkStatus, 5000);
                    }
                } catch (error) {
                    reject(error);
                }
            };
            
            checkStatus();
        });
    }

    async getPlatformStatus(platform) {
        const url = platform 
            ? `${this.baseUrl}/platforms/${platform}/status`
            : `${this.baseUrl}/platforms/status`;
            
        const response = await fetch(url, { headers: this.headers });
        return await response.json();
    }

    async scheduleUpload(contentId, platforms, scheduledTime, settings = {}) {
        const response = await fetch(`${this.baseUrl}/uploads/schedule`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                content_item_id: contentId,
                platforms: platforms,
                scheduled_time: scheduledTime,
                upload_settings: settings
            })
        });

        return await response.json();
    }

    async getAnalytics(timeframe = '7d') {
        const response = await fetch(
            `${this.baseUrl}/analytics/uploads?timeframe=${timeframe}`,
            { headers: this.headers }
        );
        return await response.json();
    }
}

// Usage
const api = new PlatformManagerAPI('http://localhost:8003', 'your_token');

// Upload with progress tracking
api.uploadContent('content_123', ['youtube', 'tiktok'], {
    youtube: {
        title: 'AI Revolution in Healthcare',
        tags: ['AI', 'Healthcare', 'Technology'],
        privacy: 'public'
    },
    tiktok: {
        description: 'AI is changing healthcare! 🤖🏥 #AI #Healthcare #Tech'
    }
})
.then(upload => {
    console.log('Upload started:', upload.upload_id);
    
    return api.monitorUpload(upload.upload_id, (status) => {
        console.log(`Progress: ${status.progress}%`);
        Object.entries(status.platforms).forEach(([platform, details]) => {
            console.log(`  ${platform}: ${details.status}`);
        });
    });
})
.then(finalStatus => {
    console.log('Upload completed!');
    Object.entries(finalStatus.platforms).forEach(([platform, details]) => {
        if (details.url) {
            console.log(`${platform}: ${details.url}`);
        }
    });
})
.catch(error => {
    console.error('Upload failed:', error);
});

// Schedule upload for later
api.scheduleUpload(
    'content_456',
    ['youtube'],
    '2024-09-15T18:00:00Z',
    {
        youtube: {
            premiere: true,
            chat_enabled: true
        }
    }
)
.then(scheduled => {
    console.log('Upload scheduled:', scheduled.upload_id);
});
```

### cURL Examples
```bash
# Upload content to multiple platforms
curl -X POST http://localhost:8003/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_item_id": "content_123456789",
    "platforms": ["youtube", "tiktok"],
    "upload_settings": {
      "youtube": {
        "title": "AI in Healthcare Guide",
        "privacy": "public",
        "tags": ["AI", "Healthcare"]
      },
      "tiktok": {
        "description": "AI revolutionizing healthcare! 🤖🏥 #AI #Healthcare"
      }
    },
    "optimization": {
      "auto_optimize": true
    }
  }'

# Check upload status
curl -X GET http://localhost:8003/upload/upload_123456789 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get platform status
curl -X GET http://localhost:8003/platforms/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Schedule upload
curl -X POST http://localhost:8003/uploads/schedule \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_item_id": "content_123456789",
    "platforms": ["youtube"],
    "scheduled_time": "2024-09-15T18:00:00Z",
    "upload_settings": {
      "youtube": {
        "premiere": true
      }
    }
  }'

# Batch upload
curl -X POST http://localhost:8003/upload/batch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "uploads": [
      {
        "content_item_id": "content_001",
        "platforms": ["youtube", "tiktok"]
      },
      {
        "content_item_id": "content_002",
        "platforms": ["instagram"]
      }
    ],
    "batch_settings": {
      "parallel_uploads": true,
      "max_concurrent": 2
    }
  }'

# Get upload analytics
curl -X GET "http://localhost:8003/analytics/uploads?timeframe=30d" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get platform-specific analytics
curl -X GET http://localhost:8003/analytics/content/content_123/performance \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

This Platform Manager API provides comprehensive multi-platform content distribution capabilities with advanced optimization, monitoring, and analytics features. The API handles the complexity of platform-specific requirements while providing a unified interface for content upload and management.

For content generation capabilities, see [Content Engine API](content-engine-api.md). For trend data integration, see [Trend Monitor API](trend-monitor-api.md). "upload_001",
      "content_title": "AI in Healthcare Guide",
      "platforms": ["youtube", "tiktok"],
      "status": "completed",
      "success_count": 2,
      "failed_count": 0,
      "started_at": "2024-09-15T10:30:00Z",
      "completed_at": "2024-09-15T10:42:00Z",
      "total_duration": "12m 0s",
      "results": {
        "youtube": {
          "video_id": "dQw4w9WgXcQ",
          "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
          "views": 156,
          "status": "live"
        },
        "tiktok": {
          "video_id": "7284756389",
          "url": "https://tiktok.com/@username/video/7284756389",
          "views": 1240,
          "status": "live"
        }
      }
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 20,
    "offset": 0,
    "has_next": true
  },
  "statistics": {
    "total_uploads": 45,
    "successful_uploads": 42,
    "failed_uploads": 3,
    "success_rate": 93.3,
    "average_upload_time": "8m 15s"
  }
}
```

### Upload Analytics

#### GET /analytics/uploads
Get comprehensive upload analytics.

**Query Parameters:**
- `timeframe` (optional): 1h, 24h, 7d, 30d (default: 7d)
- `platform` (optional): Filter by platform
- `group_by` (optional): platform, date, status

**Response:**
```json
{
  "timeframe": "7d",
  "overview": {
    "total_uploads": 156,
    "successful_uploads": 148,
    "failed_uploads": 8,
    "success_rate": 94.9,
    "total_upload_time": "20h 45m",
    "average_upload_time": "8m 15s"
  },
  "platform_breakdown": {
    "youtube": {
      "uploads": 78,
      "success_rate": 96.2,
      "avg_upload_time": "12m 30s",
      "total_views": 45680,
      "total_watch_time": "145h 30m"
    },
    "tiktok": {
      "uploads": 52,
      "success_rate": 98.1,
      "avg_upload_time": "3m 45s",
      "total_views": 126780,
      "total_engagement": 8940
    },
    "instagram": {
      "uploads": 26,
      "success_rate": 88.5,
      "avg_upload_time": "6m 15s",
      "total_views": 23450,
      "total_likes": 2890
    }
  },
  "performance_trends": {
    "upload_volume": [
      {"date": "2024-09-09", "count": 18},
      {"date": "2024-09-10", "count": 22},
      {"date": "2024-09-11", "count": 25},
      {"date": "2024-09-12", "count": 19},
      {"date": "2024-09-13", "count": 28},
      {"date": "2024-09-14", "count": 24},
      {"date": "2024-09-15", "count": 20}
    ],
    "success_rate_trend": [
      {"date": "2024-09-09", "rate": 94.4},
      {"date": "2024-09-10", "rate": 95.5},
      {"date": "2024-09-11", "rate": 92.0},
      {"date": "2024-09-12", "rate": 94.7},
      {"date": "2024-09-13", "rate": 96.4},
      {"date": "2024-09-14", "rate": 95.8},
      {"date": "2024-09-15", "rate": 95.0}
    ]
  },
  "top_performing_content": [
    {
      "upload_id": "upload_045",
      "title": "AI Trends 2024",
      "total_views": 15600,
      "total_engagement": 1240,
      "platforms": ["youtube", "tiktok", "instagram"]
    }
  ]
}
```

## Performance Analytics

### Content Performance

#### GET /analytics/content/{content_id}/performance
Get cross-platform performance analytics for specific content.

**Response:**
```json
{
  "content_id": "content_123456789",
  "title": "AI in Healthcare Guide",
  "upload_date": "2024-09-15T10:42:00Z",
  "platforms": {
    "youtube": {
      "video_id": "dQw4w9WgXcQ",
      "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "metrics": {
        "views": 15420,
        "likes": 892,
        "comments": 156,
        "shares": 78,
        "watch_time_hours": 761.2,
        "ctr": 6.7,
        "average_view_duration": "2:58",
        "revenue": 23.45
      },
      "demographics": {
        "top_countries": ["US", "UK", "CA", "AU"],
        "age_groups": {"25-34": 32.8, "35-44": 28.4},
        "gender": {"male": 62.3, "female": 37.7}
      }
    },
    "tiktok": {
      "video_id": "7284756389",
      "url": "https://tiktok.com/@username/video/7284756389",
      "metrics": {
        "views": 126780,
        "likes": 8940,
        "comments": 567,
        "shares": 1230,
        "completion_rate": 78.5,
        "engagement_rate": 8.4
      },
      "audience_insights": {
        "top_regions": ["North America", "Europe", "Asia"],
        "peak_viewing_times": ["18:00-20:00", "21:00-23:00"],
        "age_distribution": {"18-24": 45.2, "25-34": 32.1}
      }
    },
    "instagram": {
      "post_id": "CXX123456",
      "url": "https://instagram.com/p/CXX123456/",
      "metrics": {
        "views": 23450,
        "likes": 1890,
        "comments": 234,
        "saves": 445,
        "shares": 123,
        "reach": 19800,
        "impressions": 34500
      },
      "story_metrics": {
        "reach": 8940,
        "impressions": 12300,
        "taps_forward": 567,
        "taps_back": 89,
        "exits": 234
      }
    }
  },
  "cross_platform_summary": {
    "total_views": 165650,
    "total_engagement": 12543,
    "overall_engagement_rate": 7.6,
    "best_performing_platform": "tiktok",
    "revenue_total": 23.45,
    "audience_overlap": {
      "youtube_tiktok": 15.2,
      "youtube_instagram": 12.8,
      "tiktok_instagram": 8.9
    }
  },
  "insights": [
    "TikTok generated 76% of total views",
    "YouTube had highest revenue per view",
    "Instagram showed strong save rate indicating quality content",
    "Peak engagement occurred 2-4 hours after posting"
  ]
}
```

### ROI Analysis

#### GET /analytics/roi
Get return on investment analysis for uploads.

**Query Parameters:**
- `timeframe` (optional): 7d, 30d, 90d (default: 30d)
- `platform` (optional): Filter by platform
- `content_type` (optional): Filter by content type

**Response:**
```json
{
  "timeframe": "30d",
  "roi_summary": {
    "total_investment": 387.50,
    "total_revenue": 1245.67,
    "total_roi": 221.4,
    "roi_percentage": "221.4%",
    "break_even_point": "12 days",
    "profit": 858.17
  },
  "platform_roi": {
    "youtube": {
      "investment": 123.75,
      "revenue": 789.45,
      "roi": 537.9,
      "average_revenue_per_upload": 10.12
    },
    "tiktok": {
      "investment": 98.50,
      "revenue": 234.56,
      "roi": 138.1,
      "average_revenue_per_upload": 4.51
    },
    "instagram": {
      "investment": 89.25,
      "revenue": 156.78,
      "roi": 75.7,
      "average_revenue_per_upload": 6.03
    },
    "facebook": {
      "investment": 76.00,
      "revenue": 64.88,
      "roi": -14.6,
      "average_revenue_per_upload": 3.24
    }
  },
  "content_type_roi": {
    "educational": {
      "uploads": 23,
      "investment": 115.00,
      "revenue": 456.78,
      "roi": 297.2
    },
    "promotional": {
      "uploads": 18,
      "investment": 135.00,
      "revenue": 389.45,
      "roi": 188.5
    },
    "entertainment": {
      "uploads": 12,
      "investment": 72.50,
      "revenue": 234.56,
      "roi": 223.5
    }
  },
  "trends": {
    "roi_improvement": 15.2,
    "cost_optimization": 8.7,
    "revenue_growth": 23.8
  },
  "recommendations": [
    "Focus more on educational content for highest ROI",
    "Consider reducing Facebook investment due to negative ROI",
    "YouTube consistently provides best revenue per upload"
  ]
}
```

## Webhook Integration

### Webhook Configuration

#### GET /webhooks
Get configured webhooks.

**Response:**
```json
{
  "webhooks": [
    {
      "webhook_id": "webhook_001",
      "url": "https://your-app.com/webhooks/uploads",
      "events": ["upload.completed", "upload.failed", "upload.processing"],
      "platforms": ["youtube", "tiktok"],
      "status": "active",
      "created_at": "2024-09-10T09:30:00Z",
      "last_triggered": "2024-09-15T10:42:00Z",
      "success_rate": 98.5
    }
  ]
}
```

#### POST /webhooks
Create new webhook.

**Request:**
```json
{
  "url": "https://your-app.com/webhooks/uploads",
  "events": ["upload.completed", "upload.failed", "performance.milestone"],
  "platforms": ["youtube", "tiktok", "instagram"],
  "secret": "your_webhook_secret",
  "retry_config": {
    "max_retries": 3,
    "retry_delay": 5,
    "exponential_backoff": true
  }
}
```

### Webhook Events

#### Upload Events
```json
{
  "event": "upload.completed",
  "timestamp": "2024-09-15T10:42:00Z",
  "data": {
    "upload_id": "upload_123456789",
    "content_id": "content_123456789",
    "platform": "youtube",
    "video_id": "dQw4w9WgXcQ",
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "title": "AI in Healthcare Guide",
    "upload_duration": "12m 30s",
    "status": "live",
    "initial_metrics": {
      "views": 12,
      "likes": 3,
      "comments": 1
    }
  }
}
```

#### Performance Events
```json
{
  "event": "performance.milestone",
  "timestamp": "2024-09-15T14:30:00Z",
  "data": {
    "upload_id": "upload_123456789",
    "platform": "youtube", 
    "milestone": "1000_views",
    "current_metrics": {
      "views": 1000,
      "likes": 67,
      "comments": 23,
      "watch_time_hours": 52.3
    },
    "time_to_milestone": "3h 48m"
  }
}
```

## Bulk Operations

### Batch Upload

#### POST /upload/batch
Upload multiple content items across platforms.

**Request:**
```json
{
  "batch_name": "Weekly Content Drop",
  "uploads": [
    {
      "content_item_id": "content_001",
      "platforms": ["youtube", "tiktok"],
      "priority": "high"
    },
    {
      "content_item_id": "content_002", 
      "platforms": ["instagram", "facebook"],
      "scheduled_time": "2024-09-15T18:00:00Z"
    },
    {
      "content_item_id": "content_003",
      "platforms": ["youtube"],
      "upload_settings": {
        "youtube": {
          "playlist_id": "PLxxx",
          "premiere": true
        }
      }
    }
  ],
  "batch_settings": {
    "parallel_uploads": true,
    "max_concurrent": 3,
    "retry_failed": true,
    "notification_webhook": "https://your-app.com/batch-complete"
  }
}
```

**Response:**
```json
{
  "batch_id": "batch_123456789",
  "status": "started",
  "total_uploads": 3,
  "estimated_completion": "2024-09-15T11:30:00Z", 
  "uploads": [
    {
      "upload_id":# Platform Manager API Documentation

## 📋 Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Platform Management](#platform-management)
- [Content Upload](#content-upload)
- [Platform-Specific Features](#platform-specific-features)
- [Upload Monitoring](#upload-monitoring)
- [Performance Analytics](#performance-analytics)
- [Webhook Integration](#webhook-integration)
- [Bulk Operations](#bulk-operations)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The Platform Manager API handles multi-platform content distribution and upload management for AI Content Factory. It provides seamless integration with major social media platforms including YouTube, TikTok, Instagram, and Facebook, with platform-specific optimization and automated upload workflows.

### Key Features
- **Multi-Platform Support**: Upload to YouTube, TikTok, Instagram, Facebook
- **Platform Optimization**: Automatic content adaptation for each platform
- **Bulk Upload**: Efficient batch processing for multiple uploads
- **Performance Tracking**: Real-time upload progress and analytics
- **Webhook Integration**: Event-driven notifications for upload status
- **Scheduling**: Time-based upload scheduling and optimal timing
- **Content Variants**: Platform-specific content versions and formats

## Authentication

All API requests require authentication using JWT tokens.

### Platform Authentication
Each social media platform requires separate OAuth authentication:

```http
GET /platforms/{platform}/auth
Authorization: Bearer <your_jwt_token>
```

This returns a platform-specific OAuth URL for user authorization.

## Base URL

- **Development**: `http://localhost:8003`
- **Staging**: `https://staging-api.ai-content-factory.com/platform-manager`
- **Production**: `https://api.ai-content-factory.com/platform-manager`

## Platform Management

### Platform Status

#### GET /platforms/status
Get connection status of all platforms.

**Response:**
```json
{
  "platforms": {
    "youtube": {
      "status": "connected",
      "account_info": {
        "channel_name": "AI Content Factory",
        "channel_id": "UC1234567890",
        "subscriber_count": 15420,
        "verified": true
      },
      "quota_info": {
        "daily_quota": 10000,
        "used_quota": 2340,
        "remaining_quota": 7660,
        "reset_time": "2024-09-16T00:00:00Z"
      },
      "last_upload": "2024-09-15T14:30:00Z",
      "upload_capability": "enabled"
    },
    "tiktok": {
      "status": "connected",
      "account_info": {
        "username": "@aicontentfactory",
        "follower_count": 8750,
        "verified": false
      },
      "quota_info": {
        "daily_uploads": 10,
        "used_uploads": 3,
        "remaining_uploads": 7,
        "reset_time": "2024-09-16T00:00:00Z"
      },
      "last_upload": "2024-09-15T12:15:00Z",
      "upload_capability": "enabled"
    },
    "instagram": {
      "status": "authentication_expired",
      "account_info": {
        "username": "aicontentfactory",
        "follower_count": 12300,
        "verified": false
      },
      "last_upload": "2024-09-14T18:20:00Z",
      "upload_capability": "disabled",
      "reconnect_url": "/platforms/instagram/auth"
    },
    "facebook": {
      "status": "not_connected",
      "connect_url": "/platforms/facebook/auth",
      "upload_capability": "disabled"
    }
  },
  "overall_status": "partial",
  "connected_platforms": 2,
  "total_platforms": 4
}
```

#### GET /platforms/{platform}/status
Get detailed status for specific platform.

**Path Parameters:**
- `platform`: youtube, tiktok, instagram, facebook

**Response:**
```json
{
  "platform": "youtube",
  "status": "connected",
  "connection_details": {
    "authenticated_at": "2024-09-10T09:30:00Z",
    "expires_at": "2024-10-10T09:30:00Z",
    "scopes": ["youtube.upload", "youtube.readonly"],
    "refresh_token_valid": true
  },
  "account_info": {
    "channel_name": "AI Content Factory",
    "channel_id": "UC1234567890",
    "channel_url": "https://youtube.com/channel/UC1234567890",
    "subscriber_count": 15420,
    "view_count": 1250000,
    "video_count": 89,
    "verified": true,
    "monetization_enabled": true
  },
  "upload_settings": {
    "default_privacy": "public",
    "default_category": "Science & Technology",
    "auto_tags": ["AI", "Technology", "Content Creation"],
    "monetization": true,
    "comments_enabled": true,
    "notifications": true
  },
  "quota_info": {
    "daily_quota": 10000,
    "used_quota": 2340,
    "remaining_quota": 7660,
    "quota_reset_time": "2024-09-16T00:00:00Z",
    "upload_limit_reached": false
  },
  "performance_stats": {
    "total_uploads": 89,
    "successful_uploads": 87,
    "failed_uploads": 2,
    "success_rate": 97.8,
    "average_upload_time": "3m 45s",
    "last_7_days_uploads": 12
  }
}
```

### Platform Authentication