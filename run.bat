@echo off
title MEGA Web Downloader Pro
cd /d "%~dp0"
echo ========================================================
echo         MEGA Web Downloader Pro - Starting...
echo ========================================================
echo Server URL: http://localhost:8000
echo.
timeout /t 2 /nobreak >nul
start "" http://localhost:8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
