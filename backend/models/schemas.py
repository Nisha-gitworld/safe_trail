"""
Pydantic Schemas — Request & Response Models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# ── Auth ─────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email:          EmailStr
    password:       str = Field(min_length=8)
    full_name:      str
    nationality:    Optional[str] = None
    phone:          Optional[str] = None
    blood_type:     Optional[str] = None
    allergies:      Optional[str] = None
    embassy_contact:Optional[str] = None


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    token_type:    str = "bearer"
    expires_in:    int = 900  # 15 min


# ── Risk ─────────────────────────────────────────────────────────────────────
class LocationFeature(BaseModel):
    lat:           float = Field(ge=-90,  le=90)
    lng:           float = Field(ge=-180, le=180)
    speed:         float = Field(ge=0, default=0.0)     # m/s
    dwell_time:    int   = Field(ge=0, default=0)       # seconds
    hour:          int   = Field(ge=0, le=23)
    crowd_density: float = Field(ge=0.0, le=1.0, default=0.3)
    user_id:       str


class RiskResponse(BaseModel):
    danger_score:   float   # 0–100
    zone_type:      str     # safe | caution | danger
    alert_level:    int     # 0=none, 1=push, 2=SMS, 3=SOS
    recommendation: str
    weather_hazard: Optional[str] = None
    nearest_police: Optional[str] = None
    nearest_medical:Optional[str] = None
    timestamp:      datetime = Field(default_factory=datetime.utcnow)


# ── Geofence ─────────────────────────────────────────────────────────────────
class GeofenceCheckRequest(BaseModel):
    lat:     float
    lng:     float
    user_id: str


class GeofenceCheckResponse(BaseModel):
    in_danger_zone: bool
    zone_name:      Optional[str]
    risk_level:     str
    dwell_pings:    int
    should_escalate:bool


class ZoneCreate(BaseModel):
    zone_name:   str
    city:        str
    risk_level:  str
    danger_score:float = 50.0
    boundary_wkt:str   # POLYGON((lng lat, ...))


# ── Incident ─────────────────────────────────────────────────────────────────
class SOSRequest(BaseModel):
    user_id:        str
    lat:            float
    lng:            float
    incident_type:  Optional[str] = None
    description:    Optional[str] = None
    blockchain_did: Optional[str] = None


class SOSResponse(BaseModel):
    incident_id:   str
    dispatched:    bool
    notified_to:   list[str]
    timestamp:     datetime


class IncidentClassifyRequest(BaseModel):
    text: str   # Voice transcript or text description


class IncidentClassifyResponse(BaseModel):
    incident_type: str
    confidence:    float
    priority:      int
    route_to:      str


# ── Identity ─────────────────────────────────────────────────────────────────
class DIDRegisterRequest(BaseModel):
    user_id:    str
    ipfs_cid:   str
    data_hash:  str


class DIDRegisterResponse(BaseModel):
    did:         str
    tx_hash:     str
    ipfs_cid:    str
    registered:  bool
