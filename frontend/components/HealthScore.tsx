"use client";

import type { HealthScore } from "@/lib/api";

const STATUS_COLOR = {
  nominal:  { ring: "#00ff88", text: "text-green-400",  bg: "glow-green" },
  degraded: { ring: "#ffcc00", text: "text-yellow-400", bg: "glow-yellow" },
  critical: { ring: "#ff4444", text: "text-red-400",    bg: "glow-red" },
};

interface Props {
  data: HealthScore | null;
  failurePct: number | null;
  isAnomaly: boolean | null;
}

export default function HealthScoreCard({ data, failurePct, isAnomaly }: Props) {
  const score  = data?.score ?? "--";
  const status = (data?.status ?? "nominal") as keyof typeof STATUS_COLOR;
  const colors = STATUS_COLOR[status];

  const pct    = failurePct != null ? `${failurePct}%` : "--";

  const topPenalties = data?.breakdown
    ? Object.entries(data.breakdown)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .filter(([, v]) => v > 0.1)
    : [];

  return (
    <div className={`rounded-xl border border-space-border bg-space-card p-5 ${colors.bg}`}>
      <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">Health Score</p>

      {/* Big score ring */}
      <div className="flex justify-center my-3">
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="50" fill="none" stroke="#1a2540" strokeWidth="10" />
          <circle
            cx="60" cy="60" r="50"
            fill="none"
            stroke={colors.ring}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${Math.PI * 100}`}
            strokeDashoffset={`${Math.PI * 100 * (1 - (data?.score ?? 0) / 100)}`}
            transform="rotate(-90 60 60)"
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
          <text x="60" y="65" textAnchor="middle" fontSize="26" fontWeight="bold" fill={colors.ring}>
            {score}
          </text>
        </svg>
      </div>

      <p className={`text-center text-sm font-semibold uppercase tracking-widest ${colors.text}`}>
        {status}
      </p>

      <div className="mt-4 grid grid-cols-2 gap-2 text-center">
        <div className="bg-space-bg rounded-lg p-2">
          <p className="text-xs text-slate-500">Failure Risk</p>
          <p className={`font-bold text-lg ${failurePct != null && failurePct > 50 ? "text-red-400" : failurePct != null && failurePct > 25 ? "text-yellow-400" : "text-green-400"}`}>
            {pct}
          </p>
        </div>
        <div className="bg-space-bg rounded-lg p-2">
          <p className="text-xs text-slate-500">Anomaly</p>
          <p className={`font-bold text-lg ${isAnomaly ? "text-red-400" : "text-green-400"}`}>
            {isAnomaly == null ? "--" : isAnomaly ? "YES" : "NO"}
          </p>
        </div>
      </div>

      {topPenalties.length > 0 && (
        <div className="mt-3 space-y-1">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Top Penalties</p>
          {topPenalties.map(([feat, val]) => (
            <div key={feat} className="flex justify-between text-xs">
              <span className="text-slate-400">{feat.replace(/_/g, " ")}</span>
              <span className="text-orange-400 font-mono">{val.toFixed(1)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
