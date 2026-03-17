# ============================================================
# 多智能体记忆中枢 - 自动记忆服务
# ============================================================
# 功能：自动从对话中提取和存储记忆
# 作者：小码
# 日期：2026-03-06
# ============================================================

import json
import logging
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import db
from ..models.conversation import (
    AutoExtractRequest,
    AutoExtractResponse,
    ExtractedMemory,
    ConversationCreate
)
from ..models.schemas import MemoryCreate, MemoryType
from .memory_extractor import memory_extractor
from .embedding_service import embedding_service
from .conversation_service import conversation_service
from ..config import settings

logger = logging.getLogger(__name__)


class AutoMemoryService:
    """自动记忆服务：自动提取和存储记忆"""
    
    # 记忆类型映射
    MEMORY_TYPE_MAP = {
        "fact": MemoryType.FACT,
        "relationship": MemoryType.FACT,  # 关系作为事实存储
        "event": MemoryType.EXPERIENCE,   # 事件作为经验存储
        "emotion": MemoryType.FACT        # 情感作为事实存储
    }
    
    # 重要性权重
    IMPORTANCE_WEIGHTS = {
        "fact": 0.7,
        "relationship": 0.8,
        "event": 0.9,
        "emotion": 0.5
    }
    
    async def auto_extract_and_store(
        self,
        request: AutoExtractRequest
    ) -> AutoExtractResponse:
        """
        自动提取并存储记忆
        
        工作流程：
        1. 先记录对话
        2. 调用 LLM 提取关键信息
        3. 去重
        4. 存储到数据库
        
        Args:
            request: 自动提取请求
        
        Returns:
            提取和存储结果
        """
        try:
            # 步骤 1：记录对话（如果提供了对话内容）
            # 注意：这里假设 conversation_text 格式为 "用户：xxx\nAI：xxx"
            conversation_id = None
            if "\n" in request.conversation_text:
                parts = request.conversation_text.split("\n", 1)
                user_msg = parts[0].replace("用户：", "").replace("User: ", "").strip()
                ai_msg = parts[1].replace("AI：", "").replace("AI: ", "").strip() if len(parts) > 1 else ""
                
                if user_msg and ai_msg:
                    conversation = await conversation_service.create_conversation(
                        ConversationCreate(
                            agent_id=request.agent_id,
                            session_id=request.session_id,
                            user_message=user_msg,
                            ai_response=ai_msg,
                            metadata={}
                        )
                    )
                    conversation_id = conversation
                    logger.info(f"对话已记录: id={conversation_id}")
            
            # 步骤 2：调用 LLM 提取关键信息
            extraction_result = await memory_extractor.extract_memories(
                request.conversation_text
            )
            
            # 转换为记忆列表
            memories = extraction_result.to_memories()
            
            if not memories:
                return AutoExtractResponse(
                    extracted_memories=[],
                    stored_count=0,
                    message="未提取到有效记忆"
                )
            
            # 步骤 3：去重
            unique_memories = await self._deduplicate_memories(
                request.agent_id,
                memories
            )
            
            # 步骤 4：存储到数据库
            stored_count = 0
            if request.auto_store:
                stored_count = await self._store_memories(
                    request.agent_id,
                    unique_memories
                )
            
            return AutoExtractResponse(
                extracted_memories=unique_memories,
                stored_count=stored_count,
                message=f"成功提取 {len(memories)} 条记忆，去重后 {len(unique_memories)} 条，存储 {stored_count} 条"
            )
            
        except Exception as e:
            logger.error(f"自动提取失败: {e}")
            return AutoExtractResponse(
                extracted_memories=[],
                stored_count=0,
                message=f"处理失败: {str(e)}"
            )
    
    async def _deduplicate_memories(
        self,
        agent_id: uuid.UUID,
        memories: List[ExtractedMemory]
    ) -> List[ExtractedMemory]:
        """
        去重：检查记忆是否已存在
        
        使用向量相似度搜索检查相似记忆
        
        Args:
            agent_id: 智能体 ID
            memories: 待去重的记忆列表
        
        Returns:
            去重后的记忆列表
        """
        unique_memories = []
        
        for memory in memories:
            # 使用向量搜索检查相似记忆
            try:
                # 生成向量
                embedding = await embedding_service.get_embedding(memory.content)
                
                # 搜索相似记忆
                similar = await db.fetch(
                    f"""
                    SELECT id, content 
                    FROM search_similar_memories($1::vector({settings.EMBEDDING_DIMENSION}), $2::uuid, 0.85::float, 3::integer)
                    """,
                    f"[{','.join(map(str, embedding))}]",
                    agent_id
                )
                
                # 如果没有相似度 > 0.85 的记忆，则认为是新的
                if not similar:
                    unique_memories.append(memory)
                else:
                    logger.info(f"跳过重复记忆: {memory.content[:50]}...")
                    
            except Exception as e:
                logger.warning(f"去重检查失败，保留该记忆: {e}")
                unique_memories.append(memory)
        
        return unique_memories
    
    async def _store_memories(
        self,
        agent_id: uuid.UUID,
        memories: List[ExtractedMemory]
    ) -> int:
        """
        存储记忆到数据库
        
        Args:
            agent_id: 智能体 ID
            memories: 记忆列表
        
        Returns:
            成功存储的数量
        """
        stored_count = 0
        
        # 按重要性排序（事件 > 关系 > 事实 > 情感）
        sorted_memories = sorted(
            memories,
            key=lambda m: self.IMPORTANCE_WEIGHTS.get(m.memory_type, 0.5),
            reverse=True
        )
        
        for memory in sorted_memories:
            try:
                # 生成向量
                embedding = await embedding_service.get_embedding(memory.content)
                
                # 确定记忆类型
                memory_type = self.MEMORY_TYPE_MAP.get(
                    memory.memory_type, 
                    MemoryType.FACT
                )
                
                # 计算重要性
                importance = self.IMPORTANCE_WEIGHTS.get(
                    memory.memory_type, 
                    0.5
                ) * memory.confidence
                
                # 创建记忆
                memory_create = MemoryCreate(
                    agent_id=agent_id,
                    content=memory.content,
                    memory_type=memory_type,
                    importance=min(importance, 1.0),
                    embedding=embedding,
                    tags=[memory.memory_type],
                    metadata={"source": "auto_extract"}
                )
                
                # 存储到数据库
                query = """
                    INSERT INTO memories 
                    (agent_id, content, embedding, memory_type, importance, tags, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """
                
                memory_id = await db.fetchval(
                    query,
                    agent_id,
                    memory.content,
                    f"[{','.join(map(str, embedding))}]",
                    memory_type.value,
                    min(importance, 1.0),
                    [memory.memory_type],
                    json.dumps({"source": "auto_extract"})
                )
                
                stored_count += 1
                logger.info(f"记忆已存储: id={memory_id}, type={memory.memory_type}")
                
            except Exception as e:
                logger.error(f"存储记忆失败: {memory.content[:50]}, error={e}")
        
        return stored_count
    
    async def extract_from_conversation(
        self,
        agent_id: str,
        session_id: str,
        limit: int = 10
    ) -> AutoExtractResponse:
        """
        从历史对话中提取记忆
        
        Args:
            agent_id: 智能体 ID
            session_id: 会话 ID
            limit: 处理的对话数量
        
        Returns:
            提取结果
        """
        try:
            # 获取对话历史
            conversations = await conversation_service.list_conversations_by_session(
                agent_id,
                session_id,
                limit
            )
            
            if not conversations:
                return AutoExtractResponse(
                    extracted_memories=[],
                    stored_count=0,
                    message="没有找到对话记录"
                )
            
            # 合并对话内容
            conversation_text = "\n\n".join([
                f"用户：{conv['user_message']}\nAI：{conv['ai_response']}"
                for conv in conversations
            ])
            
            # 提取记忆
            return await self.auto_extract_and_store(
                AutoExtractRequest(
                    agent_id=uuid.UUID(agent_id),
                    session_id=session_id,
                    conversation_text=conversation_text,
                    auto_store=True
                )
            )
            
        except Exception as e:
            logger.error(f"从对话提取失败: {e}")
            return AutoExtractResponse(
                extracted_memories=[],
                stored_count=0,
                message=f"处理失败: {str(e)}"
            )


# 全局服务实例
auto_memory_service = AutoMemoryService()