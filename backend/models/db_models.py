"""
SQLAlchemy ORM Models
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean,
    DateTime, Text, Enum, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from database.db import Base
import enum


class RiskLevel(str, enum.Enum):
    safe    = "safe"
    caution = "caution"
    danger  = "danger"


class IncidentType(str, enum.Enum):
    accident   = "ACCIDENT"
    theft      = "THEFT"
    medical    = "MEDICAL"
    harassment = "HARASSMENT"
    lost       = "LOST"


class User(Base):
    __tablename__ = "users"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email          = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password= Column(String(255), nullable=False)
    full_name      = Column(String(255), nullable=False)
    nationality    = Column(String(100))
    phone          = Column(String(30))
    blood_type     = Column(String(10))
    allergies      = Column(Text)
    embassy_contact= Column(String(100))
    wallet_address = Column(String(42))   # Ethereum address
    ipfs_cid       = Column(String(100))  # Encrypted ID doc on IPFS
    did_registered = Column(Boolean, default=False)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=datetime.utcnow)


class GeofenceZone(Base):
    __tablename__ = "geofence_zones"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_name   = Column(String(200), nullable=False)
    city        = Column(String(100), nullable=False, index=True)
    risk_level  = Column(Enum(RiskLevel), nullable=False)
    danger_score= Column(Float, default=0.0)
    # boundary stored as WKT — PostGIS will handle spatial queries
    boundary_wkt= Column(Text, nullable=False)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Incident(Base):
    __tablename__ = "incidents"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    incident_type  = Column(Enum(IncidentType), nullable=False)
    lat            = Column(Float, nullable=False)
    lng            = Column(Float, nullable=False)
    description    = Column(Text)
    severity       = Column(Integer, default=2)   # 0=critical, 1=high, 2=medium, 3=low
    status         = Column(String(50), default="open")
    dispatched_to  = Column(String(100))          # police / hospital / helpline
    blockchain_tx  = Column(String(100))          # transaction hash
    resolved_at    = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)


class LocationPing(Base):
    __tablename__ = "location_pings"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    lat          = Column(Float, nullable=False)
    lng          = Column(Float, nullable=False)
    speed        = Column(Float, default=0.0)
    accuracy     = Column(Float, default=10.0)
    danger_score = Column(Float, default=0.0)
    zone_id      = Column(UUID(as_uuid=True), ForeignKey("geofence_zones.id"), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow, index=True)
