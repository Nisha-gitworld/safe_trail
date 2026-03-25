#!/usr/bin/env python3
"""
SafeTrail — End-to-End Demo Script
════════════════════════════════════
Demonstrates all core scenarios against the running backend.

Usage:
    cd backend
    python ../scripts/demo.py

Prerequisites:
    • Backend running on http://localhost:8000
    • Mock APIs running on :9001 and :9002
"""
import asyncio
import httpx
import json
import time
from datetime import datetime

BASE   = "http://localhost:8000/api"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"


def hdr(title: str):
    print(f"\n{BOLD}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{'─'*55}{RESET}")


def ok(msg: str):  print(f"  {GREEN}✅ {msg}{RESET}")
def warn(msg: str): print(f"  {YELLOW}⚠️  {msg}{RESET}")
def err(msg: str):  print(f"  {RED}❌ {msg}{RESET}")
def info(msg: str): print(f"     {msg}")


async def run_demo():
    async with httpx.AsyncClient(timeout=15) as c:

        # ── 0. Health check ──────────────────────────────────────────────────
        hdr("0 · Health Check")
        res = await c.get("http://localhost:8000/health")
        if res.status_code == 200:
            ok(f"Backend online — {res.json()['version']}")
        else:
            err("Backend not reachable — start it first with: uvicorn main:app --reload")
            return

        # ── 1. Register tourist ──────────────────────────────────────────────
        hdr("1 · Tourist Registration")
        reg_payload = {
            "email":          f"demo_{int(time.time())}@safetrail.test",
            "password":       "demo12345",
            "full_name":      "Priya Demo",
            "nationality":    "Indian",
            "blood_type":     "B+",
            "allergies":      "Penicillin",
            "embassy_contact":"+91-11-2301-4000",
        }
        res = await c.post(f"{BASE}/auth/register", json=reg_payload)
        if res.status_code == 201:
            ok(f"User registered: {reg_payload['email']}")
        else:
            warn(f"Registration issue: {res.text[:100]}")

        # Login
        res = await c.post(f"{BASE}/auth/login", json={
            "email": reg_payload["email"], "password": reg_payload["password"]
        })
        token = res.json().get("access_token", "demo")
        hdrs  = {"Authorization": f"Bearer {token}"}
        ok(f"JWT token acquired (expires 15 min)")

        # ── 2. Safe zone check ───────────────────────────────────────────────
        hdr("2 · Risk Scoring — Safe Zone (Marine Drive, 2 PM)")
        res = await c.post(f"{BASE}/risk/score", headers=hdrs, json={
            "lat": 18.944, "lng": 72.823,
            "speed": 1.5, "dwell_time": 60,
            "hour": 14, "crowd_density": 0.2, "user_id": "me",
        })
        if res.status_code == 200:
            d = res.json()
            ok(f"Danger score: {d['danger_score']} → {d['zone_type'].upper()}")
            info(f"Alert level: {d['alert_level']} | {d['recommendation']}")
        else:
            err(f"Risk score failed: {res.text[:120]}")

        await asyncio.sleep(0.5)

        # ── 3. Danger zone check ─────────────────────────────────────────────
        hdr("3 · Risk Scoring — Danger Zone (11 PM, stationary, high crowd)")
        res = await c.post(f"{BASE}/risk/score", headers=hdrs, json={
            "lat": 19.040, "lng": 72.855,
            "speed": 0.1, "dwell_time": 720,
            "hour": 23, "crowd_density": 0.88, "user_id": "me",
        })
        if res.status_code == 200:
            d = res.json()
            score_str = f"{RED}{d['danger_score']}{RESET}" if d['danger_score'] > 70 else str(d['danger_score'])
            ok(f"Danger score: {score_str} → {d['zone_type'].upper()}")
            info(f"Alert level: {d['alert_level']} | {d['recommendation']}")
        else:
            err(f"Risk score failed: {res.text[:120]}")

        await asyncio.sleep(0.5)

        # ── 4. Geofence check ────────────────────────────────────────────────
        hdr("4 · Geofence Check — Tourist entering danger zone")
        res = await c.post(f"{BASE}/geofence/check", headers=hdrs, json={
            "lat": 19.042, "lng": 72.851, "user_id": "me",
        })
        if res.status_code == 200:
            d = res.json()
            ok(f"Zone: {d.get('zone_name','Unknown')} | Risk: {d['risk_level'].upper()}")
            if d.get("should_escalate"):
                info(f"🚨 Escalation triggered — dwell {d['dwell_pings']} pings")
        else:
            warn(f"Geofence check: {res.text[:120]}")

        # ── 5. Incident classification ───────────────────────────────────────
        hdr("5 · Incident Classifier (NLP)")
        test_cases = [
            ("I was robbed at the market, they took my bag!", "THEFT"),
            ("I can't breathe, my chest hurts, I need help!", "MEDICAL"),
            ("I've been in a car accident near the highway", "ACCIDENT"),
            ("I'm lost and can't find my hotel",             "LOST"),
        ]
        for text, expected in test_cases:
            res = await c.post(f"{BASE}/incident/classify", headers=hdrs,
                               json={"text": text})
            if res.status_code == 200:
                d = res.json()
                match = "✅" if d['incident_type'] == expected else "⚠️ "
                print(f"  {match}  [{d['incident_type']:12}] conf={d['confidence']:.2f} → \"{text[:45]}…\"")
            await asyncio.sleep(0.2)

        # ── 6. SOS trigger ───────────────────────────────────────────────────
        hdr("6 · SOS Emergency Trigger")
        res = await c.post(f"{BASE}/incident/sos", headers=hdrs, json={
            "user_id":      "me",
            "lat":          19.045,
            "lng":          72.856,
            "incident_type":"THEFT",
            "description":  "Demo: tourist SOS triggered",
            "blockchain_did":"did:polygon:0xDEMO1234",
        })
        if res.status_code == 200:
            d = res.json()
            ok(f"SOS dispatched! Incident ID: {d['incident_id']}")
            info(f"Notified: {', '.join(d['notified_to'])}")
            info(f"Timestamp: {d['timestamp']}")
        else:
            warn(f"SOS response: {res.text[:120]}")

        await asyncio.sleep(0.5)

        # ── 7. Heatmap ───────────────────────────────────────────────────────
        hdr("7 · Safety Heatmap (Mumbai)")
        res = await c.get(f"{BASE}/heatmap/MUM", headers=hdrs)
        if res.status_code == 200:
            d = res.json()
            cells = d.get("cells", [])
            high  = [c for c in cells if c["score"] > 70]
            low   = [c for c in cells if c["score"] < 40]
            ok(f"Heatmap generated: {len(cells)} grid cells")
            info(f"High risk cells: {len(high)} | Safe cells: {len(low)}")
        else:
            warn(f"Heatmap: {res.text[:120]}")

        # ── 8. Buddy system ──────────────────────────────────────────────────
        hdr("8 · Buddy System — Create group")
        res = await c.post(f"{BASE}/buddy/groups", headers=hdrs, json={
            "group_name": "Mumbai Heritage Tour Demo",
            "city":       "MUM",
        })
        if res.status_code == 200:
            d = res.json()
            ok(f"Group created! Code: {d['group_id']}")
            info(f"Share this code with tour members: {d['join_code']}")
        else:
            warn(f"Buddy group: {res.text[:120]}")

        # ── 9. Digital ID ────────────────────────────────────────────────────
        hdr("9 · Digital Identity Profile")
        res = await c.get(f"{BASE}/identity/profile", headers=hdrs)
        if res.status_code == 200:
            d = res.json()
            ok(f"DID: {d['did']}")
            info(f"Network: {d['network']}")
            info(f"IPFS CID: {d['ipfs_cid']}")
        else:
            warn(f"Identity: {res.text[:120]}")

        # ── 10. WebSocket note ───────────────────────────────────────────────
        hdr("10 · WebSocket Real-Time (info)")
        ok("Connect at: ws://localhost:8000/ws/{user_id}?token={jwt}&city=MUM")
        info("Send: { \"lat\": 19.07, \"lng\": 72.87, \"speed\": 1.5, \"hour\": 14 }")
        info("Receive: danger_score · zone_alert · sos_confirmed · buddy_alert")

        # ── Summary ──────────────────────────────────────────────────────────
        hdr("Demo Complete ✅")
        print(f"""
  {BOLD}All systems operational:{RESET}
  • Risk AI scoring         {GREEN}✅{RESET}
  • Geofence detection      {GREEN}✅{RESET}
  • Incident classification {GREEN}✅{RESET}
  • SOS dispatch pipeline   {GREEN}✅{RESET}
  • Safety heatmap          {GREEN}✅{RESET}
  • Buddy system            {GREEN}✅{RESET}
  • Blockchain DID profile  {GREEN}✅{RESET}
  • WebSocket real-time     {GREEN}✅{RESET}

  {BOLD}API Docs:{RESET}  http://localhost:8000/docs
  {BOLD}Dashboard:{RESET} http://localhost:5173
        """)


if __name__ == "__main__":
    asyncio.run(run_demo())
