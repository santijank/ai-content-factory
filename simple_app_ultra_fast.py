from flask import Flask, jsonify
import sqlite3
from datetime import datetime
import uuid
import json

# Pre-compile everything at startup
app = Flask(__name__)

# Global database connection pool (simple version)
def get_db():
    """Ultra fast database connection"""
    conn = sqlite3.connect('content_factory.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Pre-cache common queries
_cache = {}
_cache_time = {}

def simple_cache_get(key, max_age=30):
    """Simple cache implementation"""
    import time
    if key in _cache:
        if time.time() - _cache_time[key] < max_age:
            return _cache[key]
    return None

def simple_cache_set(key, value):
    """Set cache value"""
    import time
    _cache[key] = value
    _cache_time[key] = time.time()

@app.route('/')
def dashboard():
    """Ultra-minimal dashboard"""
    return '''<!DOCTYPE html><html><head><title>AI Content Factory</title><meta charset="UTF-8"><style>body{font-family:Arial,sans-serif;margin:20px;background:#f0f2f5}.header{background:#4CAF50;color:white;padding:20px;border-radius:8px;text-align:center;margin-bottom:20px}.card{background:white;padding:20px;margin:10px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}button{background:#2196F3;color:white;border:none;padding:10px 20px;border-radius:4px;cursor:pointer;margin:5px}button:hover{background:#1976D2}.result{margin-top:10px;padding:10px;background:#e8f5e8;border-radius:4px}</style></head><body><div class="header"><h1>🚀 AI Content Factory</h1><p>Ultra Fast Version</p></div><div class="card"><h3>📊 Analytics</h3><button onclick="loadAnalytics()">Load Analytics</button><div id="analytics"></div></div><div class="card"><h3>📈 Trends</h3><button onclick="loadTrends()">Load Trends</button><div id="trends"></div></div><script>function loadAnalytics(){document.getElementById('analytics').innerHTML='⏳ Loading...';fetch('/api/analytics').then(r=>r.json()).then(d=>{document.getElementById('analytics').innerHTML=`<div class="result">Trends: ${d.trends_count}<br>Opportunities: ${d.opportunities_count}<br>ROI: ${d.avg_roi.toFixed(2)}</div>`})}function loadTrends(){document.getElementById('trends').innerHTML='⏳ Loading...';fetch('/api/trends').then(r=>r.json()).then(d=>{let html='<div class="result">';d.trends.forEach(t=>{html+=`<div>${t.topic} (${t.popularity_score})</div>`});html+='</div>';document.getElementById('trends').innerHTML=html})}</script></body></html>'''

@app.route('/api/analytics')
def analytics():
    """Ultra fast analytics"""
    # Check cache first
    cached = simple_cache_get('analytics')
    if cached:
        return jsonify(cached)
    
    conn = get_db()
    
    # Single query to get all data
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM trends')
    trends_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM content_opportunities')
    opportunities_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(estimated_roi) FROM content_opportunities')
    avg_roi_result = cursor.fetchone()[0]
    avg_roi = avg_roi_result if avg_roi_result else 0
    
    conn.close()
    
    result = {
        'trends_count': trends_count,
        'opportunities_count': opportunities_count,
        'avg_roi': float(avg_roi)
    }
    
    # Cache result
    simple_cache_set('analytics', result)
    
    return jsonify(result)

@app.route('/api/trends')
def trends():
    """Ultra fast trends"""
    cached = simple_cache_get('trends')
    if cached:
        return jsonify(cached)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, topic, popularity_score, growth_rate FROM trends ORDER BY collected_at DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    trends_data = []
    for row in rows:
        trends_data.append({
            'id': row[0],
            'topic': row[1], 
            'popularity_score': row[2],
            'growth_rate': row[3]
        })
    
    result = {'trends': trends_data}
    simple_cache_set('trends', result)
    
    return jsonify(result)

@app.route('/api/opportunities')
def opportunities():
    """Ultra fast opportunities"""
    cached = simple_cache_get('opportunities')
    if cached:
        return jsonify(cached)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT co.id, co.suggested_angle, co.estimated_views, co.estimated_roi, t.topic
        FROM content_opportunities co 
        LEFT JOIN trends t ON co.trend_id = t.id 
        ORDER BY co.priority_score DESC LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    opportunities_data = []
    for row in rows:
        opportunities_data.append({
            'id': row[0],
            'suggested_angle': row[1],
            'estimated_views': row[2],
            'estimated_roi': row[3],
            'trend_topic': row[4]
        })
    
    result = {'opportunities': opportunities_data}
    simple_cache_set('opportunities', result)
    
    return jsonify(result)

@app.route('/api/collect-trends', methods=['POST'])
def collect_trends():
    """Fast trend collection"""
    # Clear cache
    if 'trends' in _cache:
        del _cache['trends']
    if 'analytics' in _cache:
        del _cache['analytics']
    
    new_trends = [
        ('ai_video_' + str(uuid.uuid4())[:8], 'youtube', 'AI Video Tools', 88.2, 22.1),
        ('crypto_' + str(uuid.uuid4())[:8], 'twitter', 'Crypto 2025', 76.5, 8.9),
        ('fitness_' + str(uuid.uuid4())[:8], 'instagram', 'Home Fitness', 82.3, 16.7)
    ]
    
    conn = get_db()
    cursor = conn.cursor()
    count = 0
    
    for trend_data in new_trends:
        try:
            cursor.execute('''
                INSERT INTO trends (id, source, topic, popularity_score, growth_rate, category, region, collected_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trend_data[0], trend_data[1], trend_data[2], trend_data[3], trend_data[4], 'Technology', 'Global', datetime.now(), '{}'))
            count += 1
        except:
            pass
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'count': count})

@app.route('/api/generate-opportunities', methods=['POST'])
def generate_opportunities():
    """Fast opportunity generation"""
    # Clear cache
    if 'opportunities' in _cache:
        del _cache['opportunities']
    if 'analytics' in _cache:
        del _cache['analytics']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get recent trends
    cursor.execute('SELECT id, topic, popularity_score FROM trends ORDER BY collected_at DESC LIMIT 3')
    trends = cursor.fetchall()
    
    count = 0
    for trend in trends:
        opp_id = str(uuid.uuid4())[:8] + "_opp"
        try:
            cursor.execute('''
                INSERT INTO content_opportunities
                (id, trend_id, suggested_angle, estimated_views, competition_level, 
                 production_cost, estimated_roi, priority_score, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opp_id,
                trend[0],
                f"Guide to {trend[1]}",
                int(trend[2] * 100),
                'medium',
                15.0,
                3.5,
                trend[2] / 10,
                'pending',
                datetime.now()
            ))
            count += 1
        except:
            pass
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'count': count})

if __name__ == '__main__':
    print("🚀 AI Content Factory - ULTRA FAST Version")
    print("=" * 50)
    print("⚡ All optimizations enabled")
    print("🗄️ Database: SQLite with optimized queries")
    print("💾 Caching: Simple in-memory cache")
    print("🌐 Server: Production mode")
    print("📊 Dashboard: http://localhost:5000")
    print("=" * 50)
    
    # Run in production mode
    app.run(
        host='127.0.0.1', 
        port=5000, 
        debug=False,        # ปิด debug mode
        threaded=True,      # เปิด threading
        use_reloader=False  # ปิด auto-reload
    )