# ============================================================
# Memory Hub - 记忆路由服务
# ============================================================
# 功能：根据记忆类型和可见性路由到正确的表
# 作者：小码
# 日期：2026-03-09
# ============================================================

import logging
from typing import Optional, Tuple
from uuid import UUID

from .memory_classifier import memory_classifier, MemoryVisibility

logger = logging.getLogger(__name__)

class MemoryRouter:
    """记忆路由器：决定记忆存储到哪个表"""
    
    async def route(
        self,
        content: str,
        agent_id: UUID,
        memory_type: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        路由记忆到合适的表
        
        Args:
            content: 记忆内容
            agent_id: 智能体 ID
            memory_type: 记忆类型
            agent_name: 智能体名称
        
        Returns:
            (table_name, visibility, reason)
            table_name: "private" 或 "shared"
            visibility: "private" 或 "shared"
            reason: 路由理由
        """
        # 1. 调用分类器
        visibility, confidence, reason = memory_classifier.classify(
            content=content,
            agent_name=agent_name,
            memory_type=memory_type
        )
        
        # 2. 路由决策
        if visibility == MemoryVisibility.PRIVATE:
            logger.info(f"路由到私人记忆表：{content[:50]}... (置信度：{confidence:.2f})")
            return "private", "private", reason
        else:
            logger.info(f"路由到共同记忆表：{content[:50]}... (置信度：{confidence:.2f})")
            return "shared", "shared", reason
    
    async def save(
        self,
        db,
        content: str,
        agent_id: UUID,
        memory_type: Optional[str] = None,
        agent_name: Optional[str] = None,
        embedding: Optional[list] = None,
        tags: Optional[list] = None,
        metadata: Optional[dict] = None
    ) -> Tuple[UUID, str, str]:
        """
        保存记忆到合适的表
        
        Args:
            db: 数据库连接
            content: 记忆内容
            agent_id: 智能体 ID
            memory_type: 记忆类型
            agent_name: 智能体名称
            embedding: 向量嵌入
            tags: 标签列表
            metadata: 元数据
        
        Returns:
            (memory_id, table_name, visibility)
        """
        # 1. 路由决策
        table_name, visibility, reason = await self.route(
            content, agent_id, memory_type, agent_name
        )
        
        # 2. 保存到对应的表
        if table_name == "private":
            memory_id = await self._save_private(
                db, agent_id, content, memory_type, embedding, tags, metadata
            )
        else:
            memory_id = await self._save_shared(
                db, agent_id, content, memory_type, embedding, tags, metadata
            )
        
        logger.info(f"记忆已保存：{memory_id}, 表：{table_name}, 可见性：{visibility}")
        
        return memory_id, table_name, visibility
    
    async def _save_private(
        self,
        db,
        agent_id: UUID,
        content: str,
        memory_type: str,
        embedding: list,
        tags: list,
        metadata: dict
    ) -> UUID:
        """保存到私人记忆表"""
        query = """
            INSERT INTO private_memories 
            (agent_id, content, memory_type, embedding, tags, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        
        memory_id = await db.fetchval(
            query,
            agent_id,
            content,
            memory_type,
            f"[{','.join(map(str, embedding))}]",
            tags or [],
            metadata or {}
        )
        
        return memory_id
    
    async def _save_shared(
        self,
        db,
        created_by: UUID,
        content: str,
        memory_type: str,
        embedding: list,
        tags: list,
        metadata: dict
    ) -> UUID:
        """保存到共同记忆表"""
        query = """
            INSERT INTO shared_memories 
            (created_by, content, memory_type, embedding, tags, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        
        memory_id = await db.fetchval(
            query,
            created_by,
            content,
            memory_type,
            f"[{','.join(map(str, embedding))}]",
            tags or [],
            metadata or {}
        )
        
        return memory_id


# 全局实例
memory_router = MemoryRouter()