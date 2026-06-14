"""
GET /api/mission-brief  — AI executive mission summary (deterministic, always available).

Returns structured mission intelligence covering:
  status, key issues, operational impact, recommended action, confidence.
"""
import logging
import math
from fastapi import APIRouter
from app.state import get_scenario
from app.schemas.telemetry import (
    DEMO_TELEMETRY, DEMO_KP, DEMO_CONJUNCTION, FEATURE_SCHEMA,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _compute_score(readings: dict) -> tuple[int, str]:
    try:
        from app.services.health_score.scorer import compute_health_score
        score, status, _, _ = compute_health_score(readings)
        return score, status
    except Exception:
        return 85, "nominal"


def _failure_prob(score: int) -> int:
    p = 1 / (1 + math.exp((score - 70) / 8))
    return max(1, min(99, round(p * 100)))


def _detect_issues(readings: dict, kp: float, conjunction: dict | None) -> list[str]:
    issues = []
    for feature, cfg in FEATURE_SCHEMA.items():
        value = readings.get(feature)
        if value is None:
            continue
        unit = cfg["unit"]
        label = feature.replace("_", " ").title()
        if cfg["danger"] == "high" and value > cfg["band_high"]:
            issues.append(f"{label} exceeds safe limit ({value:.1f} {unit})")
        elif cfg["danger"] == "low" and value < cfg["band_low"]:
            issues.append(f"{label} below threshold ({value:.1f} {unit})")
        elif cfg["danger"] == "both":
            if value > cfg["band_high"]:
                issues.append(f"{label} above limit ({value:.1f} {unit})")
            elif value < cfg["band_low"]:
                issues.append(f"{label} below limit ({value:.1f} {unit})")
    if kp >= 7:
        issues.append(f"Severe geomagnetic storm active — Kp {kp} (G3 level)")
    elif kp >= 5:
        issues.append(f"Geomagnetic storm in progress — Kp {kp}")
    if conjunction:
        ttc = conjunction["time_to_conjunction_hours"]
        miss = conjunction["miss_distance_km"]
        issues.append(f"Debris conjunction in {ttc:.1f}h at {miss:.1f} km miss distance")
    return issues


def _operational_impact(issues: list[str], kp: float, conjunction: dict | None, failure_prob: int) -> list[str]:
    impact = []
    if any("thruster" in i.lower() for i in issues):
        impact.append("Maneuver execution reliability degraded — thermal stress on propulsion")
    if kp >= 7:
        impact.append("Satellite in active radiation environment — component lifespan reduction")
        impact.append("All thruster burns contraindicated until Kp < 5")
    elif kp >= 5:
        impact.append("Elevated particle flux — increased bit-flip and sensor error risk")
    if conjunction:
        ttc = conjunction["time_to_conjunction_hours"]
        impact.append(f"Collision avoidance window closing in {ttc:.1f}h — maneuver authority time-limited")
    if failure_prob >= 70:
        impact.append("High probability of subsystem failure within operational window")
    elif failure_prob >= 40:
        impact.append("Elevated failure probability — reduced mission reliability margin")
    if any("battery" in i.lower() or "solar" in i.lower() for i in issues):
        impact.append("Power budget constrained — non-essential loads must be shed")
    if not impact:
        impact.append("No operational constraints — mission posture nominal")
    return impact[:3]


@router.get("/mission-brief")
async def get_mission_brief():
    scenario = get_scenario()
    readings = dict(DEMO_TELEMETRY[scenario])
    kp = float(DEMO_KP[scenario])
    conjunction = DEMO_CONJUNCTION.get(scenario)

    score, _ = _compute_score(readings)
    failure_prob = _failure_prob(score)
    issues = _detect_issues(readings, kp, conjunction)
    impact = _operational_impact(issues, kp, conjunction, failure_prob)

    # Overall classification
    if score < 50 or kp >= 7:
        risk_level, mission_status = "CRITICAL", "CRITICAL"
    elif score < 70 or kp >= 5 or conjunction is not None:
        risk_level, mission_status = "HIGH", "DEGRADED"
    elif score < 85:
        risk_level, mission_status = "MODERATE", "DEGRADED"
    else:
        risk_level, mission_status = "LOW", "NOMINAL"

    # Summary
    if not issues:
        summary = (
            "All satellite systems operating within nominal parameters. "
            "No anomalies or conjunction events detected."
        )
    else:
        primary = issues[0]
        count = len(issues)
        extra = f" (+{count - 1} additional)" if count > 1 else ""
        summary = f"{primary}{extra}."

    # Recommended action
    if kp >= 7:
        action = (
            "Enter radiation-safe configuration immediately. "
            "Delay all thruster burns until Kp drops below 5."
        )
    elif conjunction:
        ttc = conjunction["time_to_conjunction_hours"]
        action = (
            f"Plan avoidance maneuver now — conjunction window closes in {ttc:.1f}h. "
            "Confirm burn clearance with ground station."
        )
    elif any("thruster" in i.lower() for i in issues):
        action = (
            "Reduce thruster duty cycle to 30% and monitor thermal profile every 15 min. "
            "Prepare contingency cooling procedure."
        )
    elif any("battery" in i.lower() or "solar" in i.lower() for i in issues):
        action = (
            "Switch to power-safe mode. "
            "Shed non-essential loads and increase battery charge monitoring."
        )
    elif issues:
        action = (
            "Increase monitoring cadence to 5-minute intervals. "
            "Review subsystem logs and prepare contingency procedures."
        )
    else:
        action = "Continue nominal operations. Next scheduled health review in 24 hours."

    # Confidence
    confidence_map = {
        "healthy": 97, "resolution": 98,
        "anomaly": 92, "debris": 89, "solar_storm": 85,
    }
    confidence = confidence_map.get(scenario, 90)

    logger.info(
        f"GET /api/mission-brief  scenario={scenario} "
        f"status={mission_status} risk={risk_level} issues={len(issues)}"
    )
    return {
        "mission_status": mission_status,
        "summary": summary,
        "key_issues": issues[:4],
        "operational_impact": impact,
        "recommended_action": action,
        "risk_level": risk_level,
        "confidence": confidence,
        "health_score": score,
        "failure_probability": failure_prob,
        "scenario": scenario,
    }
