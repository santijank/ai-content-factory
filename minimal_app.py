#!/usr/bin/env python3
"""
Minimal AI Content Factory App
Basic version for quick testing
"""

import os
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-for-testing')

# Basic HTML template
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Factory</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .btn { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Content Factory</h1>
            <p>Minimal Testing Version</p>
        </div>
        
        <div class="status success">
            ✅ System is running successfully!
        </div>
        
        <div class="status info">
            📊 This is a minimal version for testing purposes.
        </div>
        
        <h3>Available Endpoints:</h3>
        <ul>
            <li><strong>GET /</strong> - This dashboard</li>
            <li><strong>GET /api/stats</strong> - System statistics</li>
            <li><strong>GET /api/trends</strong> - Trending topics (mock data)</li>
            <li><strong>GET /api/opportunities</strong> - Content opportunities (mock data)</li>
            <li><strong>GET /api/health</strong> - Health check</li>
        </ul>
        
        <h3>Quick Actions:</h3>
        <button class="btn" onclick="testAPI('/api/stats')">Test Stats API</button>
        <button class="btn" onclick="testAPI('/api/trends')">Test Trends API</button>
        <button class="btn" onclick="testAPI('/api/health')">Health Check</button>
        
        <div id="result" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; display: none;">
            <h4>API Response:</h4>
            <pre id="response-content"></pre>
        </div>
    </div>
    
    <script>
        async function testAPI(endpoint) {
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                
                document.getElementById('response-content').textContent = JSON.stringify(data, null, 2);
                document.getElementById('result').style.display = 'block';
            } catch (error) {
                document.getElementById('response-content').textContent = 'Error: ' + error.message;
                document.getElementById('result').style.display = 'block';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Content Factory',
        'version': '1.0.0',
        'timestamp': '2025-09-11T05:35:16.132434'
    })

@app.route('/api/stats')
def api_stats():
    """Mock stats endpoint"""
    return jsonify({
        'trends_today': 15,
        'opportunities_count': 8,
        'content_today': 3,
        'cost_today': 75.50,
        'last_updated': '2025-09-11T05:35:16.132434'
    })

@app.route('/api/trends')
def api_trends():
    """Mock trends endpoint"""
    return jsonify([
        {
            'id': '1',
            'topic': 'AI Technology Trends 2025',
            'popularity_score': 8.5,
            'growth_rate': 15.2,
            'category': 'technology',
            'source': 'youtube',
            'keywords': ['AI', 'technology', 'trends']
        },
        {
            'id': '2',
            'topic': 'Thai Street Food Guide',
            'popularity_score': 7.2,
            'growth_rate': 12.8,
            'category': 'food',
            'source': 'google',
            'keywords': ['thai', 'food', 'street']
        }
    ])

@app.route('/api/opportunities')
def api_opportunities():
    """Mock opportunities endpoint"""
    return jsonify([
        {
            'id': '1',
            'trend_id': '1',
            'suggested_angle': '10 AI Tools That Will Change Your Life',
            'estimated_views': 50000,
            'competition_level': 'medium',
            'production_cost': 25.0,
            'estimated_roi': 3.2,
            'status': 'pending'
        },
        {
            'id': '2',
            'trend_id': '2',
            'suggested_angle': 'Best Street Food in Bangkok Under 50 Baht',
            'estimated_views': 35000,
            'competition_level': 'high',
            'production_cost': 40.0,
            'estimated_roi': 2.8,
            'status': 'pending'
        }
    ])

@app.route('/api/content')
def api_content():
    """Mock content endpoint"""
    return jsonify([
        {
            'id': '1',
            'title': 'AI Tools Guide',
            'description': 'Complete guide to AI tools',
            'status': 'completed',
            'platform': 'youtube',
            'created_at': '2025-09-11T04:30:00'
        }
    ])

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting AI Content Factory (Minimal Version)")
    print("📊 Dashboard: http://localhost:5000")
    print("🔗 API Docs: http://localhost:5000/api/health")
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )