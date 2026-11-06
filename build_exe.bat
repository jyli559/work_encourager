@echo off
rem Build Windows executable. Requires Python 3.10+ on PATH.
cd /d %~dp0

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] python not found in PATH. Install Python 3.10+ first.
    pause
    exit /b 1
)

if not exist .venv\Scripts\python.exe (
    echo [Setup] Creating virtual environment...
    python -m venv .venv || goto :err
    .venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller || goto :err
)

.venv\Scripts\python.exe build_exe.py || goto :err
echo.
echo Build finished. See the "dist" folder.
pause
exit /b 0

:err
echo [ERROR] Build failed.
pause
exit /b 1
