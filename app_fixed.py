#!/usr/bin/env python3
"""
AI Content Factory - Main Application (Fixed Import Paths)
เครื่องมือสร้างเนื้อหาอัตโนมัติด้วย AI
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory and subdirectories to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('./trend-monitor')
sys.path.append('./content-engine')
sys.path.append('./platform-manager')

class AIContentFactory:
    def __init__(self):
        self.db = None
        self.setup_database()
        
    def setup_database(self):
        """ตั้งค่า database"""
        try:
            from database.models_simple import Database
            self.db = Database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            sys.exit(1)
    
    def collect_trends(self):
        """เก็บรวบรวม trends จากแหล่งต่างๆ"""
        print("\n🔍 Starting trend collection...")
        
        try:
            # Import แบบ direct path
            from trend_collector import TrendCollectorManager
            
            collector = TrendCollectorManager(self.db)
            trends = collector.collect_all_trends()
            
            if trends:
                print(f"✅ Successfully collected {len(trends)} trends")
                return True
            else:
                print("⚠️ No trends collected")
                return False
                
        except Exception as e:
            print(f"❌ Trend collection failed: {e}")
            return False
    
    def analyze_trends(self):
        """วิเคราะห์ trends และสร้าง content opportunities"""
        print("\n🤖 Starting trend analysis...")
        
        try:
            # Import แบบ direct path
            from ai_trend_analyzer import OpportunityGenerator
            
            generator = OpportunityGenerator(self.db)
            opportunities_count = generator.generate_content_opportunities(min_score=5.0)
            
            if opportunities_count > 0:
                print(f"✅ Created {opportunities_count} content opportunities")
                return True
            else:
                print("⚠️ No opportunities created")
                return False
                
        except Exception as e:
            print(f"❌ Trend analysis failed: {e}")
            return False
    
    def show_dashboard(self):
        """แสดง dashboard ข้อมูลสรุป"""
        print("\n📊 AI Content Factory Dashboard")
        print("=" * 50)
        
        try:
            # แสดง trends
            from database.models_simple import TrendModel, ContentOpportunityModel
            
            trend_model = TrendModel(self.db)
            opportunity_model = ContentOpportunityModel(self.db)
            
            # สถิติ trends
            trends = trend_model.get_all()
            youtube_trends = trend_model.get_by_source('youtube')
            google_trends = trend_model.get_by_source('google_trends')
            
            print(f"📈 Total Trends: {len(trends)}")
            print(f"   YouTube: {len(youtube_trends)}")
            print(f"   Google Trends: {len(google_trends)}")
            
            # สถิติ opportunities
            opportunities = opportunity_model.get_by_status('pending')
            
            print(f"\n💡 Content Opportunities: {len(opportunities)}")
            
            # แสดง top 5 opportunities
            if opportunities:
                print("\n🎯 Top Opportunities:")
                for i, opp in enumerate(opportunities[:5], 1):
                    print(f"   {i}. {opp['suggested_angle'][:60]}...")
                    print(f"      Score: {opp['priority_score']:.1f} | Views: {opp['estimated_views']:,} | Cost: ฿{opp['production_cost']}")
            
            # แสดง top trends
            if trends:
                print(f"\n🔥 Top Trends:")
                sorted_trends = sorted(trends, key=lambda x: x['popularity_score'], reverse=True)
                for i, trend in enumerate(sorted_trends[:5], 1):
                    print(f"   {i}. {trend['topic'][:50]}...")
                    print(f"      Score: {trend['popularity_score']:.1f} | Growth: {trend['growth_rate']}% | Source: {trend['source']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Dashboard error: {e}")
            return False
    
    def run_full_cycle(self):
        """รันกระบวนการทั้งหมด: collect → analyze → dashboard"""
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
        print("\n🎯 Next Steps:")
        print("- Review content opportunities above")
        print("- Select high-scoring opportunities to create content")
        print("- Add real AI API keys for better analysis")
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
    print("🚀 AI Content Factory")
    print("=" * 30)
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
        elif command == 'interactive':
            app.interactive_mode()
        else:
            print(f"❌ Unknown command: {command}")
            print("\nAvailable commands:")
            print("  python app.py collect     - Collect trends")
            print("  python app.py analyze     - Analyze trends")
            print("  python app.py dashboard   - Show dashboard")
            print("  python app.py full        - Run full cycle")
            print("  python app.py interactive - Interactive mode")
    else:
        # ถ้าไม่มี arguments ให้รัน interactive mode
        app.interactive_mode()

if __name__ == "__main__":
    main()