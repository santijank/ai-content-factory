#!/usr/bin/env python3
"""
AI Content Factory - System Test Suite (Performance Fixed)
ทดสอบความสมบูรณ์ของระบบทั้งหมด
"""

import requests
import sqlite3
import json
import time
import os
import sys
import socket
from datetime import datetime
import subprocess
import threading
import statistics

# Fix Windows localhost performance issue
old_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return old_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4_only

class AIContentFactoryTester:
    def __init__(self, base_url="http://localhost:5000", db_path="content_factory.db"):
        # Use IP address to avoid DNS resolution delays
        self.base_url = base_url.replace('localhost', '127.0.0.1')
        self.db_path = db_path
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Create optimized session
        self.session = requests.Session()
        self.session.proxies = {'http': None, 'https': None}
        
    def log_test(self, test_name, status, message="", details=""):
        """บันทึกผลการทดสอบ"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        self.test_results.append(result)
        
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ {test_name}: {message}")
        elif status == "FAIL":
            self.failed_tests += 1
            print(f"❌ {test_name}: {message}")
            if details:
                print(f"   Details: {details}")
        elif status == "SKIP":
            print(f"⏭️  {test_name}: {message}")
        else:
            print(f"ℹ️  {test_name}: {message}")

    def test_database_exists(self):
        """ทดสอบว่ามี database file หรือไม่"""
        try:
            if os.path.exists(self.db_path):
                file_size = os.path.getsize(self.db_path)
                self.log_test("Database File", "PASS", f"Database exists ({file_size} bytes)")
                return True
            else:
                self.log_test("Database File", "FAIL", "Database file not found")
                return False
        except Exception as e:
            self.log_test("Database File", "FAIL", str(e))
            return False

    def test_database_schema(self):
        """ทดสอบ schema ของ database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ตรวจสอบตาราง
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['trends', 'content_opportunities', 'content_items']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if not missing_tables:
                visible_tables = [t for t in tables if not t.startswith('sqlite_')]
                self.log_test("Database Schema", "PASS", f"All required tables exist: {visible_tables}")
            else:
                self.log_test("Database Schema", "FAIL", f"Missing tables: {missing_tables}")
                
            # ตรวจสอบข้อมูลในตาราง
            cursor.execute("SELECT COUNT(*) FROM trends")
            trends_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM content_opportunities")
            opportunities_count = cursor.fetchone()[0]
            
            conn.close()
            
            if trends_count > 0 and opportunities_count > 0:
                self.log_test("Database Data", "PASS", f"Trends: {trends_count}, Opportunities: {opportunities_count}")
            else:
                self.log_test("Database Data", "FAIL", "No sample data found")
                
        except Exception as e:
            self.log_test("Database Schema", "FAIL", str(e))

    def test_server_connection(self):
        """ทดสอบการเชื่อมต่อ server"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Server Connection", "PASS", f"Server responding (Status: {response.status_code})")
                return True
            else:
                self.log_test("Server Connection", "FAIL", f"Server error (Status: {response.status_code})")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("Server Connection", "FAIL", "Cannot connect to server")
            return False
        except Exception as e:
            self.log_test("Server Connection", "FAIL", str(e))
            return False

    def test_dashboard_html(self):
        """ทดสอบหน้า dashboard"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            html_content = response.text
            
            # ตรวจสอบ HTML elements
            required_elements = [
                "AI Content Factory",
                "Analytics",
                "Trends", 
                "loadAnalytics",
                "loadTrends"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if not missing_elements:
                self.log_test("Dashboard HTML", "PASS", "All required elements found")
            else:
                self.log_test("Dashboard HTML", "FAIL", f"Missing elements: {missing_elements}")
                
        except Exception as e:
            self.log_test("Dashboard HTML", "FAIL", str(e))

    def test_api_analytics(self):
        """ทดสอบ Analytics API"""
        try:
            response = self.session.get(f"{self.base_url}/api/analytics", timeout=5)
            if response.status_code == 200:
                data = response.json()
                required_keys = ['trends_count', 'opportunities_count', 'avg_roi']
                
                if all(key in data for key in required_keys):
                    self.log_test("Analytics API", "PASS", 
                                f"Trends: {data['trends_count']}, Opportunities: {data['opportunities_count']}, ROI: {data['avg_roi']:.2f}")
                else:
                    self.log_test("Analytics API", "FAIL", "Missing required data keys")
            else:
                self.log_test("Analytics API", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Analytics API", "FAIL", str(e))

    def test_api_trends(self):
        """ทดสอบ Trends API"""
        try:
            # GET trends
            response = self.session.get(f"{self.base_url}/api/trends", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'trends' in data and len(data['trends']) > 0:
                    self.log_test("Get Trends API", "PASS", f"Retrieved {len(data['trends'])} trends")
                else:
                    self.log_test("Get Trends API", "FAIL", "No trends data")
            
            # POST collect trends
            response = self.session.post(f"{self.base_url}/api/collect-trends", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test("Collect Trends API", "PASS", f"Collected {data.get('count', 0)} new trends")
                else:
                    self.log_test("Collect Trends API", "FAIL", "Unexpected response")
            else:
                self.log_test("Collect Trends API", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Trends API", "FAIL", str(e))

    def test_api_opportunities(self):
        """ทดสอบ Opportunities API"""
        try:
            # GET opportunities
            response = self.session.get(f"{self.base_url}/api/opportunities", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'opportunities' in data:
                    self.log_test("Get Opportunities API", "PASS", f"Retrieved {len(data['opportunities'])} opportunities")
                else:
                    self.log_test("Get Opportunities API", "FAIL", "No opportunities data")
            
            # POST generate opportunities
            response = self.session.post(f"{self.base_url}/api/generate-opportunities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test("Generate Opportunities API", "PASS", f"Generated {data.get('count', 0)} new opportunities")
                else:
                    self.log_test("Generate Opportunities API", "FAIL", "Unexpected response")
            else:
                self.log_test("Generate Opportunities API", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Opportunities API", "FAIL", str(e))

    def test_database_integrity(self):
        """ทดสอบความสมบูรณ์ของ database หลังจาก API calls"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ตรวจสอบ Foreign Key relationships
            cursor.execute("""
                SELECT co.id, co.trend_id, t.id 
                FROM content_opportunities co 
                LEFT JOIN trends t ON co.trend_id = t.id 
                WHERE t.id IS NULL
            """)
            orphaned_opportunities = cursor.fetchall()
            
            if not orphaned_opportunities:
                self.log_test("Database Integrity", "PASS", "All foreign key relationships valid")
            else:
                self.log_test("Database Integrity", "FAIL", f"Found {len(orphaned_opportunities)} orphaned opportunities")
            
            # ตรวจสอบข้อมูลที่สร้างใหม่
            cursor.execute("SELECT COUNT(*) FROM trends WHERE collected_at > datetime('now', '-1 minute')")
            recent_trends = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM content_opportunities WHERE created_at > datetime('now', '-1 minute')")
            recent_opportunities = cursor.fetchone()[0]
            
            if recent_trends > 0 or recent_opportunities > 0:
                self.log_test("Recent Data", "PASS", f"New trends: {recent_trends}, New opportunities: {recent_opportunities}")
            else:
                self.log_test("Recent Data", "INFO", "No new data created (may be expected)")
            
            conn.close()
            
        except Exception as e:
            self.log_test("Database Integrity", "FAIL", str(e))

    def test_performance_optimized(self):
        """ทดสอบประสิทธิภาพแบบที่แก้ไขแล้ว"""
        try:
            # ทดสอบ response time หลายครั้ง
            response_times = []
            
            # Warm up
            self.session.get(f"{self.base_url}/api/analytics", timeout=5)
            
            # Test multiple times
            for i in range(3):
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/api/analytics", timeout=5)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = (end_time - start_time) * 1000
                    response_times.append(response_time)
            
            if response_times:
                avg_time = statistics.mean(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
                
                if avg_time < 100:
                    self.log_test("Response Time", "PASS", f"Excellent: {avg_time:.2f}ms (min: {min_time:.2f}ms, max: {max_time:.2f}ms)")
                elif avg_time < 500:
                    self.log_test("Response Time", "PASS", f"Good: {avg_time:.2f}ms (min: {min_time:.2f}ms, max: {max_time:.2f}ms)")
                elif avg_time < 1000:
                    self.log_test("Response Time", "PASS", f"Acceptable: {avg_time:.2f}ms (min: {min_time:.2f}ms, max: {max_time:.2f}ms)")
                else:
                    self.log_test("Response Time", "FAIL", f"Too slow: {avg_time:.2f}ms")
            
        except Exception as e:
            self.log_test("Performance", "FAIL", str(e))

    def test_concurrent_requests(self):
        """ทดสอบ concurrent requests"""
        try:
            import concurrent.futures
            
            def make_request():
                return self.session.get(f"{self.base_url}/api/analytics", timeout=5)
            
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(make_request) for _ in range(3)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            concurrent_time = time.time() - start_time
            success_count = sum(1 for r in results if r.status_code == 200)
            
            if success_count == 3:
                self.log_test("Concurrent Requests", "PASS", f"3 concurrent requests in {concurrent_time:.2f}s")
            else:
                self.log_test("Concurrent Requests", "FAIL", f"Only {success_count}/3 requests succeeded")
                
        except Exception as e:
            self.log_test("Concurrent Requests", "FAIL", str(e))

    def test_error_handling(self):
        """ทดสอบการจัดการ error"""
        try:
            # ทดสอบ invalid endpoint
            response = self.session.get(f"{self.base_url}/api/invalid-endpoint", timeout=3)
            if response.status_code == 404:
                self.log_test("404 Error Handling", "PASS", "Invalid endpoint returns 404")
            else:
                self.log_test("404 Error Handling", "FAIL", f"Expected 404, got {response.status_code}")
            
            # ทดสอบ invalid method
            response = requests.patch(f"{self.base_url}/api/trends", timeout=3, proxies={'http': None, 'https': None})
            if response.status_code in [405, 404]:
                self.log_test("Method Error Handling", "PASS", f"Invalid method returns {response.status_code}")
            else:
                self.log_test("Method Error Handling", "FAIL", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling", "FAIL", str(e))

    def check_server_running(self):
        """ตรวจสอบว่า server กำลังรันอยู่หรือไม่"""
        try:
            response = self.session.get(self.base_url, timeout=2)
            return True
        except:
            return False

    def run_all_tests(self):
        """รันการทดสอบทั้งหมด"""
        print("🚀 AI Content Factory - System Test Suite (Performance Optimized)")
        print("=" * 70)
        print(f"Testing server at: {self.base_url}")
        print(f"Database path: {self.db_path}")
        print("Performance fixes: IPv4 only, IP address, session reuse, proxy disabled")
        print("=" * 70)
        
        # ตรวจสอบ server ก่อน
        if not self.check_server_running():
            print("❌ Server is not running!")
            print("Please start the server with: python simple_app_ultra_fast.py")
            return False
        
        # รันการทดสอบทั้งหมด
        test_methods = [
            self.test_database_exists,
            self.test_database_schema,
            self.test_server_connection,
            self.test_dashboard_html,
            self.test_api_analytics,
            self.test_api_trends,
            self.test_api_opportunities,
            self.test_database_integrity,
            self.test_performance_optimized,
            self.test_concurrent_requests,
            self.test_error_handling
        ]
        
        print("\n🧪 Running Tests...")
        print("-" * 40)
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.1)
            except Exception as e:
                self.log_test(test_method.__name__, "FAIL", f"Test execution error: {str(e)}")
        
        self.print_summary()
        return self.failed_tests == 0

    def print_summary(self):
        """แสดงสรุปผลการทดสอบ"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! System is working perfectly!")
            print("✅ Your AI Content Factory is ready for production!")
            print("⚡ Performance optimizations working correctly!")
        else:
            print(f"\n⚠️  {self.failed_tests} test(s) failed. Please check the issues above.")
            
        print("\n📋 Detailed Results:")
        print("-" * 40)
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "ℹ️"
            print(f"{status_icon} [{result['timestamp']}] {result['test']}: {result['message']}")
        
        # Cleanup
        self.session.close()

def main():
    """ฟังก์ชันหลัก"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("AI Content Factory System Tester (Performance Optimized)")
            print("Usage: python test_system.py [base_url] [db_path]")
            print("Default: python test_system.py http://localhost:5000 content_factory.db")
            print("\nPerformance fixes included:")
            print("- Uses 127.0.0.1 instead of localhost")
            print("- Forces IPv4 only")
            print("- Disables proxy detection")
            print("- Uses session for connection reuse")
            return
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    db_path = sys.argv[2] if len(sys.argv) > 2 else "content_factory.db"
    
    tester = AIContentFactoryTester(base_url, db_path)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()