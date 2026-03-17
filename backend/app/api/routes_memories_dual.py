# ============================================================
# 多智能体记忆中枢 - 双表记忆 API 路由
# ============================================================
# 功能：支持 private/shared 双表架构的记忆管理
# 作者：小码
# 日期：2026-03-09
# ============================================================

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
import logging

from ..services.memory_service import memory_service
from ..models.schemas import MemoryCreate, MemoryTextSearchRequest, MemorySearchResult

router = APIRouter()
logger = logging.getLogger(__name__)


class MemoryCreateResponse(BaseModel):
    """创建记忆响应（双表架构）"""
    memory_id: str
    table: str  # "private" or "shared"
    visibility: str
    auto_routed: bool
    message: str


class MemoryListResponse(BaseModel):
    """记忆列表响应"""
    memories: List[dict]
    total: int


# ============================================================
# 创建记忆（支持自动路由）
# ============================================================

@router.post(
    "/memories",
    response_model=MemoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["双表记忆"],
    summary="创建记忆（支持自动路由）",
)
async def create_memory_dual(memory: MemoryCreate):
    """
    创建新记忆，支持自动路由到 private 或 shared 表
    
    **自动路由规则**:
    - 私人记忆关键词：密码、习惯、喜欢、偏好、个人、账号等
    - 共同记忆关键词：经验、知识、规范、文档、项目、架构等
    - 默认：私人（保护隐私）
    
    **请求参数**:
    - **agent_id**: 智能体 ID
    - **content**: 记忆内容
    - **auto_route**: 是否自动路由（默认 true）
    - **visibility**: 手动指定可见性（auto_route=false 时使用）
    """
    try:
        # 检查智能体是否存在（简化检查）
        memory_id, table, visibility, auto_routed = await memory_service.create_memory(memory)
        
        return MemoryCreateResponse(
            memory_id=memory_id,
            table=table,
            visibility=visibility,
            auto_routed=auto_routed,
            message=f"记忆创建成功，已路由到 {table} 表"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建记忆失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败：{str(e)}"
        )


# ============================================================
# 查询记忆（支持 visibility 过滤）
# ============================================================

@router.get(
    "/agents/{agent_id}/memories",
    response_model=MemoryListResponse,
    tags=["双表记忆"],
    summary="列出智能体记忆（支持 visibility 过滤）",
)
async def list_agent_memories_dual(
    agent_id: str,
    visibility: Optional[str] = Query(default=None, description="可见性过滤：private/shared"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    列出智能体的记忆
    
    **参数**:
    - **agent_id**: 智能体 ID
    - **visibility**: 过滤类型 (private/shared/None=全部)
    - **limit**: 返回数量 (1-100)
    - **offset**: 偏移量
    """
    try:
        memories = await memory_service.list_memories_by_agent(agent_id, visibility, limit, offset)
        return MemoryListResponse(memories=memories, total=len(memories))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的 agent_id 格式"
        )
    except Exception as e:
        logger.error(f"列出记忆失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败：{str(e)}"
        )


# ============================================================
# 搜索记忆（支持 visibility 过滤）
# ============================================================

@router.post(
    "/memories/search/private",
    response_model=List[dict],
    tags=["双表记忆"],
    summary="搜索私人记忆",
)
async def search_private_memories(
    agent_id: str,
    query: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    搜索私人记忆（仅当前智能体）
    
    **参数**:
    - **agent_id**: 智能体 ID
    - **query**: 搜索文本
    - **limit**: 返回数量
    """
    try:
        results = await memory_service.search_private(agent_id, query, limit)
        return results
    except Exception as e:
        logger.error(f"搜索私人记忆失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败：{str(e)}"
        )


@router.post(
    "/memories/search/shared",
    response_model=List[dict],
    tags=["双表记忆"],
    summary="搜索共同记忆",
)
async def search_shared_memories(
    agent_id: str,
    query: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    搜索共同记忆（团队共享）
    
    **参数**:
    - **agent_id**: 智能体 ID
    - **query**: 搜索文本
    - **limit**: 返回数量
    """
    try:
        results = await memory_service.search_shared(agent_id, query, limit)
        return results
    except Exception as e:
        logger.error(f"搜索共同记忆失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败：{str(e)}"
        )


# ============================================================
# 删除记忆
# ============================================================

@router.delete(
    "/memories/{memory_id}",
    tags=["双表记忆"],
    summary="删除记忆",
)
async def delete_memory(
    memory_id: str,
    visibility: str = Query(default='private', description="表类型：private/shared")
):
    """
    删除记忆
    
    **参数**:
    - **memory_id**: 记忆 ID
    - **visibility**: 表类型 (private/shared)
    """
    try:
        success = await memory_service.delete_memory(memory_id, visibility)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记忆不存在"
            )
        return {"message": "记忆删除成功"}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的记忆 ID 格式"
        )
    except Exception as e:
        logger.error(f"删除记忆失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败：{str(e)}"
        )
