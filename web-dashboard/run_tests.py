#!/usr/bin/env python3
"""
AI Content Factory - Complete Test Runner
รันการทดสอบระบบทั้งหมด พร้อมตรวจจับและแก้ไขปัญหา
"""

import os
import sys
import time
import json
import requests
import sqlite3
import subprocess
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = []
        self.problems = []
        self.server_process = None
        
    def log_test(self, test_name, status, details=""):
        """บันทึกผลการทดสอบ"""
        icons = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
        colors = {"PASS": "\033[92m", "FAIL": "\033[91m", "WARN": "\033[93m", "INFO": "\033[94m"}
        
        icon = icons.get(status, "•")
        color = colors.get(status, "")
        
        print(f"{icon} {color}{test_name:<30} {status}\033[0m")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def check_prerequisites(self):
        """ตรวจสอบข้อกำหนดเบื้องต้น"""
        print("\n🔍 CHECKING PREREQUISITES")
        print("-" * 40)
        
        # Check Python version
        version = sys.version_info
        if version.major >= 3 and version.minor >= 7:
            self.log_test("Python Version", "PASS", f"Python {version.major}.{version.minor}")
        else:
            self.log_test("Python Version", "FAIL", f"Need Python 3.7+, got {version.major}.{version.minor}")
            return False
        
        # Check required files
        required_files = ['app.py', 'templates/base.html', 'templates/dashboard.html']
        missing_files = []
        
        for file_path in required_files:
            if os.path.exists(file_path):
                self.log_test(f"File: {file_path}", "PASS")
            else:
                self.log_test(f"File: {file_path}", "FAIL", "Missing")
                missing_files.append(file_path)
        
        if missing_files:
            self.problems.append(f"Missing files: {', '.join(missing_files)}")
            return False
        
        # Check packages
        required_packages = ['flask', 'requests']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                self.log_test(f"Package: {package}", "PASS")
            except ImportError:
                self.log_test(f"Package: {package}", "FAIL", "Not installed")
                missing_packages.append(package)
        
        if missing_packages:
            self.problems.append(f"Missing packages: {', '.join(missing_packages)}")
            print(f"\n💡 Run: pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def start_server(self):
        """เริ่มต้น server"""
        print("\n🚀 STARTING SERVER")
        print("-" * 40)
        
        # Check if server is already running
        try:
            response = requests.get(self.base_url, timeout=2)
            self.log_test("Server Status", "INFO", "Already running")
            return True
        except requests.exceptions.ConnectionError:
            pass  # Server not running, which is expected
        
        # Start server
        try:
            print("Starting Flask server...")
            self.server_process = subprocess.Popen(
                [sys.executable, 'app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for server to start
            for i in range(10):  # Wait up to 10 seconds
                try:
                    response = requests.get(self.base_url, timeout=1)
                    if response.status_code == 200:
                        self.log_test("Server Start", "PASS", f"Started in {i+1} seconds")
                        return True
                except:
                    time.sleep(1)
            
            self.log_test("Server Start", "FAIL", "Timeout waiting for server")
            return False
            
        except Exception as e:
            self.log_test("Server Start", "FAIL", f"Error: {e}")
            return False
    
    def test_basic_functionality(self):
        """ทดสอบฟังก์ชันพื้นฐาน"""
        print("\n🧪 TESTING BASIC FUNCTIONALITY")
        print("-" * 40)
        
        # Test dashboard
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Dashboard Page", "PASS")
            else:
                self.log_test("Dashboard Page", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Page", "FAIL", f"Error: {e}")
        
        # Test API endpoints
        api_endpoints = [
            "/api/dashboard-stats",
            "/api/trends",
            "/api/opportunities"
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_test(f"API: {endpoint}", "PASS")
                else:
                    self.log_test(f"API: {endpoint}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"API: {endpoint}", "FAIL", f"Error: {e}")
    
    def test_data_flow(self):
        """ทดสอบ Data flow"""
        print("\n📊 TESTING DATA FLOW")
        print("-" * 40)
        
        # Test 1: Collect trends
        try:
            response = requests.post(f"{self.base_url}/api/collect-trends", timeout=10)
            data = response.json()
            
            if data.get('success'):
                trends_count = len(data.get('trends', []))
                self.log_test("Collect Trends", "PASS", f"Collected {trends_count} trends")
                
                # Wait a bit for database write
                time.sleep(1)
                
                # Test 2: Verify trends in database
                response = requests.get(f"{self.base_url}/api/trends")
                trends_data = response.json()
                db_trends = trends_data.get('trends', [])
                
                if db_trends:
                    self.log_test("Store Trends", "PASS", f"Found {len(db_trends)} in DB")
                    
                    # Test 3: Analyze first trend
                    trend = db_trends[0]
                    trend_id = trend['id']
                    
                    response = requests.post(f"{self.base_url}/api/analyze-trend/{trend_id}", timeout=15)
                    analysis_data = response.json()
                    
                    if analysis_data.get('success'):
                        opportunities = analysis_data.get('opportunities', [])
                        self.log_test("Analyze Trend", "PASS", f"Generated {len(opportunities)} opportunities")
                        
                        # Test 4: Check opportunities in database
                        time.sleep(1)
                        response = requests.get(f"{self.base_url}/api/opportunities")
                        opp_data = response.json()
                        db_opportunities = opp_data.get('opportunities', [])
                        
                        if db_opportunities:
                            self.log_test("Store Opportunities", "PASS", f"Found {len(db_opportunities)} in DB")
                            
                            # Test 5: Select opportunity
                            opp = db_opportunities[0]
                            opp_id = opp['id']
                            
                            response = requests.post(f"{self.base_url}/api/opportunity/{opp_id}/select")
                            select_data = response.json()
                            
                            if select_data.get('success'):
                                self.log_test("Select Opportunity", "PASS", "Opportunity selected")
                                
                                # Test 6: Check content items
                                time.sleep(1)
                                response = requests.get(f"{self.base_url}/api/content-items")
                                content_data = response.json()
                                content_items = content_data.get('content_items', [])
                                
                                if content_items:
                                    self.log_test("Create Content Item", "PASS", f"Found {len(content_items)} items")
                                else:
                                    self.log_test("Create Content Item", "FAIL", "No content items created")
                            else:
                                self.log_test("Select Opportunity", "FAIL", "Selection failed")
                        else:
                            self.log_test("Store Opportunities", "FAIL", "No opportunities in DB")
                    else:
                        self.log_test("Analyze Trend", "FAIL", "Analysis failed")
                else:
                    self.log_test("Store Trends", "FAIL", "No trends in DB")
            else:
                self.log_test("Collect Trends", "FAIL", "Collection failed")
                
        except Exception as e:
            self.log_test("Data Flow", "FAIL", f"Error: {e}")
    
    def test_ui_pages(self):
        """ทดสอบ UI pages"""
        print("\n🎨 TESTING UI PAGES")
        print("-" * 40)
        
        pages = [
            ("/", "Dashboard"),
            ("/trends", "Trends"),
            ("/opportunities", "Opportunities")
        ]
        
        for url, name in pages:
            try:
                response = requests.get(f"{self.base_url}{url}", timeout=5)
                content = response.text
                
                if response.status_code == 200:
                    # Check for HTML structure
                    if "<html" in content and "</html>" in content:
                        self.log_test(f"{name} HTML", "PASS", "Valid structure")
                    else:
                        self.log_test(f"{name} HTML", "FAIL", "Invalid structure")
                    
                    # Check for CSS
                    if "bootstrap" in content.lower():
                        self.log_test(f"{name} CSS", "PASS", "Bootstrap loaded")
                    else:
                        self.log_test(f"{name} CSS", "WARN", "No Bootstrap detected")
                    
                    # Check for JavaScript
                    if "<script" in content:
                        self.log_test(f"{name} JS", "PASS", "JavaScript included")
                    else:
                        self.log_test(f"{name} JS", "WARN", "No JavaScript detected")
                else:
                    self.log_test(f"{name} Page", "FAIL", f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"{name} Page", "FAIL", f"Error: {e}")
    
    def check_final_state(self):
        """ตรวจสอบสถานะสุดท้าย"""
        print("\n📈 FINAL STATE CHECK")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/api/dashboard-stats")
            data = response.json()
            stats = data.get('today_stats', {})
            
            trends_count = stats.get('trends_collected', 0)
            opportunities_count = stats.get('opportunities_generated', 0)
            content_count = stats.get('content_created', 0)
            
            print(f"   📊 Final Statistics:")
            print(f"      Trends: {trends_count}")
            print(f"      Opportunities: {opportunities_count}")
            print(f"      Content Items: {content_count}")
            
            if trends_count > 0:
                self.log_test("Has Trends", "PASS", f"{trends_count} trends")
            else:
                self.log_test("Has Trends", "WARN", "No trends collected")
            
            if opportunities_count > 0:
                self.log_test("Has Opportunities", "PASS", f"{opportunities_count} opportunities")
            else:
                self.log_test("Has Opportunities", "WARN", "No opportunities generated")
            
            if content_count > 0:
                self.log_test("Has Content", "PASS", f"{content_count} content items")
            else:
                self.log_test("Has Content", "WARN", "No content items created")
                
        except Exception as e:
            self.log_test("Final State", "FAIL", f"Error: {e}")
    
    def cleanup(self):
        """ทำความสะอาด"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("\n🧹 Server stopped")
            except:
                try:
                    self.server_process.kill()
                    print("\n🧹 Server killed")
                except:
                    pass
    
    def generate_report(self):
        """สร้างรายงาน"""
        print("\n📊 TEST REPORT")
        print("=" * 50)
        
        pass_count = len([r for r in self.test_results if r['status'] == 'PASS'])
        fail_count = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warn_count = len([r for r in self.test_results if r['status'] == 'WARN'])
        total_count = len(self.test_results)
        
        print(f"✅ Passed: {pass_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"⚠️  Warnings: {warn_count}")
        print(f"📊 Total: {total_count}")
        
        if total_count > 0:
            success_rate = (pass_count / total_count) * 100
            print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if self.problems:
            print(f"\n🚨 PROBLEMS DETECTED:")
            for i, problem in enumerate(self.problems, 1):
                print(f"   {i}. {problem}")
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total_count,
                'passed': pass_count,
                'failed': fail_count,
                'warnings': warn_count,
                'success_rate': success_rate if total_count > 0 else 0
            },
            'tests': self.test_results,
            'problems': self.problems
        }
        
        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved: test_report.json")
        
        # Final assessment
        if fail_count == 0:
            if warn_count == 0:
                print(f"\n🎉 ALL TESTS PASSED! System is working perfectly.")
                print(f"🌐 Open http://localhost:5000 in your browser")
            else:
                print(f"\n✅ System is working with minor issues.")
        else:
            print(f"\n⚠️  System has issues that need to be fixed.")
        
        return fail_count == 0
    
    def run_complete_test(self):
        """รันการทดสอบทั้งหมด"""
        print("🧪 AI CONTENT FACTORY - COMPLETE SYSTEM TEST")
        print("=" * 60)
        
        try:
            # Step 1: Check prerequisites
            if not self.check_prerequisites():
                print("\n❌ Prerequisites check failed!")
                return False
            
            # Step 2: Start server
            if not self.start_server():
                print("\n❌ Server start failed!")
                return False
            
            # Step 3: Test basic functionality
            self.test_basic_functionality()
            
            # Step 4: Test data flow
            self.test_data_flow()
            
            # Step 5: Test UI pages
            self.test_ui_pages()
            
            # Step 6: Check final state
            self.check_final_state()
            
            # Step 7: Generate report
            return self.generate_report()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            return False
        except Exception as e:
            print(f"\n\n❌ Unexpected error: {e}")
            return False
        finally:
            self.cleanup()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Content Factory Complete Test Runner')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--no-server', action='store_true', help='Skip server startup (assume running)')
    parser.add_argument('--url', default='http://localhost:5000', help='Server URL')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    runner.base_url = args.url
    
    if args.quick:
        print("🚀 Running Quick Tests...")
        runner.check_prerequisites()
        if not args.no_server:
            runner.start_server()
        runner.test_basic_functionality()
        runner.generate_report()
    else:
        print("🚀 Running Complete Test Suite...")
        success = runner.run_complete_test()
        
        if success:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()