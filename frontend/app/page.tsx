"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type {
  HealthScore, Telemetry, WeatherData,
  DebrisData, ForecastData, AnomalyResult, FailureResult,
} from "@/lib/api";

import AlertBanner      from "@/components/AlertBanner";
import ScenarioSwitcher from "@/components/ScenarioSwitcher";
import HealthScoreCard  from "@/components/HealthScore";
import TelemetryPanel   from "@/components/TelemetryPanel";
import WeatherPanel     from "@/components/WeatherPanel";
import DebrisPanel      from "@/components/DebrisPanel";
import ForecastChart    from "@/components/ForecastChart";
import CopilotChat      from "@/components/CopilotChat";

const POLL_MS = 4000;

export default function Dashboard() {
  const [health,    setHealth]   = useState<HealthScore | null>(null);
  const [telemetry, setTelemetry]= useState<Telemetry | null>(null);
  const [weather,   setWeather]  = useState<WeatherData | null>(null);
  const [debris,    setDebris]   = useState<DebrisData | null>(null);
  const [forecast,  setForecast] = useState<ForecastData | null>(null);
  const [anomaly,   setAnomaly]  = useState<AnomalyResult | null>(null);
  const [failure,   setFailure]  = useState<FailureResult | null>(null);

  const [scenario,  setScenario] = useState("healthy");
  const [switching, setSwitching]= useState(false);
  const [error,     setError]    = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [h, t, w, d, f] = await Promise.all([
        api.healthScore(), api.telemetry(), api.weather(), api.debris(), api.forecast(),
      ]);
      setHealth(h);
      setTelemetry(t);
      setWeather(w);
      setDebris(d);
      setForecast(f);
      setScenario(h.scenario);
      setError(null);

      if (t.readings && Object.keys(t.readings).length > 0) {
        const [an, fa] = await Promise.all([
          api.detectAnomaly(t.readings),
          api.predictFailure(t.readings),
        ]);
        setAnomaly(an);
        setFailure(fa);
      }
    } catch (e: any) {
      setError(e?.message ?? "Backend unreachable — is it running on port 8000?");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  async function switchScenario(s: string) {
    setSwitching(true);
    try {
      await api.injectScenario(s);
      setScenario(s);
      await refresh();
    } catch {
      setError("Failed to switch scenario.");
    } finally {
      setSwitching(false);
    }
  }

  const isAnomaly = anomaly?.is_anomaly ?? null;
  const stormAlert = weather?.alert ?? null;

  return (
    <div className="min-h-screen bg-space-bg p-4 md:p-6">
      {/* Header */}
      <header className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 tracking-tight">
            🛰 Hack Orbit
          </h1>
          <p className="text-xs text-slate-500">AI Mission Intelligence Copilot · SAT-001 · LEO 550 km</p>
        </div>
        <ScenarioSwitcher active={scenario} onSelect={switchScenario} loading={switching} />
      </header>

      {/* Error state */}
      {error && (
        <div className="mb-4 rounded-lg border border-orange-500/40 bg-orange-950/30 px-4 py-3 text-sm text-orange-300">
          ⚠ {error}
        </div>
      )}

      {/* Alert banners */}
      {(isAnomaly || stormAlert) && (
        <div className="mb-4 space-y-2">
          {stormAlert && <AlertBanner alert={stormAlert} isAnomaly={false} primaryDriver={null} />}
          {isAnomaly  && <AlertBanner alert={null}       isAnomaly={true}  primaryDriver={health?.primary_driver ?? null} />}
        </div>
      )}

      {/* Top row: Health | Telemetry | Weather */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <HealthScoreCard
          data={health}
          failurePct={failure?.failure_probability_pct ?? null}
          isAnomaly={isAnomaly}
        />
        <TelemetryPanel data={telemetry} />
        <WeatherPanel   data={weather}   />
      </div>

      {/* Mid row: Debris | Forecast */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <DebrisPanel  data={debris}   />
        <ForecastChart data={forecast} />
      </div>

      {/* Copilot full width */}
      <CopilotChat />

      {/* Footer */}
      <footer className="mt-6 text-center text-xs text-slate-700">
        Hack Orbit · Predict. Protect. Decide. · Polling every {POLL_MS / 1000}s
      </footer>
    </div>
  );
}
