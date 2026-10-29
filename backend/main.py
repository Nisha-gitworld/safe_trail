"""
SafeTrail Backend — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from database.db import init_db
from routes import risk, geofence, incident, identity, auth, buddy, heatmap, websocket
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        print("SafeTrail database initialized")
    except Exception as exc:
        print(f"SafeTrail database unavailable, starting API in demo mode: {exc}")
    print("SafeTrail backend started")
    yield
    print("SafeTrail backend shutting down")


app = FastAPI(
    title="SafeTrail API",
    description="Smart Tourist Safety Monitoring System",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/auth",     tags=["Auth"])
app.include_router(risk.router,      prefix="/api/risk",     tags=["Risk AI"])
app.include_router(geofence.router,  prefix="/api/geofence", tags=["Geofence"])
app.include_router(incident.router,  prefix="/api/incident", tags=["Incident"])
app.include_router(identity.router,  prefix="/api/identity", tags=["Digital ID"])
app.include_router(buddy.router,     prefix="/api/buddy",    tags=["Buddy System"])
app.include_router(heatmap.router,   prefix="/api/heatmap",  tags=["Heatmap"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "SafeTrail API", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "message": "SafeTrail — Smart Tourist Safety API",
        "docs": "/docs",
        "health": "/health",
    }
