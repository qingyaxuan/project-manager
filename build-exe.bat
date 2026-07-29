@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================
echo    Build ProjectManager.exe
echo ================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    pause & exit /b 1
)

:: Install PyInstaller if needed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

:: Clean old build
if exist "dist\ProjectManager.exe" del /q "dist\ProjectManager.exe"
if exist "build" rmdir /s /q "build"

echo [INFO] Building EXE...
pyinstaller --onefile ^
    --name ProjectManager ^
    --icon=NONE ^
    --add-data "web-ui;web-ui" ^
    --hidden-import http.server ^
    --clean ^
    server.py

if exist "dist\ProjectManager.exe" (
    echo.
    echo ================================
    echo    BUILD SUCCESS
    echo    dist\ProjectManager.exe
    echo ================================
) else (
    echo.
    echo [ERROR] Build failed. Check output above.
)

pause
