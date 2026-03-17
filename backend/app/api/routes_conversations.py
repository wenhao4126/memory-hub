# ============================================================
# 多智能体记忆中枢 - 对话相关 API
# ============================================================
# 功能：对话记录和自动记忆提取的 RESTful API
# 作者：小码
# 日期：2026-03-06
# ============================================================

from fastapi import APIRouter, HTTPException, status, Query
from typing import List
import uuid
import logging

from ..models.conversation import (
    ConversationCreate,
    Conversation,
    ConversationList,
    AutoExtractRequest,
    AutoExtractResponse,
    EnhancedChatRequest,
    EnhancedReply
)
from ..services.conversation_service import conversation_service
from ..services.auto_memory_service import auto_memory_service
from ..services.dialogue_enhancement_service import dialogue_enhancement_service
from ..database import db

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# API 分组标签
# ============================================================
TAG_CONVERSATION = "对话管理"
TAG_AUTO_MEMORY = "自动记忆"
TAG_CHAT = "对话增强"


# ============================================================
# 对话管理 API
# ============================================================

@router.post(
    "/conversations",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    tags=[TAG_CONVERSATION],
    summary="创建对话记录",
    responses={
        201: {"description": "对话记录创建成功"},
        400: {"description": "请求参数错误"},
        404: {"description": "智能体不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def create_conversation(conversation: ConversationCreate):
    """
    创建对话记录
    
    记录用户和 AI 的对话内容，关联到智能体和会话。
    
    - **agent_id**: 所属智能体 ID（必填）
    - **session_id**: 会话标识（必填，用于关联多轮对话）
    - **user_message**: 用户消息（必填）
    - **ai_response**: AI 回复（必填）
    - **metadata**: 额外元数据（可选）
    """
    try:
        conversation_id = await conversation_service.create_conversation(conversation)
        return {
            "message": "对话记录创建成功",
            "conversation_id": conversation_id
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建对话记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试"
        )


@router.get(
    "/conversations/{conversation_id}",
    response_model=dict,
    tags=[TAG_CONVERSATION],
    summary="获取对话记录",
    responses={
        200: {"description": "返回对话详情"},
        400: {"description": "无效的 ID 格式"},
        404: {"description": "对话不存在"}
    }
)
async def get_conversation(conversation_id: str):
    """
    获取单条对话记录
    
    - **conversation_id**: 对话 UUID
    """
    conversation = await conversation_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话不存在: {conversation_id}"
        )
    
    return conversation


@router.get(
    "/agents/{agent_id}/conversations",
    response_model=ConversationList,
    tags=[TAG_CONVERSATION],
    summary="列出智能体的对话",
    responses={
        200: {"description": "返回对话列表"},
        400: {"description": "无效的 ID 格式"}
    }
)
async def list_agent_conversations(
    agent_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="返回数量"),
    offset: int = Query(default=0, ge=0, description="偏移量")
):
    """
    列出智能体的所有对话
    
    - **agent_id**: 智能体 UUID
    - **limit**: 返回数量（1-100）
    - **offset**: 偏移量
    """
    try:
        uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    conversations = await conversation_service.list_conversations_by_agent(
        agent_id, limit, offset
    )
    
    return ConversationList(
        conversations=[Conversation(**conv) for conv in conversations],
        total=len(conversations),
        limit=limit,
        offset=offset
    )


@router.get(
    "/agents/{agent_id}/sessions/{session_id}/conversations",
    response_model=ConversationList,
    tags=[TAG_CONVERSATION],
    summary="列出会话的对话",
    responses={
        200: {"description": "返回对话列表"},
        400: {"description": "无效的 ID 格式"}
    }
)
async def list_session_conversations(
    agent_id: str,
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500, description="返回数量")
):
    """
    列出会话的所有对话（按时间正序）
    
    - **agent_id**: 智能体 UUID
    - **session_id**: 会话标识
    - **limit**: 返回数量（1-500）
    """
    try:
        uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    conversations = await conversation_service.list_conversations_by_session(
        agent_id, session_id, limit
    )
    
    return ConversationList(
        conversations=[Conversation(**conv) for conv in conversations],
        total=len(conversations),
        limit=limit,
        offset=0
    )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=dict,
    tags=[TAG_CONVERSATION],
    summary="删除对话记录",
    responses={
        200: {"description": "对话删除成功"},
        400: {"description": "无效的 ID 格式"},
        404: {"description": "对话不存在"}
    }
)
async def delete_conversation(conversation_id: str):
    """
    删除对话记录
    
    - **conversation_id**: 对话 UUID
    """
    success = await conversation_service.delete_conversation(conversation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话不存在: {conversation_id}"
        )
    
    return {"message": "对话删除成功"}


@router.delete(
    "/agents/{agent_id}/sessions/{session_id}/conversations",
    response_model=dict,
    tags=[TAG_CONVERSATION],
    summary="删除会话的所有对话",
    responses={
        200: {"description": "对话删除成功"},
        400: {"description": "无效的 ID 格式"}
    }
)
async def delete_session_conversations(
    agent_id: str,
    session_id: str
):
    """
    删除会话的所有对话
    
    - **agent_id**: 智能体 UUID
    - **session_id**: 会话标识
    """
    try:
        uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    count = await conversation_service.delete_conversations_by_session(
        agent_id, session_id
    )
    
    return {
        "message": f"已删除 {count} 条对话",
        "deleted_count": count
    }


# ============================================================
# 自动记忆 API
# ============================================================

@router.post(
    "/memories/auto-extract",
    response_model=AutoExtractResponse,
    tags=[TAG_AUTO_MEMORY],
    summary="自动提取并存储记忆",
    responses={
        200: {"description": "提取完成"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def auto_extract_memories(request: AutoExtractRequest):
    """
    自动提取并存储记忆（核心功能）
    
    工作流程：
    1. 记录对话到数据库
    2. 用 LLM 从对话中提取关键信息
    3. 去重（避免重复存储）
    4. 按重要性排序
    5. 存储到记忆数据库
    
    提取的信息类型：
    - **facts**: 事实（用户基本信息、偏好）
    - **relationships**: 关系（用户与智能体的关系）
    - **events**: 事件（重要事件、约定）
    - **emotions**: 情感（用户的情感状态）
    
    请求参数：
    - **agent_id**: 智能体 ID（必填）
    - **session_id**: 会话标识（必填）
    - **conversation_text**: 对话内容（必填）
    - **auto_store**: 是否自动存储（默认 true）
    
    示例请求：
    ```json
    {
      "agent_id": "xxx-xxx-xxx",
      "session_id": "session_123",
      "conversation_text": "用户：我是憨货，喜欢吐槽风格\\nAI：好的，记住了"
    }
    ```
    """
    try:
        result = await auto_memory_service.auto_extract_and_store(request)
        return result
    
    except Exception as e:
        logger.error(f"自动提取失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )


@router.post(
    "/memories/extract-from-session",
    response_model=AutoExtractResponse,
    tags=[TAG_AUTO_MEMORY],
    summary="从会话历史提取记忆",
    responses={
        200: {"description": "提取完成"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def extract_from_session(
    agent_id: str,
    session_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="处理的对话数量")
):
    """
    从会话历史中提取记忆
    
    获取指定会话的历史对话，然后自动提取记忆。
    
    - **agent_id**: 智能体 UUID
    - **session_id**: 会话标识
    - **limit**: 处理的对话数量（1-50）
    """
    try:
        uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的智能体 ID 格式，需要 UUID 格式"
        )
    
    try:
        result = await auto_memory_service.extract_from_conversation(
            agent_id, session_id, limit
        )
        return result
    
    except Exception as e:
        logger.error(f"从会话提取失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )


# ============================================================
# 对话增强 API（核心功能）
# ============================================================

@router.post(
    "/chat",
    response_model=EnhancedReply,
    tags=[TAG_CHAT],
    summary="增强对话（推荐）",
    description="""
🚀 **核心功能**：基于记忆的智能对话

工作流程：
1. 检索相关记忆（向量搜索）
2. 获取对话历史
3. 用 LLM 生成增强回复
4. 记录对话
5. 自动提取新记忆

**特点**：
- 个性化回复：基于用户偏好和历史记忆
- 上下文感知：考虑多轮对话历史
- 自动学习：从对话中自动提取和存储新记忆
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
    - **session_id**: 会话标识（必填，用于关联多轮对话）
    - **user_message**: 用户消息（必填）
    - **use_memory**: 是否使用记忆增强（默认 true）
    - **use_history**: 是否使用对话历史（默认 true）
    - **auto_extract**: 是否自动提取记忆（默认 true）
    - **memory_count**: 检索记忆数量（默认 5）
    - **history_count**: 历史对话数量（默认 6）
    
    **返回值**：
    - **reply**: AI 增强回复
    - **conversation_id**: 对话记录 ID
    - **memories_used**: 使用的记忆数量
    - **history_used**: 使用的历史对话数量
    - **memory_sources**: 记忆来源详情
    - **extracted_memories**: 提取的新记忆
    - **stored_count**: 存储的新记忆数量
    
    **示例请求**：
    ```json
    {
      "agent_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "session_123",
      "user_message": "你好，我是憨货，喜欢吐槽风格"
    }
    ```
    
    **示例响应**：
    ```json
    {
      "reply": "嘿，憨货！记住啦，以后就用你喜欢的吐槽风格跟你聊~",
      "conversation_id": "660e8400-e29b-41d4-a716-446655440000",
      "memories_used": 2,
      "history_used": 0,
      "memory_sources": [
        {
          "id": "...",
          "content": "用户名叫憨货",
          "type": "fact",
          "similarity": 0.95
        }
      ],
      "extracted_memories": [
        {"content": "用户名叫憨货", "memory_type": "fact", "confidence": 0.9}
      ],
      "stored_count": 1
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


@router.post(
    "/chat/enhance",
    response_model=EnhancedReply,
    tags=[TAG_CHAT],
    summary="仅增强对话（不记录）",
    description="""
增强对话但不记录到数据库，适合预览效果。

与 `/chat` 的区别：
- 不记录对话
- 不自动提取记忆
- 仅返回增强回复
""",
    responses={
        200: {"description": "返回增强回复"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def enhance_only(request: EnhancedChatRequest):
    """
    仅增强对话（不记录）
    
    与 `/chat` 的区别：
    - 不记录对话到数据库
    - 不自动提取记忆
    - 仅返回增强回复
    
    适合场景：
    - 测试增强效果
    - 预览回复
    - 不需要记忆的临时对话
    """
    try:
        result = await dialogue_enhancement_service.enhance_dialogue(
            agent_id=str(request.agent_id),
            user_message=request.user_message,
            session_id=request.session_id if request.use_history else None,
            use_memory=request.use_memory,
            use_history=request.use_history,
            memory_count=request.memory_count
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