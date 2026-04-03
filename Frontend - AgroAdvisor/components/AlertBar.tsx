"use client";

import { useWS } from "@/app/context/WebSocketContext";
import { X } from "lucide-react";

export default function AlertBar() {
  const { alerts, dismissAlert } = useWS();

  if (alerts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none">
      {alerts.map((alert) => {
        let bg = "bg-[#1f2937] border-white/20 text-white";
        let icon = "ℹ️";

        if (alert.level === "warning") {
          bg = "bg-amber-500/10 border-amber-500/20 text-amber-500";
          icon = "⚠️";
        } else if (alert.level === "error") {
          bg = "bg-red-500/10 border-red-500/20 text-red-500";
          icon = "🛑";
        } else if (alert.level === "success") {
          bg = "bg-emerald-500/10 border-emerald-500/20 text-emerald-500";
          icon = "✅";
        }

        return (
          <div
            key={alert.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-lg border p-4 shadow-lg backdrop-blur-md animate-in slide-in-from-bottom-5 fade-in duration-300 ${bg}`}
          >
            <span className="text-lg leading-none">{icon}</span>
            <div className="flex-1 text-sm font-medium leading-relaxed">
              {alert.pesan}
            </div>
            <button
              onClick={() => dismissAlert(alert.id)}
              className="text-white/40 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
