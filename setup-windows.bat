@echo off
chcp 65001 >nul
echo 🚀 AI Content Factory System Setup for Windows
echo ================================================
echo.

REM ตรวจสอบว่าอยู่ในโฟลเดอร์ที่ถูกต้อง
if not exist "docker-compose.yml" (
    echo ❌ ไม่พบไฟล์ docker-compose.yml
    echo กรุณาเข้าไปในโฟลเดอร์ ai-content-factory ก่อน
    pause
    exit /b 1
)

echo Phase 1: Setup Environment Variables
echo ------------------------------------

REM สร้าง .env file ถ้ายังไม่มี
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo ✅ สร้างไฟล์ .env จาก .env.example แล้ว
    ) else (
        echo สร้างไฟล์ .env...
        echo # AI Content Factory Environment Variables > .env
        echo # Database >> .env
        echo POSTGRES_DB=content_factory >> .env
        echo POSTGRES_USER=admin >> .env
        echo POSTGRES_PASSWORD=password123 >> .env
        echo DATABASE_URL=postgresql://admin:password123@localhost:5432/content_factory >> .env
        echo. >> .env
        echo # API Keys >> .env
        echo GROQ_API_KEY=your_groq_api_key_here >> .env
        echo OPENAI_API_KEY=your_openai_api_key_here >> .env
        echo YOUTUBE_API_KEY=your_youtube_api_key_here >> .env
        echo. >> .env
        echo # N8N Settings >> .env
        echo N8N_PASSWORD=admin123 >> .env
        echo ✅ สร้างไฟล์ .env แล้ว
    )
) else (
    echo ✅ ไฟล์ .env มีอยู่แล้ว
)

echo.
echo Phase 2: Start Database
echo -----------------------

echo เริ่มต้น PostgreSQL Database...
docker-compose up -d postgres

echo รอ Database เริ่มต้น (10 วินาที)...
timeout /t 10 /nobreak >nul

echo.
echo Phase 3: Run Database Migration
echo --------------------------------

echo เข้าไปในโฟลเดอร์ database...
cd database

REM ตรวจสอบว่ามีไฟล์ migrate.py หรือไม่
if exist "migrate.py" (
    echo รัน Database Migration...
    python migrate.py
) else (
    echo สร้างตารางฐานข้อมูล...
    if exist "migrations\001_create_trends_table.sql" (
        echo กำลังสร้างตาราง trends...
        docker exec -i ai-content-factory_postgres_1 psql -U admin -d content_factory < migrations\001_create_trends_table.sql
    )
    if exist "migrations\002_create_opportunities_table.sql" (
        echo กำลังสร้างตาราง opportunities...
        docker exec -i ai-content-factory_postgres_1 psql -U admin -d content_factory < migrations\002_create_opportunities_table.sql
    )
)

cd ..

echo.
echo Phase 4: Start Core Services
echo -----------------------------

echo เริ่มต้น Trend Monitor Service...
docker-compose up -d trend-monitor

echo เริ่มต้น Content Engine Service...
docker-compose up -d content-engine

echo.
echo Phase 5: Start Web Dashboard
echo -----------------------------

echo เริ่มต้น Web Interface...
if exist "main.py" (
    echo รัน Flask Application...
    start /b python main.py
) else if exist "app.py" (
    echo รัน Flask Application...
    start /b python app.py
)

echo.
echo 🎉 Setup เสร็จสิ้น!
echo =================
echo.
echo ✅ Database: http://localhost:5432
echo ✅ Web Dashboard: http://localhost:5000
echo ✅ N8N Workflow: http://localhost:5678
echo.
echo สำหรับดูสถานะ services:
echo docker-compose ps
echo.
echo สำหรับดู logs:
echo docker-compose logs [service-name]
echo.
pause