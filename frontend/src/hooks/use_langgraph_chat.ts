import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Client, ThreadState } from "@langchain/langgraph-sdk";
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

type ThreadValues = ThreadState["values"];

type AssistantRecord = {
  assistant_id?: string;
  assistantId?: string;
  graph_id?: string;
  graphId?: string;
};

function resolveAssistantId(candidate: AssistantRecord | null | undefined): string | null {
  if (!candidate) {
    return null;
  }
  return candidate.assistant_id ?? candidate.assistantId ?? null;
}

function extractMessages(values: ThreadValues | undefined): LangGraphMessage[] {
  if (!values) {
    return [];
  }
  if (Array.isArray(values)) {
    return values as LangGraphMessage[];
  }
  if (typeof values === "object") {
    const fromMessages = (values as { messages?: unknown }).messages;
    if (Array.isArray(fromMessages)) {
      return fromMessages as LangGraphMessage[];
    }
    if (fromMessages && typeof fromMessages === "object" && Array.isArray((fromMessages as { data?: unknown }).data)) {
      return (fromMessages as { data: unknown[] }).data as LangGraphMessage[];
    }
  }
  return [];
}

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

function normalizeMessages(items: LangGraphMessage[]): ChatMessage[] {
  return items
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({
      id: message.id ?? crypto.randomUUID(),
      role: message.role as ChatMessage["role"],
      content: extractText(message),
      payload: extractPayload(message),
    }));
}

export function useLanggraphChat(): ChatController {
  const client = useMemo<Client>(() => getLanggraphClient(), []);
  const graphId = useMemo(() => resolveGraphId(), []);
  const [status, setStatus] = useState<ChatStatus>("initializing");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const threadIdRef = useRef<string | null>(null);
  const assistantIdRef = useRef<string | null>(null);

  const ensureAssistant = useCallback(async (): Promise<string> => {
    if (assistantIdRef.current) {
      return assistantIdRef.current;
    }
    const candidates = await client.assistants.search({ graphId });
    const existing = candidates?.[0] ?? null;
    const assistant = existing ?? (await client.assistants.create({ graphId }));
    const assistantId = resolveAssistantId(assistant);
    if (!assistantId) {
      throw new Error("Unable to resolve assistant identifier");
    }
    assistantIdRef.current = assistantId;
    return assistantId;
  }, [client, graphId]);

  const refreshMessages = useCallback(
    async (threadId: string) => {
      const state = await client.threads.getState(threadId);
      const items = extractMessages(state?.values);
      setMessages(normalizeMessages(items));
    },
    [client]
  );

  const initialize = useCallback(async () => {
    try {
      setStatus("initializing");
      setError(null);
      const assistantId = await ensureAssistant();
      assistantIdRef.current = assistantId;
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
  }, [client, ensureAssistant]);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  const sendMessage = useCallback<ChatController["sendMessage"]>(
    async (content) => {
      if (!threadIdRef.current) {
        throw new Error("Thread not initialized yet");
      }
      if (!assistantIdRef.current) {
        assistantIdRef.current = await ensureAssistant();
      }
      const threadId = threadIdRef.current;
      const assistantId = assistantIdRef.current;

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
        await client.runs.wait(threadId, assistantId, {
          input: {
            messages: [
              {
                role: "user",
                content,
              },
            ],
          },
        });
        await refreshMessages(threadId);
        setStatus("ready");
      } catch (cause) {
        console.error("Failed to complete run", cause);
        setError(cause instanceof Error ? cause.message : "An unexpected error occurred");
        setStatus("unavailable");
      } finally {
        setIsStreaming(false);
      }
    },
    [client, ensureAssistant, refreshMessages]
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
