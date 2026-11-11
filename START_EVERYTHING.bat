@echo off
title Digital Twin Berlin - Launcher
color 0A

echo ========================================
echo   Digital Twin Berlin - Launcher
echo ========================================
echo.

echo [1/3] Starting PostgreSQL...
net start postgresql-x64-17 2>nul
echo   PostgreSQL is running.
echo.

echo [2/3] Starting API (hidden)...
start "" "C:\Users\Roman\Documents\code\api\start_api.vbs"
echo   API is starting...
echo.

echo [3/3] Waiting for API...
timeout /t 6 /nobreak >nul

echo.
echo ========================================
echo   All services started!
echo   Dashboard: http://127.0.0.1:8001/dashboard
echo ========================================
echo.
echo Press any key to close this window...
pause >nul