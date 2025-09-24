@echo off
echo ตรวจสอบการติดตั้ง Docker...
echo.

REM ตรวจสอบ Docker
docker --version
if %errorlevel% equ 0 (
    echo ✅ Docker ติดตั้งแล้ว
) else (
    echo ❌ Docker ยังไม่ติดตั้ง
    echo กรุณาติดตั้ง Docker Desktop for Windows จาก: https://docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo.
REM ตรวจสอบ Docker Compose
docker-compose --version
if %errorlevel% equ 0 (
    echo ✅ Docker Compose ติดตั้งแล้ว
) else (
    echo ❌ Docker Compose ยังไม่ติดตั้ง
)

echo.
echo ตรวจสอบ Docker service...
docker ps
if %errorlevel% equ 0 (
    echo ✅ Docker service ทำงานอยู่
) else (
    echo ❌ Docker service ยังไม่ทำงาน
    echo กรุณาเปิด Docker Desktop
)

pause