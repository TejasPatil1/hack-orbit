"""
Hack Orbit backend — FastAPI entry point.
Run from backend/: uvicorn app.main:app --reload

Person 2 adds their routers here. Person 3 only owns app.api.ai.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai

# Person 2 imports (stub-ready stubs already exist in app/api/):
from app.api import telemetry, health, debris, weather, forecast, anomaly

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s — %(message)s")

app = FastAPI(
    title="Hack Orbit API",
    description="AI Mission Intelligence Copilot for Satellites",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Person 3 routes
app.include_router(ai.router, prefix="/api", tags=["AI/ML — Person 3"])

# Person 2 routes (stubs — Person 2 fills in real implementations)
app.include_router(telemetry.router, prefix="/api", tags=["Telemetry — Person 2"])
app.include_router(health.router,    prefix="/api", tags=["Health — Person 2"])
app.include_router(debris.router,    prefix="/api", tags=["Debris — Person 2"])
app.include_router(weather.router,   prefix="/api", tags=["Weather — Person 2"])
app.include_router(forecast.router,  prefix="/api", tags=["Forecast — Person 2"])
app.include_router(anomaly.router,   prefix="/api", tags=["Anomaly — Person 2"])


@app.get("/health")
async def api_health():
    return {"status": "ok", "service": "hack-orbit-backend"}


@app.get("/")
async def root():
    return {"message": "Hack Orbit API — Predict. Protect. Decide."}
