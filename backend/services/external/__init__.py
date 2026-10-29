"""External real-time data feeds for SafeTrail."""
from .osm_service import fetch_nearby_emergency_services
from .weather_service import fetch_live_weather

__all__ = ["fetch_nearby_emergency_services", "fetch_live_weather"]
