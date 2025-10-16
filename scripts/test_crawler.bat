@echo off
REM Test the NFCe crawler standalone

echo ===============================================================================
echo  Testing NFCe Crawler
echo ===============================================================================

cd backend

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo.
echo Running crawler on sample NFCe URL...
echo This will open a browser window and extract NCM codes...
echo.

python nfce_crawler_ultimate.py

echo.
echo Check ncm_codes.xlsx for results!
pause

