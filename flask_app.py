import os
from flask import Flask, jsonify, render_template_string, request
import random

app = Flask(__name__)

# HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Content Factory</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { 
            background: rgba(255,255,255,0.95); 
            color: #333; padding: 30px; border-radius: 15px; text-align: center; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }
        .section { 
            background: rgba(255,255,255,0.95); 
            padding: 25px; margin: 20px 0; border-radius: 15px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        button { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; border: none; padding: 12px 24px; 
            border-radius: 8px; cursor: pointer; margin: 8px; font-size: 16px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            font-weight: 600;
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        button:active { transform: translateY(0); }
        #result { 
            margin-top: 20px; padding: 20px; 
            background: rgba(248,249,250,0.8); 
            border-radius: 10px; 
            border-left: 4px solid #667eea;
        }
        .form-group { margin: 15px 0; }
        input, select { 
            width: 100%; padding: 12px; border: 2px solid #e9ecef; 
            border-radius: 8px; font-size: 14px;
            transition: border-color 0.3s ease;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        label { 
            display: block; margin-bottom: 8px; font-weight: 600; 
            color: #495057;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            background: #28a745;
            color: white;
            margin-left: 10px;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .feature-card {
            padding: 20px;
            background: rgba(255,255,255,0.7);
            border-radius: 10px;
            border: 1px solid rgba(102, 126, 234, 0.2);
            text-align: center;
            transition: transform 0.2s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Content Factory</h1>
            <p>Create viral content with AI - Production Ready!</p>
            <span class="status-badge">LIVE</span>
        </div>
        
        <div class="feature-grid">
            <div class="feature-card">
                <h3>📊 Trend Analysis</h3>
                <p>AI-powered trend detection</p>
            </div>
            <div class="feature-card">
                <h3>🎬 Content Generation</h3>
                <p>Automated content creation</p>
            </div>
            <div class="feature-card">
                <h3>📱 Multi-Platform</h3>
                <p>Deploy across all platforms</p>
            </div>
        </div>
        
        <div class="section">
            <h2>Content Generator</h2>
            <div class="form-group">
                <label>Topic:</label>
                <input type="text" id="topic" placeholder="e.g., AI Technology, Gaming, Cooking, Travel">
            </div>
            <div class="form-group">
                <label>Platform:</label>
                <select id="platform">
                    <option value="youtube">📺 YouTube</option>
                    <option value="tiktok">🎵 TikTok</option>
                    <option value="instagram">📸 Instagram</option>
                    <option value="facebook">👥 Facebook</option>
                </select>
            </div>
            <div class="form-group">
                <label>Content Style:</label>
                <select id="style">
                    <option value="tutorial">📚 Tutorial</option>
                    <option value="entertainment">🎭 Entertainment</option>
                    <option value="news">📰 News</option>
                    <option value="review">⭐ Review</option>
                </select>
            </div>
            <button onclick="generateContent()">🎯 Generate Content</button>
            <button onclick="getStats()">📊 View Stats</button>
            <button onclick="getTrends()">🔥 Get Trends</button>
        </div>
        
        <div id="result"></div>
    </div>
    
    <script>
        function generateContent() {
            const topic = document.getElementById('topic').value || 'AI Technology';
            const platform = document.getElementById('platform').value;
            const style = document.getElementById('style').value;
            
            document.getElementById('result').innerHTML = '<div class="loading"></div> Generating content...';
            
            fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    topic: topic, 
                    platform: platform,
                    style: style
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerHTML = `
                    <div class="section">
                        <h3>✨ Generated Content</h3>
                        <p><strong>Topic:</strong> ${data.topic}</p>
                        <p><strong>Platform:</strong> ${data.platform}</p>
                        <p><strong>Style:</strong> ${data.style}</p>
                        <h4>📝 Suggested Titles:</h4>
                        <ul>
                            ${data.titles.map(t => '<li>' + t + '</li>').join('')}
                        </ul>
                        <h4>🎣 Hook:</h4>
                        <p style="background: #e8f4f8; padding: 10px; border-radius: 5px; font-style: italic;">"${data.hook}"</p>
                        <h4>🏷️ Hashtags:</h4>
                        <p style="color: #1da1f2;">${data.hashtags.join(' ')}</p>
                        <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                            <span><strong>💰 Cost:</strong> ${data.cost} THB</span>
                            <span><strong>⏱️ Est. Time:</strong> ${data.production_time}</span>
                            <span><strong>🎯 Score:</strong> ${data.viral_score}/10</span>
                        </div>
                    </div>
                `;
            })
            .catch(error => {
                document.getElementById('result').innerHTML = `
                    <div class="section" style="border-left-color: #dc3545;">
                        <h3>❌ Error</h3>
                        <p>Failed to generate content. Please try again.</p>
                    </div>
                `;
            });
        }
        
        function getStats() {
            document.getElementById('result').innerHTML = '<div class="loading"></div> Loading stats...';
            
            fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerHTML = `
                    <div class="section">
                        <h3>📊 System Statistics</h3>
                        <div class="feature-grid">
                            <div class="feature-card">
                                <h4>📈 Total Generated</h4>
                                <h2 style="color: #667eea;">${data.total}</h2>
                            </div>
                            <div class="feature-card">
                                <h4>🔥 Today</h4>
                                <h2 style="color: #28a745;">${data.today}</h2>
                            </div>
                            <div class="feature-card">
                                <h4>⚡ Success Rate</h4>
                                <h2 style="color: #ffc107;">${data.success_rate}</h2>
                            </div>
                            <div class="feature-card">
                                <h4>🕒 Uptime</h4>
                                <h2 style="color: #17a2b8;">${data.uptime}</h2>
                            </div>
                        </div>
                        <p><strong>Status:</strong> <span class="status-badge">${data.status.toUpperCase()}</span></p>
                    </div>
                `;
            });
        }
        
        function getTrends() {
            document.getElementById('result').innerHTML = '<div class="loading"></div> Fetching latest trends...';
            
            fetch('/api/trends')
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerHTML = `
                    <div class="section">
                        <h3>🔥 Trending Now</h3>
                        <div class="feature-grid">
                            ${data.trends.map(trend => `
                                <div class="feature-card">
                                    <h4>${trend.title}</h4>
                                    <p>🔥 ${trend.score}/10</p>
                                    <p style="font-size: 12px; color: #666;">${trend.category}</p>
                                </div>
                            `).join('')}
                        </div>
                        <p><strong>Last Updated:</strong> ${data.last_updated}</p>
                    </div>
                `;
            });
        }
        
        // Auto-load stats on page load
        window.onload = function() {
            getStats();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/generate', methods=['POST'])
def generate_content():
    try:
        data = request.json or {}
        topic = data.get('topic', 'Unknown Topic')
        platform = data.get('platform', 'youtube')
        style = data.get('style', 'tutorial')
        
        # Simulate AI content generation
        titles = [
            f"{topic}: Complete Guide 2025 ({style.title()})",
            f"Master {topic} in 10 Minutes - {style.title()} Style",
            f"{topic} - Everything You Need to Know",
            f"🔥 {topic} Secrets Revealed",
            f"Why Everyone is Talking About {topic}"
        ]
        
        hooks = {
            'tutorial': f"Want to learn {topic}? This step-by-step guide will make you an expert!",
            'entertainment': f"You won't believe what happens when we try {topic}!",
            'news': f"Breaking: {topic} just changed everything you thought you knew!",
            'review': f"I tested {topic} for 30 days - here's what really happened..."
        }
        
        response = {
            "success": True,
            "topic": topic,
            "platform": platform.upper(),
            "style": style.title(),
            "titles": titles[:3],
            "hook": hooks.get(style, f"Amazing {topic} content coming right up!"),
            "hashtags": [
                f"#{topic.replace(' ', '').lower()}", 
                "#viral", 
                "#trending2025", 
                f"#{style}",
                f"#{platform}"
            ],
            "cost": round(random.uniform(0.05, 2.50), 2),
            "production_time": f"{random.randint(15, 90)} minutes",
            "viral_score": random.randint(6, 10),
            "generated_at": "2025-01-20T10:30:00Z"
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    return jsonify({
        "total": random.randint(150, 500),
        "today": random.randint(8, 25),
        "status": "active",
        "uptime": f"{random.randint(2, 48)} hours {random.randint(10, 59)} minutes",
        "success_rate": f"{random.randint(94, 99)}.{random.randint(0, 9)}%"
    })

@app.route('/api/trends')
def get_trends():
    trends = [
        {"title": "AI Technology", "score": 9, "category": "Tech"},
        {"title": "Cryptocurrency", "score": 8, "category": "Finance"},
        {"title": "Climate Change", "score": 7, "category": "Environment"},
        {"title": "Space Exploration", "score": 9, "category": "Science"},
        {"title": "Gaming", "score": 8, "category": "Entertainment"},
        {"title": "Health & Fitness", "score": 7, "category": "Lifestyle"}
    ]
    
    return jsonify({
        "trends": random.sample(trends, 4),
        "last_updated": "2025-01-20T15:30:00Z"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "service": "AI Content Factory",
        "version": "1.0.0",
        "environment": "production"
    })

# ✅ Entry point for production
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)