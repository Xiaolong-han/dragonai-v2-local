
@echo off
echo ========================================
echo   Running DragonAI Tests
echo ========================================
echo.

REM Activate virtual environment
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run unit tests
echo.
echo Running unit tests...
echo.
pytest tests/unit/ -v --cov=app --cov-report=term-missing

echo.
echo ========================================
echo   Unit tests completed!
echo ========================================
echo.

REM Run integration tests
echo.
echo Running integration tests...
echo.
pytest tests/integration/ -v

echo.
echo ========================================
echo   All tests completed!
echo ========================================
echo.

pause

