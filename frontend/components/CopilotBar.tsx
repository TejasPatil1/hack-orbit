"use client";

import { useState, useEffect } from "react";

const INSIGHTS = [
  "All systems nominal — Health Score 92 · Failure Risk 4% · No active anomalies detected",
  "Space weather benign — Kp Index 1.2 · Solar wind 385 km/s · No storm advisory",
  "3 debris objects tracked — All low risk · Closest approach in 48h at 8.4 km miss distance",
  "7-day forecast stable — Health trajectory 88–93 · No maneuver windows required",
  "AI Copilot standing by — Ask me anything about satellite health, risks, or maneuvers",
];

interface Props {
  onOpenCopilot: () => void;
}

export default function CopilotBar({ onOpenCopilot }: Props) {
  const [idx, setIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIdx((i) => (i + 1) % INSIGHTS.length);
        setVisible(true);
      }, 300);
    }, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="mb-3 flex items-center gap-3 px-4 py-2.5 rounded-lg border border-green-600/30 bg-green-950/15">
      {/* Live dot */}
      <span className="flex-shrink-0 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
        <span className="text-xs font-mono text-green-500 uppercase tracking-widest font-semibold">
          ORBIT
        </span>
      </span>

      <span className="text-slate-700 text-xs">|</span>

      {/* Rotating insight */}
      <span
        className="text-xs text-slate-400 flex-1 min-w-0 truncate transition-opacity duration-300"
        style={{ opacity: visible ? 1 : 0 }}
      >
        {INSIGHTS[idx]}
      </span>

      {/* Dot indicators */}
      <div className="flex items-center gap-1 flex-shrink-0">
        {INSIGHTS.map((_, i) => (
          <span
            key={i}
            className={`w-1 h-1 rounded-full transition-colors duration-300 ${
              i === idx ? "bg-green-400" : "bg-slate-700"
            }`}
          />
        ))}
      </div>

      {/* CTA */}
      <button
        onClick={onOpenCopilot}
        className="flex-shrink-0 text-xs text-blue-400 hover:text-blue-300 font-semibold transition-colors border-l border-slate-800 pl-3 ml-1"
      >
        Ask ORBIT →
      </button>
    </div>
  );
}
