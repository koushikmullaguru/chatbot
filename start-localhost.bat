@echo off
REM Script to start the AI School Chat Application on localhost

echo Starting AI School Chat Application on localhost...
echo ==================================================

REM Check if we're in the correct directory
if not exist "package.json" (
    echo Error: Please run this script from the root directory of the project.
    pause
    exit /b 1
)

if not exist "backend\start.py" (
    echo Error: Please run this script from the root directory of the project.
    pause
    exit /b 1
)

REM Start the backend server
echo Starting backend server on http://localhost:8000...
cd backend
start "Backend Server" python start.py
cd ..

REM Wait a moment for the backend to start
timeout /t 3 /nobreak > nul

REM Start the frontend server
echo Starting frontend server on http://localhost:3000...
start "Frontend Server" npm run dev

echo.
echo ==================================================
echo Servers are running:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - API Documentation: http://localhost:8000/docs
echo.
echo Close this window to keep servers running.
echo Close the server windows to stop the servers.
echo ==================================================
echo.

pause