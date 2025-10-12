import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Client } from "@langchain/langgraph-sdk";
import { getLanggraphClient, resolveGraphId } from "../lib/langgraph_client";
import type { SupervisorPayload } from "../types/whatseat";

export type ChatStatus = "initializing" | "ready" | "streaming" | "unavailable";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  payload?: SupervisorPayload | null;
}

export interface ChatController {
  messages: ChatMessage[];
  sendMessage: (content: string) => Promise<void>;
  reset: () => Promise<void>;
  status: ChatStatus;
  isStreaming: boolean;
  error: string | null;
}

type LangGraphMessage = {
  id?: string;
  role: string;
  content?: unknown;
  additional_kwargs?: Record<string, unknown>;
  response_metadata?: Record<string, unknown>;
};

type MessagesPage = {
  data: LangGraphMessage[];
};

function extractText(message: LangGraphMessage): string {
  const { content } = message;
  if (!content) {
    return "";
  }

  if (typeof content === "string") {
    return content;
  }

  if (Array.isArray(content)) {
    return content
      .map((block) => {
        if (typeof block === "string") {
          return block;
        }
        if (typeof block === "object" && block !== null) {
          if ("text" in block && typeof block.text === "string") {
            return block.text;
          }
          if ("output" in block && typeof (block as { output?: unknown }).output === "string") {
            return String((block as { output?: string }).output);
          }
        }
        return "";
      })
      .filter(Boolean)
      .join("\n\n");
  }

  if (typeof content === "object" && content !== null && "text" in content) {
    return String((content as { text?: unknown }).text ?? "");
  }

  return "";
}

function extractPayload(message: LangGraphMessage): SupervisorPayload | null {
  const additional = message.additional_kwargs;
  if (additional && typeof additional === "object" && "structured_output" in additional) {
    return additional.structured_output as SupervisorPayload;
  }

  if (
    additional &&
    typeof additional === "object" &&
    "tool_invocation" in additional &&
    typeof (additional as Record<string, unknown>).tool_invocation === "object"
  ) {
    const invocation = (additional as { tool_invocation?: { output?: unknown } }).tool_invocation;
    if (invocation?.output && typeof invocation.output === "object") {
      return invocation.output as SupervisorPayload;
    }
  }

  const metadata = message.response_metadata;
  if (metadata && typeof metadata === "object" && "structured" in metadata) {
    return metadata.structured as SupervisorPayload;
  }

  const text = extractText(message);
  try {
    const parsed = JSON.parse(text) as SupervisorPayload;
    if (parsed && typeof parsed === "object" && "cards" in parsed) {
      return parsed;
    }
  } catch (error) {
    // ignore JSON parse failures; message contains plain text
  }
  return null;
}

function normalizeMessages(page: MessagesPage): ChatMessage[] {
  return page.data
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({
      id: message.id ?? crypto.randomUUID(),
      role: message.role as ChatMessage["role"],
      content: extractText(message),
      payload: extractPayload(message),
    }))
    .sort((a, b) => (a.id > b.id ? 1 : -1));
}

export function useLanggraphChat(): ChatController {
  const client = useMemo<Client>(() => getLanggraphClient(), []);
  const graphId = useMemo(() => resolveGraphId(), []);
  const [status, setStatus] = useState<ChatStatus>("initializing");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const threadIdRef = useRef<string | null>(null);

  const initialize = useCallback(async () => {
    try {
      setStatus("initializing");
      setError(null);
      const thread = await client.threads.create();
      threadIdRef.current =
        (thread as { thread_id?: string }).thread_id ??
        (thread as { id?: string }).id ??
        (thread as { threadId?: string }).threadId ??
        null;
      if (!threadIdRef.current) {
        throw new Error("Unable to determine thread identifier");
      }
      setMessages([]);
      setStatus("ready");
    } catch (cause) {
      console.error("Failed to initialize chat", cause);
      setError(cause instanceof Error ? cause.message : "Unable to initialize chat");
      setStatus("unavailable");
    }
  }, [client]);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  const sendMessage = useCallback<ChatController["sendMessage"]>(
    async (content) => {
      if (!threadIdRef.current) {
        throw new Error("Thread not initialized yet");
      }
      const threadId = threadIdRef.current;

      const optimisticMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
      };

      setMessages((prev) => [...prev, optimisticMessage]);
      setIsStreaming(true);
      setStatus("streaming");
      setError(null);

      try {
        await client.threads.messages.create({
          threadId,
          messages: [
            {
              role: "user",
              content,
            },
          ],
        });

        const run = await client.runs.create({
          threadId,
          graphId,
          input: {
            messages: [
              {
                role: "user",
                content,
              },
            ],
          },
          stream: false,
        });

        await client.runs.wait({ threadId, runId: (run as { run_id?: string }).run_id ?? (run as { id?: string }).id });
        const page = (await client.threads.messages.list({ threadId })) as MessagesPage;
        setMessages(normalizeMessages(page));
        setStatus("ready");
      } catch (cause) {
        console.error("Failed to complete run", cause);
        setError(cause instanceof Error ? cause.message : "An unexpected error occurred");
        setStatus("unavailable");
      } finally {
        setIsStreaming(false);
      }
    },
    [client, graphId]
  );

  const reset = useCallback(async () => {
    threadIdRef.current = null;
    await initialize();
  }, [initialize]);

  return {
    messages,
    sendMessage,
    reset,
    status,
    isStreaming,
    error,
  };
}
