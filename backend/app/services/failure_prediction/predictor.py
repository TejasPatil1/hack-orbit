"""
Failure prediction service — XGBoost model with sigmoid fallback (spec §5).

Loaded lazily on first request. Falls back to sigmoid rule
if model not trained yet.
"""
from __future__ import annotations
import logging
import math
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_MODEL_PATH = Path(__file__).parent.parent.parent.parent / "ml" / "models" / "failure_model.pkl"
_model = None


def _load():
    global _model
    if _model is not None:
        return _model
    if not _MODEL_PATH.exists():
        return None
    try:
        import joblib
        _model = joblib.load(_MODEL_PATH)
        logger.info("Loaded failure model from %s", _MODEL_PATH)
        return _model
    except Exception as exc:
        logger.warning("Could not load failure model: %s — using sigmoid fallback", exc)
        return None


def predict(readings: Dict[str, float]) -> dict:
    """
    Returns:
        failure_probability : int 0–100
        top_driver          : str feature name
        method              : "xgboost" | "sigmoid_rule"
    """
    model = _load()
    if model is None:
        return _sigmoid_predict(readings)

    try:
        import numpy as np
        from app.schemas.telemetry import FEATURE_NAMES

        X = np.array([[readings.get(f, 0.0) for f in FEATURE_NAMES]])
        prob = model.predict_proba(X)[0][1]

        # Top driver from feature importances
        importances = dict(zip(FEATURE_NAMES, model.feature_importances_))
        top_driver = max(importances, key=importances.get)

        return {
            "failure_probability": max(1, min(99, round(prob * 100))),
            "top_driver": top_driver,
            "method": "xgboost",
        }

    except Exception as exc:
        logger.warning("Failure model inference failed: %s — using sigmoid fallback", exc)
        return _sigmoid_predict(readings)


def _sigmoid_predict(readings: Dict[str, float]) -> dict:
    """
    Sigmoid rule centered at score=70 (spec §2.4).
    p_fail = 1 / (1 + exp((score - 70) / 8))
    """
    from app.services.health_score.scorer import compute_health_score

    score, _, _, _ = compute_health_score(readings)
    p = 1 / (1 + math.exp((score - 70) / 8))
    prob = max(1, min(99, round(p * 100)))

    return {
        "failure_probability": prob,
        "top_driver": "thruster_temp",
        "method": "sigmoid_rule",
    }
