# ============================================================
# 多智能体记忆中枢 - 对话增强服务
# ============================================================
# 功能：整合记忆检索和 LLM 生成，增强 AI 回复
# 作者：小码
# 日期：2026-03-06
# ============================================================

import logging
from typing import List, Dict, Any, Optional
import uuid

from ..models.schemas import MemorySearchRequest, MemoryTextSearchRequest
from .memory_service import memory_service
from .embedding_service import embedding_service
from .llm_service import llm_service
from .conversation_service import conversation_service

logger = logging.getLogger(__name__)


class DialogueEnhancementService:
    """对话增强服务：基于记忆增强 AI 回复"""
    
    async def enhance_dialogue(
        self,
        agent_id: str,
        user_message: str,
        session_id: Optional[str] = None,
        use_memory: bool = True,
        use_history: bool = True,
        memory_count: int = 5,
        history_count: int = 6
    ) -> Dict[str, Any]:
        """
        增强对话：基于记忆和历史对话生成个性化回复
        
        Args:
            agent_id: 智能体 ID
            user_message: 用户消息
            session_id: 会话 ID（可选，用于获取对话历史）
            use_memory: 是否使用记忆增强
            use_history: 是否使用对话历史
            memory_count: 检索的记忆数量
            history_count: 检索的对话历史数量
        
        Returns:
            包含回复和相关信息的字典
        """
        # 验证 agent_id
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise ValueError(f"无效的智能体 ID 格式: {agent_id}")
        
        # 1. 检索相关记忆
        memories = []
        if use_memory:
            try:
                memories = await self._retrieve_memories(agent_id, user_message, memory_count)
                logger.info(f"检索到 {len(memories)} 条相关记忆")
            except Exception as e:
                logger.warning(f"记忆检索失败: {e}")
                # 记忆检索失败不阻止对话
        
        # 2. 获取对话历史
        conversation_history = []
        if use_history and session_id:
            try:
                conversation_history = await self._get_conversation_history(
                    agent_id, session_id, history_count
                )
                logger.info(f"获取到 {len(conversation_history)} 条对话历史")
            except Exception as e:
                logger.warning(f"获取对话历史失败: {e}")
        
        # 3. 生成增强回复
        try:
            enhanced_reply = await llm_service.generate_enhanced_reply(
                user_message=user_message,
                memories=memories,
                conversation_history=conversation_history
            )
        except Exception as e:
            logger.error(f"生成增强回复失败: {e}")
            # 降级：返回基础回复
            enhanced_reply = f"抱歉，我现在无法访问记忆库。关于「{user_message}」，我能为你做些什么？"
        
        # 4. 构建结果
        result = {
            "reply": enhanced_reply,
            "memories_used": len(memories),
            "history_used": len(conversation_history),
            "memory_sources": [
                {
                    "id": str(m.get("id", "")),
                    "content": m.get("content", ""),
                    "type": m.get("memory_type", "unknown"),
                    "similarity": m.get("similarity", 0)
                }
                for m in memories
            ]
        }
        
        return result
    
    async def _retrieve_memories(
        self,
        agent_id: str,
        query: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """
        检索相关记忆
        
        Args:
            agent_id: 智能体 ID
            query: 查询文本
            count: 返回数量
        
        Returns:
            记忆列表
        """
        # 使用文本搜索
        search_request = MemoryTextSearchRequest(
            query=query,
            agent_id=uuid.UUID(agent_id),
            match_threshold=0.5,
            match_count=count
        )
        
        results = await memory_service.search_by_text(search_request)
        
        # 转换为字典列表
        memories = []
        for r in results:
            memories.append({
                "id": r.id,
                "content": r.content,
                "memory_type": r.memory_type,
                "similarity": r.similarity,
                "importance": r.importance
            })
        
        return memories
    
    async def _get_conversation_history(
        self,
        agent_id: str,
        session_id: str,
        count: int
    ) -> List[Dict[str, str]]:
        """
        获取对话历史
        
        Args:
            agent_id: 智能体 ID
            session_id: 会话 ID
            count: 返回数量
        
        Returns:
            对话历史列表
        """
        conversations = await conversation_service.list_conversations_by_session(
            agent_id, session_id, count
        )
        
        # 转换为对话历史格式
        history = []
        for conv in conversations:
            history.append({"role": "user", "content": conv.get("user_message", "")})
            history.append({"role": "assistant", "content": conv.get("ai_response", "")})
        
        return history
    
    async def chat_and_remember(
        self,
        agent_id: str,
        session_id: str,
        user_message: str,
        auto_extract: bool = True
    ) -> Dict[str, Any]:
        """
        对话并自动记忆（一站式接口）
        
        工作流程：
        1. 检索相关记忆
        2. 获取对话历史
        3. 生成增强回复
        4. 记录对话
        5. 提取新记忆（可选）
        
        Args:
            agent_id: 智能体 ID
            session_id: 会话 ID
            user_message: 用户消息
            auto_extract: 是否自动提取记忆
        
        Returns:
            包含回复和相关信息的字典
        """
        # 1. 增强对话
        result = await self.enhance_dialogue(
            agent_id=agent_id,
            user_message=user_message,
            session_id=session_id,
            use_memory=True,
            use_history=True
        )
        
        # 2. 记录对话
        try:
            from ..models.conversation import ConversationCreate
            
            conversation = ConversationCreate(
                agent_id=uuid.UUID(agent_id),
                session_id=session_id,
                user_message=user_message,
                ai_response=result["reply"],
                metadata={
                    "memories_used": result["memories_used"],
                    "history_used": result["history_used"]
                }
            )
            
            conversation_id = await conversation_service.create_conversation(conversation)
            result["conversation_id"] = conversation_id
            
            logger.info(f"对话已记录: {conversation_id}")
            
        except Exception as e:
            logger.error(f"记录对话失败: {e}")
            result["conversation_id"] = None
        
        # 3. 自动提取记忆
        if auto_extract:
            try:
                from .auto_memory_service import auto_memory_service
                from ..models.conversation import AutoExtractRequest
                
                extract_request = AutoExtractRequest(
                    agent_id=uuid.UUID(agent_id),
                    session_id=session_id,
                    conversation_text=f"用户：{user_message}\nAI：{result['reply']}",
                    auto_store=True
                )
                
                extract_result = await auto_memory_service.auto_extract_and_store(extract_request)
                result["extracted_memories"] = extract_result.extracted_memories
                result["stored_count"] = extract_result.stored_count
                
                logger.info(f"提取了 {extract_result.stored_count} 条新记忆")
                
            except Exception as e:
                logger.warning(f"自动提取记忆失败: {e}")
                result["extracted_memories"] = []
                result["stored_count"] = 0
        
        return result


# 全局服务实例
dialogue_enhancement_service = DialogueEnhancementService()