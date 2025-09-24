@echo off
echo 🧪 Testing Flask Performance with curl
echo =====================================
echo.

echo Testing minimal endpoints...
echo.

echo 1. Testing /api/test (should be instant):
curl -w "Time: %%{time_total}s\n" -s http://localhost:5000/api/test
echo.

echo 2. Testing /api/sleep (should be ~0.1s):
curl -w "Time: %%{time_total}s\n" -s http://localhost:5000/api/sleep
echo.

echo 3. Testing homepage:
curl -w "Time: %%{time_total}s\n" -s -o nul http://localhost:5000/
echo Homepage response time: see above
echo.

echo If all tests show ~2 seconds, the problem is in Flask/Python
echo If tests are fast, the problem is in the requests library