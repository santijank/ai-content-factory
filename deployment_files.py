#!/usr/bin/env python3
"""
สคริปต์สร้างไฟล์สำหรับ cloud deployment
"""

import os

# 1. สร้าง requirements.txt
requirements_content = """Flask==3.0.0
aiohttp==3.9.1
python-dotenv==1.0.0
gunicorn==21.2.0
"""

# 2. สร้าง runtime.txt (สำหรับบาง platforms)
runtime_content = """python-3.11.0"""

# 3. สร้าง Procfile (สำหรับ Heroku-style deployment)
procfile_content = """web: gunicorn app:app --host=0.0.0.0 --port=$PORT"""

# 4. สร้าง .gitignore
gitignore_content = """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Local data
data/
content_factory.db
*.db
"""

# 5. สร้าง app_production.py (Production version ของ app.py)
app_production_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Content Factory - Production Web App
"""

from flask import Flask, render_template_string, request, jsonify
import asyncio
import json
import sqlite3
from datetime import datetime
import os
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Database setup
DB_PATH = os.environ.get('DATABASE_PATH', 'content_factory.db')

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

# Initialize database on startup
try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Database initialization error: {e}")

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Factory</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { 
            max-width: 1200px; margin: 0 auto; 
            background: white; border-radius: 20px; padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { color: #667eea; margin-bottom: 30px; font-size: 32px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #f8f9fa; padding: 25px; border-radius: 15px; }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }
        .stat-card .value { font-size: 36px; font-weight: bold; color: #667eea; }
        .form-section { background: #f8f9fa; padding: 30px; border-radius: 15px; margin-bottom: 20px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        input, select, textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 16px; }
        button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
        button:hover { transform: translateY(-2px); }
        .content-list { background: white; border-radius: 10px; margin-top: 20px; }
        .content-item { padding: 20px; border-bottom: 1px solid #eee; }
        .result { margin-top: 20px; padding: 20px; background: #d4edda; border-radius: 8px; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 AI Content Factory</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Content</h3>
                <div class="value" id="totalContent">-</div>
            </div>
            <div class="stat-card">
                <h3>Total Views</h3>
                <div class="value" id="totalViews">-</div>
            </div>
            <div class="stat-card">
                <h3>Success Rate</h3>
                <div class="value">95%</div>
            </div>
            <div class="stat-card">
                <h3>Status</h3>
                <div class="value" style="color: #28a745;">Online</div>
            </div>
        </div>
        
        <div class="form-section">
            <h2>Create New Content</h2>
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
                
                <button type="submit">Generate Content</button>
            </form>
            
            <div id="result" class="result"></div>
        </div>
        
        <div class="content-list" id="contentList">
            <h2>Recent Content</h2>
            <div id="recentItems">Loading...</div>
        </div>
    </div>
    
    <script>
        // Load analytics
        async function loadStats() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();
                document.getElementById('totalContent').textContent = data.total_content;
                document.getElementById('totalViews').textContent = data.total_views.toLocaleString();
            } catch (e) {
                console.error('Error loading stats:', e);
            }
        }
        
        // Generate content
        document.getElementById('contentForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                topic: document.getElementById('topic').value,
                angle: document.getElementById('angle').value,
                platform: document.getElementById('platform').value,
                use_ai: true
            };
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('result').innerHTML = `
                        <h3>✅ Content Generated Successfully!</h3>
                        <p><strong>ID:</strong> ${result.content_id}</p>
                        <p><strong>Cost:</strong> ${result.cost} THB</p>
                        <p><strong>Titles:</strong></p>
                        <ul>${result.script.titles.map(t => `<li>${t}</li>`).join('')}</ul>
                        <p><strong>Hashtags:</strong> ${result.script.hashtags.join(' ')}</p>
                    `;
                    document.getElementById('result').style.display = 'block';
                    loadStats();
                }
            } catch (e) {
                console.error('Error generating content:', e);
            }
        });
        
        // Load initial data
        loadStats();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Dashboard home"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/generate', methods=['POST'])
def generate_content():
    """Generate content API"""
    data = request.json
    
    topic = data.get('topic', 'Unknown')
    angle = data.get('angle', 'General')
    platform = data.get('platform', 'youtube')
    
    # Create content
    script = {
        "titles": [
            f"{topic}: Complete Guide 2025",
            f"Master {topic} - {angle}",
            f"{topic} Explained Simply"
        ],
        "hook": f"Discover the secrets of {topic} with our {angle} approach...",
        "hashtags": [f"#{topic.replace(' ', '')}", "#viral", "#trending2025"]
    }
    
    # Save to database
    try:
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
            1, 0.1, 9.0
        ))
        
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "content_id": content_id,
            "script": script,
            "cost": 0.1
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/analytics')
def get_analytics():
    """Get analytics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM content")
        total_content = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM uploads")
        total_uploads = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "total_content": total_content,
            "total_uploads": total_uploads,
            "total_views": total_content * 1000,  # Mock data
            "total_cost": total_content * 0.1
        })
    except Exception as e:
        return jsonify({
            "total_content": 0,
            "total_uploads": 0,
            "total_views": 0,
            "total_cost": 0
        })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
'''

def create_deployment_files():
    """สร้างไฟล์ทั้งหมด"""
    
    files_to_create = {
        'requirements.txt': requirements_content,
        'runtime.txt': runtime_content,
        'Procfile': procfile_content,
        '.gitignore': gitignore_content,
        'app_production.py': app_production_content
    }
    
    print("Creating deployment files...")
    
    for filename, content in files_to_create.items():
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            print(f"✅ Created: {filename}")
        except Exception as e:
            print(f"❌ Error creating {filename}: {e}")
    
    print("\n📁 Files created successfully!")
    print("\nNext steps:")
    print("1. git init")
    print("2. git add .")
    print("3. git commit -m 'Initial commit'")
    print("4. Push to GitHub")
    print("5. Deploy to cloud platform")

if __name__ == "__main__":
    create_deployment_files()