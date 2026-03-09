# ============================================================
# 多智能体记忆中枢 - API 路由
# ============================================================
# 功能：定义 RESTful API 端点
# 作者：小码
# 日期：2026-03-05
# ============================================================

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
import json
import uuid
import logging

from ..models.schemas import (
    AgentCreate, Agent, AgentUpdate,
    MemoryCreate, Memory, MemoryUpdate, MemorySearchRequest, MemoryTextSearchRequest, MemorySearchResult,
    HealthResponse, MessageResponse, ErrorResponse
)
from ..models.conversation import EnhancedChatRequest, EnhancedReply
from ..services.memory_service import memory_service
from ..services.dialogue_enhancement_service import dialogue_enhancement_service
from ..database import db

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# API 分组标签
# ============================================================
TAG_RECOMMEND = "⭐ 推荐接口"
TAG_AGENT = "智能体管理"
TAG_MEMORY = "记忆管理"
TAG_SEARCH = "搜索"
TAG_MAINTAIN = "维护"


# ============================================================
# 健康检查
# ============================================================

@router.get(
    "/health", 
    response_model=HealthResponse,
    tags=[TAG_RECOMMEND],
    summary="健康检查",
    description="检查服务是否正常运行，包括数据库连接状态"
)
async def health_check():
    """
    健康检查端点
    
    用于检查服务是否正常运行
    """
    try:
        # 测试数据库连接
        await db.fetchval("SELECT 1")
        return HealthResponse(database="connected")
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(database=f"error: {str(e)}")


# ============================================================
# 增强对话 API（核心功能）
# ============================================================

@router.post(
    "/chat",
    response_model=EnhancedReply,
    tags=[TAG_RECOMMEND],
    summary="增强对话（推荐）",
    description="""
🚀 **核心功能**：基于记忆的智能对话

工作流程：
1. 检索相关记忆（向量搜索）
2. 获取对话历史
3. 用 LLM 生成增强回复
4. 记录对话
5. 自动提取新记忆
""",
    responses={
        200: {"description": "返回增强回复"},
        400: {"description": "请求参数错误"},
        404: {"description": "智能体不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def enhanced_chat(request: EnhancedChatRequest):
    """
    增强对话 - 基于记忆的智能对话（推荐使用）
    
    这是核心功能接口，实现了「对话增强」：
    
    **工作流程**：
    1. 检索相关记忆（基于用户消息的向量搜索）
    2. 获取对话历史（如果提供了 session_id）
    3. 用 LLM 生成个性化回复（融合记忆和历史）
    4. 记录对话到数据库
    5. 自动提取新记忆（可选）
    
    **请求参数**：
    - **agent_id**: 智能体 ID（必填）
    - **session_id**: 会话标识（必填）
    - **user_message**: 用户消息（必填）
    - **use_memory**: 是否使用记忆增强（默认 true）
    - **use_history**: 是否使用对话历史（默认 true）
    - **auto_extract**: 是否自动提取记忆（默认 true）
    
    **示例请求**：
    ```json
    {
      "agent_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "session_123",
      "user_message": "你好，我是憨货，喜欢吐槽风格"
    }
    ```
    """
    try:
        result = await dialogue_enhancement_service.chat_and_remember(
            agent_id=str(request.agent_id),
            session_id=request.session_id,
            user_message=request.user_message,
            auto_extract=request.auto_extract
        )
        
        return EnhancedReply(**result)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"增强对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )


# ============================================================
# 智能体管理 API
# ============================================================

@router.post(
    "/agents", 
    response_model=MessageResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=[TAG_RECOMMEND],
    summary="创建智能体（推荐）",
    responses={
        201: {"description": "智能体创建成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def create_agent(agent: AgentCreate):
    """
    注册新智能体
    
    - **name**: 智能体名称（必填，1-255字符）
    - **description**: 智能体描述
    - **capabilities**: 能力标签列表
    - **metadata**: 额外元数据
    """
    try:
        query = """
            INSERT INTO agents (name, description, capabilities, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        
        agent_id = await db.fetchval(
            query,
            agent.name,
            agent.description,
            agent.capabilities,
            json.dumps(agent.metadata)
        )
        
        return MessageResponse(message=f"智能体创建成功，ID: {agent_id}")
    
    except Exception as e:
        logger.error(f"创建智能体失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )


@router.get(
    "/agents/{agent_id}", 
    response_model=Agent,
    tags=[TAG_AGENT],
    summary="获取智能体详情",
    responses={
        200: {"description": "返回智能体详情"},
        400: {"model": ErrorResponse, "description": "无效的 ID 格式"},
        404: {"model": ErrorResponse, "description": "智能体不存在"}
    }
)
async def get_agent(agent_id: str):
    """
    获取智能体信息
    
    - **agent_id**: 智能体 UUID
    """
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    query = "SELECT * FROM agents WHERE id = $1"
    row = await db.fetchrow(query, agent_uuid)
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"智能体不存在: {agent_id}"
        )
    
    return Agent(**dict(row))


@router.get(
    "/agents", 
    response_model=List[Agent],
    tags=[TAG_AGENT],
    summary="列出所有智能体",
    responses={
        200: {"description": "返回智能体列表"}
    }
)
async def list_agents(
    limit: int = Query(default=50, ge=1, le=100, description="返回数量"),
    offset: int = Query(default=0, ge=0, description="偏移量")
):
    """
    列出所有智能体
    
    - **limit**: 返回数量（1-100）
    - **offset**: 偏移量
    """
    query = """
        SELECT * FROM agents
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
    """
    rows = await db.fetch(query, limit, offset)
    agents = []
    for row in rows:
        data = dict(row)
        # 解析 JSON 字符串字段
        if isinstance(data.get('metadata'), str):
            try:
                data['metadata'] = json.loads(data['metadata'])
            except:
                data['metadata'] = {}
        if isinstance(data.get('capabilities'), str):
            try:
                data['capabilities'] = json.loads(data['capabilities'])
            except:
                data['capabilities'] = []
        agents.append(Agent(**data))
    return agents


@router.put(
    "/agents/{agent_id}",
    response_model=Agent,
    tags=[TAG_AGENT],
    summary="更新智能体信息",
    responses={
        200: {"description": "智能体更新成功"},
        400: {"model": ErrorResponse, "description": "无效的 ID 格式"},
        404: {"model": ErrorResponse, "description": "智能体不存在"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def update_agent(agent_id: str, agent_update: AgentUpdate):
    """
    更新智能体信息
    
    - **agent_id**: 智能体 UUID
    - 只更新请求中提供的字段
    """
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    # ============================================================
# 构建动态更新语句
# ============================================================
# 安全说明：
# 1. 字段名通过白名单 ALLOWED_FIELDS 验证，防止 SQL 注入
# 2. 字段值通过参数化查询 ($1, $2...) 传递，而非字符串拼接
# 3. 当前实现中，字段名是代码硬编码的，不是用户输入，因此天然安全
# 4. 白名单验证作为额外防护层，确保即使代码被修改也能保持安全
# ============================================================
    ALLOWED_FIELDS = {'name', 'description', 'capabilities', 'metadata'}
    
    updates = []
    params = [agent_uuid]
    param_idx = 2
    
    if agent_update.name is not None:
        field = 'name'
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"非法字段: {field}")
        updates.append(f"{field} = ${param_idx}")
        params.append(agent_update.name)
        param_idx += 1
    
    if agent_update.description is not None:
        field = 'description'
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"非法字段: {field}")
        updates.append(f"{field} = ${param_idx}")
        params.append(agent_update.description)
        param_idx += 1
    
    if agent_update.capabilities is not None:
        field = 'capabilities'
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"非法字段: {field}")
        updates.append(f"{field} = ${param_idx}")
        params.append(agent_update.capabilities)
        param_idx += 1
    
    if agent_update.metadata is not None:
        field = 'metadata'
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"非法字段: {field}")
        updates.append(f"{field} = ${param_idx}")
        params.append(json.dumps(agent_update.metadata))
        param_idx += 1
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有提供要更新的字段"
        )
    
    query = f"""
        UPDATE agents 
        SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        RETURNING *
    """
    
    try:
        row = await db.fetchrow(query, *params)
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"智能体不存在: {agent_id}"
            )
        
        return Agent(**dict(row))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新智能体失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )


@router.delete(
    "/agents/{agent_id}",
    response_model=MessageResponse,
    tags=[TAG_AGENT],
    summary="删除智能体",
    responses={
        200: {"description": "智能体删除成功"},
        400: {"model": ErrorResponse, "description": "无效的 ID 格式"},
        404: {"model": ErrorResponse, "description": "智能体不存在"}
    }
)
async def delete_agent(agent_id: str):
    """
    删除智能体
    
    - **agent_id**: 智能体 UUID
    - 注意：删除智能体会级联删除其所有记忆
    """
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    query = "DELETE FROM agents WHERE id = $1"
    result = await db.execute(query, agent_uuid)
    
    if result == "DELETE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"智能体不存在: {agent_id}"
        )
    
    return MessageResponse(message="智能体删除成功")


# ============================================================
# 记忆管理 API
# ============================================================

@router.post(
    "/memories", 
    response_model=MessageResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=[TAG_RECOMMEND],
    summary="创建记忆（推荐）",
    responses={
        201: {"description": "记忆创建成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        404: {"model": ErrorResponse, "description": "智能体不存在"},
        422: {"model": ErrorResponse, "description": "embedding 维度错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def create_memory(memory: MemoryCreate):
    """
    创建新记忆
    
    - **agent_id**: 所属智能体 ID（必填）
    - **content**: 记忆内容（必填）
    - **memory_type**: 记忆类型 (fact/preference/skill/experience)
    - **importance**: 重要性分数 (0-1)
    - **tags**: 标签列表
    - **embedding**: 向量嵌入（可选，1536维）
    - **expires_at**: 过期时间
    """
    try:
        # 检查智能体是否存在
        agent_exists = await db.fetchval(
            "SELECT EXISTS(SELECT 1 FROM agents WHERE id = $1)",
            memory.agent_id
        )
        
        if not agent_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"智能体不存在: {memory.agent_id}"
            )
        
        memory_id = await memory_service.create_memory(memory)
        return MessageResponse(message=f"记忆创建成功，ID: {memory_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )


@router.get(
    "/memories/{memory_id}", 
    response_model=dict,
    tags=[TAG_MEMORY],
    summary="获取单条记忆",
    responses={
        200: {"description": "返回记忆详情"},
        400: {"model": ErrorResponse, "description": "无效的 ID 格式"},
        404: {"model": ErrorResponse, "description": "记忆不存在"}
    }
)
async def get_memory(memory_id: str):
    """
    获取单条记忆
    
    - **memory_id**: 记忆 UUID
    - 获取时会自动增加访问计数
    """
    try:
        uuid.UUID(memory_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的记忆 ID 格式，需要 UUID 格式"
        )
    
    memory = await memory_service.get_memory(memory_id)
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"记忆不存在: {memory_id}"
        )
    
    return memory


@router.put(
    "/memories/{memory_id}",
    response_model=dict,
    tags=[TAG_MEMORY],
    summary="更新记忆",
    responses={
        200: {"description": "记忆更新成功"},
        400: {"model": ErrorResponse, "description": "无效的 ID 格式"},
        404: {"model": ErrorResponse, "description": "记忆不存在"},
        422: {"model": ErrorResponse, "description": "embedding 维度错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def update_memory(memory_id: str, memory_update: MemoryUpdate):
    """
    更新记忆
    
    - **memory_id**: 记忆 UUID
    - 只更新请求中提供的字段
    """
    try:
        uuid.UUID(memory_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的记忆 ID 格式，需要 UUID 格式"
        )
    
    if not any([
        memory_update.content,
        memory_update.memory_type,
        memory_update.importance is not None,
        memory_update.tags,
        memory_update.metadata,
        memory_update.embedding,
        memory_update.expires_at
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有提供要更新的字段"
        )
    
    try:
        updated = await memory_service.update_memory(memory_id, memory_update)
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"记忆不存在: {memory_id}"
            )
        
        return updated
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )


@router.delete(
    "/memories/{memory_id}", 
    response_model=MessageResponse,
    tags=[TAG_MEMORY],
    summary="删除记忆",
    responses={
        200: {"description": "记忆删除成功"},
        400: {"model": ErrorResponse, "description": "无效的 ID 格式"},
        404: {"model": ErrorResponse, "description": "记忆不存在"}
    }
)
async def delete_memory(memory_id: str):
    """
    删除记忆
    
    - **memory_id**: 记忆 UUID
    """
    try:
        uuid.UUID(memory_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的记忆 ID 格式，需要 UUID 格式"
        )
    
    success = await memory_service.delete_memory(memory_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"记忆不存在: {memory_id}"
        )
    
    return MessageResponse(message="记忆删除成功")


@router.post(
    "/memories/search", 
    response_model=List[MemorySearchResult],
    tags=[TAG_SEARCH],
    summary="向量相似性搜索（需自备向量）",
    responses={
        200: {"description": "返回相似记忆列表"},
        422: {"model": ErrorResponse, "description": "embedding 维度错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def search_memories(request: MemorySearchRequest):
    """
    向量相似性搜索（旧版：需要 query_embedding）
    
    - **query_embedding**: 查询向量（必填，1536维）
    - **agent_id**: 限定智能体（可选）
    - **match_threshold**: 相似度阈值 (0-1)
    - **match_count**: 返回数量 (1-100)
    
    注意：此接口需要客户端提供向量。推荐使用 /memories/search/text 接口。
    """
    try:
        results = await memory_service.search_similar(request)
        return results
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )


@router.post(
    "/memories/search/text", 
    response_model=List[MemorySearchResult],
    tags=[TAG_RECOMMEND],
    summary="文本相似性搜索（推荐）",
    responses={
        200: {"description": "返回相似记忆列表"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误（可能是 Embedding API 问题）"}
    }
)
async def search_memories_by_text(request: MemoryTextSearchRequest):
    """
    文本相似性搜索（推荐）
    
    输入文本，服务端自动生成向量并搜索。
    
    - **query**: 查询文本（必填）
    - **agent_id**: 限定智能体（可选）
    - **match_threshold**: 相似度阈值 (0-1)，默认 0.7
    - **match_count**: 返回数量 (1-100)，默认 10
    
    示例请求：
    ```json
    {
      "query": "谁是主人？",
      "limit": 5
    }
    ```
    """
    try:
        results = await memory_service.search_by_text(request)
        return results
    except ValueError as e:
        logger.error(f"文本搜索参数错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="搜索参数错误，请检查输入"
        )
    except Exception as e:
        logger.error(f"文本搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )


@router.get(
    "/agents/{agent_id}/memories", 
    response_model=List[dict],
    tags=[TAG_MEMORY],
    summary="列出智能体的所有记忆",
    responses={
        200: {"description": "返回记忆列表"},
        400: {"model": ErrorResponse, "description": "无效的 ID 格式"},
        404: {"model": ErrorResponse, "description": "智能体不存在"}
    }
)
async def list_agent_memories(
    agent_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="返回数量"),
    offset: int = Query(default=0, ge=0, description="偏移量")
):
    """
    列出智能体的所有记忆
    
    - **agent_id**: 智能体 UUID
    - **limit**: 返回数量 (1-100)
    - **offset**: 偏移量
    """
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    # 检查智能体是否存在
    agent_exists = await db.fetchval(
        "SELECT EXISTS(SELECT 1 FROM agents WHERE id = $1)",
        agent_uuid
    )
    
    if not agent_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"智能体不存在: {agent_id}"
        )
    
    memories = await memory_service.list_memories_by_agent(agent_id, limit, offset)
    return memories


@router.post(
    "/memories/cleanup", 
    response_model=MessageResponse,
    tags=[TAG_MAINTAIN],
    summary="清理过期记忆",
    responses={
        200: {"description": "清理完成"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)
async def cleanup_memories(
    days_old: int = Query(default=30, ge=1, le=365, description="保留天数"),
    min_importance: float = Query(default=0.3, ge=0.0, le=1.0, description="最小重要性阈值"),
    max_access_count: int = Query(default=3, ge=0, le=100, description="最大访问次数阈值")
):
    """
    清理过期记忆
    
    删除满足以下所有条件的记忆：
    - 创建时间超过 days_old 天
    - 重要性低于 min_importance
    - 访问次数低于 max_access_count
    
    - **days_old**: 保留天数 (1-365)
    - **min_importance**: 最小重要性阈值 (0-1)
    - **max_access_count**: 最大访问次数阈值 (0-100)
    """
    try:
        deleted_count = await memory_service.cleanup_old_memories(
            days_old, min_importance, max_access_count
        )
        return MessageResponse(message=f"已清理 {deleted_count} 条过期记忆")
    except Exception as e:
        logger.error(f"清理记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )