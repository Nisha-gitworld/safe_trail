"""Routes — Incident & SOS"""
from fastapi import APIRouter, Depends, UploadFile, File
from models.schemas import (
    SOSRequest, SOSResponse,
    IncidentClassifyRequest, IncidentClassifyResponse,
)
from services.incident.sos_service import trigger_sos
from services.incident.classifier import classify_incident, transcribe_voice
from services.auth_service import get_current_user

router = APIRouter()


@router.post("/sos", response_model=SOSResponse)
async def sos_trigger(
    req: SOSRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/incident/sos
    One-tap SOS — dispatches to FCM, SMS, police, hospital.
    """
    req.user_id = current_user["user_id"]
    incident_type = req.incident_type or "ACCIDENT"
    return await trigger_sos(req, incident_type)


@router.post("/classify", response_model=IncidentClassifyResponse)
async def classify(
    req: IncidentClassifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/incident/classify
    Classify incident type from text description.
    """
    return classify_incident(req)


@router.post("/voice-sos", response_model=SOSResponse)
async def voice_sos(
    audio: UploadFile = File(...),
    lat: float = 0.0,
    lng: float = 0.0,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/incident/voice-sos
    Upload voice recording → Whisper transcription → classify → SOS dispatch.
    """
    audio_bytes = await audio.read()
    transcript  = await transcribe_voice(audio_bytes)

    classification = classify_incident(IncidentClassifyRequest(text=transcript))

    sos_req = SOSRequest(
        user_id=current_user["user_id"],
        lat=lat, lng=lng,
        incident_type=classification.incident_type,
        description=transcript,
    )
    return await trigger_sos(sos_req, classification.incident_type)


@router.get("/list")
async def list_incidents(
    status: str = "open",
    current_user: dict = Depends(get_current_user),
):
    """GET /api/incident/list — returns incident history for the user."""
    from database.db import incidents_collection
    cursor = incidents_collection.find(
        {"user_id": current_user["user_id"], "status": status},
        {"_id": 0},
    ).sort("created_at", -1).limit(20)

    incidents = await cursor.to_list(length=20)
    return {"incidents": incidents, "count": len(incidents)}


@router.get("/nearby-services")
async def get_nearby_emergency_services(
    lat: float,
    lng: float,
    radius: int = 3000,
):
    """
    GET /api/incident/nearby-services?lat=19.076&lng=72.877&radius=3000
    Fetches real police stations, hospitals, and clinics from OpenStreetMap.
    """
    from services.external.osm_service import fetch_nearby_emergency_services
    return await fetch_nearby_emergency_services(lat, lng, radius_meters=radius)

