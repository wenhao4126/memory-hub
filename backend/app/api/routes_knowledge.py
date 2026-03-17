# ============================================================
# 知识库管理 API
# ============================================================
# 功能：知识的增删改查和向量搜索
# 作者：小码 🟡
# 日期：2026-03-07
# 更新：2026-03-16 - 使用 KnowledgeService 重构
#
# ⚠️ 架构说明（憨货决策）：
#   - knowledge 表：存储文档内容/地址
#   - shared_memories 表：存储引用（knowledge_id）
#   - 此 API 直接查询 knowledge 表
# ============================================================

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import uuid
import logging

from ..database import db
from ..config import settings
from ..models.schemas import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse
)
from ..services.knowledge_service import knowledge_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 辅助函数
# ============================================================

def process_knowledge_row(row: dict) -> dict:
    """处理知识行数据，转换类型"""
    result = dict(row)
    # 处理 metadata：asyncpg 可能返回字符串
    import json
    if isinstance(result.get('metadata'), str):
        try:
            result['metadata'] = json.loads(result['metadata'])
        except json.JSONDecodeError:
            result['metadata'] = {}
    return result


# ============================================================
# CRUD 操作
# ============================================================

@router.post(
    "/knowledge",
    response_model=KnowledgeResponse,
    status_code=201,
    tags=["知识库"],
    summary="创建知识",
    description="""
    创建新的知识记录
    
    自动生成向量嵌入并存储到数据库。
    """
)
async def create_knowledge(knowledge: KnowledgeCreate):
    """
    创建知识
    
    自动生成向量嵌入并存储到数据库。
    使用 KnowledgeService 处理。
    """
    logger.info(f"创建知识: {knowledge.title}")
    
    # 使用 KnowledgeService 创建知识
    knowledge_id = await knowledge_service.create(
        title=knowledge.title,
        content=knowledge.content,
        source=knowledge.source or str(knowledge.agent_id),
        category=knowledge.category,
        tags=knowledge.tags,
        metadata=knowledge.metadata
    )
    
    # 获取创建的知识详情
    result = await knowledge_service.get(knowledge_id)
    
    logger.info(f"知识创建成功: {knowledge_id}")
    return KnowledgeResponse(**result)


@router.get(
    "/knowledge",
    response_model=List[KnowledgeResponse],
    tags=["知识库"],
    summary="查询知识列表",
    description="""
    查询知识列表
    
    支持按智能体、分类、来源筛选。
    
    **参数**:
    - **agent_id**: 智能体 ID（可选）
    - **category**: 分类过滤（可选）
    - **source**: 来源过滤，如 "小搜"、"小码"（可选）
    - **limit**: 返回数量（默认 50）
    - **offset**: 偏移量（用于分页）
    """
)
async def list_knowledge(
    agent_id: Optional[uuid.UUID] = None,
    category: Optional[str] = None,
    source: Optional[str] = Query(default=None, description="来源过滤，如 '小搜'"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    查询知识列表
    
    支持按智能体、分类、来源筛选。
    """
    # 如果指定了 source，使用 KnowledgeService
    if source:
        results = await knowledge_service.list_by_source(
            source=source,
            limit=limit,
            offset=offset
        )
        return [KnowledgeResponse(**r) for r in results]
    
    # 否则使用原有的数据库查询
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM knowledge
            WHERE ($1::uuid IS NULL OR agent_id = $1)
              AND ($2::text IS NULL OR category = $2)
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """,
            agent_id, category, limit, offset
        )
        return [KnowledgeResponse(**process_knowledge_row(row)) for row in rows]


# ============================================================
# ⚠️ 重要：固定路由必须放在动态路由（/{id}）前面！
# 否则 "search"、"statistics" 会被误解析为 knowledge_id
# ============================================================

@router.get(
    "/knowledge/search",
    response_model=List[KnowledgeSearchResponse],
    tags=["知识库"],
    summary="向量搜索知识（GET）",
    description="""
    向量搜索知识
    
    使用余弦距离进行语义相似性搜索。
    
    **参数**:
    - **query**: 搜索关键词
    - **category**: 分类过滤（可选）
    - **source**: 来源过滤，如 "小搜"、"小码"（可选）
    - **limit**: 返回数量（默认 10）
    - **threshold**: 相似度阈值（默认 0.3）
    """
)
async def search_knowledge_get(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    category: Optional[str] = Query(default=None, description="分类过滤"),
    source: Optional[str] = Query(default=None, description="来源过滤"),
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    threshold: float = Query(default=0.3, ge=0.0, le=1.0, description="相似度阈值")
):
    """
    向量搜索知识（GET 请求）
    
    更符合 REST 风格的搜索接口。
    """
    logger.info(f"知识搜索: {query}")
    
    # 使用 KnowledgeService 搜索
    results = await knowledge_service.search(
        query=query,
        category=category,
        source=source,
        limit=limit,
        match_threshold=threshold
    )
    
    logger.info(f"搜索结果: {len(results)} 条")
    
    return [
        KnowledgeSearchResponse(
            id=r['id'],
            agent_id=r['agent_id'],
            title=r['title'],
            content=r['content'],
            category=r.get('category'),
            tags=r.get('tags'),
            source=r.get('source'),
            similarity=r.get('similarity', 0)
        )
        for r in results
    ]


@router.get(
    "/knowledge/statistics",
    tags=["知识库"],
    summary="知识统计",
    description="""
    获取知识库统计信息
    
    **参数**:
    - **source**: 来源过滤（可选）
    
    **返回**:
    - 总数量、分类数、来源数
    """
)
async def get_knowledge_statistics(
    source: Optional[str] = Query(default=None, description="来源过滤")
):
    """获取知识统计信息"""
    stats = await knowledge_service.get_statistics(source=source)
    
    return {
        "total": stats.get('total', 0),
        "categories": stats.get('categories', 0),
        "sources": stats.get('sources', 0),
        "source_filter": source
    }


# ============================================================
# 动态路由（/{id}）放在最后
# ============================================================

@router.get(
    "/knowledge/{knowledge_id}",
    response_model=KnowledgeResponse,
    tags=["知识库"],
    summary="查询知识详情",
    description="根据 ID 查询知识详情"
)
async def get_knowledge(knowledge_id: uuid.UUID):
    """查询知识详情"""
    # 使用 KnowledgeService 获取
    result = await knowledge_service.get(knowledge_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="知识不存在")
    
    return KnowledgeResponse(**result)


@router.put(
    "/knowledge/{knowledge_id}",
    response_model=KnowledgeResponse,
    tags=["知识库"],
    summary="更新知识",
    description="更新知识内容和元数据"
)
async def update_knowledge(
    knowledge_id: uuid.UUID,
    knowledge: KnowledgeUpdate
):
    """更新知识"""
    async with db.pool.acquire() as conn:
        # 检查是否存在
        existing = await conn.fetchrow(
            "SELECT * FROM knowledge WHERE id = $1",
            knowledge_id
        )
        if not existing:
            raise HTTPException(status_code=404, detail="知识不存在")
        
        # 准备更新数据
        new_title = knowledge.title or existing['title']
        new_content = knowledge.content or existing['content']
        new_category = knowledge.category if knowledge.category is not None else existing['category']
        new_tags = knowledge.tags if knowledge.tags is not None else existing['tags']
        new_importance = knowledge.importance if knowledge.importance is not None else existing['importance']
        new_metadata = knowledge.metadata if knowledge.metadata is not None else existing['metadata']
        
        # 如果内容改变，重新生成向量
        embedding_str = None
        if knowledge.content or knowledge.title:
            # 使用 KnowledgeService 的 embedding
            from ..services.embedding_service import embedding_service
            text_for_embedding = f"{new_title}\n{new_content[:1000]}"
            embedding = await embedding_service.get_embedding(text_for_embedding)
            embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # 转换 metadata 为 JSON 字符串
        import json
        new_metadata_json = json.dumps(new_metadata)
        
        # 更新
        if embedding_str:
            row = await conn.fetchrow(
                """
                UPDATE knowledge
                SET title = $2,
                    content = $3,
                    category = $4,
                    tags = $5,
                    embedding = $6::vector,
                    importance = $7,
                    metadata = $8::jsonb
                WHERE id = $1
                RETURNING *
                """,
                knowledge_id,
                new_title,
                new_content,
                new_category,
                new_tags,
                embedding_str,
                new_importance,
                new_metadata_json
            )
        else:
            row = await conn.fetchrow(
                """
                UPDATE knowledge
                SET title = $2,
                    content = $3,
                    category = $4,
                    tags = $5,
                    importance = $6,
                    metadata = $7::jsonb
                WHERE id = $1
                RETURNING *
                """,
                knowledge_id,
                new_title,
                new_content,
                new_category,
                new_tags,
                new_importance,
                new_metadata_json
            )
        return KnowledgeResponse(**process_knowledge_row(row))


@router.delete(
    "/knowledge/{knowledge_id}",
    status_code=204,
    tags=["知识库"],
    summary="删除知识",
    description="删除知识记录"
)
async def delete_knowledge(knowledge_id: uuid.UUID):
    """删除知识"""
    # 使用 KnowledgeService 删除
    success = await knowledge_service.delete(knowledge_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="知识不存在")


# ============================================================
# 向量搜索（POST 方法）
# 注意：GET 方法的 /knowledge/search 已移到文件前面
# ============================================================

@router.post(
    "/knowledge/search/text",
    response_model=List[KnowledgeSearchResponse],
    tags=["知识库"],
    summary="向量搜索知识（POST）",
    description="""
    向量搜索知识
    
    使用余弦距离进行语义相似性搜索。
    """
)
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    向量搜索知识（POST 请求）
    
    使用余弦距离进行语义相似性搜索。
    """
    logger.info(f"知识搜索: {request.query}")
    
    # 使用 KnowledgeService 搜索
    results = await knowledge_service.search(
        query=request.query,
        category=request.category,
        source=str(request.agent_id) if request.agent_id else None,
        limit=request.match_count,
        match_threshold=request.match_threshold
    )
    
    logger.info(f"搜索结果: {len(results)} 条")
    
    return [
        KnowledgeSearchResponse(
            id=r['id'],
            agent_id=r['agent_id'],
            title=r['title'],
            content=r['content'],
            category=r.get('category'),
            tags=r.get('tags'),
            source=r.get('source'),
            similarity=r.get('similarity', 0)
        )
        for r in results
    ]


# ============================================================
# 文档文件操作
# ============================================================

from ..services.document_storage_service import document_storage_service


@router.get(
    "/knowledge/{knowledge_id}/file",
    tags=["知识库"],
    summary="读取知识文档文件",
    description="""
    读取知识对应的 .md 文档文件
    
    如果知识的 metadata 中包含 file_path，则读取并返回文件内容。
    
    **返回**:
    - file_path: 文件路径
    - content: 文件内容
    """
)
async def get_knowledge_file(knowledge_id: uuid.UUID):
    """
    读取知识文档文件
    
    从 knowledge 表获取 metadata.file_path，读取对应的 .md 文件。
    """
    # 获取知识详情
    knowledge = await knowledge_service.get(knowledge_id)
    
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识不存在")
    
    # 从 metadata 获取文件路径
    metadata = knowledge.get('metadata', {})
    file_path = metadata.get('file_path')
    
    if not file_path:
        raise HTTPException(
            status_code=404, 
            detail="该知识没有对应的文档文件（metadata.file_path 不存在）"
        )
    
    # 读取文件
    try:
        content = document_storage_service.read_document(file_path)
        
        return {
            "knowledge_id": str(knowledge_id),
            "title": knowledge.get('title'),
            "file_path": file_path,
            "content": content,
            "size": len(content)
        }
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"文档文件不存在：{file_path}"
        )
    
    except Exception as e:
        logger.error(f"读取文档文件失败：{e}")
        raise HTTPException(
            status_code=500,
            detail=f"读取文档文件失败：{str(e)}"
        )


@router.get(
    "/documents",
    tags=["文档文件"],
    summary="列出所有文档文件",
    description="""
    列出存储目录中的所有 .md 文档文件
    
    **参数**:
    - **limit**: 返回数量（默认 50）
    - **offset**: 偏移量（用于分页）
    """
)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """列出所有文档文件"""
    documents = document_storage_service.list_documents(limit=limit, offset=offset)
    
    return {
        "total": len(documents),
        "documents": documents,
        "storage_dir": document_storage_service.storage_dir
    }


@router.get(
    "/documents/{filename}",
    tags=["文档文件"],
    summary="读取文档文件",
    description="""
    根据文件名读取文档文件内容
    
    **参数**:
    - **filename**: 文件名（如 20260316_144000_标题.md）
    """
)
async def read_document(filename: str):
    """读取指定的文档文件"""
    # 获取完整路径
    file_path = document_storage_service.get_document_path(filename)
    
    try:
        content = document_storage_service.read_document(file_path)
        
        return {
            "filename": filename,
            "file_path": file_path,
            "content": content,
            "size": len(content)
        }
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"文档文件不存在：{filename}"
        )
    
    except Exception as e:
        logger.error(f"读取文档文件失败：{filename}, 错误={e}")
        raise HTTPException(
            status_code=500,
            detail=f"读取文档文件失败：{str(e)}"
        )