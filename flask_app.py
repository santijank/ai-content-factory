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
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; padding: 30px; border-radius: 10px; text-align: center; }
        .section { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; 
                  box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        button { background: #667eea; color: white; border: none; padding: 12px 24px; 
                border-radius: 5px; cursor: pointer; margin: 5px; font-size: 16px; }
        button:hover { background: #5a6fd8; }
        #result { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        .form-group { margin: 15px 0; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI Content Factory</h1>
            <p>Create viral content with AI - Now with Flask!</p>
        </div>
        
        <div class="section">
            <h2>Content Generator</h2>
            <div class="form-group">
                <label>Topic:</label>
                <input type="text" id="topic" placeholder="e.g., AI Technology, Gaming, Cooking">
            </div>
            <div class="form-group">
                <label>Platform:</label>
                <select id="platform">
                    <option value="youtube">YouTube</option>
                    <option value="tiktok">TikTok</option>
                    <option value="instagram">Instagram</option>
                    <option value="facebook">Facebook</option>
                </select>
            </div>
            <button onclick="generateContent()">Generate Content</button>
            <button onclick="getStats()">View Stats</button>
        </div>
        
        <div id="result"></div>
    </div>
    
    <script>
        function generateContent() {
            const topic = document.getElementById('topic').value || 'AI Technology';
            const platform = document.getElementById('platform').value;
            
            document.getElementById('result').innerHTML = '<p>Generating...</p>';
            
            fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({topic: topic, platform: platform})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerHTML = `
                    <div class="section">
                        <h3>Generated Content</h3>
                        <p><strong>Topic:</strong> ${data.topic}</p>
                        <p><strong>Platform:</strong> ${data.platform}</p>
                        <p><strong>Titles:</strong></p>
                        <ul>
                            ${data.titles.map(t => '<li>' + t + '</li>').join('')}
                        </ul>
                        <p><strong>Hook:</strong> ${data.hook}</p>
                        <p><strong>Hashtags:</strong> ${data.hashtags.join(' ')}</p>
                        <p><strong>Cost:</strong> ${data.cost} THB</p>
                    </div>
                `;
            });
        }
        
        function getStats() {
            fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerHTML = `
                    <div class="section">
                        <h3>System Stats</h3>
                        <p><strong>Total Generated:</strong> ${data.total}</p>
                        <p><strong>Today:</strong> ${data.today}</p>
                        <p><strong>Status:</strong> ${data.status}</p>
                        <p><strong>Uptime:</strong> ${data.uptime}</p>
                    </div>
                `;
            });
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
    data = request.json or {}
    topic = data.get('topic', 'Unknown Topic')
    platform = data.get('platform', 'youtube')
    
    response = {
        "success": True,
        "topic": topic,
        "platform": platform.upper(),
        "titles": [
            f"{topic}: Complete Guide 2025",
            f"Master {topic} in 10 Minutes",
            f"{topic} - Everything You Need to Know"
        ],
        "hook": f"Want to learn about {topic}? This video will change everything you know!",
        "hashtags": [f"#{topic.replace(' ', '')}", "#viral", "#trending2025", "#tutorial"],
        "cost": 0.05,
        "generated_at": "2025-01-20T10:30:00Z"
    }
    return jsonify(response)

@app.route('/api/stats')
def get_stats():
    return jsonify({
        "total": random.randint(50, 200),
        "today": random.randint(3, 15),
        "status": "active",
        "uptime": "2 hours 15 minutes",
        "success_rate": "96.5%"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "flask"})

# ✅ ส่วนนี้จะใช้เฉพาะตอนรัน local เท่านั้น
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
