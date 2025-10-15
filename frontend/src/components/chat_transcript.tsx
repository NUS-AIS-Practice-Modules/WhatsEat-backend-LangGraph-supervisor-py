import * as ScrollArea from "@radix-ui/react-scroll-area";
import clsx from "clsx";
import type { ChatMessage } from "../hooks/use_langgraph_chat";
import type { LocationCoordinates } from "../hooks/use_location";
import { RecommendationGrid } from "./recommendation_grid";

interface ChatTranscriptProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  userLocation: LocationCoordinates | null;
  onRequestMore?: () => void | Promise<void>;
  disableRequestMore?: boolean;
}

export function ChatTranscript({ messages, isStreaming, userLocation, onRequestMore, disableRequestMore }: ChatTranscriptProps) {
  if (!messages.length) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-slate-300 p-6 text-center text-slate-500">
        <h2 className="text-lg font-medium text-slate-700">Start a new culinary search</h2>
        <p className="max-w-md text-sm">
          Describe your cravings, dietary preferences, or the ambience you are in the mood for. The supervisor will orchestrate the right specialists.
        </p>
      </div>
    );
  }

  const latestAssistantPayloadMessageId = [...messages]
    .reverse()
    .find((message) => message.role === "assistant" && message.payload)?.id;

  return (
    <ScrollArea.Root className="h-full overflow-hidden rounded-lg border border-slate-200 bg-white">
      <ScrollArea.Viewport className="h-full w-full">
        <div className="flex flex-col gap-4 p-6">
          {messages.map((message) => {
            if (message.role === "assistant" && message.node && message.node !== "summarizer_agent") {
              return null;
            }

            if (message.role === "assistant" && message.payload && message.id !== latestAssistantPayloadMessageId) {
              return null;
            }

            const showContent = message.role !== "assistant" || !message.payload;

            return (
              <article
                key={message.id}
                className={clsx("flex flex-col gap-3 rounded-md border px-4 py-3", {
                  "border-brand/40 bg-brand/10 text-slate-900": message.role === "assistant",
                  "border-slate-200 bg-white text-slate-800": message.role !== "assistant",
                })}
              >
                <span className="text-xs uppercase tracking-widest text-slate-500">
                  {message.role === "assistant" ? "Supervisor" : "You"}
                </span>
                {showContent ? (
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                    {message.content}
                  </p>
                ) : null}
                {message.payload && message.id === latestAssistantPayloadMessageId ? (
                  <RecommendationGrid
                    payload={message.payload}
                    userLocation={userLocation}
                    onRequestMore={onRequestMore}
                    disableRequestMore={disableRequestMore}
                  />
                ) : null}
              </article>
            );
          })}
          {isStreaming ? (
            <div className="flex animate-pulse gap-2 text-sm text-brand">
              <span className="h-2 w-2 rounded-full bg-brand" />
              <span className="h-2 w-2 rounded-full bg-brand" />
              <span className="h-2 w-2 rounded-full bg-brand" />
            </div>
          ) : null}
        </div>
      </ScrollArea.Viewport>
      <ScrollArea.Scrollbar orientation="vertical" className="flex w-2 rounded bg-slate-200/80">
        <ScrollArea.Thumb className="flex-1 rounded bg-slate-400" />
      </ScrollArea.Scrollbar>
    </ScrollArea.Root>
  );
}
