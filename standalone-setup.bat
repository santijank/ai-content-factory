@echo off
chcp 65001 >nul
echo 🚀 AI Content Factory - Standalone Setup (ไม่ต้องใช้ Docker)
echo ==========================================================
echo.

REM ตรวจสอบ Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python ยังไม่ติดตั้ง
    echo กรุณาติดตั้ง Python จาก: https://python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python ติดตั้งแล้ว
python --version

echo.
echo Step 1: ติดตั้ง Dependencies
echo ----------------------------
if exist "requirements.txt" (
    echo ติดตั้ง Python packages...
    pip install -r requirements.txt
) else (
    echo สร้างไฟล์ requirements.txt...
    (
        echo flask
        echo requests
        echo sqlite3
        echo python-dotenv
        echo schedule
        echo beautifulsoup4
        echo pandas
        echo matplotlib
        echo plotly
    ) > requirements.txt
    
    echo ติดตั้ง packages...
    pip install -r requirements.txt
)

echo.
echo Step 2: สร้าง SQLite Database แทน PostgreSQL
echo --------------------------------------------
echo สร้างไฟล์ database setup สำหรับ SQLite...

(
echo import sqlite3
echo import os
echo.
echo def create_database^(^):
echo     """สร้าง SQLite database และตาราง"""
echo     db_path = 'content_factory.db'
echo     
echo     conn = sqlite3.connect^(db_path^)
echo     cursor = conn.cursor^(^)
echo     
echo     # สร้างตาราง trends
echo     cursor.execute^('''
echo     CREATE TABLE IF NOT EXISTS trends ^(
echo         id TEXT PRIMARY KEY,
echo         source TEXT,
echo         topic TEXT,
echo         keywords TEXT,
echo         popularity_score REAL,
echo         growth_rate REAL,
echo         category TEXT,
echo         region TEXT,
echo         collected_at TIMESTAMP,
echo         raw_data TEXT
echo     ^)
echo     '''^^)
echo     
echo     # สร้างตาราง content_opportunities
echo     cursor.execute^('''
echo     CREATE TABLE IF NOT EXISTS content_opportunities ^(
echo         id TEXT PRIMARY KEY,
echo         trend_id TEXT,
echo         suggested_angle TEXT,
echo         estimated_views INTEGER,
echo         competition_level TEXT,
echo         production_cost REAL,
echo         estimated_roi REAL,
echo         priority_score REAL,
echo         status TEXT,
echo         created_at TIMESTAMP,
echo         FOREIGN KEY ^(trend_id^) REFERENCES trends ^(id^)
echo     ^)
echo     '''^^)
echo     
echo     # สร้างตาราง content_items
echo     cursor.execute^('''
echo     CREATE TABLE IF NOT EXISTS content_items ^(
echo         id TEXT PRIMARY KEY,
echo         opportunity_id TEXT,
echo         title TEXT,
echo         description TEXT,
echo         content_plan TEXT,
echo         production_status TEXT,
echo         assets TEXT,
echo         cost_breakdown TEXT,
echo         created_at TIMESTAMP,
echo         completed_at TIMESTAMP,
echo         FOREIGN KEY ^(opportunity_id^) REFERENCES content_opportunities ^(id^)
echo     ^)
echo     '''^^)
echo     
echo     conn.commit^(^)
echo     conn.close^(^)
echo     print^("✅ Database สร้างเสร็จแล้ว: content_factory.db"^^)
echo.
echo if __name__ == '__main__':
echo     create_database^(^)
) > create_database.py

echo รัน database setup...
python create_database.py

echo.
echo Step 3: สร้าง Environment File
echo -------------------------------
(
    echo # AI Content Factory Environment Variables
    echo DATABASE_URL=sqlite:///content_factory.db
    echo.
    echo # API Keys ^(กรุณาใส่ API Key จริง^)
    echo GROQ_API_KEY=your_groq_api_key_here
    echo OPENAI_API_KEY=your_openai_api_key_here
    echo YOUTUBE_API_KEY=your_youtube_api_key_here
    echo.
    echo # Flask Settings
    echo FLASK_ENV=development
    echo FLASK_DEBUG=1
    echo FLASK_HOST=0.0.0.0
    echo FLASK_PORT=5000
) > .env

echo ✅ สร้างไฟล์ .env แล้ว

echo.
echo Step 4: สร้าง Simple Web App
echo -----------------------------

REM สร้าง simple app.py
(
echo from flask import Flask, render_template, jsonify, request
echo import sqlite3
echo import json
echo from datetime import datetime
echo import os
echo from dotenv import load_dotenv
echo.
echo load_dotenv^(^)
echo.
echo app = Flask^(__name__^)
echo.
echo def get_db_connection^(^):
echo     conn = sqlite3.connect^('content_factory.db'^)
echo     conn.row_factory = sqlite3.Row
echo     return conn
echo.
echo @app.route^('/'^^)
echo def dashboard^(^):
echo     return '''
echo     ^<!DOCTYPE html^>
echo     ^<html^>
echo     ^<head^>
echo         ^<title^>AI Content Factory^</title^>
echo         ^<style^>
echo             body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
echo             .header { background: #2196F3; color: white; padding: 20px; border-radius: 8px; text-align: center; }
echo             .dashboard { display: grid; grid-template-columns: repeat^(auto-fit, minmax^(300px, 1fr^^)^^); gap: 20px; margin-top: 20px; }
echo             .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba^(0,0,0,0.1^^); }
echo             .status { padding: 10px; background: #4CAF50; color: white; border-radius: 4px; text-align: center; }
echo             button { background: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
echo             button:hover { background: #1976D2; }
echo         ^</style^>
echo     ^</head^>
echo     ^<body^>
echo         ^<div class="header"^>
echo             ^<h1^>🚀 AI Content Factory System^</h1^>
echo             ^<p^>Content Creation & Automation Platform^</p^>
echo         ^</div^>
echo         
echo         ^<div class="status"^>
echo             ✅ System Status: Online ^(SQLite Database^^)
echo         ^</div^>
echo         
echo         ^<div class="dashboard"^>
echo             ^<div class="card"^>
echo                 ^<h3^>📊 Trend Monitor^</h3^>
echo                 ^<p^>เก็บข้อมูล trends จากแหล่งต่างๆ^</p^>
echo                 ^<button onclick="collectTrends^(^^)"^>Collect Trends^</button^>
echo                 ^<div id="trends-result"^>^</div^>
echo             ^</div^>
echo             
echo             ^<div class="card"^>
echo                 ^<h3^>🎯 Content Opportunities^</h3^>
echo                 ^<p^>วิเคราะห์และสร้างโอกาสเนื้อหา^</p^>
echo                 ^<button onclick="generateOpportunities^(^^)"^>Generate Ideas^</button^>
echo                 ^<div id="opportunities-result"^>^</div^>
echo             ^</div^>
echo             
echo             ^<div class="card"^>
echo                 ^<h3^>🎬 Content Generator^</h3^>
echo                 ^<p^>สร้างเนื้อหาด้วย AI^</p^>
echo                 ^<button onclick="generateContent^(^^)"^>Create Content^</button^>
echo                 ^<div id="content-result"^>^</div^>
echo             ^</div^>
echo             
echo             ^<div class="card"^>
echo                 ^<h3^>📈 Analytics^</h3^>
echo                 ^<p^>สถิติและผลลัพธ์^</p^>
echo                 ^<button onclick="showAnalytics^(^^)"^>View Stats^</button^>
echo                 ^<div id="analytics-result"^>^</div^>
echo             ^</div^>
echo         ^</div^>
echo         
echo         ^<script^>
echo             function collectTrends^(^) {
echo                 document.getElementById^('trends-result'^^).innerHTML = '⏳ กำลังเก็บข้อมูล trends...';
echo                 fetch^('/api/collect-trends', {method: 'POST'}^^)
echo                     .then^(response =^> response.json^(^^)^^)
echo                     .then^(data =^> {
echo                         document.getElementById^('trends-result'^^).innerHTML = 
echo                             '✅ เก็บข้อมูลแล้ว: ' + data.count + ' trends';
echo                     }^^);
echo             }
echo             
echo             function generateOpportunities^(^) {
echo                 document.getElementById^('opportunities-result'^^).innerHTML = '⏳ กำลังวิเคราะห์...';
echo                 fetch^('/api/generate-opportunities', {method: 'POST'}^^)
echo                     .then^(response =^> response.json^(^^)^^)
echo                     .then^(data =^> {
echo                         document.getElementById^('opportunities-result'^^).innerHTML = 
echo                             '✅ สร้างแล้ว: ' + data.count + ' opportunities';
echo                     }^^);
echo             }
echo             
echo             function generateContent^(^) {
echo                 document.getElementById^('content-result'^^).innerHTML = '⏳ กำลังสร้างเนื้อหา...';
echo                 // Placeholder function
echo                 setTimeout^(^(^) =^> {
echo                     document.getElementById^('content-result'^^).innerHTML = 
echo                         '✅ พร้อมใช้งาน ^(Coming Soon^^)';
echo                 }, 2000^^);
echo             }
echo             
echo             function showAnalytics^(^) {
echo                 document.getElementById^('analytics-result'^^).innerHTML = '📊 Analytics Dashboard ^(Coming Soon^^)';
echo             }
echo         ^</script^>
echo     ^</body^>
echo     ^</html^>
echo     '''
echo.
echo @app.route^('/api/collect-trends', methods=['POST']^^)
echo def collect_trends^(^):
echo     # Simulate collecting trends
echo     sample_trends = [
echo         {'topic': 'AI Content Creation', 'popularity': 85, 'growth': 12},
echo         {'topic': 'Short Form Videos', 'popularity': 92, 'growth': 18},
echo         {'topic': 'Tech Reviews 2025', 'popularity': 78, 'growth': 15}
echo     ]
echo     
echo     conn = get_db_connection^(^)
echo     for trend in sample_trends:
echo         conn.execute^('''
echo             INSERT OR REPLACE INTO trends 
echo             ^(id, source, topic, popularity_score, growth_rate, collected_at^^)
echo             VALUES ^(?, ?, ?, ?, ?, ?^^)
echo         ''', ^(
echo             f"trend_{trend['topic'].replace^(' ', '_'^^).lower^(^^)}",
echo             'demo',
echo             trend['topic'],
echo             trend['popularity'],
echo             trend['growth'],
echo             datetime.now^(^)
echo         ^^)^^)
echo     conn.commit^(^)
echo     conn.close^(^)
echo     
echo     return jsonify^({'status': 'success', 'count': len^(sample_trends^^)}^^)
echo.
echo @app.route^('/api/generate-opportunities', methods=['POST']^^)
echo def generate_opportunities^(^):
echo     # Generate sample opportunities
echo     conn = get_db_connection^(^)
echo     trends = conn.execute^('SELECT * FROM trends ORDER BY collected_at DESC LIMIT 3'^^).fetchall^(^)
echo     
echo     opportunities = []
echo     for trend in trends:
echo         conn.execute^('''
echo             INSERT OR REPLACE INTO content_opportunities
echo             ^(id, trend_id, suggested_angle, estimated_views, competition_level, 
echo              production_cost, estimated_roi, priority_score, status, created_at^^)
echo             VALUES ^(?, ?, ?, ?, ?, ?, ?, ?, ?, ?^^)
echo         ''', ^(
echo             f"opp_{trend['id']}_1",
echo             trend['id'],
echo             f"How to use {trend['topic']} in 2025",
echo             5000,
echo             'medium',
echo             15.0,
echo             3.2,
echo             8.5,
echo             'pending',
echo             datetime.now^(^)
echo         ^^)^^)
echo         opportunities.append^(1^^)
echo     
echo     conn.commit^(^)
echo     conn.close^(^)
echo     
echo     return jsonify^({'status': 'success', 'count': len^(opportunities^^)}^^)
echo.
echo if __name__ == '__main__':
echo     app.run^(
echo         host=os.getenv^('FLASK_HOST', '127.0.0.1'^^),
echo         port=int^(os.getenv^('FLASK_PORT', 5000^^)^^),
echo         debug=True
echo     ^^)
) > simple_app.py

echo ✅ สร้างไฟล์ simple_app.py แล้ว

echo.
echo 🎉 Setup เสร็จสิ้น!
echo =================
echo.
echo เพื่อเริ่มใช้งาน:
echo 1. python simple_app.py
echo 2. เปิดเบราว์เซอร์ไปที่: http://localhost:5000
echo.
echo ไฟล์ที่สร้าง:
echo ✅ content_factory.db ^(SQLite Database^^)
echo ✅ .env ^(Environment Variables^^)
echo ✅ simple_app.py ^(Web Application^^)
echo ✅ requirements.txt ^(Dependencies^^)
echo.
echo กด Enter เพื่อเริ่ม Web App...
pause

echo เริ่ม Web Application...
python simple_app.py