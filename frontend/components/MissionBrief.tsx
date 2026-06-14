"use client";

import type { MissionBriefData } from "@/lib/api";

const STATUS_STYLE = {
  NOMINAL:  {
    border: "border-green-500/40",
    bg: "bg-green-900/20",
    text: "text-green-300",
    dot: "bg-green-400",
    pulse: false,
  },
  DEGRADED: {
    border: "border-yellow-500/50",
    bg: "bg-yellow-900/20",
    text: "text-yellow-300",
    dot: "bg-yellow-400",
    pulse: true,
  },
  CRITICAL: {
    border: "border-red-500/60",
    bg: "bg-red-900/25",
    text: "text-red-300",
    dot: "bg-red-400",
    pulse: true,
  },
} as const;

const RISK_COLOR = {
  LOW:      "text-green-400",
  MODERATE: "text-yellow-400",
  HIGH:     "text-orange-400",
  CRITICAL: "text-red-400",
} as const;

function Skeleton() {
  return (
    <div className="rounded-xl border border-space-border bg-space-card p-5 h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="h-3 bg-space-bg rounded w-28 animate-pulse" />
        <div className="h-3 bg-space-bg rounded w-20 animate-pulse" />
      </div>
      <div className="h-8 bg-space-bg rounded w-2/5 mb-4 animate-pulse" />
      <div className="space-y-2">
        <div className="h-3 bg-space-bg rounded w-full animate-pulse" />
        <div className="h-3 bg-space-bg rounded w-4/5 animate-pulse" />
      </div>
      <div className="mt-4 space-y-1.5">
        <div className="h-2.5 bg-space-bg rounded w-2/3 animate-pulse" />
        <div className="h-2.5 bg-space-bg rounded w-1/2 animate-pulse" />
      </div>
      <div className="mt-4 rounded-lg bg-space-bg p-3 space-y-2">
        <div className="h-3 bg-slate-800 rounded w-32 animate-pulse" />
        <div className="h-3 bg-slate-800 rounded w-full animate-pulse" />
        <div className="h-3 bg-slate-800 rounded w-3/4 animate-pulse" />
      </div>
    </div>
  );
}

interface Props {
  data: MissionBriefData | null;
}

export default function MissionBrief({ data }: Props) {
  if (!data) return <Skeleton />;

  const s = STATUS_STYLE[data.mission_status] ?? STATUS_STYLE.NOMINAL;
  const riskColor = RISK_COLOR[data.risk_level] ?? "text-slate-400";

  return (
    <div className="rounded-xl border border-space-border bg-space-card p-5 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs uppercase tracking-widest text-slate-500">AI Mission Brief</p>
        <span className="text-xs text-slate-600">
          Confidence{" "}
          <span className="text-blue-400 font-semibold font-mono">{data.confidence}%</span>
        </span>
      </div>

      {/* Mission status badge */}
      <div className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border mb-4 ${s.border} ${s.bg}`}>
        <span className={`flex-shrink-0 w-2 h-2 rounded-full ${s.dot} ${s.pulse ? "animate-pulse" : ""}`} />
        <span className={`text-xs font-bold tracking-widest uppercase ${s.text}`}>
          Mission Status: {data.mission_status}
        </span>
        <span className={`ml-auto text-xs font-bold tracking-wider ${riskColor}`}>
          {data.risk_level} RISK
        </span>
      </div>

      {/* Summary */}
      <div className="mb-4">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1.5">Summary</p>
        <p className="text-sm text-slate-300 leading-relaxed">{data.summary}</p>
      </div>

      {/* Key Issues */}
      {data.key_issues.length > 0 && (
        <div className="mb-4 flex-1">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Key Issues</p>
          <ul className="space-y-1.5">
            {data.key_issues.map((issue, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                <span className="text-orange-400 mt-px flex-shrink-0">▸</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended action */}
      <div className="mt-auto bg-space-bg rounded-lg p-3 border border-space-border/60">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1.5">Recommended Action</p>
        <p className="text-sm text-blue-300 leading-relaxed">{data.recommended_action}</p>
      </div>
    </div>
  );
}
