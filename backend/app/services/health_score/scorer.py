"""
Health score formula — deterministic, explainable (spec §3.2).
Extracted into a service so training scripts and API both import from here.

score = 100 - sum(per-feature penalties), clamped [0, 100]

Two penalty layers per feature:
  Hard: value outside green band → min(1, excess/band_width) * weight
  Soft: in-band drift from mean   → SOFT_WEIGHT * drift²
"""
from __future__ import annotations
from typing import Dict, Optional, Tuple

from app.schemas.telemetry import FEATURE_SCHEMA

SOFT_WEIGHT = 5.0  # spec §3.2 recommended value


def compute_health_score(
    readings: Dict[str, float],
) -> Tuple[int, str, Dict[str, float], Optional[str]]:
    """
    Returns (score, status, breakdown, primary_driver).

    score         : 0-100 integer
    status        : nominal (≥80) | degraded (50-79) | critical (<50)
    breakdown     : feature → penalty contribution
    primary_driver: feature with largest penalty (None if all tiny)
    """
    penalty = 0.0
    breakdown: Dict[str, float] = {}

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
            # Hard penalty — saturates at full feature weight (spec §3.2)
            contrib = min(1.0, excess / band_width) * weight
        else:
            # Soft penalty — small quadratic for in-band drift
            drift = min(1.0, abs(value - mean) / (band_width / 2))
            contrib = SOFT_WEIGHT * (drift ** 2)

        breakdown[feature] = round(contrib, 3)
        penalty += contrib

    score = max(0, min(100, round(100 - penalty)))

    if score >= 80:
        status = "nominal"
    elif score >= 50:
        status = "degraded"
    else:
        status = "critical"

    # Primary driver: only report if penalty is meaningful
    primary_driver: Optional[str] = None
    if breakdown:
        driver = max(breakdown, key=breakdown.get)
        if breakdown[driver] >= 1.0:
            primary_driver = driver

    return score, status, breakdown, primary_driver
