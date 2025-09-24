# main_app.py - Complete AI Content Factory with YouTube Integration

import os
import sqlite3
from datetime import datetime, timedelta
import json
import asyncio
from threading import Thread
from flask import Flask, render_template, jsonify, request, redirect, url_for
from dotenv import load_dotenv
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytrends
from pytrends.request import TrendReq

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Database initialization
def init_database():
    """สร้างและเตรียมฐานข้อมูล"""
    conn = sqlite3.connect('ai_content_factory.db')
    cursor = conn.cursor()
    
    # สร้างตาราง trends
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source VARCHAR(50),
            topic VARCHAR(255),
            keywords TEXT,
            popularity_score FLOAT,
            growth_rate FLOAT,
            category VARCHAR(100),
            region VARCHAR(50),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT
        )
    ''')
    
    # สร้างตาราง content_opportunities
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trend_id INTEGER,
            suggested_angle TEXT,
            estimated_views INTEGER,
            competition_level VARCHAR(20),
            production_cost DECIMAL(10,2),
            estimated_roi FLOAT,
            priority_score FLOAT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trend_id) REFERENCES trends (id)
        )
    ''')
    
    # สร้างตาราง content_items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER,
            title VARCHAR(255),
            description TEXT,
            content_plan TEXT,
            production_status VARCHAR(20) DEFAULT 'planning',
            assets TEXT,
            cost_breakdown TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (opportunity_id) REFERENCES content_opportunities (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

class TrendCollector:
    """คลาสสำหรับเก็บ trends จากแหล่งต่างๆ"""
    
    def __init__(self):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.youtube_service = None
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        # เตรียม YouTube API
        if self.youtube_api_key:
            try:
                self.youtube_service = build('youtube', 'v3', developerKey=self.youtube_api_key)
                print("✅ YouTube API connected")
            except Exception as e:
                print(f"❌ YouTube API connection failed: {e}")
        
        # เตรียม Google Trends
        try:
            self.pytrends = TrendReq(hl='th-TH', tz=420)  # Thai language, GMT+7
            print("✅ Google Trends connected")
        except Exception as e:
            print(f"❌ Google Trends connection failed: {e}")
            self.pytrends = None
    
    def collect_youtube_trends(self):
        """เก็บ trends จาก YouTube"""
        if not self.youtube_service:
            print("⚠️  YouTube API not available")
            return []
        
        try:
            print("📺 Collecting YouTube trends...")
            
            # ดึงวิดีโอยอดนิยมในไทย
            request = self.youtube_service.videos().list(
                part='snippet,statistics',
                chart='mostPopular',
                regionCode='TH',
                maxResults=20
            )
            response = request.execute()
            
            youtube_trends = []
            for video in response['items']:
                # คำนวณคะแนนความนิยม
                popularity_score = self.calculate_youtube_popularity(video)
                
                # เตรียมข้อมูล
                trend_data = {
                    'source': 'youtube',
                    'topic': video['snippet']['title'][:250],  # จำกัดความยาว
                    'keywords': json.dumps(video['snippet'].get('tags', [])[:5]),
                    'popularity_score': popularity_score,
                    'growth_rate': 0.8,
                    'category': 'Entertainment',
                    'region': 'TH',
                    'raw_data': json.dumps({
                        'video_id': video['id'],
                        'channel': video['snippet']['channelTitle'],
                        'views': video['statistics'].get('viewCount', 0),
                        'likes': video['statistics'].get('likeCount', 0),
                        'comments': video['statistics'].get('commentCount', 0),
                        'published_at': video['snippet']['publishedAt'],
                        'thumbnail': video['snippet']['thumbnails']['high']['url']
                    })
                }
                youtube_trends.append(trend_data)
            
            print(f"📺 Collected {len(youtube_trends)} YouTube trends")
            return youtube_trends
            
        except HttpError as e:
            print(f"❌ YouTube API Error: {e}")
            return []
        except Exception as e:
            print(f"❌ YouTube collection error: {e}")
            return []
    
    def calculate_youtube_popularity(self, video):
        """คำนวณคะแนนความนิยมจาก YouTube metrics"""
        try:
            views = int(video['statistics'].get('viewCount', 0))
            likes = int(video['statistics'].get('likeCount', 0))
            comments = int(video['statistics'].get('commentCount', 0))
            
            # สูตรคำนวณ (scale 0-10)
            view_score = min(views / 100000, 8)  # 100k views = 8 points
            engagement_score = min((likes + comments * 5) / 10000, 2)  # engagement bonus
            
            total_score = min(view_score + engagement_score, 10)
            return round(total_score, 2)
            
        except:
            return 5.0
    
    def collect_google_trends(self):
        """เก็บ trends จาก Google Trends"""
        if not self.pytrends:
            print("⚠️  Google Trends not available")
            return []
        
        try:
            print("🔍 Collecting Google trends...")
            
            # ดึง trending searches
            trending_searches = self.pytrends.trending_searches(pn='thailand')
            
            google_trends = []
            for i, trend in enumerate(trending_searches[0][:15]):  # เอา 15 อันดับแรก
                trend_data = {
                    'source': 'google_trends',
                    'topic': str(trend)[:250],
                    'keywords': json.dumps([str(trend)]),
                    'popularity_score': max(10 - (i * 0.5), 5),  # คะแนนลดลงตามอันดับ
                    'growth_rate': 0.9,
                    'category': 'Search',
                    'region': 'TH',
                    'raw_data': json.dumps({
                        'rank': i + 1,
                        'keyword': str(trend)
                    })
                }
                google_trends.append(trend_data)
            
            print(f"🔍 Collected {len(google_trends)} Google trends")
            return google_trends
            
        except Exception as e:
            print(f"❌ Google Trends error: {e}")
            return []
    
    def save_trends_to_db(self, trends):
        """บันทึก trends ลงฐานข้อมูล"""
        if not trends:
            return 0
        
        conn = sqlite3.connect('ai_content_factory.db')
        cursor = conn.cursor()
        
        saved_count = 0
        for trend in trends:
            try:
                cursor.execute('''
                    INSERT INTO trends (source, topic, keywords, popularity_score, growth_rate, category, region, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trend['source'],
                    trend['topic'],
                    trend['keywords'],
                    trend['popularity_score'],
                    trend['growth_rate'],
                    trend['category'],
                    trend['region'],
                    trend['raw_data']
                ))
                saved_count += 1
            except Exception as e:
                print(f"Error saving trend: {e}")
        
        conn.commit()
        conn.close()
        return saved_count

class AIAnalyzer:
    """คลาสสำหรับวิเคราะห์ trends และสร้าง content opportunities"""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
    
    def analyze_trends_simple(self, trends):
        """วิเคราะห์ trends แบบง่ายๆ (ไม่ใช้ AI)"""
        opportunities = []
        
        for trend in trends:
            try:
                # สร้าง content angles แบบง่าย
                angles = self.generate_simple_angles(trend)
                
                for angle in angles:
                    opportunity = {
                        'trend_id': trend.get('id'),
                        'suggested_angle': angle,
                        'estimated_views': self.estimate_views(trend['popularity_score']),
                        'competition_level': self.assess_competition(trend['popularity_score']),
                        'production_cost': self.estimate_cost(angle),
                        'estimated_roi': self.calculate_roi(trend['popularity_score'], angle),
                        'priority_score': trend['popularity_score'] * trend['growth_rate']
                    }
                    opportunities.append(opportunity)
            except Exception as e:
                print(f"Error analyzing trend: {e}")
        
        return sorted(opportunities, key=lambda x: x['priority_score'], reverse=True)
    
    def generate_simple_angles(self, trend):
        """สร้าง content angles แบบง่าย"""
        topic = trend['topic']
        source = trend['source']
        
        angles = []
        
        if source == 'youtube':
            angles = [
                f"รีวิว: {topic}",
                f"วิเคราะห์เทรนด์: ทำไม {topic} ถึงดัง?",
                f"ทำตาม: {topic} ด้วยตัวเอง"
            ]
        elif source == 'google_trends':
            angles = [
                f"ข่าวด่วน: {topic} คืออะไร?",
                f"อัปเดต: สถานการณ์ {topic} ล่าสุด",
                f"มุมมอง: {topic} ส่งผลต่อเราอย่างไร?"
            ]
        
        return angles[:2]  # เอาแค่ 2 angles
    
    def estimate_views(self, popularity_score):
        """ประเมินยอดวิวที่คาดหวัง"""
        base_views = int(popularity_score * 10000)
        return base_views
    
    def assess_competition(self, popularity_score):
        """ประเมินระดับการแข่งขัน"""
        if popularity_score >= 8:
            return 'high'
        elif popularity_score >= 6:
            return 'medium'
        else:
            return 'low'
    
    def estimate_cost(self, angle):
        """ประเมินต้นทุนการผลิต"""
        if 'รีวิว' in angle or 'ทำตาม' in angle:
            return 50.0
        elif 'วิเคราะห์' in angle or 'อัปเดต' in angle:
            return 30.0
        else:
            return 20.0
    
    def calculate_roi(self, popularity_score, angle):
        """คำนวณ ROI ที่คาดหวัง"""
        estimated_revenue = popularity_score * 15  # 15 บาทต่อคะแนน
        estimated_cost = self.estimate_cost(angle)
        
        if estimated_cost > 0:
            roi = (estimated_revenue - estimated_cost) / estimated_cost
            return round(roi, 2)
        return 0.0
    
    def save_opportunities_to_db(self, opportunities):
        """บันทึก opportunities ลงฐานข้อมูล"""
        conn = sqlite3.connect('ai_content_factory.db')
        cursor = conn.cursor()
        
        saved_count = 0
        for opp in opportunities:
            try:
                cursor.execute('''
                    INSERT INTO content_opportunities 
                    (trend_id, suggested_angle, estimated_views, competition_level, production_cost, estimated_roi, priority_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    opp.get('trend_id'),
                    opp['suggested_angle'],
                    opp['estimated_views'],
                    opp['competition_level'],
                    opp['production_cost'],
                    opp['estimated_roi'],
                    opp['priority_score']
                ))
                saved_count += 1
            except Exception as e:
                print(f"Error saving opportunity: {e}")
        
        conn.commit()
        conn.close()
        return saved_count

# Global instances
trend_collector = TrendCollector()
ai_analyzer = AIAnalyzer()

# Routes
@app.route('/')
def dashboard():
    """หน้าแดชบอร์ดหลัก"""
    return render_template('dashboard.html')

@app.route('/api/trends/collect')
def collect_trends():
    """API สำหรับเก็บ trends จากทุกแหล่ง"""
    try:
        all_trends = []
        
        # เก็บจาก YouTube
        youtube_trends = trend_collector.collect_youtube_trends()
        all_trends.extend(youtube_trends)
        
        # เก็บจาก Google Trends
        google_trends = trend_collector.collect_google_trends()
        all_trends.extend(google_trends)
        
        # บันทึกลงฐานข้อมูล
        saved_count = trend_collector.save_trends_to_db(all_trends)
        
        return jsonify({
            'success': True,
            'message': f'Collected and saved {saved_count} trends',
            'data': {
                'youtube_count': len(youtube_trends),
                'google_count': len(google_trends),
                'total_count': len(all_trends),
                'saved_count': saved_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trends/youtube')
def get_youtube_trends():
    """API สำหรับ YouTube trends"""
    try:
        youtube_trends = trend_collector.collect_youtube_trends()
        return jsonify({
            'success': True,
            'data': youtube_trends,
            'count': len(youtube_trends),
            'source': 'youtube'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trends/google')
def get_google_trends():
    """API สำหรับ Google Trends"""
    try:
        google_trends = trend_collector.collect_google_trends()
        return jsonify({
            'success': True,
            'data': google_trends,
            'count': len(google_trends),
            'source': 'google'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trends/history')
def get_trends_history():
    """ดึงประวัติ trends ที่เก็บไว้"""
    try:
        conn = sqlite3.connect('ai_content_factory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trends 
            ORDER BY collected_at DESC 
            LIMIT 50
        ''')
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        trends = []
        for row in rows:
            trend = dict(zip(columns, row))
            # แปลง JSON strings กลับ
            if trend['keywords']:
                try:
                    trend['keywords'] = json.loads(trend['keywords'])
                except:
                    trend['keywords'] = []
            if trend['raw_data']:
                try:
                    trend['raw_data'] = json.loads(trend['raw_data'])
                except:
                    trend['raw_data'] = {}
            trends.append(trend)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': trends,
            'count': len(trends)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/opportunities/generate')
def generate_opportunities():
    """สร้าง content opportunities จาก trends"""
    try:
        # ดึง trends ล่าสุดจาก database
        conn = sqlite3.connect('ai_content_factory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trends 
            WHERE collected_at >= datetime('now', '-1 day')
            ORDER BY popularity_score DESC
            LIMIT 20
        ''')
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        trends = []
        for row in rows:
            trend = dict(zip(columns, row))
            trends.append(trend)
        
        conn.close()
        
        if not trends:
            return jsonify({
                'success': False,
                'error': 'No recent trends found. Please collect trends first.'
            })
        
        # วิเคราะห์และสร้าง opportunities
        opportunities = ai_analyzer.analyze_trends_simple(trends)
        
        # บันทึกลง database
        saved_count = ai_analyzer.save_opportunities_to_db(opportunities)
        
        return jsonify({
            'success': True,
            'message': f'Generated {saved_count} content opportunities',
            'data': opportunities[:10],  # ส่งกลับ 10 อันแรก
            'total_count': len(opportunities),
            'saved_count': saved_count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/opportunities')
def get_opportunities():
    """ดึง content opportunities"""
    try:
        conn = sqlite3.connect('ai_content_factory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT co.*, t.topic, t.source, t.popularity_score as trend_popularity
            FROM content_opportunities co
            LEFT JOIN trends t ON co.trend_id = t.id
            ORDER BY co.priority_score DESC
            LIMIT 20
        ''')
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        opportunities = []
        for row in rows:
            opportunity = dict(zip(columns, row))
            opportunities.append(opportunity)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': opportunities,
            'count': len(opportunities)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """ดึงสถิติรวม"""
    try:
        conn = sqlite3.connect('ai_content_factory.db')
        cursor = conn.cursor()
        
        # นับ trends
        cursor.execute('SELECT COUNT(*) FROM trends WHERE DATE(collected_at) = DATE("now")')
        trends_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trends')
        trends_total = cursor.fetchone()[0]
        
        # นับ opportunities
        cursor.execute('SELECT COUNT(*) FROM content_opportunities WHERE DATE(created_at) = DATE("now")')
        opportunities_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM content_opportunities')
        opportunities_total = cursor.fetchone()[0]
        
        # Top sources
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM trends 
            WHERE DATE(collected_at) = DATE("now")
            GROUP BY source
        ''')
        sources_today = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'trends': {
                    'today': trends_today,
                    'total': trends_total
                },
                'opportunities': {
                    'today': opportunities_today,
                    'total': opportunities_total
                },
                'sources_today': sources_today
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # เตรียมฐานข้อมูล
    init_database()
    
    # เช็ค API Keys
    print("\n🔧 Checking API Configuration:")
    print(f"YouTube API Key: {'✅ Set' if os.getenv('YOUTUBE_API_KEY') else '❌ Missing'}")
    print(f"Groq API Key: {'✅ Set' if os.getenv('GROQ_API_KEY') else '❌ Missing'}")
    
    # รันแอป
    print("\n🚀 Starting AI Content Factory...")
    print("💡 Open http://localhost:5000 in your browser")
    print("📊 API endpoints available at /api/...")
    
    app.run(debug=True, host='0.0.0.0', port=5000)