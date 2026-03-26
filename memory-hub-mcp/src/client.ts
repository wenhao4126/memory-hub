import { AppConfig } from "./config.js";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status?: number,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryableStatus(status: number): boolean {
  return status === 408 || status === 429 || status >= 500;
}

function normalizeErrorPayload(payload: any, status?: number): ApiError {
  if (payload?.error?.message) {
    return new ApiError(payload.error.message, payload.error.code || "API_ERROR", status, payload.error);
  }
  if (typeof payload?.detail === "string") {
    return new ApiError(payload.detail, "API_ERROR", status, payload.detail);
  }
  if (payload?.detail?.error?.message) {
    return new ApiError(payload.detail.error.message, payload.detail.error.code || "API_ERROR", status, payload.detail.error);
  }
  return new ApiError("请求失败", "API_ERROR", status, payload);
}

export class MemoryHubClient {
  constructor(private readonly config: AppConfig) {}

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const url = `${this.config.MEMORY_HUB_API_URL}${path}`;

    let lastErr: unknown;
    for (let i = 1; i <= this.config.MCP_RETRY_MAX_ATTEMPTS; i++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.config.MCP_TIMEOUT_MS);
      try {
        const headers = new Headers(init.headers || {});
        headers.set("X-API-Key", this.config.MEMORY_HUB_API_KEY);
        if (!headers.has("Content-Type") && init.body) {
          headers.set("Content-Type", "application/json");
        }

        const resp = await fetch(url, {
          ...init,
          headers,
          signal: controller.signal,
        });

        let payload: any = null;
        const text = await resp.text();
        if (text) {
          try {
            payload = JSON.parse(text);
          } catch {
            payload = { raw: text };
          }
        }

        if (!resp.ok) {
          const err = normalizeErrorPayload(payload, resp.status);
          if (isRetryableStatus(resp.status) && i < this.config.MCP_RETRY_MAX_ATTEMPTS) {
            await sleep(this.config.MCP_RETRY_BASE_MS * 2 ** (i - 1));
            continue;
          }
          throw err;
        }

        return payload as T;
      } catch (err: any) {
        lastErr = err;
        const isAbort = err?.name === "AbortError";
        if ((isAbort || err instanceof TypeError) && i < this.config.MCP_RETRY_MAX_ATTEMPTS) {
          await sleep(this.config.MCP_RETRY_BASE_MS * 2 ** (i - 1));
          continue;
        }
        if (err instanceof ApiError) throw err;
        throw new ApiError(err?.message || "网络错误", "NETWORK_ERROR", undefined, err);
      } finally {
        clearTimeout(timer);
      }
    }

    throw new ApiError("请求失败（重试已耗尽）", "RETRY_EXHAUSTED", undefined, lastErr);
  }
}
