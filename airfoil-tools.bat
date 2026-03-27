@echo off
cd /d "%~dp0"

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw airfoil_tools.py
    exit
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" py airfoil_tools.py
    exit
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python airfoil_tools.py
    exit
)

echo.
echo ERROR: Python not found.
echo Please install Python and ensure it is in PATH.
pause
