"""Routes — Risk AI"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional
from models.schemas import LocationFeature, RiskResponse
from services.ai.risk_engine import predict_risk_live
from services.auth_service import get_current_user
from services.external.weather_service import fetch_live_weather

router = APIRouter()


@router.post("/score", response_model=RiskResponse)
async def get_risk_score(
    feat: LocationFeature,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/risk/score
    Returns AI-predicted danger score + live weather + nearby emergency POIs.
    """
    feat.user_id = current_user["user_id"]
    return await predict_risk_live(feat)


@router.get("/live-assessment", response_model=RiskResponse)
async def get_live_assessment(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    hour: Optional[int] = Query(default=None, ge=0, le=23),
    speed: float = Query(default=1.2, ge=0),
    dwell_time: int = Query(default=0, ge=0),
    crowd_density: float = Query(default=0.3, ge=0, le=1),
):
    """
    GET /api/risk/live-assessment?lat=19.076&lng=72.877
    Public live safety analysis for current coordinates.
    """
    h = hour if hour is not None else datetime.utcnow().hour
    feat = LocationFeature(
        user_id="live_tourist",
        lat=lat,
        lng=lng,
        hour=h,
        speed=speed,
        dwell_time=dwell_time,
        crowd_density=crowd_density,
    )
    return await predict_risk_live(feat)


@router.get("/weather")
async def get_live_weather_route(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    """
    GET /api/risk/weather?lat=19.076&lng=72.877
    Live real-time weather & hazard metrics from Open-Meteo.
    """
    return await fetch_live_weather(lat, lng)


@router.get("/auto-location")
async def auto_detect_location():
    """
    GET /api/risk/auto-location
    Auto-detects the client's current city and coordinates via IP geolocation.
    """
    import httpx
    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get("http://ip-api.com/json/")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    city = data.get("city", "Local Area")
                    region = data.get("regionName", "")
                    country = data.get("country", "")
                    display_name = f"{city}, {region}" if region else city
                    return {
                        "name": display_name,
                        "city": city,
                        "region": region,
                        "country": country,
                        "lat": float(data.get("lat")),
                        "lng": float(data.get("lon")),
                        "detected": True,
                    }
    except Exception:
        pass

    return {
        "name": "Bhubaneswar, Odisha",
        "city": "Bhubaneswar",
        "region": "Odisha",
        "country": "India",
        "lat": 20.2706,
        "lng": 85.8334,
        "detected": False,
    }




@router.get("/heatmap")
async def get_heatmap(
    city: str = "MUM",
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/risk/heatmap?city=MUM
    Returns aggregated risk grid cells for the city map view.
    In production this is cached in Redis and updated hourly.
    """
    # Mock heatmap data for demo
    import random
    random.seed(42)
    cells = []
    # Mumbai bounding box approximation
    lat_range = (18.87, 19.27)
    lng_range = (72.77, 72.97)
    for _ in range(80):
        cells.append({
            "lat":   round(random.uniform(*lat_range), 4),
            "lng":   round(random.uniform(*lng_range), 4),
            "score": round(random.uniform(10, 95), 1),
        })
    return {"city": city, "cells": cells, "generated_at": "2024-01-01T00:00:00Z"}
