
@echo off
echo ========================================
echo   DragonAI Backend - Starting Service
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Copying .env.example to .env...
    copy ".env.example" ".env"
    echo Please edit .env file with your configuration!
    echo.
)

REM Create required directories
if not exist "storage" mkdir storage 2>nul
if not exist "chroma_db" mkdir chroma_db 2>nul
if not exist "logs" mkdir logs 2>nul

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.13+
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Initialize database
echo.
echo Initializing database...
python scripts\init_db.py

REM Start the server
echo.
echo ========================================
echo   Starting DragonAI Server...
echo ========================================
echo.
echo API Documentation: http://localhost:8000/docs
echo Health Check:      http://localhost:8000/health
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

