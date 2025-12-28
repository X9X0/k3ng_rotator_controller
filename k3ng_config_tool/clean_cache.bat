@echo off
REM Quick script to clean Python bytecode cache
REM Useful during development when switching branches or after git pull

echo Cleaning Python bytecode cache...

REM Remove __pycache__ directories
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Remove .pyc files
del /s /q *.pyc 2>nul

REM Remove .pyo files (optimized bytecode)
del /s /q *.pyo 2>nul

echo.
echo Cache cleared successfully!
pause
