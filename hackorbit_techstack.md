> AI Mission Intelligence Copilot for Satellites

---

## Tech Stack Overview

### Frontend

- **Framework:** Next.js 14 (React)
- **Styling:** Tailwind CSS
- **Charts & Graphs:** Recharts
- **Orbit Visualization:** CesiumJS (3D globe) or Leaflet (2D fallback)
- **State Management:** Zustand
- **HTTP Client:** Axios

### Backend

- **Framework:** FastAPI (Python)
- **Server:** Uvicorn
- **Task Queue:** None needed — keep it simple for hackathon
- **API Format:** REST JSON

### AI / ML

- **Anomaly Detection:** Scikit-learn (Isolation Forest)
- **Failure Prediction:** XGBoost
- **AI Copilot Chat:** Claude API or OpenAI API
- **Incident Report Generator:** LLM prompt via same API

### Orbital & Space Data

- **Orbit Propagation:** Skyfield + SGP4
- **TLE Data (debris tracking):** CelesTrak (free API)
- **Conjunction / Collision Math:** Poliastro
- **Space Weather:** NOAA Space Weather API (free)

### Database

- **Primary DB:** PostgreSQL
- **ORM:** SQLAlchemy

### Datasets

- **Satellite Anomaly History:** ESA Anomaly Dataset (public)
- **Orbital Debris Catalog:** Space-Track.org (free account)
- **Space Weather History:** NOAA SWPC archives

### DevOps / Deployment

- **Frontend:** Vercel (free, instant deploy)
- **Backend:** Railway or Render (free tier)
- **Database:** Supabase (free PostgreSQL)
- **Version Control:** GitHub

---

## Team Division

---

### Frontend & UI/UX

**Role:** Makes everything look real and interactive

#### Responsibilities

- Set up Next.js project, Tailwind config, folder structure
- Build the main dashboard layout — sidebar, header, panels
- Build Satellite Health Score card (big number, color coded green/yellow/red)
- Build Telemetry Chart — live updating line graph using Recharts
- Build Debris Conjunction Panel — list of nearby objects with distance + risk level
- Build Space Weather Panel — pulls from backend, shows storm level
- Build Mission Forecast Panel — 7 day trend chart
- Build AI Copilot Chat UI — message bubbles, input box, send button
- Build What-If Simulator — sliders for temperature, battery, fuel, shows score change
- Build Alert/Notification system — red banner when anomaly detected
- Connect all panels to backend APIs using Axios
- Make the demo inject flow work — button that triggers anomaly scenario

#### Key Files to Build

```
/app
  /dashboard        → main page
  /components
    HealthScore.jsx
    TelemetryChart.jsx
    DebrisPanel.jsx
    WeatherPanel.jsx
    CopilotChat.jsx
    WhatIfSimulator.jsx
    AlertBanner.jsx
    MissionForecast.jsx
```

#### Tools & Libraries

- Next.js 14, Tailwind CSS, Recharts, Axios, Zustand

---

### Backend & Data APIs

**Role:** The engine — data ingestion, API endpoints, space data

#### Responsibilities

- Set up FastAPI project structure
- Connect to CelesTrak API — fetch live TLE data for satellites and debris objects
- Connect to NOAA Space Weather API — fetch Kp index, solar wind, storm alerts
- Build `/api/telemetry` endpoint — returns simulated or real telemetry readings
- Build `/api/health-score` endpoint — calculates score from telemetry values
- Build `/api/debris` endpoint — returns nearby objects with conjunction distance
- Build `/api/weather` endpoint — returns current space weather status
- Build `/api/forecast` endpoint — returns 7 day mission outlook
- Build `/api/inject-anomaly` endpoint — for demo, triggers a fault scenario
- Build `/api/incident-report` endpoint — generates report text via LLM
- Set up PostgreSQL schema and SQLAlchemy models
- Seed database with ESA anomaly dataset for ML training
- Handle CORS so frontend can talk to backend

#### Key Files to Build

```
/app
  main.py               → FastAPI app entry
  /routers
    telemetry.py
    health.py
    debris.py
    weather.py
    forecast.py
    anomaly.py
    report.py
  /models
    satellite.py
    telemetry.py
  /services
    celestrak.py        → CelesTrak API client
    noaa.py             → NOAA API client
  database.py
```

#### Tools & Libraries

- FastAPI, Uvicorn, SQLAlchemy, PostgreSQL, Requests, Skyfield, Poliastro

---

###  AI / ML & Copilot

**Role:** The brain — anomaly detection, predictions, and the chat assistant

#### Responsibilities

- Load and clean ESA Anomaly Dataset
- Train Isolation Forest model for real-time anomaly detection on telemetry
- Train XGBoost model for failure prediction (outputs probability 0–100%)
- Build `/api/predict-failure` endpoint — takes telemetry input, returns failure probability
- Build `/api/detect-anomaly` endpoint — flags which readings are abnormal
- Build `/api/copilot` endpoint — takes user message + satellite context, returns AI response
- Write the system prompt for the AI copilot — makes it respond like a mission specialist
- Build the What-If simulation logic — takes slider values, returns updated health score
- Build Maneuver Recommendation logic — simple rule-based + ML hybrid
- Build collision risk scoring — takes conjunction distance + relative velocity, outputs risk level
- Test and tune all models on demo scenarios
- Prepare the 5 demo inject scenarios (anomaly, debris alert, solar storm, combined, resolution)

#### Key Files to Build

```
/ml
  train_anomaly.py        → Isolation Forest training
  train_failure.py        → XGBoost training
  models/
    anomaly_model.pkl
    failure_model.pkl
/app/routers
  ai.py                   → copilot + prediction endpoints
/app/services
  copilot.py              → LLM prompt builder
  simulator.py            → what-if logic
  maneuver.py             → recommendation engine
```

#### Tools & Libraries

- Scikit-learn, XGBoost, Pandas, NumPy, Claude API / OpenAI API, Joblib

---

## Integration Points (All 3 Must Agree On These)

| Endpoint                      | Owner    | Used By                        |
| ----------------------------- | -------- | ------------------------------ |
| `GET /api/telemetry`        | Person 2 | Person 1 (charts)              |
| `GET /api/health-score`     | Person 2 | Person 1 (score card)          |
| `GET /api/debris`           | Person 2 | Person 1 (debris panel)        |
| `GET /api/weather`          | Person 2 | Person 1 (weather panel)       |
| `POST /api/detect-anomaly`  | Person 3 | Person 2 (calls it internally) |
| `POST /api/predict-failure` | Person 3 | Person 1 (shows probability)   |
| `POST /api/copilot`         | Person 3 | Person 1 (chat UI)             |
| `POST /api/inject-anomaly`  | Person 2 | Person 1 (demo button)         |

---

## Demo Scenario Script (All 3 Build Toward This)

```
Step 1 — Open dashboard. Satellite is healthy. Health score: 92. All green.
Step 2 — Click "Inject Anomaly". Thruster temperature spikes to 340°C.
Step 3 — Health score drops to 61. Alert banner fires. Anomaly flagged.
Step 4 — Debris panel shows object TBA-4821 at 4.2km, closing in 3.5 hours.
Step 5 — Space weather shows Kp index 7 — strong solar storm incoming.
Step 6 — Failure prediction jumps to 73%.
Step 7 — User types in copilot: "What should I do right now?"
Step 8 — AI responds: "Thruster anomaly likely caused by solar particle
          interference. Debris conjunction in 3.5 hours. Recommend
          delaying maneuver by 6 hours until storm passes.
          Monitor thruster temp every 15 minutes."
Step 9 — Incident report auto-generated. PDF downloadable.
Step 10 — What-If simulator: user reduces thruster load, health score recovers to 81.
```

---

## Build Timeline (Suggested)

| Phase       | Hours   | What Gets Done                                    |
| ----------- | ------- | ------------------------------------------------- |
| Setup       | 0–2h   | All three set up projects, agree on API contracts |
| Core build  | 2–10h  | Each person builds their core features            |
| Integration | 10–14h | Connect frontend to backend to ML                 |
| Demo polish | 14–18h | Fix bugs, smooth the demo flow, prepare pitch     |
| Buffer      | 18–20h | Anything broken, slide deck, rehearsal            |

---

## What to Fake Smartly (Save Time)

- **Telemetry data** — generate realistic fake sensor readings in Python, no real satellite needed
- **Historical trend** — hardcode a 7-day chart that looks plausible
- **Maneuver planner** — rule-based logic is fine, no need for real orbital mechanics solver
- **What-If simulator** — a weighted formula is enough, no need for a trained model
- **Debris positions** — pull real TLE data from CelesTrak but use a fixed demo satellite (ISS works)

---

## One-Line  Should Be Able to Say in the Pitch

- 1: *"I built the dashboard that brings every signal into one view."*
- 2: *"I connected real orbital and space weather data into our platform."*
-  3: *"I built the AI brain that detects faults and tells operators what to do."*

---

*Hack Orbit — Predict. Protect. Decide.*
