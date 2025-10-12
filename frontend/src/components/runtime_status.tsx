import { useMemo } from "react";
import type { ChatStatus } from "../hooks/use_langgraph_chat";

interface RuntimeStatusProps {
  status: ChatStatus;
  onReset: () => void;
}

const STATUS_LABEL: Record<ChatStatus, string> = {
  initializing: "Connecting",
  ready: "Ready",
  streaming: "Streaming",
  unavailable: "Unavailable",
};

export function RuntimeStatus({ status, onReset }: RuntimeStatusProps) {
  const color = useMemo(() => {
    switch (status) {
      case "ready":
        return "bg-green-500";
      case "streaming":
        return "bg-brand";
      case "unavailable":
        return "bg-red-500";
      default:
        return "bg-yellow-400";
    }
  }, [status]);

  return (
    <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-slate-400">
      <span className={`inline-flex h-2 w-2 rounded-full ${color}`} aria-hidden />
      <span>{STATUS_LABEL[status]}</span>
      <button
        type="button"
        onClick={onReset}
        className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-300 hover:border-brand hover:text-brand"
      >
        Reset Thread
      </button>
    </div>
  );
}
