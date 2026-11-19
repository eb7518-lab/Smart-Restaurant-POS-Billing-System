@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Could not start with "python". Trying "py"...
    py main.py
)
pause
