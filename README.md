# SafeTrail 🛡️ — Smart Tourist Safety Monitoring System

AI · Geo-Fencing · Blockchain Digital ID · Emergency Response

---

## Project Structure

```
safetrail/
├── backend/          # FastAPI + Node.js microservices (Python)
├── blockchain/       # Solidity smart contracts (Hardhat)
├── mobile/           # Flutter app
├── frontend/         # React admin dashboard
├── docker/           # Docker configs
└── .vscode/          # VS Code workspace settings
```

---

## Quick Start

### 1. Backend (Python / FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # fill in your values
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Blockchain (Hardhat)

```bash
cd blockchain
npm install
npx hardhat compile
npx hardhat test
npx hardhat run scripts/deploy.js --network mumbai
```

### 3. Mobile (Flutter)

```bash
cd mobile
flutter pub get
flutter run
```

### 4. Frontend Admin Dashboard (React)

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

Copy `.env.example` → `.env` in each service folder and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `TWILIO_SID` | Twilio Account SID |
| `TWILIO_TOKEN` | Twilio Auth Token |
| `TWILIO_FROM` | Twilio phone number |
| `EMERGENCY_CONTACT_NUMBER` | Default emergency number |
| `FIREBASE_SERVICE_ACCOUNT` | FCM service account JSON path |
| `POLYGON_RPC_URL` | Polygon Mumbai RPC (e.g. Alchemy) |
| `PRIVATE_KEY` | Wallet private key for deployment |
| `OPENAI_API_KEY` | For Whisper voice transcription |
| `GOOGLE_MAPS_API_KEY` | Maps SDK key |

---

## Tech Stack

| Layer | Tech |
|---|---|
| Mobile | Flutter 3 + Dart |
| Backend API | FastAPI (Python 3.11) |
| AI / ML | scikit-learn · XGBoost · transformers · torch |
| Database | PostgreSQL + PostGIS · MongoDB · Redis |
| Blockchain | Polygon PoS · Solidity 0.8 · Hardhat · ethers.js |
| Storage | IPFS via Web3.Storage |
| Notifications | Twilio (SMS) + Firebase FCM |
| Admin UI | React 18 + Vite + Tailwind CSS |

---

## Demo Scenarios

1. **Tourist enters unsafe zone** → risk score > 70 → push alert fires in < 3s
2. **Voice SOS trigger** → "Help!" → Whisper transcribes → BERT classifies → SOS dispatched
3. **Authority accesses DID** → smart contract `grantEmergencyAccess()` → IPFS doc revealed

---

## License

MIT — Built for academic/hackathon use.
