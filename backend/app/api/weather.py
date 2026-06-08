"""
GET /api/weather — space weather status (Kp index, storm level).

Person 2 will replace with live NOAA Space Weather API data.
"""
import logging
from fastapi import APIRouter
from app.state import get_scenario

logger = logging.getLogger(__name__)
router = APIRouter()

_WEATHER = {
    "healthy": {
        "kp_index": 2.0, "storm_level": "quiet",
        "solar_wind_speed_km_s": 420,
        "description": "Quiet geomagnetic conditions. No storm activity.",
        "alert": None,
    },
    "anomaly": {
        "kp_index": 2.0, "storm_level": "quiet",
        "solar_wind_speed_km_s": 440,
        "description": "Quiet geomagnetic conditions.",
        "alert": None,
    },
    "debris": {
        "kp_index": 2.0, "storm_level": "quiet",
        "solar_wind_speed_km_s": 440,
        "description": "Quiet geomagnetic conditions.",
        "alert": None,
    },
    "solar_storm": {
        "kp_index": 7.0, "storm_level": "strong",
        "solar_wind_speed_km_s": 720,
        "description": "G3 Strong geomagnetic storm. Elevated particle flux. Thruster maneuvers NOT recommended.",
        "alert": "G3 STRONG GEOMAGNETIC STORM — Kp 7",
    },
    "resolution": {
        "kp_index": 3.0, "storm_level": "unsettled",
        "solar_wind_speed_km_s": 490,
        "description": "Unsettled conditions. Storm subsiding.",
        "alert": None,
    },
}


@router.get("/weather")
async def get_weather():
    scenario = get_scenario()
    data = _WEATHER[scenario]
    logger.info(f"GET /api/weather  scenario={scenario} kp={data['kp_index']}")
    return {**data, "scenario": scenario, "source": "stub"}
