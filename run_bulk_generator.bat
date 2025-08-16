@echo off
echo 🎯 QR Code Bulk Generator Launcher
echo =====================================

:: Set PostgreSQL environment
set DATABASE_URL=postgresql://postgres:%%40Carissa92@localhost:5432/qrproject_local

:: Change to project directory
cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

:: Check if required files exist
if not exist "bulk_qr_generator.py" (
    echo ❌ bulk_qr_generator.py not found
    echo Make sure you're running this from the project directory
    pause
    exit /b 1
)

if not exist "database.py" (
    echo ❌ database.py not found
    echo Make sure you're running this from the project directory
    pause
    exit /b 1
)

echo ✅ Environment configured
echo 📁 Working directory: %CD%
echo 🗄️  Database: PostgreSQL (local)
echo.

:: Run the bulk generator
echo 🚀 Starting QR Code Bulk Generator...
echo.
python bulk_qr_generator.py

:: Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo ❌ An error occurred
    pause
)

echo.
echo 👋 Bulk generation session ended
pause
