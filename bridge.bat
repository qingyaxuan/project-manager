@echo off
:: bridge.bat — called by Web UI to jump to a project
:: Usage: bridge.bat "Project Name" "D:\project\path"

set "PROJ_NAME=%~1"
set "PROJ_PATH=%~2"

echo ================================
echo   Continue: %PROJ_NAME%
echo   Path: %PROJ_PATH%
echo ================================
echo.

if not "%PROJ_PATH%"=="" (
    if exist "%PROJ_PATH%" (
        start "" "%PROJ_PATH%"
        echo [OK] Project folder opened.
    ) else (
        echo [WARN] Project path not found: %PROJ_PATH%
    )
)

echo.
echo In Claude Code, type: continue %PROJ_NAME%
echo.
pause
