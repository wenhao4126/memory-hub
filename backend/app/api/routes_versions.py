# ============================================================
# Memory Hub - 记忆版本控制 API 路由
# ============================================================
# 功能：提供版本控制的 RESTful API
# 作者：小码 1 号
# 日期：2026-03-23
# ============================================================

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging

from ..models.version_schemas import (
    VersionHistoryResponse,
    VersionDetailResponse,
    RollbackRequest,
    RollbackResponse,
    VersionCompareResponse,
    MemoryUpdateWithVersion
)
from ..services.version_service import version_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memories", tags=["版本控制"])


@router.get(
    "/{memory_id}/versions",
    response_model=VersionHistoryResponse,
    summary="获取记忆版本历史",
    description="获取指定记忆的所有历史版本"
)
async def get_version_history(
    memory_id: str,
    table: str = Query('private_memories', description="表名：private_memories 或 shared_memories"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取记忆的版本历史
    
    **路径参数**：
    - memory_id: 记忆 ID
    
    **查询参数**：
    - table: 表名（private_memories 或 shared_memories）
    - limit: 返回数量（1-100）
    - offset: 偏移量（分页）
    
    **返回**：
    - 当前版本号
    - 总版本数
    - 版本历史列表（按版本号降序）
    """
    try:
        result = await version_service.get_version_history(
            memory_id=memory_id,
            table_name=table,
            limit=limit,
            offset=offset
        )
        return result
    except ValueError as e:
        logger.error(f"获取版本历史失败：{e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取版本历史异常：{e}")
        raise HTTPException(status_code=500, detail=f"服务器错误：{str(e)}")


@router.get(
    "/{memory_id}/versions/{version_number}",
    response_model=VersionDetailResponse,
    summary="获取指定版本详情",
    description="获取记忆的指定版本详情"
)
async def get_version(
    memory_id: str,
    version_number: int,
    table: str = Query('private_memories', description="表名")
):
    """
    获取指定版本的详情
    
    **路径参数**：
    - memory_id: 记忆 ID
    - version_number: 版本号
    
    **查询参数**：
    - table: 表名
    
    **返回**：
    - 版本详情（内容、类型、重要性、标签等）
    - 创建时间、修改者、修改原因
    """
    try:
        result = await version_service.get_version(
            memory_id=memory_id,
            version_number=version_number,
            table_name=table
        )
        return result
    except ValueError as e:
        logger.error(f"获取版本详情失败：{e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取版本详情异常：{e}")
        raise HTTPException(status_code=500, detail=f"服务器错误：{str(e)}")


@router.post(
    "/{memory_id}/versions/{version_number}/rollback",
    response_model=RollbackResponse,
    summary="回滚到指定版本",
    description="将记忆回滚到指定的历史版本"
)
async def rollback_version(
    memory_id: str,
    version_number: int,
    request: Optional[RollbackRequest] = None,
    table: str = Query('private_memories', description="表名")
):
    """
    回滚记忆到指定版本
    
    **路径参数**：
    - memory_id: 记忆 ID
    - version_number: 目标版本号
    
    **请求体**：
    - reason: 回滚原因（可选）
    
    **查询参数**：
    - table: 表名
    
    **返回**：
    - 回滚结果
    - 从哪个版本回滚到哪个版本
    
    **注意**：
    - 回滚会创建新版本（不会覆盖当前版本）
    - 当前版本会被自动保存到历史记录
    """
    try:
        reason = request.reason if request else None
        result = await version_service.rollback_version(
            memory_id=memory_id,
            version_number=version_number,
            reason=reason,
            table_name=table
        )
        return result
    except ValueError as e:
        logger.error(f"回滚版本失败：{e}")
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"回滚版本错误：{e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"回滚版本异常：{e}")
        raise HTTPException(status_code=500, detail=f"服务器错误：{str(e)}")


@router.get(
    "/{memory_id}/versions/compare",
    response_model=VersionCompareResponse,
    summary="比较两个版本",
    description="比较记忆的两个版本差异"
)
async def compare_versions(
    memory_id: str,
    v1: int = Query(..., description="版本号 1"),
    v2: int = Query(..., description="版本号 2"),
    table: str = Query('private_memories', description="表名")
):
    """
    比较两个版本的差异
    
    **路径参数**：
    - memory_id: 记忆 ID
    
    **查询参数**：
    - v1: 版本号 1
    - v2: 版本号 2
    - table: 表名
    
    **返回**：
    - 两个版本的详情
    - 差异列表（新增、删除、修改的字段）
    - 内容相似度（0-1）
    """
    try:
        result = await version_service.compare_versions(
            memory_id=memory_id,
            version1=v1,
            version2=v2,
            table_name=table
        )
        return result
    except ValueError as e:
        logger.error(f"比较版本失败：{e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"比较版本异常：{e}")
        raise HTTPException(status_code=500, detail=f"服务器错误：{str(e)}")


@router.put(
    "/{memory_id}/with-version",
    summary="更新记忆（带版本控制）",
    description="更新记忆内容，自动保存历史版本"
)
async def update_memory_with_version(
    memory_id: str,
    request: MemoryUpdateWithVersion,
    table: str = Query('private_memories', description="表名")
):
    """
    更新记忆（带版本控制）
    
    **路径参数**：
    - memory_id: 记忆 ID
    
    **请求体**：
    - content: 新的记忆内容
    - memory_type: 记忆类型
    - importance: 重要性
    - tags: 标签列表
    - metadata: 元数据
    - change_reason: 修改原因
    - changed_by: 修改者 ID
    
    **查询参数**：
    - table: 表名
    
    **返回**：
    - 更新后的记忆
    - 新版本号
    
    **注意**：
    - 更新会自动保存旧版本到历史记录
    - 版本号自动递增
    """
    try:
        # 构建更新字典
        updates = {}
        if request.content is not None:
            updates['content'] = request.content
        if request.memory_type is not None:
            updates['memory_type'] = request.memory_type
        if request.importance is not None:
            updates['importance'] = request.importance
        if request.tags is not None:
            updates['tags'] = request.tags
        if request.metadata is not None:
            updates['metadata'] = request.metadata
        
        result = await version_service.update_memory_with_version(
            memory_id=memory_id,
            updates=updates,
            change_reason=request.change_reason,
            changed_by=str(request.changed_by) if request.changed_by else None,
            table_name=table
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "new_version": result.get('current_version', 1),
            "memory": result
        }
    except ValueError as e:
        logger.error(f"更新记忆失败：{e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新记忆异常：{e}")
        raise HTTPException(status_code=500, detail=f"服务器错误：{str(e)}")


# 导出路由
__all__ = ['router']