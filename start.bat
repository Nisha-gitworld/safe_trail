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
echo [1/4] Checking Docker databases...
docker ps >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker-compose up -d postgres mongodb redis
    timeout /t 2 /nobreak >nul
) else (
    echo [INFO] Docker is not running. Starting SafeTrail in standalone demo mode...
)

REM Backend
echo [2/4] Starting FastAPI backend...
cd backend
if not exist venv (
    if exist ..\.venv (
        mklink /J venv ..\.venv >nul 2>&1
    ) else (
        python -m venv venv
    )
)
call venv\Scripts\activate
python -c "import fastapi" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing backend dependencies...
    pip install fastapi uvicorn pydantic pydantic-settings python-dotenv asyncpg sqlalchemy motor redis python-jose passlib python-multipart httpx websockets numpy
)

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
