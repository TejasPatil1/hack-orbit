"use client";

interface Props {
  alert: string | null;
  isAnomaly: boolean;
  primaryDriver: string | null;
}

export default function AlertBanner({ alert, isAnomaly, primaryDriver }: Props) {
  if (!alert && !isAnomaly) return null;

  const message = alert
    ?? (primaryDriver ? `ANOMALY DETECTED — ${primaryDriver.replace(/_/g, " ").toUpperCase()}` : "ANOMALY DETECTED");

  return (
    <div className="glow-red w-full rounded-lg border border-red-500/60 bg-red-950/40 px-4 py-3 flex items-center gap-3 animate-pulse">
      <span className="text-red-400 text-xl">⚠</span>
      <span className="text-red-300 font-semibold tracking-wide text-sm">{message}</span>
    </div>
  );
}
