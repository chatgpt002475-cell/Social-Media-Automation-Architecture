@echo off
title Social Media Automation Hub - Local Hosting
cd /d "%~dp0"

echo ========================================================
echo   Starting Social Media Automation Hub (Local Hosting)
echo ========================================================
echo.

:: Open the browser automatically after 2 seconds
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:5000"

:: Start the python server
python main.py server --port 5000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server terminated with an error code.
    pause
)
