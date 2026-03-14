# ============================================================
# 多智能体记忆中枢 - 记忆服务（双表架构）
# ============================================================
# 功能：记忆的增删改查和向量搜索，支持 private/shared 双表
# 作者：小码
# 日期：2026-03-09
# ============================================================

import json
import logging
from typing import List, Optional, Tuple
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
    """记忆服务：处理记忆的存储和检索（双表架构）"""
    
    async def route_memory(self, content: str) -> str:
        """
        根据内容自动路由记忆到合适的表
        
        Args:
            content: 记忆内容
        
        Returns:
            'private' 或 'shared'
        """
        # 使用数据库路由函数
        result = await db.fetchval("SELECT route_memory($1)", content)
        return result or 'private'
    
    async def create_memory(self, memory: MemoryCreate) -> Tuple[str, str, str, bool]:
        """
        创建新记忆（双表架构）
        
        Args:
            memory: 记忆创建请求
        
        Returns:
            (memory_id, table_name, visibility, auto_routed)
        """
        # 确定目标表和可见性
        auto_routed = False
        if memory.auto_route:
            # 自动路由
            visibility = await self.route_memory(memory.content)
            auto_routed = True
        else:
            # 手动指定
            visibility = memory.visibility or 'private'
        
        table_name = f"{visibility}_memories"
        
        # 生成 embedding
        embedding_str = None
        if memory.embedding:
            embedding_str = f"[{','.join(map(str, memory.embedding))}]"
        else:
            try:
                embedding = await embedding_service.get_embedding(memory.content)
                embedding_str = f"[{','.join(map(str, embedding))}]"
                logger.info(f"成功生成 embedding，维度：{len(embedding)}")
            except Exception as e:
                logger.error(f"生成 embedding 失败：{e}")
                raise ValueError(f"生成向量失败：{str(e)}")
        
        # 根据表类型构建不同的插入语句
        if visibility == 'private':
            query = """
                INSERT INTO private_memories 
                (agent_id, content, embedding, memory_type, importance, tags, metadata, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """
            params = [
                memory.agent_id,
                memory.content,
                embedding_str,
                memory.memory_type.value,
                memory.importance,
                memory.tags,
                json.dumps(memory.metadata),
                memory.expires_at
            ]
        else:  # shared
            query = """
                INSERT INTO shared_memories 
                (agent_id, content, embedding, memory_type, importance, tags, metadata, expires_at, visibility, allowed_agents)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """
            params = [
                memory.agent_id,
                memory.content,
                embedding_str,
                memory.memory_type.value,
                memory.importance,
                memory.tags,
                json.dumps(memory.metadata),
                memory.expires_at,
                'team',  # visibility
                []      # allowed_agents (empty = all team members)
            ]
        
        memory_id = await db.fetchval(query, *params)
        
        return str(memory_id), visibility, visibility, auto_routed
    
    async def get_memory(self, memory_id: str, visibility: str = 'private') -> Optional[dict]:
        """
        获取单条记忆
        
        Args:
            memory_id: 记忆 ID
            visibility: 表类型 (private/shared)
        
        Returns:
            记忆详情或 None
        """
        table_name = f"{visibility}_memories"
        
        query = f"""
            UPDATE {table_name}
            SET access_count = access_count + 1, 
                last_accessed = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING id, agent_id, content, memory_type, importance, 
                      access_count, tags, metadata, created_at, last_accessed, expires_at,
                      CASE WHEN $2 = 'shared' THEN 'shared' ELSE 'private' END as visibility
        """
        
        try:
            row = await db.fetchrow(query, uuid.UUID(memory_id), visibility)
        except ValueError:
            return None
        
        if row:
            return dict(row)
        return None
    
    async def search_similar(self, request: MemorySearchRequest) -> List[MemorySearchResult]:
        """
        向量相似性搜索（旧版：需要 query_embedding）
        """
        embedding_str = f"[{','.join(map(str, request.query_embedding))}]"
        
        query = f"""
            SELECT * FROM search_similar_memories(
                $1::vector({settings.EMBEDDING_DIMENSION}),
                $2::uuid,
                $3::float,
                $4::integer
            )
        """
        
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
        文本相似性搜索（支持 visibility 过滤）
        """
        # 生成向量
        embedding = await embedding_service.get_embedding(request.query)
        
        # 构造向量搜索请求
        vector_request = MemorySearchRequest(
            query_embedding=embedding,
            agent_id=request.agent_id,
            match_threshold=request.match_threshold,
            match_count=request.match_count
        )
        
        return await self.search_similar(vector_request)
    
    async def search_private(self, agent_id: str, query: str, limit: int = 10) -> List[dict]:
        """
        搜索私人记忆（仅当前智能体）
        """
        embedding = await embedding_service.get_embedding(query)
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        query_sql = """
            SELECT * FROM search_private_memories(
                $1::vector(1024),
                $2::uuid,
                0.5,
                $3
            )
        """
        
        rows = await db.fetch(query_sql, embedding_str, uuid.UUID(agent_id), limit)
        return [dict(row) for row in rows]
    
    async def search_shared(self, agent_id: str, query: str, limit: int = 10) -> List[dict]:
        """
        搜索共同记忆（团队共享）
        """
        embedding = await embedding_service.get_embedding(query)
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        query_sql = """
            SELECT * FROM search_shared_memories(
                $1::vector(1024),
                $2::uuid,
                0.5,
                $3
            )
        """
        
        rows = await db.fetch(query_sql, embedding_str, uuid.UUID(agent_id), limit)
        return [dict(row) for row in rows]
    
    async def delete_memory(self, memory_id: str, visibility: str = 'private') -> bool:
        """
        删除记忆
        """
        table_name = f"{visibility}_memories"
        
        try:
            query = f"DELETE FROM {table_name} WHERE id = $1"
            result = await db.execute(query, uuid.UUID(memory_id))
            return result == "DELETE 1"
        except ValueError:
            return False
    
    async def list_memories_by_agent(
        self, 
        agent_id: str,
        visibility: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        列出智能体的记忆
        
        Args:
            agent_id: 智能体 ID
            visibility: 过滤类型 (private/shared/None=全部)
            limit: 返回数量限制
            offset: 偏移量
        """
        results = []
        
        if visibility == 'private' or visibility is None:
            query = """
                SELECT id, agent_id, content, memory_type, importance, 
                       access_count, tags, created_at, last_accessed,
                       'private' as visibility
                FROM private_memories
                WHERE agent_id = $1
                ORDER BY importance DESC, created_at DESC
                LIMIT $2 OFFSET $3
            """
            rows = await db.fetch(query, uuid.UUID(agent_id), limit, offset)
            results.extend([dict(row) for row in rows])
        
        if visibility == 'shared' or visibility is None:
            query = """
                SELECT id, agent_id, content, memory_type, importance, 
                       access_count, tags, created_at, last_accessed,
                       'shared' as visibility
                FROM shared_memories
                WHERE agent_id = $1
                ORDER BY importance DESC, created_at DESC
                LIMIT $2 OFFSET $3
            """
            rows = await db.fetch(query, uuid.UUID(agent_id), limit, offset)
            results.extend([dict(row) for row in rows])
        
        return results
    
    async def cleanup_old_memories(
        self,
        days_old: int = 30,
        min_importance: float = 0.3,
        max_access_count: int = 3
    ) -> int:
        """
        清理过期记忆（双表）
        """
        deleted = 0
        
        # 清理私人记忆
        query_private = """
            DELETE FROM private_memories
            WHERE 
                created_at < CURRENT_TIMESTAMP - ($1 || ' days')::interval
                AND importance < $2
                AND access_count < $3
        """
        result = await db.execute(query_private, days_old, min_importance, max_access_count)
        deleted += int(result.split()[-1]) if result != "DELETE 0" else 0
        
        # 清理共同记忆
        query_shared = """
            DELETE FROM shared_memories
            WHERE 
                created_at < CURRENT_TIMESTAMP - ($1 || ' days')::interval
                AND importance < $2
                AND access_count < $3
        """
        result = await db.execute(query_shared, days_old, min_importance, max_access_count)
        deleted += int(result.split()[-1]) if result != "DELETE 0" else 0
        
        return deleted


# 全局服务实例
memory_service = MemoryService()
