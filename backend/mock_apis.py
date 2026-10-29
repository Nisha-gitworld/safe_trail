"""
Mock External APIs — Police & Hospital
────────────────────────────────────────
Run this alongside the main backend for demos:
    python mock_apis.py

Listens on:
  • http://localhost:9001  ← Police API
  • http://localhost:9002  ← Hospital API
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uvicorn, threading

police_app  = FastAPI(title="Mock Police API")
hospital_app = FastAPI(title="Mock Hospital API")

incidents_log = []
ambulance_log = []


class IncidentReport(BaseModel):
    location:  dict
    type:      str
    did:       Optional[str] = None
    timestamp: Optional[str] = None


class AmbulanceRequest(BaseModel):
    location: dict
    did:      Optional[str] = None


# ── Police API ────────────────────────────────────────────────────────────────
@police_app.post("/incidents")
async def receive_incident(report: IncidentReport):
    entry = {**report.dict(), "received_at": datetime.utcnow().isoformat(),
             "case_id": f"POL-{len(incidents_log)+1001}"}
    incidents_log.append(entry)
    print(f"\n🚔 POLICE NOTIFIED | {report.type} at {report.location}")
    return {"status": "received", "case_id": entry["case_id"], "eta_minutes": 8}


@police_app.get("/incidents")
async def list_incidents():
    return {"incidents": incidents_log, "total": len(incidents_log)}


@police_app.get("/health")
async def police_health():
    return {"status": "ok", "service": "Mock Police API"}


# ── Hospital API ──────────────────────────────────────────────────────────────
@hospital_app.post("/ambulance")
async def dispatch_ambulance(req: AmbulanceRequest):
    entry = {**req.dict(), "dispatched_at": datetime.utcnow().isoformat(),
             "ambulance_id": f"AMB-{len(ambulance_log)+201}"}
    ambulance_log.append(entry)
    print(f"\n🏥 AMBULANCE DISPATCHED to {req.location}")
    return {"status": "dispatched", "ambulance_id": entry["ambulance_id"],
            "eta_minutes": 6, "hospital": "City General Hospital"}


@hospital_app.get("/ambulances")
async def list_ambulances():
    return {"ambulances": ambulance_log, "total": len(ambulance_log)}


@hospital_app.get("/health")
async def hospital_health():
    return {"status": "ok", "service": "Mock Hospital API"}


# ── Runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    def run_police():
        uvicorn.run(police_app, host="0.0.0.0", port=9001, log_level="warning")

    def run_hospital():
        uvicorn.run(hospital_app, host="0.0.0.0", port=9002, log_level="warning")

    t1 = threading.Thread(target=run_police,  daemon=True)
    t2 = threading.Thread(target=run_hospital, daemon=True)
    t1.start(); t2.start()
    print("Mock Police API running at http://localhost:9001")
    print("Mock Hospital API running at http://localhost:9002")
    t1.join(); t2.join()
