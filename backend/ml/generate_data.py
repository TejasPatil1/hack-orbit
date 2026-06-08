"""
Synthetic training data generator (spec §2.2-2.4).

Run from backend/: python ml/generate_data.py

Generates 5000 rows with realistic fault injection.
Critical: fault ranges start JUST outside the green band with no gap
so the models learn graded probabilities, not a cliff (spec §2.3).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from app.schemas.telemetry import FEATURE_SCHEMA, FEATURE_NAMES
from app.services.health_score.scorer import compute_health_score

np.random.seed(42)

N_TOTAL = 5000
HEALTHY_FRAC = 0.70
DOUBLE_FAULT_PROB = 0.25  # 25% of faulty rows get two simultaneous faults


def sample_healthy() -> dict:
    """Draw one nominal telemetry snapshot."""
    return {f: np.random.normal(cfg["mean"], cfg["std"])
            for f, cfg in FEATURE_SCHEMA.items()}


def inject_fault(row: dict, fault_type: str) -> dict:
    """
    Overwrite affected features with a value drawn from a continuous range
    that starts just outside the green band (spec §2.3).
    """
    row = dict(row)
    if fault_type == "thruster_overheat":
        # band_high=60 → fault range [61, 400]
        row["thruster_temp"] = np.random.uniform(61, 400)

    elif fault_type == "battery_fault":
        # voltage band_low=26.5 → fault [22, 26.4]
        # battery_temp band_high=35 → fault [35.1, 55]
        row["battery_voltage"] = np.random.uniform(22.0, 26.4)
        row["battery_temp"] = np.random.uniform(35.1, 55.0)

    elif fault_type == "attitude_loss":
        # gyro band_high=0.6 → fault [0.61, 3.0]
        row["gyro_rate"] = np.random.uniform(0.61, 3.0)
        # rpm band: 1500-5000 → fault low [200, 1499] or high [5001, 7000]
        if np.random.random() < 0.5:
            row["reaction_wheel_rpm"] = np.random.uniform(200, 1499)
        else:
            row["reaction_wheel_rpm"] = np.random.uniform(5001, 7000)

    elif fault_type == "power_drop":
        # solar band_low=7 → fault [1, 6.9]
        row["solar_panel_current"] = np.random.uniform(1.0, 6.9)
        # voltage sag (same as battery_fault voltage range)
        row["battery_voltage"] = np.random.uniform(23.0, 26.4)

    elif fault_type == "solar_storm":
        # radiation band_high=20 → fault [20.1, 100]
        row["radiation_dose"] = np.random.uniform(20.1, 100.0)
        # comms band_low=-95 → fault [-96, -120]
        row["comms_signal_strength"] = np.random.uniform(-120.0, -96.0)

    return row


FAULT_TYPES = [
    "thruster_overheat",
    "battery_fault",
    "attitude_loss",
    "power_drop",
    "solar_storm",
]


def sigmoid_p_fail(score: int) -> float:
    """
    Smooth failure probability centered at score=70 (spec §2.4).
    Generates a learnable, graded signal rather than a hard cutoff.
    p_fail = 1 / (1 + exp((score - 70) / 8))
    """
    return 1 / (1 + np.exp((score - 70) / 8))


def build_row(readings: dict, is_anomaly: int) -> dict:
    score, _, _, _ = compute_health_score(readings)
    p_fail = sigmoid_p_fail(score)
    will_fail = int(np.random.random() < p_fail)
    return {**readings, "is_anomaly": is_anomaly, "will_fail": will_fail, "health_score": score}


def main():
    n_healthy = int(N_TOTAL * HEALTHY_FRAC)
    n_faulty = N_TOTAL - n_healthy

    rows = []

    print(f"Generating {n_healthy} healthy rows...")
    for _ in range(n_healthy):
        readings = sample_healthy()
        rows.append(build_row(readings, is_anomaly=0))

    print(f"Generating {n_faulty} faulty rows...")
    for i in range(n_faulty):
        base = sample_healthy()
        fault = FAULT_TYPES[i % len(FAULT_TYPES)]
        readings = inject_fault(base, fault)

        # 25% chance of double fault (for compound-failure scenarios)
        if np.random.random() < DOUBLE_FAULT_PROB:
            second = FAULT_TYPES[(i + 2) % len(FAULT_TYPES)]
            readings = inject_fault(readings, second)

        rows.append(build_row(readings, is_anomaly=1))

    df = pd.DataFrame(rows)

    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "training_data.csv")
    df.to_csv(output_path, index=False)

    anomaly_rate = df["is_anomaly"].mean()
    failure_rate = df["will_fail"].mean()
    print(f"\nSaved {len(df)} rows to {output_path}")
    print(f"Anomaly rate : {anomaly_rate:.1%}  (expected ~30%)")
    print(f"Failure rate : {failure_rate:.1%}  (expected ~20-35%)")
    print(f"Health score : mean={df['health_score'].mean():.1f}  min={df['health_score'].min()}  max={df['health_score'].max()}")
    print("\nLabel correlation (score vs failure):")
    print(df.groupby("is_anomaly")["will_fail"].mean().rename("failure_rate"))


if __name__ == "__main__":
    main()
