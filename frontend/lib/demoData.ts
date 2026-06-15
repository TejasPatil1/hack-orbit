import type {
  HealthScore, Telemetry, WeatherData,
  DebrisData, ForecastData, AnomalyResult,
  FailureResult, MissionBriefData,
} from "@/lib/api";

// Static demo snapshot — "Healthy Operations" scenario
// Used during the Guided Tour so judges see real values even when backend is offline.

export const DEMO_HEALTH: HealthScore = {
  score: 92,
  status: "nominal",
  breakdown: {
    radiation_dose:    4.0,
    battery_voltage:   2.0,
    gyro_rate:         1.5,
    solar_panel_current: 0.5,
  },
  primary_driver: null,
  scenario: "healthy",
};

export const DEMO_TELEMETRY: Telemetry = {
  satellite_id:   "SAT-001",
  satellite_name: "HO-SAT-001",
  scenario:       "healthy",
  timestamp:      new Date().toISOString(),
  readings: {
    thruster_temp:         38.5,
    battery_voltage:       28.4,
    battery_temp:          18.2,
    solar_panel_current:   11.7,
    reaction_wheel_rpm:    3240,
    comms_signal_strength: -72.5,
    radiation_dose:        4.8,
    gyro_rate:             0.012,
  },
  kp_index:    1.2,
  conjunction: null,
};

export const DEMO_WEATHER: WeatherData = {
  kp_index:              1.2,
  storm_level:           "Quiet",
  solar_wind_speed_km_s: 385,
  description:
    "Geomagnetic conditions are quiet. Solar wind speed nominal. No significant solar activity detected across monitored frequency bands.",
  alert:    null,
  scenario: "healthy",
};

export const DEMO_DEBRIS: DebrisData = {
  satellite_id: "SAT-001",
  objects: [
    {
      object_id:                  "2019-006H",
      name:                       "CZ-3B DEB",
      miss_distance_km:           8.4,
      relative_velocity_km_s:     6.83,
      time_to_conjunction_hours:  48.2,
      risk_level:                 "low",
      risk_score:                 0.04,
      maneuver_advised:           false,
    },
    {
      object_id:                  "2020-019C",
      name:                       "COSMOS 1408 DEB",
      miss_distance_km:           22.1,
      relative_velocity_km_s:     7.31,
      time_to_conjunction_hours:  96.5,
      risk_level:                 "low",
      risk_score:                 0.01,
      maneuver_advised:           false,
    },
    {
      object_id:                  "2016-040B",
      name:                       "SL-16 R/B DEB",
      miss_distance_km:           51.7,
      relative_velocity_km_s:     5.94,
      time_to_conjunction_hours:  144.0,
      risk_level:                 "low",
      risk_score:                 0.00,
      maneuver_advised:           false,
    },
  ],
  total_tracked: 3,
  scenario:      "healthy",
};

export const DEMO_FORECAST: ForecastData = {
  satellite_id: "SAT-001",
  days: [
    { day: 1, date: "2026-06-15", score: 92, status: "nominal" },
    { day: 2, date: "2026-06-16", score: 91, status: "nominal" },
    { day: 3, date: "2026-06-17", score: 93, status: "nominal" },
    { day: 4, date: "2026-06-18", score: 90, status: "nominal" },
    { day: 5, date: "2026-06-19", score: 88, status: "nominal" },
    { day: 6, date: "2026-06-20", score: 91, status: "nominal" },
    { day: 7, date: "2026-06-21", score: 92, status: "nominal" },
  ],
  scenario: "healthy",
};

export const DEMO_BRIEF: MissionBriefData = {
  mission_status: "NOMINAL",
  summary:
    "SAT-001 is operating nominally across all subsystems. Power generation at 95% capacity with battery voltage holding steady at 28.4 V. Attitude control is maintaining precise pointing — gyro rate 0.012 °/s, well within tolerance. No debris conjunctions within the critical 5 km threshold. Space weather conditions are benign with Kp index at 1.2.",
  key_issues: [],
  recommended_action:
    "Continue standard monitoring protocols. No corrective action required. Next scheduled maintenance window in 14 days.",
  risk_level:          "LOW",
  confidence:          96,
  health_score:        92,
  failure_probability: 0.04,
  scenario:            "healthy",
};

export const DEMO_ANOMALY: AnomalyResult = {
  is_anomaly:       false,
  anomaly_score:    -0.42,
  flagged_features: [],
  method:           "IsolationForest",
};

export const DEMO_FAILURE: FailureResult = {
  failure_probability: 4,
  top_driver:          "radiation_dose",
  health_score_used:   92,
  method:              "XGBoost",
};
