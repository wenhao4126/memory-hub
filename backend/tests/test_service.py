# ============================================================
# 多智能体记忆中枢 - 服务层测试
# ============================================================
# 功能：测试 MemoryService 业务逻辑
# 作者：小码
# 日期：2026-03-05
# ============================================================

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime

from app.services.memory_service import MemoryService
from app.models.schemas import (
    MemoryCreate,
    MemoryUpdate,
    MemorySearchRequest,
    MemoryType
)


# 辅助函数：创建模拟的数据库记录
def make_mock_record(data):
    """创建模拟 asyncpg Record 的对象"""
    class MockRecord(dict):
        pass
    return MockRecord(data)


class TestMemoryService:
    """MemoryService 测试"""
    
    @pytest.fixture
    def memory_service(self):
        """创建服务实例"""
        return MemoryService()
    
    @pytest.fixture
    def sample_memory_create(self):
        """示例记忆创建请求"""
        return MemoryCreate(
            agent_id=uuid.uuid4(),
            content="测试记忆内容",
            memory_type=MemoryType.FACT,
            importance=0.5,
            tags=["测试"],
            metadata={}
        )
    
    @pytest.fixture
    def sample_embedding(self):
        """示例 512 维向量（bge-small-zh-v1.5）"""
        return [0.1] * 512
    
    # ============================================================
    # 创建记忆测试
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_create_memory_success(self, memory_service, sample_memory_create):
        """测试创建记忆成功"""
        memory_id = uuid.uuid4()
        
        with patch('app.services.memory_service.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = memory_id
            
            result = await memory_service.create_memory(sample_memory_create)
            
            assert result == str(memory_id)
            mock_fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_memory_with_embedding(self, memory_service, sample_memory_create, sample_embedding):
        """测试创建带向量的记忆"""
        sample_memory_create.embedding = sample_embedding
        memory_id = uuid.uuid4()
        
        with patch('app.services.memory_service.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = memory_id
            
            result = await memory_service.create_memory(sample_memory_create)
            
            assert result == str(memory_id)
    
    @pytest.mark.asyncio
    async def test_create_memory_with_expires_at(self, memory_service, sample_memory_create):
        """测试创建带过期时间的记忆"""
        sample_memory_create.expires_at = datetime.now()
        memory_id = uuid.uuid4()
        
        with patch('app.services.memory_service.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = memory_id
            
            result = await memory_service.create_memory(sample_memory_create)
            
            assert result == str(memory_id)
    
    # ============================================================
    # 获取记忆测试
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_get_memory_success(self, memory_service):
        """测试获取记忆成功"""
        memory_id = str(uuid.uuid4())
        mock_row = make_mock_record({
            "id": uuid.uuid4(),
            "agent_id": uuid.uuid4(),
            "content": "测试记忆",
            "memory_type": "fact",
            "importance": 0.5,
            "access_count": 1,
            "tags": [],
            "metadata": {},
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "expires_at": None
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = mock_row
            
            result = await memory_service.get_memory(memory_id)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, memory_service):
        """测试获取不存在的记忆"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = None
            
            result = await memory_service.get_memory(memory_id)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_memory_invalid_id(self, memory_service):
        """测试获取记忆无效 ID"""
        result = await memory_service.get_memory("invalid-uuid")
        
        assert result is None
    
    # ============================================================
    # 更新记忆测试
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_update_memory_success(self, memory_service):
        """测试更新记忆成功"""
        memory_id = str(uuid.uuid4())
        memory_uuid = uuid.UUID(memory_id)
        update_data = MemoryUpdate(content="更新后的内容")
        
        # 模拟更新后的记录
        updated_row = make_mock_record({
            "id": memory_uuid,
            "content": "更新后的内容",
            "agent_id": uuid.uuid4(),
            "memory_type": "fact",
            "importance": 0.5,
            "access_count": 1,
            "tags": [],
            "metadata": {},
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "expires_at": None
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            # 第一次调用：获取现有记录
            existing_row = make_mock_record({
                "id": memory_uuid,
                "content": "原始内容"
            })
            # 第二次调用：返回更新后的记录
            mock_fetchrow.side_effect = [existing_row, updated_row]
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            assert result is not None
            assert result["content"] == "更新后的内容"
    
    @pytest.mark.asyncio
    async def test_update_memory_not_found(self, memory_service):
        """测试更新不存在的记忆"""
        memory_id = str(uuid.uuid4())
        update_data = MemoryUpdate(content="更新内容")
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = None
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_memory_multiple_fields(self, memory_service):
        """测试更新多个字段"""
        memory_id = str(uuid.uuid4())
        memory_uuid = uuid.UUID(memory_id)
        update_data = MemoryUpdate(
            content="新内容",
            importance=0.9,
            tags=["新标签"]
        )
        
        updated_row = make_mock_record({
            "id": memory_uuid,
            "content": "新内容",
            "importance": 0.9,
            "tags": ["新标签"],
            "agent_id": uuid.uuid4(),
            "memory_type": "fact",
            "access_count": 1,
            "metadata": {},
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "expires_at": None
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            existing_row = make_mock_record({
                "id": memory_uuid,
                "content": "原始内容"
            })
            
            mock_fetchrow.side_effect = [existing_row, updated_row]
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            assert result is not None
            assert result["content"] == "新内容"
    
    # ============================================================
    # 删除记忆测试
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_delete_memory_success(self, memory_service):
        """测试删除记忆成功"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "DELETE 1"
            
            result = await memory_service.delete_memory(memory_id)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, memory_service):
        """测试删除不存在的记忆"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "DELETE 0"
            
            result = await memory_service.delete_memory(memory_id)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_memory_invalid_id(self, memory_service):
        """测试删除记忆无效 ID"""
        result = await memory_service.delete_memory("invalid-uuid")
        
        assert result is False
    
    # ============================================================
    # 搜索记忆测试
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_search_similar_success(self, memory_service, sample_embedding):
        """测试向量搜索成功"""
        request = MemorySearchRequest(
            query_embedding=sample_embedding
        )
        
        with patch('app.services.memory_service.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            result = await memory_service.search_similar(request)
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_search_similar_with_agent_filter(self, memory_service, sample_embedding):
        """测试带智能体过滤的向量搜索"""
        agent_id = uuid.uuid4()
        request = MemorySearchRequest(
            query_embedding=sample_embedding,
            agent_id=agent_id
        )
        
        with patch('app.services.memory_service.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            result = await memory_service.search_similar(request)
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_search_similar_with_threshold(self, memory_service, sample_embedding):
        """测试带相似度阈值的向量搜索"""
        request = MemorySearchRequest(
            query_embedding=sample_embedding,
            match_threshold=0.8,
            match_count=5
        )
        
        with patch('app.services.memory_service.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            result = await memory_service.search_similar(request)
            
            assert isinstance(result, list)
    
    # ============================================================
    # 列出记忆测试
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_list_memories_by_agent_success(self, memory_service):
        """测试列出智能体记忆成功"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            result = await memory_service.list_memories_by_agent(agent_id)
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_list_memories_by_agent_with_pagination(self, memory_service):
        """测试带分页的列出智能体记忆"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            result = await memory_service.list_memories_by_agent(agent_id, limit=10, offset=5)
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_list_memories_by_agent_invalid_id(self, memory_service):
        """测试列出智能体记忆无效 ID"""
        result = await memory_service.list_memories_by_agent("invalid-uuid")
        
        assert result == []
    
    # ============================================================
    # 清理记忆测试
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_cleanup_old_memories_success(self, memory_service):
        """测试清理过期记忆成功"""
        with patch('app.services.memory_service.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = 5
            
            result = await memory_service.cleanup_old_memories(days_old=30, min_importance=0.3, max_access_count=3)
            
            assert result == 5
    
    @pytest.mark.asyncio
    async def test_cleanup_old_memories_no_matches(self, memory_service):
        """测试清理过期记忆无匹配"""
        with patch('app.services.memory_service.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = 0
            
            result = await memory_service.cleanup_old_memories()
            
            assert result == 0


# ============================================================
# 数据模型验证测试
# ============================================================

class TestMemoryModels:
    """记忆数据模型测试"""
    
    def test_memory_create_valid(self):
        """测试有效的记忆创建请求"""
        memory = MemoryCreate(
            agent_id=uuid.uuid4(),
            content="测试内容"
        )
        
        assert memory.content == "测试内容"
        assert memory.memory_type == MemoryType.FACT
        assert memory.importance == 0.5
    
    def test_memory_create_invalid_embedding(self):
        """测试无效的 embedding 维度"""
        with pytest.raises(ValueError):
            MemoryCreate(
                agent_id=uuid.uuid4(),
                content="测试",
                embedding=[0.1] * 100  # 错误维度
            )
    
    def test_memory_create_invalid_importance(self):
        """测试无效的重要性分数"""
        with pytest.raises(ValueError):
            MemoryCreate(
                agent_id=uuid.uuid4(),
                content="测试",
                importance=1.5  # 超过 1.0
            )
    
    def test_memory_update_partial(self):
        """测试部分更新"""
        update = MemoryUpdate(content="新内容")
        
        assert update.content == "新内容"
        assert update.importance is None
        assert update.tags is None
    
    def test_memory_search_request_valid(self):
        """测试有效的搜索请求"""
        request = MemorySearchRequest(
            query_embedding=[0.1] * 512
        )
        
        assert request.match_threshold == 0.7
        assert request.match_count == 10
    
    def test_memory_search_request_invalid_embedding(self):
        """测试搜索请求无效 embedding"""
        with pytest.raises(ValueError):
            MemorySearchRequest(
                query_embedding=[0.1] * 100  # 错误维度
            )
    
    def test_memory_search_request_invalid_threshold(self):
        """测试搜索请求无效阈值"""
        with pytest.raises(ValueError):
            MemorySearchRequest(
                query_embedding=[0.1] * 512,
                match_threshold=1.5  # 超过 1.0
            )
    
    def test_memory_search_request_invalid_count(self):
        """测试搜索请求无效数量"""
        with pytest.raises(ValueError):
            MemorySearchRequest(
                query_embedding=[0.1] * 512,
                match_count=0  # 最小为 1
            )


# ============================================================
# 补充测试：覆盖更多分支
# ============================================================

class TestMemoryServiceExtended:
    """MemoryService 扩展测试"""
    
    @pytest.fixture
    def memory_service(self):
        """创建服务实例"""
        return MemoryService()
    
    @pytest.fixture
    def sample_memory_create(self):
        """示例记忆创建请求"""
        return MemoryCreate(
            agent_id=uuid.uuid4(),
            content="测试记忆内容",
            memory_type=MemoryType.FACT,
            importance=0.5,
            tags=["测试"],
            metadata={}
        )
    
    @pytest.fixture
    def sample_embedding(self):
        """示例 512 维向量"""
        return [0.1] * 512
    
    @pytest.mark.asyncio
    async def test_update_memory_with_embedding(self, memory_service):
        """测试更新记忆时带向量"""
        memory_id = str(uuid.uuid4())
        memory_uuid = uuid.UUID(memory_id)
        update_data = MemoryUpdate(embedding=[0.2] * 512)
        
        existing_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容"
        })
        
        updated_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容",
            "embedding": [0.2] * 512,
            "agent_id": uuid.uuid4(),
            "memory_type": "fact",
            "importance": 0.5,
            "access_count": 1,
            "tags": [],
            "metadata": {},
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "expires_at": None
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.side_effect = [existing_row, updated_row]
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_memory_with_expires_at(self, memory_service):
        """测试更新记忆时带过期时间"""
        memory_id = str(uuid.uuid4())
        memory_uuid = uuid.UUID(memory_id)
        expires = datetime.now()
        update_data = MemoryUpdate(expires_at=expires)
        
        existing_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容"
        })
        
        updated_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容",
            "expires_at": expires,
            "agent_id": uuid.uuid4(),
            "memory_type": "fact",
            "importance": 0.5,
            "access_count": 1,
            "tags": [],
            "metadata": {},
            "created_at": datetime.now(),
            "last_accessed": datetime.now()
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.side_effect = [existing_row, updated_row]
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_memory_with_metadata(self, memory_service):
        """测试更新记忆时带元数据"""
        memory_id = str(uuid.uuid4())
        memory_uuid = uuid.UUID(memory_id)
        update_data = MemoryUpdate(metadata={"key": "value"})
        
        existing_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容"
        })
        
        updated_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容",
            "metadata": {"key": "value"},
            "agent_id": uuid.uuid4(),
            "memory_type": "fact",
            "importance": 0.5,
            "access_count": 1,
            "tags": [],
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "expires_at": None
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.side_effect = [existing_row, updated_row]
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_memory_with_tags(self, memory_service):
        """测试更新记忆时带标签"""
        memory_id = str(uuid.uuid4())
        memory_uuid = uuid.UUID(memory_id)
        update_data = MemoryUpdate(tags=["新标签1", "新标签2"])
        
        existing_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容"
        })
        
        updated_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容",
            "tags": ["新标签1", "新标签2"],
            "agent_id": uuid.uuid4(),
            "memory_type": "fact",
            "importance": 0.5,
            "access_count": 1,
            "metadata": {},
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "expires_at": None
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.side_effect = [existing_row, updated_row]
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_memory_with_memory_type(self, memory_service):
        """测试更新记忆时带类型"""
        memory_id = str(uuid.uuid4())
        memory_uuid = uuid.UUID(memory_id)
        update_data = MemoryUpdate(memory_type=MemoryType.PREFERENCE)
        
        existing_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容"
        })
        
        updated_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容",
            "memory_type": "preference",
            "agent_id": uuid.uuid4(),
            "importance": 0.5,
            "access_count": 1,
            "tags": [],
            "metadata": {},
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "expires_at": None
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.side_effect = [existing_row, updated_row]
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            assert result is not None
            assert result["memory_type"] == "preference"
    
    @pytest.mark.asyncio
    async def test_update_memory_empty_update(self, memory_service):
        """测试更新记忆时空更新"""
        memory_id = str(uuid.uuid4())
        memory_uuid = uuid.UUID(memory_id)
        update_data = MemoryUpdate()  # 空更新
        
        existing_row = make_mock_record({
            "id": memory_uuid,
            "content": "原始内容",
            "agent_id": uuid.uuid4(),
            "memory_type": "fact",
            "importance": 0.5,
            "access_count": 1,
            "tags": [],
            "metadata": {},
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "expires_at": None
        })
        
        with patch('app.services.memory_service.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = existing_row
            
            result = await memory_service.update_memory(memory_id, update_data)
            
            # 空更新应该返回现有记录
            assert result is not None
            assert result["content"] == "原始内容"
    
    @pytest.mark.asyncio
    async def test_search_by_text_success(self, memory_service, sample_embedding):
        """测试文本搜索成功"""
        from app.models.schemas import MemoryTextSearchRequest
        
        request = MemoryTextSearchRequest(query="测试查询")
        
        with patch('app.services.memory_service.embedding_service.get_embedding', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = sample_embedding
            
            with patch('app.services.memory_service.db.fetch', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = []
                
                result = await memory_service.search_by_text(request)
                
                assert isinstance(result, list)
                mock_embed.assert_called_once_with("测试查询")
    
    @pytest.mark.asyncio
    async def test_search_by_text_with_options(self, memory_service, sample_embedding):
        """测试带选项的文本搜索"""
        from app.models.schemas import MemoryTextSearchRequest
        
        agent_id = uuid.uuid4()
        request = MemoryTextSearchRequest(
            query="测试查询",
            agent_id=agent_id,
            match_threshold=0.9,
            match_count=5
        )
        
        with patch('app.services.memory_service.embedding_service.get_embedding', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = sample_embedding
            
            with patch('app.services.memory_service.db.fetch', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = []
                
                result = await memory_service.search_by_text(request)
                
                assert isinstance(result, list)