# ============================================================
# 多智能体记忆中枢 - 记忆服务
# ============================================================
# 功能：记忆的增删改查和向量搜索
# 作者：小码
# 日期：2026-03-05
# ============================================================

import json
import logging
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import db
from ..models.schemas import (
    MemoryCreate,
    MemoryUpdate,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryTextSearchRequest
)
from .embedding_service import embedding_service
from ..config import settings

logger = logging.getLogger(__name__)


class MemoryService:
    """记忆服务：处理记忆的存储和检索"""
    
    async def create_memory(self, memory: MemoryCreate) -> str:
        """
        创建新记忆
        
        Args:
            memory: 记忆创建请求
        
        Returns:
            创建的记忆 ID
        """
        query = """
            INSERT INTO memories 
            (agent_id, content, embedding, memory_type, importance, tags, metadata, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        
        # 处理 embedding：如果用户未提供，自动生成
        embedding_str = None
        if memory.embedding:
            # 使用用户提供的 embedding
            embedding_str = f"[{','.join(map(str, memory.embedding))}]"
        else:
            # 自动调用 embedding_service 生成向量
            try:
                embedding = await embedding_service.get_embedding(memory.content)
                embedding_str = f"[{','.join(map(str, embedding))}]"
                logger.info(f"成功生成 embedding，维度：{len(embedding)}")
            except Exception as e:
                logger.error(f"生成 embedding 失败：{e}")
                raise ValueError(f"生成向量失败：{str(e)}")
        
        memory_id = await db.fetchval(
            query,
            memory.agent_id,
            memory.content,
            embedding_str,
            memory.memory_type.value,
            memory.importance,
            memory.tags,
            json.dumps(memory.metadata),
            memory.expires_at
        )
        
        return str(memory_id)
    
    async def get_memory(self, memory_id: str) -> Optional[dict]:
        """
        获取单条记忆
        
        Args:
            memory_id: 记忆 ID
        
        Returns:
            记忆详情或 None
        """
        query = """
            UPDATE memories 
            SET access_count = access_count + 1, 
                last_accessed = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING id, agent_id, content, memory_type, importance, 
                      access_count, tags, metadata, created_at, last_accessed, expires_at
        """
        
        try:
            row = await db.fetchrow(query, uuid.UUID(memory_id))
        except ValueError:
            return None
        
        if row:
            return dict(row)
        return None
    
    async def update_memory(self, memory_id: str, memory: MemoryUpdate) -> Optional[dict]:
        """
        更新记忆
        
        Args:
            memory_id: 记忆 ID
            memory: 更新请求
        
        Returns:
            更新后的记忆或 None
        """
        # 首先检查记忆是否存在
        existing = await self.get_memory(memory_id)
        if not existing:
            return None
        
        # 构建动态更新语句
        updates = []
        params = [uuid.UUID(memory_id)]
        param_idx = 2
        
        if memory.content is not None:
            updates.append(f"content = ${param_idx}")
            params.append(memory.content)
            param_idx += 1
        
        if memory.memory_type is not None:
            updates.append(f"memory_type = ${param_idx}")
            params.append(memory.memory_type.value)
            param_idx += 1
        
        if memory.importance is not None:
            updates.append(f"importance = ${param_idx}")
            params.append(memory.importance)
            param_idx += 1
        
        if memory.tags is not None:
            updates.append(f"tags = ${param_idx}")
            params.append(memory.tags)
            param_idx += 1
        
        if memory.metadata is not None:
            updates.append(f"metadata = ${param_idx}")
            params.append(json.dumps(memory.metadata))
            param_idx += 1
        
        if memory.embedding is not None:
            updates.append(f"embedding = ${param_idx}")
            params.append(f"[{','.join(map(str, memory.embedding))}]")
            param_idx += 1
        
        if memory.expires_at is not None:
            updates.append(f"expires_at = ${param_idx}")
            params.append(memory.expires_at)
            param_idx += 1
        
        if not updates:
            return existing
        
        query = f"""
            UPDATE memories 
            SET {', '.join(updates)}
            WHERE id = $1
            RETURNING id, agent_id, content, memory_type, importance, 
                      access_count, tags, metadata, created_at, last_accessed, expires_at
        """
        
        row = await db.fetchrow(query, *params)
        return dict(row) if row else None
    
    async def search_similar(self, request: MemorySearchRequest) -> List[MemorySearchResult]:
        """
        向量相似性搜索（旧版：需要 query_embedding）
        
        Args:
            request: 搜索请求
        
        Returns:
            相似记忆列表
        """
        # 调用数据库函数进行向量搜索（使用配置的维度）
        query = f"""
            SELECT * FROM search_similar_memories(
                $1::vector({settings.EMBEDDING_DIMENSION}),
                $2::uuid,
                $3::float,
                $4::integer
            )
        """
        
        # 格式化 embedding
        embedding_str = f"[{','.join(map(str, request.query_embedding))}]"
        
        rows = await db.fetch(
            query,
            embedding_str,
            request.agent_id,
            request.match_threshold,
            request.match_count
        )
        
        return [MemorySearchResult(**dict(row)) for row in rows]
    
    async def search_by_text(self, request: MemoryTextSearchRequest) -> List[MemorySearchResult]:
        """
        文本相似性搜索（新版：接受 query 文本）
        
        在服务器端调用 embedding_service 生成向量，然后执行搜索
        
        Args:
            request: 文本搜索请求
        
        Returns:
            相似记忆列表
        """
        # 调用 embedding_service 生成向量
        embedding = await embedding_service.get_embedding(request.query)
        
        # 构造向量搜索请求并调用原有方法
        vector_request = MemorySearchRequest(
            query_embedding=embedding,
            agent_id=request.agent_id,
            match_threshold=request.match_threshold,
            match_count=request.match_count
        )
        
        return await self.search_similar(vector_request)
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆 ID
        
        Returns:
            是否删除成功
        """
        try:
            query = "DELETE FROM memories WHERE id = $1"
            result = await db.execute(query, uuid.UUID(memory_id))
            return result == "DELETE 1"
        except ValueError:
            return False
    
    async def list_memories_by_agent(
        self, 
        agent_id: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        列出智能体的所有记忆
        
        Args:
            agent_id: 智能体 ID
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            记忆列表
        """
        try:
            query = """
                SELECT id, agent_id, content, memory_type, importance, 
                       access_count, tags, created_at, last_accessed
                FROM memories
                WHERE agent_id = $1
                ORDER BY importance DESC, created_at DESC
                LIMIT $2 OFFSET $3
            """
            
            rows = await db.fetch(query, uuid.UUID(agent_id), limit, offset)
            return [dict(row) for row in rows]
        except ValueError:
            return []
    
    async def cleanup_old_memories(
        self,
        days_old: int = 30,
        min_importance: float = 0.3,
        max_access_count: int = 3
    ) -> int:
        """
        清理过期记忆
        
        Args:
            days_old: 保留天数
            min_importance: 最小重要性阈值
            max_access_count: 最大访问次数阈值
        
        Returns:
            删除的记忆数量
        """
        query = """
            SELECT cleanup_old_memories($1, $2, $3)
        """
        return await db.fetchval(query, days_old, min_importance, max_access_count)


# 全局服务实例
memory_service = MemoryService()