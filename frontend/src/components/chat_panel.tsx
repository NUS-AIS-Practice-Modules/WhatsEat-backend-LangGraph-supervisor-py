import { FormEvent, useCallback, useState } from "react";
import { ChatTranscript } from "./chat_transcript";
import { RuntimeStatus } from "./runtime_status";
import type { ChatController } from "../hooks/use_langgraph_chat";

export function ChatPanel({
  messages,
  sendMessage,
  reset,
  status,
  isStreaming,
  error,
}: ChatController) {
  const [input, setInput] = useState("");

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!input.trim()) {
        return;
      }
      await sendMessage(input.trim());
      setInput("");
    },
    [input, sendMessage]
  );

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  return (
    <section className="flex h-full flex-col gap-4 rounded-lg border border-slate-800 bg-slate-900/60 shadow-xl">
      <div className="flex flex-col gap-3 px-6 pt-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-brand">Culinary discovery assistant</h1>
          <RuntimeStatus status={status} onReset={handleReset} />
        </div>
        <p className="text-sm text-slate-400">
          Ask for nearby restaurants, request personalized picks, or explore summaries from the multi-agent workflow.
        </p>
      </div>
      <div className="flex-1 overflow-hidden px-2">
        <ChatTranscript messages={messages} isStreaming={isStreaming} />
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 border-t border-slate-800 bg-slate-900/80 px-6 py-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Find spicy ramen near me..."
            aria-label="Message the WhatsEat supervisor"
            disabled={status === "unavailable" || isStreaming}
            className="flex-1"
          />
          <button type="submit" disabled={status !== "ready" || isStreaming || !input.trim()}>
            Send
          </button>
        </div>
        {error ? <span className="text-sm text-red-400">{error}</span> : null}
      </form>
    </section>
  );
}
