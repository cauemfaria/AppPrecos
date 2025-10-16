@echo off
REM Development setup script for Windows

echo ===============================================================================
echo  AppPrecos Development Setup
echo ===============================================================================

echo.
echo [1/3] Setting up Python backend...
cd backend

REM Create virtual environment
if not exist venv (
    python -m venv venv
    echo   [OK] Created virtual environment
) else (
    echo   [OK] Virtual environment already exists
)

REM Activate and install dependencies
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
playwright install chromium
echo   [OK] Backend dependencies installed

REM Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('  [OK] Database initialized')"

cd ..

echo.
echo [2/3] Android setup...
echo   [INFO] Open Android Studio and import the android/ folder
echo   [INFO] Sync Gradle and build the project

echo.
echo [3/3] Setup complete!
echo ===============================================================================
echo.
echo Next steps:
echo   1. Start backend: scripts\run_backend.bat
echo   2. Open Android Studio and import android/ folder
echo   3. Run the Android app
echo.
echo ===============================================================================
pause

