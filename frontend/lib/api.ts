const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

// ── Response types ────────────────────────────────────────────────────────────

export interface HealthScore {
  score: number;
  status: "nominal" | "degraded" | "critical";
  breakdown: Record<string, number>;
  primary_driver: string | null;
  scenario: string;
}

export interface Telemetry {
  satellite_id: string;
  satellite_name: string;
  scenario: string;
  timestamp: string;
  readings: Record<string, number>;
  kp_index: number;
  conjunction: ConjunctionInfo | null;
}

export interface ConjunctionInfo {
  object_id: string;
  miss_distance_km: number;
  time_to_conjunction_hours: number;
  risk_level: string;
}

export interface WeatherData {
  kp_index: number;
  storm_level: string;
  solar_wind_speed_km_s: number;
  description: string;
  alert: string | null;
  scenario: string;
}

export interface DebrisObject {
  object_id: string;
  name: string;
  miss_distance_km: number;
  relative_velocity_km_s: number;
  time_to_conjunction_hours: number;
  risk_level: string;
  risk_score: number;
  maneuver_advised: boolean;
}

export interface DebrisData {
  satellite_id: string;
  objects: DebrisObject[];
  total_tracked: number;
  scenario: string;
}

export interface ForecastDay {
  day: number;
  date: string;
  score: number;
  status: string;
}

export interface ForecastData {
  satellite_id: string;
  days: ForecastDay[];
  scenario: string;
}

export interface CopilotReply {
  reply: string;
  source: "llm" | "fallback";
  scenario: string;
}

export interface AnomalyResult {
  is_anomaly: boolean;
  anomaly_score: number;
  flagged_features: string[];
  scenario: string;
}

export interface FailureResult {
  failure_probability_pct: number;
  risk_tier: string;
  top_driver: string;
  scenario: string;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const api = {
  healthScore:   ()                          => get<HealthScore>("/api/health-score"),
  telemetry:     ()                          => get<Telemetry>("/api/telemetry"),
  weather:       ()                          => get<WeatherData>("/api/weather"),
  debris:        ()                          => get<DebrisData>("/api/debris"),
  forecast:      ()                          => get<ForecastData>("/api/forecast"),

  injectScenario: (scenario: string)         => post<{ scenario: string; status: string }>("/api/inject-anomaly", { scenario }),

  copilot: (message: string)                 => post<CopilotReply>("/api/copilot", { message, satellite_id: "SAT-001" }),

  detectAnomaly: (readings: Record<string, number>) =>
    post<AnomalyResult>("/api/detect-anomaly", { satellite_id: "SAT-001", readings }),

  predictFailure: (readings: Record<string, number>) =>
    post<FailureResult>("/api/predict-failure", { satellite_id: "SAT-001", readings }),
};
