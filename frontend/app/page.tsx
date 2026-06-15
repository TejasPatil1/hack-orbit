"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type {
  HealthScore, Telemetry, WeatherData,
  DebrisData, ForecastData, AnomalyResult, FailureResult,
  MissionBriefData,
} from "@/lib/api";

import AlertBanner        from "@/components/AlertBanner";
import ScenarioSwitcher   from "@/components/ScenarioSwitcher";
import HealthScoreCard    from "@/components/HealthScore";
import TelemetryPanel     from "@/components/TelemetryPanel";
import WeatherPanel       from "@/components/WeatherPanel";
import DebrisPanel        from "@/components/DebrisPanel";
import ForecastChart      from "@/components/ForecastChart";
import MissionBrief       from "@/components/MissionBrief";
import SystemStatus       from "@/components/SystemStatus";
import MissionSimulation  from "@/components/MissionSimulation";
import DashboardTour      from "@/components/DashboardTour";
import CopilotSidebar     from "@/components/CopilotSidebar";
import CopilotBar         from "@/components/CopilotBar";
import {
  DEMO_HEALTH, DEMO_TELEMETRY, DEMO_WEATHER,
  DEMO_DEBRIS, DEMO_FORECAST, DEMO_BRIEF,
  DEMO_ANOMALY, DEMO_FAILURE,
} from "@/lib/demoData";

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
  const [simOpen,      setSimOpen]      = useState(false);
  const [demoMode,     setDemoMode]     = useState(false);
  const [tourOpen,     setTourOpen]     = useState(false);
  const [copilotOpen,  setCopilotOpen]  = useState(false);

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

  // Auto-start the guided tour on first load after page settles
  useEffect(() => {
    const t = setTimeout(() => setTourOpen(true), 900);
    return () => clearTimeout(t);
  }, []);

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

  // When the tour is open, show static demo data so judges see full panels
  // even if the backend is offline.
  const d = tourOpen;
  const displayHealth    = d ? DEMO_HEALTH    : health;
  const displayTelemetry = d ? DEMO_TELEMETRY : telemetry;
  const displayWeather   = d ? DEMO_WEATHER   : weather;
  const displayDebris    = d ? DEMO_DEBRIS    : debris;
  const displayForecast  = d ? DEMO_FORECAST  : forecast;
  const displayBrief     = d ? DEMO_BRIEF     : brief;
  const displayAnomaly   = d ? DEMO_ANOMALY   : anomaly;
  const displayFailure   = d ? DEMO_FAILURE   : failure;

  const isAnomaly  = displayAnomaly?.is_anomaly ?? null;
  const stormAlert = displayWeather?.alert ?? null;

  return (
    <div className="min-h-screen bg-space-bg p-4 md:p-5">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="mb-1" data-tour="header">
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

          <div className="flex flex-wrap items-center gap-2">
            {/* Tour button */}
            <button
              onClick={() => setTourOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-slate-700/60 bg-space-card text-xs font-semibold text-slate-400 hover:border-slate-500 hover:text-slate-200 transition-all duration-150 uppercase tracking-widest"
            >
              <span className="text-slate-500">◎</span>
              Guided Tour
            </button>

            {/* AI Copilot sidebar toggle */}
            <button
              data-tour="copilot"
              onClick={() => setCopilotOpen((v) => !v)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-semibold transition-all duration-150 uppercase tracking-widest ${
                copilotOpen
                  ? "border-green-500/60 bg-green-900/20 text-green-300"
                  : "border-slate-700/60 bg-space-card text-slate-400 hover:border-green-500/40 hover:text-green-400"
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${copilotOpen ? "bg-green-400 animate-pulse" : "bg-slate-600"}`} />
              AI Copilot
            </button>

            {/* Mission Simulation button */}
            <button
              data-tour="sim-button"
              onClick={() => setSimOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-slate-600/50 bg-space-card text-xs font-semibold text-slate-300 hover:border-blue-500/60 hover:text-blue-300 hover:bg-blue-950/20 transition-all duration-150 uppercase tracking-widest"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400/70" />
              Mission Simulation
            </button>

            {/* Scenario Switcher */}
            <div data-tour="scenario-switcher">
              <ScenarioSwitcher active={scenario} onSelect={switchScenario} loading={switching} />
            </div>
          </div>
        </div>
        <SystemStatus backendOnline={!error} lastSync={lastSync} />
      </header>

      {/* ── Error banner ───────────────────────────────────────────────────── */}
      {error && !demoMode && (
        <div className="mb-3 rounded-lg border border-orange-500/40 bg-orange-950/30 px-4 py-3 text-sm text-orange-300">
          ⚠ {error}
        </div>
      )}

      {/* ── AI Copilot rotating insight bar (demo mode) ────────────────────── */}
      {demoMode && <CopilotBar onOpenCopilot={() => setCopilotOpen(true)} />}

      {/* ── Alert banners ──────────────────────────────────────────────────── */}
      {(isAnomaly || stormAlert) && (
        <div className="mb-3 space-y-2">
          {stormAlert && (
            <AlertBanner alert={stormAlert} isAnomaly={false} primaryDriver={null} />
          )}
          {isAnomaly && (
            <AlertBanner alert={null} isAnomaly={true} primaryDriver={displayHealth?.primary_driver ?? null} />
          )}
        </div>
      )}

      {/* ── Row 1: Health Score (1/3) + Mission Brief (2/3) ────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div data-tour="health-score">
          <HealthScoreCard
            data={displayHealth}
            failurePct={displayFailure?.failure_probability ?? null}
            isAnomaly={isAnomaly}
          />
        </div>
        <div className="md:col-span-2" data-tour="mission-brief">
          <MissionBrief data={displayBrief} />
        </div>
      </div>

      {/* ── Row 2: Telemetry | Weather | Debris ────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div data-tour="telemetry">
          <TelemetryPanel data={displayTelemetry} />
        </div>
        <div data-tour="weather">
          <WeatherPanel data={displayWeather} />
        </div>
        <div data-tour="debris">
          <DebrisPanel data={displayDebris} />
        </div>
      </div>

      {/* ── Row 3: 7-Day Forecast ──────────────────────────────────────────── */}
      <div className="mb-4" data-tour="forecast">
        <ForecastChart data={displayForecast} />
      </div>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer className="mt-5 text-center text-xs text-slate-700">
        Hack Orbit · Predict. Protect. Decide. · polling {POLL_MS / 1000}s · telemetry 1.5s
      </footer>

      {/* ── Mission Simulation Modal ────────────────────────────────────────── */}
      <MissionSimulation
        open={simOpen}
        onClose={() => setSimOpen(false)}
        demoMode={demoMode}
        onDemoModeChange={setDemoMode}
      />

      {/* ── AI Copilot Sidebar ─────────────────────────────────────────────── */}
      <CopilotSidebar
        open={copilotOpen}
        onClose={() => setCopilotOpen(false)}
        telemetry={displayTelemetry}
      />

      {/* ── Guided Tour ────────────────────────────────────────────────────── */}
      {tourOpen && <DashboardTour onClose={() => setTourOpen(false)} />}
    </div>
  );
}
