# ============================================================
# 幂等键服务
# ============================================================
# 功能：为批量接口提供 idempotency_key 去重能力
# 说明：使用 PostgreSQL 表持久化请求摘要和响应
# ============================================================

import asyncio
import hashlib
import json
import logging
from typing import Any, Optional

from ..database import db

logger = logging.getLogger(__name__)


class IdempotencyService:
    """幂等服务（数据库持久化）"""

    def __init__(self):
        self._table_ready = False
        self._lock = asyncio.Lock()

    async def _ensure_table(self):
        if self._table_ready:
            return

        async with self._lock:
            if self._table_ready:
                return

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS api_idempotency (
                    endpoint VARCHAR(255) NOT NULL,
                    idempotency_key VARCHAR(128) NOT NULL,
                    request_hash VARCHAR(64) NOT NULL,
                    response_data JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (endpoint, idempotency_key)
                )
                """
            )
            self._table_ready = True
            logger.info("api_idempotency 表已就绪")

    @staticmethod
    def _hash_payload(payload: Any) -> str:
        data = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    async def get_cached_response(
        self,
        endpoint: str,
        idempotency_key: str,
        payload: Any,
    ) -> Optional[dict]:
        """获取已缓存响应；若 key 被复用但请求体不同，抛 ValueError"""
        await self._ensure_table()

        req_hash = self._hash_payload(payload)
        row = await db.fetchrow(
            """
            SELECT request_hash, response_data
            FROM api_idempotency
            WHERE endpoint = $1 AND idempotency_key = $2
            """,
            endpoint,
            idempotency_key,
        )

        if not row:
            return None

        if row["request_hash"] != req_hash:
            raise ValueError("idempotency_key 已被用于不同请求，请更换新的 idempotency_key")

        return dict(row["response_data"]) if row["response_data"] else None

    async def save_response(
        self,
        endpoint: str,
        idempotency_key: str,
        payload: Any,
        response_data: dict,
    ) -> None:
        """保存幂等响应"""
        await self._ensure_table()

        req_hash = self._hash_payload(payload)
        await db.execute(
            """
            INSERT INTO api_idempotency (endpoint, idempotency_key, request_hash, response_data)
            VALUES ($1, $2, $3, $4::jsonb)
            ON CONFLICT (endpoint, idempotency_key)
            DO UPDATE SET response_data = EXCLUDED.response_data
            """,
            endpoint,
            idempotency_key,
            req_hash,
            json.dumps(response_data, ensure_ascii=False),
        )


idempotency_service = IdempotencyService()
