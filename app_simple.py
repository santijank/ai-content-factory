#!/usr/bin/env python3
"""
AI Content Factory - Simple Working Version
ระบบสร้างเนื้อหาอัตโนมัติด้วย AI - เวอร์ชันง่ายที่ทำงานได้แน่นอน
"""

import os
import sys
import time
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add path for database import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SimpleTrendCollector:
    """Trend Collector แบบง่าย - ใช้ mock data"""
    
    def collect_youtube_trends(self):
        """เก็บ YouTube trends (mock data)"""
        return [
            {
                'source': 'youtube',
                'topic': 'AI Content Creation Tutorial 2024',
                'popularity_score': 95.5,
                'growth_rate': 25.3,
                'category': 'Technology',
                'keywords': ['AI', 'content creation', 'automation', 'tutorial', '2024'],
                'raw_data': {
                    'views': 150000,
                    'likes': 12000,
                    'comments': 850,
                    'channel': 'Tech Tutorials TH'
                }
            },
            {
                'source': 'youtube',
                'topic': 'ChatGPT for Business Automation',
                'popularity_score': 87.2,
                'growth_rate': 18.7,
                'category': 'Business',
                'keywords': ['ChatGPT', 'business', 'productivity', 'AI tools', 'automation'],
                'raw_data': {
                    'views': 89000,
                    'likes': 7500,
                    'comments': 420,
                    'channel': 'Business AI'
                }
            },
            {
                'source': 'youtube',
                'topic': 'Python Automation Scripts for Beginners',
                'popularity_score': 82.1,
                'growth_rate': 15.2,
                'category': 'Programming',
                'keywords': ['Python', 'automation', 'scripting', 'programming', 'beginners'],
                'raw_data': {
                    'views': 67000,
                    'likes': 5200,
                    'comments': 310,
                    'channel': 'Code Masters'
                }
            }
        ]
    
    def collect_google_trends(self):
        """เก็บ Google Trends (mock data)"""
        return [
            {
                'source': 'google_trends',
                'topic': 'AI Image Generator Tools',
                'popularity_score': 92.3,
                'growth_rate': 35.8,
                'category': 'Technology',
                'keywords': ['AI', 'image generator', 'art', 'creative', 'tools'],
                'raw_data': {
                    'search_volume': 'High',
                    'related_queries': ['midjourney', 'dall-e', 'stable diffusion']
                }
            },
            {
                'source': 'google_trends',
                'topic': 'Remote Work Productivity Tools',
                'popularity_score': 78.9,
                'growth_rate': 12.4,
                'category': 'Business',
                'keywords': ['remote work', 'productivity', 'tools', 'collaboration', 'wfh'],
                'raw_data': {
                    'search_volume': 'Medium',
                    'related_queries': ['zoom', 'slack', 'notion', 'teams']
                }
            }
        ]

class SimpleAIAnalyzer:
    """AI Analyzer แบบง่าย - ใช้ logic พื้นฐาน"""
    
    def analyze_trend(self, trend):
        """วิเคราะห์ trend แต่ละตัว"""
        
        # คำนวณ scores
        viral_potential = self.calculate_viral_potential(trend)
        content_saturation = self.calculate_content_saturation(trend)
        audience_interest = trend['popularity_score'] / 10
        monetization_opportunity = self.calculate_monetization_opportunity(trend)
        
        overall_score = (viral_potential + audience_interest + monetization_opportunity - content_saturation) / 3
        
        # สร้าง content angles
        content_angles = self.generate_content_angles(trend)
        
        return {
            'trend_id': str(uuid.uuid4()),
            'trend_topic': trend['topic'],
            'scores': {
                'viral_potential': viral_potential,
                'content_saturation': content_saturation,
                'audience_interest': audience_interest,
                'monetization_opportunity': monetization_opportunity,
                'overall_score': max(overall_score, 0)
            },
            'content_angles': content_angles,
            'estimated_views': int(trend['popularity_score'] * 1000),
            'competition_level': 'high' if trend['popularity_score'] > 80 else 'medium' if trend['popularity_score'] > 60 else 'low',
            'production_cost': self.estimate_cost(trend),
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def calculate_viral_potential(self, trend):
        """คำนวณศักยภาพการแพร่กระจาย"""
        score = 5
        
        if trend['popularity_score'] > 80:
            score += 2
        elif trend['popularity_score'] > 60:
            score += 1
        
        if trend['growth_rate'] > 20:
            score += 2
        elif trend['growth_rate'] > 10:
            score += 1
        
        viral_keywords = ['ai', 'tutorial', 'hack', 'secret', 'amazing', 'new', '2024']
        keyword_matches = sum(1 for kw in trend.get('keywords', []) 
                             if any(viral in kw.lower() for viral in viral_keywords))
        score += min(keyword_matches, 2)
        
        return min(score, 10)
    
    def calculate_content_saturation(self, trend):
        """คำนวณระดับการอิ่มตัวของเนื้อหา"""
        base_saturation = 5
        
        popular_topics = ['tutorial', 'review', 'unboxing', 'comparison']
        if any(topic in trend['topic'].lower() for topic in popular_topics):
            base_saturation += 1
        
        if trend['source'] == 'youtube':
            base_saturation += 1
        
        return min(base_saturation, 10)
    
    def calculate_monetization_opportunity(self, trend):
        """คำนวณโอกาสในการสร้างรายได้"""
        score = 5
        
        profitable_categories = ['technology', 'business', 'education', 'finance']
        if trend.get('category', '').lower() in profitable_categories:
            score += 2
        
        commercial_keywords = ['tools', 'business', 'automation', 'productivity']
        keyword_matches = sum(1 for kw in trend.get('keywords', []) 
                             if any(commercial in kw.lower() for commercial in commercial_keywords))
        score += min(keyword_matches, 2)
        
        return min(score, 10)
    
    def generate_content_angles(self, trend):
        """สร้างมุมมองการสร้างเนื้อหา"""
        topic = trend['topic']
        
        angles = [
            f"สอนวิธีใช้ {topic} แบบง่ายๆ สำหรับมือใหม่",
            f"เปรียบเทียบ {topic} กับทางเลือกอื่นๆ ในตลาด",
            f"เคล็ดลับและเทคนิคขั้นสูงสำหรับ {topic}"
        ]
        
        return angles
    
    def estimate_cost(self, trend):
        """ประเมินต้นทุนการผลิต"""
        if 'tutorial' in trend['topic'].lower():
            return 200  # tutorial ต้องใช้เวลาทำมาก
        elif 'review' in trend['topic'].lower():
            return 100  # review ทำง่ายกว่า
        else:
            return 150  # ปกติ

class AIContentFactory:
    """Main Application Class"""
    
    def __init__(self):
        self.db = None
        self.trend_collector = SimpleTrendCollector()
        self.ai_analyzer = SimpleAIAnalyzer()
        self.setup_database()
        
        # เก็บข้อมูลใน memory
        self.trends = []
        self.opportunities = []
        
    def setup_database(self):
        """ตั้งค่า database"""
        try:
            from database.models_simple import Database
            self.db = Database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"⚠️ Database initialization issue: {e}")
            print("✅ Running in memory mode")
    
    def collect_trends(self):
        """เก็บรวบรวม trends จากแหล่งต่างๆ"""
        print("\n🔍 Starting trend collection...")
        
        try:
            # เก็บจาก YouTube
            youtube_trends = self.trend_collector.collect_youtube_trends()
            print(f"✅ Retrieved {len(youtube_trends)} YouTube trends")
            
            # เก็บจาก Google Trends
            google_trends = self.trend_collector.collect_google_trends()
            print(f"✅ Retrieved {len(google_trends)} Google trends")
            
            # รวม trends
            all_trends = youtube_trends + google_trends
            self.trends.extend(all_trends)
            
            # บันทึกลง database ถ้าทำได้
            if self.db:
                self.save_trends_to_database(all_trends)
            
            print(f"✅ Successfully collected {len(all_trends)} total trends")
            return True
            
        except Exception as e:
            print(f"❌ Trend collection failed: {e}")
            return False
    
    def save_trends_to_database(self, trends):
        """บันทึก trends ลง database"""
        try:
            from database.models_simple import TrendModel
            trend_model = TrendModel(self.db)
            
            saved_count = 0
            for trend in trends:
                trend_id = trend_model.create(
                    source=trend['source'],
                    topic=trend['topic'],
                    keywords=trend['keywords'],
                    popularity_score=trend['popularity_score'],
                    growth_rate=trend['growth_rate'],
                    category=trend['category'],
                    raw_data=trend['raw_data']
                )
                
                if trend_id:
                    saved_count += 1
            
            print(f"✅ Saved {saved_count} trends to database")
            
        except Exception as e:
            print(f"⚠️ Database save issue: {e}")
    
    def analyze_trends(self):
        """วิเคราะห์ trends และสร้าง content opportunities"""
        print("\n🤖 Starting trend analysis...")
        
        if not self.trends:
            print("⚠️ No trends to analyze. Please collect trends first.")
            return False
        
        try:
            opportunities_created = 0
            
            for trend in self.trends:
                # วิเคราะห์ trend
                analysis = self.ai_analyzer.analyze_trend(trend)
                
                # สร้าง opportunities หากคะแนนดี
                if analysis['scores']['overall_score'] >= 5.0:
                    for angle in analysis['content_angles']:
                        opportunity = {
                            'id': str(uuid.uuid4()),
                            'trend_id': analysis['trend_id'],
                            'trend_topic': trend['topic'],
                            'suggested_angle': angle,
                            'estimated_views': analysis['estimated_views'],
                            'competition_level': analysis['competition_level'],
                            'priority_score': analysis['scores']['overall_score'],
                            'production_cost': analysis['production_cost'],
                            'estimated_roi': max((analysis['estimated_views'] * 0.001 - analysis['production_cost']) / analysis['production_cost'], 0),
                            'status': 'pending',
                            'created_at': datetime.utcnow().isoformat()
                        }
                        
                        self.opportunities.append(opportunity)
                        opportunities_created += 1
                
                print(f"✅ Analyzed: {trend['topic'][:50]}... (Score: {analysis['scores']['overall_score']:.1f})")
            
            print(f"✅ Created {opportunities_created} content opportunities")
            return opportunities_created > 0
            
        except Exception as e:
            print(f"❌ Trend analysis failed: {e}")
            return False
    
    def show_dashboard(self):
        """แสดง dashboard ข้อมูลสรุป"""
        print("\n📊 AI Content Factory Dashboard")
        print("=" * 50)
        
        # สถิติ trends
        youtube_trends = [t for t in self.trends if t['source'] == 'youtube']
        google_trends = [t for t in self.trends if t['source'] == 'google_trends']
        
        print(f"📈 Total Trends: {len(self.trends)}")
        print(f"   YouTube: {len(youtube_trends)}")
        print(f"   Google Trends: {len(google_trends)}")
        
        # สถิติ opportunities
        pending_opportunities = [o for o in self.opportunities if o['status'] == 'pending']
        
        print(f"\n💡 Content Opportunities: {len(pending_opportunities)}")
        
        # แสดง top 5 opportunities
        if pending_opportunities:
            print("\n🎯 Top Opportunities:")
            sorted_opportunities = sorted(pending_opportunities, key=lambda x: x['priority_score'], reverse=True)
            
            for i, opp in enumerate(sorted_opportunities[:5], 1):
                print(f"   {i}. {opp['suggested_angle'][:60]}...")
                print(f"      Score: {opp['priority_score']:.1f} | Views: {opp['estimated_views']:,} | Cost: ฿{opp['production_cost']}")
        
        # แสดง top trends
        if self.trends:
            print(f"\n🔥 Top Trends:")
            sorted_trends = sorted(self.trends, key=lambda x: x['popularity_score'], reverse=True)
            
            for i, trend in enumerate(sorted_trends[:5], 1):
                print(f"   {i}. {trend['topic'][:50]}...")
                print(f"      Score: {trend['popularity_score']:.1f} | Growth: {trend['growth_rate']}% | Source: {trend['source']}")
        
        return True
    
    def run_full_cycle(self):
        """รันกระบวนการทั้งหมด"""
        print("🚀 Starting AI Content Factory Full Cycle")
        print("=" * 50)
        
        start_time = time.time()
        
        # Step 1: Collect trends
        if not self.collect_trends():
            print("❌ Failed at trend collection step")
            return False
        
        # Step 2: Analyze trends
        if not self.analyze_trends():
            print("❌ Failed at trend analysis step")
            return False
        
        # Step 3: Show dashboard
        self.show_dashboard()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Full cycle completed in {duration:.2f} seconds")
        print(f"🎯 Ready to create content from {len([o for o in self.opportunities if o['priority_score'] > 6])} high-priority opportunities!")
        return True
    
    def interactive_mode(self):
        """โหมดการทำงานแบบ interactive"""
        print("\n🎮 AI Content Factory - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\nSelect an option:")
            print("1. Collect Trends")
            print("2. Analyze Trends")
            print("3. Show Dashboard")
            print("4. Run Full Cycle")
            print("5. Exit")
            
            try:
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == '1':
                    self.collect_trends()
                elif choice == '2':
                    self.analyze_trends()
                elif choice == '3':
                    self.show_dashboard()
                elif choice == '4':
                    self.run_full_cycle()
                elif choice == '5':
                    print("👋 Goodbye!")
                    print("Thanks for using AI Content Factory!")
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🚀 AI Content Factory - Simple Version")
    print("=" * 40)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # สร้าง application instance
    app = AIContentFactory()
    
    # ตรวจสอบ command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'collect':
            app.collect_trends()
        elif command == 'analyze':
            app.analyze_trends()
        elif command == 'dashboard':
            app.show_dashboard()
        elif command == 'full':
            app.run_full_cycle()
        else:
            print(f"❌ Unknown command: {command}")
            print("\nAvailable commands:")
            print("  python app_simple.py collect     - Collect trends")
            print("  python app_simple.py analyze     - Analyze trends")
            print("  python app_simple.py dashboard   - Show dashboard")
            print("  python app_simple.py full        - Run full cycle")
    else:
        # ถ้าไม่มี arguments ให้รัน interactive mode
        app.interactive_mode()

if __name__ == "__main__":
    main()