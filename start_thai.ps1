# AI Content Engine - Thai Support Launcher
# PowerShell รองรับภาษาไทยได้ดีกว่า CMD

Write-Host "🎬 AI Content Generation Engine - Thai Support" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray
Write-Host ""

# ตั้งค่า Environment Variables
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# ตรวจสอบ Python
Write-Host "🔍 ตรวจสอบ Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ พบ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ไม่พบ Python! กรุณาติดตั้ง Python ก่อน" -ForegroundColor Red
    Read-Host "กด Enter เพื่อปิด"
    exit
}

# ตรวจสอบไฟล์
$mainScript = "production_content_engine_thai.py"
if (-not (Test-Path $mainScript)) {
    Write-Host "❌ ไม่พบไฟล์: $mainScript" -ForegroundColor Red
    Read-Host "กด Enter เพื่อปิด"
    exit
}

Write-Host "✅ พร้อมเริ่มต้น!" -ForegroundColor Green
Write-Host ""

# เรียกใช้ Python script
python $mainScript

# รอปิด
Write-Host ""
Read-Host "กด Enter เพื่อปิด"