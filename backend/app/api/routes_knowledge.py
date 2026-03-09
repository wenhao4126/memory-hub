# ============================================================
# 知识库管理 API
# ============================================================
# 功能：知识的增删改查和向量搜索
# 作者：小码
# 日期：2026-03-07
# ============================================================

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import uuid
import httpx
import logging
import json

from ..database import db
from ..config import settings
from ..models.schemas import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 辅助函数
# ============================================================

def process_knowledge_row(row: dict) -> dict:
    """处理知识行数据，转换类型"""
    result = dict(row)
    # 处理 metadata：asyncpg 可能返回字符串
    if isinstance(result.get('metadata'), str):
        try:
            result['metadata'] = json.loads(result['metadata'])
        except json.JSONDecodeError:
            result['metadata'] = {}
    return result


# ============================================================
# Embedding 辅助函数
# ============================================================

async def get_embedding(text: str) -> List[float]:
    """
    调用 DashScope API 生成文本向量
    
    Args:
        text: 需要生成向量的文本
        
    Returns:
        1024 维向量列表
        
    Raises:
        HTTPException: API 调用失败时抛出
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
                headers={
                    "Authorization": f"Bearer {settings.DASHSCOPE_EMBEDDING_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "text-embedding-v4",
                    "input": {"texts": [text]},
                    "parameters": {"text_type": "document"}
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Embedding API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"向量生成失败: {response.status_code}"
                )
            
            result = response.json()
            embedding = result["output"]["embeddings"][0]["embedding"]
            return embedding
            
    except httpx.TimeoutException:
        logger.error("Embedding API timeout")
        raise HTTPException(status_code=504, detail="向量生成超时")
    except Exception as e:
        logger.error(f"Embedding API error: {e}")
        raise HTTPException(status_code=500, detail=f"向量生成失败: {str(e)}")


# ============================================================
# CRUD 操作
# ============================================================

@router.post(
    "/knowledge",
    response_model=KnowledgeResponse,
    status_code=201,
    tags=["知识库"]
)
async def create_knowledge(knowledge: KnowledgeCreate):
    """
    创建知识
    
    自动生成向量嵌入并存储到数据库。
    """
    logger.info(f"创建知识: {knowledge.title}")
    
    async with db.pool.acquire() as conn:
        # 检查 agent 是否存在
        agent_exists = await conn.fetchval(
            "SELECT id FROM agents WHERE id = $1",
            knowledge.agent_id
        )
        if not agent_exists:
            raise HTTPException(status_code=404, detail="智能体不存在")
        
        # 生成向量
        text_for_embedding = f"{knowledge.title}\n{knowledge.content[:1000]}"
        embedding = await get_embedding(text_for_embedding)
        
        # 转换向量为 PostgreSQL 格式
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # 转换 metadata 为 JSON 字符串
        metadata_json = json.dumps(knowledge.metadata)
        
        # 插入数据库
        row = await conn.fetchrow(
            """
            INSERT INTO knowledge (
                agent_id, title, content, category, tags, source, embedding, importance, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7::vector, $8, $9::jsonb)
            RETURNING *
            """,
            knowledge.agent_id,
            knowledge.title,
            knowledge.content,
            knowledge.category,
            knowledge.tags,
            knowledge.source,
            embedding_str,
            knowledge.importance,
            metadata_json
        )
        
        logger.info(f"知识创建成功: {row['id']}")
        return process_knowledge_row(row)


@router.get(
    "/knowledge",
    response_model=List[KnowledgeResponse],
    tags=["知识库"]
)
async def list_knowledge(
    agent_id: Optional[uuid.UUID] = None,
    category: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    查询知识列表
    
    支持按智能体和分类筛选。
    """
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
        return [process_knowledge_row(row) for row in rows]


@router.get(
    "/knowledge/{knowledge_id}",
    response_model=KnowledgeResponse,
    tags=["知识库"]
)
async def get_knowledge(knowledge_id: uuid.UUID):
    """查询知识详情"""
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM knowledge WHERE id = $1",
            knowledge_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="知识不存在")
        return process_knowledge_row(row)


@router.put(
    "/knowledge/{knowledge_id}",
    response_model=KnowledgeResponse,
    tags=["知识库"]
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
            text_for_embedding = f"{new_title}\n{new_content[:1000]}"
            embedding = await get_embedding(text_for_embedding)
            embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # 转换 metadata 为 JSON 字符串
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
        return process_knowledge_row(row)


@router.delete(
    "/knowledge/{knowledge_id}",
    status_code=204,
    tags=["知识库"]
)
async def delete_knowledge(knowledge_id: uuid.UUID):
    """删除知识"""
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM knowledge WHERE id = $1",
            knowledge_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="知识不存在")


# ============================================================
# 向量搜索
# ============================================================

@router.post(
    "/knowledge/search/text",
    response_model=List[KnowledgeSearchResponse],
    tags=["知识库"]
)
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    向量搜索知识
    
    使用余弦距离进行语义相似性搜索。
    """
    logger.info(f"知识搜索: {request.query}")
    
    async with db.pool.acquire() as conn:
        # 生成查询向量
        query_embedding = await get_embedding(request.query)
        query_embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # 向量搜索
        rows = await conn.fetch(
            """
            SELECT 
                id, agent_id, title, content, category, tags, source,
                1 - (embedding <=> $1::vector) AS similarity
            FROM knowledge
            WHERE ($2::uuid IS NULL OR agent_id = $2)
              AND ($3::text IS NULL OR category = $3)
              AND 1 - (embedding <=> $1::vector) >= $4
            ORDER BY similarity DESC
            LIMIT $5
            """,
            query_embedding_str,
            request.agent_id,
            request.category,
            request.match_threshold,
            request.match_count
        )
        
        logger.info(f"搜索结果: {len(rows)} 条")
        return [process_knowledge_row(row) for row in rows]