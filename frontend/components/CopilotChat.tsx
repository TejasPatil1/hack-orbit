"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  text: string;
  source?: "llm" | "fallback";
}

export default function CopilotChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "ORBIT online. I'm monitoring SAT-001. Ask me anything about satellite health, maneuvers, or current risks.",
      source: "fallback",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await api.copilot(text);
      setMessages((m) => [...m, { role: "assistant", text: res.reply, source: res.source }]);
    } catch {
      setMessages((m) => [...m, {
        role: "assistant",
        text: "Connection error. Check that the backend is running on port 8000.",
        source: "fallback",
      }]);
    } finally {
      setLoading(false);
    }
  }

  const QUICK = [
    "What should I do right now?",
    "Is it safe to execute the maneuver?",
    "Summarize current risks",
  ];

  return (
    <div className="rounded-xl border border-space-border bg-space-card p-5 flex flex-col" style={{ minHeight: "360px" }}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs uppercase tracking-widest text-slate-500">AI Copilot</p>
        <span className="text-xs text-green-400 flex items-center gap-1">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          ORBIT Online
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-3 pr-1" style={{ maxHeight: "280px" }}>
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`
              max-w-[85%] rounded-xl px-4 py-2.5 text-sm leading-relaxed
              ${msg.role === "user"
                ? "bg-blue-900/40 border border-blue-700/50 text-blue-100"
                : "bg-space-bg border border-space-border text-slate-300"}
            `}>
              {msg.role === "assistant" && (
                <span className="text-xs text-slate-600 block mb-1">
                  ORBIT {msg.source === "llm" ? "· AI" : "· local"}
                </span>
              )}
              <span className="whitespace-pre-wrap">{msg.text}</span>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-space-bg border border-space-border rounded-xl px-4 py-2.5">
              <span className="text-slate-600 text-sm animate-pulse">ORBIT is thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      <div className="flex flex-wrap gap-1.5 mb-2">
        {QUICK.map((q) => (
          <button
            key={q}
            disabled={loading}
            onClick={() => { setInput(q); }}
            className="text-xs px-2.5 py-1 rounded-md border border-space-muted text-slate-500 hover:text-slate-300 hover:border-slate-500 transition-colors disabled:opacity-40"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask ORBIT anything…"
          disabled={loading}
          className="flex-1 bg-space-bg border border-space-border rounded-lg px-4 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-600/60 transition-colors disabled:opacity-50"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded-lg bg-blue-800/60 border border-blue-700/50 text-blue-300 text-sm font-semibold hover:bg-blue-700/60 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
}
