"""
Context block builder (spec §6.1).

Assembles a structured dict from all deterministic analysis results.
The LLM only reads this block — it never originates facts.
Every number the copilot says comes from here.
"""
from __future__ import annotations
from typing import Dict, List, Optional


def build_context(
    telemetry: Dict[str, float],
    health_score: int,
    status: str,
    is_anomaly: bool,
    flagged_features: List[dict],
    anomaly_score: float,
    failure_probability: int,
    top_driver: str,
    collision_risk_level: str,
    risk_score: int,
    maneuver_advised: bool,
    time_to_conjunction_hours: float,
    conjunction_object_id: Optional[str],
    kp_index: float,
    posture: str,
    actions: List[dict],
    satellite_id: str = "SAT-001",
) -> dict:
    """
    Returns the grounding context block passed to the LLM prompt.
    All values are pre-computed by deterministic services.
    """
    storm_active = kp_index >= 5.0
    storm_level = "G3-strong" if kp_index >= 7 else ("G2-moderate" if kp_index >= 6 else "G1-minor") if storm_active else "quiet"

    flagged_summary = [
        f"{f['feature']} = {f['value']} (expected {f['expected_range'][0]}–{f['expected_range'][1]}, direction: {f['direction']})"
        for f in flagged_features
    ]

    top_actions = [a["action"] for a in sorted(actions, key=lambda x: x["priority"])[:4]]

    return {
        "satellite_id": satellite_id,
        "health_score": health_score,
        "health_status": status,
        "is_anomaly": is_anomaly,
        "anomaly_score": anomaly_score,
        "flagged_features": flagged_summary,
        "failure_probability_pct": failure_probability,
        "top_failure_driver": top_driver,
        "collision_risk_level": collision_risk_level,
        "collision_risk_score": risk_score,
        "maneuver_advised": maneuver_advised,
        "time_to_conjunction_hours": time_to_conjunction_hours if maneuver_advised else None,
        "conjunction_object": conjunction_object_id if maneuver_advised else None,
        "kp_index": kp_index,
        "storm_active": storm_active,
        "storm_level": storm_level,
        "posture": posture,
        "recommended_actions": top_actions,
        # Raw actions list kept for fallback path
        "_actions_full": actions,
    }
