@echo off
chcp 65001 >nul
echo 🚀 AI Content Factory - Windows Setup
echo ======================================
echo.

REM สร้าง .env file (แทน cp command)
echo สร้างไฟล์ .env...
(
echo # AI Content Factory Environment Variables
echo DATABASE_URL=sqlite:///content_factory.db
echo.
echo # API Keys (กรุณาใส่ API Key จริง)
echo GROQ_API_KEY=your_groq_api_key_here
echo OPENAI_API_KEY=your_openai_api_key_here
echo YOUTUBE_API_KEY=your_youtube_api_key_here
echo.
echo # Flask Settings
echo FLASK_ENV=development
echo FLASK_DEBUG=1
echo FLASK_HOST=127.0.0.1
echo FLASK_PORT=5000
) > .env
echo ✅ สร้างไฟล์ .env แล้ว

echo.
echo สร้างไฟล์ requirements.txt...
(
echo flask==3.1.2
echo requests==2.31.0
echo python-dotenv==1.0.0
echo beautifulsoup4==4.12.2
echo pandas==2.1.4
echo matplotlib==3.8.2
echo plotly==5.17.0
echo schedule==1.2.0
) > requirements.txt
echo ✅ สร้างไฟล์ requirements.txt แล้ว

echo.
echo กำลังติดตั้ง Python packages...
pip install -r requirements.txt

echo.
echo 🎉 Setup เสร็จสิ้น!
echo.
echo ขั้นตอนถัดไป:
echo 1. วางไฟล์ create_database.py และ simple_app.py ในโฟลเดอร์นี้
echo 2. รัน: python create_database.py
echo 3. รัน: python simple_app.py
echo 4. เปิดเบราว์เซอร์ไปที่: http://localhost:5000
echo.
pause