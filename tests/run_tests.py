#!/usr/bin/env python3
"""
AI Content Factory Test Runner
Comprehensive testing and integration validation
"""

import os
import sys
import json
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """Orchestrates all testing activities"""
    
    def __init__(self, verbose=False, generate_report=True):
        self.verbose = verbose
        self.generate_report = generate_report
        self.test_results = {}
        self.start_time = time.time()
        
    def run_all_tests(self):
        """Run complete test suite"""
        
        print("🚀 Starting AI Content Factory Test Suite")
        print("=" * 60)
        
        test_suites = [
            ("Unit Tests", self.run_unit_tests),
            ("API Integration Tests", self.run_api_tests),
            ("Database Tests", self.run_database_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Security Tests", self.run_security_tests),
            ("End-to-End Tests", self.run_e2e_tests)
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n📋 Running {suite_name}...")
            result = test_func()
            self.test_results[suite_name] = result
            
            if result['success']:
                print(f"✅ {suite_name} - PASSED ({result['duration']:.2f}s)")
            else:
                print(f"❌ {suite_name} - FAILED ({result['duration']:.2f}s)")
                if self.verbose:
                    print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Generate comprehensive report
        if self.generate_report:
            self.generate_test_report()
        
        # Print summary
        self.print_test_summary()
        
        return self.get_overall_success()
    
    def run_unit_tests(self):
        """Run unit tests"""
        start_time = time.time()
        
        try:
            # Run pytest with coverage
            cmd = [
                'python', '-m', 'pytest',
                'tests/test_core_functions.py',
                '-v',
                '--tb=short',
                '--cov=content_engine',
                '--cov=trend_monitor',
                '--cov=database',
                '--cov-report=json',
                '--cov-report=term-missing'
            ]
            
            if not self.verbose:
                cmd.append('-q')
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            return {
                'success': result.returncode == 0,
                'duration': time.time() - start_time,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'exit_code': result.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def run_api_tests(self):
        """Run API integration tests"""
        start_time = time.time()
        
        try:
            cmd = [
                'python', '-m', 'pytest',
                'tests/test_api_integration.py',
                '-v',
                '--tb=short'
            ]
            
            if not self.verbose:
                cmd.append('-q')
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            return {
                'success': result.returncode == 0,
                'duration': time.time() - start_time,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'exit_code': result.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def run_database_tests(self):
        """Run database-specific tests"""
        start_time = time.time()
        
        try:
            # Test database connectivity and basic operations
            from database.models.base import init_db, get_db_session
            from database.repositories.trend_repository import TrendRepository
            
            # Initialize test database
            init_db()
            
            # Test basic repository operations
            repo = TrendRepository()
            
            # Test creating and retrieving data
            test_trend = {
                'source': 'test',
                'topic': 'Database Test Trend',
                'keywords': ['test', 'database'],
                'popularity_score': 5.0,
                'growth_rate': 10.0,
                'category': 'test',
                'region': 'test'
            }
            
            created_trend = repo.create_trend(test_trend)
            assert created_trend is not None
            
            retrieved_trends = repo.get_recent_trends(limit=1)
            assert len(retrieved_trends) > 0
            
            return {
                'success': True,
                'duration': time.time() - start_time,
                'tests_completed': ['connectivity', 'create', 'retrieve']
            }
            
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def run_performance_tests(self):
        """Run performance tests"""
        start_time = time.time()
        
        try:
            from tests.test_api_integration import run_stress_test
            from app import app
            
            # Create test client
            with app.test_client() as client:
                # Run stress test for 10 seconds
                stress_results = run_stress_test(client, duration_seconds=10)
                
                # Check performance criteria
                min_requests_per_second = 5  # Minimum 5 requests/second
                min_success_rate = 0.95      # Minimum 95% success rate
                
                success = (
                    stress_results['requests_per_second'] >= min_requests_per_second and
                    stress_results['success_rate'] >= min_success_rate
                )
                
                return {
                    'success': success,
                    'duration': time.time() - start_time,
                    'metrics': stress_results,
                    'criteria': {
                        'min_rps': min_requests_per_second,
                        'min_success_rate': min_success_rate
                    }
                }
                
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def run_security_tests(self):
        """Run security tests"""
        start_time = time.time()
        
        try:
            from app import app
            
            security_tests = []
            
            with app.test_client() as client:
                # Test SQL injection prevention
                sql_injection_payload = "'; DROP TABLE trends; --"
                response = client.get(f'/api/trends?category={sql_injection_payload}')
                
                sql_test_passed = response.status_code in [200, 400, 422]
                security_tests.append(('SQL Injection Prevention', sql_test_passed))
                
                # Test XSS prevention
                xss_payload = "<script>alert('xss')</script>"
                response = client.post('/api/generate-content', 
                                     json={'opportunity_ids': [xss_payload]})
                
                xss_test_passed = response.status_code in [400, 422, 500]
                if response.status_code == 200:
                    response_text = response.get_data(as_text=True)
                    xss_test_passed = '<script>' not in response_text
                
                security_tests.append(('XSS Prevention', xss_test_passed))
                
                # Test input validation
                long_input = 'x' * 10000
                response = client.get(f'/api/trends?category={long_input}')
                
                input_validation_passed = response.status_code in [200, 400, 422]
                security_tests.append(('Input Validation', input_validation_passed))
            
            overall_success = all(test_passed for _, test_passed in security_tests)
            
            return {
                'success': overall_success,
                'duration': time.time() - start_time,
                'tests': security_tests,
                'passed': sum(1 for _, passed in security_tests if passed),
                'total': len(security_tests)
            }
            
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def run_e2e_tests(self):
        """Run end-to-end tests"""
        start_time = time.time()
        
        try:
            from app import app
            from unittest.mock import patch
            
            with app.test_client() as client:
                # Mock external services
                with patch('trend_monitor.services.trend_collector.TrendCollector.collect_all_trends') as mock_collect:
                    mock_collect.return_value = [
                        {
                            'source': 'test',
                            'topic': 'E2E Test Trend',
                            'keywords': ['e2e', 'test'],
                            'popularity_score': 8.0,
                            'growth_rate': 15.0,
                            'category': 'test'
                        }
                    ]
                    
                    # Test complete workflow
                    workflow_steps = []
                    
                    # Step 1: Collect trends
                    response = client.post('/api/collect-trends')
                    step1_success = response.status_code == 200
                    workflow_steps.append(('Collect Trends', step1_success))
                    
                    if step1_success:
                        # Step 2: Get trends
                        response = client.get('/api/trends?limit=5')
                        step2_success = response.status_code == 200
                        workflow_steps.append(('Get Trends', step2_success))
                        
                        if step2_success:
                            # Step 3: Analyze opportunities
                            with patch('content_engine.services.trend_analyzer.TrendAnalyzer.analyze_trend_potential'):
                                response = client.post('/api/analyze-opportunities')
                                step3_success = response.status_code == 200
                                workflow_steps.append(('Analyze Opportunities', step3_success))
                    
                    # Step 4: Check system health
                    response = client.get('/api/stats')
                    step4_success = response.status_code == 200
                    workflow_steps.append(('System Health Check', step4_success))
            
            overall_success = all(success for _, success in workflow_steps)
            
            return {
                'success': overall_success,
                'duration': time.time() - start_time,
                'workflow_steps': workflow_steps,
                'completed_steps': sum(1 for _, success in workflow_steps if success),
                'total_steps': len(workflow_steps)
            }
            
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        
        report_dir = project_root / 'test_reports'
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'test_report_{timestamp}.json'
        
        # Prepare report data
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'duration': time.time() - self.start_time,
            'overall_success': self.get_overall_success(),
            'test_results': self.test_results,
            'summary': self.get_test_summary(),
            'environment': self.get_environment_info(),
            'coverage': self.get_coverage_info()
        }
        
        # Write JSON report
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Generate HTML report
        html_report_file = report_dir / f'test_report_{timestamp}.html'
        self.generate_html_report(report_data, html_report_file)
        
        print(f"\n📊 Test reports generated:")
        print(f"   JSON: {report_file}")
        print(f"   HTML: {html_report_file}")
    
    def generate_html_report(self, report_data, output_file):
        """Generate HTML test report"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Factory - Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        
        .header .subtitle {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .summary-card .label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .info {{ color: #17a2b8; }}
        
        .test-results {{
            padding: 30px;
        }}
        
        .test-suite {{
            margin-bottom: 30px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .test-suite-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .test-suite-title {{
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .test-suite-status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .status-passed {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .test-suite-content {{
            padding: 20px;
        }}
        
        .test-metric {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .test-metric:last-child {{
            border-bottom: none;
        }}
        
        .error-details {{
            background: #f8f9fa;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }}
        
        .error-details pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .environment-info {{
            background: #f8f9fa;
            padding: 30px;
            border-top: 1px solid #e9ecef;
        }}
        
        .environment-info h3 {{
            margin-top: 0;
        }}
        
        .env-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .env-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .progress-bar {{
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-fill {{
            background: linear-gradient(90deg, #28a745, #20c997);
            height: 100%;
            transition: width 0.3s ease;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Content Factory</h1>
            <div class="subtitle">Test Report - {report_data['timestamp']}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="value {'success' if report_data['overall_success'] else 'failure'}">
                    {'✅ PASSED' if report_data['overall_success'] else '❌ FAILED'}
                </div>
                <div class="label">Overall Status</div>
            </div>
            
            <div class="summary-card">
                <div class="value info">{report_data['duration']:.1f}s</div>
                <div class="label">Total Duration</div>
            </div>
            
            <div class="summary-card">
                <div class="value success">{len([r for r in report_data['test_results'].values() if r.get('success', False)])}</div>
                <div class="label">Tests Passed</div>
            </div>
            
            <div class="summary-card">
                <div class="value failure">{len([r for r in report_data['test_results'].values() if not r.get('success', True)])}</div>
                <div class="label">Tests Failed</div>
            </div>
        </div>
        
        <div class="test-results">
            <h2>Test Results</h2>
"""
        
        # Add test suite results
        for suite_name, result in report_data['test_results'].items():
            success = result.get('success', False)
            duration = result.get('duration', 0)
            
            html_content += f"""
            <div class="test-suite">
                <div class="test-suite-header">
                    <div class="test-suite-title">{suite_name}</div>
                    <div class="test-suite-status {'status-passed' if success else 'status-failed'}">
                        {'PASSED' if success else 'FAILED'}
                    </div>
                </div>
                <div class="test-suite-content">
                    <div class="test-metric">
                        <span>Duration:</span>
                        <span>{duration:.2f} seconds</span>
                    </div>
                    <div class="test-metric">
                        <span>Exit Code:</span>
                        <span>{result.get('exit_code', 'N/A')}</span>
                    </div>
"""
            
            # Add specific metrics for different test types
            if 'metrics' in result:
                metrics = result['metrics']
                html_content += f"""
                    <div class="test-metric">
                        <span>Requests/Second:</span>
                        <span>{metrics.get('requests_per_second', 0):.1f}</span>
                    </div>
                    <div class="test-metric">
                        <span>Success Rate:</span>
                        <span>{metrics.get('success_rate', 0):.1%}</span>
                    </div>
"""
            
            if 'tests' in result:
                passed_tests = result.get('passed', 0)
                total_tests = result.get('total', 0)
                if total_tests > 0:
                    html_content += f"""
                    <div class="test-metric">
                        <span>Tests Passed:</span>
                        <span>{passed_tests}/{total_tests}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {(passed_tests/total_tests)*100}%"></div>
                    </div>
"""
            
            # Add error details if test failed
            if not success and 'error' in result:
                html_content += f"""
                    <div class="error-details">
                        <strong>Error Details:</strong>
                        <pre>{result['error']}</pre>
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        # Add environment information
        env_info = report_data.get('environment', {})
        html_content += f"""
        </div>
        
        <div class="environment-info">
            <h3>Environment Information</h3>
            <div class="env-grid">
                <div class="env-item">
                    <span>Python Version:</span>
                    <span>{env_info.get('python_version', 'Unknown')}</span>
                </div>
                <div class="env-item">
                    <span>Platform:</span>
                    <span>{env_info.get('platform', 'Unknown')}</span>
                </div>
                <div class="env-item">
                    <span>CPU Count:</span>
                    <span>{env_info.get('cpu_count', 'Unknown')}</span>
                </div>
                <div class="env-item">
                    <span>Memory (GB):</span>
                    <span>{env_info.get('memory_gb', 'Unknown')}</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Generated by AI Content Factory Test Runner
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def get_environment_info(self):
        """Get environment information"""
        import platform
        import psutil
        
        try:
            return {
                'python_version': platform.python_version(),
                'platform': platform.platform(),
                'cpu_count': psutil.cpu_count(),
                'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_free_gb': round(psutil.disk_usage('.').free / (1024**3), 2)
            }
        except:
            return {
                'python_version': platform.python_version(),
                'platform': platform.platform(),
                'cpu_count': 'Unknown',
                'memory_gb': 'Unknown'
            }
    
    def get_coverage_info(self):
        """Get test coverage information"""
        coverage_file = project_root / 'coverage.json'
        
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                total_statements = coverage_data['totals']['num_statements']
                covered_statements = coverage_data['totals']['covered_lines']
                coverage_percent = coverage_data['totals']['percent_covered']
                
                return {
                    'total_statements': total_statements,
                    'covered_statements': covered_statements,
                    'coverage_percent': coverage_percent,
                    'missing_lines': coverage_data['totals']['missing_lines']
                }
            except:
                pass
        
        return None
    
    def print_test_summary(self):
        """Print test summary to console"""
        total_duration = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        passed_count = sum(1 for result in self.test_results.values() if result.get('success', False))
        total_count = len(self.test_results)
        
        print(f"📊 Overall Result: {'✅ PASSED' if self.get_overall_success() else '❌ FAILED'}")
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print(f"✅ Tests Passed: {passed_count}/{total_count}")
        print(f"❌ Tests Failed: {total_count - passed_count}/{total_count}")
        
        if not self.get_overall_success():
            print("\n❌ Failed Test Suites:")
            for suite_name, result in self.test_results.items():
                if not result.get('success', False):
                    print(f"   • {suite_name}: {result.get('error', 'Unknown error')}")
        
        print("=" * 60)
    
    def get_overall_success(self):
        """Check if all tests passed"""
        return all(result.get('success', False) for result in self.test_results.values())
    
    def get_test_summary(self):
        """Get test summary statistics"""
        passed = sum(1 for result in self.test_results.values() if result.get('success', False))
        total = len(self.test_results)
        
        return {
            'total_suites': total,
            'passed_suites': passed,
            'failed_suites': total - passed,
            'success_rate': passed / total if total > 0 else 0,
            'total_duration': time.time() - self.start_time
        }

class TestValidator:
    """Validates system before running tests"""
    
    @staticmethod
    def validate_environment():
        """Validate test environment"""
        print("🔍 Validating test environment...")
        
        issues = []
        
        # Check Python version
        import sys
        if sys.version_info < (3, 8):
            issues.append("Python 3.8+ is required")
        
        # Check required packages
        required_packages = [
            'pytest', 'flask', 'sqlalchemy', 'psutil'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                issues.append(f"Missing required package: {package}")
        
        # Check database accessibility
        try:
            from database.models.base import get_db_session
            session = get_db_session()
            session.close()
        except Exception as e:
            issues.append(f"Database connection issue: {e}")
        
        # Check file permissions
        test_dir = Path(__file__).parent
        if not os.access(test_dir, os.W_OK):
            issues.append("No write permission in test directory")
        
        if issues:
            print("❌ Environment validation failed:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        else:
            print("✅ Environment validation passed")
            return True
    
    @staticmethod
    def cleanup_test_artifacts():
        """Clean up test artifacts from previous runs"""
        print("🧹 Cleaning up test artifacts...")
        
        # Remove old test databases
        test_files = [
            '*.db',
            'test_*.sqlite',
            'coverage.json',
            '.coverage'
        ]
        
        for pattern in test_files:
            for file_path in Path('.').glob(pattern):
                try:
                    file_path.unlink()
                    print(f"   Removed: {file_path}")
                except Exception as e:
                    print(f"   Warning: Could not remove {file_path}: {e}")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='AI Content Factory Test Runner')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose output')
    parser.add_argument('--no-report', action='store_true',
                      help='Skip generating test reports')
    parser.add_argument('--suite', choices=['unit', 'api', 'database', 'performance', 'security', 'e2e'],
                      help='Run specific test suite only')
    parser.add_argument('--validate-only', action='store_true',
                      help='Only validate environment, don\'t run tests')
    parser.add_argument('--cleanup', action='store_true',
                      help='Clean up test artifacts and exit')
    
    args = parser.parse_args()
    
    # Handle cleanup
    if args.cleanup:
        TestValidator.cleanup_test_artifacts()
        return 0
    
    # Validate environment
    if not TestValidator.validate_environment():
        return 1
    
    if args.validate_only:
        return 0
    
    # Clean up before running tests
    TestValidator.cleanup_test_artifacts()
    
    # Initialize test runner
    test_runner = TestRunner(
        verbose=args.verbose,
        generate_report=not args.no_report
    )
    
    # Run specific suite or all tests
    if args.suite:
        suite_methods = {
            'unit': test_runner.run_unit_tests,
            'api': test_runner.run_api_tests,
            'database': test_runner.run_database_tests,
            'performance': test_runner.run_performance_tests,
            'security': test_runner.run_security_tests,
            'e2e': test_runner.run_e2e_tests
        }
        
        print(f"🚀 Running {args.suite} tests only...")
        result = suite_methods[args.suite]()
        
        if result['success']:
            print(f"✅ {args.suite} tests PASSED")
            return 0
        else:
            print(f"❌ {args.suite} tests FAILED: {result.get('error', 'Unknown error')}")
            return 1
    else:
        # Run all tests
        success = test_runner.run_all_tests()
        return 0 if success else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)