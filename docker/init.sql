-- SafeTrail PostgreSQL init script
-- Runs automatically on first docker-compose up

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create geofence_zones table with PostGIS geometry column
CREATE TABLE IF NOT EXISTS geofence_zones (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_name     VARCHAR(200) NOT NULL,
    city          VARCHAR(100) NOT NULL,
    risk_level    VARCHAR(20)  NOT NULL CHECK (risk_level IN ('safe','caution','danger')),
    danger_score  FLOAT        DEFAULT 0.0,
    boundary_wkt  TEXT         NOT NULL,
    is_active     BOOLEAN      DEFAULT TRUE,
    created_at    TIMESTAMPTZ  DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  DEFAULT NOW()
);

-- Spatial index on boundary for fast containment queries
-- (Run after adding actual geometry column in production)
-- CREATE INDEX IF NOT EXISTS idx_geofence_boundary ON geofence_zones USING GIST (boundary);

-- Seed demo zones (Mumbai)
INSERT INTO geofence_zones (zone_name, city, risk_level, danger_score, boundary_wkt)
VALUES
    (
        'Dharavi High Risk Zone', 'MUM', 'danger', 82.0,
        'POLYGON((72.843 19.038, 72.865 19.038, 72.865 19.055, 72.843 19.055, 72.843 19.038))'
    ),
    (
        'Kurla Station Caution', 'MUM', 'caution', 58.0,
        'POLYGON((72.883 19.068, 72.900 19.068, 72.900 19.082, 72.883 19.082, 72.883 19.068))'
    ),
    (
        'Marine Drive Safe Zone', 'MUM', 'safe', 18.0,
        'POLYGON((72.818 18.940, 72.835 18.940, 72.835 18.955, 72.818 18.955, 72.818 18.940))'
    ),
    (
        'Colaba Market Caution', 'MUM', 'caution', 47.0,
        'POLYGON((72.827 18.900, 72.843 18.900, 72.843 18.914, 72.827 18.914, 72.827 18.900))'
    );

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    nationality     VARCHAR(100),
    phone           VARCHAR(30),
    blood_type      VARCHAR(10),
    allergies       TEXT,
    embassy_contact VARCHAR(100),
    wallet_address  VARCHAR(42),
    ipfs_cid        VARCHAR(100),
    did_registered  BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Create incidents table
CREATE TABLE IF NOT EXISTS incidents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    incident_type   VARCHAR(50) NOT NULL,
    lat             FLOAT NOT NULL,
    lng             FLOAT NOT NULL,
    description     TEXT,
    severity        INTEGER DEFAULT 2,
    status          VARCHAR(50) DEFAULT 'open',
    dispatched_to   VARCHAR(100),
    blockchain_tx   VARCHAR(100),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Create location_pings table
CREATE TABLE IF NOT EXISTS location_pings (
    id           SERIAL PRIMARY KEY,
    user_id      UUID REFERENCES users(id),
    lat          FLOAT NOT NULL,
    lng          FLOAT NOT NULL,
    speed        FLOAT DEFAULT 0.0,
    accuracy     FLOAT DEFAULT 10.0,
    danger_score FLOAT DEFAULT 0.0,
    zone_id      UUID REFERENCES geofence_zones(id),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pings_user    ON location_pings(user_id);
CREATE INDEX IF NOT EXISTS idx_pings_created ON location_pings(created_at);
CREATE INDEX IF NOT EXISTS idx_incidents_user ON incidents(user_id);

COMMENT ON TABLE geofence_zones  IS 'Dynamic geofence zones with PostGIS boundaries';
COMMENT ON TABLE users           IS 'Tourist accounts with blockchain DID references';
COMMENT ON TABLE incidents       IS 'SOS incidents and emergency events';
COMMENT ON TABLE location_pings  IS 'GPS ping history for risk scoring';
