# ai_content_dashboard.py - Comprehensive Dashboard for Real Integration Pipeline

import sqlite3
import json
import os
import subprocess
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, render_template_string, jsonify, request, redirect, url_for
import threading
import time

app = Flask(__name__)
app.secret_key = 'ai_content_factory_secret_key'

# Enhanced HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Factory Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .header h1 {
            color: #4338ca;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .header-info {
            color: #64748b;
            font-size: 0.9rem;
        }
        
        .header-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: #4338ca;
            color: white;
        }
        
        .btn-primary:hover {
            background: #3730a3;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background: #059669;
            color: white;
        }
        
        .btn-success:hover {
            background: #047857;
            transform: translateY(-2px);
        }
        
        .btn-warning {
            background: #d97706;
            color: white;
        }
        
        .btn-warning:hover {
            background: #b45309;
            transform: translateY(-2px);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .stat-label {
            color: #64748b;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .stat-trend {
            font-size: 0.8rem;
            margin-top: 5px;
        }
        
        .trend-up { color: #059669; }
        .trend-down { color: #dc2626; }
        .trend-stable { color: #d97706; }
        
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        @media (max-width: 1024px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        
        .section h2 {
            color: #374151;
            margin-bottom: 20px;
            font-size: 1.4rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .trend-item, .opportunity-item {
            padding: 15px;
            margin-bottom: 12px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .trend-item:hover, .opportunity-item:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .trend-item {
            border-left: 4px solid #3b82f6;
            background: #f8fafc;
        }
        
        .opportunity-item {
            border-left: 4px solid #10b981;
            background: #f0fdf4;
        }
        
        .item-title {
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 8px;
            font-size: 1rem;
        }
        
        .item-meta {
            color: #64748b;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        .score-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 8px;
        }
        
        .score-high { background: #dcfce7; color: #166534; }
        .score-medium { background: #fef3c7; color: #92400e; }
        .score-low { background: #fee2e2; color: #991b1b; }
        
        .pipeline-status {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-running { background: #fbbf24; animation: pulse 2s infinite; }
        .status-success { background: #10b981; }
        .status-error { background: #ef4444; }
        .status-idle { background: #6b7280; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .error-banner {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .success-banner {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 3px solid #f3f4f6;
            border-top: 3px solid #4338ca;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .tabs {
            display: flex;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 5px;
            margin-bottom: 20px;
        }
        
        .tab {
            flex: 1;
            padding: 12px 20px;
            text-align: center;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .tab.active {
            background: #4338ca;
            color: white;
        }
        
        .tab:not(.active):hover {
            background: #f8fafc;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #64748b;
        }
        
        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        
        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #64748b;
            font-size: 0.85rem;
        }
        
        .refresh-countdown {
            font-weight: 600;
            color: #4338ca;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div>
                <h1>🚀 AI Content Factory</h1>
                <div class="header-info">
                    Last updated: <span id="lastUpdate">{{ last_update }}</span>
                    <div class="auto-refresh">
                        Auto-refresh in <span class="refresh-countdown" id="countdown">60</span>s
                    </div>
                </div>
            </div>
            <div class="header-actions">
                <button class="btn btn-success" onclick="runPipeline()">
                    ▶️ Run Pipeline
                </button>
                <button class="btn btn-primary" onclick="location.reload()">
                    🔄 Refresh
                </button>
                <button class="btn btn-warning" onclick="toggleAutoRefresh()">
                    ⏸️ Auto-refresh
                </button>
            </div>
        </div>

        <!-- Pipeline Status -->
        <div class="pipeline-status">
            <h3>Pipeline Status</h3>
            <div id="pipelineStatus">
                <span class="status-indicator status-{{ pipeline_status }}"></span>
                {{ pipeline_message }}
            </div>
        </div>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" style="color: #3b82f6;">{{ stats.youtube_trends }}</div>
                <div class="stat-label">YouTube Trends</div>
                <div class="stat-trend trend-{{ stats.youtube_trend }}">
                    {{ stats.youtube_change }}
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #10b981;">{{ stats.google_trends }}</div>
                <div class="stat-label">Google Trends</div>
                <div class="stat-trend trend-{{ stats.google_trend }}">
                    {{ stats.google_change }}
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #f59e0b;">{{ stats.opportunities }}</div>
                <div class="stat-label">Opportunities</div>
                <div class="stat-trend trend-{{ stats.opportunities_trend }}">
                    {{ stats.opportunities_change }}
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #8b5cf6;">{{ stats.api_calls }}</div>
                <div class="stat-label">API Calls Today</div>
                <div class="stat-trend trend-{{ stats.api_trend }}">
                    {{ stats.api_change }}
                </div>
            </div>
        </div>

        <!-- Loading Indicator -->
        <div class="loading" id="loadingIndicator">
            <div class="spinner"></div>
            <div>Running pipeline...</div>
        </div>

        <!-- Message Banners -->
        {% if success_message %}
        <div class="success-banner">{{ success_message }}</div>
        {% endif %}
        
        {% if error_message %}
        <div class="error-banner">{{ error_message }}</div>
        {% endif %}

        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="showTab('overview')">📊 Overview</div>
            <div class="tab" onclick="showTab('trends')">📈 Trends</div>
            <div class="tab" onclick="showTab('opportunities')">💡 Opportunities</div>
            <div class="tab" onclick="showTab('analytics')">📊 Analytics</div>
        </div>

        <!-- Tab Content: Overview -->
        <div id="overview" class="tab-content active">
            <div class="content-grid">
                <!-- Latest YouTube Trends -->
                <div class="section">
                    <h2>📺 Latest YouTube Trends</h2>
                    {% if youtube_trends %}
                        {% for trend in youtube_trends[:5] %}
                        <div class="trend-item">
                            <div class="item-title">{{ trend.title }}</div>
                            <div class="item-meta">
                                👀 {{ "{:,}".format(trend.view_count) }} views • 
                                👍 {{ "{:,}".format(trend.like_count) }} likes<br>
                                📺 {{ trend.channel_title }}
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="empty-state">
                            <div class="empty-state-icon">📭</div>
                            <div>No YouTube trends available</div>
                        </div>
                    {% endif %}
                </div>

                <!-- Top Opportunities -->
                <div class="section">
                    <h2>🎯 Top Opportunities</h2>
                    {% if opportunities %}
                        {% for opp in opportunities[:5] %}
                        <div class="opportunity-item">
                            <div class="item-title">{{ opp.trend_topic }}</div>
                            <div class="item-meta">
                                <span class="score-badge {% if opp.overall_score >= 7 %}score-high{% elif opp.overall_score >= 5 %}score-medium{% else %}score-low{% endif %}">
                                    {{ "%.1f"|format(opp.overall_score) }}/10
                                </span>
                                {{ opp.suggested_angle }}<br>
                                🔥 Viral: {{ opp.viral_potential }}/10 • 
                                📊 Saturation: {{ opp.content_saturation }}/10
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="empty-state">
                            <div class="empty-state-icon">💡</div>
                            <div>No opportunities generated yet</div>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Tab Content: Trends -->
        <div id="trends" class="tab-content">
            <div class="content-grid">
                <!-- All YouTube Trends -->
                <div class="section">
                    <h2>📺 All YouTube Trends</h2>
                    {% for trend in youtube_trends %}
                    <div class="trend-item">
                        <div class="item-title">{{ trend.title }}</div>
                        <div class="item-meta">
                            👀 {{ "{:,}".format(trend.view_count) }} views • 
                            👍 {{ "{:,}".format(trend.like_count) }} likes • 
                            📺 {{ trend.channel_title }}<br>
                            📅 {{ trend.collected_at }}
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <!-- Google Trends -->
                <div class="section">
                    <h2>🔍 Google Trending Keywords</h2>
                    {% for trend in google_trends %}
                    <div class="trend-item">
                        <div class="item-title">{{ trend.keyword }}</div>
                        <div class="item-meta">
                            Interest Score: 
                            <span class="score-badge {% if trend.interest_score >= 70 %}score-high{% elif trend.interest_score >= 50 %}score-medium{% else %}score-low{% endif %}">
                                {{ trend.interest_score }}/100
                            </span>
                            📅 {{ trend.collected_at }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Tab Content: Opportunities -->
        <div id="opportunities" class="tab-content">
            <div class="section">
                <h2>💡 All Content Opportunities</h2>
                {% for opp in opportunities %}
                <div class="opportunity-item">
                    <div class="item-title">{{ opp.trend_topic }}</div>
                    <div class="item-meta">
                        Overall Score: 
                        <span class="score-badge {% if opp.overall_score >= 7 %}score-high{% elif opp.overall_score >= 5 %}score-medium{% else %}score-low{% endif %}">
                            {{ "%.1f"|format(opp.overall_score) }}/10
                        </span><br>
                        📝 Angle: {{ opp.suggested_angle }}<br>
                        🔥 Viral: {{ opp.viral_potential }}/10 • 
                        📊 Saturation: {{ opp.content_saturation }}/10 • 
                        👥 Interest: {{ opp.audience_interest }}/10 • 
                        💰 Monetization: {{ opp.monetization_opportunity }}/10<br>
                        🧠 Analysis: {{ opp.reasoning }}<br>
                        📅 Created: {{ opp.created_at }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Tab Content: Analytics -->
        <div id="analytics" class="tab-content">
            <div class="content-grid">
                <div class="section">
                    <h2>📊 Performance Analytics</h2>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #6366f1;">{{ analytics.total_trends }}</div>
                        <div class="stat-label">Total Trends Collected</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #ec4899;">{{ analytics.avg_score }}</div>
                        <div class="stat-label">Average Opportunity Score</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #14b8a6;">{{ analytics.success_rate }}%</div>
                        <div class="stat-label">Pipeline Success Rate</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🎯 Category Breakdown</h2>
                    {% for category in analytics.categories %}
                    <div class="trend-item">
                        <div class="item-title">{{ category.name }}</div>
                        <div class="item-meta">
                            Count: {{ category.count }} • 
                            Avg Score: {{ "%.1f"|format(category.avg_score) }}/10
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <script>
        let autoRefreshEnabled = true;
        let countdownTimer = 60;
        
        // Tab functionality
        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
        
        // Run pipeline
        async function runPipeline() {
            const loadingIndicator = document.getElementById('loadingIndicator');
            const pipelineStatus = document.getElementById('pipelineStatus');
            
            loadingIndicator.style.display = 'block';
            pipelineStatus.innerHTML = '<span class="status-indicator status-running"></span>Running pipeline...';
            
            try {
                const response = await fetch('/api/run-pipeline', {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.success) {
                    pipelineStatus.innerHTML = '<span class="status-indicator status-success"></span>Pipeline completed successfully';
                    setTimeout(() => location.reload(), 2000);
                } else {
                    pipelineStatus.innerHTML = '<span class="status-indicator status-error"></span>Pipeline failed: ' + result.error;
                }
            } catch (error) {
                pipelineStatus.innerHTML = '<span class="status-indicator status-error"></span>Error: ' + error.message;
            }
            
            loadingIndicator.style.display = 'none';
        }
        
        // Toggle auto-refresh
        function toggleAutoRefresh() {
            autoRefreshEnabled = !autoRefreshEnabled;
            const btn = event.target;
            if (autoRefreshEnabled) {
                btn.textContent = '⏸️ Auto-refresh';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-warning');
            } else {
                btn.textContent = '▶️ Auto-refresh';
                btn.classList.remove('btn-warning');
                btn.classList.add('btn-success');
            }
        }
        
        // Auto-refresh countdown
        function updateCountdown() {
            if (autoRefreshEnabled) {
                countdownTimer--;
                document.getElementById('countdown').textContent = countdownTimer;
                
                if (countdownTimer <= 0) {
                    location.reload();
                }
            } else {
                document.getElementById('countdown').textContent = 'Paused';
            }
        }
        
        // Start countdown
        setInterval(updateCountdown, 1000);
        
        // Update last update time
        document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
    </script>
</body>
</html>
"""

class DatabaseManager:
    def __init__(self, db_path: str = 'content_factory.db'):
        self.db_path = db_path
        
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_trends_data(self) -> Dict[str, List]:
        """Get trends data from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # YouTube trends
            cursor.execute("""
                SELECT * FROM trends 
                WHERE source = 'youtube' 
                ORDER BY collected_at DESC 
                LIMIT 20
            """)
            youtube_raw = cursor.fetchall()
            
            # Google trends  
            cursor.execute("""
                SELECT * FROM trends 
                WHERE source = 'google_trends' 
                ORDER BY collected_at DESC 
                LIMIT 15
            """)
            google_raw = cursor.fetchall()
            
            conn.close()
            
            # Process YouTube trends
            youtube_trends = []
            for trend in youtube_raw:
                try:
                    raw_data = json.loads(trend['raw_data']) if trend['raw_data'] else {}
                    youtube_trends.append({
                        'title': trend['topic'],
                        'view_count': raw_data.get('view_count', 0),
                        'like_count': raw_data.get('like_count', 0),
                        'channel_title': raw_data.get('channel_title', 'Unknown'),
                        'collected_at': trend['collected_at']
                    })
                except:
                    youtube_trends.append({
                        'title': trend['topic'],
                        'view_count': 0,
                        'like_count': 0,
                        'channel_title': 'Unknown',
                        'collected_at': trend['collected_at']
                    })
            
            # Process Google trends
            google_trends = []
            for trend in google_raw:
                google_trends.append({
                    'keyword': trend['topic'],
                    'interest_score': int(trend['popularity_score'] or 50),
                    'collected_at': trend['collected_at']
                })
            
            return {
                'youtube_trends': youtube_trends,
                'google_trends': google_trends
            }
            
        except Exception as e:
            print(f"Database error: {e}")
            return {'youtube_trends': [], 'google_trends': []}
    
    def get_opportunities_data(self) -> List[Dict]:
        """Get content opportunities from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM content_opportunities 
                ORDER BY overall_score DESC, created_at DESC
                LIMIT 50
            """)
            opportunities_raw = cursor.fetchall()
            conn.close()
            
            opportunities = []
            for opp in opportunities_raw:
                opportunities.append({
                    'trend_topic': opp['trend_topic'],
                    'suggested_angle': opp['suggested_angle'] or 'Content creation',
                    'viral_potential': opp['viral_potential'] or 0,
                    'content_saturation': opp['content_saturation'] or 0,
                    'audience_interest': opp['audience_interest'] or 0,
                    'monetization_opportunity': opp['monetization_opportunity'] or 0,
                    'overall_score': opp['overall_score'] or 0,
                    'reasoning': opp['reasoning'] or 'AI analysis',
                    'created_at': opp['created_at']
                })
            
            return opportunities
            
        except Exception as e:
            print(f"Database error: {e}")
            return []
    
    def get_analytics_data(self) -> Dict:
        """Get analytics data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total trends
            cursor.execute("SELECT COUNT(*) as count FROM trends")
            total_trends = cursor.fetchone()['count']
            
            # Average opportunity score
            cursor.execute("SELECT AVG(overall_score) as avg_score FROM content_opportunities")
            avg_score_result = cursor.fetchone()
            avg_score = round(avg_score_result['avg_score'] or 0, 1)
            
            # Category breakdown
            cursor.execute("""
                SELECT reasoning, COUNT(*) as count, AVG(overall_score) as avg_score
                FROM content_opportunities 
                WHERE reasoning IS NOT NULL
                GROUP BY reasoning
                ORDER BY count DESC
                LIMIT 10
            """)
            categories_raw = cursor.fetchall()
            
            categories = []
            for cat in categories_raw:
                category_name = cat['reasoning'].split(':')[0] if ':' in cat['reasoning'] else 'General'
                categories.append({
                    'name': category_name,
                    'count': cat['count'],
                    'avg_score': round(cat['avg_score'] or 0, 1)
                })
            
            conn.close()
            
            return {
                'total_trends': total_trends,
                'avg_score': avg_score,
                'success_rate': 95,  # Mock success rate
                'categories': categories
            }
            
        except Exception as e:
            print(f"Analytics error: {e}")
            return {
                'total_trends': 0,
                'avg_score': 0,
                'success_rate': 0,
                'categories': []
            }
    
    def get_stats_with_trends(self) -> Dict:
        """Get statistics with trend indicators"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Current counts
            cursor.execute("SELECT COUNT(*) as count FROM trends WHERE source = 'youtube'")
            youtube_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM trends WHERE source = 'google_trends'")
            google_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM content_opportunities")
            opportunities_count = cursor.fetchone()['count']
            
            # API calls today
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*) as count FROM trends 
                WHERE DATE(collected_at) = ?
            """, (today,))
            api_calls_today = cursor.fetchone()['count']
            
            conn.close()
            
            # Mock trend calculations (you can enhance this with historical data)
            return {
                'youtube_trends': youtube_count,
                'youtube_trend': 'up',
                'youtube_change': '+5 from yesterday',
                
                'google_trends': google_count,
                'google_trend': 'stable',
                'google_change': 'No change',
                
                'opportunities': opportunities_count,
                'opportunities_trend': 'up',
                'opportunities_change': '+3 new today',
                
                'api_calls': api_calls_today,
                'api_trend': 'stable',
                'api_change': 'Within limits'
            }
            
        except Exception as e:
            print(f"Stats error: {e}")
            return {
                'youtube_trends': 0, 'youtube_trend': 'stable', 'youtube_change': 'No data',
                'google_trends': 0, 'google_trend': 'stable', 'google_change': 'No data',
                'opportunities': 0, 'opportunities_trend': 'stable', 'opportunities_change': 'No data',
                'api_calls': 0, 'api_trend': 'stable', 'api_change': 'No data'
            }

class PipelineRunner:
    def __init__(self):
        self.is_running = False
        self.last_run = None
        self.status = "idle"
        self.message = "Ready to run pipeline"
    
    def run_pipeline_async(self):
        """Run pipeline in background thread"""
        def run():
            try:
                self.is_running = True
                self.status = "running"
                self.message = "Collecting trends and analyzing opportunities..."
                
                # Run the real integration main script
                result = subprocess.run(
                    ['python', 'real_integration_main.py'],
                    capture_output=True,
                    text=True,
                    timeout=180  # 3 minutes timeout
                )
                
                if result.returncode == 0:
                    self.status = "success"
                    self.message = "Pipeline completed successfully"
                    self.last_run = datetime.now()
                else:
                    self.status = "error"
                    self.message = f"Pipeline failed: {result.stderr[:100]}"
                    
            except subprocess.TimeoutExpired:
                self.status = "error"
                self.message = "Pipeline timed out after 3 minutes"
            except FileNotFoundError:
                self.status = "error"
                self.message = "real_integration_main.py not found"
            except Exception as e:
                self.status = "error"
                self.message = f"Error: {str(e)[:100]}"
            finally:
                self.is_running = False
        
        if not self.is_running:
            thread = threading.Thread(target=run)
            thread.daemon = True
            thread.start()
            return True
        return False

# Global instances
db_manager = DatabaseManager()
pipeline_runner = PipelineRunner()

@app.route('/')
def dashboard():
    """Main dashboard route"""
    
    # Get data from database
    trends_data = db_manager.get_trends_data()
    opportunities_data = db_manager.get_opportunities_data()
    analytics_data = db_manager.get_analytics_data()
    stats_data = db_manager.get_stats_with_trends()
    
    # Prepare template data
    template_data = {
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'pipeline_status': pipeline_runner.status,
        'pipeline_message': pipeline_runner.message,
        
        'stats': stats_data,
        
        'youtube_trends': trends_data['youtube_trends'],
        'google_trends': trends_data['google_trends'],
        'opportunities': opportunities_data,
        'analytics': analytics_data,
        
        'success_message': None,
        'error_message': None
    }
    
    return render_template_string(DASHBOARD_HTML, **template_data)

@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data"""
    trends_data = db_manager.get_trends_data()
    opportunities_data = db_manager.get_opportunities_data()
    analytics_data = db_manager.get_analytics_data()
    stats_data = db_manager.get_stats_with_trends()
    
    return jsonify({
        'trends': trends_data,
        'opportunities': opportunities_data,
        'analytics': analytics_data,
        'stats': stats_data,
        'pipeline_status': {
            'status': pipeline_runner.status,
            'message': pipeline_runner.message,
            'is_running': pipeline_runner.is_running,
            'last_run': pipeline_runner.last_run.isoformat() if pipeline_runner.last_run else None
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/run-pipeline', methods=['POST'])
def api_run_pipeline():
    """API endpoint to trigger pipeline"""
    success = pipeline_runner.run_pipeline_async()
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Pipeline started successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Pipeline is already running'
        })

@app.route('/api/pipeline-status')
def api_pipeline_status():
    """Get current pipeline status"""
    return jsonify({
        'status': pipeline_runner.status,
        'message': pipeline_runner.message,
        'is_running': pipeline_runner.is_running,
        'last_run': pipeline_runner.last_run.isoformat() if pipeline_runner.last_run else None
    })

@app.route('/logs')
def view_logs():
    """View pipeline logs"""
    log_file = 'real_integration.log'
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
            
            return f"""
            <html>
            <head><title>Pipeline Logs</title></head>
            <body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #00ff00;">
            <h1>Pipeline Logs</h1>
            <a href="/" style="color: #0080ff;">← Back to Dashboard</a>
            <pre style="background: #000; padding: 20px; border-radius: 5px; overflow-x: auto;">
{logs}
            </pre>
            </body>
            </html>
            """
        except Exception as e:
            return f"Error reading logs: {e}"
    else:
        return "No log file found"

@app.route('/database')
def view_database():
    """Simple database viewer"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        
        html = """
        <html>
        <head><title>Database Viewer</title></head>
        <body style="font-family: Arial; padding: 20px;">
        <h1>Database Viewer</h1>
        <a href="/">← Back to Dashboard</a>
        """
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            
            html += f"""
            <h2>{table} ({count} records)</h2>
            <table border="1" style="border-collapse: collapse; margin-bottom: 20px;">
            """
            
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            
            if rows:
                # Header
                columns = rows[0].keys()
                html += "<tr>" + "".join(f"<th style='padding: 8px; background: #f0f0f0;'>{col}</th>" for col in columns) + "</tr>"
                
                # Data rows
                for row in rows:
                    html += "<tr>"
                    for col in columns:
                        value = str(row[col])[:100] + "..." if len(str(row[col])) > 100 else str(row[col])
                        html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{value}</td>"
                    html += "</tr>"
            
            html += "</table>"
        
        html += "</body></html>"
        conn.close()
        
        return html
        
    except Exception as e:
        return f"Database error: {e}"

if __name__ == '__main__':
    print("🚀 Starting AI Content Factory Dashboard...")
    print("📊 Dashboard URL: http://localhost:5000")
    print("📋 Logs URL: http://localhost:5000/logs")
    print("🗃️ Database URL: http://localhost:5000/database")
    print("=" * 50)
    
    # Check if database exists
    if not os.path.exists('content_factory.db'):
        print("⚠️  Database not found. Run 'python real_integration_main.py' first!")
    else:
        db_size = os.path.getsize('content_factory.db') / 1024
        print(f"✅ Database found: {db_size:.1f} KB")
    
    # Check if main script exists
    if not os.path.exists('real_integration_main.py'):
        print("⚠️  real_integration_main.py not found!")
    else:
        print("✅ Pipeline script found")
    
    print("\nStarting web server...")
    app.run(host='0.0.0.0', port=5000, debug=True)