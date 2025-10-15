import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Client, ThreadState } from "@langchain/langgraph-sdk";
import { getLanggraphClient, resolveGraphId } from "../lib/langgraph_client";
import type { SupervisorPayload } from "../types/whatseat";
import { normalizeSupervisorPayload } from "../lib/payload";
import type { LocationCoordinates } from "./use_location";

export type ChatStatus = "initializing" | "ready" | "streaming" | "unavailable";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  payload?: SupervisorPayload | null;
  node?: string | null;
}

export interface ChatController {
  messages: ChatMessage[];
  sendMessage: (content: string, location?: LocationCoordinates | null) => Promise<void>;
  reset: () => Promise<void>;
  status: ChatStatus;
  isStreaming: boolean;
  error: string | null;
}

type LangGraphMessage = {
  id?: string;
  role?: string;
  type?: string;
  content?: unknown;
  additional_kwargs?: Record<string, unknown>;
  response_metadata?: Record<string, unknown>;
};

type ThreadValues = ThreadState["values"];

type RunStreamUpdate = {
  event?: string;
  data?: Record<string, unknown>;
};

type AssistantRecord = {
  assistant_id?: string;
  assistantId?: string;
  graph_id?: string;
  graphId?: string;
};

const SUMMARIZER_NODE = "summarizer_agent";

function extractNodeName(update: RunStreamUpdate | null | undefined): string | null {
  const data = update?.data;
  if (!data || typeof data !== "object") {
    return null;
  }
  const nodeCandidate = (data as { node?: unknown }).node;
  if (typeof nodeCandidate === "string" && nodeCandidate.length > 0) {
    return nodeCandidate;
  }
  const langgraphNode = (data as { langgraph_node?: unknown }).langgraph_node;
  if (typeof langgraphNode === "string" && langgraphNode.length > 0) {
    return langgraphNode;
  }
  const metadata = (data as { metadata?: unknown }).metadata;
  if (metadata && typeof metadata === "object") {
    const nested = (metadata as { node?: unknown }).node;
    if (typeof nested === "string" && nested.length > 0) {
      return nested;
    }
  }
  return null;
}

function extractThreadValues(update: RunStreamUpdate | null | undefined): ThreadValues | null {
  const data = update?.data;
  if (!data || typeof data !== "object") {
    return null;
  }

  const updateValues = (data as { update?: unknown }).update;
  if (updateValues) {
    if (Array.isArray(updateValues)) {
      return updateValues as ThreadValues;
    }
    if (typeof updateValues === "object" && "values" in (updateValues as Record<string, unknown>)) {
      return (updateValues as { values?: ThreadValues }).values ?? null;
    }
  }

  const directValue = (data as { value?: unknown }).value;
  if (directValue) {
    return directValue as ThreadValues;
  }

  const pluralValues = (data as { values?: unknown }).values;
  if (pluralValues) {
    return pluralValues as ThreadValues;
  }

  const state = (data as { state?: unknown }).state;
  if (state && typeof state === "object" && "values" in (state as Record<string, unknown>)) {
    return (state as { values?: ThreadValues }).values ?? null;
  }

  const result = (data as { result?: unknown }).result;
  if (result && typeof result === "object" && "values" in (result as Record<string, unknown>)) {
    return (result as { values?: ThreadValues }).values ?? null;
  }

  return null;
}

function isFinalUpdate(update: RunStreamUpdate | null | undefined): boolean {
  const data = update?.data;
  if (!data || typeof data !== "object") {
    return false;
  }
  if ((data as { final?: unknown }).final === true) {
    return true;
  }
  if ((data as { is_final?: unknown }).is_final === true) {
    return true;
  }
  if ((data as { completed?: unknown }).completed === true) {
    return true;
  }
  return false;
}

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
    const normalized = normalizeSupervisorPayload(additional.structured_output);
    if (normalized) {
      return normalized;
    }
  }

  if (
    additional &&
    typeof additional === "object" &&
    "tool_invocation" in additional &&
    typeof (additional as Record<string, unknown>).tool_invocation === "object"
  ) {
    const invocation = (additional as { tool_invocation?: { output?: unknown } }).tool_invocation;
    if (invocation?.output && typeof invocation.output === "object") {
      const normalized = normalizeSupervisorPayload(invocation.output);
      if (normalized) {
        return normalized;
      }
    }
  }

  const metadata = message.response_metadata;
  if (metadata && typeof metadata === "object" && "structured" in metadata) {
    const normalized = normalizeSupervisorPayload(metadata.structured);
    if (normalized) {
      return normalized;
    }
  }

  const text = extractText(message);
  try {
    const parsed = normalizeSupervisorPayload(JSON.parse(text));
    if (parsed) {
      return parsed;
    }
  } catch (error) {
    // ignore JSON parse failures; message contains plain text
  }
  return null;
}

function resolveRole(message: LangGraphMessage): ChatMessage["role"] | null {
  const rawRole = message.role ?? message.type ?? "";
  const normalized = rawRole.toLowerCase();
  if (normalized === "assistant" || normalized === "user") {
    return normalized;
  }
  if (normalized === "ai") {
    return "assistant";
  }
  if (normalized === "human") {
    return "user";
  }
  return null;
}

function resolveMessageNodeName(message: LangGraphMessage): string | null {
  const additional = message.additional_kwargs;
  if (additional && typeof additional === "object") {
    const direct = (additional as { node?: unknown }).node;
    if (typeof direct === "string" && direct.length > 0) {
      return direct;
    }

    const langgraphNode = (additional as { langgraph_node?: unknown }).langgraph_node;
    if (typeof langgraphNode === "string" && langgraphNode.length > 0) {
      return langgraphNode;
    }

    const sender = (additional as { sender?: unknown }).sender;
    if (typeof sender === "string" && sender.length > 0) {
      return sender;
    }

    const metadata = (additional as { metadata?: unknown }).metadata;
    if (metadata && typeof metadata === "object") {
      const metaNode = (metadata as { node?: unknown }).node;
      if (typeof metaNode === "string" && metaNode.length > 0) {
        return metaNode;
      }

      const metaLanggraphNode = (metadata as { langgraph_node?: unknown }).langgraph_node;
      if (typeof metaLanggraphNode === "string" && metaLanggraphNode.length > 0) {
        return metaLanggraphNode;
      }

      const agentName = (metadata as { agent?: unknown }).agent;
      if (typeof agentName === "string" && agentName.length > 0) {
        return agentName;
      }
    }
  }

  const responseMetadata = message.response_metadata;
  if (responseMetadata && typeof responseMetadata === "object") {
    const direct = (responseMetadata as { node?: unknown }).node;
    if (typeof direct === "string" && direct.length > 0) {
      return direct;
    }

    const langgraphNode = (responseMetadata as { langgraph_node?: unknown }).langgraph_node;
    if (typeof langgraphNode === "string" && langgraphNode.length > 0) {
      return langgraphNode;
    }

    const metadata = (responseMetadata as { metadata?: unknown }).metadata;
    if (metadata && typeof metadata === "object") {
      const metaNode = (metadata as { node?: unknown }).node;
      if (typeof metaNode === "string" && metaNode.length > 0) {
        return metaNode;
      }

      const metaLanggraphNode = (metadata as { langgraph_node?: unknown }).langgraph_node;
      if (typeof metaLanggraphNode === "string" && metaLanggraphNode.length > 0) {
        return metaLanggraphNode;
      }

      const agentName = (metadata as { agent?: unknown }).agent;
      if (typeof agentName === "string" && agentName.length > 0) {
        return agentName;
      }
    }
  }

  return null;
}

function normalizeMessages(items: LangGraphMessage[]): ChatMessage[] {
  const normalized: ChatMessage[] = [];
  for (const message of items) {
    const role = resolveRole(message);
    if (!role) {
      continue;
    }
    const nodeName = resolveMessageNodeName(message);
    const content = extractText(message);
    const payload = extractPayload(message);

    if (role === "assistant") {
      if (nodeName && nodeName !== SUMMARIZER_NODE) {
        continue;
      }
      if (!nodeName && !payload) {
        // Assistant messages without a node attribution or structured payload are
        // intermediate agent emissions that should not surface in the UI.
        continue;
      }
    }
    normalized.push({
      id: message.id ?? crypto.randomUUID(),
      role,
      content,
      payload,
      node: nodeName ?? null,
    });
  }
  return normalized;
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
  const streamingAssistantIdRef = useRef<string | null>(null);

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
    async (content, location) => {
      if (!threadIdRef.current) {
        throw new Error("Thread not initialized yet");
      }
      if (!assistantIdRef.current) {
        assistantIdRef.current = await ensureAssistant();
      }
      const threadId = threadIdRef.current;
      const assistantId = assistantIdRef.current;

      // 如果提供了位置信息，将其附加到消息内容中
      let enrichedContent = content;
      if (location) {
        enrichedContent = `${content}\n\n[用户位置信息: 纬度 ${location.latitude}, 经度 ${location.longitude}]`;
      }

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
        // 构建发送给 supervisor 的消息，包含位置信息
        const messagePayload: Record<string, unknown> = {
          messages: [
            {
              role: "user",
              content: enrichedContent,
            },
          ],
        };

        // 如果有位置信息，将其作为独立字段传递
        if (location) {
          messagePayload.user_location = {
            latitude: location.latitude,
            longitude: location.longitude,
            accuracy: location.accuracy,
          };
        }

        const stream = await client.runs.stream(threadId, assistantId, {
          input: messagePayload,
          stream_mode: "updates",
        });

        let sawSummarizer = false;

        for await (const update of stream as AsyncIterable<RunStreamUpdate>) {
          const nodeName = extractNodeName(update);
          const finalUpdate = isFinalUpdate(update);

          if (!finalUpdate && nodeName !== SUMMARIZER_NODE) {
            continue;
          }

          const values = extractThreadValues(update);
          if (!values) {
            continue;
          }

          const items = extractMessages(values);
          if (!items.length) {
            continue;
          }

          const normalized = normalizeMessages(items).filter((message) => {
            if (message.role !== "assistant") {
              return false;
            }
            if (message.node && message.node !== SUMMARIZER_NODE) {
              return false;
            }
            if (!message.node && !message.payload) {
              return false;
            }
            return true;
          });
          if (!normalized.length) {
            continue;
          }

          const latest = normalized[normalized.length - 1];
          if (nodeName === SUMMARIZER_NODE) {
            sawSummarizer = true;
          }

          setMessages((prev) => {
            const assistantId = streamingAssistantIdRef.current;
            if (!assistantId) {
              const newId = crypto.randomUUID();
              streamingAssistantIdRef.current = newId;
              return [...prev, { ...latest, id: newId }];
            }
            return prev.map((message) =>
              message.id === assistantId ? { ...message, content: latest.content, payload: latest.payload } : message
            );
          });
        }

        if (!sawSummarizer) {
          await refreshMessages(threadId);
        }

        setStatus("ready");
      } catch (cause) {
        console.error("Failed to complete run", cause);
        setError(cause instanceof Error ? cause.message : "An unexpected error occurred");
        setStatus("unavailable");
      } finally {
        setIsStreaming(false);
        streamingAssistantIdRef.current = null;
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
