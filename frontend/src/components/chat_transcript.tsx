import * as ScrollArea from "@radix-ui/react-scroll-area";
import clsx from "clsx";
import type { ChatMessage } from "@hooks/use_langgraph_chat";
import { RecommendationGrid } from "@components/recommendation_grid";

interface ChatTranscriptProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export function ChatTranscript({ messages, isStreaming }: ChatTranscriptProps) {
  if (!messages.length) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-slate-800/60 p-6 text-center text-slate-500">
        <h2 className="text-lg font-medium text-slate-200">Start a new culinary search</h2>
        <p className="max-w-md text-sm">
          Describe your cravings, dietary preferences, or the ambience you are in the mood for. The supervisor will orchestrate the right specialists.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea.Root className="h-full overflow-hidden rounded-lg border border-slate-800/60 bg-slate-950/60">
      <ScrollArea.Viewport className="h-full w-full">
        <div className="flex flex-col gap-4 p-6">
          {messages.map((message) => (
            <article
              key={message.id}
              className={clsx("flex flex-col gap-3 rounded-md border px-4 py-3", {
                "border-brand/40 bg-brand-muted/10 text-brand": message.role === "assistant",
                "border-slate-800 bg-slate-900 text-slate-200": message.role !== "assistant",
              })}
            >
              <span className="text-xs uppercase tracking-widest text-slate-400">
                {message.role === "assistant" ? "Supervisor" : "You"}
              </span>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-100">
                {message.content}
              </p>
              {message.payload ? <RecommendationGrid payload={message.payload} /> : null}
            </article>
          ))}
          {isStreaming ? (
            <div className="flex animate-pulse gap-2 text-sm text-brand">
              <span className="h-2 w-2 rounded-full bg-brand" />
              <span className="h-2 w-2 rounded-full bg-brand" />
              <span className="h-2 w-2 rounded-full bg-brand" />
            </div>
          ) : null}
        </div>
      </ScrollArea.Viewport>
      <ScrollArea.Scrollbar orientation="vertical" className="flex w-2 rounded bg-slate-800/60">
        <ScrollArea.Thumb className="flex-1 rounded bg-slate-600" />
      </ScrollArea.Scrollbar>
    </ScrollArea.Root>
  );
}
