# ทดสอบการติดตั้งพื้นฐาน
import os
import sys
from dotenv import load_dotenv

def test_environment():
    """ทดสอบ environment setup"""
    print("🧪 Testing Environment Setup...")
    
    # Load environment variables
    load_dotenv()
    
    # Test Python version
    print(f"✅ Python Version: {sys.version}")
    
    # Test environment variables
    db_path = os.getenv('DB_PATH', 'Not found')
    print(f"✅ Database Path: {db_path}")
    
    # Test imports
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask not found: {e}")
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"❌ SQLAlchemy not found: {e}")
    
    try:
        import requests
        print(f"✅ Requests: {requests.__version__}")
    except ImportError as e:
        print(f"❌ Requests not found: {e}")

def test_database():
    """ทดสอบ database connection"""
    print("\n🗄️ Testing Database Setup...")
    
    try:
        from database.models import create_tables, engine
        
        # สร้าง tables
        create_tables()
        
        # ทดสอบ connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful!")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_environment()
    test_database()
    print("\n🚀 Setup complete! Ready to start development.")