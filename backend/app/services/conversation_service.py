# ============================================================
# 多智能体记忆中枢 - 对话记录服务
# ============================================================
# 功能：记录和管理用户与AI的对话历史
# 作者：小码
# 日期：2026-03-06
# ============================================================

import json
import logging
from typing import Optional, List
from datetime import datetime
import uuid

from ..database import db
from ..models.conversation import (
    ConversationCreate,
    Conversation,
    ConversationList
)

logger = logging.getLogger(__name__)


class ConversationService:
    """对话记录服务：管理对话历史"""
    
    async def create_conversation(self, conversation: ConversationCreate) -> str:
        """
        创建对话记录
        
        Args:
            conversation: 对话创建请求
        
        Returns:
            创建的对话 ID
        
        Raises:
            ValueError: 智能体不存在
        """
        # 检查智能体是否存在
        agent_exists = await db.fetchval(
            "SELECT EXISTS(SELECT 1 FROM agents WHERE id = $1)",
            conversation.agent_id
        )
        
        if not agent_exists:
            raise ValueError(f"智能体不存在: {conversation.agent_id}")
        
        query = """
            INSERT INTO conversations 
            (agent_id, session_id, user_message, ai_response, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        
        conversation_id = await db.fetchval(
            query,
            conversation.agent_id,
            conversation.session_id,
            conversation.user_message,
            conversation.ai_response,
            json.dumps(conversation.metadata)
        )
        
        logger.info(
            f"对话记录已创建: agent_id={conversation.agent_id}, "
            f"session_id={conversation.session_id}, id={conversation_id}"
        )
        
        return str(conversation_id)
    
    async def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """
        获取单条对话记录
        
        Args:
            conversation_id: 对话 ID
        
        Returns:
            对话详情或 None
        """
        try:
            query = """
                SELECT id, agent_id, session_id, user_message, ai_response, 
                       created_at, metadata
                FROM conversations
                WHERE id = $1
            """
            
            row = await db.fetchrow(query, uuid.UUID(conversation_id))
            
            if row:
                return dict(row)
            return None
            
        except ValueError:
            logger.warning(f"无效的对话 ID 格式: {conversation_id}")
            return None
    
    async def list_conversations_by_agent(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        列出智能体的所有对话
        
        Args:
            agent_id: 智能体 ID
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            对话列表
        """
        try:
            query = """
                SELECT id, agent_id, session_id, user_message, ai_response, 
                       created_at, metadata
                FROM conversations
                WHERE agent_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            
            rows = await db.fetch(query, uuid.UUID(agent_id), limit, offset)
            return [dict(row) for row in rows]
            
        except ValueError:
            logger.warning(f"无效的智能体 ID 格式: {agent_id}")
            return []
    
    async def list_conversations_by_session(
        self,
        agent_id: str,
        session_id: str,
        limit: int = 100
    ) -> List[dict]:
        """
        列出会话的所有对话
        
        Args:
            agent_id: 智能体 ID
            session_id: 会话 ID
            limit: 返回数量限制
        
        Returns:
            对话列表（按时间正序）
        """
        try:
            query = """
                SELECT id, agent_id, session_id, user_message, ai_response, 
                       created_at, metadata
                FROM conversations
                WHERE agent_id = $1 AND session_id = $2
                ORDER BY created_at ASC
                LIMIT $3
            """
            
            rows = await db.fetch(query, uuid.UUID(agent_id), session_id, limit)
            return [dict(row) for row in rows]
            
        except ValueError:
            logger.warning(f"无效的智能体 ID 格式: {agent_id}")
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话记录
        
        Args:
            conversation_id: 对话 ID
        
        Returns:
            是否删除成功
        """
        try:
            query = "DELETE FROM conversations WHERE id = $1"
            result = await db.execute(query, uuid.UUID(conversation_id))
            return result == "DELETE 1"
            
        except ValueError:
            logger.warning(f"无效的对话 ID 格式: {conversation_id}")
            return False
    
    async def delete_conversations_by_session(
        self,
        agent_id: str,
        session_id: str
    ) -> int:
        """
        删除会话的所有对话
        
        Args:
            agent_id: 智能体 ID
            session_id: 会话 ID
        
        Returns:
            删除的对话数量
        """
        try:
            query = """
                DELETE FROM conversations 
                WHERE agent_id = $1 AND session_id = $2
            """
            result = await db.execute(query, uuid.UUID(agent_id), session_id)
            
            # 解析 DELETE N 格式
            if result.startswith("DELETE "):
                count = int(result.split()[1])
                logger.info(f"已删除 {count} 条对话: agent_id={agent_id}, session_id={session_id}")
                return count
            return 0
            
        except ValueError:
            logger.warning(f"无效的智能体 ID 格式: {agent_id}")
            return 0
    
    async def get_recent_conversations(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[dict]:
        """
        获取智能体最近的对话
        
        Args:
            agent_id: 智能体 ID
            limit: 返回数量
        
        Returns:
            对话列表（按时间倒序）
        """
        try:
            query = """
                SELECT id, agent_id, session_id, user_message, ai_response, 
                       created_at, metadata
                FROM conversations
                WHERE agent_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            
            rows = await db.fetch(query, uuid.UUID(agent_id), limit)
            return [dict(row) for row in rows]
            
        except ValueError:
            logger.warning(f"无效的智能体 ID 格式: {agent_id}")
            return []


# 全局服务实例
conversation_service = ConversationService()