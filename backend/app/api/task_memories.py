# ============================================================
# 多智能体记忆中枢 - 任务记忆 API 路由
# ============================================================
# 功能：任务与记忆系统的集成 API
# 作者：小码 🟡
# 日期：2026-03-16
# 
# Phase 3 集成 API：
#   GET  /api/tasks/{task_id}/memories         - 获取任务记忆
#   GET  /api/projects/{project_id}/memories   - 获取项目记忆
#   GET  /api/memories/search                  - 搜索任务记忆
#   GET  /api/agents/{agent_id}/task-memories  - 获取智能体任务记忆
#   GET  /api/task-memories/statistics         - 获取任务记忆统计
#   GET  /api/memories/documents               - 查询文档记忆（新增）
#
# ⚠️ 架构升级（2026-03-16 憨货决策）：
#   - knowledge 表：存储文档内容/地址
#   - shared_memories 表：存储引用（knowledge_id）
#   - 查询流程：先查 shared_memories → 提取 knowledge_id → 查 knowledge 表
# ============================================================

from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import uuid

from ..services.task_memory_service import task_memory_service
from ..services.knowledge_service import knowledge_service
from ..database import db
from ..auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


# ============================================================
# 响应模型
# ============================================================

class TaskMemoryResponse(BaseModel):
    """任务记忆响应"""
    memory_id: str
    agent_id: str
    content: str
    memory_type: str
    importance: float
    visibility: str
    task_type: Optional[str] = None
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: str


class TaskMemoriesListResponse(BaseModel):
    """任务记忆列表响应"""
    memories: List[Dict[str, Any]]
    total: int
    task_id: str


class ProjectMemoriesResponse(BaseModel):
    """项目记忆响应"""
    memories: List[Dict[str, Any]]
    total: int
    project_id: str


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[Dict[str, Any]]
    query: str
    total: int


class StatisticsResponse(BaseModel):
    """统计响应"""
    total_memories: int
    by_task_type: Dict[str, int]
    by_visibility: Dict[str, int]
    avg_importance: float


# ============================================================
# API 路由
# ============================================================

@router.get(
    "/tasks/{task_id}/memories",
    response_model=TaskMemoriesListResponse,
    tags=["任务记忆"],
    summary="获取任务的所有记忆",
    description="""
    获取某个任务的所有记忆记录
    
    **参数**:
    - **task_id**: 任务 ID
    - **limit**: 返回数量限制（默认 10）
    
    **返回**:
    - 该任务创建的所有记忆，按创建时间倒序
    """,
)
async def get_task_memories(
    task_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="返回数量限制")
):
    """
    获取某个任务的所有记忆
    
    当任务完成后，系统会自动为任务创建记忆。
    此接口用于查询这些记忆。
    """
    try:
        memories = await task_memory_service.get_task_memories(task_id, limit)
        
        # 处理 UUID 和时间格式
        for m in memories:
            m['id'] = str(m['id'])
            m['agent_id'] = str(m['agent_id'])
            m['created_at'] = str(m['created_at'])
            if m.get('last_accessed'):
                m['last_accessed'] = str(m['last_accessed'])
        
        return TaskMemoriesListResponse(
            memories=memories,
            total=len(memories),
            task_id=task_id
        )
    
    except Exception as e:
        logger.error(f"获取任务记忆失败: task_id={task_id}, 错误={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务记忆失败: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/memories",
    response_model=ProjectMemoriesResponse,
    tags=["任务记忆"],
    summary="获取项目的所有记忆",
    description="""
    获取某个项目的所有记忆记录
    
    **参数**:
    - **project_id**: 项目 ID
    - **limit**: 返回数量限制（默认 50）
    - **offset**: 偏移量（用于分页）
    
    **返回**:
    - 该项目下所有任务创建的记忆
    """,
)
async def get_project_memories(
    project_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量")
):
    """
    获取某个项目的所有记忆
    
    按项目 ID 查询所有相关任务的记忆。
    支持分页查询。
    """
    try:
        result = await task_memory_service.get_project_memories(project_id, limit, offset)
        
        # 处理 UUID 和时间格式
        for m in result['memories']:
            m['id'] = str(m['id'])
            m['agent_id'] = str(m['agent_id'])
            m['created_at'] = str(m['created_at'])
            if m.get('last_accessed'):
                m['last_accessed'] = str(m['last_accessed'])
        
        return ProjectMemoriesResponse(**result)
    
    except Exception as e:
        logger.error(f"获取项目记忆失败: project_id={project_id}, 错误={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目记忆失败: {str(e)}"
        )


@router.get(
    "/memories/search",
    response_model=SearchResponse,
    tags=["任务记忆"],
    summary="搜索任务记忆",
    description="""
    搜索任务相关的记忆（支持向量搜索）
    
    **参数**:
    - **q**: 搜索关键词
    - **agent_id**: 智能体 ID（可选）
    - **task_type**: 任务类型（可选）
    - **project_id**: 项目 ID（可选）
    - **limit**: 返回数量（默认 10）
    
    **返回**:
    - 按相似度排序的记忆列表
    """,
)
async def search_task_memories(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    agent_id: Optional[str] = Query(default=None, description="智能体 ID"),
    task_type: Optional[str] = Query(default=None, description="任务类型"),
    project_id: Optional[str] = Query(default=None, description="项目 ID"),
    limit: int = Query(default=10, ge=1, le=50, description="返回数量")
):
    """
    搜索任务相关的记忆
    
    使用向量相似性搜索，支持按智能体、任务类型、项目过滤。
    结果按相似度从高到低排序。
    """
    try:
        results = await task_memory_service.search_task_memories(
            query=q,
            agent_id=agent_id,
            task_type=task_type,
            project_id=project_id,
            limit=limit
        )
        
        # 处理 UUID 和时间格式
        for r in results:
            r['id'] = str(r['id'])
            r['agent_id'] = str(r['agent_id'])
            r['created_at'] = str(r['created_at'])
            # 处理 similarity 精度
            if 'similarity' in r:
                r['similarity'] = round(r['similarity'], 4)
        
        return SearchResponse(
            results=results,
            query=q,
            total=len(results)
        )
    
    except Exception as e:
        logger.error(f"搜索任务记忆失败: query={q}, 错误={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.get(
    "/agents/{agent_id}/task-memories",
    response_model=TaskMemoriesListResponse,
    tags=["任务记忆"],
    summary="获取智能体的任务记忆",
    description="""
    获取某个智能体的所有任务记忆
    
    **参数**:
    - **agent_id**: 智能体 ID
    - **task_type**: 任务类型过滤（可选）
    - **limit**: 返回数量（默认 20）
    
    **返回**:
    - 该智能体执行任务产生的所有记忆
    """,
)
async def get_agent_task_memories(
    agent_id: str,
    task_type: Optional[str] = Query(default=None, description="任务类型过滤"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量")
):
    """
    获取智能体的任务记忆
    
    查询某个智能体执行任务产生的所有记忆。
    可按任务类型过滤。
    """
    try:
        memories = await task_memory_service.get_agent_task_memories(
            agent_id=agent_id,
            task_type=task_type,
            limit=limit
        )
        
        # 处理 UUID 和时间格式
        for m in memories:
            m['id'] = str(m['id'])
            m['agent_id'] = str(m['agent_id'])
            m['created_at'] = str(m['created_at'])
            if m.get('last_accessed'):
                m['last_accessed'] = str(m['last_accessed'])
        
        return TaskMemoriesListResponse(
            memories=memories,
            total=len(memories),
            task_id=""  # 此接口不针对特定任务
        )
    
    except Exception as e:
        logger.error(f"获取智能体任务记忆失败: agent_id={agent_id}, 错误={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.get(
    "/task-memories/statistics",
    response_model=StatisticsResponse,
    tags=["任务记忆"],
    summary="获取任务记忆统计",
    description="""
    获取任务记忆的统计信息
    
    **参数**:
    - **agent_id**: 智能体 ID（可选）
    - **project_id**: 项目 ID（可选）
    
    **返回**:
    - 总记忆数
    - 按任务类型分组统计
    - 按可见性分组统计
    - 平均重要性
    """,
)
async def get_task_memory_statistics(
    agent_id: Optional[str] = Query(default=None, description="智能体 ID"),
    project_id: Optional[str] = Query(default=None, description="项目 ID")
):
    """
    获取任务记忆统计
    
    统计任务相关的记忆信息，支持按智能体或项目过滤。
    """
    try:
        stats = await task_memory_service.get_task_memory_statistics(
            agent_id=agent_id,
            project_id=project_id
        )
        
        return StatisticsResponse(
            total_memories=stats['total_memories'],
            by_task_type=stats['by_task_type'],
            by_visibility=stats['by_visibility'],
            avg_importance=round(stats['avg_importance'], 4)
        )
    
    except Exception as e:
        logger.error(f"获取任务记忆统计失败: 错误={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}"
        )


# ============================================================
# 手动创建任务记忆（可选）
# ============================================================

class CreateTaskMemoryRequest(BaseModel):
    """创建任务记忆请求"""
    task_id: str = Field(..., description="任务 ID")
    agent_id: str = Field(..., description="智能体 ID")
    task_type: str = Field(default="custom", description="任务类型")
    title: str = Field(..., min_length=1, max_length=500, description="任务标题")
    description: Optional[str] = Field(default=None, description="任务描述")
    result_summary: Optional[Dict[str, Any]] = Field(default=None, description="结果摘要")
    duration_seconds: Optional[float] = Field(default=None, description="执行耗时（秒）")
    project_id: Optional[str] = Field(default=None, description="项目 ID")
    agent_name: Optional[str] = Field(default=None, description="智能体名称")
    visibility: Optional[str] = Field(default=None, description="可见性（private/shared）")


@router.post(
    "/task-memories",
    status_code=status.HTTP_201_CREATED,
    tags=["任务记忆"],
    summary="手动创建任务记忆",
    description="""
    手动为任务创建记忆（通常由系统自动创建，此接口用于特殊情况）
    
    **请求体**:
    - task_id: 任务 ID
    - agent_id: 智能体 ID
    - title: 任务标题
    - 其他可选字段
    
    **返回**:
    - memory_id: 创建的记忆 ID
    - table: 存储的表（private/shared）
    - importance: 记忆重要性
    """,
)
async def create_task_memory(request: CreateTaskMemoryRequest):
    """
    手动创建任务记忆
    
    通常情况下，任务完成后会自动创建记忆。
    此接口用于特殊场景下手动创建。
    """
    try:
        result = await task_memory_service.create_task_memory(
            task_id=request.task_id,
            agent_id=request.agent_id,
            task_type=request.task_type,
            title=request.title,
            description=request.description,
            result_summary=request.result_summary,
            duration_seconds=request.duration_seconds,
            project_id=request.project_id,
            agent_name=request.agent_name,
            visibility=request.visibility
        )
        
        return {
            "success": True,
            **result
        }
    
    except Exception as e:
        logger.error(f"创建任务记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


# ============================================================
# 文档记忆查询接口（2026-03-16 憨货决策新增）
# ============================================================

class DocumentMemoryItem(BaseModel):
    """文档记忆条目"""
    title: str = Field(..., description="文档标题")
    url: str = Field(..., description="文档地址")
    source: str = Field(default="未知", description="来源（小搜/小码等）")
    description: Optional[str] = Field(default=None, description="文档描述")
    created_at: str = Field(..., description="创建时间")
    task_id: Optional[str] = Field(default=None, description="关联任务 ID")
    project_id: Optional[str] = Field(default=None, description="项目 ID")


class DocumentMemoriesResponse(BaseModel):
    """文档记忆响应"""
    documents: List[DocumentMemoryItem]
    total: int
    query: Optional[str] = None


class SharedMemoryItem(BaseModel):
    """共享记忆条目"""
    id: str
    agent_id: str
    content: str
    memory_type: str
    importance: float
    visibility: str
    created_at: str
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SharedMemoriesResponse(BaseModel):
    """共享记忆响应"""
    memories: List[SharedMemoryItem]
    total: int


# ============================================================
# 共享记忆查询接口（修复 2026-03-18）
# ============================================================

@router.get(
    "/memories/shared",
    response_model=SharedMemoriesResponse,
    tags=["共享记忆"],
    summary="查询共享记忆",
    description="""
    查询所有共享记忆
    
    **参数**:
    - **limit**: 返回数量（默认 20，最大 100）
    - **offset**: 偏移量（用于分页）
    
    **返回**:
    - memories: 共享记忆列表
    - total: 总数量
    """,
)
async def get_shared_memories(
    limit: int = Query(default=20, ge=1, le=100, description="返回数量"),
    offset: int = Query(default=0, ge=0, description="偏移量")
):
    """
    查询所有共享记忆
    
    直接查询 shared_memories 表，返回所有共享记忆。
    """
    try:
        query = """
            SELECT id, agent_id, content, memory_type, importance, 
                   visibility, created_at, tags, metadata
            FROM shared_memories
            ORDER BY importance DESC, created_at DESC
            LIMIT $1 OFFSET $2
        """
        rows = await db.fetch(query, limit, offset)
        
        memories = []
        for row in rows:
            # 处理 metadata 和 tags（可能是字符串或 dict）
            import json
            metadata_raw = row['metadata']
            if isinstance(metadata_raw, str):
                try:
                    metadata = json.loads(metadata_raw)
                except json.JSONDecodeError:
                    metadata = {}
            else:
                metadata = metadata_raw or {}
            
            tags_raw = row['tags']
            if isinstance(tags_raw, str):
                try:
                    tags = json.loads(tags_raw)
                except json.JSONDecodeError:
                    tags = []
            else:
                tags = tags_raw or []
            
            memories.append(SharedMemoryItem(
                id=str(row['id']),
                agent_id=str(row['agent_id']),
                content=row['content'],
                memory_type=row['memory_type'],
                importance=row['importance'],
                visibility=row['visibility'],
                created_at=str(row['created_at']),
                tags=tags,
                metadata=metadata
            ))
        
        # 获取总数
        count_query = "SELECT COUNT(*) FROM shared_memories"
        total = await db.fetchval(count_query)
        
        return SharedMemoriesResponse(memories=memories, total=total)
    
    except Exception as e:
        logger.error(f"查询共享记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get(
    "/memories/documents",
    response_model=DocumentMemoriesResponse,
    tags=["文档记忆"],
    summary="查询文档记忆",
    description="""
    查询文档/资源记忆
    
    ⚠️ 架构升级（2026-03-16 憨货决策）：
        - knowledge 表：存储文档内容/地址
        - shared_memories 表：存储引用（knowledge_id）
        - 查询流程：先查 shared_memories → 提取 knowledge_id → 查 knowledge 表
    
    **参数**:
    - **query**: 搜索关键词（可选）
    - **project_id**: 项目 ID（可选）
    - **source**: 来源过滤，如 "小搜"、"小码"（可选）
    - **limit**: 返回数量（默认 20）
    
    **返回**:
    - documents: 文档列表，每个包含 title, url, source, content, created_at
    - total: 总数量
    """,
)
async def get_document_memories(
    query: Optional[str] = Query(default=None, description="搜索关键词"),
    project_id: Optional[str] = Query(default=None, description="项目 ID"),
    source: Optional[str] = Query(default=None, description="来源过滤"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量")
):
    """
    查询文档记忆
    
    使用新架构：
    1. 先查 shared_memories 表获取记忆列表
    2. 从 metadata 中提取 knowledge_id
    3. 查询 knowledge 表获取文档详情
    """
    try:
        documents = []
        
        # ============================================================
        # 步骤 1：查询 shared_memories 表获取文档引用
        # ============================================================
        conditions = ["metadata->>'memory_category' = 'document'"]
        params = []
        param_idx = 1
        
        if project_id:
            conditions.append(f"metadata->>'project_id' = ${param_idx}")
            params.append(project_id)
            param_idx += 1
        
        if source:
            conditions.append(f"metadata->>'source' = ${param_idx}")
            params.append(source)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        # 查询 shared_memories 表
        memory_query = f"""
            SELECT id, content, metadata, created_at
            FROM shared_memories
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx}
        """
        memory_rows = await db.fetch(memory_query, *params, limit)
        
        # ============================================================
        # 步骤 2：从记忆中提取 knowledge_id，查询 knowledge 表
        # ============================================================
        import json
        
        for row in memory_rows:
            # 处理 metadata（可能是字符串或 dict）
            metadata_raw = row['metadata']
            if isinstance(metadata_raw, str):
                try:
                    metadata = json.loads(metadata_raw)
                except json.JSONDecodeError:
                    metadata = {}
            else:
                metadata = metadata_raw or {}
            
            knowledge_id = metadata.get('knowledge_id')
            
            if knowledge_id:
                # 查询 knowledge 表获取文档详情
                try:
                    doc = await knowledge_service.get(uuid.UUID(knowledge_id))
                    if doc:
                        # 如果有搜索关键词，进行过滤
                        if query:
                            doc_title = doc.get('title', '').lower()
                            doc_content = doc.get('content', '').lower()
                            if query.lower() not in doc_title and query.lower() not in doc_content:
                                continue
                        
                        documents.append(DocumentMemoryItem(
                            title=doc.get('title', '未知'),
                            url=doc.get('metadata', {}).get('url', ''),
                            source=doc.get('source', metadata.get('source', '未知')),
                            description=doc.get('content', '')[:500] if doc.get('content') else None,
                            created_at=str(row['created_at']),
                            task_id=metadata.get('task_id'),
                            project_id=metadata.get('project_id')
                        ))
                except Exception as e:
                    logger.warning(f"查询知识详情失败: knowledge_id={knowledge_id}, 错误={e}")
                    # 如果 knowledge 表查询失败，使用 memory 中的信息
                    documents.append(DocumentMemoryItem(
                        title=metadata.get('doc_title', '未知'),
                        url=metadata.get('doc_url', ''),
                        source=metadata.get('source', '未知'),
                        description=None,
                        created_at=str(row['created_at']),
                        task_id=metadata.get('task_id'),
                        project_id=metadata.get('project_id')
                    ))
            elif metadata.get('documents'):
                # 【修复 2026-03-16】处理没有 knowledge_id 但有 documents 字段的记忆
                # 直接从 metadata.documents 中提取文档信息
                docs_list = metadata.get('documents', [])
                for doc_item in docs_list:
                    doc_title = doc_item.get('title', '未知')
                    doc_url = doc_item.get('url', '')
                    doc_description = doc_item.get('description', '')
                    
                    # 如果有搜索关键词，进行过滤
                    if query:
                        if query.lower() not in doc_title.lower() and query.lower() not in doc_description.lower():
                            continue
                    
                    documents.append(DocumentMemoryItem(
                        title=doc_title,
                        url=doc_url,
                        source=metadata.get('source', '未知'),
                        description=doc_description[:500] if doc_description else None,
                        created_at=str(row['created_at']),
                        task_id=metadata.get('task_id'),
                        project_id=metadata.get('project_id')
                    ))
            elif metadata.get('doc_title'):
                # 兼容旧格式：直接有 doc_title 字段
                documents.append(DocumentMemoryItem(
                    title=metadata.get('doc_title', '未知'),
                    url=metadata.get('doc_url', ''),
                    source=metadata.get('source', '未知'),
                    description=None,
                    created_at=str(row['created_at']),
                    task_id=metadata.get('task_id'),
                    project_id=metadata.get('project_id')
                ))
        
        # ============================================================
        # 步骤 3：如果没有 knowledge_id，直接搜索 knowledge 表
        # 兼容旧数据或直接查询 knowledge 表
        # ============================================================
        if query and len(documents) < limit:
            # 使用向量搜索 knowledge 表
            try:
                knowledge_results = await knowledge_service.search(
                    query=query,
                    source=source,
                    limit=limit - len(documents)
                )
                
                # 转换为文档格式
                for doc in knowledge_results:
                    doc_url = doc.get('metadata', {}).get('url', '')
                    # 去重
                    if doc_url and any(d.url == doc_url for d in documents):
                        continue
                    
                    documents.append(DocumentMemoryItem(
                        title=doc.get('title', '未知'),
                        url=doc_url,
                        source=doc.get('source', '未知'),
                        description=doc.get('content', '')[:500] if doc.get('content') else None,
                        created_at=str(doc.get('created_at', '')),
                        task_id=doc.get('metadata', {}).get('task_id'),
                        project_id=doc.get('metadata', {}).get('project_id')
                    ))
            except Exception as e:
                logger.warning(f"搜索 knowledge 表失败: {e}")
        
        # ============================================================
        # 去重（按 URL）
        # ============================================================
        seen_urls = set()
        unique_documents = []
        for doc in documents:
            if doc.url not in seen_urls or not doc.url:
                seen_urls.add(doc.url)
                unique_documents.append(doc)
        
        # 限制返回数量
        unique_documents = unique_documents[:limit]
        
        return DocumentMemoriesResponse(
            documents=unique_documents,
            total=len(unique_documents),
            query=query
        )
    
    except Exception as e:
        logger.error(f"查询文档记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )