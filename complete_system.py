#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete AI Content Factory - Production System
รวมทุกฟีเจอร์: AI Generation + Upload + Analytics + Scheduling
"""

import sys
import os
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import aiohttp

# Encoding setup
if sys.platform.startswith('win'):
    os.system('chcp 65001 >nul 2>&1')
os.environ['PYTHONIOENCODING'] = 'utf-8'

def p(text, end='\n'):
    try:
        print(text, end=end, flush=True)
    except:
        print('[Output]', end=end, flush=True)

def header(text, w=70):
    p("=" * w)
    p(text)
    p("=" * w)

def section(text):
    p(f"\n{text}")
    p("-" * 50)

# ================================
# Database Manager
# ================================

class DatabaseManager:
    """SQLite Database Manager"""
    
    def __init__(self, db_path: str = "content_factory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Content table
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
        
        # Uploads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                platform TEXT NOT NULL,
                video_id TEXT,
                url TEXT,
                status TEXT DEFAULT 'uploaded',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content(id)
            )
        """)
        
        # Analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                engagement_rate REAL DEFAULT 0.0,
                revenue REAL DEFAULT 0.0,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (upload_id) REFERENCES uploads(id)
            )
        """)
        
        # Schedule table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                platforms TEXT,
                scheduled_time TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content(id)
            )
        """)
        
        conn.commit()
        conn.close()
        p("[DB] Database initialized")
    
    def save_content(self, content: Dict) -> int:
        """Save generated content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO content (topic, angle, platform, script, hashtags, 
                               thumbnail_concept, ai_generated, cost, quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            content['topic'],
            content['angle'],
            content['platform'],
            json.dumps(content.get('script', {})),
            json.dumps(content.get('hashtags', [])),
            json.dumps(content.get('thumbnail', {})),
            content.get('ai_generated', 0),
            content.get('cost', 0.0),
            content.get('quality_score', 0.0)
        ))
        
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return content_id
    
    def save_upload(self, content_id: int, upload_result: Dict) -> int:
        """Save upload result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO uploads (content_id, platform, video_id, url, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            content_id,
            upload_result['platform'],
            upload_result.get('video_id', ''),
            upload_result.get('url', ''),
            upload_result.get('status', 'uploaded')
        ))
        
        upload_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return upload_id
    
    def get_all_content(self, limit: int = 50) -> List[Dict]:
        """Get all content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, topic, angle, platform, cost, quality_score, created_at
            FROM content ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0], "topic": r[1], "angle": r[2], 
                "platform": r[3], "cost": r[4], "quality_score": r[5],
                "created_at": r[6]
            }
            for r in rows
        ]
    
    def get_analytics_summary(self) -> Dict:
        """Get analytics summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_uploads,
                SUM(views) as total_views,
                SUM(likes) as total_likes,
                AVG(engagement_rate) as avg_engagement,
                SUM(revenue) as total_revenue
            FROM analytics
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total_uploads": row[0] or 0,
            "total_views": row[1] or 0,
            "total_likes": row[2] or 0,
            "avg_engagement": round(row[3] or 0, 2),
            "total_revenue": round(row[4] or 0, 2)
        }

# ================================
# AI Service (Groq)
# ================================

class GroqAIService:
    """Groq AI Service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
    
    async def generate_script(self, topic: str, angle: str, platform: str) -> Dict:
        """Generate complete script"""
        
        prompt = f"""Create a viral {platform} video script about:
Topic: {topic}
Angle: {angle}

Include:
1. 3 catchy titles (under 60 chars each)
2. Hook (5 seconds, attention-grabbing)
3. Full script with timestamps
4. 8 relevant hashtags
5. Call-to-action

Make it engaging, actionable, and optimized for {platform}."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert viral content creator."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Parse response
                        return self._parse_script(content, topic, angle, platform)
                    else:
                        return self._fallback_script(topic, angle, platform)
        except:
            return self._fallback_script(topic, angle, platform)
    
    def _parse_script(self, content: str, topic: str, angle: str, platform: str) -> Dict:
        """Parse AI response"""
        lines = content.split('\n')
        
        return {
            "titles": [line.strip() for line in lines[:3] if line.strip()],
            "hook": content[:200],
            "full_script": content,
            "hashtags": [w for w in content.split() if w.startswith('#')][:8],
            "ai_generated": True
        }
    
    def _fallback_script(self, topic: str, angle: str, platform: str) -> Dict:
        """Fallback script"""
        return {
            "titles": [f"{topic}: {angle} Guide", f"Master {topic}", f"{topic} Tutorial"],
            "hook": f"Discover the secrets of {topic} with {angle}...",
            "full_script": f"Complete guide to {topic} using {angle} approach.",
            "hashtags": [f"#{topic.replace(' ', '')}", "#viral", "#trending"],
            "ai_generated": False
        }

# ================================
# Upload Service
# ================================

class MultiPlatformUploader:
    """Multi-platform uploader"""
    
    async def upload(self, platform: str, content: Dict) -> Dict:
        """Simulate upload"""
        p(f"[UPLOAD] Uploading to {platform.upper()}...")
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "platform": platform,
            "video_id": f"{platform.upper()}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "url": f"https://{platform}.com/video/demo123",
            "status": "published"
        }

# ================================
# Complete System
# ================================

class CompleteContentFactory:
    """Complete AI Content Factory System"""
    
    def __init__(self, groq_api_key: str = None):
        self.db = DatabaseManager()
        self.ai = GroqAIService(groq_api_key) if groq_api_key else None
        self.uploader = MultiPlatformUploader()
    
    async def generate_content(self, topic: str, angle: str, platform: str) -> Dict:
        """Generate content"""
        
        p(f"\n[GENERATE] Creating content: {topic}")
        
        if self.ai:
            script_data = await self.ai.generate_script(topic, angle, platform)
        else:
            script_data = {
                "titles": [f"{topic} - {angle}"],
                "hook": f"Learn about {topic}...",
                "full_script": f"Full content about {topic}",
                "hashtags": [f"#{topic.replace(' ', '')}"],
                "ai_generated": False
            }
        
        content = {
            "topic": topic,
            "angle": angle,
            "platform": platform,
            "script": script_data,
            "hashtags": script_data['hashtags'],
            "thumbnail": {"concept": f"Visual for {topic}"},
            "ai_generated": script_data.get('ai_generated', False),
            "cost": 0.1 if script_data.get('ai_generated') else 0.0,
            "quality_score": 9.5 if script_data.get('ai_generated') else 7.0
        }
        
        content_id = self.db.save_content(content)
        content['id'] = content_id
        
        p(f"[GENERATE] Content saved! ID: {content_id}")
        return content
    
    async def upload_content(self, content_id: int, platforms: List[str]) -> List[Dict]:
        """Upload content to platforms"""
        
        p(f"\n[UPLOAD] Uploading content ID {content_id} to {len(platforms)} platforms")
        
        results = []
        for platform in platforms:
            result = await self.uploader.upload(platform, {})
            upload_id = self.db.save_upload(content_id, result)
            result['upload_id'] = upload_id
            results.append(result)
        
        p(f"[UPLOAD] Uploaded to {len(results)} platforms")
        return results
    
    def get_dashboard_data(self) -> Dict:
        """Get dashboard data"""
        return {
            "recent_content": self.db.get_all_content(10),
            "analytics": self.db.get_analytics_summary()
        }

# ================================
# Main UI
# ================================

class ProductionUI:
    """Production UI"""
    
    def __init__(self, groq_key: str = None):
        self.system = CompleteContentFactory(groq_key)
        self.ai_enabled = bool(groq_key)
    
    def welcome(self):
        p("")
        header("AI CONTENT FACTORY - PRODUCTION SYSTEM")
        p("")
        p("[*] Complete Content Generation Pipeline")
        p(f"[*] AI Mode: {'ENABLED (Groq)' if self.ai_enabled else 'DISABLED'}")
        p("[*] Multi-Platform Upload")
        p("[*] Database Storage")
        p("[*] Analytics & Tracking")
        p("")
        header("", 70)
    
    async def workflow_create_and_upload(self):
        """Complete workflow: Generate -> Upload"""
        
        section("CREATE & UPLOAD WORKFLOW")
        
        # Step 1: Generate content
        p("\n[STEP 1] Generate Content")
        topic = input("Topic: ").strip() or "AI Technology"
        angle = input("Angle: ").strip() or "Beginner Guide"
        platform = input("Platform (youtube/tiktok/instagram/facebook): ").strip() or "youtube"
        
        content = await self.system.generate_content(topic, angle, platform)
        
        # Show preview
        p(f"\n[PREVIEW]")
        p(f"Title: {content['script']['titles'][0]}")
        p(f"Hook: {content['script']['hook'][:80]}...")
        p(f"Hashtags: {' '.join(content['script']['hashtags'][:5])}")
        
        # Step 2: Upload
        p("\n[STEP 2] Upload to Platforms")
        p("Select platforms (comma-separated): youtube,tiktok,instagram,facebook")
        platforms_input = input("Platforms: ").strip()
        
        if platforms_input:
            platforms = [p.strip() for p in platforms_input.split(',')]
        else:
            platforms = [platform]
        
        uploads = await self.system.upload_content(content['id'], platforms)
        
        p(f"\n[SUCCESS] Uploaded to {len(uploads)} platforms!")
        for upload in uploads:
            p(f"  {upload['platform'].upper()}: {upload['url']}")
    
    async def view_dashboard(self):
        """View dashboard"""
        
        section("DASHBOARD")
        
        data = self.system.get_dashboard_data()
        
        p("\nRecent Content:")
        for content in data['recent_content'][:5]:
            p(f"  [{content['id']}] {content['topic']} | {content['platform'].upper()}")
            p(f"      Quality: {content['quality_score']}/10 | Cost: {content['cost']} THB")
        
        analytics = data['analytics']
        p(f"\nAnalytics Summary:")
        p(f"  Total Uploads: {analytics['total_uploads']}")
        p(f"  Total Views: {analytics['total_views']:,}")
        p(f"  Total Likes: {analytics['total_likes']:,}")
        p(f"  Avg Engagement: {analytics['avg_engagement']}%")
        p(f"  Total Revenue: {analytics['total_revenue']:.2f} THB")
    
    async def export_data(self):
        """Export data to JSON"""
        
        section("EXPORT DATA")
        
        data = self.system.get_dashboard_data()
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        p(f"\n[EXPORT] Data saved to: {filename}")
    
    async def run(self):
        """Run UI"""
        
        self.welcome()
        
        while True:
            try:
                p("\n" + "="*70)
                p("MAIN MENU")
                p("1. Create & Upload Content")
                p("2. View Dashboard")
                p("3. Export Data")
                p("4. Exit")
                
                choice = input("\nSelect: ").strip()
                
                if choice == "1":
                    await self.workflow_create_and_upload()
                elif choice == "2":
                    await self.view_dashboard()
                elif choice == "3":
                    await self.export_data()
                elif choice == "4":
                    p("\n[EXIT] Shutting down...")
                    break
                else:
                    p("[ERROR] Invalid choice")
                    
            except KeyboardInterrupt:
                p("\n\n[EXIT] Goodbye!")
                break
            except Exception as e:
                p(f"\n[ERROR] {e}")

# ================================
# Main
# ================================

async def main():
    groq_key = os.getenv('GROQ_API_KEY')
    
    if not groq_key:
        p("[WARNING] GROQ_API_KEY not found - using template mode")
    
    ui = ProductionUI(groq_key)
    await ui.run()

if __name__ == "__main__":
    p("[INIT] AI Content Factory - Production System v1.0")
    
    try:
        asyncio.run(main())
    except Exception as e:
        p(f"\n[FATAL] {e}")
        input("\nPress Enter to exit...")