@echo off
title psy-client-cards

echo.
echo ========================================
echo   psy-client-cards
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Install Python from https://www.python.org/downloads/
    echo Check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies.
        echo Try manually: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed
    echo.
) else (
    echo [OK] Dependencies ready
    echo.
)

echo Starting app at http://127.0.0.1:8501
echo To stop: close this window or press Ctrl+C
echo.

python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501

pause
