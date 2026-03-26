import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { loadConfig } from "./config.js";
import { ApiError, MemoryHubClient } from "./client.js";
import { buildHandlers } from "./tools.js";

const TOOL_DESCRIPTIONS: Record<string, string> = {
  agent_create: "创建智能体",
  agent_get: "获取智能体信息",
  memory_create: "创建记忆",
  memory_search_private: "搜索私有记忆",
  memory_search_shared: "搜索共享记忆",
  chat_enhanced: "增强对话",
  knowledge_search: "搜索知识库",
  task_create: "创建任务",
  task_complete: "完成任务",
};

function toMcpText(data: unknown): string {
  return JSON.stringify(data, null, 2);
}

async function main() {
  const config = loadConfig();
  const client = new MemoryHubClient(config);
  const handlers = buildHandlers(client);

  const server = new McpServer({
    name: "memory-hub-mcp",
    version: "0.1.0",
  });

  for (const [name, handler] of Object.entries(handlers)) {
    server.registerTool(
      name,
      {
        description: TOOL_DESCRIPTIONS[name] || name,
        inputSchema: {
          payload: z.record(z.any()).default({}),
        },
      },
      async ({ payload }: { payload?: unknown }) => {
        try {
          const result = await handler(payload ?? {});
          return {
            content: [{ type: "text", text: toMcpText({ success: true, data: result }) }],
          };
        } catch (err: any) {
          const e = err instanceof ApiError
            ? err
            : new ApiError(err?.message || "工具调用失败", "TOOL_ERROR", undefined, err);

          return {
            content: [
              {
                type: "text",
                text: toMcpText({
                  success: false,
                  error: {
                    code: e.code,
                    message: e.message,
                    status: e.status,
                  },
                }),
              },
            ],
            isError: true,
          };
        }
      },
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("memory-hub-mcp 启动失败:", error);
  process.exit(1);
});
