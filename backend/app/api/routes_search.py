# ============================================================
# 搜索 API
# ============================================================
# 功能：集成搜索服务，搜索结果自动保存到知识库
# 作者：小码 🟡
# 日期：2026-03-16
#
# ⚠️ 架构说明（憨货决策）：
#   小搜搜索到的文档处理流程：
#   1. 执行搜索
#   2. 抓取文档内容
#   3. 保存为 .md 文件
#   4. 存入 knowledge 表
#
# API：
#   POST /api/v1/search - 执行搜索并保存结果
#   GET /api/v1/search/history - 查看搜索历史
# ============================================================

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from ..services.search_integration_service import search_integration_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 数据模型
# ============================================================

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, max_length=500, description="搜索关键词")
    max_results: int = Field(default=5, ge=1, le=20, description="最多返回结果数")
    source: str = Field(default="小搜", description="来源标识")
    agent_id: Optional[str] = Field(default=None, description="智能体 ID（用于创建记忆引用）")


class SearchResultItem(BaseModel):
    """单个搜索结果"""
    title: str
    url: str
    snippet: str
    knowledge_id: Optional[str] = None
    file_path: Optional[str] = None
    memory_id: Optional[str] = None
    status: str = "pending"


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    total: int
    success_count: int
    failed_count: int
    results: List[SearchResultItem]


# ============================================================
# 搜索 API
# ============================================================

@router.post(
    "/search",
    response_model=SearchResponse,
    tags=["搜索"],
    summary="执行搜索并保存结果",
    description="""
    执行搜索并自动保存结果到知识库
    
    处理流程：
    1. 执行搜索（使用 DuckDuckGo）
    2. 抓取每个结果的文档内容
    3. 保存为 .md 文件
    4. 存入 knowledge 表
    
    **请求体**:
    - **query**: 搜索关键词
    - **max_results**: 最多返回结果数（默认 5，最大 20）
    - **source**: 来源标识（默认"小搜"）
    - **agent_id**: 智能体 ID（可选，用于创建记忆引用）
    """
)
async def search_and_save(request: SearchRequest):
    """
    执行搜索并保存结果到知识库
    
    使用 DuckDuckGo 搜索，结果自动保存为 .md 文件并存入 knowledge 表。
    """
    logger.info(f"搜索请求：{request.query}")
    
    try:
        # ============================================================
        # 执行搜索
        # ============================================================
        from agents.team_researcher.duckduckgo_search import duck_search
        
        results = duck_search(request.query, max_results=request.max_results)
        
        if not results:
            logger.warning(f"搜索无结果：{request.query}")
            return SearchResponse(
                query=request.query,
                total=0,
                success_count=0,
                failed_count=0,
                results=[]
            )
        
        logger.info(f"搜索完成：{len(results)} 条结果")
        
        # ============================================================
        # 处理搜索结果（保存到知识库）
        # ============================================================
        import uuid
        agent_id = uuid.UUID(request.agent_id) if request.agent_id else None
        
        processed_results = await search_integration_service.process_search_results(
            results=results,
            query=request.query,
            source=request.source,
            agent_id=agent_id
        )
        
        # ============================================================
        # 构建响应
        # ============================================================
        success_count = sum(1 for r in processed_results if r['status'] == 'success')
        failed_count = len(processed_results) - success_count
        
        return SearchResponse(
            query=request.query,
            total=len(processed_results),
            success_count=success_count,
            failed_count=failed_count,
            results=[SearchResultItem(**r) for r in processed_results]
        )
    
    except Exception as e:
        logger.error(f"搜索失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败：{str(e)}")


@router.get(
    "/search",
    response_model=SearchResponse,
    tags=["搜索"],
    summary="执行搜索并保存结果（GET）",
    description="""
    执行搜索并自动保存结果到知识库（GET 请求）
    
    **参数**:
    - **query**: 搜索关键词
    - **max_results**: 最多返回结果数（默认 5，最大 20）
    - **source**: 来源标识（默认"小搜"）
    """
)
async def search_and_save_get(
    query: str = Query(..., min_length=1, max_length=500, description="搜索关键词"),
    max_results: int = Query(default=5, ge=1, le=20, description="最多返回结果数"),
    source: str = Query(default="小搜", description="来源标识")
):
    """
    执行搜索并保存结果到知识库（GET 请求）
    """
    request = SearchRequest(
        query=query,
        max_results=max_results,
        source=source
    )
    
    return await search_and_save(request)