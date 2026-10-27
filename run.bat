@echo off
title OmniDownloader Pro - Universal Web Downloader
cd /d "%~dp0"
echo ========================================================
echo       OmniDownloader Pro (Universal Web Downloader)
echo ========================================================
echo Server URL: http://localhost:8000
echo.
timeout /t 2 /nobreak >nul
start "" http://localhost:8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
