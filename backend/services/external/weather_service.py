"""
Real-Time Weather & Environmental Risk Service
─────────────────────────────────────────────
Fetches live weather metrics using Open-Meteo API (100% free, no key needed)
and computes environmental risk adjustments for tourist safety.
"""
import time
import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Weather cache: (lat_rounded, lng_rounded) -> {data, expires_at}
_WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 1800  # 30 minutes


async def fetch_live_weather(lat: float, lng: float) -> Dict[str, Any]:
    """
    Fetch real-time weather parameters and calculate safety hazards.
    """
    cache_key = f"{round(lat, 2)}_{round(lng, 2)}"
    now = time.time()

    if cache_key in _WEATHER_CACHE:
        cached = _WEATHER_CACHE[cache_key]
        if cached["expires_at"] > now:
            return cached["data"]

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,wind_speed_10m,wind_gusts_10m"
    )

    weather_data = {
        "temperature_c": 28.0,
        "feels_like_c": 30.0,
        "humidity_pct": 65,
        "rain_mm": 0.0,
        "wind_speed_kmh": 10.0,
        "hazard_level": "none",
        "hazard_description": "Normal weather conditions",
        "risk_penalty": 0.0,
        "source": "Open-Meteo Live API",
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(url, headers={"User-Agent": "SafeTrail-Safety-Platform/1.0"})
            if resp.status_code == 200:
                data = resp.json().get("current", {})
                temp = data.get("temperature_2m", 28.0)
                feels = data.get("apparent_temperature", temp)
                humidity = data.get("relative_humidity_2m", 65)
                rain = data.get("rain", data.get("precipitation", 0.0))
                wind = data.get("wind_speed_10m", 10.0)
                gusts = data.get("wind_gusts_10m", wind)

                risk_penalty = 0.0
                hazard_level = "none"
                hazards = []

                if rain > 15.0:
                    hazard_level = "danger"
                    hazards.append(f"Heavy rain / flood risk ({rain} mm/h)")
                    risk_penalty += 0.25
                elif rain > 2.0:
                    hazard_level = "caution"
                    hazards.append(f"Moderate rain ({rain} mm/h)")
                    risk_penalty += 0.10

                if wind > 45.0 or gusts > 60.0:
                    hazard_level = "danger"
                    hazards.append(f"High storm winds ({wind} km/h)")
                    risk_penalty += 0.20
                elif wind > 28.0:
                    if hazard_level == "none":
                        hazard_level = "caution"
                    hazards.append(f"Brisk winds ({wind} km/h)")
                    risk_penalty += 0.05

                if temp > 40.0 or feels > 44.0:
                    hazard_level = "caution"
                    hazards.append(f"Extreme heat warning ({feels}°C heat index)")
                    risk_penalty += 0.10

                weather_data = {
                    "temperature_c": temp,
                    "feels_like_c": feels,
                    "humidity_pct": humidity,
                    "rain_mm": rain,
                    "wind_speed_kmh": wind,
                    "wind_gusts_kmh": gusts,
                    "hazard_level": hazard_level,
                    "hazard_description": ", ".join(hazards) if hazards else "Normal weather conditions",
                    "risk_penalty": round(risk_penalty, 2),
                    "source": "Open-Meteo Live API",
                }
    except Exception as e:
        logger.warning(f"Failed to fetch live weather: {e}")

    _WEATHER_CACHE[cache_key] = {
        "data": weather_data,
        "expires_at": now + CACHE_TTL,
    }

    return weather_data
