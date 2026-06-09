"""
GET /api/health-score — satellite health score (0-100) + breakdown.
Uses the same scorer service as all AI endpoints — single source of truth.
"""
import logging
from fastapi import APIRouter
from app.state import get_scenario
from app.schemas.telemetry import DEMO_TELEMETRY
from app.services.health_score.scorer import compute_health_score

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health-score")
async def get_health_score():
    scenario = get_scenario()
    readings = dict(DEMO_TELEMETRY[scenario])
    score, status, breakdown, primary_driver = compute_health_score(readings)
    logger.info(f"GET /api/health-score  scenario={scenario} score={score}")
    return {
        "score": score,
        "status": status,
        "breakdown": breakdown,
        "primary_driver": primary_driver,
        "scenario": scenario,
    }
