#!/usr/bin/env python3
"""
AI Content Factory - Performance Benchmark
ทดสอบประสิทธิภาพของระบบ
"""

import requests
import time
import threading
import statistics
import json

class PerformanceBenchmark:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
    
    def benchmark_single_request(self, endpoint, method="GET", iterations=10):
        """ทดสอบประสิทธิภาพของ endpoint เดียว"""
        print(f"🔄 Benchmarking {method} {endpoint}...")
        
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=10)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # milliseconds
                
                if response.status_code == 200:
                    response_times.append(response_time)
                    success_count += 1
                    
            except Exception as e:
                print(f"   Request {i+1} failed: {e}")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            median_time = statistics.median(response_times)
            
            result = {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'success_count': success_count,
                'success_rate': (success_count / iterations) * 100,
                'avg_response_time': avg_time,
                'min_response_time': min_time,
                'max_response_time': max_time,
                'median_response_time': median_time
            }
            
            self.results[f"{method} {endpoint}"] = result
            
            print(f"   ✅ Avg: {avg_time:.2f}ms | Min: {min_time:.2f}ms | Max: {max_time:.2f}ms")
            print(f"   📊 Success Rate: {result['success_rate']:.1f}%")
            
        else:
            print(f"   ❌ All requests failed")
    
    def benchmark_concurrent_requests(self, endpoint, concurrent_users=5, requests_per_user=5):
        """ทดสอบ concurrent requests"""
        print(f"🚀 Benchmarking concurrent access: {concurrent_users} users, {requests_per_user} requests each")
        
        all_response_times = []
        success_count = 0
        total_requests = concurrent_users * requests_per_user
        
        def user_simulation(user_id):
            user_times = []
            user_success = 0
            
            for req in range(requests_per_user):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    if response.status_code == 200:
                        user_times.append(response_time)
                        user_success += 1
                        
                except Exception as e:
                    pass
            
            return user_times, user_success
        
        # สร้าง threads
        threads = []
        results = [None] * concurrent_users
        
        start_time = time.time()
        
        for i in range(concurrent_users):
            thread = threading.Thread(
                target=lambda idx=i: results.__setitem__(idx, user_simulation(idx)),
                args=()
            )
            threads.append(thread)
            thread.start()
        
        # รอให้ threads เสร็จ
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # รวมผลลัพธ์
        for user_times, user_success in results:
            if user_times:
                all_response_times.extend(user_times)
                success_count += user_success
        
        if all_response_times:
            avg_time = statistics.mean(all_response_times)
            throughput = total_requests / total_time  # requests per second
            
            result = {
                'endpoint': endpoint,
                'concurrent_users': concurrent_users,
                'requests_per_user': requests_per_user,
                'total_requests': total_requests,
                'success_count': success_count,
                'success_rate': (success_count / total_requests) * 100,
                'total_time': total_time,
                'avg_response_time': avg_time,
                'throughput': throughput
            }
            
            self.results[f"Concurrent {endpoint}"] = result
            
            print(f"   ✅ Total Time: {total_time:.2f}s")
            print(f"   📊 Throughput: {throughput:.2f} req/sec")
            print(f"   ⚡ Avg Response: {avg_time:.2f}ms")
            print(f"   📈 Success Rate: {result['success_rate']:.1f}%")
        
    def benchmark_api_load(self):
        """ทดสอบ API load ต่างๆ"""
        print(f"⚡ API Load Testing...")
        
        # ทดสอบขนาดข้อมูลที่ส่งกลับ
        endpoints_to_test = [
            ('/api/analytics', 'GET'),
            ('/api/trends', 'GET'),
            ('/api/opportunities', 'GET')
        ]
        
        for endpoint, method in endpoints_to_test:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data_size = len(response.content)
                    
                    try:
                        json_data = response.json()
                        if endpoint == '/api/trends':
                            record_count = len(json_data.get('trends', []))
                        elif endpoint == '/api/opportunities':
                            record_count = len(json_data.get('opportunities', []))
                        else:
                            record_count = 1
                    except:
                        record_count = 0
                    
                    print(f"   📄 {endpoint}: {data_size} bytes, {record_count} records, {response_time:.2f}ms")
                    
            except Exception as e:
                print(f"   ❌ {endpoint}: {e}")
    
    def run_full_benchmark(self):
        """รันการทดสอบประสิทธิภาพทั้งหมด"""
        print("⚡ AI Content Factory - Performance Benchmark")
        print("=" * 60)
        
        # ทดสอบการเชื่อมต่อพื้นฐาน
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code != 200:
                print("❌ Server not responding properly")
                return False
        except:
            print("❌ Cannot connect to server")
            return False
        
        print(f"🎯 Testing server: {self.base_url}")
        print("-" * 60)
        
        # 1. ทดสอบ individual endpoints
        print("\n1️⃣ Individual Endpoint Performance:")
        endpoints = [
            ('/', 'GET'),
            ('/api/analytics', 'GET'),
            ('/api/trends', 'GET'),
            ('/api/opportunities', 'GET'),
            ('/api/collect-trends', 'POST'),
            ('/api/generate-opportunities', 'POST')
        ]
        
        for endpoint, method in endpoints:
            self.benchmark_single_request(endpoint, method, iterations=5)
            time.sleep(0.5)  # หน่วงเวลาระหว่างการทดสอบ
        
        # 2. ทดสอบ concurrent access
        print("\n2️⃣ Concurrent Access Performance:")
        self.benchmark_concurrent_requests('/api/analytics', concurrent_users=3, requests_per_user=3)
        
        # 3. ทดสอบ API load
        print("\n3️⃣ API Data Load Analysis:")
        self.benchmark_api_load()
        
        # 4. ทดสอบ stress test
        print("\n4️⃣ Stress Testing:")
        self.stress_test()
        
        # แสดงสรุปผล
        self.print_summary()
        
        return True
    
    def stress_test(self):
        """ทดสอบความทนทานของระบบ"""
        print("🔥 Running stress test (rapid requests)...")
        
        rapid_requests = 20
        success_count = 0
        start_time = time.time()
        
        for i in range(rapid_requests):
            try:
                response = requests.get(f"{self.base_url}/api/analytics", timeout=2)
                if response.status_code == 200:
                    success_count += 1
            except:
                pass
        
        total_time = time.time() - start_time
        throughput = rapid_requests / total_time
        success_rate = (success_count / rapid_requests) * 100
        
        print(f"   ⚡ {rapid_requests} rapid requests in {total_time:.2f}s")
        print(f"   📊 Throughput: {throughput:.2f} req/sec")
        print(f"   ✅ Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("   🎉 Excellent stress performance!")
        elif success_rate >= 70:
            print("   😊 Good stress performance")
        else:
            print("   ⚠️ Poor stress performance - system may be overloaded")
    
    def print_summary(self):
        """แสดงสรุปผลการทดสอบ"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("❌ No benchmark results available")
            return
        
        # หา endpoint ที่เร็วที่สุดและช้าที่สุด
        response_times = []
        for key, result in self.results.items():
            if 'avg_response_time' in result:
                response_times.append((key, result['avg_response_time']))
        
        if response_times:
            response_times.sort(key=lambda x: x[1])
            fastest = response_times[0]
            slowest = response_times[-1]
            
            print(f"⚡ Fastest Endpoint: {fastest[0]} ({fastest[1]:.2f}ms)")
            print(f"🐌 Slowest Endpoint: {slowest[0]} ({slowest[1]:.2f}ms)")
        
        # คำนวณ overall performance score
        avg_response_times = [r['avg_response_time'] for r in self.results.values() if 'avg_response_time' in r]
        success_rates = [r['success_rate'] for r in self.results.values() if 'success_rate' in r]
        
        if avg_response_times and success_rates:
            avg_response = statistics.mean(avg_response_times)
            avg_success = statistics.mean(success_rates)
            
            # Performance score (lower response time = better, higher success rate = better)
            if avg_response < 100 and avg_success > 95:
                performance_grade = "A+ (Excellent)"
            elif avg_response < 200 and avg_success > 90:
                performance_grade = "A (Very Good)"
            elif avg_response < 500 and avg_success > 80:
                performance_grade = "B (Good)"
            elif avg_response < 1000 and avg_success > 70:
                performance_grade = "C (Average)"
            else:
                performance_grade = "D (Needs Improvement)"
            
            print(f"\n📈 Overall Performance Grade: {performance_grade}")
            print(f"⏱️ Average Response Time: {avg_response:.2f}ms")
            print(f"✅ Average Success Rate: {avg_success:.1f}%")
        
        # แนะนำการปรับปรุง
        print(f"\n💡 Performance Recommendations:")
        
        slow_endpoints = [key for key, result in self.results.items() 
                         if 'avg_response_time' in result and result['avg_response_time'] > 500]
        
        if slow_endpoints:
            print(f"🔧 Optimize slow endpoints: {', '.join(slow_endpoints)}")
        
        low_success = [key for key, result in self.results.items() 
                      if 'success_rate' in result and result['success_rate'] < 90]
        
        if low_success:
            print(f"🚨 Fix reliability issues: {', '.join(low_success)}")
        
        if not slow_endpoints and not low_success:
            print("🎉 No performance issues detected!")
        
        # รายละเอียดแต่ละ endpoint
        print(f"\n📋 Detailed Results:")
        print("-" * 40)
        for key, result in self.results.items():
            if 'avg_response_time' in result:
                print(f"{key}:")
                print(f"  ⏱️ Response: {result['avg_response_time']:.2f}ms")
                print(f"  ✅ Success: {result['success_rate']:.1f}%")
                if 'throughput' in result:
                    print(f"  ⚡ Throughput: {result['throughput']:.2f} req/sec")


def main():
    """ฟังก์ชันหลัก"""
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    benchmark = PerformanceBenchmark(base_url)
    success = benchmark.run_full_benchmark()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()