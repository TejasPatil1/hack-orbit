"""
GET /api/telemetry   — current satellite telemetry snapshot
GET /api/satellite   — static satellite metadata
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from app.state import get_scenario
from app.schemas.telemetry import DEMO_TELEMETRY, DEMO_KP, DEMO_CONJUNCTION

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/telemetry")
async def get_telemetry():
    scenario = get_scenario()
    logger.info(f"GET /api/telemetry  scenario={scenario}")

    readings = dict(DEMO_TELEMETRY[scenario])
    conjunction = DEMO_CONJUNCTION.get(scenario)

    return {
        "satellite_id": "SAT-001",
        "satellite_name": "HO-SAT-001",
        "scenario": scenario,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "readings": readings,
        "kp_index": DEMO_KP[scenario],
        "conjunction": conjunction,
    }


@router.get("/satellite")
async def get_satellite():
    return {
        "satellite_id": "SAT-001",
        "name": "HO-SAT-001",
        "orbit_type": "LEO",
        "altitude_km": 550,
        "inclination_deg": 53.0,
        "period_min": 95.4,
        "launch_date": "2023-03-15",
        "status": "operational",
    }
