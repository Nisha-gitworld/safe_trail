"""
WebSocket Route — /ws/{user_id}
────────────────────────────────
Handles persistent tourist connections for real-time:
  • Risk score updates
  • Zone crossing alerts
  • SOS confirmations
  • Buddy proximity warnings
  • City-wide admin broadcasts
"""
import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from services.realtime.ws_manager import manager, city_alert_payload
from services.ai.risk_engine import predict_risk
from services.location.geofence_service import check_geofence
from models.schemas import LocationFeature, GeofenceCheckRequest
from config import settings
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


async def _verify_ws_token(token: str) -> dict | None:
    """Verify JWT for WebSocket connections (token passed as query param)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return {"user_id": payload["sub"], "email": payload.get("email")}
    except JWTError:
        return None


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...),
    city:  str = Query(default="MUM"),
):
    """
    Main tourist WebSocket connection.

    Client sends JSON location pings:
        { "lat": 19.07, "lng": 72.87, "speed": 1.2, "hour": 14 }

    Server pushes back:
        danger_score · zone_alert · sos_confirmed · buddy_alert · city_alert
    """
    # ── Authenticate ──────────────────────────────────────────────────────────
    user = await _verify_ws_token(token)
    if not user or user["user_id"] != user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket, user_id, city)

    try:
        while True:
            # Receive location ping from client
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=35)
            data = json.loads(raw)

            lat   = float(data.get("lat",   19.076))
            lng   = float(data.get("lng",   72.877))
            speed = float(data.get("speed", 0.0))
            hour  = int(data.get("hour",    datetime.utcnow().hour))

            # ── Risk score ────────────────────────────────────────────────────
            risk = predict_risk(LocationFeature(
                lat=lat, lng=lng, speed=speed,
                dwell_time=int(data.get("dwell_time", 0)),
                hour=hour,
                crowd_density=float(data.get("crowd_density", 0.3)),
                user_id=user_id,
            ))

            await manager.send_personal(user_id, {
                "type":           "danger_score",
                "danger_score":   risk.danger_score,
                "zone_type":      risk.zone_type,
                "alert_level":    risk.alert_level,
                "recommendation": risk.recommendation,
                "timestamp":      datetime.utcnow().isoformat(),
            })

            # ── Geofence check ────────────────────────────────────────────────
            geo = await check_geofence(GeofenceCheckRequest(
                lat=lat, lng=lng, user_id=user_id
            ))

            if geo.in_danger_zone:
                await manager.send_personal(user_id, {
                    "type":            "zone_alert",
                    "zone_name":       geo.zone_name,
                    "risk_level":      geo.risk_level,
                    "dwell_pings":     geo.dwell_pings,
                    "should_escalate": geo.should_escalate,
                    "message": (
                        f"🚨 You've been in danger zone '{geo.zone_name}' "
                        f"for {geo.dwell_pings * 10 // 60} min — evacuate now!"
                        if geo.should_escalate
                        else f"⚠️ Entering {geo.risk_level} zone: {geo.zone_name}"
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        logger.info(f"Client {user_id} disconnected normally")
    except asyncio.TimeoutError:
        # Client stopped sending — send keepalive then close
        try:
            await websocket.send_text(json.dumps({"type": "ping"}))
        except Exception:
            pass
    except Exception as e:
        logger.error(f"WS error for {user_id}: {e}")
    finally:
        manager.disconnect(user_id, city)


@router.websocket("/ws/admin/broadcast")
async def admin_broadcast(
    websocket: WebSocket,
    token: str = Query(...),
):
    """Admin endpoint — broadcast city-wide alerts."""
    user = await _verify_ws_token(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)
            city     = data.get("city", "MUM")
            message  = data.get("message", "Safety alert")
            severity = data.get("severity", "warning")

            payload = city_alert_payload(city, message, severity)
            await manager.broadcast_city(city, payload)
            await websocket.send_text(json.dumps({
                "status": "broadcast_sent",
                "recipients": len(manager.city_rooms.get(city, set())),
            }))
    except WebSocketDisconnect:
        pass


@router.get("/ws/stats")
async def ws_stats():
    """GET /ws/stats — connection count per city."""
    return {
        "total_connections": manager.connection_count,
        "cities": {city: len(users) for city, users in manager.city_rooms.items()},
    }
