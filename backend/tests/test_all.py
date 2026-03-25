"""
Backend Test Suite — pytest + httpx AsyncClient
Run: pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# ── Health ────────────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# ── Risk Engine ───────────────────────────────────────────────────────────────
def test_risk_rule_based_safe():
    from services.ai.risk_engine import rule_based_score
    from models.schemas import LocationFeature
    feat = LocationFeature(
        lat=19.076, lng=72.877, speed=2.0,
        dwell_time=60, hour=14, crowd_density=0.2, user_id="test"
    )
    score = rule_based_score(feat)
    assert 0.0 <= score <= 1.0
    assert score < 0.5   # daytime, moving, low crowd → should be safe


def test_risk_rule_based_danger():
    from services.ai.risk_engine import rule_based_score
    from models.schemas import LocationFeature
    feat = LocationFeature(
        lat=19.040, lng=72.855, speed=0.1,
        dwell_time=700, hour=23, crowd_density=0.9, user_id="test"
    )
    score = rule_based_score(feat)
    assert score > 0.5   # night, stationary, high crowd → risky


def test_predict_risk_returns_valid():
    from services.ai.risk_engine import predict_risk
    from models.schemas import LocationFeature
    feat = LocationFeature(
        lat=19.076, lng=72.877, speed=1.5,
        dwell_time=120, hour=10, crowd_density=0.3, user_id="test"
    )
    result = predict_risk(feat)
    assert 0 <= result.danger_score <= 100
    assert result.zone_type in ("safe", "caution", "danger")
    assert result.alert_level in (0, 1, 2, 3)
    assert len(result.recommendation) > 0


# ── Incident Classifier ───────────────────────────────────────────────────────
def test_classify_theft():
    from services.incident.classifier import classify_incident, keyword_classify
    incident_type, confidence = keyword_classify("I was robbed at the market")
    assert incident_type == "THEFT"
    assert confidence > 0.5


def test_classify_medical():
    from services.incident.classifier import keyword_classify
    incident_type, _ = keyword_classify("I can't breathe and my chest hurts")
    assert incident_type == "MEDICAL"


def test_classify_accident():
    from services.incident.classifier import keyword_classify
    incident_type, _ = keyword_classify("There was a car crash on the road")
    assert incident_type == "ACCIDENT"


def test_classify_lost():
    from services.incident.classifier import keyword_classify
    incident_type, _ = keyword_classify("I am lost and don't know where I am")
    assert incident_type == "LOST"


# ── Geofence Service ──────────────────────────────────────────────────────────
def test_adaptive_ping_interval():
    from services.location.geofence_service import adaptive_ping_interval
    assert adaptive_ping_interval(10.0) == 5    # fast → 5s
    assert adaptive_ping_interval(2.0)  == 15   # walking → 15s
    assert adaptive_ping_interval(0.1)  == 30   # stationary → 30s


# ── Auth Service ──────────────────────────────────────────────────────────────
def test_password_hashing():
    from services.auth_service import hash_password, verify_password
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"
    assert verify_password("mysecretpassword", hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_access_token():
    from services.auth_service import create_access_token
    from jose import jwt
    from config import settings
    token = create_access_token("user-123", "test@example.com")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"


# ── Training Data ─────────────────────────────────────────────────────────────
def test_generate_training_data():
    from services.ai.train import generate_training_data
    df = generate_training_data(n=100)
    assert len(df) == 100
    assert set(df.columns) >= {"lat", "lng", "speed", "dwell_time",
                                "sin_hour", "cos_hour", "crowd_density", "label"}
    assert df["label"].isin([0, 1]).all()
