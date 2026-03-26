import { z } from "zod";

export const uuidSchema = z.string().uuid();

export const agentCreateInput = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  capabilities: z.array(z.string()).default([]),
  metadata: z.record(z.any()).default({}),
});

export const memoryCreateInput = z.object({
  agent_id: uuidSchema,
  content: z.string().min(1),
  memory_type: z.enum(["fact", "preference", "skill", "experience"]).default("fact"),
  importance: z.number().min(0).max(1).default(0.5),
  tags: z.array(z.string()).default([]),
  metadata: z.record(z.any()).default({}),
  auto_route: z.boolean().default(true),
  visibility: z.enum(["private", "shared"]).optional(),
});

export const memorySearchInput = z.object({
  agent_id: uuidSchema,
  query: z.string().min(1),
  limit: z.number().int().min(1).max(50).default(10),
});

export const chatEnhancedInput = z.object({
  agent_id: uuidSchema,
  session_id: z.string().min(1).max(255),
  user_message: z.string().min(1),
  use_memory: z.boolean().default(true),
  use_history: z.boolean().default(true),
  auto_extract: z.boolean().default(true),
  memory_count: z.number().int().min(1).max(20).default(5),
  history_count: z.number().int().min(1).max(20).default(6),
});

export const knowledgeSearchInput = z.object({
  query: z.string().min(1),
  category: z.string().optional(),
  source: z.string().optional(),
  limit: z.number().int().min(1).max(50).default(10),
  threshold: z.number().min(0).max(1).default(0.3),
});

export const taskCreateInput = z.object({
  task_type: z.enum(["search", "write", "code", "review", "analyze", "design", "layout", "custom"]),
  title: z.string().min(1).max(500),
  description: z.string().optional(),
  priority: z.enum(["low", "normal", "high", "urgent"]).default("normal"),
  params: z.record(z.any()).default({}),
  agent_id: uuidSchema.optional(),
  parent_task_id: uuidSchema.optional(),
  timeout_minutes: z.number().int().min(1).max(1440).default(30),
  max_retries: z.number().int().min(0).max(10).default(3),
});

export const taskCompleteInput = z.object({
  task_id: uuidSchema,
  result: z.record(z.any()).optional(),
});
