@echo off
REM AI Content Engine Launcher with Thai Support
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo 🎬 AI Content Generation Engine - Thai Support
echo ================================================
echo 🔧 ตั้งค่าการแสดงผลภาษาไทย...
echo.

REM Start the application
python production_content_engine.py

pause
