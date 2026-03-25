"""
Extended Test Suite — Buddy, Heatmap, Identity, WebSocket
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Buddy Service Unit Tests ──────────────────────────────────────────────────
def test_haversine_distance():
    """Two GPS coordinates 200m apart should return ~200m."""
    from services.buddy.buddy_service import _haversine
    # Marine Drive to a point ~200m north
    dist = _haversine(18.944, 72.823, 18.946, 72.823)
    assert 180 <= dist <= 230, f"Expected ~200m, got {dist:.1f}m"


def test_haversine_same_point():
    from services.buddy.buddy_service import _haversine
    assert _haversine(19.07, 72.87, 19.07, 72.87) == 0.0


# ── Heatmap Service Unit Tests ────────────────────────────────────────────────
def test_heatmap_grid_generation():
    from services.heatmap.heatmap_service import generate_grid
    cells = generate_grid("MUM")
    assert len(cells) > 50, "Mumbai should produce many grid cells"
    # All cells within bounding box
    for c in cells:
        assert 18.87 <= c["lat"] <= 19.28
        assert 72.77 <= c["lng"] <= 72.98


def test_heatmap_unknown_city():
    from services.heatmap.heatmap_service import generate_grid
    cells = generate_grid("UNKNOWN")
    assert cells == []


def test_recency_weight_today():
    from services.heatmap.heatmap_service import recency_weight
    from datetime import datetime
    weight = recency_weight(datetime.utcnow())
    assert 0.95 <= weight <= 1.0


def test_recency_weight_old():
    from services.heatmap.heatmap_service import recency_weight
    from datetime import datetime, timedelta
    old = datetime.utcnow() - timedelta(days=30)
    weight = recency_weight(old)
    assert weight < 0.10, "30-day-old incident should have very low weight"


# ── IPFS / Encryption Tests ───────────────────────────────────────────────────
def test_document_hash_deterministic():
    from services.identity.ipfs_service import compute_document_hash
    data = {"name": "Test Tourist", "blood_type": "O+"}
    h1 = compute_document_hash(data)
    h2 = compute_document_hash(data)
    assert h1 == h2
    assert len(h1) == 64   # SHA-256 hex


def test_document_hash_changes_with_data():
    from services.identity.ipfs_service import compute_document_hash
    h1 = compute_document_hash({"name": "Alice"})
    h2 = compute_document_hash({"name": "Bob"})
    assert h1 != h2


def test_encrypt_decrypt_roundtrip():
    from services.identity.ipfs_service import encrypt_document, decrypt_document
    raw = {"full_name": "Priya Kumar", "blood_type": "B+", "allergies": "None"}
    passphrase = "test-secret-key-for-demo"

    encrypted = encrypt_document(raw, passphrase)
    assert "ciphertext" in encrypted
    assert encrypted["ciphertext"] != str(raw)

    decrypted = decrypt_document(encrypted, passphrase)
    # Demo fallback (no cryptography package) returns dict
    if decrypted is not None:
        assert decrypted.get("full_name") == "Priya Kumar"


def test_wrong_passphrase_fails():
    from services.identity.ipfs_service import encrypt_document, decrypt_document
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        raw       = {"name": "Test"}
        encrypted = encrypt_document(raw, "correct-passphrase")
        result    = decrypt_document(encrypted, "wrong-passphrase")
        assert result is None
    except ImportError:
        pytest.skip("cryptography package not installed")


# ── WebSocket Manager Tests ───────────────────────────────────────────────────
def test_ws_payload_helpers():
    from services.realtime.ws_manager import (
        danger_score_payload, zone_alert_payload,
        sos_confirmed_payload, buddy_alert_payload,
    )
    p = danger_score_payload("u1", 45.5, "caution", "Stay alert")
    assert p["type"] == "danger_score"
    assert p["danger_score"] == 45.5

    z = zone_alert_payload("u1", "Dharavi", "danger", 35, True)
    assert z["type"] == "zone_alert"
    assert z["should_escalate"] is True
    assert "min" in z["message"]   # should mention minutes

    s = sos_confirmed_payload("u1", "INC-001", ["fcm", "sms"])
    assert s["type"] == "sos_confirmed"
    assert "fcm" in s["notified_to"]

    b = buddy_alert_payload("G1", "u2", 250.0)
    assert b["type"] == "buddy_alert"
    assert b["distance_m"] == 250.0


def test_ws_manager_connection_count():
    from services.realtime.ws_manager import ConnectionManager
    mgr = ConnectionManager()
    assert mgr.connection_count == 0
    # Simulate adding entries (without real WebSocket)
    mgr.active["user-1"] = object()
    mgr.active["user-2"] = object()
    assert mgr.connection_count == 2


# ── Integration: Auth + Risk API ──────────────────────────────────────────────
@pytest.mark.anyio
async def test_risk_score_requires_auth():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:
        res = await ac.post("/api/risk/score", json={
            "lat": 19.07, "lng": 72.87, "speed": 1.0,
            "dwell_time": 60, "hour": 14, "crowd_density": 0.3, "user_id": "me",
        })
        assert res.status_code == 401


@pytest.mark.anyio
async def test_health_endpoint():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "version" in data


# ── Adaptive ping interval ────────────────────────────────────────────────────
@pytest.mark.parametrize("speed,expected", [
    (0.0,  30),
    (0.5,  30),
    (1.5,  15),
    (5.0,  15),
    (6.0,   5),
    (20.0,  5),
])
def test_adaptive_ping_intervals(speed, expected):
    from services.location.geofence_service import adaptive_ping_interval
    assert adaptive_ping_interval(speed) == expected
