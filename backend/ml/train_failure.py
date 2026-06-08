"""
Train XGBoost failure predictor (spec §5.1-5.3).

Run from backend/: python ml/train_failure.py

Saves: ml/models/failure_model.pkl

Key design decisions from spec:
  - sigmoid probability label prevents AUC≈0.5 (spec §2.4)
  - scale_pos_weight handles class imbalance
  - continuous fault ranges prevent probability cliff (spec §2.3)
  - max_depth=4 resists overfitting on synthetic data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss

from app.schemas.telemetry import FEATURE_NAMES

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "training_data.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "failure_model.pkl")


def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Training data not found at {DATA_PATH}\n"
            "Run: python ml/generate_data.py first"
        )

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_NAMES]
    y = df["will_fail"]
    print(f"Loaded {len(df)} rows  |  failure rate: {y.mean():.1%}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Scale positive weight to handle class imbalance (spec §5.1)
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    spw = n_neg / n_pos if n_pos > 0 else 1.0
    print(f"Class balance: {n_neg} neg / {n_pos} pos  ->  scale_pos_weight={spw:.2f}")

    clf = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=spw,
        random_state=42,
        eval_metric="logloss",
        verbosity=0,
    )
    clf.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # Evaluate — quote both AUC and Brier in pitch (spec §5.2)
    probs = clf.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, probs)
    brier = brier_score_loss(y_test, probs)
    print(f"XGBoost  AUC: {auc:.3f}  Brier: {brier:.3f}  (target AUC >= 0.80)")

    # Feature importances — "model learned real physics" talking point (spec §5.2)
    importances = dict(zip(FEATURE_NAMES, clf.feature_importances_))
    ranked = sorted(importances, key=importances.get, reverse=True)
    print("Feature importances:")
    for f in ranked:
        bar = "#" * int(importances[f] * 30)
        print(f"  {f:28s} {importances[f]:.3f}  {bar}")

    # Sanity check on demo scenarios
    from app.schemas.telemetry import DEMO_TELEMETRY
    print("\nDemo scenario predictions:")
    for scenario, vals in DEMO_TELEMETRY.items():
        X_demo = np.array([[vals[f] for f in FEATURE_NAMES]])
        prob = clf.predict_proba(X_demo)[0][1]
        print(f"  [{scenario:12s}] failure prob: {prob*100:.0f}%")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    print(f"\nSaved: {MODEL_PATH}")


if __name__ == "__main__":
    main()
