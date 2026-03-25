"""Routes — Safety Heatmap"""
from fastapi import APIRouter, Depends
from services.heatmap.heatmap_service import build_heatmap, invalidate_heatmap
from services.auth_service import get_current_user

router = APIRouter()


@router.get("/{city}")
async def get_heatmap(city: str, user=Depends(get_current_user)):
    """
    GET /api/heatmap/MUM
    Returns risk-weighted grid cells for the city map layer.
    Cached in Redis for 1 hour, auto-rebuilt on new incidents.
    """
    city = city.upper()
    cells = await build_heatmap(city)
    return {
        "city":       city,
        "cell_count": len(cells),
        "cells":      cells,
        "note":       "weight field (0.0–1.0) is for Google Maps HeatmapLayer",
    }


@router.post("/{city}/invalidate")
async def invalidate(city: str, user=Depends(get_current_user)):
    """Force heatmap rebuild (call after new incident reported)."""
    await invalidate_heatmap(city.upper())
    return {"invalidated": True, "city": city.upper()}
