@echo off
cd /d "%~dp0"

REM --- Prova con pyw (senza console)
where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw naca4_pts.py
    exit
)

REM --- Fallback con py
where py >nul 2>nul
if %errorlevel%==0 (
    start "" py naca4_pts.py
    exit
)

REM --- Fallback con python
where python >nul 2>nul
if %errorlevel%==0 (
    start "" python naca4_pts.py
    exit
)

REM --- Errore se Python non trovato
echo.
echo ERRORE: Python non trovato!
echo Installa Python e assicurati che sia nel PATH.
pause