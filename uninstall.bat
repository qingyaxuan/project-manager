@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ================================================
echo   Project Manager - Uninstaller
echo ================================================
echo.
echo   This will remove the project manager.
echo   Press Ctrl+C at any time to cancel.
echo.
echo ================================================
echo.

:: ---- [1/2] Kill running server ----
echo [1/2] Stopping server (if running)...
set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8765" ^| findstr "LISTENING"') do (
    set "FOUND=1"
    taskkill /PID %%a /F >nul 2>&1
    echo        Process PID %%a terminated.
)
if !FOUND! equ 0 echo        No running server found.
echo.

:: ---- [2/2] Project data and program files ----
echo [2/2] Clean up files?
echo.
echo     Program directory: %~dp0
echo     Project data:      projects-data.json
echo     Your projects:     D:\Claude program\
echo.
set /p "DEL_ALL=     Delete ALL program files AND project data? [y/N]: "

if /i "!DEL_ALL!"=="y" (
    echo.
    echo     *** FINAL WARNING ***
    echo     This will permanently delete everything in:
    echo       %~dp0
    echo       D:\Claude program\
    set /p "CONFIRM=     Type YES to confirm: "
    if "!CONFIRM!"=="YES" (
        echo.
        echo     Deleting program files...
        cd /d "D:\"
        rmdir /s /q "%~dp0" 2>nul
        rmdir /s /q "D:\Claude program" 2>nul
        if not exist "%~dp0" (
            echo     All files removed.
            echo.
            echo     ================================================
            echo       Uninstall complete. Goodbye!
            echo     ================================================
            echo.
            pause
            exit /b 0
        ) else (
            echo     Some files could not be deleted (may be in use).
            echo     You can manually delete the folder later.
        )
    ) else (
        echo     Skipped - files preserved.
    )
) else (
    echo     Files preserved.
)

echo.
echo ================================================
echo   Done!
echo ================================================
echo.
pause
