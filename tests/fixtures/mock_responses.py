"""
Mock API Responses
==================

This module contains mock responses for various external APIs
used in testing to ensure consistent and predictable test behavior.

Includes mocks for:
- YouTube Data API
- Google Trends API  
- OpenAI/ChatGPT API
- Claude API
- TikTok API
- Instagram API
- Facebook Graph API
- Twitter API
- Reddit API
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta
import uuid
import random

class MockYouTubeAPI:
    """Mock responses for YouTube Data API."""
    
    @staticmethod
    def trending_videos_response() -> Dict[str, Any]:
        """Mock response for trending videos endpoint."""
        return {
            "kind": "youtube#videoListResponse",
            "etag": "mock_etag_12345",
            "nextPageToken": "CAUQAA",
            "regionCode": "US",
            "pageInfo": {
                "totalResults": 200,
                "resultsPerPage": 50
            },
            "items": [
                {
                    "kind": "youtube#video",
                    "etag": "mock_video_etag_1",
                    "id": "dQw4w9WgXcQ",
                    "snippet": {
                        "publishedAt": "2025-09-14T08:00:00Z",
                        "channelId": "UC_channel_mock_1",
                        "title": "AI Content Creation - The Ultimate Guide for 2025!",
                        "description": "Learn how AI is revolutionizing content creation with the latest tools and techniques. In this comprehensive guide, we'll explore...",
                        "thumbnails": {
                            "default": {
                                "url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
                                "width": 120,
                                "height": 90
                            },
                            "medium": {
                                "url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg", 
                                "width": 320,
                                "height": 180
                            },
                            "high": {
                                "url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                                "width": 480,
                                "height": 360
                            },
                            "standard": {
                                "url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/sddefault.jpg",
                                "width": 640,
                                "height": 480
                            },
                            "maxres": {
                                "url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
                                "width": 1280,
                                "height": 720
                            }
                        },
                        "channelTitle": "AI Creator Pro",
                        "tags": ["AI", "artificial intelligence", "content creation", "technology", "tutorial", "2025", "automation"],
                        "categoryId": "28",
                        "liveBroadcastContent": "none",
                        "defaultLanguage": "en",
                        "localized": {
                            "title": "AI Content Creation - The Ultimate Guide for 2025!",
                            "description": "Learn how AI is revolutionizing content creation..."
                        }
                    },
                    "statistics": {
                        "viewCount": "1250000",
                        "likeCount": "89500",
                        "dislikeCount": "1200",
                        "favoriteCount": "0",
                        "commentCount": "5670"
                    },
                    "contentDetails": {
                        "duration": "PT12M34S",
                        "dimension": "2d",
                        "definition": "hd",
                        "caption": "true",
                        "licensedContent": true,
                        "projection": "rectangular"
                    }
                },
                {
                    "kind": "youtube#video",
                    "etag": "mock_video_etag_2", 
                    "id": "aBc123XyZ",
                    "snippet": {
                        "publishedAt": "2025-09-13T15:30:00Z",
                        "channelId": "UC_channel_mock_2",
                        "title": "Machine Learning Explained in 5 Minutes (Beginner Friendly)",
                        "description": "Complete beginner's guide to machine learning! We break down complex concepts into simple, easy-to-understand explanations...",
                        "thumbnails": {
                            "high": {
                                "url": "https://i.ytimg.com/vi/aBc123XyZ/hqdefault.jpg",
                                "width": 480,
                                "height": 360
                            }
                        },
                        "channelTitle": "Tech Simplified",
                        "tags": ["machine learning", "AI", "beginner tutorial", "data science", "python", "education"],
                        "categoryId": "27",
                        "liveBroadcastContent": "none"
                    },
                    "statistics": {
                        "viewCount": "875000",
                        "likeCount": "67800",
                        "commentCount": "3450"
                    }
                },
                {
                    "kind": "youtube#video",
                    "etag": "mock_video_etag_3",
                    "id": "XyZ789AbC", 
                    "snippet": {
                        "publishedAt": "2025-09-12T20:15:00Z",
                        "channelId": "UC_channel_mock_3",
                        "title": "Remote Work Productivity Setup Tour - My $5000 Home Office",
                        "description": "Take a complete tour of my productivity-focused home office setup! I'll show you every piece of equipment, software, and system I use to stay productive working from home.",
                        "thumbnails": {
                            "high": {
                                "url": "https://i.ytimg.com/vi/XyZ789AbC/hqdefault.jpg",
                                "width": 480,
                                "height": 360
                            }
                        },
                        "channelTitle": "Productivity Master",
                        "tags": ["remote work", "home office", "productivity", "setup tour", "work from home", "office tour"],
                        "categoryId": "22",
                        "liveBroadcastContent": "none"
                    },
                    "statistics": {
                        "viewCount": "432000",
                        "likeCount": "28900",
                        "commentCount": "1890"
                    }
                }
            ]
        }
    
    @staticmethod
    def video_upload_response() -> Dict[str, Any]:
        """Mock response for video upload."""
        return {
            "kind": "youtube#video",
            "etag": "mock_upload_etag",
            "id": "uploaded_video_123456",
            "snippet": {
                "publishedAt": "2025-09-14T12:00:00Z",
                "channelId": "UC_test_channel",
                "title": "Test Upload - AI Content Creation",
                "description": "This is a test video upload for the AI content creation system.",
                "thumbnails": {
                    "default": {
                        "url": "https://i.ytimg.com/vi/uploaded_video_123456/default.jpg"
                    }
                },
                "channelTitle": "Test Channel",
                "tags": ["test", "upload", "AI", "content"],
                "categoryId": "22",
                "defaultLanguage": "en"
            },
            "status": {
                "uploadStatus": "uploaded",
                "privacyStatus": "public",
                "license": "youtube",
                "embeddable": True,
                "publicStatsViewable": True
            },
            "statistics": {
                "viewCount": "0",
                "likeCount": "0", 
                "commentCount": "0"
            }
        }
    
    @staticmethod
    def search_response(query: str) -> Dict[str, Any]:
        """Mock response for search endpoint."""
        return {
            "kind": "youtube#searchListResponse",
            "etag": "mock_search_etag",
            "nextPageToken": "CDIQAA",
            "regionCode": "US",
            "pageInfo": {
                "totalResults": 1000000,
                "resultsPerPage": 50
            },
            "items": [
                {
                    "kind": "youtube#searchResult",
                    "etag": "mock_search_item_etag",
                    "id": {
                        "kind": "youtube#video",
                        "videoId": f"search_{query.replace(' ', '_')}_123"
                    },
                    "snippet": {
                        "publishedAt": "2025-09-14T10:00:00Z",
                        "channelId": "UC_search_result_channel",
                        "title": f"How to Master {query.title()} in 2025",
                        "description": f"Complete guide to {query} with step-by-step instructions and real examples.",
                        "thumbnails": {
                            "high": {
                                "url": f"https://i.ytimg.com/vi/search_{query.replace(' ', '_')}_123/hqdefault.jpg"
                            }
                        },
                        "channelTitle": f"{query.title()} Expert",
                        "liveBroadcastContent": "none"
                    }
                }
            ]
        }

class MockGoogleTrendsAPI:
    """Mock responses for Google Trends (pytrends)."""
    
    @staticmethod
    def trending_searches() -> List[Dict[str, Any]]:
        """Mock trending searches response."""
        return [
            {
                "title": "AI content creation tools",
                "formattedTraffic": "500K+",
                "relatedQueries": [
                    "AI video generator",
                    "content automation tools", 
                    "AI writing assistant",
                    "automated content creation"
                ],
                "image": {
                    "newsUrl": "https://news.google.com/articles/ai-content-tools",
                    "imageUrl": "https://example.com/ai-tools-image.jpg"
                },
                "articles": [
                    {
                        "title": "Top 10 AI Content Creation Tools for 2025",
                        "timeAgo": "2 hours ago",
                        "source": "TechCrunch",
                        "url": "https://techcrunch.com/ai-content-tools-2025"
                    }
                ]
            },
            {
                "title": "machine learning for beginners",
                "formattedTraffic": "200K+",
                "relatedQueries": [
                    "machine learning tutorial",
                    "ML basics explained",
                    "python machine learning",
                    "data science beginner"
                ],
                "image": {
                    "newsUrl": "https://news.google.com/articles/ml-beginners-guide"
                }
            },
            {
                "title": "remote work productivity tips",
                "formattedTraffic": "150K+",
                "relatedQueries": [
                    "work from home setup",
                    "productivity hacks",
                    "remote work tools",
                    "home office organization"
                ]
            },
            {
                "title": "cryptocurrency investment strategy",
                "formattedTraffic": "300K+",
                "relatedQueries": [
                    "crypto trading tips",
                    "bitcoin investment",
                    "DeFi strategies",
                    "altcoin analysis"
                ]
            }
        ]
    
    @staticmethod
    def interest_over_time(keyword: str) -> Dict[str, Any]:
        """Mock interest over time data."""
        dates = []
        values = []
        
        # Generate 12 weeks of data
        base_date = datetime.now() - timedelta(weeks=12)
        base_interest = random.randint(40, 80)
        
        for week in range(12):
            date = base_date + timedelta(weeks=week)
            dates.append(date.strftime("%Y-%m-%d"))
            
            # Simulate trending pattern
            if week < 4:
                value = base_interest + random.randint(-5, 5)
            elif week < 8:
                value = base_interest + random.randint(5, 20)  # Growing trend
            else:
                value = base_interest + random.randint(15, 35)  # Peak trend
                
            values.append(max(0, min(100, value)))
        
        return {
            "date": dates,
            keyword: values,
            "isPartial": [False] * 11 + [True]  # Last data point is partial
        }
    
    @staticmethod
    def related_topics(keyword: str) -> Dict[str, Any]:
        """Mock related topics data."""
        topics_map = {
            "AI content creation": [
                {"topic": "Artificial Intelligence", "value": 100, "link": "/m/0mkz"},
                {"topic": "Video Editing Software", "value": 85, "link": "/m/02rnkmn"},
                {"topic": "Content Marketing", "value": 73, "link": "/m/025sb5z"},
                {"topic": "Social Media", "value": 67, "link": "/m/02y_9m3"},
                {"topic": "YouTube", "value": 58, "link": "/m/09jcvs"}
            ],
            "machine learning": [
                {"topic": "Python Programming", "value": 100, "link": "/m/05z1_"},
                {"topic": "Data Science", "value": 92, "link": "/m/06mq7"},
                {"topic": "Neural Network", "value": 78, "link": "/m/05s2h"},
                {"topic": "Deep Learning", "value": 71, "link": "/m/0h1fn8y"},
                {"topic": "Algorithm", "value": 65, "link": "/m/0gwr"}
            ]
        }
        
        topics = topics_map.get(keyword, [
            {"topic": f"{keyword.title()} Topic 1", "value": 100},
            {"topic": f"{keyword.title()} Topic 2", "value": 75},
            {"topic": f"{keyword.title()} Topic 3", "value": 50}
        ])
        
        return {
            "default": {
                "df": topics
            }
        }

class MockOpenAIAPI:
    """Mock responses for OpenAI API."""
    
    @staticmethod
    def chat_completion_response(content_type: str = "educational") -> Dict[str, Any]:
        """Mock ChatGPT completion response."""
        
        # Different responses based on content type
        responses = {
            "educational": {
                "content_type": "educational",
                "script": {
                    "hook": "Want to master AI tools in 2025? Here's everything you need to know!",
                    "main_content": "In this comprehensive guide, we'll explore the most powerful AI tools that are transforming content creation. From automated video editing to intelligent script writing, these tools will revolutionize your workflow.",
                    "cta": "If this helped streamline your content creation, hit subscribe for more AI productivity tips!"
                },
                "visual_plan": {
                    "style": "modern_professional",
                    "scenes": ["engaging_intro", "tool_demonstrations", "workflow_integration", "results_showcase", "call_to_action"],
                    "text_overlays": ["AI REVOLUTION", "PRODUCTIVITY BOOST", "GAME CHANGER", "SUBSCRIBE NOW"]
                },
                "audio_plan": {
                    "voice_style": "energetic_professional",
                    "background_music": "upbeat_inspiring",
                    "sound_effects": ["whoosh_transitions", "notification_sounds", "success_chimes"]
                },
                "platform_optimization": {
                    "title": "AI Tools That Will Change Your Content Creation Game Forever",
                    "description": "Discover the AI tools top creators use to produce viral content faster. Complete workflow included!",
                    "hashtags": ["#AITools", "#ContentCreation", "#Productivity", "#Automation"],
                    "thumbnail_concept": "Split screen showing overwhelmed vs empowered creator with bold AI text overlay"
                },
                "production_estimate": {
                    "time_minutes": 45,
                    "cost_baht": 32.50,
                    "complexity": "medium"
                }
            },
            "tutorial": {
                "content_type": "tutorial",
                "script": {
                    "hook": "Think this is too complicated? I'll break it down step-by-step in simple terms!",
                    "main_content": "Let's start with the basics and build your understanding gradually. I'll show you exactly how to implement each step with real examples.",
                    "cta": "Try this yourself and let me know your results in the comments!"
                },
                "visual_plan": {
                    "style": "educational_clean",
                    "scenes": ["concept_introduction", "step_by_step_demo", "common_mistakes", "final_results"],
                    "text_overlays": ["STEP 1", "STEP 2", "STEP 3", "YOU DID IT!"]
                },
                "audio_plan": {
                    "voice_style": "calm_educational",
                    "background_music": "subtle_focus",
                    "sound_effects": ["gentle_transitions", "achievement_sounds"]
                },
                "platform_optimization": {
                    "title": "Complete Beginner's Guide - Step by Step Tutorial",
                    "description": "Learn from scratch with this comprehensive step-by-step guide. Perfect for beginners!",
                    "hashtags": ["#Tutorial", "#Beginner", "#StepByStep", "#Education"],
                    "thumbnail_concept": "Before and after transformation with clear step numbers"
                },
                "production_estimate": {
                    "time_minutes": 35,
                    "cost_baht": 25.00,
                    "complexity": "low"
                }
            }
        }
        
        selected_response = responses.get(content_type, responses["educational"])
        
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:10]}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(selected_response, indent=2)
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": random.randint(100, 300),
                "completion_tokens": random.randint(200, 500),
                "total_tokens": random.randint(300, 800)
            }
        }
    
    @staticmethod
    def image_generation_response() -> Dict[str, Any]:
        """Mock DALL-E image generation response."""
        return {
            "created": int(datetime.now().timestamp()),
            "data": [
                {
                    "url": f"https://oaidalleapiprodscus.blob.core.windows.net/private/mock-image-{uuid.uuid4().hex[:8]}.png?se=2025-09-15T12%3A00%3A00Z&sp=r&sv=2021-08-06&sr=b&rscc=max-age%3D31536000&rscd=attachment%3Bfilename%3Dmock_generated_image.png"
                }
            ]
        }

class MockClaudeAPI:
    """Mock responses for Anthropic Claude API."""
    
    @staticmethod
    def message_response(content_type: str = "educational") -> Dict[str, Any]:
        """Mock Claude message response."""
        
        premium_responses = {
            "educational": {
                "content_type": "educational",
                "script": {
                    "hook": "Ready to discover the AI revolution that's transforming content creation? Let me show you the tools that industry leaders are using to create viral content at unprecedented speed.",
                    "main_content": "In this comprehensive deep-dive, we'll explore five cutting-edge AI tools that represent the future of content creation. Each tool has been carefully selected based on real-world performance data and creator feedback. First, we'll examine advanced video generation platforms that can create Hollywood-quality visuals from simple text descriptions. Then we'll dive into sophisticated AI writing systems that understand context, tone, and audience psychology. We'll also explore revolutionary voice synthesis technology, intelligent design automation, and strategic social media optimization tools.",
                    "cta": "If you're serious about scaling your content creation and staying ahead of the curve, make sure to subscribe and activate notifications. The creators who adopt these tools early will dominate their niches."
                },
                "visual_plan": {
                    "style": "cinematic_professional",
                    "scenes": [
                        "dramatic_hook_sequence",
                        "industry_data_visualization", 
                        "advanced_tool_demonstrations",
                        "creator_success_stories",
                        "future_predictions",
                        "strategic_call_to_action"
                    ],
                    "text_overlays": [
                        "THE AI REVOLUTION IS HERE",
                        "5 GAME-CHANGING TOOLS",
                        "INDUSTRY SECRETS REVEALED",
                        "EARLY ADOPTER ADVANTAGE",
                        "DOMINATE YOUR NICHE"
                    ]
                },
                "audio_plan": {
                    "voice_style": "authoritative_premium",
                    "background_music": "cinematic_inspiring_orchestral",
                    "sound_effects": [
                        "epic_transitions",
                        "data_visualization_sounds", 
                        "premium_notification_chimes",
                        "suspense_building_elements"
                    ]
                },
                "platform_optimization": {
                    "title": "5 AI Tools Industry Leaders Use to Create Viral Content (Insider Secrets Revealed)",
                    "description": "Discover the premium AI tools that top creators and agencies use to produce viral content at scale. This isn't about basic tools - these are the professional-grade systems that are reshaping the industry. Includes exclusive case studies and ROI analysis.",
                    "hashtags": [
                        "#AIContentCreation",
                        "#PremiumTools", 
                        "#IndustrySecrets",
                        "#ViralContent",
                        "#ContentStrategy"
                    ],
                    "thumbnail_concept": "Professional creator in modern studio with holographic AI elements and premium gold accents. Expression of confident expertise."
                },
                "production_estimate": {
                    "time_minutes": 90,
                    "cost_baht": 65.00,
                    "complexity": "high"
                }
            }
        }
        
        response_content = premium_responses.get(content_type, premium_responses["educational"])
        
        return {
            "id": f"msg_{uuid.uuid4().hex[:10]}",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(response_content, indent=2)
                }
            ],
            "model": "claude-3-opus-20240229",
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": random.randint(150, 400),
                "output_tokens": random.randint(300, 800)
            }
        }

class MockTikTokAPI:
    """Mock responses for TikTok API."""
    
    @staticmethod
    def upload_response() -> Dict[str, Any]:
        """Mock TikTok video upload response."""
        return {
            "data": {
                "video": {
                    "id": f"tiktok_video_{uuid.uuid4().hex[:8]}",
                    "title": "Test TikTok Upload",
                    "embed_html": "<blockquote class=\"tiktok-embed\"...",
                    "embed_link": f"https://tiktok.com/embed/v2/{uuid.uuid4().hex[:8]}",
                    "cover_image_url": f"https://p16-sign-va.tiktokcdn.com/mock-cover-{uuid.uuid4().hex[:8]}.jpeg",
                    "share_url": f"https://vm.tiktok.com/{uuid.uuid4().hex[:8]}",
                    "create_time": int(datetime.now().timestamp()),
                    "duration": 60,
                    "height": 1024,
                    "width": 576,
                    "like_count": 0,
                    "comment_count": 0,
                    "share_count": 0,
                    "view_count": 0
                }
            },
            "error": {
                "code": "ok",
                "message": "",
                "log_id": f"20250914120000{random.randint(1000000, 9999999)}"
            }
        }
    
    @staticmethod
    def video_info_response(video_id: str) -> Dict[str, Any]:
        """Mock TikTok video info response."""
        return {
            "data": {
                "videos": [
                    {
                        "id": video_id,
                        "title": "AI Content Creation Tips 🤖",
                        "cover_image_url": f"https://p16-sign-va.tiktokcdn.com/mock-cover-{video_id}.jpeg",
                        "share_url": f"https://vm.tiktok.com/{video_id}",
                        "video_description": "5 AI tools that will change your content game! #AITools #ContentCreator #TechTok",
                        "duration": 59,
                        "create_time": int((datetime.now() - timedelta(hours=2)).timestamp()),
                        "username": "testcreator2025",
                        "region_code": "US",
                        "video_view_count": random.randint(1000, 100000),
                        "like_count": random.randint(50, 5000),
                        "comment_count": random.randint(10, 500),
                        "share_count": random.randint(5, 200),
                        "download_count": random.randint(20, 1000)
                    }
                ]
            }
        }
    
    @staticmethod
    def user_info_response() -> Dict[str, Any]:
        """Mock TikTok user info response."""
        return {
            "data": {
                "user": {
                    "open_id": f"mock_open_id_{uuid.uuid4().hex[:8]}",
                    "union_id": f"mock_union_id_{uuid.uuid4().hex[:8]}",
                    "avatar_url": "https://p16-sign-va.tiktokcdn.com/mock-avatar.jpeg",
                    "avatar_url_100": "https://p16-sign-va.tiktokcdn.com/mock-avatar-100.jpeg",
                    "avatar_large_url": "https://p16-sign-va.tiktokcdn.com/mock-avatar-large.jpeg",
                    "display_name": "AI Content Creator",
                    "bio_description": "Teaching creators how to use AI tools 🤖 | 500K+ students",
                    "profile_deep_link": "https://tiktok.com/@testcreator2025",
                    "is_verified": False,
                    "follower_count": random.randint(10000, 1000000),
                    "following_count": random.randint(100, 5000),
                    "likes_count": random.randint(50000, 5000000),
                    "video_count": random.randint(50, 500)
                }
            }
        }

class MockInstagramAPI:
    """Mock responses for Instagram Basic Display API."""
    
    @staticmethod
    def media_upload_response() -> Dict[str, Any]:
        """Mock Instagram media upload response."""
        return {
            "id": f"instagram_media_{uuid.uuid4().hex[:8]}",
            "media_type": "VIDEO",
            "media_url": f"https://scontent-sjc3-1.cdninstagram.com/v/mock-video-{uuid.uuid4().hex[:8]}.mp4",
            "permalink": f"https://www.instagram.com/p/{uuid.uuid4().hex[:8]}/",
            "thumbnail_url": f"https://scontent-sjc3-1.cdninstagram.com/v/mock-thumbnail-{uuid.uuid4().hex[:8]}.jpg",
            "timestamp": datetime.now().isoformat(),
            "username": "testcreator2025",
            "caption": "New AI tools that are changing the game! 🚀 #AITools #ContentCreator #TechTips",
            "like_count": random.randint(100, 10000),
            "comments_count": random.randint(10, 500),
            "media_product_type": "REELS"
        }
    
    @staticmethod
    def user_media_response() -> Dict[str, Any]:
        """Mock user media list response."""
        media_items = []
        
        for i in range(12):  # Return 12 recent posts
            media_items.append({
                "id": f"media_{uuid.uuid4().hex[:8]}",
                "media_type": random.choice(["IMAGE", "VIDEO", "CAROUSEL_ALBUM"]),
                "media_url": f"https://scontent-sjc3-1.cdninstagram.com/v/mock-media-{i}.jpg",
                "permalink": f"https://www.instagram.com/p/mock{i}/",
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "caption": f"Mock Instagram post #{i+1} #ContentCreator #AI",
                "like_count": random.randint(500, 15000),
                "comments_count": random.randint(20, 300)
            })
        
        return {
            "data": media_items,
            "paging": {
                "cursors": {
                    "before": "mock_before_cursor",
                    "after": "mock_after_cursor"
                },
                "next": "https://graph.instagram.com/v18.0/mock_user_id/media?after=mock_after_cursor"
            }
        }

class MockFacebookAPI:
    """Mock responses for Facebook Graph API."""
    
    @staticmethod
    def page_videos_upload_response() -> Dict[str, Any]:
        """Mock Facebook video upload response."""
        return {
            "id": f"facebook_video_{uuid.uuid4().hex[:8]}",
            "post_id": f"page_id_{random.randint(100000000000000, 999999999999999)}",
            "permalink_url": f"https://facebook.com/page/videos/{uuid.uuid4().hex[:8]}",
            "created_time": datetime.now().isoformat(),
            "description": "New AI tools for content creators! Check out these game-changing technologies.",
            "title": "5 AI Tools That Will Transform Your Content Creation",
            "status": {
                "video_status": "ready",
                "processing_progress": 100
            },
            "views": random.randint(100, 5000),
            "length": random.uniform(30, 600),  # Duration in seconds
            "source": f"https://video.xx.fbcdn.net/v/mock-video-{uuid.uuid4().hex[:8]}.mp4"
        }
    
    @staticmethod
    def page_insights_response() -> Dict[str, Any]:
        """Mock Facebook page insights response."""
        return {
            "data": [
                {
                    "name": "page_video_views",
                    "period": "day",
                    "values": [
                        {
                            "value": random.randint(1000, 10000),
                            "end_time": (datetime.now() - timedelta(days=1)).isoformat()
                        },
                        {
                            "value": random.randint(1000, 10000), 
                            "end_time": datetime.now().isoformat()
                        }
                    ]
                },
                {
                    "name": "page_video_view_time",
                    "period": "day",
                    "values": [
                        {
                            "value": random.randint(10000, 100000),  # Total view time in seconds
                            "end_time": datetime.now().isoformat()
                        }
                    ]
                }
            ]
        }

class MockTwitterAPI:
    """Mock responses for Twitter API v2."""
    
    @staticmethod
    def tweet_search_response(query: str) -> Dict[str, Any]:
        """Mock Twitter search response."""
        tweets = []
        
        for i in range(10):
            tweet_id = f"tweet_{uuid.uuid4().hex[:8]}"
            tweets.append({
                "id": tweet_id,
                "text": f"🚀 {query} is trending! Here's what you need to know about this game-changing technology. Thread 1/{random.randint(3, 8)} 👇",
                "author_id": f"user_{uuid.uuid4().hex[:8]}",
                "created_at": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                "public_metrics": {
                    "retweet_count": random.randint(10, 1000),
                    "like_count": random.randint(50, 5000),
                    "reply_count": random.randint(5, 200),
                    "quote_count": random.randint(2, 100)
                },
                "context_annotations": [
                    {
                        "domain": {
                            "id": "66",
                            "name": "Technology",
                            "description": "Technology and computing"
                        },
                        "entity": {
                            "id": f"entity_{random.randint(1000000, 9999999)}",
                            "name": query.title()
                        }
                    }
                ]
            })
        
        return {
            "data": tweets,
            "meta": {
                "newest_id": tweets[0]["id"],
                "oldest_id": tweets[-1]["id"],
                "result_count": len(tweets),
                "next_token": f"next_token_{uuid.uuid4().hex[:8]}"
            }
        }
    
    @staticmethod
    def trending_topics_response() -> Dict[str, Any]:
        """Mock Twitter trending topics response."""
        return {
            "data": [
                {
                    "trend": "AI Content Creation",
                    "tweet_volume": random.randint(50000, 200000),
                    "rank": 1
                },
                {
                    "trend": "Machine Learning",
                    "tweet_volume": random.randint(30000, 150000),
                    "rank": 2
                },
                {
                    "trend": "Remote Work",
                    "tweet_volume": random.randint(40000, 120000),
                    "rank": 3
                },
                {
                    "trend": "Cryptocurrency",
                    "tweet_volume": random.randint(60000, 300000),
                    "rank": 4
                },
                {
                    "trend": "Productivity Hacks",
                    "tweet_volume": random.randint(20000, 80000),
                    "rank": 5
                }
            ]
        }

class MockRedditAPI:
    """Mock responses for Reddit API."""
    
    @staticmethod
    def subreddit_hot_posts_response(subreddit: str) -> Dict[str, Any]:
        """Mock Reddit hot posts response."""
        posts = []
        
        for i in range(25):
            post_id = f"post_{uuid.uuid4().hex[:6]}"
            posts.append({
                "kind": "t3",
                "data": {
                    "id": post_id,
                    "title": f"Amazing {subreddit.replace('r/', '')} tip that changed my life",
                    "selftext": f"I've been working with {subreddit.replace('r/', '')} for years, and this technique has completely transformed my approach...",
                    "author": f"user_{uuid.uuid4().hex[:6]}",
                    "subreddit": subreddit.replace("r/", ""),
                    "subreddit_name_prefixed": subreddit,
                    "score": random.randint(500, 15000),
                    "upvote_ratio": round(random.uniform(0.7, 0.98), 2),
                    "num_comments": random.randint(50, 800),
                    "created_utc": (datetime.now() - timedelta(hours=random.randint(1, 48))).timestamp(),
                    "url": f"https://reddit.com/r/{subreddit.replace('r/', '')}/comments/{post_id}/",
                    "permalink": f"/r/{subreddit.replace('r/', '')}/comments/{post_id}/",
                    "is_video": random.choice([True, False]),
                    "domain": "self." + subreddit.replace("r/", "") if random.choice([True, False]) else "youtube.com",
                    "gilded": random.randint(0, 3),
                    "awards": random.randint(0, 10)
                }
            })
        
        return {
            "kind": "Listing",
            "data": {
                "modhash": "",
                "dist": 25,
                "children": posts,
                "after": f"t3_{uuid.uuid4().hex[:6]}",
                "before": None
            }
        }
    
    @staticmethod
    def search_posts_response(query: str) -> Dict[str, Any]:
        """Mock Reddit search response."""
        return {
            "kind": "Listing",
            "data": {
                "children": [
                    {
                        "kind": "t3",
                        "data": {
                            "id": f"search_{uuid.uuid4().hex[:6]}",
                            "title": f"Comprehensive guide to {query} - Everything you need to know",
                            "selftext": f"After months of research and testing, here's my complete guide to {query}...",
                            "author": "expert_user_2025",
                            "subreddit": query.replace(" ", "").lower(),
                            "score": random.randint(1000, 8000),
                            "num_comments": random.randint(100, 500),
                            "created_utc": (datetime.now() - timedelta(days=random.randint(1, 30))).timestamp(),
                            "url": f"https://reddit.com/r/{query.replace(' ', '').lower()}/comments/guide/",
                            "upvote_ratio": 0.95,
                            "gilded": 2
                        }
                    }
                ]
            }
        }

# Utility functions for creating dynamic mock responses
def create_mock_trend_response(topic: str, popularity: float, source: str = "youtube") -> Dict[str, Any]:
    """Create a mock trend response with custom data."""
    return {
        "id": f"trend_{uuid.uuid4().hex[:8]}",
        "topic": topic,
        "source": source,
        "popularity_score": popularity,
        "growth_rate": max(0, (popularity - 50) / 5),  # Higher popularity = higher growth
        "keywords": topic.lower().replace(",", "").split(),
        "category": "Technology" if "AI" in topic or "tech" in topic.lower() else "General",
        "region": "Global",
        "collected_at": datetime.utcnow().isoformat(),
        "raw_data": {
            "search_volume": int(popularity * 1000),
            "competition": "medium",
            "engagement_rate": round(popularity / 20, 1)
        }
    }

def create_mock_ai_content_response(
    content_type: str = "educational",
    complexity: str = "medium",
    platform_focus: str = "youtube"
) -> str:
    """Create a mock AI response in JSON format for content generation."""
    
    complexity_settings = {
        "low": {
            "scenes": 3,
            "overlays": 2,
            "effects": 1,
            "time": 20,
            "cost": 15
        },
        "medium": {
            "scenes": 5,
            "overlays": 4,
            "effects": 3,
            "time": 35,
            "cost": 25
        },
        "high": {
            "scenes": 8,
            "overlays": 6,
            "effects": 5,
            "time": 60,
            "cost": 45
        }
    }
    
    settings = complexity_settings[complexity]
    
    response = {
        "content_type": content_type,
        "script": {
            "hook": f"Amazing {content_type} content hook that grabs attention!",
            "main_content": f"This is comprehensive {content_type} content that provides real value to viewers. We'll cover the most important aspects and give actionable insights.",
            "cta": f"If this {content_type} content helped you, don't forget to subscribe and hit the notification bell!"
        },
        "visual_plan": {
            "style": f"{complexity}_professional",
            "scenes": [f"scene_{i+1}" for i in range(settings["scenes"])],
            "text_overlays": [f"overlay_{i+1}" for i in range(settings["overlays"])]
        },
        "audio_plan": {
            "voice_style": "professional_engaging",
            "background_music": "upbeat" if content_type == "educational" else "subtle",
            "sound_effects": [f"effect_{i+1}" for i in range(settings["effects"])]
        },
        "platform_optimization": {
            "title": f"Ultimate {content_type.title()} Guide for {platform_focus.title()}",
            "description": f"Complete {content_type} guide optimized for {platform_focus}",
            "hashtags": [f"#{content_type}", f"#{platform_focus}", "#tutorial", "#guide"],
            "thumbnail_concept": f"{content_type.title()} focused design with {complexity} complexity"
        },
        "production_estimate": {
            "time_minutes": settings["time"],
            "cost_baht": settings["cost"],
            "complexity": complexity
        }
    }
    
    return json.dumps(response, indent=2)

# Error response mocks for testing error handling
class MockErrorResponses:
    """Mock error responses for testing error handling."""
    
    @staticmethod
    def youtube_quota_exceeded() -> Dict[str, Any]:
        return {
            "error": {
                "code": 403,
                "message": "The request cannot be completed because you have exceeded your quota.",
                "errors": [
                    {
                        "message": "The request cannot be completed because you have exceeded your quota.",
                        "domain": "youtube.quota",
                        "reason": "quotaExceeded"
                    }
                ]
            }
        }
    
    @staticmethod
    def tiktok_rate_limit() -> Dict[str, Any]:
        return {
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Rate limit exceeded. Please try again later.",
                "log_id": f"20250914{random.randint(100000000, 999999999)}"
            }
        }
    
    @staticmethod
    def openai_server_error() -> Dict[str, Any]:
        return {
            "error": {
                "message": "The server had an error while processing your request. Sorry about that!",
                "type": "server_error",
                "param": None,
                "code": None
            }
        }
    
    @staticmethod
    def instagram_invalid_token() -> Dict[str, Any]:
        return {
            "error": {
                "message": "Invalid access token",
                "type": "OAuthException",
                "code": 190,
                "fbtrace_id": f"mock_trace_{uuid.uuid4().hex[:8]}"
            }
        }
    
    @staticmethod
    def generic_network_error() -> Exception:
        """Create a generic network error exception."""
        return Exception("Network connection failed - unable to reach API endpoint")
    
    @staticmethod
    def timeout_error() -> Exception:
        """Create a timeout error exception."""
        return Exception("Request timed out after 30 seconds")

# Performance testing mock responses
class MockPerformanceData:
    """Mock performance data for testing analytics and tracking."""
    
    @staticmethod
    def youtube_analytics_response(video_id: str) -> Dict[str, Any]:
        """Mock YouTube analytics data."""
        return {
            "kind": "youtubeAnalytics#resultTable",
            "columnHeaders": [
                {"name": "day", "columnType": "DIMENSION", "dataType": "STRING"},
                {"name": "views", "columnType": "METRIC", "dataType": "INTEGER"},
                {"name": "likes", "columnType": "METRIC", "dataType": "INTEGER"},
                {"name": "comments", "columnType": "METRIC", "dataType": "INTEGER"},
                {"name": "shares", "columnType": "METRIC", "dataType": "INTEGER"},
                {"name": "estimatedRevenue", "columnType": "METRIC", "dataType": "FLOAT"}
            ],
            "rows": [
                [
                    "2025-09-14",
                    random.randint(5000, 50000),
                    random.randint(250, 2500),
                    random.randint(50, 500),
                    random.randint(25, 250),
                    round(random.uniform(10.0, 100.0), 2)
                ],
                [
                    "2025-09-13", 
                    random.randint(3000, 30000),
                    random.randint(150, 1500),
                    random.randint(30, 300),
                    random.randint(15, 150),
                    round(random.uniform(5.0, 50.0), 2)
                ]
            ]
        }
    
    @staticmethod
    def social_media_performance_summary() -> Dict[str, Any]:
        """Mock cross-platform performance summary."""
        return {
            "youtube": {
                "views": random.randint(10000, 100000),
                "likes": random.randint(500, 5000),
                "comments": random.randint(100, 1000),
                "shares": random.randint(50, 500),
                "revenue": round(random.uniform(50.0, 500.0), 2),
                "ctr": round(random.uniform(0.03, 0.12), 3),
                "retention_rate": round(random.uniform(0.4, 0.8), 2)
            },
            "tiktok": {
                "views": random.randint(25000, 500000),
                "likes": random.randint(1000, 25000),
                "comments": random.randint(200, 2500),
                "shares": random.randint(500, 5000),
                "completion_rate": round(random.uniform(0.6, 0.9), 2)
            },
            "instagram": {
                "views": random.randint(8000, 80000),
                "likes": random.randint(400, 4000),
                "comments": random.randint(80, 800),
                "saves": random.randint(200, 2000),
                "reach": random.randint(15000, 150000),
                "engagement_rate": round(random.uniform(0.03, 0.08), 3)
            }
        }

if __name__ == "__main__":
    # Test the mock responses
    print("=== Testing Mock Responses ===")
    
    # Test YouTube API
    print("\n1. YouTube Trending Videos:")
    yt_response = MockYouTubeAPI.trending_videos_response()
    print(f"Found {len(yt_response['items'])} trending videos")
    
    # Test OpenAI API  
    print("\n2. OpenAI Chat Completion:")
    openai_response = MockOpenAIAPI.chat_completion_response("educational")
    content = json.loads(openai_response['choices'][0]['message']['content'])
    print(f"Generated {content['content_type']} content plan")
    
    # Test Google Trends
    print("\n3. Google Trends:")
    trends = MockGoogleTrendsAPI.trending_searches()
    print(f"Found {len(trends)} trending topics")
    
    # Test TikTok API
    print("\n4. TikTok Upload:")
    tiktok_response = MockTikTokAPI.upload_response()
    print(f"TikTok video ID: {tiktok_response['data']['video']['id']}")
    
    # Test custom trend generation
    print("\n5. Custom Trend Generation:")
    custom_trend = create_mock_trend_response("AI Video Editing", 85.5, "youtube")
    print(f"Created trend: {custom_trend['topic']} (Score: {custom_trend['popularity_score']})")
    
    print("\n=== All Mock Responses Working! ===")