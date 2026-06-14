"use client";

import { useEffect, useRef, useState } from "react";
import type { Telemetry } from "@/lib/api";

const BANDS: Record<string, {
  low: number; high: number; unit: string;
  danger: "high" | "low" | "both";
  noiseScale: number;
}> = {
  thruster_temp:         { low: 20,   high: 60,   unit: "°C",  danger: "high", noiseScale: 0.8  },
  battery_voltage:       { low: 26.5, high: 30,   unit: "V",   danger: "low",  noiseScale: 0.04 },
  battery_temp:          { low: -5,   high: 35,   unit: "°C",  danger: "both", noiseScale: 0.3  },
  solar_panel_current:   { low: 7,    high: 15,   unit: "A",   danger: "low",  noiseScale: 0.1  },
  reaction_wheel_rpm:    { low: 1500, high: 5000, unit: "rpm", danger: "both", noiseScale: 15   },
  comms_signal_strength: { low: -95,  high: -40,  unit: "dBm", danger: "low",  noiseScale: 0.5  },
  radiation_dose:        { low: 0,    high: 20,   unit: "mGy", danger: "high", noiseScale: 0.15 },
  gyro_rate:             { low: 0,    high: 0.6,  unit: "°/s", danger: "high", noiseScale: 0.004 },
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
  crit: "text-red-400 animate-pulse",
};

const LABEL: Record<string, string> = {
  thruster_temp:         "Thruster Temp",
  battery_voltage:       "Battery Voltage",
  battery_temp:          "Battery Temp",
  solar_panel_current:   "Solar Current",
  reaction_wheel_rpm:    "Wheel RPM",
  comms_signal_strength: "Signal Strength",
  radiation_dose:        "Radiation Dose",
  gyro_rate:             "Gyro Rate",
};

interface Props { data: Telemetry | null }

export default function TelemetryPanel({ data }: Props) {
  const baseRef = useRef<Record<string, number>>({});
  const [live, setLive]     = useState<Record<string, number>>({});
  const [deltas, setDeltas] = useState<Record<string, "up" | "down" | "">>({});
  const prevRef = useRef<Record<string, number>>({});

  // Sync base values when backend data changes (scenario switches)
  useEffect(() => {
    if (data?.readings) {
      baseRef.current = data.readings;
      setLive(data.readings);
      prevRef.current = data.readings;
      setDeltas({});
    }
  }, [data?.readings]);

  // Client-side noise tick — 1.5 s interval makes it feel live
  useEffect(() => {
    const id = setInterval(() => {
      const base = baseRef.current;
      if (!Object.keys(base).length) return;

      const next: Record<string, number> = {};
      const newDeltas: Record<string, "up" | "down" | ""> = {};

      for (const [key, val] of Object.entries(base)) {
        const b = BANDS[key];
        // Gaussian-ish noise from two uniform samples (Box-Muller approximation)
        const noise = b
          ? (Math.random() - 0.5) * 2 * b.noiseScale
          : 0;
        next[key] = val + noise;
        const prev = prevRef.current[key] ?? val;
        newDeltas[key] = Math.abs(next[key] - prev) > b?.noiseScale * 0.1
          ? next[key] > prev ? "up" : "down"
          : "";
      }

      prevRef.current = next;
      setLive(next);
      setDeltas(newDeltas);
    }, 1500);

    return () => clearInterval(id);
  }, []);

  if (!data) {
    return (
      <div className="rounded-xl border border-space-border bg-space-card p-5">
        <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">Live Telemetry</p>
        <div className="space-y-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex justify-between animate-pulse">
              <div className="h-3 bg-space-bg rounded w-28" />
              <div className="h-3 bg-space-bg rounded w-16" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const readings = Object.keys(BANDS).filter((k) => live[k] != null);

  return (
    <div className="rounded-xl border border-space-border bg-space-card p-5">
      <div className="flex justify-between items-center mb-3">
        <p className="text-xs uppercase tracking-widest text-slate-500">Live Telemetry</p>
        <span className="flex items-center gap-1 text-xs text-blue-500">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          Streaming
        </span>
      </div>

      <div className="space-y-2.5">
        {readings.map((key) => {
          const val = live[key]!;
          const b   = BANDS[key];
          const st  = getStatus(key, val);
          const delta = deltas[key];
          const decimals = b.noiseScale < 0.01 ? 3 : b.noiseScale < 1 ? 2 : b.noiseScale < 10 ? 1 : 0;

          return (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-slate-400 text-xs">{LABEL[key] ?? key.replace(/_/g, " ")}</span>
              <span className={`font-mono font-semibold tabular-nums ${STATUS_CLASS[st]}`}>
                {val.toFixed(decimals)}
                <span className="text-slate-600 font-normal text-xs ml-0.5">{b.unit}</span>
                {delta === "up"   && <span className="text-slate-600 text-xs ml-0.5">↑</span>}
                {delta === "down" && <span className="text-slate-600 text-xs ml-0.5">↓</span>}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-3 pt-3 border-t border-space-border flex justify-between text-xs text-slate-600">
        <span>{data.satellite_name}</span>
        <span>Kp {data.kp_index.toFixed(1)}</span>
      </div>
    </div>
  );
}
