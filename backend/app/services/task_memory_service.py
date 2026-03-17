# ============================================================
# 多智能体记忆中枢 - 任务记忆服务
# ============================================================
# 功能：任务与记忆系统的集成服务
# 作者：小码 🟡
# 日期：2026-03-16
# 
# Phase 3 集成功能：
#   1. 为完成的任务自动创建记忆
#   2. 查询任务相关的记忆
#   3. 按项目查询记忆
#   4. 搜索任务记忆
#
# ⚠️ 架构升级（2026-03-16 憨货决策）：
#   - knowledge 表：存储文档内容/地址
#   - shared_memories 表：存储引用（knowledge_id）
#   - 优势：结构清晰、知识独立管理、支持向量搜索、记忆表轻量
# ============================================================

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..database import db
from ..services.memory_service import memory_service
from ..services.embedding_service import embedding_service
from ..services.knowledge_service import knowledge_service
from ..models.schemas import MemoryCreate, MemoryType

logger = logging.getLogger(__name__)


class TaskMemoryService:
    """
    任务记忆服务 - 任务与记忆系统的集成
    
    功能：
        - create_task_memory(): 为完成的任务创建记忆
        - get_task_memories(): 获取任务相关的记忆
        - get_project_memories(): 获取项目相关的记忆
        - search_task_memories(): 搜索任务记忆
        - get_agent_task_memories(): 获取智能体的任务记忆
    
    ⚠️ 设计决策（2026-03-16 憨货亲定）：
        - 公共记忆数据表只保存文档位置/资源地址
        - 没有文档的搜索结果不保存到记忆系统
        - 避免记忆系统被无用数据污染
    """
    
    # 任务类型到记忆类型的映射
    TASK_TO_MEMORY_TYPE = {
        'search': MemoryType.FACT,        # 搜索任务 → 事实
        'write': MemoryType.EXPERIENCE,   # 写作任务 → 经验
        'code': MemoryType.SKILL,         # 代码任务 → 技能
        'review': MemoryType.EXPERIENCE,  # 审查任务 → 经验
        'analyze': MemoryType.FACT,       # 分析任务 → 事实
        'design': MemoryType.SKILL,       # 设计任务 → 技能
        'layout': MemoryType.SKILL,       # 排版任务 → 技能
        'custom': MemoryType.EXPERIENCE   # 自定义 → 经验
    }
    
    # 任务类型到重要性基准的映射
    TASK_IMPORTANCE_BASE = {
        'search': 0.5,
        'write': 0.6,
        'code': 0.7,
        'review': 0.5,
        'analyze': 0.6,
        'design': 0.6,
        'layout': 0.5,
        'custom': 0.5
    }
    
    # 文档记忆的重要性（高优先级）
    DOCUMENT_MEMORY_IMPORTANCE = 0.8
    
    async def create_task_memory(
        self,
        task_id: str,
        agent_id: str,
        task_type: str,
        title: str,
        description: str = None,
        result_summary: Dict[str, Any] = None,
        duration_seconds: float = None,
        project_id: str = None,
        agent_name: str = None,
        auto_route: bool = True,
        visibility: str = None
    ) -> Dict[str, Any]:
        """
        为完成的任务创建记忆
        
        ⚠️ 架构升级（2026-03-16 憨货决策）：
            - 文档内容存入 knowledge 表
            - shared_memories 表只存引用（knowledge_id）
            - 优势：结构清晰、知识独立管理、支持向量搜索
        
        Args:
            task_id: 任务 ID
            agent_id: 智能体 ID
            task_type: 任务类型
            title: 任务标题
            description: 任务描述
            result_summary: 结果摘要（必须包含 documents/urls/file_paths 才会保存）
            duration_seconds: 执行耗时（秒）
            project_id: 项目 ID
            agent_name: 智能体名称
            auto_route: 是否自动路由到合适的表
            visibility: 可见性（private/shared）
        
        Returns:
            创建结果，包含 memory_ids, knowledge_ids 等
            如果没有文档/资源，返回 None
        """
        # ============================================================
        # 步骤 0：【核心逻辑】检查是否有文档/资源
        # 憨货决定：只保存有文档/资源地址的记忆
        # ============================================================
        documents = []
        urls = []
        file_paths = []
        
        if result_summary:
            # 提取文档列表
            documents = result_summary.get('documents', [])
            urls = result_summary.get('urls', [])
            file_paths = result_summary.get('file_paths', [])
            
            # 兼容旧格式：检查 result_summary 顶层是否有 url
            if 'url' in result_summary and result_summary['url']:
                urls.append(result_summary['url'])
            
            # 兼容旧格式：检查 results 列表中的 url
            results_list = result_summary.get('results', [])
            if isinstance(results_list, list):
                for r in results_list:
                    if isinstance(r, dict):
                        if r.get('url'):
                            urls.append(r['url'])
                        if r.get('doc_url'):
                            urls.append(r['doc_url'])
        
        # 如果没有文档/资源，不保存到记忆系统
        if not documents and not urls and not file_paths:
            logger.info(
                f"任务 {task_id} 没有文档/资源地址，不保存到记忆系统"
            )
            return {
                "memory_ids": [],
                "knowledge_ids": [],
                "table": None,
                "visibility": None,
                "auto_routed": False,
                "importance": 0,
                "message": "没有文档/资源，不保存到记忆系统"
            }
        
        # ============================================================
        # 步骤 1：【新架构】将文档存入 knowledge 表
        # 每个文档单独创建一条 knowledge 记录
        # ============================================================
        knowledge_ids = []
        memory_ids = []
        source_name = agent_name or agent_id
        
        try:
            # 处理 documents 列表
            for doc in documents:
                if not isinstance(doc, dict):
                    continue
                
                doc_title = doc.get('title', '未知文档')
                doc_content = doc.get('content', doc.get('description', doc_title))
                doc_url = doc.get('url', '')
                
                if not doc_url and not doc_content:
                    continue
                
                # 1.1 存入 knowledge 表
                knowledge_id = await knowledge_service.create(
                    title=doc_title,
                    content=doc_content,
                    source=source_name,
                    url=doc_url,
                    category='documentation',
                    tags=[task_type, '文档'],
                    metadata={
                        'task_id': task_id,
                        'project_id': project_id,
                        'agent_id': agent_id,
                        'doc_type': 'document'
                    }
                )
                knowledge_ids.append(str(knowledge_id))
                
                # 1.2 创建 shared_memory（引用 knowledge_id）
                memory_content = f"找到文档：{doc_title}"
                if doc_url:
                    memory_content += f"\n地址：{doc_url}"
                
                memory = MemoryCreate(
                    agent_id=uuid.UUID(agent_id),
                    content=memory_content,
                    memory_type=MemoryType.FACT,
                    importance=self.DOCUMENT_MEMORY_IMPORTANCE,
                    tags=[task_type, "任务", "文档"],
                    metadata={
                        'knowledge_id': str(knowledge_id),  # ← 引用 knowledge 表
                        'source': source_name,
                        'type': 'document_reference',
                        'task_id': task_id,
                        'project_id': project_id,
                        'doc_title': doc_title,
                        'doc_url': doc_url,
                        'memory_category': 'document'
                    },
                    auto_route=False,
                    visibility='shared'  # 文档记忆默认共享
                )
                
                memory_id, table, vis, routed = await memory_service.create_memory(memory)
                memory_ids.append(memory_id)
                
                logger.info(
                    f"文档记忆创建成功: doc={doc_title}, "
                    f"knowledge_id={knowledge_id}, memory_id={memory_id}"
                )
            
            # 处理 urls 列表
            for url in urls:
                if not url:
                    continue
                
                # 从 URL 提取标题
                url_title = url.split('/')[-1] or url
                if '.' in url_title:
                    url_title = url_title.split('.')[0]
                
                # 2.1 存入 knowledge 表
                knowledge_id = await knowledge_service.create(
                    title=url_title,
                    content=f"资源链接：{url}",
                    source=source_name,
                    url=url,
                    category='link',
                    tags=[task_type, '链接'],
                    metadata={
                        'task_id': task_id,
                        'project_id': project_id,
                        'agent_id': agent_id,
                        'doc_type': 'url'
                    }
                )
                knowledge_ids.append(str(knowledge_id))
                
                # 2.2 创建 shared_memory（引用 knowledge_id）
                memory_content = f"找到资源：{url_title}\n地址：{url}"
                
                memory = MemoryCreate(
                    agent_id=uuid.UUID(agent_id),
                    content=memory_content,
                    memory_type=MemoryType.FACT,
                    importance=self.DOCUMENT_MEMORY_IMPORTANCE,
                    tags=[task_type, "任务", "链接"],
                    metadata={
                        'knowledge_id': str(knowledge_id),
                        'source': source_name,
                        'type': 'document_reference',
                        'task_id': task_id,
                        'project_id': project_id,
                        'doc_title': url_title,
                        'doc_url': url,
                        'memory_category': 'document'
                    },
                    auto_route=False,
                    visibility='shared'
                )
                
                memory_id, table, vis, routed = await memory_service.create_memory(memory)
                memory_ids.append(memory_id)
            
            # 处理 file_paths 列表
            for file_path in file_paths:
                if not file_path:
                    continue
                
                file_name = file_path.split('/')[-1] or file_path
                
                # 3.1 存入 knowledge 表
                knowledge_id = await knowledge_service.create(
                    title=file_name,
                    content=f"文件路径：{file_path}",
                    source=source_name,
                    url=file_path,  # 用 url 字段存储路径
                    category='file',
                    tags=[task_type, '文件'],
                    metadata={
                        'task_id': task_id,
                        'project_id': project_id,
                        'agent_id': agent_id,
                        'doc_type': 'file'
                    }
                )
                knowledge_ids.append(str(knowledge_id))
                
                # 3.2 创建 shared_memory（引用 knowledge_id）
                memory_content = f"找到文件：{file_name}\n路径：{file_path}"
                
                memory = MemoryCreate(
                    agent_id=uuid.UUID(agent_id),
                    content=memory_content,
                    memory_type=MemoryType.FACT,
                    importance=self.DOCUMENT_MEMORY_IMPORTANCE,
                    tags=[task_type, "任务", "文件"],
                    metadata={
                        'knowledge_id': str(knowledge_id),
                        'source': source_name,
                        'type': 'document_reference',
                        'task_id': task_id,
                        'project_id': project_id,
                        'doc_title': file_name,
                        'doc_url': file_path,
                        'memory_category': 'document'
                    },
                    auto_route=False,
                    visibility='shared'
                )
                
                memory_id, table, vis, routed = await memory_service.create_memory(memory)
                memory_ids.append(memory_id)
            
            logger.info(
                f"任务 {task_id} 记忆创建完成: "
                f"knowledge_ids={len(knowledge_ids)}, memory_ids={len(memory_ids)}"
            )
            
            return {
                "memory_ids": memory_ids,
                "knowledge_ids": knowledge_ids,
                "table": "shared",
                "visibility": "shared",
                "auto_routed": False,
                "importance": self.DOCUMENT_MEMORY_IMPORTANCE,
                "documents_count": len(knowledge_ids),
                "message": f"文档记忆已创建，存储在 knowledge 表 + shared_memories 表"
            }
        
        except Exception as e:
            logger.error(f"创建文档记忆失败: {e}", exc_info=True)
            raise
    
    def _build_document_memory_content(
        self,
        title: str,
        description: str,
        documents: List[Dict],
        urls: List[str],
        file_paths: List[str],
        agent_name: str = None
    ) -> str:
        """
        构建文档记忆的内容
        
        Args:
            title: 任务标题
            description: 任务描述
            documents: 文档列表
            urls: URL 列表
            file_paths: 文件路径列表
            agent_name: 执行者名称
        
        Returns:
            记忆内容字符串
        """
        content_parts = [f"【文档记忆】{title}"]
        
        if description:
            desc_short = description[:200] + ('...' if len(description) > 200 else '')
            content_parts.append(f"描述：{desc_short}")
        
        # 添加文档信息
        if documents:
            content_parts.append(f"\n文档 ({len(documents)} 个):")
            for i, doc in enumerate(documents[:5], 1):  # 最多显示 5 个
                doc_title = doc.get('title', '未知')
                doc_url = doc.get('url', '')
                content_parts.append(f"  {i}. {doc_title}")
                if doc_url:
                    content_parts.append(f"     {doc_url}")
        
        # 添加 URL 信息
        if urls:
            unique_urls = list(set(urls))  # 去重
            content_parts.append(f"\n资源链接 ({len(unique_urls)} 个):")
            for i, url in enumerate(unique_urls[:10], 1):  # 最多显示 10 个
                content_parts.append(f"  {i}. {url}")
        
        # 添加文件路径信息
        if file_paths:
            content_parts.append(f"\n文件路径 ({len(file_paths)} 个):")
            for i, path in enumerate(file_paths[:10], 1):  # 最多显示 10 个
                content_parts.append(f"  {i}. {path}")
        
        if agent_name:
            content_parts.append(f"\n执行者：{agent_name}")
        
        return "\n".join(content_parts)
    
    def _build_document_memory_metadata(
        self,
        task_id: str,
        task_type: str,
        agent_id: str,
        agent_name: str,
        project_id: str,
        duration_seconds: float,
        documents: List[Dict],
        urls: List[str],
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """
        构建文档记忆的元数据
        
        Args:
            task_id: 任务 ID
            task_type: 任务类型
            agent_id: 智能体 ID
            agent_name: 智能体名称
            project_id: 项目 ID
            duration_seconds: 执行耗时
            documents: 文档列表
            urls: URL 列表
            file_paths: 文件路径列表
        
        Returns:
            元数据字典，必须包含 url/title/source 字段
        """
        metadata = {
            "task_id": task_id,
            "task_type": task_type,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "project_id": project_id,
            "duration_seconds": duration_seconds,
            "created_at": datetime.now().isoformat(),
            
            # 文档记忆必须包含的字段
            "documents": documents,
            "urls": list(set(urls)) if urls else [],  # 去重
            "file_paths": file_paths,
            
            # 记忆来源
            "source": agent_name or "未知",
            "memory_category": "document"  # 标记为文档类型记忆
        }
        
        # 清理 None 值
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return metadata
    
    async def get_task_memories(
        self,
        task_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取某个任务的所有记忆
        
        Args:
            task_id: 任务 ID
            limit: 返回数量限制
        
        Returns:
            记忆列表
        """
        # 在两个表中搜索包含 task_id 的记忆
        results = []
        
        # 搜索私人记忆
        private_query = """
            SELECT id, agent_id, content, memory_type, importance,
                   access_count, tags, metadata, created_at, last_accessed,
                   'private' as visibility
            FROM private_memories
            WHERE metadata->>'task_id' = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        private_rows = await db.fetch(private_query, task_id, limit)
        results.extend([dict(row) for row in private_rows])
        
        # 搜索共同记忆
        shared_query = """
            SELECT id, agent_id, content, memory_type, importance,
                   access_count, tags, metadata, created_at, last_accessed,
                   'shared' as visibility
            FROM shared_memories
            WHERE metadata->>'task_id' = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        shared_rows = await db.fetch(shared_query, task_id, limit)
        results.extend([dict(row) for row in shared_rows])
        
        # 按创建时间排序
        results.sort(key=lambda x: x['created_at'], reverse=True)
        
        return results[:limit]
    
    async def get_project_memories(
        self,
        project_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取某个项目的所有记忆
        
        Args:
            project_id: 项目 ID
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            包含 memories 和 total 的字典
        """
        results = []
        
        # 搜索私人记忆
        private_query = """
            SELECT id, agent_id, content, memory_type, importance,
                   access_count, tags, metadata, created_at, last_accessed,
                   'private' as visibility
            FROM private_memories
            WHERE metadata->>'project_id' = $1
            ORDER BY created_at DESC
        """
        private_rows = await db.fetch(private_query, project_id)
        results.extend([dict(row) for row in private_rows])
        
        # 搜索共同记忆
        shared_query = """
            SELECT id, agent_id, content, memory_type, importance,
                   access_count, tags, metadata, created_at, last_accessed,
                   'shared' as visibility
            FROM shared_memories
            WHERE metadata->>'project_id' = $1
            ORDER BY created_at DESC
        """
        shared_rows = await db.fetch(shared_query, project_id)
        results.extend([dict(row) for row in shared_rows])
        
        # 按创建时间排序
        results.sort(key=lambda x: x['created_at'], reverse=True)
        
        total = len(results)
        paginated = results[offset:offset + limit]
        
        return {
            "memories": paginated,
            "total": total,
            "project_id": project_id
        }
    
    async def search_task_memories(
        self,
        query: str,
        agent_id: str = None,
        task_type: str = None,
        project_id: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索任务相关的记忆
        
        使用向量搜索 + 元数据过滤
        
        Args:
            query: 搜索文本
            agent_id: 智能体 ID（可选）
            task_type: 任务类型（可选）
            project_id: 项目 ID（可选）
            limit: 返回数量
        
        Returns:
            记忆列表（按相似度排序）
        """
        # 生成查询向量
        embedding = await embedding_service.get_embedding(query)
        
        results = []
        
        # 搜索私人记忆
        if agent_id:
            private_query = """
                SELECT id, agent_id, content, memory_type, importance,
                       access_count, tags, metadata, created_at,
                       1 - (embedding <=> $1::vector) as similarity,
                       'private' as visibility
                FROM private_memories
                WHERE agent_id = $2::uuid
                  AND metadata->>'task_id' IS NOT NULL
                  AND ($3::text IS NULL OR metadata->>'task_type' = $3)
                  AND ($4::text IS NULL OR metadata->>'project_id' = $4)
                ORDER BY similarity DESC
                LIMIT $5
            """
            rows = await db.fetch(
                private_query,
                f"[{','.join(map(str, embedding))}]",
                uuid.UUID(agent_id),
                task_type,
                project_id,
                limit
            )
            results.extend([dict(row) for row in rows])
        
        # 搜索共同记忆（团队共享）
        shared_query = """
            SELECT id, agent_id, content, memory_type, importance,
                   access_count, tags, metadata, created_at,
                   1 - (embedding <=> $1::vector) as similarity,
                   'shared' as visibility
            FROM shared_memories
            WHERE metadata->>'task_id' IS NOT NULL
              AND ($2::uuid IS NULL OR agent_id = $2)
              AND ($3::text IS NULL OR metadata->>'task_type' = $3)
              AND ($4::text IS NULL OR metadata->>'project_id' = $4)
            ORDER BY similarity DESC
            LIMIT $5
        """
        rows = await db.fetch(
            shared_query,
            f"[{','.join(map(str, embedding))}]",
            uuid.UUID(agent_id) if agent_id else None,
            task_type,
            project_id,
            limit
        )
        results.extend([dict(row) for row in rows])
        
        # 按相似度排序并去重
        results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        # 去重（同一记忆可能出现在两个结果中）
        seen = set()
        unique_results = []
        for r in results:
            key = (str(r['id']), r['visibility'])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return unique_results[:limit]
    
    async def get_agent_task_memories(
        self,
        agent_id: str,
        task_type: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取智能体的任务记忆
        
        Args:
            agent_id: 智能体 ID
            task_type: 任务类型过滤（可选）
            limit: 返回数量
        
        Returns:
            记忆列表
        """
        results = []
        
        # 构建查询条件
        type_condition = "AND metadata->>'task_type' = $3" if task_type else ""
        
        # 搜索私人记忆
        private_query = f"""
            SELECT id, agent_id, content, memory_type, importance,
                   access_count, tags, metadata, created_at, last_accessed,
                   'private' as visibility
            FROM private_memories
            WHERE agent_id = $1::uuid
              AND metadata->>'task_id' IS NOT NULL
              {type_condition}
            ORDER BY created_at DESC
            LIMIT $2
        """
        params = [uuid.UUID(agent_id), limit]
        if task_type:
            params.append(task_type)
        
        private_rows = await db.fetch(private_query, *params)
        results.extend([dict(row) for row in private_rows])
        
        # 搜索共同记忆
        shared_query = f"""
            SELECT id, agent_id, content, memory_type, importance,
                   access_count, tags, metadata, created_at, last_accessed,
                   'shared' as visibility
            FROM shared_memories
            WHERE agent_id = $1::uuid
              AND metadata->>'task_id' IS NOT NULL
              {type_condition}
            ORDER BY created_at DESC
            LIMIT $2
        """
        
        shared_rows = await db.fetch(shared_query, *params)
        results.extend([dict(row) for row in shared_rows])
        
        # 按创建时间排序
        results.sort(key=lambda x: x['created_at'], reverse=True)
        
        return results[:limit]
    
    async def get_task_memory_statistics(
        self,
        agent_id: str = None,
        project_id: str = None
    ) -> Dict[str, Any]:
        """
        获取任务记忆统计
        
        Args:
            agent_id: 智能体 ID（可选）
            project_id: 项目 ID（可选）
        
        Returns:
            统计信息
        """
        stats = {
            "total_memories": 0,
            "by_task_type": {},
            "by_visibility": {"private": 0, "shared": 0},
            "avg_importance": 0.0
        }
        
        # 构建过滤条件
        conditions = ["metadata->>'task_id' IS NOT NULL"]
        params = []
        param_idx = 1
        
        if agent_id:
            conditions.append(f"agent_id = ${param_idx}::uuid")
            params.append(uuid.UUID(agent_id))
            param_idx += 1
        
        if project_id:
            conditions.append(f"metadata->>'project_id' = ${param_idx}")
            params.append(project_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        # 查询私人记忆
        private_query = f"""
            SELECT COUNT(*) as count, AVG(importance) as avg_importance
            FROM private_memories
            WHERE {where_clause}
        """
        private_stats = await db.fetchrow(private_query, *params)
        
        # 查询共同记忆
        shared_query = f"""
            SELECT COUNT(*) as count, AVG(importance) as avg_importance
            FROM shared_memories
            WHERE {where_clause}
        """
        shared_stats = await db.fetchrow(shared_query, *params)
        
        stats["by_visibility"]["private"] = private_stats['count'] or 0
        stats["by_visibility"]["shared"] = shared_stats['count'] or 0
        stats["total_memories"] = stats["by_visibility"]["private"] + stats["by_visibility"]["shared"]
        
        # 计算平均重要性
        total_count = stats["total_memories"]
        if total_count > 0:
            private_avg = float(private_stats['avg_importance'] or 0)
            shared_avg = float(shared_stats['avg_importance'] or 0)
            stats["avg_importance"] = (
                private_avg * stats["by_visibility"]["private"] +
                shared_avg * stats["by_visibility"]["shared"]
            ) / total_count
        
        # 按任务类型统计
        type_query = f"""
            SELECT metadata->>'task_type' as task_type, COUNT(*) as count
            FROM (
                SELECT metadata FROM private_memories WHERE {where_clause}
                UNION ALL
                SELECT metadata FROM shared_memories WHERE {where_clause}
            ) combined
            WHERE metadata->>'task_type' IS NOT NULL
            GROUP BY metadata->>'task_type'
        """
        type_rows = await db.fetch(type_query, *params, *params)
        stats["by_task_type"] = {row['task_type']: row['count'] for row in type_rows}
        
        return stats


# 全局服务实例
task_memory_service = TaskMemoryService()