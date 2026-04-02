"""memory-hub-mcp Python server

提供 5 个 MCP 工具：
1) agent_create
2) agent_get
3) memory_create
4) memory_search
5) chat

要求：
- 调用 memory-hub API
- 自动添加 X-API-Key
- 错误处理
- 返回简洁结果
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("memory-hub-mcp")


UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}")


@dataclass
class Settings:
    api_url: str
    api_key: str
    timeout_s: float = 30.0


class ApiError(Exception):
    def __init__(self, message: str, code: str = "API_ERROR", status: int | None = None, detail: Any = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.detail = detail


def _settings() -> Settings:
    api_url = os.getenv("MEMORY_HUB_API_URL", "http://localhost:8000/api/v1").rstrip("/")
    api_key = os.getenv("MEMORY_HUB_API_KEY", "").strip()
    if not api_key:
        raise ApiError("未配置 MEMORY_HUB_API_KEY", code="CONFIG_ERROR")
    timeout_s = float(os.getenv("MCP_TIMEOUT_SECONDS", "30"))
    return Settings(api_url=api_url, api_key=api_key, timeout_s=timeout_s)


def _parse_json_bytes(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _normalize_error_payload(payload: Any, status: int | None = None) -> ApiError:
    if isinstance(payload, dict):
        if isinstance(payload.get("error"), dict):
            err = payload["error"]
            return ApiError(
                message=err.get("message") or "请求失败",
                code=err.get("code") or "API_ERROR",
                status=status,
                detail=err,
            )
        if isinstance(payload.get("detail"), str):
            return ApiError(payload["detail"], code="API_ERROR", status=status, detail=payload)
        if isinstance(payload.get("message"), str) and status and status >= 400:
            return ApiError(payload["message"], code="API_ERROR", status=status, detail=payload)
    return ApiError("请求失败", code="API_ERROR", status=status, detail=payload)


def _request(method: str, path: str, payload: dict[str, Any] | None = None, query: dict[str, Any] | None = None) -> Any:
    cfg = _settings()

    url = f"{cfg.api_url}{path}"
    if query:
        url = f"{url}?{urlparse.urlencode(query)}"

    data = None
    headers = {"X-API-Key": cfg.api_key, "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urlrequest.Request(url=url, data=data, headers=headers, method=method.upper())

    try:
        with urlrequest.urlopen(req, timeout=cfg.timeout_s) as resp:
            body = _parse_json_bytes(resp.read())
            status = getattr(resp, "status", 200)
            if status >= 400:
                raise _normalize_error_payload(body, status)
            return body
    except urlerror.HTTPError as e:
        payload_obj = _parse_json_bytes(e.read()) if e.fp else {}
        raise _normalize_error_payload(payload_obj, e.code) from e
    except urlerror.URLError as e:
        raise ApiError(f"网络错误: {e.reason}", code="NETWORK_ERROR") from e


def _extract_uuid(value: str | None) -> str | None:
    if not value:
        return None
    m = UUID_RE.search(value)
    return m.group(0) if m else None


def _require_uuid(value: str, field: str) -> None:
    if not UUID_RE.fullmatch(value):
        raise ApiError(f"{field} 必须是合法 UUID", code="VALIDATION_ERROR")


def _tool_ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"success": True, **data}


def _tool_fail(err: Exception) -> dict[str, Any]:
    if isinstance(err, ApiError):
        return {
            "success": False,
            "error": {
                "code": err.code,
                "message": str(err),
                "status": err.status,
            },
        }
    return {"success": False, "error": {"code": "TOOL_ERROR", "message": str(err)}}


@mcp.tool(name="agent_create", description="创建智能体")
def agent_create(params: dict[str, Any]) -> dict[str, Any]:
    try:
        name = (params.get("name") or "").strip()
        description = params.get("description")
        capabilities = params.get("capabilities")
        metadata = params.get("metadata")

        if not name:
            raise ApiError("name 不能为空", code="VALIDATION_ERROR")
        if capabilities is not None and not isinstance(capabilities, list):
            raise ApiError("capabilities 必须是数组", code="VALIDATION_ERROR")
        if metadata is not None and not isinstance(metadata, dict):
            raise ApiError("metadata 必须是对象", code="VALIDATION_ERROR")

        res = _request(
            "POST",
            "/agents",
            {
                "name": name,
                "description": description,
                "capabilities": capabilities or [],
                "metadata": metadata or {},
            },
        )
        message = res.get("message") if isinstance(res, dict) else None
        return _tool_ok({"agent_id": _extract_uuid(message), "message": message or "创建成功"})
    except Exception as e:
        return _tool_fail(e)


@mcp.tool(name="agent_get", description="获取智能体")
def agent_get(agent_id: str) -> dict[str, Any]:
    try:
        _require_uuid(agent_id, "agent_id")
        res = _request("GET", f"/agents/{agent_id}")
        if not isinstance(res, dict):
            raise ApiError("接口返回格式异常", code="API_ERROR")

        return _tool_ok(
            {
                "agent": {
                    "id": res.get("id"),
                    "name": res.get("name"),
                    "description": res.get("description"),
                    "capabilities": res.get("capabilities") or [],
                    "metadata": res.get("metadata") or {},
                    "created_at": res.get("created_at"),
                    "updated_at": res.get("updated_at"),
                }
            }
        )
    except Exception as e:
        return _tool_fail(e)


@mcp.tool(name="memory_create", description="创建记忆")
def memory_create(params: dict[str, Any]) -> dict[str, Any]:
    try:
        agent_id = (params.get("agent_id") or "").strip()
        content = (params.get("content") or "").strip()
        memory_type = params.get("memory_type", "fact")
        importance = float(params.get("importance", 0.5))
        tags = params.get("tags")
        metadata = params.get("metadata")
        auto_route = params.get("auto_route", True)
        visibility = params.get("visibility")

        _require_uuid(agent_id, "agent_id")
        if not content:
            raise ApiError("content 不能为空", code="VALIDATION_ERROR")
        if not (0.0 <= importance <= 1.0):
            raise ApiError("importance 必须在 0~1", code="VALIDATION_ERROR")
        if tags is not None and not isinstance(tags, list):
            raise ApiError("tags 必须是数组", code="VALIDATION_ERROR")
        if metadata is not None and not isinstance(metadata, dict):
            raise ApiError("metadata 必须是对象", code="VALIDATION_ERROR")

        payload: dict[str, Any] = {
            "agent_id": agent_id,
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "tags": tags or [],
            "metadata": metadata or {},
            "auto_route": auto_route,
        }
        if visibility:
            payload["visibility"] = visibility

        res = _request("POST", "/memories", payload)
        if not isinstance(res, dict):
            raise ApiError("接口返回格式异常", code="API_ERROR")

        message = res.get("message")
        memory_id = res.get("memory_id") or _extract_uuid(message)
        return _tool_ok(
            {
                "memory_id": memory_id,
                "table": res.get("table"),
                "visibility": res.get("visibility"),
                "message": message or "创建成功",
            }
        )
    except Exception as e:
        return _tool_fail(e)


@mcp.tool(name="memory_search", description="搜索记忆")
def memory_search(params: dict[str, Any]) -> dict[str, Any]:
    try:
        agent_id = (params.get("agent_id") or "").strip()
        query = (params.get("query") or "").strip()
        limit = int(params.get("limit", 10))
        match_threshold = float(params.get("match_threshold", 0.5))

        _require_uuid(agent_id, "agent_id")
        if not query:
            raise ApiError("query 不能为空", code="VALIDATION_ERROR")
        limit = max(1, min(limit, 50))
        match_threshold = max(0.0, min(match_threshold, 1.0))

        res = _request(
            "POST",
            "/memories/search/text",
            {
                "agent_id": agent_id,
                "query": query,
                "match_count": limit,
                "match_threshold": match_threshold,
            },
        )

        items: list[dict[str, Any]]
        if isinstance(res, list):
            items = res
        elif isinstance(res, dict):
            # 兼容不同返回结构
            maybe = res.get("items") or res.get("memories") or []
            items = maybe if isinstance(maybe, list) else []
        else:
            items = []

        compact = [
            {
                "id": x.get("id"),
                "content": x.get("content"),
                "memory_type": x.get("memory_type"),
                "similarity": x.get("similarity"),
                "importance": x.get("importance"),
            }
            for x in items
            if isinstance(x, dict)
        ]

        return _tool_ok({"count": len(compact), "items": compact})
    except Exception as e:
        return _tool_fail(e)


@mcp.tool(name="chat", description="对话")
def chat(
    agent_id: str,
    session_id: str,
    user_message: str,
    use_memory: bool = True,
    use_history: bool = True,
    auto_extract: bool = True,
    memory_count: int = 5,
    history_count: int = 6,
) -> dict[str, Any]:
    try:
        _require_uuid(agent_id, "agent_id")
        if not session_id.strip():
            raise ApiError("session_id 不能为空", code="VALIDATION_ERROR")
        if not user_message.strip():
            raise ApiError("user_message 不能为空", code="VALIDATION_ERROR")

        payload = {
            "agent_id": agent_id,
            "session_id": session_id,
            "user_message": user_message,
            "use_memory": use_memory,
            "use_history": use_history,
            "auto_extract": auto_extract,
            "memory_count": max(1, min(memory_count, 20)),
            "history_count": max(1, min(history_count, 20)),
        }

        res = _request("POST", "/chat", payload)
        if not isinstance(res, dict):
            raise ApiError("接口返回格式异常", code="API_ERROR")

        memories_used = res.get("memories_used", 0)
        if isinstance(memories_used, list):
            memories_used = len(memories_used)

        history_used = res.get("history_used", 0)
        if isinstance(history_used, list):
            history_used = len(history_used)

        extracted = res.get("extracted_memories") or res.get("memories_extracted") or []
        extracted_count = len(extracted) if isinstance(extracted, list) else 0

        return _tool_ok(
            {
                "reply": res.get("reply"),
                "conversation_id": res.get("conversation_id"),
                "memories_used": memories_used,
                "history_used": history_used,
                "extracted_count": extracted_count,
                "stored_count": res.get("stored_count"),
            }
        )
    except Exception as e:
        return _tool_fail(e)


if __name__ == "__main__":
    mcp.run(transport="stdio")
