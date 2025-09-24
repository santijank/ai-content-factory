import sqlite3
import json
import uuid
from datetime import datetime
import os

class Database:
    def __init__(self, db_path='./database/ai_content.db'):
        self.db_path = db_path
        # สร้างโฟลเดอร์ database ถ้ายังไม่มี
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """สร้าง database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # เพื่อให้ access columns by name
        return conn
    
    def init_database(self):
        """สร้าง tables ถ้ายังไม่มี"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # สร้าง trends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trends (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                topic TEXT NOT NULL,
                keywords TEXT,
                popularity_score REAL DEFAULT 0,
                growth_rate REAL DEFAULT 0,
                category TEXT,
                region TEXT DEFAULT 'global',
                collected_at TEXT,
                raw_data TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # สร้าง content_opportunities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_opportunities (
                id TEXT PRIMARY KEY,
                trend_id TEXT NOT NULL,
                suggested_angle TEXT NOT NULL,
                estimated_views INTEGER DEFAULT 0,
                competition_level TEXT DEFAULT 'medium',
                production_cost REAL DEFAULT 0,
                estimated_roi REAL DEFAULT 0,
                priority_score REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # สร้าง content_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_items (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                content_plan TEXT,
                production_status TEXT DEFAULT 'planning',
                assets TEXT,
                cost_breakdown TEXT,
                created_at TEXT,
                completed_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database tables created successfully!")

class TrendModel:
    def __init__(self, db):
        self.db = db
    
    def create(self, source, topic, keywords=None, popularity_score=0, **kwargs):
        """สร้าง trend record ใหม่"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        trend_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO trends 
            (id, source, topic, keywords, popularity_score, growth_rate, 
             category, region, collected_at, raw_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trend_id,
            source,
            topic,
            json.dumps(keywords) if keywords else None,
            popularity_score,
            kwargs.get('growth_rate', 0),
            kwargs.get('category'),
            kwargs.get('region', 'global'),
            now,
            json.dumps(kwargs.get('raw_data')) if kwargs.get('raw_data') else None,
            now,
            now
        ))
        
        conn.commit()
        conn.close()
        return trend_id
    
    def get_all(self):
        """ดึง trends ทั้งหมด"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM trends ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        trends = []
        for row in rows:
            trend = dict(row)
            # แปลง JSON strings กลับเป็น objects
            trend['keywords'] = json.loads(trend['keywords']) if trend['keywords'] else {}
            trend['raw_data'] = json.loads(trend['raw_data']) if trend['raw_data'] else {}
            trends.append(trend)
        
        conn.close()
        return trends
    
    def get_by_source(self, source):
        """ดึง trends ตาม source"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM trends WHERE source = ? ORDER BY created_at DESC', (source,))
        rows = cursor.fetchall()
        
        trends = []
        for row in rows:
            trend = dict(row)
            trend['keywords'] = json.loads(trend['keywords']) if trend['keywords'] else {}
            trends.append(trend)
        
        conn.close()
        return trends

class ContentOpportunityModel:
    def __init__(self, db):
        self.db = db
    
    def create(self, trend_id, suggested_angle, **kwargs):
        """สร้าง content opportunity ใหม่"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        opportunity_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO content_opportunities 
            (id, trend_id, suggested_angle, estimated_views, competition_level,
             production_cost, estimated_roi, priority_score, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            opportunity_id,
            trend_id,
            suggested_angle,
            kwargs.get('estimated_views', 0),
            kwargs.get('competition_level', 'medium'),
            kwargs.get('production_cost', 0),
            kwargs.get('estimated_roi', 0),
            kwargs.get('priority_score', 0),
            kwargs.get('status', 'pending'),
            now,
            now
        ))
        
        conn.commit()
        conn.close()
        return opportunity_id
    
    def get_by_status(self, status='pending'):
        """ดึง opportunities ตาม status"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM content_opportunities 
            WHERE status = ? 
            ORDER BY priority_score DESC, created_at DESC
        ''', (status,))
        
        rows = cursor.fetchall()
        opportunities = [dict(row) for row in rows]
        
        conn.close()
        return opportunities

def test_database_simple():
    """ทดสอบ database แบบง่าย"""
    try:
        # สร้าง database instance
        db = Database('./database/test_ai_content.db')
        
        # สร้าง models
        trend_model = TrendModel(db)
        opportunity_model = ContentOpportunityModel(db)
        
        # ทดสอบ insert trend
        trend_id = trend_model.create(
            source='test',
            topic='Test Trend Topic',
            keywords={'test': 'keyword', 'ai': 'content'},
            popularity_score=85.5,
            category='technology'
        )
        print(f"✅ Created trend: {trend_id}")
        
        # ทดสอบ query trends
        trends = trend_model.get_all()
        print(f"✅ Retrieved {len(trends)} trends")
        
        if trends:
            print(f"✅ First trend: {trends[0]['topic']}")
            print(f"✅ Keywords: {trends[0]['keywords']}")
        
        # ทดสอบ create opportunity
        opp_id = opportunity_model.create(
            trend_id=trend_id,
            suggested_angle='Create tutorial about this trend',
            estimated_views=10000,
            priority_score=8.5
        )
        print(f"✅ Created opportunity: {opp_id}")
        
        # ทดสอบ query opportunities
        opportunities = opportunity_model.get_by_status('pending')
        print(f"✅ Retrieved {len(opportunities)} opportunities")
        
        # ลบ test database
        os.remove('./database/test_ai_content.db')
        print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False