"use client";

import type { WeatherData } from "@/lib/api";

const KP_COLOR = (kp: number) =>
  kp >= 7 ? "text-red-400" :
  kp >= 5 ? "text-yellow-400" :
  kp >= 4 ? "text-orange-400" :
            "text-green-400";

const STORM_ICONS: Record<string, string> = {
  quiet: "🟢",
  unsettled: "🟡",
  active: "🟠",
  minor: "🟠",
  moderate: "🔴",
  strong: "🔴",
  severe: "💥",
  extreme: "💥",
};

interface Props { data: WeatherData | null }

export default function WeatherPanel({ data }: Props) {
  return (
    <div className={`rounded-xl border bg-space-card p-5 ${data?.alert ? "border-red-500/60 glow-red" : "border-space-border"}`}>
      <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">Space Weather</p>

      {data ? (
        <>
          {data.alert && (
            <div className="mb-3 rounded-md bg-red-950/60 border border-red-500/50 px-3 py-2 text-xs text-red-300 font-semibold">
              {data.alert}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-space-bg rounded-lg p-3 text-center">
              <p className="text-xs text-slate-500 mb-1">Kp Index</p>
              <p className={`text-2xl font-bold ${KP_COLOR(data.kp_index)}`}>
                {data.kp_index.toFixed(1)}
              </p>
            </div>
            <div className="bg-space-bg rounded-lg p-3 text-center">
              <p className="text-xs text-slate-500 mb-1">Storm Level</p>
              <p className="text-base font-semibold text-slate-300">
                {STORM_ICONS[data.storm_level] ?? "⚪"} {data.storm_level}
              </p>
            </div>
          </div>

          <div className="bg-space-bg rounded-lg p-3 flex justify-between items-center">
            <span className="text-xs text-slate-500">Solar Wind</span>
            <span className="text-sm font-mono text-blue-400">{data.solar_wind_speed_km_s} km/s</span>
          </div>

          <p className="mt-3 text-xs text-slate-500 leading-relaxed">{data.description}</p>
        </>
      ) : (
        <div className="h-32 flex items-center justify-center text-slate-600 text-sm">Loading…</div>
      )}
    </div>
  );
}
