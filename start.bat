@echo off
title psy-client-cards

echo.
echo ========================================
echo   psy-client-cards
echo ========================================
echo.

cd /d "%~dp0"

:: Проверка Python
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

:: Проверка зависимостей
python -c "import fastapi" >nul 2>&1
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
    echo [OK] Dependencies installed
    echo.
) else (
    echo [OK] Dependencies ready
    echo.
)

:: Запускаем FastAPI-сервер в отдельном окне
echo Starting server at http://127.0.0.1:8000 ...
start "psy-client-cards SERVER" python server.py

:: Ждём 2 секунды пока сервер поднимется
timeout /t 2 /nobreak > nul

:: Открываем фронтенд в браузере
echo Opening Frontend_ergonomic_v2.html in browser...
start "" "%~dp0Frontend_ergonomic_v2.html"

echo.
echo ========================================
echo   Готово!
echo   Сервер: http://127.0.0.1:8000
echo   Документация API: http://127.0.0.1:8000/docs
echo   Фронтенд открыт в браузере
echo.
echo   Чтобы остановить: закройте окно SERVER
echo ========================================
echo.
pause
