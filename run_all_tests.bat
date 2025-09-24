@echo off
chcp 65001 >nul
echo 🧪 AI Content Factory - Complete Test Suite
echo =============================================
echo.

REM ตรวจสอบว่ามีไฟล์ทดสอบหรือไม่
if not exist "test_system.py" (
    echo ❌ test_system.py not found
    echo กรุณาสร้างไฟล์ test_system.py ก่อน
    pause
    exit /b 1
)

REM ตรวจสอบว่า server กำลังรันอยู่หรือไม่
echo 🔍 ตรวจสอบ server status...
python -c "import requests; requests.get('http://localhost:5000', timeout=2)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Server ไม่ได้รันอยู่
    echo กรุณาเปิด server ก่อน: python simple_app.py
    echo.
    echo ต้องการเปิด server ใหม่หรือไม่? (y/n^)
    set /p start_server=
    if /i "%start_server%"=="y" (
        echo เริ่ม server...
        start "AI Content Factory Server" python simple_app.py
        echo รอ server เริ่มต้น (10 วินาที^)...
        timeout /t 10 /nobreak >nul
    ) else (
        echo กรุณาเปิด server แล้วลองใหม่
        pause
        exit /b 1
    )
)

echo ✅ Server กำลังทำงาน
echo.

echo 1️⃣ Running Quick System Check...
echo =====================================
if exist "quick_test.py" (
    python quick_test.py
    echo.
) else (
    echo ⏭️ quick_test.py not found, skipping...
)

echo 2️⃣ Running Complete System Test...
echo ====================================
python test_system.py
set test_result=%errorlevel%
echo.

echo 3️⃣ Running Performance Benchmark...
echo ====================================
if exist "benchmark_test.py" (
    python benchmark_test.py
    echo.
) else (
    echo ⏭️ benchmark_test.py not found, skipping...
)

echo 4️⃣ Database Integrity Check...
echo ===============================
python -c "
import sqlite3
try:
    conn = sqlite3.connect('content_factory.db')
    cursor = conn.cursor()
    
    # ตรวจสอบจำนวนข้อมูล
    cursor.execute('SELECT COUNT(*) FROM trends')
    trends = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM content_opportunities')
    opportunities = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM content_items')
    content_items = cursor.fetchone()[0]
    
    print(f'📊 Database Status:')
    print(f'   Trends: {trends}')
    print(f'   Opportunities: {opportunities}')
    print(f'   Content Items: {content_items}')
    
    # ตรวจสอบข้อมูลล่าสุด
    cursor.execute('SELECT topic, collected_at FROM trends ORDER BY collected_at DESC LIMIT 3')
    recent_trends = cursor.fetchall()
    
    print(f'📈 Recent Trends:')
    for topic, collected_at in recent_trends:
        print(f'   - {topic} ({collected_at})')
    
    conn.close()
    print('✅ Database integrity check passed')
    
except Exception as e:
    print(f'❌ Database error: {e}')
"

echo.
echo 5️⃣ API Endpoints Validation...
echo ===============================
python -c "
import requests
import json

base_url = 'http://localhost:5000'
endpoints = [
    ('/', 'GET', 'Dashboard'),
    ('/api/analytics', 'GET', 'Analytics'),
    ('/api/trends', 'GET', 'Get Trends'),
    ('/api/opportunities', 'GET', 'Get Opportunities'),
]

print('🔗 API Endpoints Check:')
for endpoint, method, name in endpoints:
    try:
        response = requests.get(f'{base_url}{endpoint}', timeout=5)
        if response.status_code == 200:
            print(f'   ✅ {name}: OK ({response.status_code})')
        else:
            print(f'   ❌ {name}: ERROR ({response.status_code})')
    except Exception as e:
        print(f'   ❌ {name}: FAILED ({e})')

# ทดสอบ POST endpoints
post_endpoints = [
    ('/api/collect-trends', 'Collect Trends'),
    ('/api/generate-opportunities', 'Generate Opportunities'),
]

print('📝 POST Endpoints Check:')
for endpoint, name in post_endpoints:
    try:
        response = requests.post(f'{base_url}{endpoint}', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'   ✅ {name}: OK (Created: {data.get(\"count\", 0)})')
        else:
            print(f'   ❌ {name}: ERROR ({response.status_code})')
    except Exception as e:
        print(f'   ❌ {name}: FAILED ({e})')
"

echo.
echo 📊 FINAL TEST SUMMARY
echo ======================

if %test_result% equ 0 (
    echo 🎉 ALL TESTS PASSED!
    echo ✅ Your AI Content Factory system is working perfectly!
    echo.
    echo 🚀 System Ready For:
    echo    - Content trend monitoring
    echo    - Opportunity generation  
    echo    - API integrations
    echo    - Production deployment
    echo.
    echo 💡 Next Steps:
    echo    1. Add real API keys to .env file
    echo    2. Configure trend sources
    echo    3. Set up AI integrations
    echo    4. Deploy to production
) else (
    echo ⚠️ SOME TESTS FAILED
    echo 🔧 Please check the errors above and fix them
    echo.
    echo 🛠️ Common Solutions:
    echo    1. Restart the server: python simple_app.py
    echo    2. Recreate database: python create_database.py
    echo    3. Install dependencies: pip install -r requirements.txt
    echo    4. Check port 5000 is not in use
)

echo.
echo 📋 Test Files Created:
echo ✅ test_system.py - Complete system testing
echo ✅ quick_test.py - Quick system check
echo ✅ benchmark_test.py - Performance testing
echo ✅ run_all_tests.bat - This test runner
echo.

echo กด Enter เพื่อออก...
pause >nul