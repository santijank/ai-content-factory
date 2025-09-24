@echo off
echo 🚀 Creating AI Content Factory Structure
echo ==========================================

REM Create main directories
mkdir ai-content-factory\trend-monitor 2>nul
mkdir ai-content-factory\trend-monitor\services 2>nul
mkdir ai-content-factory\trend-monitor\models 2>nul
mkdir ai-content-factory\content-engine 2>nul
mkdir ai-content-factory\content-engine\services 2>nul
mkdir ai-content-factory\content-engine\ai_services 2>nul
mkdir ai-content-factory\content-engine\models 2>nul
mkdir ai-content-factory\platform-manager 2>nul
mkdir ai-content-factory\platform-manager\services 2>nul
mkdir ai-content-factory\database 2>nul
mkdir ai-content-factory\database\models 2>nul
mkdir ai-content-factory\database\repositories 2>nul
mkdir ai-content-factory\config 2>nul
mkdir ai-content-factory\shared 2>nul
mkdir ai-content-factory\shared\models 2>nul
mkdir ai-content-factory\shared\utils 2>nul

echo ✅ Created directories

REM Create basic Python files to fix missing file errors
echo # Trend Monitor App > ai-content-factory\trend-monitor\app.py
echo """Trend Monitor Service""" >> ai-content-factory\trend-monitor\app.py
echo. >> ai-content-factory\trend-monitor\app.py
echo import asyncio >> ai-content-factory\trend-monitor\app.py
echo from datetime import datetime >> ai-content-factory\trend-monitor\app.py
echo. >> ai-content-factory\trend-monitor\app.py
echo async def main(): >> ai-content-factory\trend-monitor\app.py
echo     print("Trend Monitor Service Started") >> ai-content-factory\trend-monitor\app.py
echo. >> ai-content-factory\trend-monitor\app.py
echo if __name__ == "__main__": >> ai-content-factory\trend-monitor\app.py
echo     asyncio.run(main()) >> ai-content-factory\trend-monitor\app.py

echo # Content Engine App > ai-content-factory\content-engine\app.py
echo """Content Engine Service""" >> ai-content-factory\content-engine\app.py
echo. >> ai-content-factory\content-engine\app.py
echo import asyncio >> ai-content-factory\content-engine\app.py
echo from datetime import datetime >> ai-content-factory\content-engine\app.py
echo. >> ai-content-factory\content-engine\app.py
echo async def main(): >> ai-content-factory\content-engine\app.py
echo     print("Content Engine Service Started") >> ai-content-factory\content-engine\app.py
echo. >> ai-content-factory\content-engine\app.py
echo if __name__ == "__main__": >> ai-content-factory\content-engine\app.py
echo     asyncio.run(main()) >> ai-content-factory\content-engine\app.py

echo # Database Base Model > ai-content-factory\database\models\base.py
echo """Database Base Models""" >> ai-content-factory\database\models\base.py
echo. >> ai-content-factory\database\models\base.py
echo from datetime import datetime >> ai-content-factory\database\models\base.py
echo import uuid >> ai-content-factory\database\models\base.py
echo. >> ai-content-factory\database\models\base.py
echo class BaseModel: >> ai-content-factory\database\models\base.py
echo     def __init__(self): >> ai-content-factory\database\models\base.py
echo         self.id = str(uuid.uuid4()) >> ai-content-factory\database\models\base.py
echo         self.created_at = datetime.now() >> ai-content-factory\database\models\base.py

echo # App Config YAML > ai-content-factory\config\app_config.yaml
echo # AI Content Factory Configuration > ai-content-factory\config\app_config.yaml
echo app: >> ai-content-factory\config\app_config.yaml
echo   name: "AI Content Factory" >> ai-content-factory\config\app_config.yaml
echo   version: "1.0.0" >> ai-content-factory\config\app_config.yaml
echo   debug: true >> ai-content-factory\config\app_config.yaml
echo. >> ai-content-factory\config\app_config.yaml
echo database: >> ai-content-factory\config\app_config.yaml
echo   url: "sqlite:///content_factory.db" >> ai-content-factory\config\app_config.yaml
echo. >> ai-content-factory\config\app_config.yaml
echo apis: >> ai-content-factory\config\app_config.yaml
echo   youtube: >> ai-content-factory\config\app_config.yaml
echo     enabled: true >> ai-content-factory\config\app_config.yaml
echo   groq: >> ai-content-factory\config\app_config.yaml
echo     enabled: true >> ai-content-factory\config\app_config.yaml
echo   openai: >> ai-content-factory\config\app_config.yaml
echo     enabled: true >> ai-content-factory\config\app_config.yaml

echo ✅ Created basic files

REM Create __init__.py files
echo # Init files > ai-content-factory\__init__.py
echo. > ai-content-factory\trend-monitor\__init__.py
echo. > ai-content-factory\trend-monitor\services\__init__.py
echo. > ai-content-factory\trend-monitor\models\__init__.py
echo. > ai-content-factory\content-engine\__init__.py
echo. > ai-content-factory\content-engine\services\__init__.py
echo. > ai-content-factory\content-engine\ai_services\__init__.py
echo. > ai-content-factory\content-engine\models\__init__.py
echo. > ai-content-factory\platform-manager\__init__.py
echo. > ai-content-factory\platform-manager\services\__init__.py
echo. > ai-content-factory\database\__init__.py
echo. > ai-content-factory\database\models\__init__.py
echo. > ai-content-factory\database\repositories\__init__.py
echo. > ai-content-factory\shared\__init__.py
echo. > ai-content-factory\shared\models\__init__.py
echo. > ai-content-factory\shared\utils\__init__.py

echo ✅ Created __init__.py files

echo.
echo 🎉 File structure creation completed!
echo.
echo 📋 Next steps:
echo 1. Install dependencies: pip install google-api-python-client pytrends
echo 2. Run test again: python test_real_integration.py
echo 3. If tests pass: python real_integration_main.py