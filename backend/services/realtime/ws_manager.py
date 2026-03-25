"""
WebSocket Real-Time Alert Service
───────────────────────────────────
Manages live connections and broadcasts:
  • Danger score updates (every 10s per user)
  • Zone entry/exit events
  • City-wide alerts (admin → all tourists in a city)
  • Buddy system proximity warnings
  • SOS confirmation receipts

Architecture:
  • Each tourist connects with JWT token
  • Server maintains a connection pool per city
  • Redis pub/sub bridges multiple backend instances
    (allows horizontal scaling)
"""
import json
import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """In-process connection pool (use Redis pub/sub for multi-instance prod)."""

    def __init__(self):
        # user_id → WebSocket
        self.active: Dict[str, WebSocket] = {}
        # city_code → set of user_ids
        self.city_rooms: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, city: str = "MUM"):
        await websocket.accept()
        self.active[user_id] = websocket
        self.city_rooms.setdefault(city, set()).add(user_id)
        logger.info(f"WS connected: {user_id} in {city} ({len(self.active)} total)")

        # Send immediate connection acknowledgement
        await self.send_personal(user_id, {
            "type":      "connected",
            "user_id":   user_id,
            "city":      city,
            "timestamp": datetime.utcnow().isoformat(),
            "message":   "SafeTrail real-time alerts active",
        })

    def disconnect(self, user_id: str, city: str = "MUM"):
        self.active.pop(user_id, None)
        if city in self.city_rooms:
            self.city_rooms[city].discard(user_id)
        logger.info(f"WS disconnected: {user_id}")

    async def send_personal(self, user_id: str, payload: dict):
        """Send a message to one specific user."""
        ws = self.active.get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception as e:
                logger.warning(f"WS send failed for {user_id}: {e}")
                self.active.pop(user_id, None)

    async def broadcast_city(self, city: str, payload: dict, exclude: str = None):
        """Broadcast to all users in a city (city-wide alert)."""
        user_ids = self.city_rooms.get(city, set()).copy()
        tasks = [
            self.send_personal(uid, payload)
            for uid in user_ids
            if uid != exclude
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"City broadcast to {len(tasks)} users in {city}")

    async def broadcast_all(self, payload: dict):
        """Broadcast to every connected user."""
        tasks = [ws.send_text(json.dumps(payload)) for ws in self.active.values()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    @property
    def connection_count(self) -> int:
        return len(self.active)


# Singleton — imported by routes
manager = ConnectionManager()


# ── Payload helpers ───────────────────────────────────────────────────────────
def danger_score_payload(user_id: str, score: float, zone: str, rec: str) -> dict:
    return {
        "type":           "danger_score",
        "user_id":        user_id,
        "danger_score":   score,
        "zone_type":      zone,
        "recommendation": rec,
        "timestamp":      datetime.utcnow().isoformat(),
    }


def zone_alert_payload(user_id: str, zone_name: str, risk_level: str,
                       dwell_pings: int, escalate: bool) -> dict:
    return {
        "type":          "zone_alert",
        "user_id":       user_id,
        "zone_name":     zone_name,
        "risk_level":    risk_level,
        "dwell_pings":   dwell_pings,
        "should_escalate": escalate,
        "message": (
            f"⚠️ You have been in {zone_name} for "
            f"{dwell_pings * 10 // 60} min — please move to safety!"
        ) if escalate else f"Entered {risk_level} zone: {zone_name}",
        "timestamp": datetime.utcnow().isoformat(),
    }


def sos_confirmed_payload(user_id: str, incident_id: str, notified: list) -> dict:
    return {
        "type":        "sos_confirmed",
        "user_id":     user_id,
        "incident_id": incident_id,
        "notified_to": notified,
        "message":     "✅ Emergency services have been notified.",
        "timestamp":   datetime.utcnow().isoformat(),
    }


def buddy_alert_payload(group_id: str, separated_user: str, distance_m: float) -> dict:
    return {
        "type":           "buddy_alert",
        "group_id":       group_id,
        "separated_user": separated_user,
        "distance_m":     distance_m,
        "message":        f"👥 Group member separated by {distance_m:.0f}m!",
        "timestamp":      datetime.utcnow().isoformat(),
    }


def city_alert_payload(city: str, message: str, severity: str = "info") -> dict:
    return {
        "type":      "city_alert",
        "city":      city,
        "severity":  severity,    # info | warning | danger
        "message":   message,
        "timestamp": datetime.utcnow().isoformat(),
    }
