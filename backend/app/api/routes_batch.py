# ============================================================
# 批量接口路由
# ============================================================
# 功能：记忆批量创建/搜索、任务批量状态更新
# 响应：统一使用 {success,data} / {success,error}
# ============================================================

from typing import Any, Dict, List, Optional, Literal
import json
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from ..auth import verify_api_key
from ..database import db
from ..models.schemas import MemoryCreate
from ..services.memory_service import memory_service
from ..services.idempotency_service import idempotency_service


router = APIRouter(dependencies=[Depends(verify_api_key)])


# ==================== 统一响应 ====================

def ok(data: Any) -> Dict[str, Any]:
    return {"success": True, "data": data}


def fail(code: str, message: str) -> Dict[str, Any]:
    return {"success": False, "error": {"code": code, "message": message}}


# ==================== 请求模型 ====================

class MemoryBatchCreateRequest(BaseModel):
    idempotency_key: Optional[str] = Field(default=None, min_length=1, max_length=128)
    items: List[MemoryCreate] = Field(..., min_length=1, max_length=100)


class MemorySearchBatchQuery(BaseModel):
    agent_id: str
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    visibility: Literal["private", "shared"] = "private"

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("agent_id 必须是合法 UUID")


class MemoryBatchSearchRequest(BaseModel):
    idempotency_key: Optional[str] = Field(default=None, min_length=1, max_length=128)
    queries: List[MemorySearchBatchQuery] = Field(..., min_length=1, max_length=100)


class TaskBatchStatusItem(BaseModel):
    task_id: str
    status: Literal[
        "pending", "queued", "running", "paused", "completed", "failed", "cancelled", "timeout"
    ]
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    progress_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("task_id 必须是合法 UUID")


class TaskBatchStatusRequest(BaseModel):
    idempotency_key: Optional[str] = Field(default=None, min_length=1, max_length=128)
    items: List[TaskBatchStatusItem] = Field(..., min_length=1, max_length=200)


# ==================== 辅助函数 ====================

async def _get_cached_if_any(endpoint: str, idempotency_key: Optional[str], payload: Any):
    if not idempotency_key:
        return None
    return await idempotency_service.get_cached_response(endpoint, idempotency_key, payload)


async def _save_cache_if_needed(
    endpoint: str, idempotency_key: Optional[str], payload: Any, response_data: dict
):
    if idempotency_key:
        await idempotency_service.save_response(endpoint, idempotency_key, payload, response_data)


# ==================== 批量接口 ====================

@router.post("/memories/batch", tags=["批量接口"], summary="批量创建记忆")
async def create_memories_batch(request: MemoryBatchCreateRequest):
    endpoint = "/api/v1/memories/batch"

    try:
        payload = request.model_dump(mode="json")
        cached = await _get_cached_if_any(endpoint, request.idempotency_key, payload)
        if cached is not None:
            return cached

        results = []
        succeeded = 0

        for idx, item in enumerate(request.items):
            try:
                agent_exists = await db.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM agents WHERE id = $1)",
                    item.agent_id,
                )
                if not agent_exists:
                    raise ValueError(f"智能体不存在: {item.agent_id}")

                memory_id, table, visibility, auto_routed = await memory_service.create_memory(item)
                results.append(
                    {
                        "index": idx,
                        "success": True,
                        "data": {
                            "memory_id": memory_id,
                            "table": table,
                            "visibility": visibility,
                            "auto_routed": auto_routed,
                        },
                    }
                )
                succeeded += 1
            except Exception as e:
                results.append(
                    {
                        "index": idx,
                        "success": False,
                        "error": {"code": "MEMORY_CREATE_FAILED", "message": str(e)},
                    }
                )

        response_data = ok(
            {
                "total": len(request.items),
                "succeeded": succeeded,
                "failed": len(request.items) - succeeded,
                "partial_success": succeeded != len(request.items),
                "results": results,
            }
        )

        await _save_cache_if_needed(endpoint, request.idempotency_key, payload, response_data)
        return response_data

    except ValueError as e:
        return fail("IDEMPOTENCY_CONFLICT", str(e))
    except Exception as e:
        return fail("MEMORY_BATCH_CREATE_FAILED", str(e))


@router.post("/memories/search/batch", tags=["批量接口"], summary="批量搜索记忆")
async def search_memories_batch(request: MemoryBatchSearchRequest):
    endpoint = "/api/v1/memories/search/batch"

    try:
        payload = request.model_dump(mode="json")
        cached = await _get_cached_if_any(endpoint, request.idempotency_key, payload)
        if cached is not None:
            return cached

        results = []
        succeeded = 0

        for idx, item in enumerate(request.queries):
            try:
                if item.visibility == "private":
                    matched = await memory_service.search_private(item.agent_id, item.query, item.limit)
                else:
                    matched = await memory_service.search_shared(item.agent_id, item.query, item.limit)

                results.append(
                    {
                        "index": idx,
                        "success": True,
                        "data": {
                            "count": len(matched),
                            "items": matched,
                        },
                    }
                )
                succeeded += 1
            except Exception as e:
                results.append(
                    {
                        "index": idx,
                        "success": False,
                        "error": {"code": "MEMORY_SEARCH_FAILED", "message": str(e)},
                    }
                )

        response_data = ok(
            {
                "total": len(request.queries),
                "succeeded": succeeded,
                "failed": len(request.queries) - succeeded,
                "partial_success": succeeded != len(request.queries),
                "results": results,
            }
        )

        await _save_cache_if_needed(endpoint, request.idempotency_key, payload, response_data)
        return response_data

    except ValueError as e:
        return fail("IDEMPOTENCY_CONFLICT", str(e))
    except Exception as e:
        return fail("MEMORY_BATCH_SEARCH_FAILED", str(e))


@router.patch("/tasks/batch/status", tags=["批量接口"], summary="批量更新任务状态")
async def update_tasks_batch_status(request: TaskBatchStatusRequest):
    endpoint = "/api/v1/tasks/batch/status"

    try:
        payload = request.model_dump(mode="json")
        cached = await _get_cached_if_any(endpoint, request.idempotency_key, payload)
        if cached is not None:
            return cached

        results = []
        succeeded = 0

        for idx, item in enumerate(request.items):
            try:
                task_uuid = uuid.UUID(item.task_id)

                updates = []
                params = [task_uuid]
                param_idx = 2

                if item.status is not None:
                    if item.status == "running":
                        updates.append("started_at = CURRENT_TIMESTAMP")
                    elif item.status in ["completed", "failed", "cancelled", "timeout"]:
                        updates.append("completed_at = CURRENT_TIMESTAMP")

                    updates.append(f"status = ${param_idx}::task_status")
                    params.append(item.status)
                    param_idx += 1

                if item.progress is not None:
                    updates.append(f"progress = ${param_idx}")
                    params.append(item.progress)
                    param_idx += 1

                if item.progress_message is not None:
                    updates.append(f"progress_message = ${param_idx}")
                    params.append(item.progress_message)
                    param_idx += 1

                if item.result is not None:
                    updates.append(f"result = ${param_idx}")
                    params.append(json.dumps(item.result, ensure_ascii=False))
                    param_idx += 1

                if item.error_message is not None:
                    updates.append(f"error_message = ${param_idx}")
                    params.append(item.error_message)
                    param_idx += 1

                if not updates:
                    raise ValueError("没有提供要更新的字段")

                updates.append("updated_at = CURRENT_TIMESTAMP")

                query = f"""
                    UPDATE parallel_tasks
                    SET {', '.join(updates)}
                    WHERE id = $1
                """

                result = await db.execute(query, *params)
                if result == "UPDATE 0":
                    raise ValueError(f"任务不存在: {item.task_id}")

                results.append(
                    {
                        "index": idx,
                        "success": True,
                        "data": {
                            "task_id": item.task_id,
                            "status": item.status,
                        },
                    }
                )
                succeeded += 1
            except Exception as e:
                results.append(
                    {
                        "index": idx,
                        "success": False,
                        "error": {"code": "TASK_UPDATE_FAILED", "message": str(e)},
                    }
                )

        response_data = ok(
            {
                "total": len(request.items),
                "succeeded": succeeded,
                "failed": len(request.items) - succeeded,
                "partial_success": succeeded != len(request.items),
                "results": results,
            }
        )

        await _save_cache_if_needed(endpoint, request.idempotency_key, payload, response_data)
        return response_data

    except ValueError as e:
        return fail("IDEMPOTENCY_CONFLICT", str(e))
    except Exception as e:
        return fail("TASK_BATCH_UPDATE_FAILED", str(e))
