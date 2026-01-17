@echo off
REM Valhalla Authentication Service - Startup Script for Windows
REM This script sets up and starts the secure authentication service

setlocal enabledelayedexpansion

echo.
echo ========================================================================
echo   Valhalla Secure Authentication Service - Startup
echo ========================================================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Checking Python installation...
python --version
echo.

REM Check dependencies
echo [2/3] Checking required packages...
python -m pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing required packages...
    python -m pip install -q fastapi uvicorn "python-jose[cryptography]" passlib[bcrypt] pydantic python-dotenv requests
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
    echo Packages installed successfully!
) else (
    echo All required packages are already installed
)
echo.

REM Start the authentication service
echo [3/3] Starting authentication service...
echo.
echo ========================================================================
echo   Service Configuration:
echo   - URL: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Username: The All father
echo   - Password: IAmBatman!1
echo ========================================================================
echo.
echo Press CTRL+C to stop the service
echo.

python -m uvicorn services.auth_service:app --reload --host 127.0.0.1 --port 8000

endlocal
