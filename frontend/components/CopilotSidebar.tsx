"use client";

import { useEffect } from "react";
import CopilotChat from "@/components/CopilotChat";
import type { Telemetry } from "@/lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
  telemetry: Telemetry | null;
}

export default function CopilotSidebar({ open, onClose, telemetry }: Props) {
  useEffect(() => {
    const fn = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    if (open) window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, [open, onClose]);

  return (
    <div
      style={{
        position: "fixed",
        top: 0, right: 0, bottom: 0,
        width: 400,
        zIndex: 50,
        display: "flex",
        flexDirection: "column",
        background: "#0d1224",
        borderLeft: "1px solid #1a2540",
        boxShadow: open ? "-8px 0 32px rgba(0,0,0,0.6)" : "none",
        transform: open ? "translateX(0)" : "translateX(100%)",
        transition: "transform 0.25s cubic-bezier(0.4,0,0.2,1), box-shadow 0.25s ease",
      }}
    >
      {/* Header */}
      <div
        style={{ borderBottom: "1px solid #1a2540" }}
        className="flex items-center justify-between px-5 py-4 flex-shrink-0"
      >
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <div>
            <p className="text-xs font-bold text-slate-200 uppercase tracking-widest font-mono">
              AI Mission Copilot
            </p>
            <p className="text-xs text-slate-600 mt-px">ORBIT · SAT-001</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-xs text-slate-600 hover:text-slate-400 font-mono uppercase tracking-widest transition-colors px-2 py-1 rounded hover:bg-space-bg"
        >
          ✕
        </button>
      </div>

      {/* Chat fills remaining height */}
      <div className="flex-1 min-h-0 p-4">
        <CopilotChat telemetry={telemetry} sidebar />
      </div>
    </div>
  );
}
