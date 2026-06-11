"""
Training data generator — real-world calibrated (spec §2.2-2.4).

Primary processed datasets (new, from friend's branch):
  datasets/processed/space_weather.csv     → Kp, solar wind speed, Bt time-series (1 min res)
  datasets/processed/satellite_catalog.csv → 69k satellites: LEO alt, inclination
  datasets/processed/health_features.csv  → 69k satellites: real health_score distribution

Fallback raw datasets:
  datasets/noaa/geomagnetic/kp_index.json  → broader Kp history including storms
  datasets/noaa/solar/solar_wind.json      → solar wind speed
  datasets/noaa/solar/magnetic_field.json  → magnetic field Bt

Run from backend/: python ml/generate_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
import pandas as pd

from app.schemas.telemetry import FEATURE_SCHEMA, FEATURE_NAMES
from app.services.health_score.scorer import compute_health_score

np.random.seed(42)

N_TOTAL           = 20000
HEALTHY_FRAC      = 0.70
DOUBLE_FAULT_PROB = 0.25

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "datasets")


# ---------------------------------------------------------------------------
# Load real-world distributions — processed CSVs first, raw JSON fallback
# ---------------------------------------------------------------------------

def _load_real_distributions() -> dict:
    dist = {}

    # ── Space weather (processed CSV — 1358 real 1-min readings) ─────────────
    try:
        sw_path = os.path.join(_ROOT, "processed", "space_weather.csv")
        sw = pd.read_csv(sw_path)

        kp_vals   = sw["Kp"].dropna().values
        spd_vals  = sw["speed"].dropna().values
        bt_vals   = sw["bt"].dropna().values

        dist["kp_mean"]        = float(kp_vals.mean())
        dist["kp_std"]         = float(kp_vals.std())
        dist["kp_p95"]         = float(np.percentile(kp_vals, 95))
        dist["solar_wind_mean"]= float(spd_vals.mean())
        dist["solar_wind_std"] = float(spd_vals.std())
        dist["bt_mean"]        = float(bt_vals.mean())
        dist["bt_std"]         = float(bt_vals.std())
        dist["bt_p95"]         = float(np.percentile(bt_vals, 95))
        dist["_sw_kp_samples"] = kp_vals       # keep raw for sampling
        dist["_sw_spd_samples"]= spd_vals
        dist["_sw_bt_samples"] = bt_vals

        # Real average space_weather_score from the processed file
        if "space_weather_score" in sw.columns:
            sws = sw["space_weather_score"].dropna().values
            dist["sw_score_mean"] = float(sws.mean())
            dist["sw_score_std"]  = float(sws.std())

        print(f"[processed] Space weather CSV: Kp mean={dist['kp_mean']:.2f} std={dist['kp_std']:.2f}  "
              f"wind={dist['solar_wind_mean']:.1f} km/s  Bt={dist['bt_mean']:.2f} nT")
    except Exception as e:
        print(f"[warn] space_weather.csv failed ({e}) — trying raw NOAA JSON")
        dist.setdefault("kp_mean", 2.21); dist.setdefault("kp_std", 0.70)
        dist.setdefault("kp_p95", 3.0);  dist.setdefault("storm_prob", 0.068)
        dist.setdefault("solar_wind_mean", 518.0); dist.setdefault("solar_wind_std", 31.0)
        dist.setdefault("bt_mean", 4.42); dist.setdefault("bt_std", 0.28); dist.setdefault("bt_p95", 4.86)

    # ── Storm probability — needs broader history (kp_index.json) ─────────────
    # The space_weather.csv is a quiet 1-day window (0% storms).
    # Fall back to kp_index.json for the storm tail.
    try:
        kp_path = os.path.join(_ROOT, "noaa", "geomagnetic", "kp_index.json")
        with open(kp_path) as f:
            kp_data = json.load(f)
        kp_hist = np.array([r["Kp"] for r in kp_data if isinstance(r.get("Kp"), (int, float))])
        dist["storm_prob"] = float((kp_hist >= 5).mean())
        dist["kp_hist_p99"] = float(np.percentile(kp_hist, 99))
        print(f"[raw] Kp history: storm_prob={dist['storm_prob']:.1%}  p99={dist['kp_hist_p99']:.1f}")
    except Exception as e:
        print(f"[warn] kp_index.json failed ({e})")
        dist.setdefault("storm_prob", 0.068)
        dist.setdefault("kp_hist_p99", 7.0)

    # ── LEO orbital parameters — satellite_catalog.csv (69k objects) ──────────
    try:
        cat_path = os.path.join(_ROOT, "processed", "satellite_catalog.csv")
        cat = pd.read_csv(cat_path, usecols=["ALTITUDE_AVG", "INCLINATION"])
        leo = cat[(cat.ALTITUDE_AVG >= 200) & (cat.ALTITUDE_AVG <= 2000)].dropna()
        dist["leo_alt_mean"]  = float(leo.ALTITUDE_AVG.mean())
        dist["leo_alt_std"]   = float(leo.ALTITUDE_AVG.std())
        dist["leo_incl_mean"] = float(leo.INCLINATION.mean())
        dist["leo_incl_std"]  = float(leo.INCLINATION.std())
        dist["_leo_alt_samples"] = leo.ALTITUDE_AVG.values   # raw for bootstrap sampling
        print(f"[processed] Satellite catalog: LEO alt mean={dist['leo_alt_mean']:.1f} km  "
              f"std={dist['leo_alt_std']:.1f}  incl mean={dist['leo_incl_mean']:.1f}°  n={len(leo)}")
    except Exception as e:
        print(f"[warn] satellite_catalog.csv failed ({e}) — trying collision_event.csv")
        try:
            tle_path = os.path.join(_ROOT, "processed", "collision_event.csv")
            tle_df = pd.read_csv(tle_path, usecols=["MEAN_MOTION", "INCLINATION"])
            tle_df = tle_df[tle_df.MEAN_MOTION > 0]
            tle_df["altitude_km"] = (
                (398600.4418 / ((tle_df.MEAN_MOTION * 2 * np.pi / 86400) ** 2)) ** (1/3)
            ) - 6371
            leo = tle_df[(tle_df.altitude_km >= 200) & (tle_df.altitude_km <= 2000)]
            dist["leo_alt_mean"]  = float(leo.altitude_km.mean())
            dist["leo_alt_std"]   = float(leo.altitude_km.std())
            dist["leo_incl_mean"] = float(leo.INCLINATION.mean())
            dist["leo_incl_std"]  = float(leo.INCLINATION.std())
            print(f"[fallback] TLE alt: mean={dist['leo_alt_mean']:.0f} km  n={len(leo)}")
        except Exception as e2:
            print(f"[warn] TLE also failed ({e2}) — using defaults")
            dist.update({"leo_alt_mean": 573.6, "leo_alt_std": 328.5,
                         "leo_incl_mean": 73.6, "leo_incl_std": 21.8})

    # ── Real health_score baseline from health_features.csv ───────────────────
    try:
        hf_path = os.path.join(_ROOT, "processed", "health_features.csv")
        hf = pd.read_csv(hf_path, usecols=["health_score"])
        hs = hf["health_score"].dropna().values
        dist["real_hs_mean"] = float(hs.mean())
        dist["real_hs_std"]  = float(hs.std())
        print(f"[processed] Real health scores: mean={dist['real_hs_mean']:.2f}  std={dist['real_hs_std']:.2f}")
    except Exception as e:
        print(f"[warn] health_features.csv failed ({e})")
        dist["real_hs_mean"] = 77.65
        dist["real_hs_std"]  = 2.02

    return dist


# ---------------------------------------------------------------------------
# Bootstrap sampler: draw from real distribution when available
# ---------------------------------------------------------------------------

def _sample_kp(dist: dict) -> float:
    if "_sw_kp_samples" in dist:
        return float(np.random.choice(dist["_sw_kp_samples"]))
    return max(0.0, np.random.normal(dist["kp_mean"], dist["kp_std"]))


def _sample_wind(dist: dict) -> float:
    if "_sw_spd_samples" in dist:
        return float(np.random.choice(dist["_sw_spd_samples"]))
    return max(200.0, np.random.normal(dist["solar_wind_mean"], dist["solar_wind_std"]))


def _sample_bt(dist: dict) -> float:
    if "_sw_bt_samples" in dist:
        return float(np.random.choice(dist["_sw_bt_samples"]))
    return max(0.1, np.random.normal(dist["bt_mean"], dist["bt_std"]))


def _sample_alt(dist: dict) -> float:
    if "_leo_alt_samples" in dist:
        # Bootstrap from the real LEO distribution (cap to LEO range)
        alt = float(np.random.choice(dist["_leo_alt_samples"]))
        return max(200.0, min(2000.0, alt))
    return max(200.0, np.random.normal(dist["leo_alt_mean"], dist["leo_alt_std"] * 0.5))


# ---------------------------------------------------------------------------
# Healthy sample — calibrated to real orbital + space weather environment
# ---------------------------------------------------------------------------

def sample_healthy(dist: dict) -> dict:
    row = {f: np.random.normal(cfg["mean"], cfg["std"])
           for f, cfg in FEATURE_SCHEMA.items()}

    # Radiation dose scales with real LEO altitude + Bt (bootstrap from catalog)
    alt       = _sample_alt(dist)
    alt_factor = (alt / 573.6) ** 0.6          # radiation ∝ altitude^0.6
    bt        = _sample_bt(dist)
    bt_factor  = max(0.5, bt / dist["bt_mean"])
    row["radiation_dose"] = abs(np.random.normal(
        FEATURE_SCHEMA["radiation_dose"]["mean"] * alt_factor * bt_factor,
        FEATURE_SCHEMA["radiation_dose"]["std"]
    ))

    # Solar panel current perturbed by real wind speed distribution
    wind       = _sample_wind(dist)
    wind_factor = 1.0 + 0.03 * ((wind - 450) / 100)   # ±3% effect per 100 km/s
    row["solar_panel_current"] = abs(np.random.normal(
        FEATURE_SCHEMA["solar_panel_current"]["mean"] * wind_factor,
        FEATURE_SCHEMA["solar_panel_current"]["std"]
    ))

    # Gyro micro-disturbances from real Bt sample
    gyro_noise = 0.005 * (bt / dist["bt_mean"])
    row["gyro_rate"] = abs(row["gyro_rate"] + np.random.normal(0, gyro_noise))

    return row


# ---------------------------------------------------------------------------
# Fault injection — continuous ranges just outside band (spec §2.3)
# ---------------------------------------------------------------------------

def inject_fault(row: dict, fault_type: str, dist: dict) -> dict:
    row = dict(row)

    if fault_type == "thruster_overheat":
        row["thruster_temp"] = np.random.uniform(61, 400)

    elif fault_type == "battery_fault":
        row["battery_voltage"] = np.random.uniform(22.0, 26.4)
        row["battery_temp"]    = np.random.uniform(35.1, 55.0)

    elif fault_type == "attitude_loss":
        row["gyro_rate"] = np.random.uniform(0.61, 3.0)
        if np.random.random() < 0.5:
            row["reaction_wheel_rpm"] = np.random.uniform(200, 1499)
        else:
            row["reaction_wheel_rpm"] = np.random.uniform(5001, 7000)

    elif fault_type == "power_drop":
        # Real wind variance → realistic dropout magnitude
        wind  = _sample_wind(dist)
        ratio = max(0.3, wind / 450)
        row["solar_panel_current"] = np.random.uniform(1.0, 6.9) * ratio
        row["battery_voltage"]     = np.random.uniform(23.0, 26.4)

    elif fault_type == "solar_storm":
        # Storm severity from real Kp history tail (p95 × 1.5 to ensure storm range)
        kp_storm     = np.random.uniform(5.0, max(7.0, dist["kp_hist_p99"]))
        storm_factor = kp_storm / 5.0
        row["radiation_dose"]        = np.random.uniform(20.1, 100.0) * storm_factor * 0.5
        row["comms_signal_strength"] = np.random.uniform(-120.0, -96.0)
        # Real Bt p95 × storm factor → gyro disturbance
        row["gyro_rate"]             = np.random.uniform(0.61, 2.5) * min(2.0, dist["bt_p95"] / 5.0)

    elif fault_type == "solar_storm_compound":
        # Storm + power degradation — real co-occurrence pattern
        row["radiation_dose"]        = np.random.uniform(20.1, 80.0)
        row["comms_signal_strength"] = np.random.uniform(-110.0, -96.0)
        row["solar_panel_current"]   = np.random.uniform(4.0, 6.9)
        row["battery_voltage"]       = np.random.uniform(24.0, 26.4)

    return row


FAULT_TYPES = [
    "thruster_overheat",
    "battery_fault",
    "attitude_loss",
    "power_drop",
    "solar_storm",
    "solar_storm_compound",
]


def sigmoid_p_fail(score: int) -> float:
    return 1 / (1 + np.exp((score - 70) / 8))


def build_row(readings: dict, is_anomaly: int) -> dict:
    score, _, _, _ = compute_health_score(readings)
    p_fail    = sigmoid_p_fail(score)
    will_fail = int(np.random.random() < p_fail)
    return {**readings, "is_anomaly": is_anomaly, "will_fail": will_fail, "health_score": score}


def main():
    print("Loading real-world calibration data...")
    dist = _load_real_distributions()
    print()

    n_healthy = int(N_TOTAL * HEALTHY_FRAC)
    n_faulty  = N_TOTAL - n_healthy

    rows = []

    print(f"Generating {n_healthy} healthy rows (real-world bootstrapped)...")
    for _ in range(n_healthy):
        rows.append(build_row(sample_healthy(dist), is_anomaly=0))

    print(f"Generating {n_faulty} faulty rows ({len(FAULT_TYPES)} fault modes, {DOUBLE_FAULT_PROB:.0%} double-faults)...")
    for i in range(n_faulty):
        base     = sample_healthy(dist)
        fault    = FAULT_TYPES[i % len(FAULT_TYPES)]
        readings = inject_fault(base, fault, dist)
        if np.random.random() < DOUBLE_FAULT_PROB:
            second   = FAULT_TYPES[(i + 2) % len(FAULT_TYPES)]
            readings = inject_fault(readings, second, dist)
        rows.append(build_row(readings, is_anomaly=1))

    df = pd.DataFrame(rows)

    output_dir  = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "training_data.csv")
    df.to_csv(output_path, index=False)

    print(f"\nSaved {len(df)} rows -> {output_path}")
    print(f"Anomaly rate  : {df['is_anomaly'].mean():.1%}  (expected ~30%)")
    print(f"Failure rate  : {df['will_fail'].mean():.1%}  (expected ~20-35%)")
    print(f"Health score  : mean={df['health_score'].mean():.1f}  "
          f"min={df['health_score'].min()}  max={df['health_score'].max()}")
    print(f"\nReal baseline : mean={dist['real_hs_mean']:.2f}  std={dist['real_hs_std']:.2f}  "
          f"(from health_features.csv nominal satellites)")
    print("\nFailure rate by anomaly label:")
    print(df.groupby("is_anomaly")["will_fail"].mean().rename("failure_rate"))


if __name__ == "__main__":
    main()
