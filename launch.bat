@echo off
cd /d "D:\claude-projects-manager"

echo ================================
echo    Project Manager Launcher
echo ================================

:: Kill old server
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Find Python
set "PYTHON="
if exist "D:\anaconda\python.exe" set "PYTHON=D:\anaconda\python.exe"
if not defined PYTHON if exist "C:\Users\qingy\AppData\Local\Programs\Python\Launcher\py.exe" set "PYTHON=C:\Users\qingy\AppData\Local\Programs\Python\Launcher\py.exe"
if not defined PYTHON (
    for %%p in (py python3 python) do (
        where %%p >nul 2>&1
        if not errorlevel 1 if not defined PYTHON set "PYTHON=%%p"
    )
)

if not defined PYTHON (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

echo Python: %PYTHON%
echo Starting http://localhost:8765 ...

start "" /MIN "%PYTHON%" server.py
timeout /t 2 /nobreak >nul
start "" http://localhost:8765/web-ui/index.html

echo Done!
timeout /t 2 /nobreak >nul
exit
