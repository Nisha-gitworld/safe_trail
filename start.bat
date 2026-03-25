@echo off
REM SafeTrail — Quick Start (Windows)
REM Run: start.bat

echo.
echo ===== SafeTrail - Starting Services =====
echo.

REM Check .env
if not exist .env (
    echo [WARN] .env not found - copying from .env.example
    copy .env.example .env
)

REM Start databases
echo [1/4] Starting Docker databases...
docker-compose up -d postgres mongodb redis
timeout /t 3 /nobreak >nul

REM Backend
echo [2/4] Starting FastAPI backend...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q

REM Train models if needed
if not exist models\artifacts\xgb_risk.pkl (
    echo       Training AI models (first run)...
    python services\ai\train.py
)

start "SafeTrail Backend" cmd /k "venv\Scripts\activate && uvicorn main:app --reload --port 8000"
start "SafeTrail Mock APIs" cmd /k "venv\Scripts\activate && python mock_apis.py"
cd ..

REM Frontend
echo [3/4] Starting React dashboard...
cd frontend
if not exist node_modules npm install -q
start "SafeTrail Dashboard" cmd /k "npm run dev"
cd ..

echo.
echo ============================================
echo   SafeTrail is running!
echo ============================================
echo   Backend API   -^> http://localhost:8000
echo   API Docs      -^> http://localhost:8000/docs
echo   Admin UI      -^> http://localhost:5173
echo   Mock Police   -^> http://localhost:9001
echo   Mock Hospital -^> http://localhost:9002
echo ============================================
echo.
pause
