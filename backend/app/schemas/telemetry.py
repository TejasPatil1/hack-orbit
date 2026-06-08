"""
Shared telemetry schema — single source of truth for all 8 features.
Every score, model, simulator, and prompt imports from here.
Changing a range here propagates consistently to every downstream component.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Feature metadata — consumed by health score, anomaly detector, and simulator
# Weights sum to 100 intentionally so score formula is clean.
# ─────────────────────────────────────────────────────────────────────────────
FEATURE_SCHEMA: Dict[str, Dict] = {
    "thruster_temp": {
        "unit": "°C", "mean": 28.0, "std": 4.0,
        "band_low": 10.0, "band_high": 60.0,
        "weight": 38, "danger": "high",
    },
    "battery_voltage": {
        "unit": "V", "mean": 28.0, "std": 0.4,
        "band_low": 26.5, "band_high": 29.5,
        "weight": 14, "danger": "both",
    },
    "battery_temp": {
        "unit": "°C", "mean": 18.0, "std": 3.0,
        "band_low": 0.0, "band_high": 35.0,
        "weight": 8, "danger": "both",
    },
    "solar_panel_current": {
        "unit": "A", "mean": 10.0, "std": 0.8,
        "band_low": 7.0, "band_high": 13.0,
        "weight": 8, "danger": "low",
    },
    "gyro_rate": {
        "unit": "°/s", "mean": 0.15, "std": 0.08,
        "band_low": 0.0, "band_high": 0.6,
        "weight": 10, "danger": "high",
    },
    "reaction_wheel_rpm": {
        "unit": "rpm", "mean": 3000.0, "std": 400.0,
        "band_low": 1500.0, "band_high": 5000.0,
        "weight": 6, "danger": "both",
    },
    "comms_signal_strength": {
        "unit": "dB", "mean": -80.0, "std": 4.0,
        "band_low": -95.0, "band_high": -65.0,
        "weight": 6, "danger": "low",
    },
    "radiation_dose": {
        "unit": "rad/hr", "mean": 5.0, "std": 1.5,
        "band_low": 0.0, "band_high": 20.0,
        "weight": 10, "danger": "high",
    },
}

FEATURE_NAMES: List[str] = list(FEATURE_SCHEMA.keys())


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic request/response models
# ─────────────────────────────────────────────────────────────────────────────

class TelemetryReading(BaseModel):
    """Raw telemetry snapshot from a satellite."""
    satellite_id: str = "SAT-001"
    timestamp: Optional[datetime] = None
    thruster_temp: float = Field(..., description="Thruster temperature °C")
    battery_voltage: float = Field(..., description="Battery voltage V")
    battery_temp: float = Field(..., description="Battery temperature °C")
    solar_panel_current: float = Field(..., description="Solar panel current A")
    gyro_rate: float = Field(..., description="Gyro rate °/s")
    reaction_wheel_rpm: float = Field(..., description="Reaction wheel rpm")
    comms_signal_strength: float = Field(..., description="Comms signal dB")
    radiation_dose: float = Field(..., description="Radiation dose rad/hr")

    def to_feature_dict(self) -> Dict[str, float]:
        return {k: getattr(self, k) for k in FEATURE_NAMES}


class ConjunctionData(BaseModel):
    """Orbital conjunction / debris close-approach geometry."""
    object_id: str = "TBA-4821"
    miss_distance_km: float = 4.2
    relative_velocity_km_s: float = 7.2
    time_to_conjunction_hours: float = 3.5


class AnomalyRequest(BaseModel):
    telemetry: TelemetryReading


class FailurePredictRequest(BaseModel):
    telemetry: TelemetryReading


class CollisionRiskRequest(BaseModel):
    conjunction: ConjunctionData
    kp_index: float = 2.0


class WhatIfRequest(BaseModel):
    telemetry: TelemetryReading
    overrides: Dict[str, float] = {}  # feature_name → new_value


class ManeuverRequest(BaseModel):
    telemetry: TelemetryReading
    conjunction: Optional[ConjunctionData] = None
    kp_index: float = 2.0


class CopilotRequest(BaseModel):
    message: str
    telemetry: TelemetryReading
    conjunction: Optional[ConjunctionData] = None
    kp_index: float = 2.0


class IncidentReportRequest(BaseModel):
    telemetry: TelemetryReading
    conjunction: Optional[ConjunctionData] = None
    kp_index: float = 2.0


class InjectAnomalyRequest(BaseModel):
    scenario: str = "anomaly"  # healthy | anomaly | debris | solar_storm | resolution


# ─────────────────────────────────────────────────────────────────────────────
# Demo scenario telemetry — 5 canonical states the demo cycles through.
# Phase 2 ML models are tuned to produce correct outputs for these exact values.
# ─────────────────────────────────────────────────────────────────────────────

DEMO_TELEMETRY: Dict[str, Dict[str, Any]] = {
    "healthy": {
        # Each feature drifted ~0.447 of its half-band from mean so that
        # SOFT_WEIGHT=5 produces total penalty ≈ 8 → score ≈ 92.
        # All values verified inside both the green band AND the 3σ bound
        # so the anomaly detector stays quiet (spec §3.3, §4.3).
        "thruster_temp": 39.2,        # mean 28 ± 3σ=[16,40]  → 39.2 inside
        "battery_voltage": 28.67,     # mean 28 ± 3σ=[26.8,29.2]
        "battery_temp": 25.8,         # mean 18 ± 3σ=[9,27]
        "solar_panel_current": 8.66,  # mean 10 ± 3σ=[7.6,12.4]
        "gyro_rate": 0.284,           # mean 0.15 ± 3σ=[0,0.39]
        "reaction_wheel_rpm": 3782.0, # mean 3000 ± 3σ=[1800,4200]
        "comms_signal_strength": -86.7, # mean -80 ± 3σ=[-92,-68]
        "radiation_dose": 9.3,        # mean 5 ± 3σ=[0.5,9.5]
    },
    "anomaly": {
        "thruster_temp": 340.0,   # Spike — thruster_overheat fault
        "battery_voltage": 27.9,
        "battery_temp": 20.1,
        "solar_panel_current": 10.0,
        "gyro_rate": 0.16,
        "reaction_wheel_rpm": 3020.0,
        "comms_signal_strength": -80.5,
        "radiation_dose": 5.1,
    },
    "debris": {
        # Same thermal anomaly, but now conjunction TBA-4821 is active
        "thruster_temp": 340.0,
        "battery_voltage": 27.9,
        "battery_temp": 20.1,
        "solar_panel_current": 10.0,
        "gyro_rate": 0.16,
        "reaction_wheel_rpm": 3020.0,
        "comms_signal_strength": -80.5,
        "radiation_dose": 5.1,
    },
    "solar_storm": {
        # Kp 7 storm adds radiation/comms/power hits on top of thruster fault
        "thruster_temp": 340.0,
        "battery_voltage": 26.1,
        "battery_temp": 36.5,
        "solar_panel_current": 6.8,
        "gyro_rate": 0.65,
        "reaction_wheel_rpm": 3020.0,
        "comms_signal_strength": -93.0,
        "radiation_dose": 22.0,
    },
    "resolution": {
        # Operator reduced thruster load — score recovers.
        # thruster_temp kept below 3σ bound (40°C) so anomaly detector stays quiet.
        "thruster_temp": 35.0,
        "battery_voltage": 27.8,
        "battery_temp": 20.0,
        "solar_panel_current": 9.8,
        "gyro_rate": 0.15,
        "reaction_wheel_rpm": 2980.0,
        "comms_signal_strength": -81.0,
        "radiation_dose": 5.2,
    },
}

DEMO_KP: Dict[str, float] = {
    "healthy": 2.0,
    "anomaly": 2.0,
    "debris": 2.0,
    "solar_storm": 7.0,
    "resolution": 3.0,
}

DEMO_CONJUNCTION: Dict[str, Optional[Dict]] = {
    "healthy": None,
    "anomaly": None,
    "debris": {
        "object_id": "TBA-4821",
        "miss_distance_km": 4.2,
        "relative_velocity_km_s": 7.2,
        "time_to_conjunction_hours": 3.5,
    },
    "solar_storm": {
        "object_id": "TBA-4821",
        "miss_distance_km": 4.2,
        "relative_velocity_km_s": 7.2,
        "time_to_conjunction_hours": 3.5,
    },
    "resolution": None,
}

VALID_SCENARIOS = set(DEMO_TELEMETRY.keys())
