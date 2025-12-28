@echo off
REM K3NG Configuration Tool - Easy Launcher (Windows)

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Run the Python launcher
python "%SCRIPT_DIR%launcher.py"

REM Pause if there was an error
if errorlevel 1 pause
