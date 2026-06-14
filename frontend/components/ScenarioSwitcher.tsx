"use client";

const SCENARIOS = [
  { id: "healthy",     label: "Healthy",      icon: "●", color: "green",  score: "92" },
  { id: "anomaly",     label: "Anomaly",      icon: "▲", color: "yellow", score: "62" },
  { id: "debris",      label: "Debris",       icon: "◆", color: "yellow", score: "62" },
  { id: "solar_storm", label: "Solar Storm",  icon: "☀", color: "red",    score: "54" },
  { id: "resolution",  label: "Resolution",   icon: "✓", color: "green",  score: "99" },
] as const;

const COLOR_MAP = {
  green:  {
    base:   "border-green-600/40 text-green-500",
    active: "border-green-500 bg-green-900/30 text-green-300 ring-1 ring-green-500/50",
    hover:  "hover:bg-green-900/20 hover:border-green-500/60",
  },
  yellow: {
    base:   "border-yellow-600/40 text-yellow-500",
    active: "border-yellow-500 bg-yellow-900/30 text-yellow-300 ring-1 ring-yellow-500/50",
    hover:  "hover:bg-yellow-900/20 hover:border-yellow-500/60",
  },
  red: {
    base:   "border-red-600/40 text-red-500",
    active: "border-red-500 bg-red-900/30 text-red-300 ring-1 ring-red-500/50",
    hover:  "hover:bg-red-900/20 hover:border-red-500/60",
  },
};

interface Props {
  active: string;
  onSelect: (scenario: string) => void;
  loading: boolean;
}

export default function ScenarioSwitcher({ active, onSelect, loading }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-xs text-slate-600 uppercase tracking-widest mr-1 hidden sm:block">
        Scenario
      </span>
      {SCENARIOS.map((s) => {
        const isActive = active === s.id;
        const c = COLOR_MAP[s.color];
        return (
          <button
            key={s.id}
            disabled={loading}
            onClick={() => onSelect(s.id)}
            className={`
              px-2.5 py-1 rounded-md border text-xs font-semibold
              transition-all duration-150 select-none
              ${isActive ? c.active : `${c.base} opacity-50 ${c.hover}`}
              disabled:cursor-not-allowed disabled:opacity-30
            `}
          >
            <span className="mr-1 opacity-70">{s.icon}</span>
            {s.label}
            <span className="ml-1.5 opacity-50 font-mono">{s.score}</span>
          </button>
        );
      })}
      {loading && (
        <span className="text-xs text-slate-600 animate-pulse ml-1">switching…</span>
      )}
    </div>
  );
}
