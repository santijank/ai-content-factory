from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
from datetime import datetime, timedelta
import sqlite3
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import requests
import uuid
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Database connection
def get_db_connection():
    conn = sqlite3.connect('content_factory.db')
    conn.row_factory = sqlite3.Row
    return conn

@dataclass
class TrendData:
    id: str
    source: str
    topic: str
    keywords: List[str]
    popularity_score: float
    growth_rate: float
    category: str
    collected_at: str
    
@dataclass
class ContentOpportunity:
    id: str
    trend_id: str
    suggested_angle: str
    estimated_views: int
    competition_level: str
    production_cost: float
    estimated_roi: float
    priority_score: float
    status: str

# Initialize database
def init_db():
    conn = get_db_connection()
    
    # Create trends table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trends (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            topic TEXT NOT NULL,
            keywords TEXT,
            popularity_score REAL,
            growth_rate REAL,
            category TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT
        )
    ''')
    
    # Create content_opportunities table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS content_opportunities (
            id TEXT PRIMARY KEY,
            trend_id TEXT,
            suggested_angle TEXT,
            estimated_views INTEGER,
            competition_level TEXT,
            production_cost REAL,
            estimated_roi REAL,
            priority_score REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trend_id) REFERENCES trends (id)
        )
    ''')
    
    # Create content_items table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS content_items (
            id TEXT PRIMARY KEY,
            opportunity_id TEXT,
            title TEXT,
            description TEXT,
            content_plan TEXT,
            production_status TEXT DEFAULT 'planning',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (opportunity_id) REFERENCES content_opportunities (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# Mock AI service for demo
class MockAIService:
    def analyze_trend(self, trend_data):
        return {
            "viral_potential": random.randint(6, 10),
            "content_saturation": random.randint(3, 8),
            "audience_interest": random.randint(7, 10),
            "monetization_opportunity": random.randint(5, 9),
            "suggested_angles": [
                f"How to leverage {trend_data['topic']} for beginners",
                f"5 secrets about {trend_data['topic']} no one tells you",
                f"{trend_data['topic']} vs traditional methods"
            ]
        }

ai_service = MockAIService()

# Routes
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/trends')
def trends():
    return render_template('trends.html')

@app.route('/opportunities')
def opportunities():
    return render_template('opportunities.html')

@app.route('/content')
def content():
    return render_template('content.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

# API Routes
@app.route('/api/dashboard-stats')
def get_dashboard_stats():
    conn = get_db_connection()
    
    # Get today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    
    trends_today = conn.execute(
        'SELECT COUNT(*) as count FROM trends WHERE DATE(collected_at) = ?',
        (today,)
    ).fetchone()['count']
    
    opportunities_today = conn.execute(
        'SELECT COUNT(*) as count FROM content_opportunities WHERE DATE(created_at) = ?',
        (today,)
    ).fetchone()['count']
    
    content_created = conn.execute(
        'SELECT COUNT(*) as count FROM content_items WHERE DATE(created_at) = ?',
        (today,)
    ).fetchone()['count']
    
    # Get recent trends
    recent_trends = conn.execute('''
        SELECT * FROM trends 
        ORDER BY collected_at DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get best opportunities
    best_opportunities = conn.execute('''
        SELECT co.*, t.topic, t.category 
        FROM content_opportunities co
        JOIN trends t ON co.trend_id = t.id
        WHERE co.status = 'pending'
        ORDER BY co.priority_score DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'today_stats': {
            'trends_collected': trends_today,
            'opportunities_generated': opportunities_today,
            'content_created': content_created,
            'total_cost': 0,
            'estimated_revenue': 0
        },
        'recent_trends': [dict(row) for row in recent_trends],
        'best_opportunities': [dict(row) for row in best_opportunities]
    })

@app.route('/api/trends')
def get_trends():
    conn = get_db_connection()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category = request.args.get('category', '')
    
    # Build query
    query = 'SELECT * FROM trends'
    params = []
    
    if category:
        query += ' WHERE category = ?'
        params.append(category)
    
    query += ' ORDER BY collected_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])
    
    trends = conn.execute(query, params).fetchall()
    
    # Get total count
    count_query = 'SELECT COUNT(*) as total FROM trends'
    if category:
        count_query += ' WHERE category = ?'
        total = conn.execute(count_query, [category] if category else []).fetchone()['total']
    else:
        total = conn.execute(count_query).fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'trends': [dict(row) for row in trends],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })

@app.route('/api/collect-trends', methods=['POST'])
def collect_trends():
    """Manually trigger trend collection"""
    
    # Mock trend collection
    mock_trends = [
        {
            'id': str(uuid.uuid4()),
            'source': 'youtube',
            'topic': 'AI Content Creation Tools',
            'keywords': json.dumps(['AI', 'content', 'automation', 'tools']),
            'popularity_score': random.uniform(7.0, 9.5),
            'growth_rate': random.uniform(15.0, 45.0),
            'category': 'Technology',
            'raw_data': json.dumps({'views': random.randint(100000, 1000000)})
        },
        {
            'id': str(uuid.uuid4()),
            'source': 'google_trends',
            'topic': 'Sustainable Living 2024',
            'keywords': json.dumps(['sustainable', 'eco-friendly', 'green living', '2024']),
            'popularity_score': random.uniform(6.5, 8.8),
            'growth_rate': random.uniform(20.0, 35.0),
            'category': 'Lifestyle',
            'raw_data': json.dumps({'search_volume': random.randint(50000, 500000)})
        },
        {
            'id': str(uuid.uuid4()),
            'source': 'youtube',
            'topic': 'Remote Work Productivity',
            'keywords': json.dumps(['remote work', 'productivity', 'work from home', 'tips']),
            'popularity_score': random.uniform(8.0, 9.2),
            'growth_rate': random.uniform(10.0, 30.0),
            'category': 'Business',
            'raw_data': json.dumps({'views': random.randint(200000, 800000)})
        }
    ]
    
    conn = get_db_connection()
    
    for trend in mock_trends:
        conn.execute('''
            INSERT OR REPLACE INTO trends 
            (id, source, topic, keywords, popularity_score, growth_rate, category, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trend['id'], trend['source'], trend['topic'], trend['keywords'],
            trend['popularity_score'], trend['growth_rate'], trend['category'], trend['raw_data']
        ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'Collected {len(mock_trends)} new trends',
        'trends': mock_trends
    })

@app.route('/api/analyze-trend/<trend_id>', methods=['POST'])
def analyze_trend(trend_id):
    """Analyze a specific trend and generate opportunities"""
    
    conn = get_db_connection()
    
    # Get trend data
    trend = conn.execute('SELECT * FROM trends WHERE id = ?', (trend_id,)).fetchone()
    
    if not trend:
        return jsonify({'error': 'Trend not found'}), 404
    
    # Mock AI analysis
    analysis = ai_service.analyze_trend(dict(trend))
    
    # Generate opportunities
    opportunities = []
    for i, angle in enumerate(analysis['suggested_angles']):
        opportunity_id = f"{trend_id}_opp_{i}"
        
        opportunity = {
            'id': opportunity_id,
            'trend_id': trend_id,
            'suggested_angle': angle,
            'estimated_views': random.randint(10000, 100000),
            'competition_level': random.choice(['low', 'medium', 'high']),
            'production_cost': random.uniform(50, 500),
            'estimated_roi': random.uniform(2.0, 8.0),
            'priority_score': random.uniform(6.0, 9.5),
            'status': 'pending'
        }
        
        conn.execute('''
            INSERT OR REPLACE INTO content_opportunities
            (id, trend_id, suggested_angle, estimated_views, competition_level, 
             production_cost, estimated_roi, priority_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            opportunity['id'], opportunity['trend_id'], opportunity['suggested_angle'],
            opportunity['estimated_views'], opportunity['competition_level'],
            opportunity['production_cost'], opportunity['estimated_roi'],
            opportunity['priority_score'], opportunity['status']
        ))
        
        opportunities.append(opportunity)
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'analysis': analysis,
        'opportunities': opportunities
    })

@app.route('/api/opportunities')
def get_opportunities():
    conn = get_db_connection()
    
    status = request.args.get('status', '')
    sort_by = request.args.get('sort_by', 'priority_score')
    order = request.args.get('order', 'desc')
    
    # Build query
    query = '''
        SELECT co.*, t.topic, t.category, t.source
        FROM content_opportunities co
        JOIN trends t ON co.trend_id = t.id
    '''
    params = []
    
    if status:
        query += ' WHERE co.status = ?'
        params.append(status)
    
    query += f' ORDER BY co.{sort_by} {order.upper()}'
    
    opportunities = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify({
        'opportunities': [dict(row) for row in opportunities]
    })

@app.route('/api/opportunity/<opportunity_id>/select', methods=['POST'])
def select_opportunity(opportunity_id):
    """Mark an opportunity as selected for content creation"""
    
    conn = get_db_connection()
    
    # Update opportunity status
    conn.execute(
        'UPDATE content_opportunities SET status = ? WHERE id = ?',
        ('selected', opportunity_id)
    )
    
    # Create content item
    content_id = f"content_{opportunity_id}"
    conn.execute('''
        INSERT INTO content_items (id, opportunity_id, production_status)
        VALUES (?, ?, ?)
    ''', (content_id, opportunity_id, 'planning'))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Opportunity selected for content creation',
        'content_id': content_id
    })

@app.route('/api/content-items')
def get_content_items():
    conn = get_db_connection()
    
    content_items = conn.execute('''
        SELECT ci.*, co.suggested_angle, t.topic, t.category
        FROM content_items ci
        JOIN content_opportunities co ON ci.opportunity_id = co.id
        JOIN trends t ON co.trend_id = t.id
        ORDER BY ci.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'content_items': [dict(row) for row in content_items]
    })

if __name__ == '__main__':
    print("🚀 Starting AI Content Factory...")
    init_db()
    print("🌐 Starting web server...")
    app.run(debug=True, host='0.0.0.0', port=5000)