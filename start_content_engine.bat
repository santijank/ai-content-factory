@echo off
title AI Content Engine - Thai Support
color 0A

echo ========================================
echo   AI CONTENT GENERATION ENGINE
echo   Thai Language Support Enabled
echo ========================================
echo.
echo Starting system...
echo.

REM Set UTF-8 encoding
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Start the engine
python ultimate_thai_content_engine.py

echo.
echo ========================================
echo   Thank you for using our system!
echo ========================================
pause
