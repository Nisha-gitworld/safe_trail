"""Routes — Geofence"""
from fastapi import APIRouter, Depends
from models.schemas import GeofenceCheckRequest, GeofenceCheckResponse, ZoneCreate
from services.location.geofence_service import check_geofence
from services.auth_service import get_current_user

router = APIRouter()


@router.post("/check", response_model=GeofenceCheckResponse)
async def geofence_check(
    req: GeofenceCheckRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/geofence/check
    Check if tourist is inside a risk zone.
    Called on every GPS ping from the mobile app.
    """
    req.user_id = current_user["user_id"]
    return await check_geofence(req)


@router.post("/zones")
async def create_zone(
    zone: ZoneCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/geofence/zones
    Admin endpoint to add a new geofence zone.
    boundary_wkt example: "POLYGON((72.82 18.92, 72.85 18.92, 72.85 18.95, 72.82 18.95, 72.82 18.92))"
    """
    # In production: validate WKT, insert into PostgreSQL with PostGIS
    return {
        "status":    "created",
        "zone_name": zone.zone_name,
        "risk_level":zone.risk_level,
        "message":   "Zone saved. PostGIS will index the boundary.",
    }


@router.get("/zones")
async def list_zones(
    city: str = "MUM",
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/geofence/zones?city=MUM
    Returns all active zones for the city (used for client-side caching / offline).
    """
    # Mock response for demo
    return {
        "city": city,
        "zones": [
            {"id": "z1", "name": "Dharavi Area",    "risk_level": "danger",  "danger_score": 82},
            {"id": "z2", "name": "Kurla Station",   "risk_level": "caution", "danger_score": 58},
            {"id": "z3", "name": "Marine Drive",    "risk_level": "safe",    "danger_score": 18},
            {"id": "z4", "name": "Colaba Market",   "risk_level": "caution", "danger_score": 47},
        ]
    }
