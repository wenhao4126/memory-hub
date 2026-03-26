import { z } from "zod";
import { MemoryHubClient } from "./client.js";
import {
  agentCreateInput,
  chatEnhancedInput,
  knowledgeSearchInput,
  memoryCreateInput,
  memorySearchInput,
  taskCompleteInput,
  taskCreateInput,
  uuidSchema,
} from "./schemas.js";

export type ToolHandler = (input: unknown) => Promise<any>;

function flattenAgent(data: any) {
  return {
    id: data?.id,
    name: data?.name,
    description: data?.description,
    capabilities: data?.capabilities ?? [],
    metadata: data?.metadata ?? {},
    created_at: data?.created_at,
    updated_at: data?.updated_at,
  };
}

function extractIdFromMessage(message: string | undefined): string | null {
  const idMatch = /ID:\s*([0-9a-fA-F-]{36})/.exec(message || "");
  return idMatch?.[1] ?? null;
}

export function buildHandlers(client: MemoryHubClient): Record<string, ToolHandler> {
  return {
    agent_create: async (input) => {
      const payload = agentCreateInput.parse(input || {});
      const res = await client.request<{ message: string }>("/agents", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return {
        agent_id: extractIdFromMessage(res?.message),
        message: res?.message,
      };
    },

    agent_get: async (input) => {
      const { agent_id } = z.object({ agent_id: uuidSchema }).parse(input || {});
      const res = await client.request<any>(`/agents/${agent_id}`);
      return flattenAgent(res);
    },

    memory_create: async (input) => {
      const payload = memoryCreateInput.parse(input || {});
      const res = await client.request<any>("/memories", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return {
        memory_id: extractIdFromMessage(res?.message),
        message: res?.message,
      };
    },

    memory_search_private: async (input) => {
      const payload = memorySearchInput.parse(input || {});
      const q = new URLSearchParams({
        agent_id: payload.agent_id,
        query: payload.query,
        limit: String(payload.limit),
      });
      const res = await client.request<any[]>(`/memories/search/private?${q.toString()}`, {
        method: "POST",
      });
      return {
        count: Array.isArray(res) ? res.length : 0,
        items: Array.isArray(res)
          ? res.map((x) => ({
              id: x.id,
              content: x.content,
              memory_type: x.memory_type,
              similarity: x.similarity,
              importance: x.importance,
              visibility: "private",
            }))
          : [],
      };
    },

    memory_search_shared: async (input) => {
      const payload = memorySearchInput.parse(input || {});
      const q = new URLSearchParams({
        agent_id: payload.agent_id,
        query: payload.query,
        limit: String(payload.limit),
      });
      const res = await client.request<any[]>(`/memories/search/shared?${q.toString()}`, {
        method: "POST",
      });
      return {
        count: Array.isArray(res) ? res.length : 0,
        items: Array.isArray(res)
          ? res.map((x) => ({
              id: x.id,
              content: x.content,
              memory_type: x.memory_type,
              similarity: x.similarity,
              importance: x.importance,
              visibility: "shared",
            }))
          : [],
      };
    },

    chat_enhanced: async (input) => {
      const payload = chatEnhancedInput.parse(input || {});
      const res = await client.request<any>("/chat", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return {
        reply: res?.reply,
        conversation_id: res?.conversation_id,
        memories_used: res?.memories_used ?? 0,
        history_used: res?.history_used ?? 0,
        extracted_count: Array.isArray(res?.extracted_memories) ? res.extracted_memories.length : 0,
        stored_count: res?.stored_count ?? 0,
      };
    },

    knowledge_search: async (input) => {
      const payload = knowledgeSearchInput.parse(input || {});
      const q = new URLSearchParams({
        query: payload.query,
        limit: String(payload.limit),
        threshold: String(payload.threshold),
      });
      if (payload.category) q.set("category", payload.category);
      if (payload.source) q.set("source", payload.source);

      const res = await client.request<any[]>(`/knowledge/search?${q.toString()}`);
      return {
        count: Array.isArray(res) ? res.length : 0,
        items: Array.isArray(res)
          ? res.map((x) => ({
              id: x.id,
              title: x.title,
              content: x.content,
              category: x.category,
              source: x.source,
              similarity: x.similarity,
            }))
          : [],
      };
    },

    task_create: async (input) => {
      const payload = taskCreateInput.parse(input || {});
      const res = await client.request<{ message: string }>("/tasks", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return {
        task_id: extractIdFromMessage(res?.message),
        message: res?.message,
      };
    },

    task_complete: async (input) => {
      const payload = taskCompleteInput.parse(input || {});
      const body = payload.result ?? {};
      await client.request(`/tasks/${payload.task_id}/complete`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      return { task_id: payload.task_id, status: "completed", updated_via: "tasks/{id}/complete" };
    },
  };
}
