"""
GET /api/health-score — satellite health score (0-100) + breakdown.

Stub hardcodes demo-validated scores per scenario.
Phase 2 replaces with real formula from services/health_score/.
"""
import logging
from fastapi import APIRouter
from app.state import get_scenario

logger = logging.getLogger(__name__)
router = APIRouter()

# Demo-validated target scores (spec §3.4 and §11)
_SCORES = {
    "healthy":     {"score": 92, "status": "nominal"},
    "anomaly":     {"score": 57, "status": "degraded"},
    "debris":      {"score": 57, "status": "degraded"},
    "solar_storm": {"score": 47, "status": "critical"},
    "resolution":  {"score": 83, "status": "nominal"},
}

_BREAKDOWN = {
    "healthy": {
        "thruster_temp": 0.5, "battery_voltage": 0.3, "battery_temp": 0.2,
        "solar_panel_current": 0.2, "gyro_rate": 0.1, "reaction_wheel_rpm": 0.1,
        "comms_signal_strength": 0.2, "radiation_dose": 0.1,
    },
    "anomaly": {
        "thruster_temp": 38.0, "battery_voltage": 0.3, "battery_temp": 0.2,
        "solar_panel_current": 0.2, "gyro_rate": 0.1, "reaction_wheel_rpm": 0.1,
        "comms_signal_strength": 0.2, "radiation_dose": 0.1,
    },
    "debris": {
        "thruster_temp": 38.0, "battery_voltage": 0.3, "battery_temp": 0.2,
        "solar_panel_current": 0.2, "gyro_rate": 0.1, "reaction_wheel_rpm": 0.1,
        "comms_signal_strength": 0.2, "radiation_dose": 0.1,
    },
    "solar_storm": {
        "thruster_temp": 38.0, "battery_voltage": 3.1, "battery_temp": 1.2,
        "solar_panel_current": 2.5, "gyro_rate": 1.8, "reaction_wheel_rpm": 0.1,
        "comms_signal_strength": 2.1, "radiation_dose": 4.2,
    },
    "resolution": {
        "thruster_temp": 7.5, "battery_voltage": 0.4, "battery_temp": 0.2,
        "solar_panel_current": 0.2, "gyro_rate": 0.1, "reaction_wheel_rpm": 0.1,
        "comms_signal_strength": 0.2, "radiation_dose": 0.1,
    },
}


@router.get("/health-score")
async def get_health_score():
    scenario = get_scenario()
    data = _SCORES[scenario]
    logger.info(f"GET /api/health-score  scenario={scenario} score={data['score']}")

    return {
        "score": data["score"],
        "status": data["status"],
        "breakdown": _BREAKDOWN[scenario],
        "primary_driver": "thruster_temp" if scenario not in ("healthy",) else None,
        "scenario": scenario,
    }
