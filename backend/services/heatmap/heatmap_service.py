"""
Safety Heatmap Engine
──────────────────────
Generates a risk-scored grid over a city for the map heatmap layer.

Algorithm:
  1. Divide city bounding box into 500m × 500m grid cells
  2. For each cell, aggregate:
       • Historical incident count (last 30 days)
       • Average danger score from location_pings
       • Time-weighted recency bonus (recent incidents score higher)
  3. Normalise scores 0–100
  4. Cache result in Redis with 1-hour TTL
  5. Optionally: run LSTM to predict next-hour risk per cell

Output format (for Google Maps heatmap layer):
  [{ "lat": 19.07, "lng": 72.87, "weight": 0.85 }, ...]
"""
import json
import math
import logging
import hashlib
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── City bounding boxes ───────────────────────────────────────────────────────
CITY_BOUNDS = {
    "MUM": {"lat_min": 18.87, "lat_max": 19.28, "lng_min": 72.77, "lng_max": 72.98},
    "DEL": {"lat_min": 28.40, "lat_max": 28.88, "lng_min": 76.84, "lng_max": 77.35},
    "BLR": {"lat_min": 12.83, "lat_max": 13.14, "lng_min": 77.46, "lng_max": 77.77},
}

GRID_SIZE_DEG = 0.0045    # ≈ 500 m at equatorial latitudes
HEATMAP_TTL   = 3600      # Redis TTL in seconds (1 hour)


# ── Grid helpers ──────────────────────────────────────────────────────────────
def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in metres between two GPS coordinates."""
    R = 6_371_000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lng2 - lng1)
    a  = math.sin(dφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def cell_centre(lat_min: float, lng_min: float) -> tuple[float, float]:
    return lat_min + GRID_SIZE_DEG / 2, lng_min + GRID_SIZE_DEG / 2


def generate_grid(city: str) -> List[Dict]:
    """Generate all grid cell centres for a city."""
    bounds = CITY_BOUNDS.get(city)
    if not bounds:
        return []

    cells = []
    lat = bounds["lat_min"]
    while lat < bounds["lat_max"]:
        lng = bounds["lng_min"]
        while lng < bounds["lng_max"]:
            clat, clng = cell_centre(lat, lng)
            cells.append({"lat": round(clat, 5), "lng": round(clng, 5)})
            lng += GRID_SIZE_DEG
        lat += GRID_SIZE_DEG
    return cells


# ── Score computation ─────────────────────────────────────────────────────────
def recency_weight(incident_time: datetime) -> float:
    """
    Exponential decay: incidents from today score 1.0,
    incidents 30 days ago score ~0.05.
    """
    days_ago = (datetime.utcnow() - incident_time).days
    return math.exp(-0.1 * days_ago)


def compute_cell_score(incidents: list, pings: list) -> float:
    """
    Combine incident history + average ping scores into a 0–100 cell score.
    """
    incident_score = sum(recency_weight(i["created_at"]) for i in incidents) * 15
    ping_score     = (sum(p["danger_score"] for p in pings) / len(pings)) if pings else 0

    raw = incident_score * 0.6 + ping_score * 0.4
    return min(100.0, raw)


# ── Main heatmap builder ──────────────────────────────────────────────────────
async def build_heatmap(city: str) -> List[Dict]:
    """
    Build and cache the heatmap for a city.
    Returns list of { lat, lng, score, weight } dicts.
    """
    from database.db import redis_client

    cache_key = f"heatmap:{city}"
    cached    = await redis_client.get(cache_key)
    if cached:
        logger.info(f"Heatmap cache hit: {city}")
        return json.loads(cached)

    logger.info(f"Building heatmap for {city}…")
    cells  = generate_grid(city)
    result = []

    # In production: query PostgreSQL + MongoDB for real incidents/pings
    # For MVP/demo: generate deterministic synthetic scores per cell
    for cell in cells:
        # Deterministic pseudo-random score based on coordinates
        seed  = hashlib.md5(f"{cell['lat']:.4f}{cell['lng']:.4f}".encode()).hexdigest()
        score = (int(seed[:4], 16) % 90) + 5   # 5–95 range

        # Apply known high-risk area boosts (demo data for Mumbai)
        if city == "MUM":
            # Dharavi boost
            if 19.038 <= cell["lat"] <= 19.055 and 72.843 <= cell["lng"] <= 72.865:
                score = min(100, score + 35)
            # Marine Drive safe bonus
            if 18.940 <= cell["lat"] <= 18.955 and 72.818 <= cell["lng"] <= 72.835:
                score = max(5, score - 40)

        result.append({
            "lat":    cell["lat"],
            "lng":    cell["lng"],
            "score":  round(float(score), 1),
            "weight": round(score / 100, 3),  # 0.0–1.0 for Maps heatmap layer
        })

    # Cache for 1 hour
    await redis_client.setex(cache_key, HEATMAP_TTL, json.dumps(result))
    logger.info(f"Heatmap built: {len(result)} cells for {city}")
    return result


async def invalidate_heatmap(city: str):
    """Call this when a new incident is reported — forces rebuild on next request."""
    from database.db import redis_client
    await redis_client.delete(f"heatmap:{city}")
    logger.info(f"Heatmap cache invalidated: {city}")
