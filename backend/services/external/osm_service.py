"""
OpenStreetMap Emergency Infrastructure Service
─────────────────────────────────────────────
Fetches real, live emergency infrastructure (police stations, hospitals, clinics)
around any GPS coordinate globally using OpenStreetMap.
"""
import math
import time
import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cache: cache_key -> {data, expires_at}
_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 7200  # 2 hours cache

# Curated emergency fallback nodes for Mumbai demo area
DEFAULT_MUMBAI_FALLBACK = [
    {"name": "Bandra Police Station", "type": "police", "lat": 19.0556, "lng": 72.8398, "phone": "100"},
    {"name": "Bail Bazar Police Station", "type": "police", "lat": 19.0853, "lng": 72.8811, "phone": "100"},
    {"name": "Khar Police Station", "type": "police", "lat": 19.0729, "lng": 72.8377, "phone": "100"},
    {"name": "Nehru Nagar Police Chowky", "type": "police", "lat": 19.0651, "lng": 72.8809, "phone": "100"},
    {"name": "Lilavati Hospital & Research Centre", "type": "hospital", "lat": 19.0514, "lng": 72.8291, "phone": "102"},
    {"name": "Ayurseva Hospital", "type": "hospital", "lat": 19.0435, "lng": 72.8499, "phone": "108"},
    {"name": "Zynova Heart Hospital", "type": "hospital", "lat": 19.0890, "lng": 72.9071, "phone": "108"},
    {"name": "Babasaheb Gawde Hospital", "type": "hospital", "lat": 19.0997, "lng": 72.8463, "phone": "108"},
]


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two GPS points."""
    r = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 1)


async def _query_nominatim(q: str, lat: float, lng: float, delta_deg: float, limit: int = 5) -> List[Dict[str, Any]]:
    """Query OpenStreetMap Nominatim with viewbox bounding."""
    viewbox = f"{lng - delta_deg},{lat + delta_deg},{lng + delta_deg},{lat - delta_deg}"
    url = f"https://nominatim.openstreetmap.org/search?q={q}&viewbox={viewbox}&bounded=1&format=json&limit={limit}"
    results = []

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "SafeTrail-Safety-Platform/1.0 (safety@safetrail.org)"},
            )
            if resp.status_code == 200:
                for item in resp.json():
                    item_lat = float(item["lat"])
                    item_lng = float(item["lon"])
                    dist = haversine_distance_meters(lat, lng, item_lat, item_lng)
                    name = item.get("name") or item.get("display_name", "").split(",")[0].strip()
                    results.append({
                        "id": str(item.get("place_id")),
                        "name": name,
                        "type": "police" if "police" in q else "hospital",
                        "lat": item_lat,
                        "lng": item_lng,
                        "distance_meters": dist,
                        "source": "OpenStreetMap Nominatim",
                    })
    except Exception as exc:
        logger.warning(f"Nominatim query '{q}' failed: {exc}")

    return results


async def fetch_nearby_emergency_services(
    lat: float,
    lng: float,
    radius_meters: int = 4000,
) -> Dict[str, Any]:
    """
    Fetch real police stations and hospitals around given coordinates.
    """
    cache_key = f"{round(lat, 3)}_{round(lng, 3)}_{radius_meters}"
    now = time.time()

    if cache_key in _CACHE:
        cached = _CACHE[cache_key]
        if cached["expires_at"] > now:
            return cached["data"]

    # 1 degree lat is ~111km, so radius_meters to delta degrees:
    delta_deg = max(0.02, min(0.12, (radius_meters / 111000.0) * 1.3))

    import asyncio
    police_task = _query_nominatim("police", lat, lng, delta_deg, limit=6)
    medical_task = _query_nominatim("hospital", lat, lng, delta_deg, limit=6)

    police_results, medical_results = await asyncio.gather(police_task, medical_task)
    all_places = police_results + medical_results

    # If live search returned empty (e.g. offline/network issue), use curated local fallback
    if not all_places:
        for fb in DEFAULT_MUMBAI_FALLBACK:
            dist = haversine_distance_meters(lat, lng, fb["lat"], fb["lng"])
            if dist <= radius_meters * 1.5:
                all_places.append({
                    "id": f"fallback_{fb['name'].lower().replace(' ', '_')}",
                    "name": fb["name"],
                    "type": fb["type"],
                    "lat": fb["lat"],
                    "lng": fb["lng"],
                    "distance_meters": dist,
                    "phone": fb.get("phone"),
                    "source": "Emergency Registry",
                })

    all_places.sort(key=lambda x: x["distance_meters"])

    police = [p for p in all_places if p["type"] == "police"]
    medical = [p for p in all_places if p["type"] in ("hospital", "clinic")]

    result = {
        "center": {"lat": lat, "lng": lng},
        "radius_meters": radius_meters,
        "total_found": len(all_places),
        "police_count": len(police),
        "medical_count": len(medical),
        "nearest_police": police[0] if police else None,
        "nearest_medical": medical[0] if medical else None,
        "services": all_places[:12],
        "is_isolated": len(police) == 0 and len(medical) == 0,
    }

    _CACHE[cache_key] = {
        "data": result,
        "expires_at": now + CACHE_TTL_SECONDS,
    }

    return result
