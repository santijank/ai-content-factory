#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Content Factory - Web Dashboard
Flask-based web interface
"""

from flask import Flask, render_template, request, jsonify, send_file
import asyncio
import json
import sqlite3
from datetime import datetime
import os
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Database setup
DB_PATH = "content_factory.db"

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            angle TEXT,
            platform TEXT,
            script TEXT,
            hashtags TEXT,
            thumbnail_concept TEXT,
            ai_generated INTEGER DEFAULT 0,
            cost REAL DEFAULT 0.0,
            quality_score REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            platform TEXT NOT NULL,
            video_id TEXT,
            url TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'uploaded',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES content(id)
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# =====================================
# API Endpoints
# =====================================

@app.route('/')
def index():
    """Dashboard home"""
    return render_template('dashboard.html')

@app.route('/api/generate', methods=['POST'])
def generate_content():
    """Generate content API"""
    data = request.json
    
    topic = data.get('topic', 'Unknown')
    angle = data.get('angle', 'General')
    platform = data.get('platform', 'youtube')
    use_ai = data.get('use_ai', False)
    
    # Simulate content generation
    script = {
        "titles": [
            f"{topic}: Complete Guide 2025",
            f"Master {topic} - {angle}",
            f"{topic} Explained Simply"
        ],
        "hook": f"Discover the secrets of {topic} with our {angle} approach...",
        "full_script": f"Complete video script about {topic} using {angle} methodology.",
        "hashtags": [f"#{topic.replace(' ', '')}", "#viral", "#trending2025"]
    }
    
    # Save to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO content (topic, angle, platform, script, hashtags, 
                           ai_generated, cost, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        topic, angle, platform,
        json.dumps(script),
        json.dumps(script['hashtags']),
        1 if use_ai else 0,
        0.1 if use_ai else 0.0,
        9.5 if use_ai else 7.5
    ))
    
    content_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "content_id": content_id,
        "script": script,
        "cost": 0.1 if use_ai else 0.0
    })

@app.route('/api/upload', methods=['POST'])
def upload_content():
    """Upload content API"""
    data = request.json
    
    content_id = data.get('content_id')
    platforms = data.get('platforms', [])
    
    results = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for platform in platforms:
        video_id = f"{platform.upper()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        url = f"https://{platform}.com/video/{video_id}"
        
        cursor.execute("""
            INSERT INTO uploads (content_id, platform, video_id, url, status)
            VALUES (?, ?, ?, ?, ?)
        """, (content_id, platform, video_id, url, 'published'))
        
        results.append({
            "platform": platform,
            "video_id": video_id,
            "url": url
        })
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "uploads": results
    })

@app.route('/api/content/list')
def list_content():
    """List all content"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, topic, angle, platform, cost, quality_score, 
               ai_generated, created_at
        FROM content 
        ORDER BY created_at DESC 
        LIMIT 50
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    content_list = []
    for row in rows:
        content_list.append({
            "id": row[0],
            "topic": row[1],
            "angle": row[2],
            "platform": row[3],
            "cost": row[4],
            "quality_score": row[5],
            "ai_generated": bool(row[6]),
            "created_at": row[7]
        })
    
    return jsonify(content_list)

@app.route('/api/content/<int:content_id>')
def get_content(content_id):
    """Get specific content"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, topic, angle, platform, script, hashtags, 
               thumbnail_concept, cost, quality_score, created_at
        FROM content WHERE id = ?
    """, (content_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return jsonify({"error": "Content not found"}), 404
    
    # Get uploads for this content
    cursor.execute("""
        SELECT platform, video_id, url, views, likes, uploaded_at
        FROM uploads WHERE content_id = ?
    """, (content_id,))
    
    uploads = cursor.fetchall()
    conn.close()
    
    content = {
        "id": row[0],
        "topic": row[1],
        "angle": row[2],
        "platform": row[3],
        "script": json.loads(row[4]) if row[4] else {},
        "hashtags": json.loads(row[5]) if row[5] else [],
        "thumbnail_concept": json.loads(row[6]) if row[6] else {},
        "cost": row[7],
        "quality_score": row[8],
        "created_at": row[9],
        "uploads": [
            {
                "platform": u[0],
                "video_id": u[1],
                "url": u[2],
                "views": u[3],
                "likes": u[4],
                "uploaded_at": u[5]
            }
            for u in uploads
        ]
    }
    
    return jsonify(content)

@app.route('/api/analytics')
def get_analytics():
    """Get analytics summary"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total content
    cursor.execute("SELECT COUNT(*) FROM content")
    total_content = cursor.fetchone()[0]
    
    # Total uploads
    cursor.execute("SELECT COUNT(*) FROM uploads")
    total_uploads = cursor.fetchone()[0]
    
    # Total views
    cursor.execute("SELECT SUM(views) FROM uploads")
    total_views = cursor.fetchone()[0] or 0
    
    # Total cost
    cursor.execute("SELECT SUM(cost) FROM content")
    total_cost = cursor.fetchone()[0] or 0
    
    # Platform breakdown
    cursor.execute("""
        SELECT platform, COUNT(*) as count, SUM(views) as views
        FROM uploads
        GROUP BY platform
    """)
    platform_stats = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        "total_content": total_content,
        "total_uploads": total_uploads,
        "total_views": total_views,
        "total_cost": round(total_cost, 2),
        "platforms": [
            {"platform": p[0], "count": p[1], "views": p[2] or 0}
            for p in platform_stats
        ]
    })

@app.route('/api/export')
def export_data():
    """Export all data as JSON"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM content")
    content = cursor.fetchall()
    
    cursor.execute("SELECT * FROM uploads")
    uploads = cursor.fetchall()
    
    conn.close()
    
    data = {
        "content": [dict(zip([d[0] for d in cursor.description], row)) for row in content],
        "uploads": [dict(zip([d[0] for d in cursor.description], row)) for row in uploads],
        "exported_at": datetime.now().isoformat()
    }
    
    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return send_file(filename, as_attachment=True)

# =====================================
# HTML Template (Embedded)
# =====================================

@app.route('/create')
def create_page():
    """Create content page"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Create Content - AI Content Factory</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { 
            color: #667eea; 
            margin-bottom: 30px;
            font-size: 32px;
        }
        .form-group { 
            margin-bottom: 25px;
        }
        label { 
            display: block; 
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        input, select, textarea { 
            width: 100%; 
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        button { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }
        button:hover { 
            transform: translateY(-2px);
        }
        .result { 
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        .success { 
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Create Content</h1>
        
        <form id="contentForm">
            <div class="form-group">
                <label>Topic</label>
                <input type="text" id="topic" placeholder="e.g., AI Technology" required>
            </div>
            
            <div class="form-group">
                <label>Content Angle</label>
                <input type="text" id="angle" placeholder="e.g., Beginner Guide" required>
            </div>
            
            <div class="form-group">
                <label>Platform</label>
                <select id="platform">
                    <option value="youtube">YouTube</option>
                    <option value="tiktok">TikTok</option>
                    <option value="instagram">Instagram</option>
                    <option value="facebook">Facebook</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="use_ai"> Use AI Generation (0.10 THB)
                </label>
            </div>
            
            <button type="submit">Generate Content</button>
        </form>
        
        <div id="result" class="result"></div>
    </div>
    
    <script>
        document.getElementById('contentForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                topic: document.getElementById('topic').value,
                angle: document.getElementById('angle').value,
                platform: document.getElementById('platform').value,
                use_ai: document.getElementById('use_ai').checked
            };
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('result').innerHTML = `
                    <div class="success">✅ Content Generated!</div>
                    <p><strong>ID:</strong> ${result.content_id}</p>
                    <p><strong>Cost:</strong> ${result.cost} THB</p>
                    <p><strong>Titles:</strong></p>
                    <ul>
                        ${result.script.titles.map(t => `<li>${t}</li>`).join('')}
                    </ul>
                    <p><strong>Hashtags:</strong> ${result.script.hashtags.join(' ')}</p>
                `;
                document.getElementById('result').style.display = 'block';
            }
        });
    </script>
</body>
</html>
    """

if __name__ == '__main__':
    print("="*70)
    print("🚀 AI Content Factory - Web Dashboard")
    print("="*70)
    print("\n📍 Open in browser: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000")
    print("➕ Create: http://localhost:5000/create")
    print("\n⚡ Press Ctrl+C to stop\n")
    print("="*70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)