@echo off
title UpTime Monitor Startup

echo Starting UpTime Monitor...
echo.

echo [1/3] Checking Python dependencies...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)

echo [2/3] Checking Node.js dependencies...
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo Error: Failed to install Node.js dependencies
        pause
        exit /b 1
    )
)

echo [3/3] Starting services...
echo.

echo Starting backend server...
start "UpTime Monitor Backend" cmd /k "python main.py"

timeout /t 5 /nobreak > nul

echo Starting frontend development server...
start "UpTime Monitor Frontend" cmd /k "npm start"

echo.
echo UpTime Monitor is starting up!
echo - Backend API: http://localhost:8000
echo - Frontend UI: http://localhost:3000
echo.
echo Both services are running in separate windows.
echo Close those windows to stop the application.
echo.
pause