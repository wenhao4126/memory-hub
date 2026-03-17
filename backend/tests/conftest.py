# ============================================================
# 多智能体记忆中枢 - 测试配置
# ============================================================
# 功能：pytest 配置和 fixtures
# 作者：小码
# 日期：2026-03-05
# ============================================================

import pytest
import pytest_asyncio
import asyncpg
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock 数据库连接
@pytest_asyncio.fixture
async def mock_db():
    """Mock 数据库连接池"""
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    
    # 模拟连接获取
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    # 模拟常用数据库操作
    mock_conn.fetchval = AsyncMock(return_value="test-uuid-1234")
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.execute = AsyncMock(return_value="UPDATE 1")
    
    with patch('app.database.db') as mock_database:
        mock_database.pool = mock_pool
        mock_database.fetchval = mock_conn.fetchval
        mock_database.fetchrow = mock_conn.fetchrow
        mock_database.fetch = mock_conn.fetch
        mock_database.execute = mock_conn.execute
        yield mock_database


@pytest.fixture
def sample_agent_data():
    """示例智能体数据"""
    return {
        "name": "TestAgent",
        "description": "测试智能体",
        "capabilities": ["对话", "分析"],
        "metadata": {"version": "1.0"}
    }


@pytest.fixture
def sample_memory_data():
    """示例记忆数据"""
    return {
        "agent_id": "12345678-1234-5678-1234-567812345678",
        "content": "用户喜欢简洁的回答",
        "memory_type": "preference",
        "importance": 0.8,
        "tags": ["用户偏好", "沟通风格"],
        "metadata": {}
    }


@pytest.fixture
def sample_embedding():
    """示例 1536 维向量"""
    return [0.1] * 1536