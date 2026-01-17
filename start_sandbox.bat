@echo off
REM Start Valhalla Sandbox Service
REM This script keeps the sandbox running in the background

cd /d c:\dev\valhalla

REM Run the sandbox service
python SANDBOX_SERVICE.py
