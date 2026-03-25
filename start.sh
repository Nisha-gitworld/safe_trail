#!/usr/bin/env bash
# SafeTrail — Quick Start Script
# Usage: chmod +x start.sh && ./start.sh

set -e
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RESET="\033[0m"

echo -e "${BOLD}🛡️  SafeTrail — Starting Services${RESET}\n"

# ── Check dependencies ────────────────────────────────────────────────────────
command -v python3 >/dev/null || { echo "❌ Python 3 is required"; exit 1; }
command -v node    >/dev/null || { echo "❌ Node.js is required";  exit 1; }
command -v docker  >/dev/null || { echo "⚠️  Docker not found — skipping DB containers"; DOCKER=false; }

DOCKER=${DOCKER:-true}

# ── .env check ────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  echo -e "${YELLOW}⚠️  .env not found — copying from .env.example${RESET}"
  cp .env.example .env
  echo -e "   Edit .env with your API keys before running in production.\n"
fi

# ── Start databases via Docker ────────────────────────────────────────────────
if [ "$DOCKER" = true ]; then
  echo -e "${BLUE}🐳 Starting Docker services (PostgreSQL · MongoDB · Redis)…${RESET}"
  docker-compose up -d postgres mongodb redis
  echo -e "${GREEN}   ✅ Databases started${RESET}\n"
  sleep 3
fi

# ── Backend setup ─────────────────────────────────────────────────────────────
echo -e "${BLUE}⚡ Setting up Python backend…${RESET}"
cd backend
if [ ! -d venv ]; then
  python3 -m venv venv
  echo "   Virtual environment created"
fi
source venv/bin/activate
pip install -r requirements.txt -q
echo -e "${GREEN}   ✅ Dependencies installed${RESET}"

# Train models if not present
if [ ! -f models/artifacts/xgb_risk.pkl ]; then
  echo -e "${YELLOW}   🤖 Training AI models (first run only)…${RESET}"
  python services/ai/train.py
fi

# Start backend in background
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}   ✅ Backend started → http://localhost:8000${RESET}"
echo -e "      API docs → http://localhost:8000/docs\n"

# Start mock APIs in background
python mock_apis.py &
MOCK_PID=$!
echo -e "${GREEN}   ✅ Mock APIs started → :9001 (Police) · :9002 (Hospital)${RESET}\n"
cd ..

# ── Frontend setup ────────────────────────────────────────────────────────────
echo -e "${BLUE}🖥️  Setting up React dashboard…${RESET}"
cd frontend
if [ ! -d node_modules ]; then
  npm install -q
fi
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}   ✅ Dashboard started → http://localhost:5173${RESET}\n"
cd ..

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "${BOLD}════════════════════════════════════════${RESET}"
echo -e "${BOLD}🛡️  SafeTrail is running!${RESET}"
echo -e "${BOLD}════════════════════════════════════════${RESET}"
echo -e "  Backend API   → ${GREEN}http://localhost:8000${RESET}"
echo -e "  API Docs      → ${GREEN}http://localhost:8000/docs${RESET}"
echo -e "  Admin UI      → ${GREEN}http://localhost:5173${RESET}"
echo -e "  Mock Police   → ${GREEN}http://localhost:9001${RESET}"
echo -e "  Mock Hospital → ${GREEN}http://localhost:9002${RESET}"
echo ""
echo -e "  Press ${BOLD}Ctrl+C${RESET} to stop all services"
echo -e "${BOLD}════════════════════════════════════════${RESET}\n"

# ── Wait and cleanup ──────────────────────────────────────────────────────────
trap "echo -e '\n🛑 Stopping...'; kill $BACKEND_PID $MOCK_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
