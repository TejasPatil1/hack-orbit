"use client";

import { useState } from "react";

const RISK_COLORS = {
  green: {
    badge: "text-green-400 border-green-500/40 bg-green-900/20",
    dot: "bg-green-400",
    card: "border-green-600/40",
    cardActive: "border-green-500 bg-green-900/20 ring-1 ring-green-500/40",
    glow: "glow-green",
    action: "border-green-600/40 bg-green-950/20",
    actionText: "text-green-300",
  },
  yellow: {
    badge: "text-yellow-400 border-yellow-500/40 bg-yellow-900/20",
    dot: "bg-yellow-400",
    card: "border-yellow-600/40",
    cardActive: "border-yellow-500 bg-yellow-900/20 ring-1 ring-yellow-500/40",
    glow: "glow-yellow",
    action: "border-yellow-600/40 bg-yellow-950/20",
    actionText: "text-yellow-300",
  },
  red: {
    badge: "text-red-400 border-red-500/40 bg-red-900/20",
    dot: "bg-red-400",
    card: "border-red-600/40",
    cardActive: "border-red-500 bg-red-900/20 ring-1 ring-red-500/40",
    glow: "glow-red",
    action: "border-red-600/40 bg-red-950/20",
    actionText: "text-red-300",
  },
};

const SIM_SCENARIOS = [
  {
    id: "healthy",
    index: "01",
    label: "Healthy Operations",
    missionState: "Nominal",
    healthScore: 92,
    risk: "Low",
    riskColor: "green" as const,
    explanation:
      "All subsystems operating within nominal parameters. This scenario represents standard spacecraft operations under expected conditions with no active alerts.",
    observe: [
      "Stable telemetry across all 8 sensor channels",
      "Subsystem values within nominal operating ranges",
      "No debris objects within conjunction warning threshold",
      "Kp index below 3 — space weather conditions benign",
    ],
    operationalImpact:
      "No active operational constraints. Mission timeline proceeding as planned.",
    recommendedAction:
      "Continue standard monitoring protocols. No corrective action required.",
    aiAssessment: {
      situation: "All subsystems reporting nominal telemetry values.",
      assessment:
        "Health score of 92 reflects optimal spacecraft performance. No active anomaly flags detected. Failure probability within acceptable bounds.",
      recommendation:
        "Maintain current operational posture. No corrective action required.",
      confidence: 96,
    },
  },
  {
    id: "anomaly",
    index: "02",
    label: "Thruster Anomaly",
    missionState: "Attention Required",
    healthScore: 62,
    risk: "Elevated",
    riskColor: "yellow" as const,
    explanation:
      "Anomaly detection has flagged a thruster temperature spike above operational thresholds, triggering a subsystem health alert.",
    observe: [
      "Elevated thruster temperature — exceeding nominal by 15%",
      "Reduced health score (62) — degraded from 92 baseline",
      "Anomaly detection flag active on propulsion channel",
      "Propulsion subsystem under automated monitoring watch",
    ],
    operationalImpact:
      "Potential propulsion degradation if thermal condition persists. All scheduled maneuvers should be deferred pending investigation.",
    recommendedAction:
      "Monitor thermal subsystem closely and investigate root cause before executing any scheduled burns.",
    aiAssessment: {
      situation: "Thruster temperature exceeded operational thresholds by 15%.",
      assessment:
        "Health score degraded to 62 due to thermal anomaly in propulsion subsystem. No cascade failures detected at this time.",
      recommendation:
        "Reduce thruster load. Schedule diagnostic sequence in next available maintenance window.",
      confidence: 87,
    },
  },
  {
    id: "debris",
    index: "03",
    label: "Debris Conjunction",
    missionState: "Collision Risk",
    healthScore: 62,
    risk: "Medium",
    riskColor: "yellow" as const,
    explanation:
      "Space Surveillance Network tracking data indicates a conjunction event with a catalogued debris object on an intersecting orbital trajectory.",
    observe: [
      "Conjunction alert active — tracked object on intersecting trajectory",
      "Collision probability exceeding automated watch threshold",
      "Time-to-closest-approach narrowing over next orbital passes",
      "Risk classification elevated to Medium",
    ],
    operationalImpact:
      "Possible collision window within upcoming orbital passes. Avoidance maneuver window may be time-constrained.",
    recommendedAction:
      "Evaluate avoidance maneuver options and prepare contingency burn parameters with ground team.",
    aiAssessment: {
      situation:
        "TLE catalog match indicates conjunction event in upcoming orbital window.",
      assessment:
        "Collision probability exceeds watch threshold. Avoidance maneuver assessment required within 24 hours.",
      recommendation:
        "Coordinate delta-V computation with ground team. Hold all non-critical operations pending conjunction clearance.",
      confidence: 79,
    },
  },
  {
    id: "solar_storm",
    index: "04",
    label: "Solar Storm",
    missionState: "Environmental Threat",
    healthScore: 54,
    risk: "High",
    riskColor: "red" as const,
    explanation:
      "NOAA Space Weather Center reporting elevated geomagnetic activity. An active G3-class solar storm is affecting the operational environment.",
    observe: [
      "Kp Index at 7 — classified G3 (Strong) geomagnetic storm",
      "Elevated radiation environment across orbital plane",
      "GPS signal degradation possible — navigation reliability reduced",
      "Atmospheric drag increase due to thermospheric expansion",
    ],
    operationalImpact:
      "Reduced reliability of radiation-sensitive systems. Potential orbit decay acceleration in LEO. Power fluctuations possible.",
    recommendedAction:
      "Delay all non-critical maneuvers. Increase monitoring cadence. Prepare safe-mode standby if Kp exceeds 8.",
    aiAssessment: {
      situation:
        "Geomagnetic storm classified G3. Kp index reading 7 across multiple reporting stations.",
      assessment:
        "Health score reduced to 54 due to combined environmental stressors. Solar array output and attitude control systems may fluctuate.",
      recommendation:
        "Enter reduced-operations posture. Defer all scheduled maneuvers until Kp drops below 5.",
      confidence: 91,
    },
  },
  {
    id: "resolution",
    index: "05",
    label: "Mission Recovery",
    missionState: "Recovered",
    healthScore: 99,
    risk: "Minimal",
    riskColor: "green" as const,
    explanation:
      "Corrective actions have been executed successfully. All subsystems have returned to nominal operating parameters and mission operations are restored.",
    observe: [
      "All telemetry channels stable and within nominal ranges",
      "Risk indicators cleared — no active alert flags",
      "Health score fully restored to 99",
      "Anomaly detection flags cleared across all subsystems",
    ],
    operationalImpact:
      "No current operational constraints. Mission continuity confirmed. Full operational capability restored.",
    recommendedAction:
      "Return to nominal operations. Document recovery actions in mission log and schedule post-incident review.",
    aiAssessment: {
      situation:
        "All previously flagged anomalies resolved. Full subsystem telemetry nominal.",
      assessment:
        "Recovery actions successful. Health score restored to 99. No residual risk indicators active across any monitored channel.",
      recommendation:
        "Resume normal operational schedule. Conduct post-incident review within 48 hours.",
      confidence: 98,
    },
  },
];

interface Props {
  open: boolean;
  onClose: () => void;
  demoMode: boolean;
  onDemoModeChange: (v: boolean) => void;
}

export default function MissionSimulation({
  open,
  onClose,
  demoMode,
  onDemoModeChange,
}: Props) {
  const [selectedId, setSelectedId] = useState("healthy");

  if (!open) return null;

  const scenario =
    SIM_SCENARIOS.find((s) => s.id === selectedId) ?? SIM_SCENARIOS[0];
  const rc = RISK_COLORS[scenario.riskColor];

  const scoreColor =
    scenario.healthScore >= 80
      ? "text-green-400"
      : scenario.healthScore >= 60
      ? "text-yellow-400"
      : "text-red-400";

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/85 backdrop-blur-sm">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-b border-space-border bg-space-bg px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-0.5">
              <span className="text-xs uppercase tracking-[0.2em] text-slate-500 font-mono">
                🛰 HACKORBIT
              </span>
              <span className="text-slate-700 text-xs">|</span>
              <span className="text-xs uppercase tracking-[0.2em] text-blue-500 font-mono font-semibold">
                MISSION SIMULATION CENTER
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1">
              Guided walkthrough of satellite operational scenarios — AI-assisted decision support
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => onDemoModeChange(!demoMode)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-semibold transition-all duration-150 ${
                demoMode
                  ? "border-blue-500 bg-blue-900/30 text-blue-300 ring-1 ring-blue-500/40"
                  : "border-slate-700/60 text-slate-500 hover:border-slate-500/60 hover:text-slate-400"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  demoMode ? "bg-blue-400 animate-pulse" : "bg-slate-600"
                }`}
              />
              DEMO MODE
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-md border border-slate-700/60 text-xs text-slate-400 font-semibold hover:border-slate-500 hover:text-slate-300 transition-all duration-150"
            >
              ✕ CLOSE
            </button>
          </div>
        </div>
      </div>

      {/* ── Body ────────────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0">

        {/* ── Left: Scenario List ───────────────────────────────────────── */}
        <div className="w-72 flex-shrink-0 border-r border-space-border bg-space-card overflow-y-auto p-4 space-y-2">
          <p className="text-xs uppercase tracking-widest text-slate-600 mb-3 font-mono">
            Select Scenario
          </p>
          {SIM_SCENARIOS.map((s) => {
            const isActive = s.id === selectedId;
            const c = RISK_COLORS[s.riskColor];
            const sc =
              s.healthScore >= 80
                ? "text-green-400"
                : s.healthScore >= 60
                ? "text-yellow-400"
                : "text-red-400";
            return (
              <button
                key={s.id}
                onClick={() => setSelectedId(s.id)}
                className={`w-full text-left rounded-lg border p-3 transition-all duration-150 ${
                  isActive
                    ? `${c.cardActive} ${c.glow}`
                    : `${c.card} opacity-60 hover:opacity-100 hover:bg-space-bg`
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs font-mono text-slate-600">{s.index}</span>
                      <span
                        className={`text-xs font-bold uppercase tracking-wide truncate ${
                          isActive ? "text-slate-100" : "text-slate-400"
                        }`}
                      >
                        {s.label}
                      </span>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded border ${c.badge}`}
                    >
                      <span className={`w-1 h-1 rounded-full ${c.dot}`} />
                      {s.risk}
                    </span>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className={`text-xl font-bold font-mono ${sc}`}>
                      {s.healthScore}
                    </div>
                    <div className="text-xs text-slate-600 font-mono">HSI</div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* ── Right: Scenario Detail ────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-space-bg">

          {/* Mission State Banner */}
          <div className={`rounded-xl border p-5 ${rc.card} ${rc.glow}`}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500 font-mono mb-1">
                  SCENARIO {scenario.index} — {scenario.label}
                </p>
                <h2 className="text-2xl font-bold text-slate-100 tracking-tight mb-2">
                  {scenario.missionState}
                </h2>
                <p className="text-sm text-slate-400 leading-relaxed max-w-2xl">
                  {scenario.explanation}
                </p>
              </div>
              <div className="flex gap-6 flex-shrink-0">
                <div className="text-center">
                  <div className={`text-4xl font-bold font-mono tabular-nums ${scoreColor}`}>
                    {scenario.healthScore}
                  </div>
                  <div className="text-xs text-slate-500 font-mono uppercase tracking-widest mt-0.5">
                    Health Score
                  </div>
                </div>
                <div className="text-center">
                  <div
                    className={`text-4xl font-bold font-mono ${
                      scenario.riskColor === "green"
                        ? "text-green-400"
                        : scenario.riskColor === "yellow"
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {scenario.risk}
                  </div>
                  <div className="text-xs text-slate-500 font-mono uppercase tracking-widest mt-0.5">
                    Risk Level
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Briefing Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

            {/* What to Observe */}
            <div className="rounded-xl border border-space-border bg-space-card p-4">
              <p className="text-xs uppercase tracking-widest text-slate-500 font-mono mb-3">
                ◈ What to Observe
              </p>
              <ul className="space-y-2.5">
                {scenario.observe.map((o, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-300 leading-relaxed">
                    <span className="text-blue-400 mt-0.5 flex-shrink-0 font-mono">→</span>
                    {o}
                  </li>
                ))}
              </ul>
            </div>

            {/* Operational Impact */}
            <div className="rounded-xl border border-space-border bg-space-card p-4">
              <p className="text-xs uppercase tracking-widest text-slate-500 font-mono mb-3">
                ◈ Operational Impact
              </p>
              <p className="text-xs text-slate-300 leading-relaxed">
                {scenario.operationalImpact}
              </p>
            </div>

            {/* Operator Action */}
            <div className={`rounded-xl border p-4 ${rc.action}`}>
              <p className="text-xs uppercase tracking-widest text-slate-500 font-mono mb-3">
                ◈ Operator Action
              </p>
              <p className={`text-xs font-semibold leading-relaxed ${rc.actionText}`}>
                {scenario.recommendedAction}
              </p>
            </div>
          </div>

          {/* AI Mission Copilot */}
          <div className="rounded-xl border border-blue-800/50 bg-blue-950/20 p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-blue-400 text-xs font-mono uppercase tracking-widest font-semibold">
                ◈ AI Mission Copilot
              </span>
              <span className="text-slate-700 text-xs">—</span>
              <span className="text-xs text-slate-500">Operational Assessment</span>
              <div className="ml-auto flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                <span className="text-xs text-blue-400 font-mono tracking-widest">
                  ORBIT ONLINE
                </span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-4">
              <div>
                <p className="text-xs text-slate-600 uppercase tracking-widest font-mono mb-1.5">
                  Situation
                </p>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {scenario.aiAssessment.situation}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-600 uppercase tracking-widest font-mono mb-1.5">
                  Assessment
                </p>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {scenario.aiAssessment.assessment}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-600 uppercase tracking-widest font-mono mb-1.5">
                  Recommendation
                </p>
                <p className="text-xs text-blue-300 font-semibold leading-relaxed">
                  {scenario.aiAssessment.recommendation}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 pt-3 border-t border-blue-900/40">
              <span className="text-xs text-slate-600 font-mono uppercase tracking-widest">
                Confidence
              </span>
              <div className="flex-1 h-1.5 rounded-full bg-space-bg overflow-hidden">
                <div
                  className="h-full rounded-full bg-blue-500 transition-all duration-700"
                  style={{ width: `${scenario.aiAssessment.confidence}%` }}
                />
              </div>
              <span className="text-xs font-bold font-mono text-blue-300 tabular-nums">
                {scenario.aiAssessment.confidence}%
              </span>
            </div>
          </div>

          {/* Demo Mode status */}
          {demoMode && (
            <div className="rounded-xl border border-blue-900/40 bg-blue-950/10 px-4 py-3 flex items-center gap-3">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse flex-shrink-0" />
              <span className="text-xs text-blue-400/80">
                Demo Mode active — backend errors suppressed. Static scenario data in use. Dashboard remains fully functional.
              </span>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
