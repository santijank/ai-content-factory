# Trend Monitor API Documentation

## 📋 Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The Trend Monitor API provides access to real-time trending data collected from multiple social media platforms including YouTube, Google Trends, Twitter, and Reddit. This service continuously monitors these platforms and provides structured trend data with analysis and scoring.

### Key Features
- Real-time trend collection from 4+ platforms
- Trend scoring and categorization
- Geographic and temporal trend analysis
- Duplicate detection and data normalization
- Historical trend data access

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

- **Development**: `http://localhost:8001`
- **Staging**: `https://staging-api.ai-content-factory.com/trend-monitor`
- **Production**: `https://api.ai-content-factory.com/trend-monitor`

## Endpoints

### Health Check

#### GET /health
Check service health and status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-09-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "youtube_api": "healthy",
    "twitter_api": "healthy"
  }
}
```

### Trends Collection

#### POST /trends/collect
Trigger manual trend collection from all sources.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "task_id": "collect_123456789",
  "status": "started",
  "message": "Trend collection initiated",
  "estimated_completion": "2024-09-15T10:35:00Z"
}
```

#### GET /trends/collect/{task_id}
Get status of a collection task.

**Response:**
```json
{
  "task_id": "collect_123456789",
  "status": "completed",
  "progress": 100,
  "results": {
    "trends_collected": 25,
    "new_trends": 8,
    "updated_trends": 17,
    "sources": {
      "youtube": 12,
      "google_trends": 5,
      "twitter": 6,
      "reddit": 2
    }
  },
  "started_at": "2024-09-15T10:30:00Z",
  "completed_at": "2024-09-15T10:34:30Z"
}
```

### Trends Retrieval

#### GET /trends
Get list of trends with filtering and pagination.

**Query Parameters:**
- `source` (optional): Filter by source (youtube, google_trends, twitter, reddit)
- `category` (optional): Filter by category (technology, lifestyle, business, etc.)
- `region` (optional): Filter by region (US, global, etc.)
- `min_score` (optional): Minimum popularity score (0-10)
- `min_growth` (optional): Minimum growth rate percentage
- `since` (optional): ISO timestamp for trends since this time
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `sort_by` (optional): Sort field (popularity_score, growth_rate, collected_at)
- `sort_order` (optional): Sort order (asc, desc) (default: desc)

**Example Request:**
```http
GET /trends?source=youtube&category=technology&min_score=7&limit=10&sort_by=growth_rate
```

**Response:**
```json
{
  "trends": [
    {
      "id": "trend_yt_001",
      "source": "youtube",
      "topic": "AI Content Creation",
      "keywords": ["ai", "content", "creation", "automation"],
      "popularity_score": 8.5,
      "growth_rate": 45.2,
      "category": "technology",
      "region": "global",
      "collected_at": "2024-09-15T10:30:00Z",
      "metadata": {
        "video_count": 1250,
        "view_count": 15600000,
        "engagement_rate": 7.8
      }
    }
  ],
  "pagination": {
    "total": 156,
    "limit": 10,
    "offset": 0,
    "has_next": true,
    "has_prev": false
  },
  "filters_applied": {
    "source": "youtube",
    "category": "technology",
    "min_score": 7
  }
}
```

#### GET /trends/{trend_id}
Get detailed information about a specific trend.

**Response:**
```json
{
  "id": "trend_yt_001",
  "source": "youtube",
  "topic": "AI Content Creation",
  "keywords": ["ai", "content", "creation", "automation", "video"],
  "popularity_score": 8.5,
  "growth_rate": 45.2,
  "category": "technology",
  "region": "global",
  "collected_at": "2024-09-15T10:30:00Z",
  "raw_data": {
    "video_count": 1250,
    "view_count": 15600000,
    "engagement_rate": 7.8,
    "trending_duration": "3 days",
    "related_hashtags": ["#AI", "#ContentCreation", "#Automation"],
    "top_creators": ["TechGuru123", "AIExplainer", "ContentKing"]
  },
  "analysis": {
    "content_opportunities": 15,
    "competition_level": "medium",
    "audience_size": "large",
    "monetization_potential": "high"
  },
  "history": {
    "first_seen": "2024-09-13T08:15:00Z",
    "peak_score": 9.2,
    "peak_date": "2024-09-14T14:20:00Z",
    "trend_trajectory": "rising"
  }
}
```

### Trend Analysis

#### GET /trends/analytics/summary
Get trend analytics summary.

**Query Parameters:**
- `timeframe` (optional): Time period (1h, 6h, 24h, 7d, 30d) (default: 24h)
- `source` (optional): Filter by source
- `category` (optional): Filter by category

**Response:**
```json
{
  "timeframe": "24h",
  "summary": {
    "total_trends": 89,
    "new_trends": 23,
    "trending_up": 34,
    "trending_down": 12,
    "stable": 43
  },
  "by_source": {
    "youtube": 35,
    "google_trends": 18,
    "twitter": 24,
    "reddit": 12
  },
  "by_category": {
    "technology": 28,
    "lifestyle": 21,
    "business": 15,
    "entertainment": 13,
    "health": 8,
    "other": 4
  },
  "top_growing": [
    {
      "id": "trend_yt_005",
      "topic": "Virtual Reality Fitness",
      "growth_rate": 89.3,
      "source": "youtube"
    }
  ],
  "top_scored": [
    {
      "id": "trend_gt_003",
      "topic": "Sustainable Energy",
      "popularity_score": 9.4,
      "source": "google_trends"
    }
  ]
}
```

#### GET /trends/analytics/categories
Get trend distribution by categories.

**Response:**
```json
{
  "categories": [
    {
      "name": "technology",
      "trend_count": 28,
      "avg_popularity": 7.8,
      "avg_growth": 35.2,
      "top_keywords": ["ai", "blockchain", "automation", "vr"]
    },
    {
      "name": "lifestyle",
      "trend_count": 21,
      "avg_popularity": 6.9,
      "avg_growth": 22.1,
      "top_keywords": ["wellness", "productivity", "minimalism", "fitness"]
    }
  ],
  "generated_at": "2024-09-15T10:30:00Z"
}
```

### Keyword Analysis

#### GET /trends/keywords
Get trending keywords analysis.

**Query Parameters:**
- `timeframe` (optional): Time period (default: 24h)
- `min_frequency` (optional): Minimum keyword frequency (default: 3)
- `limit` (optional): Number of results (default: 50)

**Response:**
```json
{
  "keywords": [
    {
      "keyword": "ai",
      "frequency": 15,
      "avg_score": 8.2,
      "growth_trend": "rising",
      "associated_trends": [
        "AI Content Creation",
        "ChatGPT alternatives",
        "AI productivity tools"
      ]
    },
    {
      "keyword": "sustainability",
      "frequency": 8,
      "avg_score": 7.5,
      "growth_trend": "stable",
      "associated_trends": [
        "Sustainable Living Tips",
        "Green technology",
        "Zero waste lifestyle"
      ]
    }
  ],
  "metadata": {
    "total_keywords": 234,
    "timeframe": "24h",
    "generated_at": "2024-09-15T10:30:00Z"
  }
}
```

### Source-Specific Endpoints

#### GET /trends/youtube
Get YouTube-specific trends with platform-specific metadata.

**Response includes additional YouTube fields:**
```json
{
  "trends": [
    {
      "id": "trend_yt_001",
      "topic": "AI Content Creation",
      "youtube_data": {
        "video_count": 1250,
        "total_views": 15600000,
        "avg_duration": "8:35",
        "top_channels": ["TechGuru123", "AIExplainer"],
        "trending_tags": ["#AI", "#ContentCreation"],
        "upload_frequency": "daily"
      }
    }
  ]
}
```

#### GET /trends/google
Get Google Trends-specific data.

#### GET /trends/twitter
Get Twitter-specific trends.

#### GET /trends/reddit
Get Reddit-specific trends.

## Data Models

### Trend Object
```json
{
  "id": "string",
  "source": "youtube|google_trends|twitter|reddit",
  "topic": "string",
  "keywords": ["string"],
  "popularity_score": "number (0-10)",
  "growth_rate": "number (percentage)",
  "category": "string",
  "region": "string",
  "collected_at": "ISO timestamp",
  "raw_data": "object (source-specific)",
  "metadata": "object (processed data)"
}
```

### Pagination Object
```json
{
  "total": "number",
  "limit": "number", 
  "offset": "number",
  "has_next": "boolean",
  "has_prev": "boolean"
}
```

### Task Status Object
```json
{
  "task_id": "string",
  "status": "pending|started|completed|failed",
  "progress": "number (0-100)",
  "message": "string",
  "started_at": "ISO timestamp",
  "completed_at": "ISO timestamp (if completed)",
  "error": "string (if failed)"
}
```

## Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "Invalid query parameters provided",
    "details": {
      "field": "min_score",
      "issue": "must be between 0 and 10"
    },
    "timestamp": "2024-09-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

## Rate Limiting

### Limits
- **Free Tier**: 100 requests/hour
- **Standard**: 1,000 requests/hour  
- **Premium**: 10,000 requests/hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1634567890
```

### Rate Limit Exceeded Response
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "retry_after": 3600,
    "limit": 1000,
    "window": "1 hour"
  }
}
```

## Examples

### Python Example
```python
import requests
import json

# Authentication
auth_response = requests.post(
    "https://api.ai-content-factory.com/auth/login",
    json={"username": "user", "password": "pass"}
)
token = auth_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Get trending YouTube content about AI
response = requests.get(
    "https://api.ai-content-factory.com/trend-monitor/trends",
    headers=headers,
    params={
        "source": "youtube",
        "keywords": "ai",
        "min_score": 7,
        "limit": 10
    }
)

trends = response.json()["trends"]
for trend in trends:
    print(f"Topic: {trend['topic']}")
    print(f"Score: {trend['popularity_score']}")
    print(f"Growth: {trend['growth_rate']}%")
    print("---")
```

### JavaScript Example
```javascript
const API_BASE = 'https://api.ai-content-factory.com/trend-monitor';

class TrendMonitorClient {
  constructor(token) {
    this.token = token;
  }

  async getTrends(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${API_BASE}/trends?${params}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async collectTrends() {
    const response = await fetch(`${API_BASE}/trends/collect`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return await response.json();
  }
}

// Usage
const client = new TrendMonitorClient('your_jwt_token');
const trends = await client.getTrends({
  source: 'youtube',
  category: 'technology',
  min_score: 7
});
```

### cURL Examples
```bash
# Get authentication token
curl -X POST https://api.ai-content-factory.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Get trends
curl -X GET "https://api.ai-content-factory.com/trend-monitor/trends?source=youtube&min_score=7" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Trigger collection
curl -X POST https://api.ai-content-factory.com/trend-monitor/trends/collect \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get analytics
curl -X GET "https://api.ai-content-factory.com/trend-monitor/trends/analytics/summary?timeframe=24h" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## WebSocket API

For real-time trend updates, connect to the WebSocket endpoint:

```javascript
const ws = new WebSocket('wss://api.ai-content-factory.com/trend-monitor/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'new_trend':
      console.log('New trend detected:', data.trend);
      break;
    case 'trend_update':
      console.log('Trend updated:', data.trend);
      break;
    case 'collection_complete':
      console.log('Collection completed:', data.summary);
      break;
  }
};

// Subscribe to specific categories
ws.send(JSON.stringify({
  action: 'subscribe',
  categories: ['technology', 'lifestyle']
}));
```

---

This API provides comprehensive access to trend monitoring capabilities with real-time updates, flexible filtering, and detailed analytics to power content creation decisions.