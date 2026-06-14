"""
AI/ML endpoints — anomaly detection, failure prediction, copilot, maneuver planning.

  POST /api/detect-anomaly     — IsolationForest anomaly detection (3σ fallback)
  POST /api/predict-failure    — XGBoost failure probability
  POST /api/collision-risk     — Conjunction risk scoring
  POST /api/whatif             — Health score simulation with operator overrides
  POST /api/maneuver           — Storm-gated maneuver recommendations
  POST /api/copilot            — LLM chat with grounded context (deterministic fallback)
  POST /api/incident-report    — Structured incident report generation
"""
import logging
import math
from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.telemetry import (
    FEATURE_SCHEMA,
    AnomalyRequest,
    FailurePredictRequest,
    CollisionRiskRequest,
    WhatIfRequest,
    ManeuverRequest,
    CopilotRequest,
    IncidentReportRequest,
    InjectAnomalyRequest,
    VALID_SCENARIOS,
)
from app.state import set_scenario

# ML services — import failures are handled gracefully; stubs remain as fallback
try:
    from app.services.anomaly_detection import detector as _anomaly_svc
    _HAS_ANOMALY_SVC = True
except Exception:
    _HAS_ANOMALY_SVC = False

try:
    from app.services.failure_prediction import predictor as _failure_svc
    _HAS_FAILURE_SVC = True
except Exception:
    _HAS_FAILURE_SVC = False

try:
    from app.services.health_score.scorer import compute_health_score as _real_score
    _HAS_SCORER = True
except Exception:
    _HAS_SCORER = False

try:
    from app.services.ai_copilot import copilot as _copilot_svc
    from app.services.ai_copilot.context_builder import build_context as _build_context
    _HAS_COPILOT_SVC = True
except Exception:
    _HAS_COPILOT_SVC = False

try:
    from app.services.maneuver_planner.engine import recommend as _maneuver_recommend
    _HAS_MANEUVER_SVC = True
except Exception:
    _HAS_MANEUVER_SVC = False

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers — real services used when available, rules as fallback
# ─────────────────────────────────────────────────────────────────────────────

def _stub_health_score(readings: dict) -> tuple[int, str]:
    """Rule-based health score — same formula as spec §3.2. Phase 2 moves to service."""
    SOFT_WEIGHT = 5.0  # spec §3.2 recommended value
    penalty = 0.0

    for feature, cfg in FEATURE_SCHEMA.items():
        value = readings.get(feature)
        if value is None:
            continue
        low, high = cfg["band_low"], cfg["band_high"]
        weight = cfg["weight"]
        band_width = high - low
        danger = cfg["danger"]
        mean = cfg["mean"]

        out_of_band = False
        excess = 0.0

        if danger == "high" and value > high:
            excess = value - high
            out_of_band = True
        elif danger == "low" and value < low:
            excess = low - value
            out_of_band = True
        elif danger == "both":
            if value > high:
                excess = value - high
                out_of_band = True
            elif value < low:
                excess = low - value
                out_of_band = True

        if out_of_band:
            # Hard penalty — saturates at full feature weight
            penalty += min(1.0, excess / band_width) * weight
        else:
            # Soft penalty — small quadratic for in-band drift
            drift = min(1.0, abs(value - mean) / (band_width / 2))
            penalty += SOFT_WEIGHT * (drift ** 2)

    score = max(0, min(100, round(100 - penalty)))
    if score >= 80:
        status = "nominal"
    elif score >= 50:
        status = "degraded"
    else:
        status = "critical"

    return score, status


def _stub_check_anomaly(readings: dict) -> tuple[bool, list, float]:
    """
    Per-feature bound check using healthy-population 3σ bounds (mean ± 3*std).
    Returns (is_anomaly, flagged_features, raw_score_0_to_1).
    """
    flagged = []
    n_out = 0

    for feature, cfg in FEATURE_SCHEMA.items():
        value = readings.get(feature)
        if value is None:
            continue
        mean, std = cfg["mean"], cfg["std"]
        k = 3.0
        bound_low = mean - k * std
        bound_high = mean + k * std

        direction = None
        if value > bound_high:
            direction = "high"
        elif value < bound_low:
            direction = "low"

        if direction:
            n_out += 1
            flagged.append({
                "feature": feature,
                "value": round(value, 3),
                "expected_range": [round(bound_low, 3), round(bound_high, 3)],
                "direction": direction,
            })

    is_anomaly = len(flagged) > 0
    # Sigmoid-mapped anomaly score: more flagged features → higher score
    raw = min(1.0, n_out / 3.0)
    anomaly_score = round(1 / (1 + math.exp(-6 * (raw - 0.4))), 3) if n_out else 0.08

    return is_anomaly, flagged, anomaly_score


def _stub_failure_prob(score: int) -> tuple[int, str]:
    """
    Sigmoid failure probability centered at score=70 (spec §2.4).
    Returns (probability_0_to_100, top_driver).
    """
    p = 1 / (1 + math.exp((score - 70) / 8))
    prob = max(1, min(99, round(p * 100)))
    return prob, "thruster_temp"


def _stub_collision_risk(miss_km: float, vel_km_s: float, hours: float) -> tuple[str, int, bool]:
    """Transparent band-based collision risk (spec §9)."""
    if miss_km <= 1.0:
        level, base = "critical", 90
    elif miss_km <= 5.0:
        level, base = "high", 65
    elif miss_km <= 25.0:
        level, base = "moderate", 35
    else:
        level, base = "low", 10

    # Velocity modifier: faster closing → higher risk
    vel_modifier = min(15, int((vel_km_s - 3.0) * 2))
    # Time modifier: less time → higher operational risk
    time_modifier = max(0, min(15, int((6.0 - hours) * 3)))

    score = min(100, base + vel_modifier + time_modifier)
    maneuver_advised = level in ("critical", "high") or score >= 60

    return level, score, maneuver_advised


# ── Service-backed wrappers (try real model, fall back to rule logic) ─────────

def _health_score(readings: dict) -> tuple[int, str]:
    if _HAS_SCORER:
        try:
            score, status, _, _ = _real_score(readings)
            return score, status
        except Exception:
            pass
    return _stub_health_score(readings)


def _anomaly_detect(readings: dict) -> tuple[bool, list, float]:
    if _HAS_ANOMALY_SVC:
        try:
            r = _anomaly_svc.detect(readings)
            return r["is_anomaly"], r["flagged_features"], r["anomaly_score"]
        except Exception:
            pass
    return _stub_check_anomaly(readings)


def _failure_predict(readings: dict) -> tuple[int, str]:
    if _HAS_FAILURE_SVC:
        try:
            r = _failure_svc.predict(readings)
            return r["failure_probability"], r["top_driver"]
        except Exception:
            pass
    score, _ = _health_score(readings)
    return _stub_failure_prob(score)


def _build_maneuver_actions(
    score: int,
    failure_prob: int,
    flagged: list,
    risk_level: str,
    maneuver_advised: bool,
    kp: float,
    time_to_conj_h: float = 99.0,
) -> tuple[str, list]:
    """
    Rule engine for maneuver recommendations (spec §8).
    Storm-gating (Kp ≥ 5 delays burn) is the key demo moment.
    """
    actions = []
    flagged_names = {f["feature"] for f in flagged}

    # Determine posture
    if failure_prob >= 70:
        posture = "critical"
    elif failure_prob >= 40:
        posture = "elevated"
    else:
        posture = "nominal"

    priority = 1

    # 1. Conjunction handling — storm-gated (most impressive logic in demo)
    if maneuver_advised and time_to_conj_h < 6.0:
        if kp >= 5.0:
            actions.append({
                "priority": priority,
                "action": f"DELAY avoidance burn — wait for storm to pass (Kp={kp})",
                "reason": f"Firing thrusters during Kp≥5 storm risks compounding existing anomaly",
            })
        else:
            actions.append({
                "priority": priority,
                "action": f"Plan avoidance burn for conjunction in {time_to_conj_h:.1f}h",
                "reason": f"Collision risk {risk_level} — maneuver window closing",
            })
        priority += 1

    # 2. Storm posture
    if kp >= 5.0:
        actions.append({
            "priority": priority,
            "action": "Enter radiation-safe configuration",
            "reason": f"Kp {kp} — elevated particle flux above G2 threshold",
        })
        priority += 1

    # 3. Per-subsystem actions from flagged features
    if "thruster_temp" in flagged_names:
        actions.append({
            "priority": priority,
            "action": "Reduce thruster duty cycle to 30%",
            "reason": "Thruster temperature above safe limit — thermal runaway risk",
        })
        priority += 1
        actions.append({
            "priority": priority,
            "action": "Monitor thruster temperature every 15 minutes",
            "reason": "Active thermal anomaly requires continuous tracking",
        })
        priority += 1

    if "battery_voltage" in flagged_names or "battery_temp" in flagged_names:
        actions.append({
            "priority": priority,
            "action": "Switch to power-safe mode — reduce non-essential loads",
            "reason": "Battery anomaly detected",
        })
        priority += 1

    if "gyro_rate" in flagged_names or "reaction_wheel_rpm" in flagged_names:
        actions.append({
            "priority": priority,
            "action": "Engage attitude stabilization backup",
            "reason": "Attitude control anomaly detected",
        })
        priority += 1

    # 4. General high-failure posture
    if failure_prob >= 70 and not any("safe-mode" in a["action"] for a in actions):
        actions.append({
            "priority": priority,
            "action": "Prepare contingency safe-mode sequence",
            "reason": f"Failure probability {failure_prob}% — critical threshold exceeded",
        })
        priority += 1

    summary_map = {
        "critical": "Critical posture — immediate action required.",
        "elevated": "Elevated posture — close monitoring required.",
        "nominal": "Nominal posture — no immediate action required.",
    }

    return posture, actions, summary_map[posture]


def _run_maneuver(
    score: int,
    failure_prob: int,
    flagged: list,
    risk_level: str,
    maneuver_advised: bool,
    kp: float,
    time_to_conj_h: float = 99.0,
) -> tuple:
    if _HAS_MANEUVER_SVC:
        try:
            return _maneuver_recommend(
                score, failure_prob, flagged, risk_level, maneuver_advised, kp, time_to_conj_h
            )
        except Exception:
            pass
    return _build_maneuver_actions(score, failure_prob, flagged, risk_level, maneuver_advised, kp, time_to_conj_h)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/inject-anomaly")
async def inject_anomaly(request: InjectAnomalyRequest):
    if request.scenario not in VALID_SCENARIOS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown scenario '{request.scenario}'. Valid: {sorted(VALID_SCENARIOS)}")
    set_scenario(request.scenario)
    logger.info(f"POST /api/inject-anomaly  scenario={request.scenario}")
    return {"scenario": request.scenario, "status": "active"}


@router.post("/detect-anomaly")
async def detect_anomaly(request: AnomalyRequest):
    readings = request.telemetry.to_feature_dict()
    is_anomaly, flagged, anomaly_score = _anomaly_detect(readings)
    logger.info(
        f"POST /api/detect-anomaly  is_anomaly={is_anomaly} flagged={[f['feature'] for f in flagged]}"
    )
    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": anomaly_score,
        "flagged_features": flagged,
        "method": "isolation_forest" if _HAS_ANOMALY_SVC else "rule_bounds",
    }


@router.post("/predict-failure")
async def predict_failure(request: FailurePredictRequest):
    readings = request.telemetry.to_feature_dict()
    prob, driver = _failure_predict(readings)
    score, _ = _health_score(readings)
    logger.info(f"POST /api/predict-failure  score={score} prob={prob}%")
    return {
        "failure_probability": prob,
        "top_driver": driver,
        "health_score_used": score,
        "method": "xgboost" if _HAS_FAILURE_SVC else "sigmoid_rule",
    }


@router.post("/collision-risk")
async def collision_risk(request: CollisionRiskRequest):
    c = request.conjunction
    level, risk_score, maneuver_advised = _stub_collision_risk(
        c.miss_distance_km, c.relative_velocity_km_s, c.time_to_conjunction_hours
    )
    logger.info(f"POST /api/collision-risk  level={level} score={risk_score}")
    return {
        "object_id": c.object_id,
        "risk_level": level,
        "risk_score": risk_score,
        "maneuver_advised": maneuver_advised,
        "miss_distance_km": c.miss_distance_km,
        "time_to_conjunction_hours": c.time_to_conjunction_hours,
        "method": "rule_bands",
    }


@router.post("/whatif")
async def whatif_simulation(request: WhatIfRequest):
    """
    Apply operator overrides to telemetry, recompute health score.
    Uses the same scoring formula as the live system — guaranteed consistency (spec §7).
    """
    readings_before = request.telemetry.to_feature_dict()
    readings_after = {**readings_before, **request.overrides}

    before_score, _ = _health_score(readings_before)
    after_score, after_status = _health_score(readings_after)
    delta = after_score - before_score

    logger.info(f"POST /api/whatif  before={before_score} after={after_score} delta={delta:+d}")
    return {
        "before_score": before_score,
        "after_score": after_score,
        "after_status": after_status,
        "delta": delta,
        "direction": "improved" if delta > 0 else ("worsened" if delta < 0 else "unchanged"),
        "adjusted_readings": {k: round(v, 3) for k, v in request.overrides.items()},
    }


@router.post("/maneuver")
async def maneuver_recommendation(request: ManeuverRequest):
    readings = request.telemetry.to_feature_dict()
    score, _ = _health_score(readings)
    failure_prob, _ = _failure_predict(readings)
    _, flagged, _ = _anomaly_detect(readings)

    risk_level, risk_score, maneuver_advised = "low", 10, False
    time_to_conj = 99.0
    if request.conjunction:
        c = request.conjunction
        risk_level, risk_score, maneuver_advised = _stub_collision_risk(
            c.miss_distance_km, c.relative_velocity_km_s, c.time_to_conjunction_hours
        )
        time_to_conj = c.time_to_conjunction_hours

    posture, actions, summary = _run_maneuver(
        score, failure_prob, flagged, risk_level, maneuver_advised, request.kp_index, time_to_conj
    )

    logger.info(f"POST /api/maneuver  posture={posture} actions={len(actions)}")
    return {
        "posture": posture,
        "actions": actions,
        "summary": summary,
        "inputs": {
            "health_score": score,
            "failure_probability": failure_prob,
            "collision_risk_level": risk_level,
            "kp_index": request.kp_index,
        },
    }


@router.post("/copilot")
async def copilot_chat(request: CopilotRequest):
    """
    AI Copilot — grounded context block fed to LLM; deterministic fallback when offline.
    LLM never originates facts — all numbers come from pre-computed signals.
    """
    # Build context block — LLM never originates facts (spec §6.1)
    readings = request.telemetry.to_feature_dict()
    score, status = _health_score(readings)
    failure_prob, top_driver = _failure_predict(readings)
    is_anomaly, flagged, anomaly_score = _anomaly_detect(readings)

    risk_level, risk_score, maneuver_advised = "low", 10, False
    time_to_conj = 99.0
    if request.conjunction:
        c = request.conjunction
        risk_level, risk_score, maneuver_advised = _stub_collision_risk(
            c.miss_distance_km, c.relative_velocity_km_s, c.time_to_conjunction_hours
        )
        time_to_conj = c.time_to_conjunction_hours

    posture, actions, summary = _run_maneuver(
        score, failure_prob, flagged, risk_level, maneuver_advised, request.kp_index, time_to_conj
    )

    conj_id = request.conjunction.object_id if request.conjunction else None
    context = _build_context(
        telemetry=readings,
        health_score=score,
        status=status,
        is_anomaly=is_anomaly,
        flagged_features=flagged,
        anomaly_score=anomaly_score,
        failure_probability=failure_prob,
        top_driver=top_driver,
        collision_risk_level=risk_level,
        risk_score=risk_score,
        maneuver_advised=maneuver_advised,
        time_to_conjunction_hours=time_to_conj,
        conjunction_object_id=conj_id,
        kp_index=request.kp_index,
        posture=posture,
        actions=actions,
        satellite_id=request.telemetry.satellite_id,
    )

    reply, source = _copilot_svc.chat(request.message, context)

    logger.info(f"POST /api/copilot  score={score} posture={posture} source={source}")
    return {
        "reply": reply,
        "source": source,
        "signals": {
            "health_score": score,
            "failure_probability": failure_prob,
            "is_anomaly": is_anomaly,
            "posture": posture,
        },
    }


@router.post("/incident-report")
async def incident_report(request: IncidentReportRequest):
    """
    Formal incident report — LLM-generated with structured deterministic fallback.
    """
    readings = request.telemetry.to_feature_dict()
    score, status = _health_score(readings)
    failure_prob, top_driver = _failure_predict(readings)
    is_anomaly, flagged, anomaly_score = _anomaly_detect(readings)

    risk_level, risk_score, maneuver_advised = "low", 10, False
    time_to_conj = 99.0
    if request.conjunction:
        c = request.conjunction
        risk_level, risk_score, maneuver_advised = _stub_collision_risk(
            c.miss_distance_km, c.relative_velocity_km_s, c.time_to_conjunction_hours
        )
        time_to_conj = c.time_to_conjunction_hours

    posture, actions, summary = _run_maneuver(
        score, failure_prob, flagged, risk_level, maneuver_advised, request.kp_index, time_to_conj
    )

    conj_id = request.conjunction.object_id if request.conjunction else None
    context = _build_context(
        telemetry=readings,
        health_score=score,
        status=status,
        is_anomaly=is_anomaly,
        flagged_features=flagged,
        anomaly_score=anomaly_score,
        failure_probability=failure_prob,
        top_driver=top_driver,
        collision_risk_level=risk_level,
        risk_score=risk_score,
        maneuver_advised=maneuver_advised,
        time_to_conjunction_hours=time_to_conj,
        conjunction_object_id=conj_id,
        kp_index=request.kp_index,
        posture=posture,
        actions=actions,
        satellite_id=request.telemetry.satellite_id,
    )

    report, source = _copilot_svc.generate_report(context)

    logger.info(f"POST /api/incident-report  score={score} posture={posture} source={source}")
    return {
        "report": report,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "summary": {
            "health_score": score,
            "failure_probability": failure_prob,
            "posture": posture,
        },
    }

