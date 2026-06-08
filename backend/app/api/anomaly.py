"""
POST /api/inject-anomaly — switches the demo scenario state.

Person 2 owns this endpoint. Calls set_scenario() which all other
endpoints read via get_scenario().
"""
import logging
from fastapi import APIRouter
from app.schemas.telemetry import InjectAnomalyRequest, VALID_SCENARIOS
from app.state import set_scenario, get_state

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/inject-anomaly")
async def inject_anomaly(request: InjectAnomalyRequest):
    if request.scenario not in VALID_SCENARIOS:
        return {
            "success": False,
            "error": f"Unknown scenario '{request.scenario}'. Valid: {sorted(VALID_SCENARIOS)}",
        }

    set_scenario(request.scenario)
    logger.info(f"POST /api/inject-anomaly  scenario={request.scenario}")

    return {
        "success": True,
        "scenario": request.scenario,
        "message": f"Scenario '{request.scenario}' activated. All endpoints now reflect this state.",
    }


@router.get("/demo-state")
async def get_demo_state():
    """Debug endpoint — shows current scenario and when it was set."""
    return get_state()
