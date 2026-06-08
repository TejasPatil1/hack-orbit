"""
In-memory demo state — all endpoints read current scenario from here.
POST /api/inject-anomaly is the only writer.
"""
from datetime import datetime, timezone

_state: dict = {
    "scenario": "healthy",
    "injected_at": None,
}


def get_scenario() -> str:
    return _state["scenario"]


def set_scenario(scenario: str) -> None:
    _state["scenario"] = scenario
    _state["injected_at"] = datetime.now(timezone.utc).isoformat()


def get_state() -> dict:
    return dict(_state)
