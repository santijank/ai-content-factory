@echo off
chcp 65001 >nul
echo 🚀 AI Content Factory - Quick Start
echo ====================================
echo.

REM ตรวจสอบ Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python ยังไม่ติดตั้ง
    echo กรุณาติดตั้ง Python จาก: https://python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python ตรวจพบ
python --version

echo.
echo Step 1: ติดตั้ง Dependencies
echo ----------------------------
pip install flask requests python-dotenv beautifulsoup4 pandas matplotlib plotly schedule

echo.
echo Step 2: สร้าง Database
echo ----------------------
python create_database.py

echo.
echo Step 3: เริ่ม Web Application
echo -----------------------------
echo 🌟 กำลังเริ่ม AI Content Factory...
echo 📊 เปิดเบราว์เซอร์ไปที่: http://localhost:5000
echo.
echo กด Ctrl+C เพื่อหยุดเซิร์ฟเวอร์
echo.

python simple_app.py