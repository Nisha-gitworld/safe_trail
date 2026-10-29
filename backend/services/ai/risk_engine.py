"""
AI Risk Engine
─────────────
Predicts a danger score (0–100) using:
  • XGBoost classifier (tabular features)
  • Isolation Forest (anomaly detection)
  • Cyclic time encoding (hour of day)

In production, load pre-trained models from disk.
For the MVP / demo, a rule-based fallback is included.
"""
import numpy as np
import os
import logging
from pathlib import Path
from models.schemas import LocationFeature, RiskResponse
from datetime import datetime

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models" / "artifacts"


def encode_time(hour: int) -> tuple[float, float]:
    """Cyclic encoding so 23:00 and 00:00 are adjacent in feature space."""
    return (
        float(np.sin(2 * np.pi * hour / 24)),
        float(np.cos(2 * np.pi * hour / 24)),
    )


def rule_based_score(feat: LocationFeature) -> float:
    """
    Heuristic risk score for demo / when models are not trained yet.
    Returns a value 0.0 – 1.0.
    """
    score = 0.0
    # Night hours are riskier
    if feat.hour >= 22 or feat.hour <= 5:
        score += 0.35
    elif 20 <= feat.hour < 22 or 5 < feat.hour <= 7:
        score += 0.15
    # High dwell time in one spot
    if feat.dwell_time > 600:
        score += 0.25
    elif feat.dwell_time > 300:
        score += 0.10
    # Very slow movement (stationary)
    if feat.speed < 0.3:
        score += 0.15
    # High crowd density
    score += feat.crowd_density * 0.25
    return min(score, 1.0)


def predict_risk(feat: LocationFeature) -> RiskResponse:
    """
    Main prediction function.
    Tries trained models first; falls back to rule-based scorer.
    """
    sin_h, cos_h = encode_time(feat.hour)
    X = np.array([[
        feat.lat, feat.lng, feat.speed,
        feat.dwell_time, sin_h, cos_h,
        feat.crowd_density,
    ]], dtype=np.float32)

    base_prob = rule_based_score(feat)  # default

    # ── Try loading trained models ──────────────────────────────────────────
    try:
        import joblib
        xgb_path    = MODELS_DIR / "xgb_risk.pkl"
        scaler_path = MODELS_DIR / "scaler.pkl"
        iso_path    = MODELS_DIR / "isolation_forest.pkl"

        if xgb_path.exists() and scaler_path.exists():
            scaler      = joblib.load(scaler_path)
            xgb_model   = joblib.load(xgb_path)
            X_scaled    = scaler.transform(X)
            base_prob   = float(xgb_model.predict_proba(X_scaled)[0][1])

            if iso_path.exists():
                iso_model = joblib.load(iso_path)
                anomaly   = iso_model.decision_function(X_scaled)[0]
                if anomaly < -0.15:
                    base_prob = min(1.0, base_prob * 1.30)

    except Exception as e:
        logger.warning(f"Model load failed, using heuristic: {e}")

    danger_score = round(base_prob * 100, 2)

    # ── Classify & respond ──────────────────────────────────────────────────
    if danger_score < 40:
        zone_type   = "safe"
        alert_level = 0
        rec         = "All clear — enjoy your visit!"
    elif danger_score < 70:
        zone_type   = "caution"
        alert_level = 1
        rec         = "Stay alert. Avoid isolated areas and keep valuables secure."
    else:
        zone_type   = "danger"
        alert_level = 2
        rec         = "High risk detected. Move to a safe zone immediately."

    return RiskResponse(
        danger_score=danger_score,
        zone_type=zone_type,
        alert_level=alert_level,
        recommendation=rec,
    )


async def predict_risk_live(feat: LocationFeature) -> RiskResponse:
    """
    Live prediction pipeline incorporating real-time telemetry:
    • Live weather hazards from Open-Meteo
    • Real nearby police & hospital infrastructure from OpenStreetMap
    • Adaptive distance-based risk scoring
    """
    import asyncio
    from services.external.weather_service import fetch_live_weather
    from services.external.osm_service import fetch_nearby_emergency_services

    # Base score
    base_res = predict_risk(feat)
    danger_score = base_res.danger_score

    # Fetch live feeds concurrently
    weather_task = fetch_live_weather(feat.lat, feat.lng)
    osm_task = fetch_nearby_emergency_services(feat.lat, feat.lng, radius_meters=3000)

    weather_data, osm_data = await asyncio.gather(weather_task, osm_task, return_exceptions=True)

    weather_hazard = None
    nearest_police_str = None
    nearest_med_str = None
    recs = [base_res.recommendation]

    # Process weather adjustments
    if isinstance(weather_data, dict):
        if weather_data.get("hazard_level") in ("caution", "danger"):
            penalty_pts = weather_data.get("risk_penalty", 0.0) * 100
            danger_score += penalty_pts
            weather_hazard = weather_data.get("hazard_description")
            recs.append(f"Weather alert: {weather_hazard}.")

    # Process OpenStreetMap emergency infrastructure
    if isinstance(osm_data, dict):
        nearest_pol = osm_data.get("nearest_police")
        nearest_med = osm_data.get("nearest_medical")

        if nearest_pol:
            dist_p = nearest_pol["distance_meters"]
            nearest_police_str = f"{nearest_pol['name']} ({dist_p}m)"
            if dist_p < 400:
                danger_score -= 12  # Safety boost near police station
        else:
            danger_score += 10  # Isolated from police coverage

        if nearest_med:
            dist_m = nearest_med["distance_meters"]
            nearest_med_str = f"{nearest_med['name']} ({dist_m}m)"
            if dist_m < 400:
                danger_score -= 8   # Quick medical access buffer
        else:
            danger_score += 5

        if osm_data.get("is_isolated"):
            danger_score += 15
            recs.append("Isolated area: No emergency services within 3 km.")

    # Clamp final score
    danger_score = round(max(5.0, min(99.0, danger_score)), 2)

    if danger_score < 40:
        zone_type = "safe"
        alert_level = 0
    elif danger_score < 70:
        zone_type = "caution"
        alert_level = 1
    else:
        zone_type = "danger"
        alert_level = 2

    return RiskResponse(
        danger_score=danger_score,
        zone_type=zone_type,
        alert_level=alert_level,
        recommendation=" ".join(recs),
        weather_hazard=weather_hazard,
        nearest_police=nearest_police_str,
        nearest_medical=nearest_med_str,
    )

