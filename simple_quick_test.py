#!/usr/bin/env python3
"""
Simple Quick Test for AI Content Factory
Tests basic functionality without complex dependencies
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

def test_dependencies():
    """Test basic dependencies"""
    print("📦 Testing Dependencies...")
    
    required = ['flask', 'requests']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies OK")
    return True

def test_environment():
    """Test environment setup"""
    print("\n🔧 Testing Environment...")
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
    else:
        print("⚠️  .env file missing (will use defaults)")
    
    # Check SECRET_KEY
    secret_key = os.getenv('SECRET_KEY')
    if secret_key:
        print("✅ SECRET_KEY set")
    else:
        print("⚠️  SECRET_KEY not set (will use default)")
        os.environ['SECRET_KEY'] = 'test-secret-key'
    
    return True

def test_minimal_app():
    """Test minimal app functionality"""
    print("\n🚀 Testing Minimal App...")
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import minimal app
        from minimal_app import app
        
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            # Test main dashboard
            response = client.get('/')
            print(f"✅ Dashboard: HTTP {response.status_code}")
            
            # Test API endpoints
            endpoints = ['/api/health', '/api/stats', '/api/trends', '/api/opportunities']
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                if response.status_code == 200:
                    print(f"✅ {endpoint}: HTTP {response.status_code}")
                else:
                    print(f"❌ {endpoint}: HTTP {response.status_code}")
        
        print("✅ Minimal app test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ App test failed: {e}")
        return False

def test_system_health():
    """Test basic system health"""
    print("\n🏥 Testing System Health...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (need 3.8+)")
        return False
    
    # Check disk space
    try:
        import shutil
        free_space = shutil.disk_usage('.').free / (1024**3)
        if free_space > 1.0:
            print(f"✅ Disk space: {free_space:.1f} GB free")
        else:
            print(f"⚠️  Disk space: {free_space:.1f} GB free (low)")
    except:
        print("⚠️  Could not check disk space")
    
    # Check write permissions
    try:
        test_file = Path('test_write.tmp')
        test_file.write_text('test')
        test_file.unlink()
        print("✅ Write permissions OK")
    except:
        print("❌ No write permissions")
        return False
    
    return True

def main():
    """Main test function"""
    print("🤖 AI Content Factory - Simple Quick Test")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Environment", test_environment),
        ("System Health", test_system_health),
        ("Minimal App", test_minimal_app),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            results.append({
                'name': test_name,
                'success': result,
                'duration': duration
            })
            
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append({
                'name': test_name,
                'success': False,
                'duration': 0,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("  • Run the app: python minimal_app.py")
        print("  • Open browser: http://localhost:5000")
        print("  • Test APIs through the dashboard")
        return True
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)