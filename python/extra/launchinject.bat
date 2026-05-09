@echo off
title Chrome Debug Launcher
echo Killing all Chrome processes...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo Starting Chrome with remote debugging on port 9222...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
    --remote-debugging-port=9222 ^
    --remote-allow-origins=* ^
    --user-data-dir=%temp%\chrome_debug_profile
echo Done.
echo.
echo Verifying debugger is running...
timeout /t 3 /nobreak >nul
powershell -Command "(Invoke-WebRequest http://localhost:9222/json -UseBasicParsing).Content"
echo.
echo If you see a JSON list (even empty), the debugger is working.
pause
start python\inject.py
exit