"""
GET /api/forecast — 7-day mission health forecast.
"""
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from app.state import get_scenario

logger = logging.getLogger(__name__)
router = APIRouter()

_FORECAST_SCORES = {
    "healthy":     [92, 91, 93, 90, 92, 94, 93],
    "anomaly":     [57, 54, 51, 48, 46, 43, 40],
    "debris":      [57, 54, 51, 48, 46, 43, 40],
    "solar_storm": [47, 44, 41, 38, 42, 51, 58],
    "resolution":  [83, 85, 87, 88, 90, 91, 92],
}


def _status(score: int) -> str:
    if score >= 80:
        return "nominal"
    if score >= 50:
        return "degraded"
    return "critical"


@router.get("/forecast")
async def get_forecast():
    scenario = get_scenario()
    logger.info(f"GET /api/forecast  scenario={scenario}")

    scores = _FORECAST_SCORES[scenario]
    today = datetime.now(timezone.utc)

    days = [
        {
            "day": i + 1,
            "date": (today + timedelta(days=i)).strftime("%Y-%m-%d"),
            "score": scores[i],
            "status": _status(scores[i]),
        }
        for i in range(7)
    ]

    return {"satellite_id": "SAT-001", "days": days, "scenario": scenario}
