#!/usr/bin/env python3
"""
AI Content Factory - Problem Detection Script
ตรวจจับและแก้ไขปัญหาที่เกิดขึ้นบ่อย
"""

import os
import sys
import sqlite3
import requests
import json
import subprocess
import platform
from pathlib import Path

class ProblemDetector:
    def __init__(self):
        self.problems = []
        self.solutions = []
        
    def check_python_version(self):
        """ตรวจสอบ Python version"""
        print("🐍 Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            self.problems.append("Python version too old")
            self.solutions.append("Upgrade to Python 3.7 or newer")
            print(f"   ❌ Python {version.major}.{version.minor} (need 3.7+)")
            return False
        else:
            print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
            return True
    
    def check_virtual_environment(self):
        """ตรวจสอบ Virtual Environment"""
        print("\n📦 Checking Virtual Environment...")
        
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("   ✅ Virtual environment is active")
            return True
        else:
            print("   ⚠️  Virtual environment not detected")
            print("   💡 Consider using: python -m venv venv")
            return False
    
    def check_required_packages(self):
        """ตรวจสอบ Required packages"""
        print("\n📚 Checking Required Packages...")
        
        required_packages = [
            ('flask', 'Flask'),
            ('requests', 'requests'),
        ]
        
        missing_packages = []
        
        for package, install_name in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {install_name}")
            except ImportError:
                print(f"   ❌ {install_name} (missing)")
                missing_packages.append(install_name)
        
        if missing_packages:
            self.problems.append("Missing required packages")
            self.solutions.append(f"Run: pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def check_file_structure(self):
        """ตรวจสอบ File structure"""
        print("\n📁 Checking File Structure...")
        
        required_files = [
            'app.py',
            'templates/base.html',
            'templates/dashboard.html',
            'templates/trends.html',
            'templates/opportunities.html'
        ]
        
        missing_files = []
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} (missing)")
                missing_files.append(file_path)
        
        if missing_files:
            self.problems.append("Missing required files")
            self.solutions.append("Create missing files from the provided templates")
            return False
        
        return True
    
    def check_app_py_syntax(self):
        """ตรวจสอบ app.py syntax"""
        print("\n🔍 Checking app.py syntax...")
        
        if not os.path.exists('app.py'):
            print("   ❌ app.py not found")
            return False
        
        try:
            with open('app.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic syntax check
            compile(content, 'app.py', 'exec')
            print("   ✅ app.py syntax is valid")
            
            # Check for common imports
            if 'from flask import Flask' in content:
                print("   ✅ Flask import found")
            else:
                print("   ❌ Flask import missing")
                self.problems.append("Flask import missing in app.py")
            
            # Check for app creation
            if 'app = Flask(__name__)' in content:
                print("   ✅ Flask app creation found")
            else:
                print("   ❌ Flask app creation missing")
                self.problems.append("Flask app creation missing")
            
            return True
            
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            self.problems.append(f"Syntax error in app.py: {e}")
            self.solutions.append("Fix syntax errors in app.py")
            return False
        except Exception as e:
            print(f"   ❌ Error reading app.py: {e}")
            return False
    
    def check_database_permissions(self):
        """ตรวจสอบ Database permissions"""
        print("\n🗄️ Checking Database Permissions...")
        
        try:
            # Try to create a test database
            test_db = 'test_permissions.db'
            conn = sqlite3.connect(test_db)
            conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER)')
            conn.close()
            os.remove(test_db)
            print("   ✅ Database write permissions OK")
            return True
        except Exception as e:
            print(f"   ❌ Database permission error: {e}")
            self.problems.append("Cannot create database files")
            self.solutions.append("Check folder write permissions")
            return False
    
    def check_port_availability(self):
        """ตรวจสอบ Port 5000"""
        print("\n🌐 Checking Port 5000...")
        
        try:
            response = requests.get('http://localhost:5000', timeout=2)
            print("   ⚠️  Port 5000 is already in use")
            print("   💡 Another Flask app might be running")
            return False
        except requests.exceptions.ConnectionError:
            print("   ✅ Port 5000 is available")
            return True
        except Exception as e:
            print(f"   ❌ Error checking port: {e}")
            return False
    
    def check_template_syntax(self):
        """ตรวจสอบ Template syntax"""
        print("\n🎨 Checking Template Syntax...")
        
        templates = [
            'templates/base.html',
            'templates/dashboard.html',
            'templates/trends.html',
            'templates/opportunities.html'
        ]
        
        all_valid = True
        
        for template in templates:
            if os.path.exists(template):
                try:
                    with open(template, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Basic HTML structure check
                    if '<html' in content and '</html>' in content:
                        print(f"   ✅ {template} - Valid HTML structure")
                    else:
                        print(f"   ⚠️  {template} - Missing HTML structure")
                    
                    # Check for Jinja2 template inheritance
                    if template != 'templates/base.html':
                        if '{% extends' in content:
                            print(f"   ✅ {template} - Template inheritance OK")
                        else:
                            print(f"   ⚠️  {template} - No template inheritance")
                            
                except Exception as e:
                    print(f"   ❌ {template} - Error: {e}")
                    all_valid = False
            else:
                print(f"   ❌ {template} - File not found")
                all_valid = False
        
        return all_valid
    
    def check_common_errors(self):
        """ตรวจสอบ Common errors"""
        print("\n🔧 Checking Common Issues...")
        
        # Check if running from correct directory
        if os.path.exists('app.py'):
            print("   ✅ Running from correct directory")
        else:
            print("   ❌ Not in correct directory")
            print("   💡 Make sure you're in the web-dashboard folder")
            self.problems.append("Wrong working directory")
            self.solutions.append("cd to web-dashboard folder")
        
        # Check for __pycache__ conflicts
        if os.path.exists('__pycache__'):
            print("   ⚠️  __pycache__ folder exists")
            print("   💡 Consider deleting it if you have issues")
        else:
            print("   ✅ No __pycache__ conflicts")
        
        # Check OS-specific issues
        os_name = platform.system()
        print(f"   ℹ️  Operating System: {os_name}")
        
        if os_name == "Windows":
            print("   💡 Windows detected - use 'python' command")
        else:
            print("   💡 Unix-like OS - may use 'python3' command")
    
    def generate_fix_script(self):
        """สร้าง Fix script"""
        print("\n🛠️ Generating Fix Script...")
        
        fix_commands = []
        
        # Add solutions
        for solution in self.solutions:
            if solution.startswith("Run:"):
                fix_commands.append(solution[4:].strip())
        
        if fix_commands:
            fix_script = "#!/bin/bash\n# Auto-generated fix script\n\n"
            
            for cmd in fix_commands:
                fix_script += f"echo 'Running: {cmd}'\n"
                fix_script += f"{cmd}\n\n"
            
            fix_script += "echo 'Fix script completed!'\n"
            
            with open('fix_issues.sh', 'w') as f:
                f.write(fix_script)
            
            print("   ✅ Fix script saved as: fix_issues.sh")
            
            # Also create Windows batch file
            win_script = "@echo off\nREM Auto-generated fix script\n\n"
            for cmd in fix_commands:
                win_script += f"echo Running: {cmd}\n"
                win_script += f"{cmd}\n\n"
            win_script += "echo Fix script completed!\npause\n"
            
            with open('fix_issues.bat', 'w') as f:
                f.write(win_script)
            
            print("   ✅ Windows fix script saved as: fix_issues.bat")
        else:
            print("   ℹ️  No automated fixes available")
    
    def run_diagnosis(self):
        """รันการตรวจสอบทั้งหมด"""
        print("🔍 AI Content Factory - Problem Detection")
        print("=" * 50)
        
        checks = [
            self.check_python_version,
            self.check_virtual_environment,
            self.check_required_packages,
            self.check_file_structure,
            self.check_app_py_syntax,
            self.check_database_permissions,
            self.check_port_availability,
            self.check_template_syntax,
            self.check_common_errors
        ]
        
        passed = 0
        total = len(checks)
        
        for check in checks:
            if check():
                passed += 1
        
        print("\n" + "=" * 50)
        print("📊 DIAGNOSIS SUMMARY")
        print("=" * 50)
        
        print(f"✅ Passed: {passed}/{total}")
        
        if self.problems:
            print(f"❌ Problems found: {len(self.problems)}")
            print("\n🚨 PROBLEMS:")
            for i, problem in enumerate(self.problems, 1):
                print(f"   {i}. {problem}")
            
            print("\n💡 SOLUTIONS:")
            for i, solution in enumerate(self.solutions, 1):
                print(f"   {i}. {solution}")
        else:
            print("🎉 No problems detected!")
        
        self.generate_fix_script()
        
        if passed == total and not self.problems:
            print(f"\n✅ System looks good! Try running: python app.py")
        else:
            print(f"\n⚠️  Please fix the issues above before running the app")
        
        return passed == total and not self.problems

def main():
    detector = ProblemDetector()
    detector.run_diagnosis()

if __name__ == "__main__":
    main()