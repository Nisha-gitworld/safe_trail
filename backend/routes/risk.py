"""Routes — Risk AI"""
from fastapi import APIRouter, Depends
from models.schemas import LocationFeature, RiskResponse
from services.ai.risk_engine import predict_risk
from services.auth_service import get_current_user

router = APIRouter()


@router.post("/score", response_model=RiskResponse)
async def get_risk_score(
    feat: LocationFeature,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/risk/score
    Returns AI-predicted danger score + recommendation for given coordinates.
    """
    feat.user_id = current_user["user_id"]
    return predict_risk(feat)


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
