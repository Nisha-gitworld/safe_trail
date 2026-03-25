"""
AI Buddy System — Group Tour Safety
──────────────────────────────────────
Features:
  1. Group creation & member management
  2. Proximity monitoring — alert if member separates > 200m
  3. Dead-man switch — tourist must check in every 2 hours
  4. Group danger score — aggregate of all members' scores
  5. Tour guide dashboard data

Redis schema:
  group:{group_id}            → JSON group metadata
  group:{group_id}:members    → SET of user_ids
  group:{group_id}:loc:{uid}  → JSON {lat, lng, score, ts}  (TTL 60s)
  checkin:{user_id}           → timestamp of last check-in  (TTL 7200s)
"""
import json
import uuid
import math
import logging
from datetime import datetime, timedelta
from typing import Optional
from database.db import redis_client

logger = logging.getLogger(__name__)

PROXIMITY_ALERT_M   = 200     # metres — trigger buddy alert if exceeded
CHECKIN_INTERVAL_S  = 7200    # 2 hours
LOCATION_TTL_S      = 60      # drop member if no ping for 60s


# ── Group management ──────────────────────────────────────────────────────────
async def create_group(guide_id: str, group_name: str, city: str = "MUM") -> dict:
    group_id = str(uuid.uuid4())[:8].upper()
    meta = {
        "group_id":   group_id,
        "group_name": group_name,
        "guide_id":   guide_id,
        "city":       city,
        "created_at": datetime.utcnow().isoformat(),
    }
    await redis_client.setex(f"group:{group_id}", 86400, json.dumps(meta))
    return {"group_id": group_id, "join_code": group_id, **meta}


async def join_group(group_id: str, user_id: str) -> bool:
    key = f"group:{group_id}"
    if not await redis_client.exists(key):
        return False
    await redis_client.sadd(f"group:{group_id}:members", user_id)
    logger.info(f"User {user_id} joined group {group_id}")
    return True


async def leave_group(group_id: str, user_id: str):
    await redis_client.srem(f"group:{group_id}:members", user_id)
    await redis_client.delete(f"group:{group_id}:loc:{user_id}")


# ── Location update ───────────────────────────────────────────────────────────
async def update_member_location(
    group_id: str, user_id: str,
    lat: float, lng: float, danger_score: float = 0.0,
) -> list[dict]:
    """
    Update member location and check proximity to all other members.
    Returns list of proximity alerts (empty if all good).
    """
    # Store location
    loc_data = json.dumps({
        "lat": lat, "lng": lng,
        "score": danger_score,
        "ts": datetime.utcnow().isoformat(),
    })
    await redis_client.setex(f"group:{group_id}:loc:{user_id}", LOCATION_TTL_S, loc_data)

    # Check proximity against all other members
    member_ids = await redis_client.smembers(f"group:{group_id}:members")
    alerts = []

    for other_id in member_ids:
        if other_id == user_id:
            continue
        raw = await redis_client.get(f"group:{group_id}:loc:{other_id}")
        if not raw:
            continue  # member went offline
        other_loc = json.loads(raw)
        dist = _haversine(lat, lng, other_loc["lat"], other_loc["lng"])
        if dist > PROXIMITY_ALERT_M:
            alerts.append({
                "separated_user": other_id,
                "distance_m":     round(dist, 1),
                "last_seen":      other_loc["ts"],
            })

    return alerts


# ── Dead-man switch ───────────────────────────────────────────────────────────
async def record_checkin(user_id: str) -> dict:
    """Tourist taps 'I'm safe' — resets 2-hour countdown."""
    ts = datetime.utcnow().isoformat()
    await redis_client.setex(f"checkin:{user_id}", CHECKIN_INTERVAL_S, ts)
    next_due = (datetime.utcnow() + timedelta(seconds=CHECKIN_INTERVAL_S)).isoformat()
    return {"checked_in": ts, "next_due": next_due}


async def is_checkin_overdue(user_id: str) -> bool:
    """Returns True if tourist missed their 2-hour check-in."""
    val = await redis_client.get(f"checkin:{user_id}")
    return val is None   # TTL expired = overdue


# ── Group dashboard ───────────────────────────────────────────────────────────
async def get_group_status(group_id: str) -> dict:
    """
    Return full group status for the tour guide dashboard.
    Includes each member's last known location and danger score.
    """
    meta_raw = await redis_client.get(f"group:{group_id}")
    if not meta_raw:
        return {"error": "Group not found"}

    meta       = json.loads(meta_raw)
    member_ids = await redis_client.smembers(f"group:{group_id}:members")
    members    = []
    scores     = []

    for uid in member_ids:
        raw = await redis_client.get(f"group:{group_id}:loc:{uid}")
        checkin_ok = not await is_checkin_overdue(uid)
        if raw:
            loc = json.loads(raw)
            scores.append(loc["score"])
            members.append({
                "user_id":    uid,
                "lat":        loc["lat"],
                "lng":        loc["lng"],
                "score":      loc["score"],
                "last_seen":  loc["ts"],
                "online":     True,
                "checkin_ok": checkin_ok,
            })
        else:
            members.append({
                "user_id":    uid,
                "online":     False,
                "checkin_ok": checkin_ok,
            })

    group_score = sum(scores) / len(scores) if scores else 0

    return {
        **meta,
        "member_count":  len(member_ids),
        "online_count":  sum(1 for m in members if m.get("online")),
        "group_score":   round(group_score, 1),
        "group_zone":    "danger" if group_score > 70 else "caution" if group_score > 40 else "safe",
        "members":       members,
    }


# ── Utils ─────────────────────────────────────────────────────────────────────
def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6_371_000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ, dλ = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
