#!/usr/bin/env python3
"""
Fast Performance Test - ทดสอบ Response Time อย่างแม่นยำ
"""

import requests
import time
import statistics

def test_single_endpoint_speed(url, iterations=10):
    """ทดสอบความเร็วของ endpoint เดียว"""
    print(f"🔄 Testing {url}...")
    
    response_times = []
    
    # Warm up request (ไม่นับเวลา)
    try:
        requests.get(url, timeout=5)
    except:
        pass
    
    # ทดสอบจริง
    for i in range(iterations):
        start_time = time.time()
        try:
            response = requests.get(url, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000  # ms
                response_times.append(response_time)
                print(f"  Request {i+1}: {response_time:.2f}ms")
            else:
                print(f"  Request {i+1}: ERROR ({response.status_code})")
                
        except Exception as e:
            print(f"  Request {i+1}: FAILED ({e})")
    
    if response_times:
        avg = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"📊 Results for {url}:")
        print(f"  Average: {avg:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  Median: {statistics.median(response_times):.2f}ms")
        
        if avg < 100:
            print("  ⚡ EXCELLENT (< 100ms)")
        elif avg < 500:
            print("  ✅ GOOD (< 500ms)")
        elif avg < 1000:
            print("  ⚠️ OK (< 1000ms)")
        else:
            print("  ❌ SLOW (> 1000ms)")
        
        return avg
    else:
        print("  ❌ All requests failed")
        return None

def test_analytics_api_directly():
    """ทดสอบ Analytics API โดยตรง"""
    print("\n🎯 Direct Analytics API Test")
    print("=" * 40)
    
    url = "http://localhost:5000/api/analytics"
    
    # Single fast test
    start_time = time.time()
    try:
        response = requests.get(url, timeout=5)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"⚡ Direct test: {response_time:.2f}ms")
            print(f"📊 Data: Trends={data.get('trends_count')}, Opportunities={data.get('opportunities_count')}")
            
            if response_time < 500:
                print("✅ API is actually FAST!")
                print("🔍 The slow test might be due to test setup overhead")
            else:
                print("❌ API is genuinely slow")
                
        else:
            print(f"❌ API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

def test_database_directly():
    """ทดสอบ Database โดยตรง"""
    print("\n🗄️ Direct Database Test")
    print("=" * 40)
    
    try:
        import sqlite3
        
        # Test database speed
        start_time = time.time()
        
        conn = sqlite3.connect('content_factory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM trends")
        trends_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM content_opportunities")
        opportunities_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(estimated_roi) FROM content_opportunities")
        avg_roi = cursor.fetchone()[0]
        
        conn.close()
        
        end_time = time.time()
        db_time = (end_time - start_time) * 1000
        
        print(f"⚡ Database query time: {db_time:.2f}ms")
        print(f"📊 Results: {trends_count} trends, {opportunities_count} opportunities, ROI={avg_roi:.2f}")
        
        if db_time < 50:
            print("✅ Database is FAST!")
        elif db_time < 200:
            print("⚠️ Database is OK")
        else:
            print("❌ Database is SLOW")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

def diagnose_slow_response():
    """วินิจฉัยสาเหตุของ Response Time ช้า"""
    print("\n🔍 Diagnosing Slow Response")
    print("=" * 40)
    
    # Test 1: Check if server is responding quickly
    print("1. Testing server response...")
    try:
        start_time = time.time()
        response = requests.get("http://localhost:5000", timeout=3)
        response_time = (time.time() - start_time) * 1000
        print(f"   Homepage: {response_time:.2f}ms")
    except Exception as e:
        print(f"   Homepage: FAILED ({e})")
    
    # Test 2: Test simple endpoint
    print("\n2. Testing simple endpoint...")
    try:
        start_time = time.time()
        response = requests.get("http://localhost:5000/api/analytics", timeout=3)
        response_time = (time.time() - start_time) * 1000
        print(f"   Analytics: {response_time:.2f}ms")
        
        if response.status_code == 200:
            print(f"   ✅ Success: {len(response.content)} bytes")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"   Analytics: FAILED ({e})")
    
    # Test 3: Check system resources
    print("\n3. System resource check...")
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        print(f"   CPU: {cpu_percent}%")
        print(f"   Memory: {memory.percent}% used")
        
        if cpu_percent > 80:
            print("   ⚠️ High CPU usage detected")
        if memory.percent > 80:
            print("   ⚠️ High memory usage detected")
            
    except ImportError:
        print("   ⏭️ psutil not installed, skipping...")
    except Exception as e:
        print(f"   ❌ Resource check failed: {e}")

def main():
    """รันการทดสอบประสิทธิภาพแบบเร็ว"""
    print("⚡ Fast Performance Test")
    print("=" * 50)
    
    # ตรวจสอบการเชื่อมต่อพื้นฐาน
    try:
        response = requests.get("http://localhost:5000", timeout=2)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            return
    except:
        print("❌ Cannot connect to server")
        return
    
    print("✅ Server is online")
    
    # ทดสอบ API endpoints
    endpoints = [
        "http://localhost:5000/api/analytics",
        "http://localhost:5000/api/trends", 
        "http://localhost:5000/api/opportunities"
    ]
    
    avg_times = []
    
    for endpoint in endpoints:
        avg_time = test_single_endpoint_speed(endpoint, iterations=5)
        if avg_time:
            avg_times.append(avg_time)
        print()
    
    # ทดสอบแบบตรง
    test_analytics_api_directly()
    test_database_directly()
    diagnose_slow_response()
    
    # สรุป
    print("\n📊 SUMMARY")
    print("=" * 50)
    
    if avg_times:
        overall_avg = statistics.mean(avg_times)
        print(f"Overall Average Response Time: {overall_avg:.2f}ms")
        
        if overall_avg < 100:
            print("🎉 EXCELLENT PERFORMANCE!")
        elif overall_avg < 500:
            print("✅ GOOD PERFORMANCE")
        elif overall_avg < 1000:
            print("⚠️ ACCEPTABLE PERFORMANCE")
        else:
            print("❌ POOR PERFORMANCE")
    
    print("\n💡 Performance Tips:")
    print("- Response times < 100ms = Excellent")
    print("- Response times < 500ms = Good") 
    print("- Response times > 1000ms = Needs optimization")
    print("- The original test may have overhead from complex testing logic")

if __name__ == "__main__":
    main()