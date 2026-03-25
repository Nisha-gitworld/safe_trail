"""
Geofence Service
─────────────────
• Zone containment check via PostGIS
• Dwell time tracking via Redis
• Battery-optimised ping interval logic
• Offline fallback hint (zones cached client-side)
"""
import logging
from dataclasses import dataclass
from typing import Optional
from database.db import redis_client, get_db
from models.schemas import GeofenceCheckRequest, GeofenceCheckResponse

logger = logging.getLogger(__name__)

DWELL_ESCALATION_PINGS = 30   # 30 pings × 10s = 5 minutes in danger zone


@dataclass
class ZoneResult:
    zone_id:    Optional[str]
    zone_name:  Optional[str]
    risk_level: str = "safe"


async def _query_zone(lat: float, lng: float) -> ZoneResult:
    """
    PostGIS spatial containment query.
    Falls back gracefully if PostGIS extension is not installed.
    """
    try:
        from sqlalchemy import text
        async for db in get_db():
            result = await db.execute(
                text("""
                    SELECT id::text, zone_name, risk_level
                    FROM geofence_zones
                    WHERE is_active = true
                      AND ST_Contains(
                            ST_GeomFromText(boundary_wkt, 4326),
                            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
                          )
                    ORDER BY
                        CASE risk_level
                            WHEN 'danger'  THEN 0
                            WHEN 'caution' THEN 1
                            ELSE 2
                        END
                    LIMIT 1
                """),
                {"lat": lat, "lng": lng},
            )
            row = result.fetchone()
            if row:
                return ZoneResult(zone_id=row[0], zone_name=row[1], risk_level=row[2])

    except Exception as e:
        logger.warning(f"PostGIS query failed: {e}")

    return ZoneResult(zone_id=None, zone_name=None, risk_level="safe")


async def check_geofence(req: GeofenceCheckRequest) -> GeofenceCheckResponse:
    """Main geofence check — called on every GPS ping."""

    # Save live position to Redis (30-second TTL for battery optimisation)
    await redis_client.setex(
        f"loc:{req.user_id}",
        30,
        f"{req.lat},{req.lng}",
    )

    zone = await _query_zone(req.lat, req.lng)

    in_danger = zone.risk_level == "danger"
    dwell_pings = 0
    should_escalate = False

    if in_danger and zone.zone_id:
        dwell_key   = f"dwell:{req.user_id}:{zone.zone_id}"
        dwell_pings = await redis_client.incr(dwell_key)
        await redis_client.expire(dwell_key, 600)   # reset after 10-min absence
        should_escalate = dwell_pings >= DWELL_ESCALATION_PINGS

    return GeofenceCheckResponse(
        in_danger_zone=in_danger,
        zone_name=zone.zone_name,
        risk_level=zone.risk_level,
        dwell_pings=dwell_pings,
        should_escalate=should_escalate,
    )


def adaptive_ping_interval(speed_ms: float) -> int:
    """
    Return recommended GPS ping interval in seconds.
    Lower speed → less frequent pings (battery saving).
    """
    if speed_ms > 5.0:   return 5    # fast moving — frequent updates
    if speed_ms > 1.0:   return 15   # walking pace
    return 30                        # stationary
