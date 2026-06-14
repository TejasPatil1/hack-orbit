"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type {
  HealthScore, Telemetry, WeatherData,
  DebrisData, ForecastData, AnomalyResult, FailureResult,
  MissionBriefData,
} from "@/lib/api";

import AlertBanner      from "@/components/AlertBanner";
import ScenarioSwitcher from "@/components/ScenarioSwitcher";
import HealthScoreCard  from "@/components/HealthScore";
import TelemetryPanel   from "@/components/TelemetryPanel";
import WeatherPanel     from "@/components/WeatherPanel";
import DebrisPanel      from "@/components/DebrisPanel";
import ForecastChart    from "@/components/ForecastChart";
import CopilotChat      from "@/components/CopilotChat";
import MissionBrief     from "@/components/MissionBrief";
import SystemStatus     from "@/components/SystemStatus";

const POLL_MS = 4000;

export default function Dashboard() {
  const [health,    setHealth]    = useState<HealthScore | null>(null);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [weather,   setWeather]   = useState<WeatherData | null>(null);
  const [debris,    setDebris]    = useState<DebrisData | null>(null);
  const [forecast,  setForecast]  = useState<ForecastData | null>(null);
  const [brief,     setBrief]     = useState<MissionBriefData | null>(null);
  const [anomaly,   setAnomaly]   = useState<AnomalyResult | null>(null);
  const [failure,   setFailure]   = useState<FailureResult | null>(null);

  const [scenario,  setScenario]  = useState("healthy");
  const [switching, setSwitching] = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const [lastSync,  setLastSync]  = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [h, t, w, d, f, b] = await Promise.all([
        api.healthScore(),
        api.telemetry(),
        api.weather(),
        api.debris(),
        api.forecast(),
        api.missionBrief(),
      ]);
      setHealth(h);
      setTelemetry(t);
      setWeather(w);
      setDebris(d);
      setForecast(f);
      setBrief(b);
      setScenario(h.scenario);
      setLastSync(new Date());
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

  const isAnomaly  = anomaly?.is_anomaly ?? null;
  const stormAlert = weather?.alert ?? null;

  return (
    <div className="min-h-screen bg-space-bg p-4 md:p-5">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="mb-1">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
          <div>
            <h1 className="text-base font-bold text-slate-100 tracking-tight">
              🛰 Hack Orbit
              <span className="ml-2 text-xs font-normal text-slate-600 tracking-normal">
                AI Mission Intelligence Copilot
              </span>
            </h1>
            <p className="text-xs text-slate-600 mt-0.5">
              SAT-001 (HO-SAT-001) · LEO 550 km · 53° incl.
            </p>
          </div>
          <ScenarioSwitcher active={scenario} onSelect={switchScenario} loading={switching} />
        </div>
        <SystemStatus backendOnline={!error} lastSync={lastSync} />
      </header>

      {/* ── Error banner ───────────────────────────────────────────────────── */}
      {error && (
        <div className="mb-3 rounded-lg border border-orange-500/40 bg-orange-950/30 px-4 py-3 text-sm text-orange-300">
          ⚠ {error}
        </div>
      )}

      {/* ── Alert banners ──────────────────────────────────────────────────── */}
      {(isAnomaly || stormAlert) && (
        <div className="mb-3 space-y-2">
          {stormAlert && (
            <AlertBanner alert={stormAlert} isAnomaly={false} primaryDriver={null} />
          )}
          {isAnomaly && (
            <AlertBanner alert={null} isAnomaly={true} primaryDriver={health?.primary_driver ?? null} />
          )}
        </div>
      )}

      {/* ── Row 1: Health Score (1/3) + Mission Brief (2/3) ────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <HealthScoreCard
          data={health}
          failurePct={failure?.failure_probability ?? null}
          isAnomaly={isAnomaly}
        />
        <div className="md:col-span-2">
          <MissionBrief data={brief} />
        </div>
      </div>

      {/* ── Row 2: Telemetry | Weather | Debris ────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <TelemetryPanel data={telemetry} />
        <WeatherPanel   data={weather}   />
        <DebrisPanel    data={debris}    />
      </div>

      {/* ── Row 3: 7-Day Forecast ──────────────────────────────────────────── */}
      <div className="mb-4">
        <ForecastChart data={forecast} />
      </div>

      {/* ── Row 4: AI Copilot ──────────────────────────────────────────────── */}
      <CopilotChat telemetry={telemetry} />

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer className="mt-5 text-center text-xs text-slate-700">
        Hack Orbit · Predict. Protect. Decide. · polling {POLL_MS / 1000}s · telemetry 1.5s
      </footer>
    </div>
  );
}
