#!/usr/bin/env python3
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
    
    print("\n💡 Fix applied:")
    print("- Using 127.0.0.1 instead of localhost")
    print("- Forced IPv4 only")
    print("- Disabled proxy")
    print("- Session connection reuse")

if __name__ == "__main__":
    main()
