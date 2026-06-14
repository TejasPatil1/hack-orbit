"use client";

type StatusKey = "connected" | "active" | "online" | "degraded" | "offline";

const STATUS_MAP: Record<StatusKey, { dot: string; text: string; label: string }> = {
  connected: { dot: "bg-green-400",                       text: "text-green-400",  label: "Connected" },
  active:    { dot: "bg-blue-400 animate-pulse",          text: "text-blue-400",   label: "Active"    },
  online:    { dot: "bg-green-400",                       text: "text-green-400",  label: "Online"    },
  degraded:  { dot: "bg-yellow-400",                      text: "text-yellow-400", label: "Degraded"  },
  offline:   { dot: "bg-red-500",                         text: "text-red-400",    label: "Offline"   },
};

interface Props {
  backendOnline: boolean;
  lastSync: Date | null;
}

export default function SystemStatus({ backendOnline, lastSync }: Props) {
  const items: { label: string; status: StatusKey }[] = [
    { label: "NOAA Feed",        status: backendOnline ? "connected" : "offline"  },
    { label: "Orbit Feed",       status: backendOnline ? "connected" : "offline"  },
    { label: "Telemetry Stream", status: backendOnline ? "active"    : "offline"  },
    { label: "AI Copilot",       status: backendOnline ? "online"    : "degraded" },
  ];

  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-1 py-1.5 border-b border-space-border/50 mb-3">
      {items.map(({ label, status }) => {
        const s = STATUS_MAP[status];
        return (
          <div key={label} className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${s.dot}`} />
            <span className="text-xs text-slate-600">{label}:</span>
            <span className={`text-xs font-medium ${s.text}`}>{s.label}</span>
          </div>
        );
      })}
      {lastSync && (
        <span className="ml-auto text-xs text-slate-700 hidden sm:block">
          Last sync {lastSync.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}
