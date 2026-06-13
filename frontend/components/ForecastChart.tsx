"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer,
} from "recharts";
import type { ForecastData } from "@/lib/api";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const score = payload[0].value as number;
  const status = score >= 80 ? "nominal" : score >= 50 ? "degraded" : "critical";
  const color  = score >= 80 ? "#00ff88" : score >= 50 ? "#ffcc00" : "#ff4444";
  return (
    <div className="bg-space-card border border-space-border rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-slate-400">{label}</p>
      <p style={{ color }} className="font-bold text-base">{score}</p>
      <p className="text-slate-500 capitalize">{status}</p>
    </div>
  );
};

interface Props { data: ForecastData | null }

export default function ForecastChart({ data }: Props) {
  const points = data?.days.map((d) => ({
    date: d.date.slice(5),
    score: d.score,
    status: d.status,
  })) ?? [];

  return (
    <div className="rounded-xl border border-space-border bg-space-card p-5">
      <p className="text-xs uppercase tracking-widest text-slate-500 mb-4">7-Day Mission Forecast</p>

      {points.length > 0 ? (
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <CartesianGrid stroke="#1a2540" strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fill: "#475569", fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fill: "#475569", fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={80} stroke="#00ff88" strokeDasharray="4 4" strokeOpacity={0.4} label={{ value: "80", fill: "#00ff88", fontSize: 10, position: "right" }} />
            <ReferenceLine y={50} stroke="#ffcc00" strokeDasharray="4 4" strokeOpacity={0.4} label={{ value: "50", fill: "#ffcc00", fontSize: 10, position: "right" }} />
            <Line
              type="monotone" dataKey="score"
              stroke="#00aaff" strokeWidth={2} dot={{ fill: "#00aaff", r: 3 }}
              activeDot={{ r: 5, fill: "#00aaff" }}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-44 flex items-center justify-center text-slate-600 text-sm">Loading…</div>
      )}
    </div>
  );
}
