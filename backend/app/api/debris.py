"""
GET /api/debris — nearby debris objects and conjunction status.

Person 2 will replace with live CelesTrak TLE data for demo satellite (ISS).
"""
import logging
from fastapi import APIRouter
from app.state import get_scenario

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/debris")
async def get_debris():
    scenario = get_scenario()
    logger.info(f"GET /api/debris  scenario={scenario}")

    if scenario in ("debris", "solar_storm"):
        objects = [
            {
                "object_id": "TBA-4821",
                "name": "Debris TBA-4821",
                "miss_distance_km": 4.2,
                "relative_velocity_km_s": 7.2,
                "time_to_conjunction_hours": 3.5,
                "risk_level": "high",
                "risk_score": 72,
                "maneuver_advised": True,
            }
        ]
    else:
        objects = [
            {
                "object_id": "TBA-4821",
                "name": "Debris TBA-4821",
                "miss_distance_km": 18.5,
                "relative_velocity_km_s": 6.1,
                "time_to_conjunction_hours": 12.0,
                "risk_level": "low",
                "risk_score": 18,
                "maneuver_advised": False,
            }
        ]

    return {
        "satellite_id": "SAT-001",
        "objects": objects,
        "total_tracked": 1,
        "scenario": scenario,
    }
