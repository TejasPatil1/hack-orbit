"use client";

const SCENARIOS = [
  { id: "healthy",     label: "Healthy",     color: "green",  score: "92" },
  { id: "anomaly",     label: "Anomaly",     color: "yellow", score: "62" },
  { id: "debris",      label: "Debris",      color: "yellow", score: "62" },
  { id: "solar_storm", label: "Solar Storm", color: "red",    score: "54" },
  { id: "resolution",  label: "Resolution",  color: "green",  score: "99" },
] as const;

const COLOR_MAP = {
  green:  "border-green-500/60 hover:bg-green-900/30 text-green-400",
  yellow: "border-yellow-500/60 hover:bg-yellow-900/30 text-yellow-400",
  red:    "border-red-500/60 hover:bg-red-900/30 text-red-400",
};

interface Props {
  active: string;
  onSelect: (scenario: string) => void;
  loading: boolean;
}

export default function ScenarioSwitcher({ active, onSelect, loading }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs text-slate-500 uppercase tracking-widest mr-1">Demo Scenario</span>
      {SCENARIOS.map((s) => (
        <button
          key={s.id}
          disabled={loading}
          onClick={() => onSelect(s.id)}
          className={`
            px-3 py-1.5 rounded-md border text-xs font-semibold transition-all
            ${COLOR_MAP[s.color]}
            ${active === s.id ? "opacity-100 ring-1 ring-current bg-current/10" : "opacity-50"}
            disabled:cursor-not-allowed
          `}
        >
          {s.label} <span className="opacity-60 ml-1">{s.score}</span>
        </button>
      ))}
    </div>
  );
}
