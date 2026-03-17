# ============================================================
# 多智能体记忆中枢 - 双表记忆 API 路由
# ============================================================
# 功能：支持 private/shared 双表架构的记忆管理
# 作者：小码
# 日期：2026-03-09
# 更新：2026-03-17 - 添加权限校验
# ============================================================

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from ..services.memory_service import memory_service
from ..models.schemas import MemoryCreate, MemoryTextSearchRequest, MemorySearchResult
from ..database import db
from ..services.permission_service import permission_service

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
    
    **权限要求（2026-03-17 憨货亲定）**:
    - private_memories: 仅创建者可写
    - shared_memories: 小搜/小写/小审/小析/小览/小图/小排可写，小码池禁止
    """
    try:
        # ============================================================
        # 【权限校验】检查智能体是否有权限写入对应表
        # ============================================================
        # 先判断路由目标
        if memory.visibility:
            target_table = "private_memories" if memory.visibility == "private" else "shared_memories"
        else:
            # 自动路由，先检查 shared_memories 权限
            # 如果没有 shared_memories 写权限，强制使用 private
            if not permission_service.check_permission(str(memory.agent_id), "shared_memories", "write"):
                target_table = "private_memories"
                logger.info(f"智能体 {memory.agent_id} 无 shared_memories 写权限，路由到 private_memories")
            else:
                target_table = None  # 让 memory_service 自动判断
        
        # 如果指定了目标表，检查权限
        if target_table:
            if target_table == "shared_memories":
                permission_service.require_permission(str(memory.agent_id), "shared_memories", "write")
            # private_memories 只检查是否是 owner（在 service 层处理）
        
        # 创建记忆
        memory_id, table, visibility, auto_routed = await memory_service.create_memory(memory)
        
        # 再次验证最终路由结果
        if table == "shared_memories":
            permission_service.require_permission(str(memory.agent_id), "shared_memories", "write")
        
        return MemoryCreateResponse(
            memory_id=memory_id,
            table=table,
            visibility=visibility,
            auto_routed=auto_routed,
            message=f"记忆创建成功，已路由到 {table} 表"
        )
    
    except HTTPException:
        raise  # 权限异常直接抛出
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


# ============================================================
# 导出记忆为 Markdown
# ============================================================

# 记忆类型的中文映射和图标
MEMORY_TYPE_CONFIG = {
    "fact": {"icon": "📌", "label": "事实记忆"},
    "preference": {"icon": "❤️", "label": "偏好记忆"},
    "skill": {"icon": "🛠️", "label": "技能记忆"},
    "experience": {"icon": "📖", "label": "经验记忆"},
}


@router.get(
    "/memories/export/markdown",
    response_class=PlainTextResponse,
    tags=["双表记忆"],
    summary="导出所有记忆为 Markdown",
)
async def export_memories_markdown(
    agent_id: Optional[str] = Query(default=None, description="智能体 ID（可选，不填则导出所有）")
):
    """
    将所有记忆导出为 Markdown 格式
    
    **输出格式**：
    ```markdown
    # Memory Hub - 记忆导出
    
    **导出时间**: 2026-03-17 13:10:00
    **智能体**: 傻妞 (ID: xxx)
    
    ---
    
    ## 📌 事实记忆
    
    - 用户叫憨货，住在上海
    - 喜欢简洁的回答，讨厌废话
    
    ---
    
    ## ❤️ 偏好记忆
    ...
    ```
    
    **参数**:
    - **agent_id**: 智能体 ID（可选，不填则导出所有智能体的记忆）
    """
    try:
        # 获取当前时间
        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 查询智能体信息
        agent_info = ""
        if agent_id:
            try:
                agent_row = await db.fetchrow(
                    "SELECT id, name FROM agents WHERE id = $1",
                    uuid.UUID(agent_id)
                )
                if agent_row:
                    agent_info = f"**智能体**: {agent_row['name']} (ID: {agent_row['id']})"
                else:
                    agent_info = f"**智能体**: 未知 (ID: {agent_id})"
            except ValueError:
                agent_info = f"**智能体**: ID 无效 ({agent_id})"
        else:
            agent_info = "**智能体**: 全部"
        
        # 查询所有记忆
        memories = []
        
        # 查询 private_memories
        if agent_id:
            try:
                private_query = """
                    SELECT id, agent_id, content, memory_type, importance, 
                           tags, created_at, 'private' as visibility
                    FROM private_memories
                    WHERE agent_id = $1
                    ORDER BY importance DESC, created_at DESC
                """
                rows = await db.fetch(private_query, uuid.UUID(agent_id))
                memories.extend([dict(row) for row in rows])
            except ValueError:
                pass  # 无效的 agent_id，跳过
        else:
            private_query = """
                SELECT id, agent_id, content, memory_type, importance, 
                       tags, created_at, 'private' as visibility
                FROM private_memories
                ORDER BY importance DESC, created_at DESC
            """
            rows = await db.fetch(private_query)
            memories.extend([dict(row) for row in rows])
        
        # 查询 shared_memories
        if agent_id:
            try:
                shared_query = """
                    SELECT id, agent_id, content, memory_type, importance, 
                           tags, created_at, 'shared' as visibility
                    FROM shared_memories
                    WHERE agent_id = $1
                    ORDER BY importance DESC, created_at DESC
                """
                rows = await db.fetch(shared_query, uuid.UUID(agent_id))
                memories.extend([dict(row) for row in rows])
            except ValueError:
                pass
        else:
            shared_query = """
                SELECT id, agent_id, content, memory_type, importance, 
                       tags, created_at, 'shared' as visibility
                FROM shared_memories
                ORDER BY importance DESC, created_at DESC
            """
            rows = await db.fetch(shared_query)
            memories.extend([dict(row) for row in rows])
        
        # 按类型分组
        memories_by_type = {}
        for m in memories:
            mtype = m.get("memory_type", "fact")
            if mtype not in memories_by_type:
                memories_by_type[mtype] = []
            memories_by_type[mtype].append(m)
        
        # 构建 Markdown
        lines = [
            "# Memory Hub - 记忆导出",
            "",
            f"**导出时间**: {export_time}",
            agent_info,
            "",
            "---",
            "",
            f"**总计**: {len(memories)} 条记忆",
            "",
            "---",
        ]
        
        # 按类型输出
        for mtype in ["fact", "preference", "skill", "experience"]:
            config = MEMORY_TYPE_CONFIG.get(mtype, {"icon": "📝", "label": f"{mtype}记忆"})
            type_memories = memories_by_type.get(mtype, [])
            
            lines.append("")
            lines.append(f"## {config['icon']} {config['label']}")
            lines.append("")
            
            if type_memories:
                for m in type_memories:
                    content = m.get("content", "")
                    # 添加标签信息（如果有）
                    tags = m.get("tags", [])
                    if tags:
                        # 处理可能的 JSON 字符串
                        if isinstance(tags, str):
                            try:
                                import json
                                tags = json.loads(tags)
                            except:
                                tags = []
                        if tags:
                            tag_str = " ".join([f"`{t}`" for t in tags])
                            lines.append(f"- {content} {tag_str}")
                        else:
                            lines.append(f"- {content}")
                    else:
                        lines.append(f"- {content}")
            else:
                lines.append("_暂无记忆_")
            
            lines.append("")
        
        # 添加页脚
        lines.extend([
            "---",
            "",
            "_由 Memory Hub 自动生成_",
        ])
        
        markdown_content = "\n".join(lines)
        
        return PlainTextResponse(
            content=markdown_content,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=memory-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
            }
        )
    
    except Exception as e:
        logger.error(f"导出记忆失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败：{str(e)}"
        )
