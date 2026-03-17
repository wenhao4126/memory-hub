# ============================================================
# 多智能体记忆中枢 - 数据库连接
# ============================================================
# 功能：管理数据库连接池和会话
# 作者：小码
# 日期：2026-03-05
# ============================================================

import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager

from .config import settings

logger = logging.getLogger(__name__)

# 尝试导入 tenacity 库用于重试机制
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    logger.warning("tenacity 库未安装，数据库连接重试功能已禁用。安装方法: pip install tenacity")


class Database:
    """数据库连接管理器"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """建立数据库连接池（带重试机制）"""
        if self.pool is not None:
            return
        
        max_retries = 3
        retry_delay = 1  # 初始重试延迟（秒）
        
        for attempt in range(1, max_retries + 1):
            try:
                self.pool = await asyncpg.create_pool(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    database=settings.DB_NAME,
                    min_size=5,
                    max_size=20,
                    command_timeout=60
                )
                logger.info(
                    f"✅ 数据库连接池已建立: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
                )
                return
            except Exception as e:
                logger.warning(
                    f"数据库连接失败 (尝试 {attempt}/{max_retries}): {e}"
                )
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error(f"数据库连接失败，已达到最大重试次数")
                    raise
    
    async def disconnect(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("🔴 数据库连接池已关闭")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        if self.pool is None:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args):
        """执行 SQL 命令"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """查询多行"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """查询单行"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """查询单个值"""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)


# 全局数据库实例
db = Database()