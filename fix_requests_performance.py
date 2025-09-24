#!/usr/bin/env python3
"""
แก้ไขปัญหา requests library ช้าใน Windows
"""

import requests
import time
import socket

def test_requests_fixes():
    """ทดสอบวิธีแก้ไขต่างๆ สำหรับ requests ช้า"""
    
    print("🔧 Testing Requests Performance Fixes")
    print("=" * 50)
    
    base_url = "http://localhost:5000/api/test"
    
    # Test 1: ใช้ IP address แทน localhost
    print("\n1. Testing with IP address (127.0.0.1):")
    ip_url = "http://127.0.0.1:5000/api/test"
    start = time.time()
    try:
        response = requests.get(ip_url, timeout=5)
        elapsed = (time.time() - start) * 1000
        print(f"   IP address: {elapsed:.2f}ms")
    except Exception as e:
        print(f"   IP address: FAILED ({e})")
    
    # Test 2: Disable IPv6
    print("\n2. Testing with disabled IPv6:")
    try:
        # Force IPv4
        old_getaddrinfo = socket.getaddrinfo
        def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
            return old_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
        
        socket.getaddrinfo = getaddrinfo_ipv4_only
        
        start = time.time()
        response = requests.get(base_url, timeout=5)
        elapsed = (time.time() - start) * 1000
        print(f"   IPv4 only: {elapsed:.2f}ms")
        
        # Restore original function
        socket.getaddrinfo = old_getaddrinfo
        
    except Exception as e:
        print(f"   IPv4 only: FAILED ({e})")
        socket.getaddrinfo = old_getaddrinfo
    
    # Test 3: Session with connection pooling
    print("\n3. Testing with Session (connection pooling):")
    session = requests.Session()
    start = time.time()
    try:
        response = session.get(ip_url, timeout=5)
        elapsed = (time.time() - start) * 1000
        print(f"   Session: {elapsed:.2f}ms")
    except Exception as e:
        print(f"   Session: FAILED ({e})")
    finally:
        session.close()
    
    # Test 4: Disable proxy
    print("\n4. Testing with disabled proxy:")
    start = time.time()
    try:
        response = requests.get(ip_url, timeout=5, proxies={'http': None, 'https': None})
        elapsed = (time.time() - start) * 1000
        print(f"   No proxy: {elapsed:.2f}ms")
    except Exception as e:
        print(f"   No proxy: FAILED ({e})")
    
    # Test 5: Custom adapter
    print("\n5. Testing with HTTPAdapter settings:")
    try:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        
        # Configure adapter
        adapter = HTTPAdapter(
            pool_connections=1,
            pool_maxsize=1,
            max_retries=Retry(total=0)
        )
        session.mount('http://', adapter)
        
        start = time.time()
        response = session.get(ip_url, timeout=5)
        elapsed = (time.time() - start) * 1000
        print(f"   Custom adapter: {elapsed:.2f}ms")
        
        session.close()
    except Exception as e:
        print(f"   Custom adapter: FAILED ({e})")

def create_fast_test_system():
    """สร้าง test system ที่ใช้ IP address แทน localhost"""
    
    print("\n📝 Creating Fast Test System...")
    
    fast_test_code = '''#!/usr/bin/env python3
"""
Fast Performance Test - Fixed for Windows
"""

import requests
import time
import statistics
import socket

# Force IPv4 to avoid IPv6/IPv4 conflicts
old_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return old_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4_only

def test_single_endpoint_speed(url, iterations=5):
    """ทดสอบความเร็วของ endpoint เดียว (Fixed Version)"""
    print(f"🔄 Testing {url}...")
    
    # Use IP address instead of localhost
    url = url.replace('localhost', '127.0.0.1')
    
    response_times = []
    
    # Create session for connection reuse
    session = requests.Session()
    
    # Disable proxy
    session.proxies = {'http': None, 'https': None}
    
    # Warm up request
    try:
        session.get(url, timeout=3)
    except:
        pass
    
    # Actual tests
    for i in range(iterations):
        start_time = time.time()
        try:
            response = session.get(url, timeout=5)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000  # ms
                response_times.append(response_time)
                print(f"  Request {i+1}: {response_time:.2f}ms")
            else:
                print(f"  Request {i+1}: ERROR ({response.status_code})")
                
        except Exception as e:
            print(f"  Request {i+1}: FAILED ({e})")
    
    session.close()
    
    if response_times:
        avg = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"📊 Results for {url}:")
        print(f"  Average: {avg:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        
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

def main():
    """รันการทดสอบประสิทธิภาพที่แก้ไขแล้ว"""
    print("⚡ Fast Performance Test - Windows Fixed")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        "http://localhost:5000/api/analytics",
        "http://localhost:5000/api/trends", 
        "http://localhost:5000/api/opportunities"
    ]
    
    avg_times = []
    
    for endpoint in endpoints:
        avg_time = test_single_endpoint_speed(endpoint, iterations=3)
        if avg_time:
            avg_times.append(avg_time)
        print()
    
    # Summary
    if avg_times:
        overall_avg = statistics.mean(avg_times)
        print(f"📊 Overall Average: {overall_avg:.2f}ms")
        
        if overall_avg < 100:
            print("🎉 EXCELLENT PERFORMANCE!")
        elif overall_avg < 500:
            print("✅ GOOD PERFORMANCE")
        else:
            print("⚠️ NEEDS IMPROVEMENT")
    
    print("\\n💡 Fix applied:")
    print("- Using 127.0.0.1 instead of localhost")
    print("- Forced IPv4 only")
    print("- Disabled proxy")
    print("- Session connection reuse")

if __name__ == "__main__":
    main()
'''
    
    with open('fast_test_fixed.py', 'w', encoding='utf-8') as f:
        f.write(fast_test_code)
    
    print("✅ Created fast_test_fixed.py")

def main():
    """รันการทดสอบและแก้ไข"""
    test_requests_fixes()
    create_fast_test_system()
    
    print("\n🎯 SOLUTION:")
    print("The problem is requests library DNS resolution on Windows")
    print("\n📋 Quick fixes:")
    print("1. Use 127.0.0.1 instead of localhost")
    print("2. Force IPv4 only")
    print("3. Disable proxy settings")
    print("4. Use session for connection reuse")
    
    print("\n🚀 Test the fix:")
    print("python fast_test_fixed.py")

if __name__ == "__main__":
    main()