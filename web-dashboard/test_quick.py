#!/usr/bin/env python3
"""
Quick Test Script for AI Content Factory
ทดสอบระบบแบบง่ายๆ ที่ใช้ได้ทันที
"""

import requests
import json
import time
import os

def test_system():
    """ทดสอบระบบแบบครบครัน"""
    
    print("🧪 AI Content Factory - Quick System Test")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Server Connection
    print("\n1. 🌐 Testing Server Connection...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running!")
        else:
            print(f"   ❌ Server error: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server!")
        print("   💡 Make sure you run: python app.py")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Database
    print("\n2. 🗄️ Testing Database...")
    if os.path.exists("content_factory.db"):
        print("   ✅ Database file exists!")
    else:
        print("   ❌ Database file not found!")
    
    # Test 3: Dashboard API
    print("\n3. 📊 Testing Dashboard API...")
    try:
        response = requests.get(f"{base_url}/api/dashboard-stats")
        data = response.json()
        stats = data.get('today_stats', {})
        print(f"   ✅ Dashboard API working!")
        print(f"   📈 Trends: {stats.get('trends_collected', 0)}")
        print(f"   💡 Opportunities: {stats.get('opportunities_generated', 0)}")
        print(f"   🎬 Content: {stats.get('content_created', 0)}")
    except Exception as e:
        print(f"   ❌ Dashboard API error: {e}")
    
    # Test 4: Collect Trends
    print("\n4. 📈 Testing Trend Collection...")
    try:
        response = requests.post(f"{base_url}/api/collect-trends")
        data = response.json()
        if data.get('success'):
            trends_count = len(data.get('trends', []))
            print(f"   ✅ Collected {trends_count} trends!")
        else:
            print("   ❌ Failed to collect trends!")
    except Exception as e:
        print(f"   ❌ Trend collection error: {e}")
    
    # Test 5: Check Trends
    print("\n5. 🔍 Testing Trends API...")
    try:
        response = requests.get(f"{base_url}/api/trends")
        data = response.json()
        trends = data.get('trends', [])
        print(f"   ✅ Found {len(trends)} trends in database!")
        
        if trends:
            trend = trends[0]
            print(f"   📝 Sample: {trend.get('topic', 'Unknown')}")
            
            # Test 6: Analyze Trend
            print(f"\n6. 🧠 Testing Trend Analysis...")
            try:
                trend_id = trend['id']
                response = requests.post(f"{base_url}/api/analyze-trend/{trend_id}")
                data = response.json()
                if data.get('success'):
                    opportunities = data.get('opportunities', [])
                    print(f"   ✅ Generated {len(opportunities)} opportunities!")
                else:
                    print("   ❌ Failed to analyze trend!")
            except Exception as e:
                print(f"   ❌ Trend analysis error: {e}")
        else:
            print("   ⚠️ No trends to analyze!")
            
    except Exception as e:
        print(f"   ❌ Trends API error: {e}")
    
    # Test 7: Check Opportunities
    print("\n7. 💡 Testing Opportunities API...")
    try:
        response = requests.get(f"{base_url}/api/opportunities")
        data = response.json()
        opportunities = data.get('opportunities', [])
        print(f"   ✅ Found {len(opportunities)} opportunities!")
        
        if opportunities:
            opp = opportunities[0]
            print(f"   💭 Sample: {opp.get('suggested_angle', 'Unknown')[:50]}...")
            
            # Test 8: Select Opportunity
            print(f"\n8. ⭐ Testing Opportunity Selection...")
            try:
                opp_id = opp['id']
                response = requests.post(f"{base_url}/api/opportunity/{opp_id}/select")
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ Selected opportunity successfully!")
                else:
                    print("   ❌ Failed to select opportunity!")
            except Exception as e:
                print(f"   ❌ Opportunity selection error: {e}")
        else:
            print("   ⚠️ No opportunities to select!")
            
    except Exception as e:
        print(f"   ❌ Opportunities API error: {e}")
    
    # Test 9: Check Content Items
    print("\n9. 🎬 Testing Content Items API...")
    try:
        response = requests.get(f"{base_url}/api/content-items")
        data = response.json()
        content_items = data.get('content_items', [])
        print(f"   ✅ Found {len(content_items)} content items!")
    except Exception as e:
        print(f"   ❌ Content items API error: {e}")
    
    # Test 10: UI Pages
    print("\n10. 🎨 Testing UI Pages...")
    pages = [
        ("/", "Dashboard"),
        ("/trends", "Trends"),
        ("/opportunities", "Opportunities")
    ]
    
    for url, name in pages:
        try:
            response = requests.get(f"{base_url}{url}")
            if response.status_code == 200 and "<html" in response.text:
                print(f"   ✅ {name} page working!")
            else:
                print(f"   ❌ {name} page error!")
        except Exception as e:
            print(f"   ❌ {name} page error: {e}")
    
    # Final Dashboard Check
    print("\n🔄 Final Dashboard Check...")
    try:
        response = requests.get(f"{base_url}/api/dashboard-stats")
        data = response.json()
        stats = data.get('today_stats', {})
        print(f"   📊 Final Stats:")
        print(f"      Trends: {stats.get('trends_collected', 0)}")
        print(f"      Opportunities: {stats.get('opportunities_generated', 0)}")
        print(f"      Content: {stats.get('content_created', 0)}")
    except Exception as e:
        print(f"   ❌ Final check error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test Complete!")
    print("💡 Open http://localhost:5000 in your browser")
    print("=" * 50)

if __name__ == "__main__":
    test_system()