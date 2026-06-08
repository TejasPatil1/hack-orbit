"""
Train Isolation Forest for anomaly detection (spec §4.1).

Run from backend/: python ml/train_anomaly.py

Saves: ml/models/anomaly_model.pkl
  Bundle contains:
    model  : fitted IsolationForest
    bounds : per-feature healthy-population mean ± 3σ (for flagged_features)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score

from app.schemas.telemetry import FEATURE_NAMES

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "training_data.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "anomaly_model.pkl")


def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Training data not found at {DATA_PATH}\n"
            "Run: python ml/generate_data.py first"
        )

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows  |  anomaly rate: {df['is_anomaly'].mean():.1%}")

    X_all = df[FEATURE_NAMES].values
    y_all = df["is_anomaly"].values

    # Train on FULL dataset — IsolationForest is unsupervised, learns which
    # feature combinations are rare/unusual across the whole distribution.
    # contamination matches the true anomaly prevalence in the data.
    X_healthy = df[df["is_anomaly"] == 0][FEATURE_NAMES]
    print(f"Training on {len(df)} rows (full dataset)...")

    clf = IsolationForest(
        n_estimators=200,
        contamination=0.25,  # true anomaly prevalence ~30% (spec §4.1)
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(df[FEATURE_NAMES])

    # Per-feature 3σ bounds from healthy population only (spec §4.2)
    bounds = {}
    for feat in FEATURE_NAMES:
        vals = X_healthy[feat]
        m, s = float(vals.mean()), float(vals.std())
        bounds[feat] = {
            "mean": m,
            "std": s,
            "low": m - 3 * s,
            "high": m + 3 * s,
        }

    # Validate on full dataset
    scores = -clf.score_samples(X_all)
    auc = roc_auc_score(y_all, scores)
    print(f"Anomaly detection AUC: {auc:.3f}  (target: >= 0.90)")

    # Quick sanity check on demo scenarios
    from app.schemas.telemetry import DEMO_TELEMETRY
    for scenario, vals in DEMO_TELEMETRY.items():
        X_demo = np.array([[vals[f] for f in FEATURE_NAMES]])
        pred = clf.predict(X_demo)[0]
        label = "ANOMALY" if pred == -1 else "normal"
        print(f"  Demo [{scenario:12s}] -> {label}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    bundle = {"model": clf, "bounds": bounds, "feature_names": FEATURE_NAMES}
    joblib.dump(bundle, MODEL_PATH)
    print(f"\nSaved: {MODEL_PATH}")


if __name__ == "__main__":
    main()
