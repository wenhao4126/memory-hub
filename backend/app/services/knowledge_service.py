# ============================================================
# 多智能体记忆中枢 - 知识库服务
# ============================================================
# 功能：知识/文档的存储、检索和向量搜索
# 作者：小码 🟡
# 日期：2026-03-16
#
# ⚠️ 架构说明（憨货决策）：
#   - knowledge 表：存储文档内容/地址
#   - shared_memories 表：存储引用（knowledge_id）
#   - 优势：结构清晰、知识独立管理、支持向量搜索、记忆表轻量
#
# 使用场景：
#   1. 小搜找到文档 → 存入 knowledge 表 → shared_memories 存引用
#   2. 查询文档 → 先查 shared_memories → 再查 knowledge 表
# ============================================================

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..database import db
from ..services.embedding_service import embedding_service
from ..config import settings

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    知识库服务 - 管理文档/知识的存储和检索
    
    功能：
        - create(): 创建知识记录，返回 knowledge_id
        - get(): 获取知识详情
        - search(): 搜索知识（支持向量搜索）
        - list_by_source(): 按来源列出知识（如"小搜"）
        - list_by_agent(): 按智能体列出知识
    
    ⚠️ 架构设计（憨货决策 2026-03-16）：
        - knowledge 表存储文档内容/地址
        - shared_memories 表存储引用（knowledge_id）
        - 支持向量搜索，便于语义检索
    """
    
    # 默认智能体 ID（用于知识库 agent）
    # 这个 ID 在数据库中应该已经存在（通过 create-knowledge-table.sql 创建）
    DEFAULT_AGENT_ID = None  # 延迟初始化
    
    async def _get_knowledge_agent_id(self) -> uuid.UUID:
        """
        获取知识库智能体 ID
        
        如果不存在则创建一个。
        """
        if self.DEFAULT_AGENT_ID:
            return self.DEFAULT_AGENT_ID
        
        # 查询或创建知识库 agent
        query = """
            SELECT id FROM agents WHERE name = '知识' LIMIT 1
        """
        result = await db.fetchrow(query)
        
        if result:
            self.DEFAULT_AGENT_ID = result['id']
        else:
            # 创建知识库 agent
            create_query = """
                INSERT INTO agents (name, description, capabilities, metadata)
                VALUES (
                    '知识',
                    '知识库 agent，存储所有知识文件',
                    ARRAY['knowledge_management', 'question_answering'],
                    '{"role": "knowledge_base"}'
                )
                RETURNING id
            """
            result = await db.fetchrow(create_query)
            self.DEFAULT_AGENT_ID = result['id']
            logger.info(f"创建知识库 agent: {self.DEFAULT_AGENT_ID}")
        
        return self.DEFAULT_AGENT_ID
    
    async def create(
        self,
        title: str,
        content: str,
        source: str,
        url: str = None,
        category: str = None,
        tags: List[str] = None,
        metadata: dict = None,
        file_path: str = None
    ) -> uuid.UUID:
        """
        创建知识记录
        
        将文档内容存入 knowledge 表，支持向量搜索。
        
        Args:
            title: 文档标题
            content: 文档内容（可以是正文或摘要）
            source: 来源（如"小搜"、"小码"）
            url: 文档 URL（可选）
            category: 分类（如"documentation"、"article"）
            tags: 标签列表
            metadata: 额外元数据（可包含 task_id, project_id 等）
            file_path: .md 文件存储路径（可选）
        
        Returns:
            knowledge_id: 知识记录的 UUID
        
        Raises:
            ValueError: 参数验证失败
            Exception: 数据库操作失败
        """
        # ============================================================
        # 参数验证
        # ============================================================
        if not title or not title.strip():
            raise ValueError("标题不能为空")
        
        if not content or not content.strip():
            raise ValueError("内容不能为空")
        
        if not source or not source.strip():
            raise ValueError("来源不能为空")
        
        logger.info(f"创建知识记录: title={title[:50]}, source={source}")
        
        try:
            # ============================================================
            # 获取知识库智能体 ID
            # ============================================================
            agent_id = await self._get_knowledge_agent_id()
            
            # ============================================================
            # 生成向量嵌入
            # 用于语义搜索，使用 title + content 前 1000 字符
            # ============================================================
            text_for_embedding = f"{title}\n{content[:1000]}"
            embedding = await embedding_service.get_embedding(text_for_embedding)
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            logger.info(f"生成向量成功，维度: {len(embedding)}")
            
            # ============================================================
            # 准备元数据
            # ============================================================
            full_metadata = metadata or {}
            full_metadata.update({
                "source": source,
                "url": url,
                "created_by": source,  # 记录创建者
                "created_at": datetime.now().isoformat()
            })
            
            # 如果有 URL，添加到元数据中方便检索
            if url:
                full_metadata["url"] = url
            
            metadata_json = json.dumps(full_metadata)
            
            # ============================================================
            # 插入数据库
            # ============================================================
            query = """
                INSERT INTO knowledge (
                    agent_id, title, content, category, tags, source, 
                    embedding, metadata, file_path
                ) VALUES ($1, $2, $3, $4, $5, $6, $7::vector, $8::jsonb, $9)
                RETURNING id
            """
            
            knowledge_id = await db.fetchval(
                query,
                agent_id,
                title,
                content,
                category or "documentation",
                tags or [],
                source,
                embedding_str,
                metadata_json,
                file_path
            )
            
            logger.info(f"知识记录创建成功: knowledge_id={knowledge_id}")
            
            return knowledge_id
        
        except Exception as e:
            logger.error(f"创建知识记录失败: {e}", exc_info=True)
            raise
    
    async def get(self, knowledge_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        获取知识详情
        
        Args:
            knowledge_id: 知识 ID
        
        Returns:
            知识详情字典，包含所有字段
            如果不存在返回 None
        """
        try:
            query = """
                SELECT 
                    id, agent_id, title, content, category, 
                    tags, source, importance, metadata, 
                    created_at, updated_at
                FROM knowledge
                WHERE id = $1
            """
            
            row = await db.fetchrow(query, knowledge_id)
            
            if not row:
                logger.warning(f"知识记录不存在: knowledge_id={knowledge_id}")
                return None
            
            result = dict(row)
            
            # 处理 metadata（可能是字符串或 dict）
            if isinstance(result.get('metadata'), str):
                try:
                    result['metadata'] = json.loads(result['metadata'])
                except json.JSONDecodeError:
                    result['metadata'] = {}
            
            return result
        
        except Exception as e:
            logger.error(f"获取知识详情失败: knowledge_id={knowledge_id}, 错误={e}")
            raise
    
    async def search(
        self,
        query: str = None,
        category: str = None,
        source: str = None,
        limit: int = 10,
        match_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        搜索知识（支持向量搜索）
        
        使用语义相似性搜索知识库，返回最相关的结果。
        
        Args:
            query: 搜索文本（会生成向量进行搜索）
            category: 分类过滤（可选）
            source: 来源过滤（可选，如"小搜"）
            limit: 返回数量限制
            match_threshold: 相似度阈值（0-1）
        
        Returns:
            知识列表，按相似度排序
        """
        if not query:
            # 如果没有查询文本，返回按时间排序的结果
            return await self.list_by_source(source or "", limit)
        
        logger.info(f"搜索知识: query={query[:50]}, source={source}")
        
        try:
            # ============================================================
            # 生成查询向量
            # ============================================================
            embedding = await embedding_service.get_embedding(query)
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            # ============================================================
            # 构建查询条件
            # ============================================================
            conditions = []
            params = [embedding_str]
            param_idx = 2
            
            if category:
                conditions.append(f"category = ${param_idx}")
                params.append(category)
                param_idx += 1
            
            if source:
                conditions.append(f"source = ${param_idx}")
                params.append(source)
                param_idx += 1
            
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            # ============================================================
            # 执行向量搜索
            # 使用余弦距离计算相似度
            # ============================================================
            search_query = f"""
                SELECT 
                    id, agent_id, title, content, category, 
                    tags, source, importance, metadata,
                    created_at,
                    1 - (embedding <=> $1::vector) AS similarity
                FROM knowledge
                WHERE {where_clause}
                  AND 1 - (embedding <=> $1::vector) >= ${param_idx}
                ORDER BY similarity DESC
                LIMIT ${param_idx + 1}
            """
            
            params.extend([match_threshold, limit])
            
            rows = await db.fetch(search_query, *params)
            
            results = []
            for row in rows:
                result = dict(row)
                # 处理 metadata
                if isinstance(result.get('metadata'), str):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        result['metadata'] = {}
                # 处理相似度精度
                if 'similarity' in result:
                    result['similarity'] = round(result['similarity'], 4)
                results.append(result)
            
            logger.info(f"搜索结果: {len(results)} 条")
            
            return results
        
        except Exception as e:
            logger.error(f"搜索知识失败: query={query}, 错误={e}")
            raise
    
    async def list_by_source(
        self,
        source: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        按来源列出知识
        
        查询特定来源（如"小搜"）的所有知识记录。
        
        Args:
            source: 来源名称（可选，为空则返回全部）
            limit: 返回数量限制
            offset: 偏移量（用于分页）
        
        Returns:
            知识列表，按创建时间倒序
        """
        try:
            if source:
                query = """
                    SELECT 
                        id, agent_id, title, content, category, 
                        tags, source, importance, metadata, created_at
                    FROM knowledge
                    WHERE source = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                """
                rows = await db.fetch(query, source, limit, offset)
            else:
                query = """
                    SELECT 
                        id, agent_id, title, content, category, 
                        tags, source, importance, metadata, created_at
                    FROM knowledge
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                """
                rows = await db.fetch(query, limit, offset)
            
            results = []
            for row in rows:
                result = dict(row)
                # 处理 metadata
                if isinstance(result.get('metadata'), str):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        result['metadata'] = {}
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"列出知识失败: source={source}, 错误={e}")
            raise
    
    async def list_by_agent(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        按智能体列出知识
        
        查询特定智能体创建的知识记录。
        
        Args:
            agent_id: 智能体 ID（或从 metadata.created_by 查询）
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            知识列表
        """
        try:
            # 注意：knowledge 表的 agent_id 是知识库 agent，不是创建者
            # 创建者信息存在 metadata.created_by 中
            query = """
                SELECT 
                    id, agent_id, title, content, category, 
                    tags, source, importance, metadata, created_at
                FROM knowledge
                WHERE source = $1 OR metadata->>'created_by' = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            
            rows = await db.fetch(query, agent_id, limit, offset)
            
            results = []
            for row in rows:
                result = dict(row)
                if isinstance(result.get('metadata'), str):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        result['metadata'] = {}
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"列出智能体知识失败: agent_id={agent_id}, 错误={e}")
            raise
    
    async def delete(self, knowledge_id: uuid.UUID) -> bool:
        """
        删除知识记录
        
        Args:
            knowledge_id: 知识 ID
        
        Returns:
            是否删除成功
        """
        try:
            query = "DELETE FROM knowledge WHERE id = $1"
            result = await db.execute(query, knowledge_id)
            success = result == "DELETE 1"
            
            if success:
                logger.info(f"知识记录已删除: knowledge_id={knowledge_id}")
            else:
                logger.warning(f"知识记录不存在或删除失败: knowledge_id={knowledge_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"删除知识失败: knowledge_id={knowledge_id}, 错误={e}")
            raise
    
    async def get_statistics(self, source: str = None) -> Dict[str, Any]:
        """
        获取知识统计信息
        
        Args:
            source: 来源过滤（可选）
        
        Returns:
            统计信息字典
        """
        try:
            if source:
                query = """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(DISTINCT category) as categories,
                        COUNT(DISTINCT source) as sources
                    FROM knowledge
                    WHERE source = $1
                """
                row = await db.fetchrow(query, source)
            else:
                query = """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(DISTINCT category) as categories,
                        COUNT(DISTINCT source) as sources
                    FROM knowledge
                """
                row = await db.fetchrow(query)
            
            return dict(row)
        
        except Exception as e:
            logger.error(f"获取知识统计失败: 错误={e}")
            raise


# 全局服务实例
knowledge_service = KnowledgeService()