"use client";

import type { Telemetry } from "@/lib/api";

const BANDS: Record<string, { low: number; high: number; unit: string; danger: "high" | "low" | "both" }> = {
  thruster_temp:          { low: 20,   high: 60,   unit: "°C",  danger: "high" },
  battery_voltage:        { low: 26.5, high: 30,   unit: "V",   danger: "low"  },
  battery_temp:           { low: -5,   high: 35,   unit: "°C",  danger: "both" },
  solar_panel_current:    { low: 7,    high: 15,   unit: "A",   danger: "low"  },
  reaction_wheel_rpm:     { low: 1500, high: 5000, unit: "rpm", danger: "both" },
  comms_signal_strength:  { low: -95,  high: -40,  unit: "dBm", danger: "low"  },
  radiation_dose:         { low: 0,    high: 20,   unit: "mGy", danger: "high" },
  gyro_rate:              { low: 0,    high: 0.6,  unit: "°/s", danger: "high" },
};

function getStatus(key: string, value: number): "ok" | "warn" | "crit" {
  const b = BANDS[key];
  if (!b) return "ok";
  const { low, high, danger } = b;
  const outHigh = value > high;
  const outLow  = value < low;
  const out = danger === "high" ? outHigh : danger === "low" ? outLow : outHigh || outLow;
  if (!out) return "ok";
  const excess = outHigh ? value - high : low - value;
  const width  = high - low;
  return excess / width > 0.5 ? "crit" : "warn";
}

const STATUS_CLASS = {
  ok:   "text-green-400",
  warn: "text-yellow-400",
  crit: "text-red-400",
};

interface Props { data: Telemetry | null }

export default function TelemetryPanel({ data }: Props) {
  const readings = data?.readings ?? {};

  return (
    <div className="rounded-xl border border-space-border bg-space-card p-5">
      <div className="flex justify-between items-center mb-3">
        <p className="text-xs uppercase tracking-widest text-slate-500">Live Telemetry</p>
        {data && (
          <span className="text-xs text-slate-600 font-mono">
            {new Date(data.timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>

      <div className="space-y-2">
        {Object.entries(BANDS).map(([key, { unit }]) => {
          const val = readings[key];
          if (val == null) return null;
          const st = getStatus(key, val);
          return (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-slate-400 capitalize">{key.replace(/_/g, " ")}</span>
              <span className={`font-mono font-semibold ${STATUS_CLASS[st]}`}>
                {val.toFixed(1)} <span className="text-slate-600 font-normal text-xs">{unit}</span>
              </span>
            </div>
          );
        })}
      </div>

      {data && (
        <div className="mt-3 pt-3 border-t border-space-border flex justify-between text-xs text-slate-600">
          <span>{data.satellite_name}</span>
          <span>Kp {data.kp_index.toFixed(1)}</span>
        </div>
      )}
    </div>
  );
}
