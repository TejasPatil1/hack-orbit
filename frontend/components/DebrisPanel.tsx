"use client";

import type { DebrisData, DebrisObject } from "@/lib/api";

const RISK_COLOR: Record<string, string> = {
  low:      "text-green-400  border-green-500/40  bg-green-900/20",
  medium:   "text-yellow-400 border-yellow-500/40 bg-yellow-900/20",
  high:     "text-red-400    border-red-500/40    bg-red-900/20",
  critical: "text-red-300    border-red-400/60    bg-red-900/30",
};

function DebrisRow({ obj }: { obj: DebrisObject }) {
  const cls = RISK_COLOR[obj.risk_level] ?? RISK_COLOR.low;
  return (
    <div className={`rounded-lg border px-4 py-3 ${cls}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-semibold">{obj.name}</p>
          <p className="text-xs text-slate-500 font-mono mt-0.5">{obj.object_id}</p>
        </div>
        <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded border ${cls}`}>
          {obj.risk_level}
        </span>
      </div>

      <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-400">
        <div>
          <p className="text-slate-600">Miss Dist</p>
          <p className="font-mono font-semibold">{obj.miss_distance_km.toFixed(1)} km</p>
        </div>
        <div>
          <p className="text-slate-600">Velocity</p>
          <p className="font-mono font-semibold">{obj.relative_velocity_km_s.toFixed(1)} km/s</p>
        </div>
        <div>
          <p className="text-slate-600">Time TCA</p>
          <p className="font-mono font-semibold">{obj.time_to_conjunction_hours.toFixed(1)}h</p>
        </div>
      </div>

      {obj.maneuver_advised && (
        <p className="mt-2 text-xs font-semibold text-orange-400">⚡ Maneuver Advised</p>
      )}
    </div>
  );
}

interface Props { data: DebrisData | null }

export default function DebrisPanel({ data }: Props) {
  return (
    <div className="rounded-xl border border-space-border bg-space-card p-5">
      <div className="flex justify-between items-center mb-3">
        <p className="text-xs uppercase tracking-widest text-slate-500">Debris Conjunction</p>
        {data && (
          <span className="text-xs text-slate-600">{data.total_tracked} tracked</span>
        )}
      </div>

      {data ? (
        data.objects.length > 0 ? (
          <div className="space-y-2">
            {data.objects.map((obj) => <DebrisRow key={obj.object_id} obj={obj} />)}
          </div>
        ) : (
          <p className="text-sm text-slate-500 text-center py-4">No conjunction events</p>
        )
      ) : (
        <div className="h-24 flex items-center justify-center text-slate-600 text-sm">Loading…</div>
      )}
    </div>
  );
}
