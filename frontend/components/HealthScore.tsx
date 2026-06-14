"use client";

import type { HealthScore } from "@/lib/api";

const STATUS_COLOR = {
  nominal:  { ring: "#00ff88", text: "text-green-400",  bg: "glow-green",  badge: "text-green-400  bg-green-900/20  border-green-500/30"  },
  degraded: { ring: "#ffcc00", text: "text-yellow-400", bg: "glow-yellow", badge: "text-yellow-400 bg-yellow-900/20 border-yellow-500/30" },
  critical: { ring: "#ff4444", text: "text-red-400",    bg: "glow-red",    badge: "text-red-400    bg-red-900/20    border-red-500/30"    },
};

function riskTier(pct: number): { label: string; cls: string; barCls: string } {
  if (pct >= 70) return { label: "CRITICAL",  cls: "text-red-400",    barCls: "bg-red-500/70"    };
  if (pct >= 40) return { label: "HIGH",      cls: "text-orange-400", barCls: "bg-orange-500/70" };
  if (pct >= 20) return { label: "ELEVATED",  cls: "text-yellow-400", barCls: "bg-yellow-500/70" };
  return           { label: "LOW",       cls: "text-green-400",  barCls: "bg-green-500/70"  };
}

interface Props {
  data: HealthScore | null;
  failurePct: number | null;
  isAnomaly: boolean | null;
}

export default function HealthScoreCard({ data, failurePct, isAnomaly }: Props) {
  const score  = data?.score ?? 0;
  const status = (data?.status ?? "nominal") as keyof typeof STATUS_COLOR;
  const colors = STATUS_COLOR[status];
  const tier   = failurePct != null ? riskTier(failurePct) : null;

  // Risk drivers from penalty breakdown
  const totalPenalty = Math.max(1, 100 - score);
  const drivers = data?.breakdown
    ? Object.entries(data.breakdown)
        .filter(([, v]) => v > 0.5)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([feat, penalty]) => ({
          name: feat.replace(/_/g, " "),
          pct:  Math.round((penalty / totalPenalty) * 100),
        }))
    : [];

  if (!data) {
    return (
      <div className="rounded-xl border border-space-border bg-space-card p-5">
        <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">Health Score</p>
        <div className="flex justify-center my-3">
          <div className="w-[120px] h-[120px] rounded-full border-4 border-space-bg animate-pulse" />
        </div>
        <div className="space-y-2 mt-4">
          <div className="h-3 bg-space-bg rounded animate-pulse w-3/4 mx-auto" />
          <div className="h-8 bg-space-bg rounded animate-pulse" />
          <div className="h-8 bg-space-bg rounded animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-xl border border-space-border bg-space-card p-5 ${colors.bg}`}>
      <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">Health Score</p>

      {/* Score ring */}
      <div className="flex justify-center my-2">
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="50" fill="none" stroke="#1a2540" strokeWidth="10" />
          <circle
            cx="60" cy="60" r="50"
            fill="none"
            stroke={colors.ring}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${Math.PI * 100}`}
            strokeDashoffset={`${Math.PI * 100 * (1 - score / 100)}`}
            transform="rotate(-90 60 60)"
            style={{ transition: "stroke-dashoffset 0.8s ease, stroke 0.4s ease" }}
          />
          <text x="60" y="58" textAnchor="middle" fontSize="28" fontWeight="bold" fill={colors.ring}>
            {score}
          </text>
          <text x="60" y="72" textAnchor="middle" fontSize="10" fill="#475569">
            / 100
          </text>
        </svg>
      </div>

      {/* Status badge */}
      <div className={`text-center mb-1`}>
        <span className={`inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full border text-xs font-bold uppercase tracking-widest ${colors.badge}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${status !== "nominal" ? "animate-pulse" : ""} ${status === "nominal" ? "bg-green-400" : status === "degraded" ? "bg-yellow-400" : "bg-red-400"}`} />
          {status}
        </span>
      </div>

      {data.primary_driver && (
        <p className="text-center text-xs text-slate-600 mt-1 mb-3">
          Driver:{" "}
          <span className="text-orange-400 font-medium">
            {data.primary_driver.replace(/_/g, " ")}
          </span>
        </p>
      )}

      {/* Failure Risk + Anomaly */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-space-bg rounded-lg p-2.5 text-center">
          <p className="text-xs text-slate-500 mb-1">Failure Risk</p>
          <p className={`font-bold text-xl font-mono ${tier?.cls ?? "text-slate-500"}`}>
            {failurePct != null ? `${failurePct}%` : "--"}
          </p>
          {tier && (
            <p className={`text-xs font-semibold mt-0.5 ${tier.cls}`}>{tier.label}</p>
          )}
        </div>
        <div className="bg-space-bg rounded-lg p-2.5 text-center">
          <p className="text-xs text-slate-500 mb-1">Anomaly</p>
          <p className={`font-bold text-xl ${isAnomaly ? "text-red-400" : "text-green-400"}`}>
            {isAnomaly == null ? "--" : isAnomaly ? "YES" : "NO"}
          </p>
          {isAnomaly != null && (
            <p className={`text-xs font-semibold mt-0.5 ${isAnomaly ? "text-red-400" : "text-green-400"}`}>
              {isAnomaly ? "DETECTED" : "CLEAR"}
            </p>
          )}
        </div>
      </div>

      {/* Risk drivers */}
      {drivers.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Risk Drivers</p>
          <div className="space-y-1.5">
            {drivers.map(({ name, pct }) => (
              <div key={name}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-slate-400 capitalize">{name}</span>
                  <span className="text-orange-400 font-mono font-semibold">+{pct}%</span>
                </div>
                <div className="h-1 bg-space-bg rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-500/60 rounded-full"
                    style={{
                      width: `${Math.min(100, pct)}%`,
                      transition: "width 0.8s ease",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
