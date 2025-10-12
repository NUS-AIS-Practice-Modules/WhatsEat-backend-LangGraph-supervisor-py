import { Client } from "@langchain/langgraph-sdk";

let cachedClient: Client | null = null;

function getBaseUrl(): string | undefined {
  if (process.env.REACT_APP_LANGGRAPH_API_URL) {
    return process.env.REACT_APP_LANGGRAPH_API_URL.trim() || undefined;
  }
  if (typeof window !== "undefined" && window.location) {
    return `${window.location.origin}/api`;
  }
  return undefined;
}

function getApiKey(): string | undefined {
  const raw = process.env.REACT_APP_LANGGRAPH_API_KEY;
  return raw && raw.trim().length > 0 ? raw.trim() : undefined;
}

export function getLanggraphClient(): Client {
  if (!cachedClient) {
    cachedClient = new Client({
      apiUrl: getBaseUrl(),
      apiKey: getApiKey(),
    });
  }
  return cachedClient;
}

export function resolveGraphId(): string {
  const raw = process.env.REACT_APP_LANGGRAPH_GRAPH_ID;
  return raw && raw.trim().length > 0 ? raw.trim() : "agent";
}
