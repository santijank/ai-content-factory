#!/usr/bin/env python3
"""
YouTube Data API Setup and Testing
แนะนำการใช้ YouTube API สำหรับเก็บข้อมูล trending videos
"""

def install_requirements():
    """ติดตั้ง packages ที่จำเป็น"""
    print("📦 ติดตั้ง YouTube API dependencies...")
    
    requirements = """
pip install google-api-python-client
pip install google-auth-oauthlib
pip install google-auth-httplib2
"""
    
    print("คำสั่งการติดตั้ง:")
    print(requirements)
    
    with open('install_youtube_api.bat', 'w') as f:
        f.write('''@echo off
echo Installing YouTube API dependencies...
pip install google-api-python-client
pip install google-auth-oauthlib  
pip install google-auth-httplib2
echo Done!
pause
''')
    
    print("✅ สร้างไฟล์ install_youtube_api.bat")

def create_youtube_api_example():
    """สร้างตัวอย่างการใช้ YouTube API"""
    
    code = '''#!/usr/bin/env python3
"""
YouTube Data API - Real Implementation
ดึงข้อมูล trending videos จาก YouTube
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from datetime import datetime
import json

class YouTubeTrendCollector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_trending_videos(self, region_code='US', max_results=50):
        """ดึง trending videos"""
        try:
            print(f"🔍 ดึง trending videos จาก {region_code}...")
            
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                chart='mostPopular',
                regionCode=region_code,
                maxResults=max_results,
                videoCategoryId='0'  # All categories
            )
            
            response = request.execute()
            
            trending_videos = []
            for item in response['items']:
                video_data = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'category_id': item['snippet']['categoryId'],
                    'tags': item['snippet'].get('tags', []),
                    'description': item['snippet']['description'][:500]  # First 500 chars
                }
                trending_videos.append(video_data)
            
            print(f"✅ ดึงข้อมูลได้ {len(trending_videos)} videos")
            return trending_videos
            
        except HttpError as e:
            print(f"❌ YouTube API Error: {e}")
            return []
        except Exception as e:
            print(f"❌ General Error: {e}")
            return []
    
    def get_video_categories(self, region_code='US'):
        """ดึงรายการ video categories"""
        try:
            request = self.youtube.videoCategories().list(
                part='snippet',
                regionCode=region_code
            )
            
            response = request.execute()
            
            categories = {}
            for item in response['items']:
                categories[item['id']] = item['snippet']['title']
            
            return categories
            
        except Exception as e:
            print(f"❌ Categories Error: {e}")
            return {}
    
    def search_trending_topics(self, query, max_results=25):
        """ค้นหาวิดีโอตาม topic"""
        try:
            print(f"🔎 ค้นหา: {query}")
            
            request = self.youtube.search().list(
                part='snippet',
                q=query,
                type='video',
                order='relevance',
                publishedAfter='2024-01-01T00:00:00Z',
                maxResults=max_results
            )
            
            response = request.execute()
            
            search_results = []
            for item in response['items']:
                video_data = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'description': item['snippet']['description'][:200]
                }
                search_results.append(video_data)
            
            print(f"✅ พบ {len(search_results)} videos")
            return search_results
            
        except Exception as e:
            print(f"❌ Search Error: {e}")
            return []

def test_with_sample_key():
    """ทดสอบโดยไม่ใช้ API key จริง"""
    print("🧪 ทดสอบ YouTube API (Sample Data)")
    print("=" * 50)
    
    # Sample trending data
    sample_trending = [
        {
            'video_id': 'dQw4w9WgXcQ',
            'title': 'How to Use AI for Content Creation 2024',
            'channel': 'TechChannel',
            'view_count': 1500000,
            'like_count': 75000,
            'category_id': '28',  # Science & Technology
            'tags': ['AI', 'Content', 'Tutorial', '2024']
        },
        {
            'video_id': 'sample123',
            'title': 'Top 10 YouTube Growth Hacks',
            'channel': 'CreatorTips',
            'view_count': 890000,
            'like_count': 42000,
            'category_id': '22',  # People & Blogs
            'tags': ['YouTube', 'Growth', 'Tips', 'Creator']
        },
        {
            'video_id': 'sample456',
            'title': 'React to Viral TikTok Trends',
            'channel': 'TrendWatcher',
            'view_count': 2300000,
            'like_count': 125000,
            'category_id': '24',  # Entertainment
            'tags': ['TikTok', 'Viral', 'Trends', 'React']
        }
    ]
    
    print("📊 Sample Trending Videos:")
    for i, video in enumerate(sample_trending, 1):
        print(f"{i}. {video['title']}")
        print(f"   Channel: {video['channel']}")
        print(f"   Views: {video['view_count']:,}")
        print(f"   Likes: {video['like_count']:,}")
        print(f"   Tags: {', '.join(video['tags'])}")
        print()
    
    return sample_trending

def test_with_real_api():
    """ทดสอบด้วย API key จริง"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key or api_key == 'your_youtube_api_key_here':
        print("⚠️ ไม่พบ YouTube API Key")
        print("กรุณาเพิ่ม YOUTUBE_API_KEY ในไฟล์ .env")
        print()
        return test_with_sample_key()
    
    print("🎯 ใช้ YouTube API จริง")
    print("=" * 50)
    
    collector = YouTubeTrendCollector(api_key)
    
    # ทดสอบ trending videos
    trending = collector.get_trending_videos(region_code='US', max_results=10)
    
    if trending:
        print("📈 Top Trending Videos:")
        for i, video in enumerate(trending[:5], 1):
            print(f"{i}. {video['title'][:60]}...")
            print(f"   Views: {video['view_count']:,}")
            print(f"   Channel: {video['channel']}")
        
        return trending
    else:
        print("❌ ไม่สามารถดึงข้อมูลได้")
        return test_with_sample_key()

def create_integration_example():
    """สร้างตัวอย่างการรวมเข้ากับระบบหลัก"""
    
    integration_code = '''#!/usr/bin/env python3
"""
Integration: YouTube API + AI Content Factory
รวม YouTube trending data เข้ากับระบบหลัก
"""

import sqlite3
from datetime import datetime
from youtube_api_example import YouTubeTrendCollector
import os

def integrate_youtube_data():
    """รวม YouTube data เข้า database"""
    
    # เชื่อมต่อ database
    conn = sqlite3.connect('content_factory.db')
    cursor = conn.cursor()
    
    # YouTube API
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("⚠️ ใช้ sample data แทน")
        return add_sample_trends_to_db(conn, cursor)
    
    collector = YouTubeTrendCollector(api_key)
    
    # ดึง trending videos
    trending_videos = collector.get_trending_videos(max_results=20)
    
    # แปลงเป็น trends data
    trends_added = 0
    for video in trending_videos:
        try:
            # สร้าง trend ID
            trend_id = f"yt_{video['video_id']}"
            
            # คำนวณ popularity score (0-100)
            popularity_score = min(100, (video['view_count'] / 10000))
            
            # คำนวณ growth rate estimate
            growth_rate = min(50, (video['like_count'] / video['view_count'] * 1000))
            
            # Insert เข้า database
            cursor.execute('''
                INSERT OR REPLACE INTO trends 
                (id, source, topic, keywords, popularity_score, growth_rate, 
                 category, region, collected_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trend_id,
                'youtube',
                video['title'],
                ','.join(video.get('tags', [])[:5]),  # First 5 tags
                popularity_score,
                growth_rate,
                f"Category_{video.get('category_id', 'Unknown')}",
                'US',
                datetime.now(),
                str(video)  # Store full data as string
            ))
            
            trends_added += 1
            
        except Exception as e:
            print(f"❌ Error adding trend: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ เพิ่ม {trends_added} trends จาก YouTube")
    return trends_added

def add_sample_trends_to_db(conn, cursor):
    """เพิ่ม sample trends เมื่อไม่มี API key"""
    
    sample_trends = [
        ('yt_sample_1', 'youtube', 'AI Content Creation Tutorial 2024', 'AI,tutorial,content', 85.5, 15.2, 'Technology', 'US'),
        ('yt_sample_2', 'youtube', 'Viral TikTok Dance Challenge', 'viral,dance,tiktok', 92.3, 25.8, 'Entertainment', 'US'),
        ('yt_sample_3', 'youtube', 'Crypto Trading for Beginners', 'crypto,trading,finance', 78.1, 12.4, 'Finance', 'US')
    ]
    
    trends_added = 0
    for trend_data in sample_trends:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trends 
                (id, source, topic, keywords, popularity_score, growth_rate, 
                 category, region, collected_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*trend_data, datetime.now(), '{}'))
            trends_added += 1
        except:
            pass
    
    conn.commit()
    return trends_added

if __name__ == "__main__":
    integrate_youtube_data()
'''
    
    with open('youtube_integration.py', 'w', encoding='utf-8') as f:
        f.write(integration_code)
    
    print("✅ สร้างไฟล์ youtube_integration.py")

def main():
    """รันการ setup YouTube API"""
    print("🎬 YouTube Data API Setup")
    print("=" * 40)
    
    install_requirements()
    create_youtube_api_example()
    create_integration_example()
    
    print("\n📋 ขั้นตอนต่อไป:")
    print("1. รัน: install_youtube_api.bat")
    print("2. สมัคร YouTube API key จาก Google Cloud Console")
    print("3. เพิ่ม API key ในไฟล์ .env")
    print("4. ทดสอบ: python youtube_api_example.py")
    print("5. รวมเข้าระบบ: python youtube_integration.py")
    
    print("\n💰 ค่าใช้จ่าย: ฟรี 10,000 requests/วัน")
    print("📊 ข้อมูลที่ได้: trending videos, view counts, engagement data")

if __name__ == "__main__":
    main()