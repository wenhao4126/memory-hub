# ============================================================
# 多智能体记忆中枢 - 主程序入口
# ============================================================
# 功能：FastAPI 应用初始化和生命周期管理
# 作者：小码
# 日期：2026-03-05
# ============================================================

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from .config import settings
from .database import db
from .api.routes import router
from .api.routes_conversations import router as conversations_router
from .api.routes_knowledge import router as knowledge_router
from .api.routes_memories_dual import router as dual_memories_router
from .api.task_memories import router as task_memories_router
from .api.routes_search import router as search_router
from .auth import verify_api_key
from .rate_limit import limiter, setup_rate_limiting
from .models.schemas import HealthResponse
from .errors import (
    global_exception_handler,
    validation_exception_handler,
    APIException
)


# ============================================================
# 日志配置
# ============================================================
# 日志格式：时间 - 日志级别 - 模块名 - 消息
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 配置根日志记录器
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    handlers=[
        # 输出到控制台
        logging.StreamHandler(),
        # 输出到文件（生产环境可添加）
        # logging.FileHandler("app.log", encoding="utf-8"),
    ]
)

# 设置第三方库日志级别（避免过多日志）
logging.getLogger("asyncpg").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# 获取应用日志记录器
logger = logging.getLogger(__name__)


# ============================================================
# API 分组配置（用于 Swagger UI 排序和展示）
# ============================================================
tags_metadata = [
    {
        "name": "⭐ 推荐接口",
        "description": "🚀 **最常用的接口，推荐优先使用**",
    },
    {
        "name": "对话增强",
        "description": "💬 **基于记忆的智能对话（核心功能）**",
    },
    {
        "name": "智能体管理",
        "description": "🤖 **智能体的增删改查操作**",
    },
    {
        "name": "记忆管理",
        "description": "💾 **记忆的增删改查操作**",
    },
    {
        "name": "搜索",
        "description": "🔍 **向量相似性搜索**",
    },
    {
        "name": "自动记忆",
        "description": "🧠 **自动从对话中提取和存储记忆**",
    },
    {
        "name": "对话管理",
        "description": "📝 **对话记录的增删改查操作**",
    },
    {
        "name": "维护",
        "description": "🔧 **系统维护操作**",
    },
    {
        "name": "双表记忆",
        "description": "💾 **双表架构记忆管理（private/shared）**",
    },
    {
        "name": "任务记忆",
        "description": "🔗 **任务与记忆系统集成（Phase 3）**",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时：建立数据库连接
    关闭时：断开数据库连接
    """
    # 启动
    print("🚀 多智能体记忆中枢启动中...")
    await db.connect()
    
    yield
    
    # 关闭
    print("👋 多智能体记忆中枢关闭中...")
    await db.disconnect()


# 创建 FastAPI 应用
app = FastAPI(
    title="多智能体记忆中枢",
    description="""
    为智能体提供统一的记忆存储和检索服务。
    
    ## 核心功能
    
    * 🤖 **智能体管理**：注册和管理多个智能体
    * 💾 **记忆存储**：支持多种记忆类型的事实、偏好、技能、经验
    * 🔍 **向量搜索**：基于语义相似度的智能检索
    * 🔄 **记忆遗忘**：基于重要性和访问频率的自动清理
    * 🔐 **API 认证**：基于 API Key 的安全认证
    * ⚡ **请求限流**：防止滥用和过载
    
    ## 快速开始
    
    1. **创建智能体** → `POST /api/v1/agents`
    2. **创建记忆** → `POST /api/v1/memories`
    3. **搜索记忆** → `POST /api/v1/memories/search/text`
    
    ## API 认证
    
    所有 API 请求都需要在请求头中提供 API Key：
    ```
    X-API-Key: your_api_key_here
    ```
    
    ## 限流规则
    
    * 默认限制：60 次/分钟
    * 每小时限制：1000 次
    * 超过限制将返回 429 错误
    
    ## 技术栈
    
    * FastAPI + asyncpg（异步高性能）
    * PostgreSQL + pgvector（向量搜索）
    * Docker 容器化部署
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    # Swagger UI 配置：默认展开所有操作
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "displayOperationId": False,
        "filter": True,  # 启用搜索过滤
        "showExtensions": True,
        "showCommonExtensions": True,
    }
)


# ============================================================
# 全局异常处理器 - 统一错误响应格式
# ============================================================
from fastapi.exceptions import RequestValidationError

# 注册全局异常处理器
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(APIException, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# CORS 中间件配置
# 安全说明：生产环境应限制允许的来源，而非使用 "*"
# 通过 ALLOWED_ORIGINS 环境变量配置（多个用逗号分隔）
# 示例：ALLOWED_ORIGINS=http://localhost:3000,https://example.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# 配置限流中间件（必须在 CORS 之后，路由之前）
setup_rate_limiting(app)

# 注册路由
# 注意：具体路由（如 /memories/documents）必须在参数路由（如 /memories/{memory_id}）之前注册

# 健康检查端点（不需要认证）
@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["⭐ 推荐接口"],
    summary="健康检查",
    description="检查服务是否正常运行，包括数据库连接状态"
)
async def health_check():
    """
    健康检查端点（不需要 API Key）
    
    用于检查服务是否正常运行
    """
    try:
        # 测试数据库连接
        await db.fetchval("SELECT 1")
        return HealthResponse(database="connected")
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(database=f"error: {str(e)}")

app.include_router(task_memories_router, prefix="/api/v1")  # Phase 3: 任务记忆路由（先注册具体路由）
app.include_router(router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(dual_memories_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")  # Phase 3: 搜索集成路由


# 限流测试端点（用于测试限流功能）
@app.get("/api/v1/test-rate-limit")
@limiter.limit("5/minute")  # 严格限流：5 次/分钟
async def test_rate_limit(request: Request):
    """
    限流测试端点
    
    用于测试限流功能是否正常工作
    限制：5 次/分钟
    """
    return {"message": "OK", "limit": "5/minute", "endpoint": "test-rate-limit"}


@app.get("/")
async def root():
    """根路径，返回欢迎信息"""
    return {
        "message": "多智能体记忆中枢 API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG
    )