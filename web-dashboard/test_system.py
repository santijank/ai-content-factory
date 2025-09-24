#!/usr/bin/env python3
"""
AI Content Factory - System Test Suite
ทดสอบระบบทั้งหมดพร้อมตรวจจับปัญหา
"""

import requests
import json
import time
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any
import unittest
from unittest.mock import patch
import sys

class Colors:
    """ANSI Color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.errors = []
        
    def print_header(self, title: str):
        """Print formatted test section header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}{Colors.END}\n")
        
    def print_test(self, test_name: str, status: str, details: str = ""):
        """Print test result"""
        if status == "PASS":
            icon = "✅"
            color = Colors.GREEN
        elif status == "FAIL":
            icon = "❌"
            color = Colors.RED
        elif status == "WARN":
            icon = "⚠️"
            color = Colors.YELLOW
        else:
            icon = "ℹ️"
            color = Colors.BLUE
            
        print(f"{icon} {color}{test_name:<40}{status}{Colors.END}")
        if details:
            print(f"   {Colors.WHITE}{details}{Colors.END}")
            
        self.test_results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def test_server_connection(self):
        """Test 1: Server Connection"""
        self.print_header("Server Connection Tests")
        
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                self.print_test("Server Connection", "PASS", f"Status: {response.status_code}")
                return True
            else:
                self.print_test("Server Connection", "FAIL", f"Status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_test("Server Connection", "FAIL", "Cannot connect to server")
            self.errors.append("Server is not running or not accessible")
            return False
        except requests.exceptions.Timeout:
            self.print_test("Server Connection", "FAIL", "Connection timeout")
            return False
        except Exception as e:
            self.print_test("Server Connection", "FAIL", f"Error: {str(e)}")
            return False

    def test_database_structure(self):
        """Test 2: Database Structure"""
        self.print_header("Database Structure Tests")
        
        db_path = "content_factory.db"
        
        if not os.path.exists(db_path):
            self.print_test("Database File Exists", "FAIL", "Database file not found")
            self.errors.append("Database file missing")
            return False
            
        self.print_test("Database File Exists", "PASS", f"Found: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check required tables
            tables = ['trends', 'content_opportunities', 'content_items']
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    self.print_test(f"Table '{table}' exists", "PASS")
                else:
                    self.print_test(f"Table '{table}' exists", "FAIL")
                    self.errors.append(f"Missing table: {table}")
                    
            # Check table structures
            cursor.execute("PRAGMA table_info(trends)")
            trends_columns = [row[1] for row in cursor.fetchall()]
            required_columns = ['id', 'source', 'topic', 'popularity_score', 'growth_rate', 'category']
            
            for col in required_columns:
                if col in trends_columns:
                    self.print_test(f"Column 'trends.{col}' exists", "PASS")
                else:
                    self.print_test(f"Column 'trends.{col}' exists", "FAIL")
                    self.errors.append(f"Missing column: trends.{col}")
                    
            conn.close()
            return True
            
        except Exception as e:
            self.print_test("Database Access", "FAIL", f"Error: {str(e)}")
            self.errors.append(f"Database error: {str(e)}")
            return False

    def test_api_endpoints(self):
        """Test 3: API Endpoints"""
        self.print_header("API Endpoints Tests")
        
        endpoints = [
            ("/", "GET", "Dashboard Page"),
            ("/trends", "GET", "Trends Page"),
            ("/opportunities", "GET", "Opportunities Page"),
            ("/api/dashboard-stats", "GET", "Dashboard Stats API"),
            ("/api/trends", "GET", "Trends API"),
            ("/api/opportunities", "GET", "Opportunities API"),
        ]
        
        for endpoint, method, description in endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", timeout=5)
                    
                if response.status_code == 200:
                    self.print_test(f"{description}", "PASS", f"{method} {endpoint}")
                else:
                    self.print_test(f"{description}", "FAIL", f"Status: {response.status_code}")
                    self.errors.append(f"API endpoint failed: {endpoint}")
                    
            except Exception as e:
                self.print_test(f"{description}", "FAIL", f"Error: {str(e)}")
                self.errors.append(f"API error {endpoint}: {str(e)}")

    def test_trend_collection(self):
        """Test 4: Trend Collection"""
        self.print_header("Trend Collection Tests")
        
        try:
            # Test collect trends API
            response = self.session.post(f"{self.base_url}/api/collect-trends", timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.print_test("Collect Trends API", "PASS", f"Collected {len(data.get('trends', []))} trends")
                
                # Verify trends in database
                time.sleep(1)  # Wait for database write
                trends_response = self.session.get(f"{self.base_url}/api/trends")
                trends_data = trends_response.json()
                
                if trends_data.get('trends'):
                    self.print_test("Trends Stored in Database", "PASS", f"Found {len(trends_data['trends'])} trends")
                    return trends_data['trends']
                else:
                    self.print_test("Trends Stored in Database", "FAIL", "No trends found")
                    self.errors.append("Trends not stored in database")
                    
            else:
                self.print_test("Collect Trends API", "FAIL", f"Response: {data}")
                self.errors.append("Trend collection failed")
                
        except Exception as e:
            self.print_test("Collect Trends API", "FAIL", f"Error: {str(e)}")
            self.errors.append(f"Trend collection error: {str(e)}")
            
        return []

    def test_trend_analysis(self, trends: List[Dict]):
        """Test 5: Trend Analysis"""
        self.print_header("Trend Analysis Tests")
        
        if not trends:
            self.print_test("Trend Analysis", "SKIP", "No trends available for analysis")
            return []
            
        try:
            trend = trends[0]  # Test with first trend
            trend_id = trend['id']
            
            response = self.session.post(f"{self.base_url}/api/analyze-trend/{trend_id}", timeout=15)
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                opportunities = data.get('opportunities', [])
                self.print_test("Trend Analysis API", "PASS", f"Generated {len(opportunities)} opportunities")
                
                # Verify opportunities in database
                time.sleep(1)
                opp_response = self.session.get(f"{self.base_url}/api/opportunities")
                opp_data = opp_response.json()
                
                if opp_data.get('opportunities'):
                    self.print_test("Opportunities Stored", "PASS", f"Found {len(opp_data['opportunities'])} opportunities")
                    return opp_data['opportunities']
                else:
                    self.print_test("Opportunities Stored", "FAIL", "No opportunities found")
                    self.errors.append("Opportunities not stored")
                    
            else:
                self.print_test("Trend Analysis API", "FAIL", f"Response: {data}")
                self.errors.append("Trend analysis failed")
                
        except Exception as e:
            self.print_test("Trend Analysis API", "FAIL", f"Error: {str(e)}")
            self.errors.append(f"Trend analysis error: {str(e)}")
            
        return []

    def test_opportunity_selection(self, opportunities: List[Dict]):
        """Test 6: Opportunity Selection"""
        self.print_header("Opportunity Selection Tests")
        
        if not opportunities:
            self.print_test("Opportunity Selection", "SKIP", "No opportunities available")
            return
            
        try:
            opportunity = opportunities[0]  # Test with first opportunity
            opp_id = opportunity['id']
            
            response = self.session.post(f"{self.base_url}/api/opportunity/{opp_id}/select", timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.print_test("Select Opportunity API", "PASS", f"Selected opportunity: {opp_id}")
                
                # Verify content item created
                time.sleep(1)
                content_response = self.session.get(f"{self.base_url}/api/content-items")
                content_data = content_response.json()
                
                if content_data.get('content_items'):
                    self.print_test("Content Item Created", "PASS", f"Found {len(content_data['content_items'])} content items")
                else:
                    self.print_test("Content Item Created", "FAIL", "No content items found")
                    self.errors.append("Content item not created")
                    
            else:
                self.print_test("Select Opportunity API", "FAIL", f"Response: {data}")
                self.errors.append("Opportunity selection failed")
                
        except Exception as e:
            self.print_test("Select Opportunity API", "FAIL", f"Error: {str(e)}")
            self.errors.append(f"Opportunity selection error: {str(e)}")

    def test_ui_pages(self):
        """Test 7: UI Pages"""
        self.print_header("UI Pages Tests")
        
        pages = [
            ("/", "Dashboard"),
            ("/trends", "Trends"),
            ("/opportunities", "Opportunities"),
        ]
        
        for url, name in pages:
            try:
                response = self.session.get(f"{self.base_url}{url}", timeout=10)
                content = response.text
                
                # Check for basic HTML structure
                if "<html" in content and "</html>" in content:
                    self.print_test(f"{name} Page HTML", "PASS", "Valid HTML structure")
                else:
                    self.print_test(f"{name} Page HTML", "FAIL", "Invalid HTML structure")
                    self.errors.append(f"{name} page has invalid HTML")
                    
                # Check for Bootstrap CSS
                if "bootstrap" in content:
                    self.print_test(f"{name} Page CSS", "PASS", "Bootstrap CSS loaded")
                else:
                    self.print_test(f"{name} Page CSS", "WARN", "Bootstrap CSS not detected")
                    
                # Check for JavaScript
                if "<script" in content:
                    self.print_test(f"{name} Page JS", "PASS", "JavaScript included")
                else:
                    self.print_test(f"{name} Page JS", "WARN", "No JavaScript detected")
                    
            except Exception as e:
                self.print_test(f"{name} Page", "FAIL", f"Error: {str(e)}")
                self.errors.append(f"{name} page error: {str(e)}")

    def test_performance(self):
        """Test 8: Performance"""
        self.print_header("Performance Tests")
        
        # Test response times
        endpoints = [
            ("/", "Dashboard"),
            ("/api/dashboard-stats", "Dashboard API"),
            ("/api/trends", "Trends API"),
        ]
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response_time < 1000:  # Less than 1 second
                    self.print_test(f"{name} Response Time", "PASS", f"{response_time:.0f}ms")
                elif response_time < 3000:  # Less than 3 seconds
                    self.print_test(f"{name} Response Time", "WARN", f"{response_time:.0f}ms (slow)")
                else:
                    self.print_test(f"{name} Response Time", "FAIL", f"{response_time:.0f}ms (too slow)")
                    self.errors.append(f"{name} response too slow: {response_time:.0f}ms")
                    
            except Exception as e:
                self.print_test(f"{name} Response Time", "FAIL", f"Error: {str(e)}")

    def test_data_integrity(self):
        """Test 9: Data Integrity"""
        self.print_header("Data Integrity Tests")
        
        try:
            # Test dashboard stats
            response = self.session.get(f"{self.base_url}/api/dashboard-stats")
            data = response.json()
            
            stats = data.get('today_stats', {})
            
            # Check if numbers make sense
            trends_count = stats.get('trends_collected', 0)
            opportunities_count = stats.get('opportunities_generated', 0)
            
            if trends_count >= 0:
                self.print_test("Trends Count Valid", "PASS", f"Count: {trends_count}")
            else:
                self.print_test("Trends Count Valid", "FAIL", f"Invalid count: {trends_count}")
                
            if opportunities_count >= 0:
                self.print_test("Opportunities Count Valid", "PASS", f"Count: {opportunities_count}")
            else:
                self.print_test("Opportunities Count Valid", "FAIL", f"Invalid count: {opportunities_count}")
                
            # Test data relationships
            if opportunities_count > 0 and trends_count == 0:
                self.print_test("Data Relationship", "WARN", "Opportunities exist without trends")
            else:
                self.print_test("Data Relationship", "PASS", "Data relationships are consistent")
                
        except Exception as e:
            self.print_test("Data Integrity", "FAIL", f"Error: {str(e)}")
            self.errors.append(f"Data integrity error: {str(e)}")

    def test_error_handling(self):
        """Test 10: Error Handling"""
        self.print_header("Error Handling Tests")
        
        # Test invalid endpoints
        try:
            response = self.session.get(f"{self.base_url}/api/invalid-endpoint")
            if response.status_code == 404:
                self.print_test("404 Error Handling", "PASS", "Returns 404 for invalid endpoints")
            else:
                self.print_test("404 Error Handling", "WARN", f"Status: {response.status_code}")
                
        except Exception as e:
            self.print_test("404 Error Handling", "FAIL", f"Error: {str(e)}")
            
        # Test invalid trend analysis
        try:
            response = self.session.post(f"{self.base_url}/api/analyze-trend/invalid-id")
            if response.status_code == 404:
                self.print_test("Invalid Trend ID", "PASS", "Returns 404 for invalid trend ID")
            else:
                self.print_test("Invalid Trend ID", "WARN", f"Status: {response.status_code}")
                
        except Exception as e:
            self.print_test("Invalid Trend ID", "FAIL", f"Error: {str(e)}")

    def run_full_test_suite(self):
        """Run all tests"""
        print(f"{Colors.BOLD}{Colors.PURPLE}")
        print("🚀 AI Content Factory - Full System Test")
        print("=" * 60)
        print(f"{Colors.END}")
        
        start_time = time.time()
        
        # Run tests in sequence
        if not self.test_server_connection():
            print(f"\n{Colors.RED}❌ Server connection failed. Cannot continue tests.{Colors.END}")
            return self.generate_report()
            
        self.test_database_structure()
        self.test_api_endpoints()
        
        # Functional tests
        trends = self.test_trend_collection()
        opportunities = self.test_trend_analysis(trends)
        self.test_opportunity_selection(opportunities)
        
        # UI and performance tests
        self.test_ui_pages()
        self.test_performance()
        self.test_data_integrity()
        self.test_error_handling()
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        return self.generate_report(test_duration)

    def generate_report(self, duration: float = 0):
        """Generate test report"""
        self.print_header("Test Report Summary")
        
        pass_count = len([r for r in self.test_results if r['status'] == 'PASS'])
        fail_count = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warn_count = len([r for r in self.test_results if r['status'] == 'WARN'])
        skip_count = len([r for r in self.test_results if r['status'] == 'SKIP'])
        total_count = len(self.test_results)
        
        print(f"📊 Test Results:")
        print(f"   ✅ Passed: {Colors.GREEN}{pass_count}{Colors.END}")
        print(f"   ❌ Failed: {Colors.RED}{fail_count}{Colors.END}")
        print(f"   ⚠️  Warnings: {Colors.YELLOW}{warn_count}{Colors.END}")
        print(f"   ⏭️  Skipped: {Colors.BLUE}{skip_count}{Colors.END}")
        print(f"   📈 Total: {total_count}")
        
        if duration > 0:
            print(f"   ⏱️  Duration: {duration:.2f} seconds")
        
        success_rate = (pass_count / total_count * 100) if total_count > 0 else 0
        print(f"   🎯 Success Rate: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n{Colors.RED}🚨 Critical Issues Found:{Colors.END}")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
                
        # Overall assessment
        if fail_count == 0:
            if warn_count == 0:
                print(f"\n{Colors.GREEN}🎉 All tests passed! System is working perfectly.{Colors.END}")
            else:
                print(f"\n{Colors.YELLOW}✅ System is working with minor issues.{Colors.END}")
        else:
            print(f"\n{Colors.RED}⚠️  System has critical issues that need to be fixed.{Colors.END}")
            
        # Save report to file
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'summary': {
                'total': total_count,
                'passed': pass_count,
                'failed': fail_count,
                'warnings': warn_count,
                'skipped': skip_count,
                'success_rate': success_rate
            },
            'tests': self.test_results,
            'errors': self.errors
        }
        
        with open('test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: test_report.json")
        
        return report_data

def main():
    """Main function to run tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Content Factory System Tests')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL of the application')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    
    args = parser.parse_args()
    
    tester = SystemTester(args.url)
    
    if args.quick:
        # Quick tests only
        tester.test_server_connection()
        tester.test_api_endpoints()
    else:
        # Full test suite
        tester.run_full_test_suite()

if __name__ == "__main__":
    main()