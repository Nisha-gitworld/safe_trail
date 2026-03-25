"""
Incident Classifier
────────────────────
Classifies tourist incident descriptions into categories using:
  • Keyword fallback (always available, zero dependencies)
  • HuggingFace DistilBERT (if transformers is installed)
  • OpenAI Whisper (optional — for voice-to-text input)
"""
import logging
import re
from models.schemas import IncidentClassifyRequest, IncidentClassifyResponse

logger = logging.getLogger(__name__)


# ── Incident metadata ─────────────────────────────────────────────────────────
INCIDENT_META = {
    "ACCIDENT":   {"priority": 2, "route_to": "hospital",        "color": "#FAC775"},
    "THEFT":      {"priority": 1, "route_to": "police",          "color": "#F09595"},
    "MEDICAL":    {"priority": 0, "route_to": "hospital",        "color": "#E24B4A"},
    "HARASSMENT": {"priority": 1, "route_to": "police",          "color": "#F09595"},
    "LOST":       {"priority": 3, "route_to": "tourist_helpline","color": "#85B7EB"},
}

KEYWORD_MAP = {
    r"\b(accident|crash|collision|fell|fall|hit)\b":       "ACCIDENT",
    r"\b(steal|stole|stolen|rob|robbed|pickpocket|theft)\b":"THEFT",
    r"\b(chest|breath|breathing|unconscious|faint|heart|seizure|bleed)\b":"MEDICAL",
    r"\b(harass|follow|stalk|threaten|assault|attack)\b":  "HARASSMENT",
    r"\b(lost|missing|can't find|separated|don't know)\b": "LOST",
}


def keyword_classify(text: str) -> tuple[str, float]:
    """Fast regex-based classification — always works offline."""
    text_lower = text.lower()
    for pattern, incident_type in KEYWORD_MAP.items():
        if re.search(pattern, text_lower):
            return incident_type, 0.85
    return "ACCIDENT", 0.50   # safe default


def classify_incident(req: IncidentClassifyRequest) -> IncidentClassifyResponse:
    """
    Classify incident from text.
    Tries DistilBERT pipeline first; falls back to keyword matching.
    """
    text = req.text[:512]
    incident_type, confidence = keyword_classify(text)

    # ── Try HuggingFace pipeline ────────────────────────────────────────────
    try:
        from transformers import pipeline as hf_pipeline
        # In production: replace with your fine-tuned model
        # model = "safetrail/incident-classifier"
        classifier = hf_pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )
        candidate_labels = list(INCIDENT_META.keys())
        result = classifier(text, candidate_labels)
        incident_type = result["labels"][0]
        confidence    = float(result["scores"][0])
        logger.info(f"HuggingFace classified as: {incident_type} ({confidence:.2f})")

    except Exception as e:
        logger.warning(f"HuggingFace unavailable, using keywords: {e}")

    meta = INCIDENT_META[incident_type]
    return IncidentClassifyResponse(
        incident_type=incident_type,
        confidence=round(confidence, 3),
        priority=meta["priority"],
        route_to=meta["route_to"],
    )


# ── Optional: Whisper voice-to-text ─────────────────────────────────────────
async def transcribe_voice(audio_bytes: bytes, language: str = "en") -> str:
    """
    Transcribe audio via OpenAI Whisper API.
    Returns plain text transcript.
    """
    try:
        from openai import AsyncOpenAI
        from config import settings
        import io

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "sos.webm"

        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
        )
        return transcript.text

    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return ""
