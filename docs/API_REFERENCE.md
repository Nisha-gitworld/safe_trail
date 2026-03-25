# SafeTrail API Reference

Base URL: `http://localhost:8000/api`  
Auth: `Bearer <JWT>` header on all protected routes  
Interactive docs: `http://localhost:8000/docs`

---

## Authentication

### POST `/auth/register`
Register a new tourist account.

**Body**
```json
{
  "email": "tourist@example.com",
  "password": "min8chars",
  "full_name": "Priya Kumar",
  "nationality": "Indian",
  "blood_type": "O+",
  "allergies": "Penicillin",
  "embassy_contact": "+91-11-2301-4000"
}
```
**Response `201`**
```json
{ "message": "User registered successfully", "user_id": "uuid" }
```

---

### POST `/auth/login`
**Body** `{ "email": "...", "password": "..." }`  
**Response** `{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 900 }`

---

## Risk AI

### POST `/risk/score` 🔒
Predict danger score for a GPS location.

**Body**
```json
{
  "lat": 19.076, "lng": 72.877,
  "speed": 1.5,
  "dwell_time": 120,
  "hour": 23,
  "crowd_density": 0.8,
  "user_id": "me"
}
```
**Response**
```json
{
  "danger_score": 74.5,
  "zone_type": "danger",
  "alert_level": 2,
  "recommendation": "High risk detected. Move to a safe zone immediately."
}
```

| `danger_score` | `zone_type` | `alert_level` | Action |
|---|---|---|---|
| 0–39  | safe    | 0 | None |
| 40–69 | caution | 1 | Push notification |
| 70–100| danger  | 2 | SMS + push |

---

### GET `/risk/heatmap?city=MUM` 🔒
Returns grid cells for the city safety heatmap.

**Response**
```json
{
  "city": "MUM",
  "cell_count": 320,
  "cells": [
    { "lat": 19.076, "lng": 72.877, "score": 74.1, "weight": 0.741 }
  ]
}
```
`weight` (0.0–1.0) maps directly to Google Maps `HeatmapLayer` intensity.

---

## Geofence

### POST `/geofence/check` 🔒
Check if tourist is inside a risk zone. Call on every GPS ping.

**Body** `{ "lat": 19.042, "lng": 72.851, "user_id": "me" }`

**Response**
```json
{
  "in_danger_zone": true,
  "zone_name": "Dharavi High Risk Zone",
  "risk_level": "danger",
  "dwell_pings": 18,
  "should_escalate": false
}
```
`should_escalate` becomes `true` when `dwell_pings >= 30` (5 minutes).

---

### GET `/geofence/zones?city=MUM` 🔒
Returns all active zones (cache client-side for offline use).

---

### POST `/geofence/zones` 🔒
Create a new geofence zone (admin).

**Body**
```json
{
  "zone_name": "Old Market Area",
  "city": "MUM",
  "risk_level": "caution",
  "danger_score": 55.0,
  "boundary_wkt": "POLYGON((72.82 18.92, 72.85 18.92, 72.85 18.95, 72.82 18.95, 72.82 18.92))"
}
```

---

## Incident & SOS

### POST `/incident/sos` 🔒
Trigger emergency SOS — dispatches FCM push, SMS, police API, hospital API.

**Body**
```json
{
  "user_id": "me",
  "lat": 19.045, "lng": 72.856,
  "incident_type": "THEFT",
  "description": "Wallet stolen at Crawford Market",
  "blockchain_did": "did:polygon:0x8f3a...4d2c"
}
```
**Response**
```json
{
  "incident_id": "ObjectId",
  "dispatched": true,
  "notified_to": ["fcm", "sms", "police"],
  "timestamp": "2024-01-01T22:14:00Z"
}
```

---

### POST `/incident/classify` 🔒
Classify incident type from text description.

**Body** `{ "text": "I was robbed near the train station" }`

**Response**
```json
{
  "incident_type": "THEFT",
  "confidence": 0.91,
  "priority": 1,
  "route_to": "police"
}
```

---

### POST `/incident/voice-sos` 🔒
Upload voice recording → Whisper transcription → auto classify → SOS dispatch.

**Form data**: `audio` (file), `lat` (float), `lng` (float)

---

### GET `/incident/list?status=open` 🔒
Returns user's incident history.

---

## Digital Identity (Blockchain)

### POST `/identity/register` 🔒
Register DID on Polygon — stores IPFS CID on-chain.

**Body**
```json
{
  "user_id": "me",
  "ipfs_cid": "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP",
  "data_hash": "sha256hexstring"
}
```

---

### GET `/identity/profile` 🔒
Returns public DID metadata (no raw personal data).

---

### POST `/identity/grant-access?authority_address=0x...` 🔒
Pre-authorise emergency authority wallet address.

---

## Buddy System

### POST `/buddy/groups` 🔒
Create a tour group.  
**Body** `{ "group_name": "Heritage Tour", "city": "MUM" }`  
**Response** `{ "group_id": "A3F2BC", "join_code": "A3F2BC" }`

### POST `/buddy/groups/{group_id}/join` 🔒
Join an existing group by code.

### POST `/buddy/groups/location` 🔒
Update member location + receive proximity alerts.

**Body**
```json
{ "group_id": "A3F2BC", "lat": 19.07, "lng": 72.87, "danger_score": 34.0 }
```
**Response** `{ "alerts": [...], "alert_count": 0 }`

### POST `/buddy/checkin` 🔒
Record a safety check-in (resets 2-hour dead-man timer).

### GET `/buddy/groups/{group_id}/status` 🔒
Full group status for tour guide dashboard.

---

## WebSocket (Real-time)

### `ws://localhost:8000/ws/{user_id}?token=JWT&city=MUM`

**Client → Server** (send every GPS ping):
```json
{ "lat": 19.07, "lng": 72.87, "speed": 1.5, "hour": 14, "dwell_time": 120 }
```

**Server → Client** message types:

| `type` | Description |
|---|---|
| `connected` | Initial handshake confirmation |
| `danger_score` | Risk score update for current location |
| `zone_alert` | Entered or dwelling in a risk zone |
| `sos_confirmed` | SOS dispatched confirmation |
| `buddy_alert` | Group member separated |
| `city_alert` | Admin broadcast to all city tourists |
| `ping` | Keepalive (respond with any message) |

---

## Heatmap

### GET `/heatmap/{city}` 🔒
Build/retrieve cached heatmap. Cities: `MUM`, `DEL`, `BLR`.

### POST `/heatmap/{city}/invalidate` 🔒
Force cache rebuild (called automatically after new SOS).

---

## Health

### GET `/health`
```json
{ "status": "ok", "service": "SafeTrail API", "version": "1.0.0" }
```

### GET `/ws/stats`
```json
{ "total_connections": 42, "cities": { "MUM": 38, "DEL": 4 } }
```
