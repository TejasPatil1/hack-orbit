"""
Anomaly detection service — IsolationForest + per-feature 3σ bounds (spec §4).

Loaded lazily on first request. Falls back to rule-based 3σ check
if the model file doesn't exist yet (so Phase 1 stubs keep working).
"""
from __future__ import annotations
import logging
import math
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

_MODEL_PATH = Path(__file__).parent.parent.parent.parent / "ml" / "models" / "anomaly_model.pkl"
_bundle: Optional[dict] = None


def _load() -> Optional[dict]:
    global _bundle
    if _bundle is not None:
        return _bundle
    if not _MODEL_PATH.exists():
        return None
    try:
        import joblib
        _bundle = joblib.load(_MODEL_PATH)
        logger.info("Loaded anomaly model from %s", _MODEL_PATH)
        return _bundle
    except Exception as exc:
        logger.warning("Could not load anomaly model: %s — using rule fallback", exc)
        return None


def detect(readings: Dict[str, float]) -> dict:
    """
    Returns:
        is_anomaly      : bool
        anomaly_score   : float 0–1 (1 = most anomalous)
        flagged_features: list of {feature, value, expected_range, direction}
        method          : "isolation_forest" | "rule_bounds"
    """
    bundle = _load()
    if bundle is None:
        return _rule_detect(readings)

    try:
        import numpy as np
        feature_names = bundle["feature_names"]
        X = np.array([[readings.get(f, 0.0) for f in feature_names]])

        # IsolationForest raw score (more negative = more anomalous)
        raw = bundle["model"].score_samples(X)[0]
        # Map to [0, 1] via logistic transform
        anomaly_score = round(1 / (1 + math.exp(5 * (raw + 0.1))), 3)

        # Per-feature bound violations (spec §4.2 — tells UI which sensor is bad)
        flagged: List[dict] = []
        for feat, value in readings.items():
            if feat not in bundle["bounds"]:
                continue
            b = bundle["bounds"][feat]
            if value > b["high"]:
                flagged.append({
                    "feature": feat,
                    "value": round(value, 3),
                    "expected_range": [round(b["low"], 3), round(b["high"], 3)],
                    "direction": "high",
                })
            elif value < b["low"]:
                flagged.append({
                    "feature": feat,
                    "value": round(value, 3),
                    "expected_range": [round(b["low"], 3), round(b["high"], 3)],
                    "direction": "low",
                })

        # Binary decision: per-feature bounds are the ground truth.
        # Forest predict() is NOT used for the binary call — its threshold
        # (contamination-based) falsely flags tail-of-distribution healthy
        # samples. The forest score above provides the severity metric.
        is_anomaly = len(flagged) > 0

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "flagged_features": flagged,
            "method": "isolation_forest",
        }

    except Exception as exc:
        logger.warning("Anomaly model inference failed: %s — using rule fallback", exc)
        return _rule_detect(readings)


def _rule_detect(readings: Dict[str, float]) -> dict:
    """
    3σ bound check using FEATURE_SCHEMA stats (no model required).
    Same logic as Phase 1 stubs — guaranteed to work.
    """
    from app.schemas.telemetry import FEATURE_SCHEMA

    flagged: List[dict] = []
    n_out = 0

    for feature, cfg in FEATURE_SCHEMA.items():
        value = readings.get(feature)
        if value is None:
            continue
        low = cfg["mean"] - 3 * cfg["std"]
        high = cfg["mean"] + 3 * cfg["std"]

        if value > high:
            n_out += 1
            flagged.append({
                "feature": feature, "value": round(value, 3),
                "expected_range": [round(low, 3), round(high, 3)],
                "direction": "high",
            })
        elif value < low:
            n_out += 1
            flagged.append({
                "feature": feature, "value": round(value, 3),
                "expected_range": [round(low, 3), round(high, 3)],
                "direction": "low",
            })

    raw = min(1.0, n_out / 3.0)
    anomaly_score = round(1 / (1 + math.exp(-6 * (raw - 0.4))), 3) if n_out else 0.08

    return {
        "is_anomaly": len(flagged) > 0,
        "anomaly_score": anomaly_score,
        "flagged_features": flagged,
        "method": "rule_bounds",
    }
