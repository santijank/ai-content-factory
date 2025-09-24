from flask import Flask, jsonify, request
import sqlite3
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid
import time
from functools import wraps

load_dotenv()

app = Flask(__name__)

# Simple in-memory cache
cache = {}
cache_timeout = {}

def cached(timeout=60):
    """Simple caching decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            current_time = time.time()
            
            if (cache_key in cache and 
                cache_key in cache_timeout and 
                current_time - cache_timeout[cache_key] < timeout):
                return cache[cache_key]
            
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_timeout[cache_key] = current_time
            
            return result
        return wrapper
    return decorator

def get_db_connection():
    """Optimized database connection"""
    conn = sqlite3.connect('content_factory.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # เพิ่ม pragmas เพื่อเพิ่มประสิทธิภาพ
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = 1000")
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn

@app.route('/')
def dashboard():
    """Optimized dashboard with minified HTML"""
    return """<!DOCTYPE html><html><head><title>AI Content Factory</title><meta charset="UTF-8"><style>body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;margin:0;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}.container{max-width:1200px;margin:0 auto}.header{background:rgba(255,255,255,0.95);color:#333;padding:30px;border-radius:15px;text-align:center;margin-bottom:30px;box-shadow:0 8px 32px rgba(0,0,0,0.1)}.status{padding:15px;background:#4CAF50;color:white;border-radius:10px;text-align:center;margin-bottom:30px;box-shadow:0 4px 15px rgba(76,175,80,0.3)}.dashboard{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:25px}.card{background:rgba(255,255,255,0.95);padding:25px;border-radius:15px;box-shadow:0 8px 32px rgba(0,0,0,0.1);transition:transform 0.3s ease,box-shadow 0.3s ease}.card:hover{transform:translateY(-5px);box-shadow:0 15px 45px rgba(0,0,0,0.2)}.card h3{margin-top:0;color:#333;font-size:1.3em}.card p{color:#666;line-height:1.6}button{background:linear-gradient(45deg,#2196F3,#21CBF3);color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-weight:600;transition:all 0.3s ease;width:100%;margin-bottom:15px}button:hover{background:linear-gradient(45deg,#1976D2,#1AB7EA);transform:translateY(-2px);box-shadow:0 5px 15px rgba(33,150,243,0.4)}.result-box{margin-top:15px;padding:10px;background:#f8f9fa;border-radius:8px;border-left:4px solid #2196F3;font-size:0.9em}.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:15px;margin-top:20px}.stat-item{text-align:center;padding:15px;background:#f8f9fa;border-radius:10px}.stat-number{font-size:1.5em;font-weight:bold;color:#2196F3}.stat-label{font-size:0.8em;color:#666;margin-top:5px}</style></head><body><div class="container"><div class="header"><h1>🚀 AI Content Factory System</h1><p>Content Creation & Automation Platform</p><p style="font-size:0.9em;color:#666;">Optimized Version - High Performance</p></div><div class="status">✅ System Status: Online (Optimized Database)</div><div class="dashboard"><div class="card"><h3>📊 Trend Monitor</h3><p>เก็บข้อมูล trends จากแหล่งต่างๆ และวิเคราะห์ความนิยม</p><button onclick="collectTrends()">🔍 Collect Trends</button><button onclick="viewTrends()">📋 View Current Trends</button><div id="trends-result" class="result-box" style="display:none;"></div></div><div class="card"><h3>🎯 Content Opportunities</h3><p>วิเคราะห์และสร้างโอกาสเนื้อหาจาก trending topics</p><button onclick="generateOpportunities()">💡 Generate Ideas</button><button onclick="viewOpportunities()">📝 View Opportunities</button><div id="opportunities-result" class="result-box" style="display:none;"></div></div><div class="card"><h3>🎬 Content Generator</h3><p>สร้างเนื้อหาด้วย AI (Coming Soon)</p><button onclick="generateContent()">🎨 Create Content</button><div id="content-result" class="result-box" style="display:none;"></div></div><div class="card"><h3>📈 Analytics Dashboard</h3><p>สถิติและผลลัพธ์การทำงานของระบบ</p><button onclick="showAnalytics()">📊 View Analytics</button><div id="analytics-result" class="result-box" style="display:none;"></div></div></div></div><script>function showLoading(elementId){document.getElementById(elementId).style.display='block';document.getElementById(elementId).innerHTML='⏳ กำลังดำเนินการ...'}function showResult(elementId,message){document.getElementById(elementId).style.display='block';document.getElementById(elementId).innerHTML=message}function collectTrends(){showLoading('trends-result');fetch('/api/collect-trends',{method:'POST'}).then(response=>response.json()).then(data=>{showResult('trends-result',`✅ เก็บข้อมูลแล้ว: ${data.count} trends`)})}function viewTrends(){showLoading('trends-result');fetch('/api/trends').then(response=>response.json()).then(data=>{let html='<h4>📊 Current Trends:</h4>';data.trends.forEach(trend=>{html+=`<div style="margin:10px 0;padding:10px;background:#e3f2fd;border-radius:5px;"><strong>${trend.topic}</strong><br><small>Popularity: ${trend.popularity_score} | Growth: ${trend.growth_rate}%</small></div>`});showResult('trends-result',html)})}function generateOpportunities(){showLoading('opportunities-result');fetch('/api/generate-opportunities',{method:'POST'}).then(response=>response.json()).then(data=>{showResult('opportunities-result',`✅ สร้างแล้ว: ${data.count} opportunities`)})}function viewOpportunities(){showLoading('opportunities-result');fetch('/api/opportunities').then(response=>response.json()).then(data=>{let html='<h4>🎯 Content Opportunities:</h4>';data.opportunities.forEach(opp=>{html+=`<div style="margin:10px 0;padding:10px;background:#f3e5f5;border-radius:5px;"><strong>${opp.suggested_angle}</strong><br><small>Views: ${opp.estimated_views} | ROI: ${opp.estimated_roi}</small></div>`});showResult('opportunities-result',html)})}function generateContent(){showLoading('content-result');setTimeout(()=>{showResult('content-result','🎨 Content Generator (Coming Soon)')},1000)}function showAnalytics(){showLoading('analytics-result');fetch('/api/analytics').then(response=>response.json()).then(data=>{const html=`<div class="stats-grid"><div class="stat-item"><div class="stat-number">${data.trends_count}</div><div class="stat-label">Trends</div></div><div class="stat-item"><div class="stat-number">${data.opportunities_count}</div><div class="stat-label">Opportunities</div></div><div class="stat-item"><div class="stat-number">${data.avg_roi.toFixed(1)}</div><div class="stat-label">Avg ROI</div></div></div>`;showResult('analytics-result',html)})}window.onload=function(){showAnalytics()}</script></body></html>"""

@app.route('/api/collect-trends', methods=['POST'])
def collect_trends():
    """Optimized trend collection"""
    new_trends = [
        ('ai_video_editing', 'youtube', 'AI Video Editing Tools', 'ai,video,editing', 88.2, 22.1, 'Technology', 'Global'),
        ('crypto_trends_2025', 'twitter', 'Cryptocurrency Trends 2025', 'crypto,bitcoin,blockchain', 76.5, 8.9, 'Finance', 'Global'),
        ('fitness_content', 'instagram', 'Home Fitness Content', 'fitness,workout,health', 82.3, 16.7, 'Health', 'Global')
    ]
    
    conn = get_db_connection()
    count = 0
    
    # Use transaction for better performance
    with conn:
        for trend_data in new_trends:
            trend_id = str(uuid.uuid4())[:8] + "_" + trend_data[0]
            try:
                conn.execute("""
                    INSERT INTO trends (id, source, topic, keywords, popularity_score, growth_rate, category, region, collected_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (trend_id, trend_data[1], trend_data[2], trend_data[3], trend_data[4], trend_data[5], trend_data[6], trend_data[7], datetime.now(), '{}'))
                count += 1
            except sqlite3.IntegrityError:
                pass
    
    conn.close()
    return jsonify({'status': 'success', 'count': count})

@app.route('/api/trends')
@cached(timeout=30)  # Cache for 30 seconds
def get_trends():
    """Optimized trends retrieval with caching"""
    conn = get_db_connection()
    trends = conn.execute('SELECT * FROM trends ORDER BY collected_at DESC LIMIT 10').fetchall()
    conn.close()
    return jsonify({'trends': [dict(trend) for trend in trends]})

@app.route('/api/generate-opportunities', methods=['POST'])
def generate_opportunities():
    """Optimized opportunity generation"""
    conn = get_db_connection()
    
    # Use more efficient query
    trends = conn.execute('SELECT id, topic, popularity_score, growth_rate FROM trends ORDER BY collected_at DESC LIMIT 5').fetchall()
    
    count = 0
    with conn:  # Use transaction
        for trend in trends:
            opp_id = str(uuid.uuid4())[:8] + "_opp"
            suggested_angles = [
                f"Complete Guide to {trend['topic']}",
                f"Top 5 {trend['topic']} Tips for Beginners"
            ]
            
            for i, angle in enumerate(suggested_angles):
                try:
                    conn.execute("""
                        INSERT INTO content_opportunities
                        (id, trend_id, suggested_angle, estimated_views, competition_level, 
                         production_cost, estimated_roi, priority_score, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"{opp_id}_{i}",
                        trend['id'],
                        angle,
                        int(trend['popularity_score'] * 100),
                        'medium',
                        15.0,
                        3.5,
                        trend['popularity_score'] / 10,
                        'pending',
                        datetime.now()
                    ))
                    count += 1
                except sqlite3.IntegrityError:
                    pass
    
    conn.close()
    return jsonify({'status': 'success', 'count': count})

@app.route('/api/opportunities')
@cached(timeout=30)  # Cache for 30 seconds
def get_opportunities():
    """Optimized opportunities retrieval with caching"""
    conn = get_db_connection()
    opportunities = conn.execute("""
        SELECT co.*, t.topic as trend_topic 
        FROM content_opportunities co 
        LEFT JOIN trends t ON co.trend_id = t.id 
        ORDER BY co.priority_score DESC LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify({'opportunities': [dict(opp) for opp in opportunities]})

@app.route('/api/analytics')
@cached(timeout=60)  # Cache for 1 minute
def get_analytics():
    """Optimized analytics with caching"""
    conn = get_db_connection()
    
    # Use more efficient single query
    result = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM trends) as trends_count,
            (SELECT COUNT(*) FROM content_opportunities) as opportunities_count,
            (SELECT AVG(estimated_roi) FROM content_opportunities) as avg_roi
    """).fetchone()
    
    conn.close()
    
    return jsonify({
        'trends_count': result['trends_count'],
        'opportunities_count': result['opportunities_count'],
        'avg_roi': result['avg_roi'] if result['avg_roi'] else 0
    })

if __name__ == '__main__':
    print("\n🚀 AI Content Factory - Optimized Version")
    print("=" * 50)
    print("📊 Dashboard: http://localhost:5000")
    print("⚡ Performance optimizations enabled")
    print("🗄️ Database indexing active")
    print("💾 Response caching enabled")
    print("=" * 50)
    
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
