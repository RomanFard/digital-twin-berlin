@echo off
echo Stopping API...
taskkill /F /IM python.exe 2>nul
echo Done.
timeout /t 2