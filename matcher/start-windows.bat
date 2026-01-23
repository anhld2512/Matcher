@echo off
setlocal enabledelayedexpansion
title Matcher
color 0A

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║     Matcher - Auto Installer       ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Check if Docker is installed
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker chua duoc cai dat tren may tinh nay.
    echo.
    echo [*] Dang tai Docker Desktop...
    echo     Vui long doi trong giay lat...
    echo.
    
    :: Download Docker Desktop installer
    curl -L -o "%TEMP%\DockerDesktopInstaller.exe" "https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe"
    
    if exist "%TEMP%\DockerDesktopInstaller.exe" (
        echo [*] Dang cai dat Docker Desktop...
        echo     Luu y: May tinh co the can khoi dong lai sau khi cai dat.
        echo.
        start /wait "" "%TEMP%\DockerDesktopInstaller.exe" install --quiet
        
        echo.
        echo [!] Docker Desktop da cai dat xong.
        echo [!] Vui long KHOI DONG LAI may tinh, sau do chay lai file nay.
        echo.
        pause
        exit /b 0
    ) else (
        echo [X] Khong the tai Docker. Vui long tai thu cong tai:
        echo     https://www.docker.com/products/docker-desktop
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Docker da duoc cai dat
echo.

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Dang khoi dong Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    echo     Vui long doi Docker khoi dong (khoang 30-60 giay)...
    
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        echo     Van dang khoi dong Docker...
        goto wait_docker
    )
)

echo [OK] Docker dang chay
echo.

:: Navigate to script directory
cd /d "%~dp0"

echo [*] Dang khoi dong ung dung...
echo.

:: Build and start services
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo [X] Loi khi khoi dong ung dung!
    pause
    exit /b 1
)

:: Wait for services to be ready
echo [*] Dang cho cac dich vu san sang...
timeout /t 5 /nobreak >nul

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  THANH CONG! Ung dung da san sang!       ║
echo  ║                                          ║
echo  ║  Truy cap: http://localhost:8000         ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Open browser
start http://localhost:8000

echo Nhan phim bat ky de dong cua so nay...
echo (Ung dung van tiep tuc chay)
echo.
pause >nul
