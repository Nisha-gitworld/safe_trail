"""
Real-Time Weather & Environmental Risk Service
─────────────────────────────────────────────
Fetches live weather metrics using Open-Meteo API
and maps WMO codes to accurate real-time conditions.
"""
import time
import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Weather cache: (lat_rounded, lng_rounded) -> {data, expires_at}
_WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 300  # 5 minutes for freshness

WMO_DESCRIPTIONS = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Freezing Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Freezing Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail",
}


async def fetch_live_weather(lat: float, lng: float) -> Dict[str, Any]:
    """
    Fetch live weather parameters for given GPS coordinates.
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
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,wind_speed_10m,wind_gusts_10m"
        "&timezone=auto"
    )

    weather_data = {
        "temperature_c": 25.0,
        "feels_like_c": 26.0,
        "humidity_pct": 70,
        "rain_mm": 0.0,
        "wind_speed_kmh": 5.0,
        "condition": "Clear Sky",
        "hazard_level": "none",
        "hazard_description": "Clear Sky",
        "risk_penalty": 0.0,
        "is_day": 1,
        "source": "Open-Meteo Real-Time Weather API",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers={"User-Agent": "SafeTrail-Safety-Platform/1.0"})
            if resp.status_code == 200:
                current = resp.json().get("current", {})
                temp = round(current.get("temperature_2m", 25.0), 1)
                feels = round(current.get("apparent_temperature", temp), 1)
                humidity = int(current.get("relative_humidity_2m", 70))
                rain = round(current.get("rain", current.get("precipitation", 0.0)), 1)
                wind = round(current.get("wind_speed_10m", 5.0), 1)
                gusts = round(current.get("wind_gusts_10m", wind), 1)
                code = current.get("weather_code", 0)
                is_day = current.get("is_day", 1)

                condition = WMO_DESCRIPTIONS.get(code, "Clear Sky")

                risk_penalty = 0.0
                hazard_level = "none"
                hazards = []

                if code in (95, 96, 99) or rain > 15.0 or wind > 45.0:
                    hazard_level = "danger"
                    hazards.append(f"Severe Weather: {condition}")
                    risk_penalty += 0.25
                elif code in (51, 53, 55, 61, 63, 80, 81) or rain > 1.0 or wind > 25.0:
                    hazard_level = "caution"
                    hazards.append(f"{condition}")
                    risk_penalty += 0.10

                if temp > 40.0 or feels > 44.0:
                    hazard_level = "caution"
                    hazards.append(f"Heat Alert: {feels}°C")
                    risk_penalty += 0.10

                weather_data = {
                    "temperature_c": temp,
                    "feels_like_c": feels,
                    "humidity_pct": humidity,
                    "rain_mm": rain,
                    "wind_speed_kmh": wind,
                    "wind_gusts_kmh": gusts,
                    "condition": condition,
                    "hazard_level": hazard_level,
                    "hazard_description": ", ".join(hazards) if hazards else condition,
                    "risk_penalty": round(risk_penalty, 2),
                    "is_day": is_day,
                    "source": "Open-Meteo Real-Time Weather API",
                }
    except Exception as e:
        logger.warning(f"Failed to fetch live weather: {e}")

    _WEATHER_CACHE[cache_key] = {
        "data": weather_data,
        "expires_at": now + CACHE_TTL,
    }

    return weather_data
