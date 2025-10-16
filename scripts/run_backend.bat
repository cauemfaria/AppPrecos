@echo off
REM Start the Flask backend server

echo ===============================================================================
echo  Starting AppPrecos Backend...
echo ===============================================================================

cd backend

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo.
echo Server starting at: http://localhost:5000
echo API Documentation: http://localhost:5000/
echo.
echo Press CTRL+C to stop
echo ===============================================================================
echo.

python app.py

