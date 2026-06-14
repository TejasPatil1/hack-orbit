# Hack Orbit — AI Mission Intelligence Copilot

> **Predict. Protect. Decide.**

Real-time AI-powered satellite operations dashboard. Integrates anomaly detection (IsolationForest), failure prediction (XGBoost), space weather monitoring, debris conjunction analysis, and an LLM-backed operations copilot — all with deterministic fallbacks so the demo always works.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`

---

## Environment Variables

Create `.env` in the project root (copy from `.env.example` if present):

```env
# HuggingFace — primary LLM provider (Kimi K2 via router.huggingface.co)
HF_TOKEN=hf_...
HF_MODEL=moonshotai/Kimi-K2.6:novita

# AWS Bedrock — optional fallback
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION_NAME=us-east-1
BEDROCK_MODEL=openai.gpt-oss-120b-1:0

# Anthropic — optional fallback
ANTHROPIC_API_KEY=

# Frontend (only needed for production; dev defaults to localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**No API keys required for demo.** The AI copilot and incident report fall back to a fully deterministic, context-aware rule engine when all LLM providers are unavailable.

---

## Demo Scenarios

Click the scenario buttons in the top bar to instantly switch the satellite's operational state:

| Scenario     | Score | What it demonstrates                                        |
|--------------|-------|-------------------------------------------------------------|
| Healthy      | ~92   | All systems nominal — low risk                              |
| Anomaly      | ~62   | Thruster temperature spike → anomaly detection fires        |
| Debris       | ~62   | Active conjunction event → avoidance maneuver advised       |
| Solar Storm  | ~54   | Kp 7 (G3 storm) → storm-gated maneuver logic               |
| Resolution   | ~99   | Operator intervention resolves all issues                   |

---

## Architecture

```
frontend/
  app/
    page.tsx              Dashboard — polling + layout
    globals.css           Space theme + animations
  components/
    MissionBrief.tsx      AI executive mission summary
    HealthScore.tsx       Score ring + risk drivers
    TelemetryPanel.tsx    Live sensor readings (1.5 s noise)
    WeatherPanel.tsx      Kp index + storm level
    DebrisPanel.tsx       Conjunction objects
    ForecastChart.tsx     7-day health forecast
    CopilotChat.tsx       LLM chat + incident report
    SystemStatus.tsx      Feed / connection status bar
    ScenarioSwitcher.tsx  Demo scenario selector
  lib/
    api.ts                Typed fetch wrappers

backend/
  app/
    main.py               FastAPI entry point + CORS
    state.py              In-memory scenario state
    api/
      health.py           GET /api/health-score
      telemetry.py        GET /api/telemetry
      weather.py          GET /api/weather
      debris.py           GET /api/debris
      forecast.py         GET /api/forecast
      mission_brief.py    GET /api/mission-brief
      ai.py               POST /api/copilot + detect + predict + maneuver
      anomaly.py          POST /api/inject-anomaly
    services/
      anomaly_detection/  IsolationForest (3σ fallback)
      failure_prediction/ XGBoost (sigmoid fallback)
      health_score/       Deterministic scorer
      ai_copilot/         LLM chain + fallback engine
      maneuver_planner/   Storm-gated recommendations
    schemas/
      telemetry.py        Feature schema + demo data + Pydantic models
  ml/
    generate_data.py      Synthetic training data from real NOAA / CelesTrak
    train_anomaly.py      IsolationForest training
    train_failure.py      XGBoost training
    models/               Trained model artifacts (.pkl)

datasets/
  processed/              Real NOAA + CelesTrak CSVs
```

---

## Key API Endpoints

| Method | Path                    | Description                                  |
|--------|-------------------------|----------------------------------------------|
| GET    | `/api/health-score`     | Health score 0–100 + penalty breakdown        |
| GET    | `/api/telemetry`        | Current 8-feature sensor snapshot            |
| GET    | `/api/weather`          | Kp index, storm level, solar wind            |
| GET    | `/api/debris`           | Conjunction objects + risk scores            |
| GET    | `/api/forecast`         | 7-day mission health forecast                |
| GET    | `/api/mission-brief`    | AI executive summary + recommended action    |
| POST   | `/api/detect-anomaly`   | IsolationForest inference                    |
| POST   | `/api/predict-failure`  | XGBoost failure probability                  |
| POST   | `/api/copilot`          | LLM chat with grounded context               |
| POST   | `/api/incident-report`  | Structured incident report generation        |
| POST   | `/api/maneuver`         | Storm-gated maneuver recommendations         |
| POST   | `/api/inject-anomaly`   | Switch demo scenario                         |
| GET    | `/health`               | Backend health check                         |

---

## Deployment

### Backend — Railway / Render

1. Set environment variables in the platform dashboard.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend — Vercel

1. Set `NEXT_PUBLIC_API_URL` to your deployed backend URL.
2. Deploy with `vercel --prod` or via GitHub integration.

---

## ML Models

The models are pre-trained and committed to the repo (`backend/ml/models/`). To retrain:

```bash
cd backend
python ml/generate_data.py    # regenerate synthetic training data
python ml/train_anomaly.py    # retrain IsolationForest
python ml/train_failure.py    # retrain XGBoost
```

Training data is derived from real NOAA space weather and CelesTrak satellite catalog records in `datasets/processed/`.

---

*Built for the Hack Orbit hackathon — June 2025*
