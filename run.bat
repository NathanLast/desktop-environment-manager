@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Program stopped unexpectedly with error code %ERRORLEVEL%.
    pause
)
