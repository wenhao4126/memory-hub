import { z } from "zod";

const configSchema = z.object({
  MEMORY_HUB_API_URL: z.string().url().default("http://localhost:8000/api/v1"),
  MEMORY_HUB_API_KEY: z.string().min(1, "MEMORY_HUB_API_KEY 未配置"),
  MCP_RETRY_MAX_ATTEMPTS: z.coerce.number().int().min(1).max(8).default(3),
  MCP_RETRY_BASE_MS: z.coerce.number().int().min(50).max(5000).default(300),
  MCP_TIMEOUT_MS: z.coerce.number().int().min(1000).max(120000).default(30000),
});

export type AppConfig = z.infer<typeof configSchema>;

export function loadConfig(): AppConfig {
  return configSchema.parse({
    MEMORY_HUB_API_URL: process.env.MEMORY_HUB_API_URL,
    MEMORY_HUB_API_KEY: process.env.MEMORY_HUB_API_KEY,
    MCP_RETRY_MAX_ATTEMPTS: process.env.MCP_RETRY_MAX_ATTEMPTS,
    MCP_RETRY_BASE_MS: process.env.MCP_RETRY_BASE_MS,
    MCP_TIMEOUT_MS: process.env.MCP_TIMEOUT_MS,
  });
}
