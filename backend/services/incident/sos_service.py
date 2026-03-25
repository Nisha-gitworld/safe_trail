"""
SOS Dispatch Service
─────────────────────
Handles the full SOS trigger pipeline:
  1. FCM push to emergency responders
  2. Twilio SMS
  3. Mock Police API
  4. Mock Hospital API (if MEDICAL)
  5. Saves incident to MongoDB
"""
import logging
import httpx
from datetime import datetime
from models.schemas import SOSRequest, SOSResponse
from database.db import incidents_collection
from config import settings

logger = logging.getLogger(__name__)


def _maps_link(lat: float, lng: float) -> str:
    return f"https://maps.google.com/?q={lat},{lng}"


async def _send_fcm(payload: SOSRequest, incident_type: str):
    """Send FCM push notification to emergency responder topic."""
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT)
            firebase_admin.initialize_app(cred)

        message = messaging.Message(
            topic=f"emergency_responders_{settings.CITY_CODE}",
            notification=messaging.Notification(
                title="🚨 Tourist Emergency",
                body=f"{incident_type} at {_maps_link(payload.lat, payload.lng)}",
            ),
            data={
                "lat":          str(payload.lat),
                "lng":          str(payload.lng),
                "type":         incident_type,
                "user_id":      payload.user_id,
                "blockchain_did": payload.blockchain_did or "",
            },
        )
        messaging.send(message)
        logger.info("FCM push sent")
    except Exception as e:
        logger.warning(f"FCM push failed: {e}")


async def _send_sms(payload: SOSRequest, incident_type: str):
    """Send Twilio SMS to emergency contact."""
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        body = (
            f"🚨 TOURIST SOS | {incident_type}\n"
            f"Location: {_maps_link(payload.lat, payload.lng)}\n"
            f"DID: {payload.blockchain_did or 'N/A'}\n"
            f"Time: {datetime.utcnow().isoformat()}Z"
        )
        client.messages.create(
            body=body,
            from_=settings.TWILIO_FROM,
            to=settings.EMERGENCY_CONTACT_NUMBER,
        )
        logger.info("SMS sent via Twilio")
    except Exception as e:
        logger.warning(f"Twilio SMS failed: {e}")


async def _notify_police(payload: SOSRequest, incident_type: str):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{settings.POLICE_API_URL}/incidents", json={
                "location":    {"lat": payload.lat, "lng": payload.lng},
                "type":        incident_type,
                "did":         payload.blockchain_did,
                "timestamp":   datetime.utcnow().isoformat(),
            })
        logger.info("Police API notified")
    except Exception as e:
        logger.warning(f"Police API unreachable (mock): {e}")


async def _notify_hospital(payload: SOSRequest):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{settings.HOSPITAL_API_URL}/ambulance", json={
                "location": {"lat": payload.lat, "lng": payload.lng},
                "did":      payload.blockchain_did,
            })
        logger.info("Hospital API notified (ambulance requested)")
    except Exception as e:
        logger.warning(f"Hospital API unreachable (mock): {e}")


async def trigger_sos(payload: SOSRequest, incident_type: str = "ACCIDENT") -> SOSResponse:
    """
    Main SOS trigger — runs all notification channels concurrently.
    """
    import asyncio

    notified = []
    tasks = [
        _send_fcm(payload, incident_type),
        _send_sms(payload, incident_type),
        _notify_police(payload, incident_type),
    ]
    if incident_type == "MEDICAL":
        tasks.append(_notify_hospital(payload))

    await asyncio.gather(*tasks, return_exceptions=True)
    notified = ["fcm", "sms", "police"] + (["hospital"] if incident_type == "MEDICAL" else [])

    # Persist to MongoDB
    doc = {
        "user_id":      payload.user_id,
        "lat":          payload.lat,
        "lng":          payload.lng,
        "incident_type":incident_type,
        "description":  payload.description,
        "blockchain_did":payload.blockchain_did,
        "notified_to":  notified,
        "status":       "open",
        "created_at":   datetime.utcnow(),
    }
    result = await incidents_collection.insert_one(doc)

    return SOSResponse(
        incident_id=str(result.inserted_id),
        dispatched=True,
        notified_to=notified,
        timestamp=datetime.utcnow(),
    )
