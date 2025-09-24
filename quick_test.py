#!/usr/bin/env python3
"""
AI Content Factory - Quick System Check
ทดสอบระบบแบบเร็วๆ
"""

import requests
import sqlite3
import os
import sys

def quick_check():
    """ทดสอบระบบแบบรวดเร็ว"""
    print("🔍 AI Content Factory - Quick System Check")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 7
    
    # 1. ตรวจสอบไฟล์ database
    if os.path.exists("content_factory.db"):
        print("✅ Database file exists")
        checks_passed += 1
    else:
        print("❌ Database file missing")
    
    # 2. ตรวจสอบ database schema
    try:
        conn = sqlite3.connect("content_factory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        if all(table in tables for table in ['trends', 'content_opportunities', 'content_items']):
            print("✅ Database schema valid")
            checks_passed += 1
        else:
            print("❌ Database schema incomplete")
        
        # ตรวจสอบข้อมูล
        cursor.execute("SELECT COUNT(*) FROM trends")
        trends_count = cursor.fetchone()[0]
        if trends_count > 0:
            print(f"✅ Sample data exists ({trends_count} trends)")
            checks_passed += 1
        else:
            print("❌ No sample data")
        
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # 3. ตรวจสอบ server
    try:
        response = requests.get("http://localhost:5000", timeout=3)
        if response.status_code == 200:
            print("✅ Server responding")
            checks_passed += 1
        else:
            print(f"❌ Server error (Status: {response.status_code})")
    except:
        print("❌ Server not reachable")
    
    # 4. ตรวจสอบ Analytics API
    try:
        response = requests.get("http://localhost:5000/api/analytics", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analytics API working (Trends: {data.get('trends_count', 0)})")
            checks_passed += 1
        else:
            print("❌ Analytics API failed")
    except:
        print("❌ Analytics API not accessible")
    
    # 5. ทดสอบ Collect Trends API
    try:
        response = requests.post("http://localhost:5000/api/collect-trends", timeout=5)
        if response.status_code == 200:
            print("✅ Collect Trends API working")
            checks_passed += 1
        else:
            print("❌ Collect Trends API failed")
    except:
        print("❌ Collect Trends API not accessible")
    
    # 6. ทดสอบ Generate Opportunities API
    try:
        response = requests.post("http://localhost:5000/api/generate-opportunities", timeout=5)
        if response.status_code == 200:
            print("✅ Generate Opportunities API working")
            checks_passed += 1
        else:
            print("❌ Generate Opportunities API failed")
    except:
        print("❌ Generate Opportunities API not accessible")
    
    # สรุปผล
    print("\n" + "=" * 50)
    print(f"📊 QUICK CHECK RESULT: {checks_passed}/{total_checks}")
    
    if checks_passed == total_checks:
        print("🎉 PERFECT! System is working 100%")
        print("✅ Ready for production use!")
    elif checks_passed >= total_checks * 0.8:
        print("😊 GOOD! System is mostly working")
        print("⚠️  Minor issues detected")
    elif checks_passed >= total_checks * 0.5:
        print("😐 OKAY! System has some issues")
        print("🔧 Needs attention")
    else:
        print("😞 POOR! System has major issues")
        print("🚨 Requires immediate fixes")
    
    print(f"\n💡 Success Rate: {(checks_passed/total_checks)*100:.1f}%")
    
    if checks_passed < total_checks:
        print("\n🔧 Troubleshooting Tips:")
        print("1. Make sure server is running: python simple_app.py")
        print("2. Check database exists: python create_database.py")
        print("3. Install dependencies: pip install -r requirements.txt")
    
    return checks_passed == total_checks

if __name__ == "__main__":
    success = quick_check()
    sys.exit(0 if success else 1)