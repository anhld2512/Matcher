@echo off
echo ========================================
echo    CV-JD Matcher - Stop Services
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] Stopping all services...
docker-compose down

echo.
echo [SUCCESS] All services stopped!
echo.
pause
