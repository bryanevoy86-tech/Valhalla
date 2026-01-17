@echo off
REM Valhalla Sandbox Service Management - Batch Version
REM Simple control script for the sandbox service

if "%1%"=="" (
    echo.
    echo ================================
    echo VALHALLA SANDBOX SERVICE MANAGER
    echo ================================
    echo.
    echo Usage: manage_sandbox.bat [command]
    echo.
    echo Commands:
    echo   start     - Start sandbox service
    echo   stop      - Stop sandbox service
    echo   status    - Show service status
    echo   logs      - Show recent logs
    echo.
    goto :eof
)

if "%1%"=="start" (
    echo Starting Valhalla Sandbox Service...
    python SANDBOX_SERVICE.py
    goto :eof
)

if "%1%"=="stop" (
    echo Stopping Valhalla Sandbox Service...
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq SANDBOX_SERVICE*" 2>nul
    for /f "tokens=5" %%a in ('tasklist /FI "IMAGENAME eq python.exe" ^| findstr /R "^python"') do (
        taskkill /F /PID %%a 2>nul
    )
    echo Service stopped.
    goto :eof
)

if "%1%"=="status" (
    echo.
    echo Checking sandbox service...
    tasklist /FI "IMAGENAME eq python.exe" | findstr "python" >nul
    if %errorlevel%==0 (
        echo Status: RUNNING
        tasklist /FI "IMAGENAME eq python.exe"
    ) else (
        echo Status: STOPPED
    )
    echo.
    goto :eof
)

if "%1%"=="logs" (
    echo.
    echo Recent Sandbox Service Logs:
    echo =============================
    if exist logs\sandbox_service.log (
        powershell -NoProfile -Command "Get-Content logs\sandbox_service.log | Select-Object -Last 20"
    ) else (
        echo No logs found.
    )
    echo.
    goto :eof
)

echo Unknown command: %1%
