import requests
import json
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import os
import sys

# เพิ่ม path เพื่อ import จาก database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class YouTubeTrendsCollector:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    def get_trending_videos(self, region_code='TH', max_results=50):
        """ดึงวิดีโอที่กำลัง trending จาก YouTube"""
        try:
            url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet,statistics',
                'chart': 'mostPopular',
                'regionCode': region_code,
                'maxResults': max_results,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                trends = []
                
                for item in data.get('items', []):
                    trend = self.extract_trend_data(item, 'youtube')
                    trends.append(trend)
                
                print(f"✅ Retrieved {len(trends)} YouTube trends")
                return trends
            else:
                print(f"❌ YouTube API error: {response.status_code}")
                return self.get_mock_youtube_trends()  # fallback to mock data
                
        except Exception as e:
            print(f"❌ Error collecting YouTube trends: {e}")
            return self.get_mock_youtube_trends()
    
    def get_mock_youtube_trends(self):
        """สร้างข้อมูล mock สำหรับทดสอบ"""
        mock_trends = [
            {
                'source': 'youtube',
                'topic': 'AI Content Creation Tutorial',
                'popularity_score': 95.5,
                'growth_rate': 25.3,
                'category': 'Technology',
                'keywords': ['AI', 'content creation', 'automation', 'tutorial'],
                'raw_data': {
                    'views': 150000,
                    'likes': 12000,
                    'comments': 850,
                    'channel': 'Tech Tutorials TH'
                }
            },
            {
                'source': 'youtube',
                'topic': 'ChatGPT for Business',
                'popularity_score': 87.2,
                'growth_rate': 18.7,
                'category': 'Business',
                'keywords': ['ChatGPT', 'business', 'productivity', 'AI tools'],
                'raw_data': {
                    'views': 89000,
                    'likes': 7500,
                    'comments': 420,
                    'channel': 'Business AI'
                }
            },
            {
                'source': 'youtube',
                'topic': 'Python Automation Scripts',
                'popularity_score': 82.1,
                'growth_rate': 15.2,
                'category': 'Programming',
                'keywords': ['Python', 'automation', 'scripting', 'programming'],
                'raw_data': {
                    'views': 67000,
                    'likes': 5200,
                    'comments': 310,
                    'channel': 'Code Masters'
                }
            }
        ]
        
        print("📋 Using mock YouTube trends for testing")
        return mock_trends
    
    def extract_trend_data(self, youtube_item, source):
        """แปลงข้อมูลจาก YouTube API เป็นรูปแบบของเรา"""
        snippet = youtube_item.get('snippet', {})
        statistics = youtube_item.get('statistics', {})
        
        return {
            'source': source,
            'topic': snippet.get('title', 'Unknown Title'),
            'popularity_score': self.calculate_popularity_score(statistics),
            'growth_rate': 0,  # จะคำนวณจากการเปรียบเทียบข้อมูลเก่า
            'category': snippet.get('categoryId', 'General'),
            'keywords': self.extract_keywords(snippet.get('title', '') + ' ' + snippet.get('description', '')),
            'raw_data': {
                'video_id': youtube_item.get('id'),
                'channel_title': snippet.get('channelTitle'),
                'published_at': snippet.get('publishedAt'),
                'views': int(statistics.get('viewCount', 0)),
                'likes': int(statistics.get('likeCount', 0)),
                'comments': int(statistics.get('commentCount', 0)),
                'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url')
            }
        }
    
    def calculate_popularity_score(self, statistics):
        """คำนวณคะแนนความนิยมจาก YouTube statistics"""
        views = int(statistics.get('viewCount', 0))
        likes = int(statistics.get('likeCount', 0))
        comments = int(statistics.get('commentCount', 0))
        
        # สูตรคำนวณแบบง่าย (สามารถปรับได้)
        score = (views * 0.6 + likes * 30 + comments * 100) / 10000
        return min(score, 100)  # จำกัดไม่เกิน 100
    
    def extract_keywords(self, text):
        """สกัดคำสำคัญจาก title และ description"""
        # คำที่ไม่ต้องการ
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        
        # แปลงเป็นตัวพิมพ์เล็กและแยกคำ
        words = text.lower().replace(',', ' ').replace('.', ' ').split()
        
        # กรองคำที่มีความยาวมากกว่า 2 ตัวอักษร และไม่ใช่ stop words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # เอาเฉพาะ 10 คำแรก
        return keywords[:10]

class GoogleTrendsCollector:
    def __init__(self):
        self.base_url = "https://trends.google.com/trends/api"
    
    def get_trending_topics(self, geo='TH'):
        """ดึงหัวข้อที่กำลัง trending จาก Google Trends"""
        try:
            # Google Trends ต้องใช้ unofficial API หรือ web scraping
            # สำหรับ MVP เราจะใช้ mock data ก่อน
            return self.get_mock_google_trends()
            
        except Exception as e:
            print(f"❌ Error collecting Google trends: {e}")
            return self.get_mock_google_trends()
    
    def get_mock_google_trends(self):
        """สร้างข้อมูล mock Google Trends"""
        mock_trends = [
            {
                'source': 'google_trends',
                'topic': 'AI Image Generator',
                'popularity_score': 92.3,
                'growth_rate': 35.8,
                'category': 'Technology',
                'keywords': ['AI', 'image generator', 'art', 'creative'],
                'raw_data': {
                    'search_volume': 'High',
                    'related_queries': ['midjourney', 'dall-e', 'stable diffusion']
                }
            },
            {
                'source': 'google_trends',
                'topic': 'Remote Work Tools',
                'popularity_score': 78.9,
                'growth_rate': 12.4,
                'category': 'Business',
                'keywords': ['remote work', 'productivity', 'tools', 'collaboration'],
                'raw_data': {
                    'search_volume': 'Medium',
                    'related_queries': ['zoom', 'slack', 'notion']
                }
            }
        ]
        
        print("📋 Using mock Google Trends for testing")
        return mock_trends

class TrendCollectorManager:
    def __init__(self, db):
        self.db = db
        self.youtube_collector = YouTubeTrendsCollector()
        self.google_collector = GoogleTrendsCollector()
    
    def collect_all_trends(self):
        """เก็บ trends จากทุก source"""
        print("🔍 Starting trend collection...")
        
        all_trends = []
        
        # เก็บจาก YouTube
        youtube_trends = self.youtube_collector.get_trending_videos()
        all_trends.extend(youtube_trends)
        
        # เก็บจาก Google Trends
        google_trends = self.google_collector.get_trending_topics()
        all_trends.extend(google_trends)
        
        # บันทึกลง database
        saved_count = self.save_trends_to_database(all_trends)
        
        print(f"✅ Collected {len(all_trends)} trends, saved {saved_count} to database")
        return all_trends
    
    def save_trends_to_database(self, trends):
        """บันทึก trends ลง database"""
        try:
            from database.models_simple import TrendModel
            trend_model = TrendModel(self.db)
            
            saved_count = 0
            for trend in trends:
                trend_id = trend_model.create(
                    source=trend['source'],
                    topic=trend['topic'],
                    keywords=trend['keywords'],
                    popularity_score=trend['popularity_score'],
                    growth_rate=trend['growth_rate'],
                    category=trend['category'],
                    raw_data=trend['raw_data']
                )
                
                if trend_id:
                    saved_count += 1
            
            return saved_count
            
        except Exception as e:
            print(f"❌ Error saving trends to database: {e}")
            return 0
    
    def get_recent_trends(self, limit=10):
        """ดึง trends ล่าสุดจาก database"""
        try:
            from database.models_simple import TrendModel
            trend_model = TrendModel(self.db)
            
            trends = trend_model.get_all()
            return trends[:limit]
            
        except Exception as e:
            print(f"❌ Error getting recent trends: {e}")
            return []
    
    def analyze_trend_growth(self):
        """วิเคราะห์การเติบโตของ trends"""
        print("📈 Analyzing trend growth...")
        
        trends = self.get_recent_trends(20)
        
        growth_analysis = {
            'high_growth': [t for t in trends if t['growth_rate'] > 20],
            'medium_growth': [t for t in trends if 10 <= t['growth_rate'] <= 20],
            'stable': [t for t in trends if t['growth_rate'] < 10],
            'total_trends': len(trends)
        }
        
        print(f"📊 Analysis: {len(growth_analysis['high_growth'])} high growth, "
              f"{len(growth_analysis['medium_growth'])} medium growth, "
              f"{len(growth_analysis['stable'])} stable trends")
        
        return growth_analysis

def main():
    """ทดสอบ Trend Collector"""
    print("🚀 Testing Trend Collector...")
    
    try:
        # สร้าง database connection
        from database.models_simple import Database
        db = Database()
        
        # สร้าง trend collector
        collector = TrendCollectorManager(db)
        
        # เก็บ trends
        trends = collector.collect_all_trends()
        
        # แสดงผลลัพธ์
        print("\n📊 Collected Trends:")
        for i, trend in enumerate(trends[:5], 1):
            print(f"{i}. {trend['topic']} (Score: {trend['popularity_score']:.1f})")
        
        # วิเคราะห์ growth
        analysis = collector.analyze_trend_growth()
        
        print(f"\n🎯 Total trends in database: {analysis['total_trends']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Trend collection test failed: {e}")
        return False

if __name__ == "__main__":
    main()