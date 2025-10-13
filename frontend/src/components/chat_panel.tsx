import { FormEvent, useCallback, useState } from "react";
import { ChatTranscript } from "./chat_transcript";
import { RuntimeStatus } from "./runtime_status";
import type { ChatController } from "../hooks/use_langgraph_chat";
import type { LocationCoordinates } from "../hooks/use_location";

interface ChatPanelProps extends ChatController {
  userLocation: LocationCoordinates | null;
}

export function ChatPanel({
  messages,
  sendMessage,
  reset,
  status,
  isStreaming,
  error,
  userLocation,
}: ChatPanelProps) {
  const [input, setInput] = useState("");

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const message = input.trim();
      if (!message) {
        return;
      }
      setInput("");
      // 发送消息时携带用户位置信息
      await sendMessage(message, userLocation);
    },
    [input, sendMessage, userLocation]
  );

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  const handleRequestMore = useCallback(async () => {
    if (status !== "ready" || isStreaming) {
      return;
    }
    await sendMessage("Please recommend more restaurants.", userLocation);
  }, [isStreaming, sendMessage, status, userLocation]);

  return (
    <section className="flex h-full flex-col gap-4 rounded-lg border border-slate-200 bg-white shadow-lg">
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
        <ChatTranscript
          messages={messages}
          isStreaming={isStreaming}
          onRequestMore={handleRequestMore}
          disableRequestMore={status !== "ready" || isStreaming}
        />
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 border-t border-slate-200 bg-slate-50 px-6 py-4">
        {userLocation && (
          <div className="flex items-center gap-2 text-xs text-green-700 bg-green-50 border border-green-200 rounded px-3 py-2">
            <span>✅</span>
            <span>已获取位置，将自动使用您的当前位置搜索附近餐厅</span>
          </div>
        )}
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
        {error ? <span className="text-sm text-red-500">{error}</span> : null}
      </form>
    </section>
  );
}
