#!/usr/bin/env python3
"""
Simple YouTube API Setup
"""

def create_install_script():
    """สร้าง script สำหรับติดตั้ง dependencies"""
    install_script = '''@echo off
echo Installing YouTube API dependencies...
pip install google-api-python-client
pip install google-auth-oauthlib  
pip install google-auth-httplib2
echo Done!
pause
'''
    
    with open('install_youtube_api.bat', 'w') as f:
        f.write(install_script)
    
    print("Created install_youtube_api.bat")

def create_youtube_example():
    """สร้างตัวอย่างการใช้ YouTube API"""
    
    example_code = '''#!/usr/bin/env python3
"""
YouTube API Example
"""

import os
from datetime import datetime

# Sample data ถ้าไม่มี API key
def get_sample_youtube_data():
    """ข้อมูลตัวอย่างจาก YouTube"""
    sample_data = [
        {
            'title': 'How to Use AI for Content Creation 2024',
            'channel': 'TechChannel',
            'view_count': 1500000,
            'like_count': 75000,
            'tags': ['AI', 'Content', 'Tutorial', '2024']
        },
        {
            'title': 'Top 10 YouTube Growth Hacks',
            'channel': 'CreatorTips', 
            'view_count': 890000,
            'like_count': 42000,
            'tags': ['YouTube', 'Growth', 'Tips']
        },
        {
            'title': 'React to Viral TikTok Trends',
            'channel': 'TrendWatcher',
            'view_count': 2300000,
            'like_count': 125000,
            'tags': ['TikTok', 'Viral', 'Trends']
        }
    ]
    
    print("Sample YouTube Trending Data:")
    for i, video in enumerate(sample_data, 1):
        print(f"{i}. {video['title']}")
        print(f"   Views: {video['view_count']:,}")
        print(f"   Tags: {', '.join(video['tags'])}")
        print()
    
    return sample_data

def test_youtube_api():
    """ทดสอบ YouTube API"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key or api_key == 'your_youtube_api_key_here':
        print("No API key found, using sample data")
        return get_sample_youtube_data()
    
    try:
        from googleapiclient.discovery import build
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        request = youtube.videos().list(
            part='snippet,statistics',
            chart='mostPopular',
            regionCode='US',
            maxResults=10
        )
        
        response = request.execute()
        
        videos = []
        for item in response['items']:
            video = {
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'like_count': int(item['statistics'].get('likeCount', 0)),
            }
            videos.append(video)
        
        print("Real YouTube trending data retrieved!")
        return videos
        
    except ImportError:
        print("YouTube API library not installed")
        return get_sample_youtube_data()
    except Exception as e:
        print(f"API Error: {e}")
        return get_sample_youtube_data()

if __name__ == "__main__":
    test_youtube_api()
'''
    
    with open('youtube_example.py', 'w', encoding='utf-8') as f:
        f.write(example_code)
    
    print("Created youtube_example.py")

def create_integration():
    """สร้างไฟล์รวม YouTube เข้าระบบ"""
    
    integration_code = '''#!/usr/bin/env python3
"""
YouTube Integration with AI Content Factory
"""

import sqlite3
from datetime import datetime
import uuid

def integrate_youtube_trends():
    """รวม YouTube trends เข้า database"""
    
    # Sample YouTube trends
    youtube_trends = [
        {
            'title': 'AI Content Creation Tools 2024',
            'view_count': 1500000,
            'growth_rate': 15.2,
            'tags': ['AI', 'Content', 'Tools']
        },
        {
            'title': 'Viral YouTube Shorts Ideas',
            'view_count': 890000,
            'growth_rate': 25.8,
            'tags': ['YouTube', 'Shorts', 'Viral']
        },
        {
            'title': 'TikTok vs YouTube: Which is Better?',
            'view_count': 2300000,
            'growth_rate': 18.5,
            'tags': ['TikTok', 'YouTube', 'Comparison']
        }
    ]
    
    # Connect to database
    conn = sqlite3.connect('content_factory.db')
    cursor = conn.cursor()
    
    trends_added = 0
    for trend in youtube_trends:
        try:
            trend_id = f"yt_{uuid.uuid4().hex[:8]}"
            
            # Calculate popularity score
            popularity_score = min(100, trend['view_count'] / 50000)
            
            cursor.execute('''
                INSERT INTO trends 
                (id, source, topic, keywords, popularity_score, growth_rate, 
                 category, region, collected_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trend_id,
                'youtube',
                trend['title'],
                ','.join(trend['tags']),
                popularity_score,
                trend['growth_rate'],
                'Entertainment',
                'US',
                datetime.now(),
                str(trend)
            ))
            
            trends_added += 1
            
        except Exception as e:
            print(f"Error adding trend: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Added {trends_added} YouTube trends to database")
    return trends_added

if __name__ == "__main__":
    integrate_youtube_trends()
'''
    
    with open('youtube_integration.py', 'w', encoding='utf-8') as f:
        f.write(integration_code)
    
    print("Created youtube_integration.py")

def main():
    """รันการ setup"""
    print("YouTube API Setup")
    print("=" * 30)
    
    create_install_script()
    create_youtube_example()
    create_integration()
    
    print("\nNext steps:")
    print("1. Run: install_youtube_api.bat")
    print("2. Get YouTube API key from Google Cloud Console")
    print("3. Add to .env file: YOUTUBE_API_KEY=your_key")
    print("4. Test: python youtube_example.py")
    print("5. Integrate: python youtube_integration.py")

if __name__ == "__main__":
    main()