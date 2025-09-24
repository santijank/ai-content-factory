# ทดสอบการติดตั้งพื้นฐาน - ไม่ใช้ SQLAlchemy
import os
import sys
import sqlite3
from dotenv import load_dotenv

def test_environment():
    """ทดสอบ environment setup"""
    print("🧪 Testing Environment Setup...")
    
    # Load environment variables
    try:
        load_dotenv()
        print("✅ Environment variables loaded")
    except Exception as e:
        print(f"⚠️ Environment loading issue: {e}")
    
    # Test Python version
    print(f"✅ Python Version: {sys.version.split()[0]}")
    
    # Test environment variables
    db_path = os.getenv('DB_PATH', './database/ai_content.db')
    print(f"✅ Database Path: {db_path}")
    
    # Test essential imports
    essential_packages = [
        ('sqlite3', 'SQLite3 (built-in)'),
        ('json', 'JSON (built-in)'),
        ('uuid', 'UUID (built-in)'),
        ('datetime', 'DateTime (built-in)'),
        ('requests', 'Requests'),
    ]
    
    all_good = True
    for package, name in essential_packages:
        try:
            module = __import__(package)
            if hasattr(module, '__version__'):
                version = module.__version__
            else:
                version = 'Built-in'
            print(f"✅ {name}: {version}")
        except ImportError as e:
            print(f"❌ {name} not found: {e}")
            if package not in ['sqlite3', 'json', 'uuid', 'datetime']:
                all_good = False
    
    return all_good

def test_sqlite():
    """ทดสอบ SQLite database"""
    print("\n🗄️ Testing SQLite Database...")
    
    try:
        # สร้างโฟลเดอร์ database
        os.makedirs('./database', exist_ok=True)
        print("✅ Database folder created")
        
        # ทดสอบ SQLite connection
        test_db_path = './database/test_connection.db'
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # สร้าง test table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                name TEXT,
                created_at TEXT
            )
        ''')
        
        # Insert test data
        from datetime import datetime
        cursor.execute('''
            INSERT INTO test (name, created_at) 
            VALUES (?, ?)
        ''', ('Test Entry', datetime.utcnow().isoformat()))
        
        # Query test data
        cursor.execute('SELECT * FROM test')
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if result:
            print("✅ SQLite read/write test successful!")
            print(f"✅ Test data: {result}")
        
        # ลบ test database
        os.remove(test_db_path)
        print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite test failed: {e}")
        return False

def test_simple_database():
    """ทดสอบ simple database models"""
    print("\n🔧 Testing Simple Database Models...")
    
    try:
        # ลอง import simple database models
        sys.path.append('.')
        from database.models_simple import test_database_simple
        
        # รัน test
        if test_database_simple():
            print("✅ Simple database models work perfectly!")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Simple database test failed: {e}")
        print("💡 Make sure you created database/models_simple.py file")
        return False

def test_basic_functionality():
    """ทดสอบ functionality พื้นฐาน"""
    print("\n🔧 Testing Basic Functionality...")
    
    try:
        # ทดสอบ datetime
        from datetime import datetime
        now = datetime.utcnow()
        print(f"✅ DateTime: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ทดสอบ UUID
        import uuid
        test_uuid = str(uuid.uuid4())
        print(f"✅ UUID generation: {test_uuid[:8]}...")
        
        # ทดสอบ JSON
        import json
        test_data = {'test': 'data', 'number': 123}
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)
        print(f"✅ JSON handling: {parsed_data}")
        
        # ทดสอบ requests (ถ้ามี)
        try:
            import requests
            print(f"✅ Requests library: {requests.__version__}")
        except ImportError:
            print("⚠️ Requests library not installed (will install later)")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AI Content Factory - Simple Setup Test\n")
    
    # Run tests
    env_ok = test_environment()
    basic_ok = test_basic_functionality()
    sqlite_ok = test_sqlite()
    db_ok = test_simple_database()
    
    print("\n" + "="*50)
    if env_ok and basic_ok and sqlite_ok:
        print("🎉 Core tests passed! Basic setup working!")
        if db_ok:
            print("🎉 Database models working perfectly!")
        else:
            print("⚠️ Database models need to be created")
        
        print("🚀 Ready to start development.")
        print("\nNext steps:")
        print("1. Create database/models_simple.py (if not done)")
        print("2. Start building trend collector")
        print("3. Test with real data")
    else:
        print("⚠️ Some core tests failed. Please check the errors above.")
        print("💡 Focus on fixing basic imports first")
    
    print("="*50)