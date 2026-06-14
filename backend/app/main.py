"""
Hack Orbit backend — FastAPI entry point.
Run from backend/: uvicorn app.main:app --reload
"""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, telemetry, health, debris, weather, forecast, anomaly, mission_brief

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s — %(message)s")

app = FastAPI(
    title="Hack Orbit API",
    description="AI Mission Intelligence Copilot for Satellites — Predict. Protect. Decide.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai.router,       prefix="/api", tags=["AI / ML"])
app.include_router(telemetry.router, prefix="/api", tags=["Telemetry"])
app.include_router(health.router,    prefix="/api", tags=["Health Score"])
app.include_router(debris.router,    prefix="/api", tags=["Debris Conjunction"])
app.include_router(weather.router,   prefix="/api", tags=["Space Weather"])
app.include_router(forecast.router,  prefix="/api", tags=["Mission Forecast"])
app.include_router(anomaly.router,        prefix="/api", tags=["Demo Scenarios"])
app.include_router(mission_brief.router,  prefix="/api", tags=["Mission Brief"])


@app.get("/health")
async def api_health():
    return {"status": "ok", "service": "hack-orbit-backend"}


@app.get("/")
async def root():
    return {"message": "Hack Orbit API — Predict. Protect. Decide."}
