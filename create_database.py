import sqlite3
import os
from datetime import datetime

def create_database():
    """สร้าง SQLite database และตาราง"""
    db_path = 'content_factory.db'
    
    # ลบไฟล์เก่าถ้ามี
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ ลบไฟล์เก่า: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # สร้างตาราง trends
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trends (
        id TEXT PRIMARY KEY,
        source TEXT,
        topic TEXT,
        keywords TEXT,
        popularity_score REAL,
        growth_rate REAL,
        category TEXT,
        region TEXT,
        collected_at TIMESTAMP,
        raw_data TEXT
    )
    ''')
    
    # สร้างตาราง content_opportunities
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content_opportunities (
        id TEXT PRIMARY KEY,
        trend_id TEXT,
        suggested_angle TEXT,
        estimated_views INTEGER,
        competition_level TEXT,
        production_cost REAL,
        estimated_roi REAL,
        priority_score REAL,
        status TEXT,
        created_at TIMESTAMP,
        FOREIGN KEY (trend_id) REFERENCES trends (id)
    )
    ''')
    
    # สร้างตาราง content_items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content_items (
        id TEXT PRIMARY KEY,
        opportunity_id TEXT,
        title TEXT,
        description TEXT,
        content_plan TEXT,
        production_status TEXT,
        assets TEXT,
        cost_breakdown TEXT,
        created_at TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (opportunity_id) REFERENCES content_opportunities (id)
    )
    ''')
    
    # เพิ่มข้อมูลตัวอย่าง
    sample_trends = [
        ('ai_content_2025', 'demo', 'AI Content Creation Tools 2025', 'AI,content,automation', 85.5, 12.3, 'Technology', 'Global', datetime.now(), '{}'),
        ('short_video_trends', 'demo', 'Short Form Video Marketing', 'video,marketing,social', 92.1, 18.7, 'Marketing', 'Global', datetime.now(), '{}'),
        ('tech_reviews_2025', 'demo', 'Tech Product Reviews 2025', 'tech,reviews,gadgets', 78.9, 15.2, 'Technology', 'Global', datetime.now(), '{}')
    ]
    
    cursor.executemany('''
        INSERT INTO trends (id, source, topic, keywords, popularity_score, growth_rate, category, region, collected_at, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_trends)
    
    # เพิ่ม content opportunities ตัวอย่าง
    sample_opportunities = [
        ('opp_ai_1', 'ai_content_2025', 'Best AI Tools for Content Creators in 2025', 8500, 'medium', 25.0, 4.2, 9.1, 'pending', datetime.now()),
        ('opp_video_1', 'short_video_trends', 'How to Create Viral Short Videos', 12000, 'high', 15.0, 5.8, 8.7, 'pending', datetime.now()),
        ('opp_tech_1', 'tech_reviews_2025', 'Top 10 Gadgets to Review in 2025', 6500, 'low', 35.0, 3.5, 7.9, 'pending', datetime.now())
    ]
    
    cursor.executemany('''
        INSERT INTO content_opportunities (id, trend_id, suggested_angle, estimated_views, competition_level, production_cost, estimated_roi, priority_score, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_opportunities)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database สร้างเสร็จแล้ว: {db_path}")
    print(f"📊 เพิ่มข้อมูลตัวอย่าง: {len(sample_trends)} trends, {len(sample_opportunities)} opportunities")

if __name__ == '__main__':
    create_database()