# ============================================================
# 多智能体记忆中枢 - 数据模型测试
# ============================================================
# 功能：测试 Pydantic 数据模型验证
# 作者：小码
# 日期：2026-03-06
# ============================================================

import pytest
from pydantic import ValidationError
import uuid

from app.models.schemas import (
    AgentCreate, AgentUpdate, Agent,
    MemoryCreate, MemoryUpdate, Memory,
    MemorySearchRequest, MemoryTextSearchRequest, MemorySearchResult,
    MemoryType, RelationType,
    HealthResponse, MessageResponse, ErrorResponse
)


# ============================================================
# 枚举测试
# ============================================================

class TestEnums:
    """枚举类型测试"""
    
    def test_memory_type_values(self):
        """测试记忆类型枚举值"""
        assert MemoryType.FACT.value == "fact"
        assert MemoryType.PREFERENCE.value == "preference"
        assert MemoryType.SKILL.value == "skill"
        assert MemoryType.EXPERIENCE.value == "experience"
    
    def test_relation_type_values(self):
        """测试关系类型枚举值"""
        assert RelationType.SIMILAR.value == "similar"
        assert RelationType.CONTRADICTS.value == "contradicts"
        assert RelationType.DERIVES_FROM.value == "derives_from"
        assert RelationType.SUPERSEDES.value == "supersedes"


# ============================================================
# 智能体模型测试
# ============================================================

class TestAgentModels:
    """智能体模型测试"""
    
    def test_agent_create_valid(self):
        """测试有效的智能体创建请求"""
        agent = AgentCreate(
            name="TestAgent",
            description="测试智能体",
            capabilities=["对话", "分析"],
            metadata={"version": "1.0"}
        )
        
        assert agent.name == "TestAgent"
        assert agent.description == "测试智能体"
        assert len(agent.capabilities) == 2
        assert agent.metadata["version"] == "1.0"
    
    def test_agent_create_minimal(self):
        """测试最小化的智能体创建请求"""
        agent = AgentCreate(name="Minimal")
        
        assert agent.name == "Minimal"
        assert agent.description is None
        assert agent.capabilities == []
        assert agent.metadata == {}
    
    def test_agent_create_name_required(self):
        """测试智能体名称必填"""
        with pytest.raises(ValidationError):
            AgentCreate(description="无名称智能体")
    
    def test_agent_create_name_too_long(self):
        """测试智能体名称超长"""
        with pytest.raises(ValidationError):
            AgentCreate(name="a" * 256)
    
    def test_agent_create_empty_name(self):
        """测试智能体名称为空"""
        with pytest.raises(ValidationError):
            AgentCreate(name="")
    
    def test_agent_update_partial(self):
        """测试部分更新智能体"""
        update = AgentUpdate(name="NewName")
        
        assert update.name == "NewName"
        assert update.description is None
        assert update.capabilities is None
        assert update.metadata is None
    
    def test_agent_update_empty(self):
        """测试空的更新请求"""
        update = AgentUpdate()
        
        assert update.name is None
        assert update.description is None


# ============================================================
# 记忆模型测试
# ============================================================

class TestMemoryModels:
    """记忆模型测试"""
    
    def test_memory_create_valid(self):
        """测试有效的记忆创建请求"""
        memory = MemoryCreate(
            agent_id=uuid.uuid4(),
            content="测试记忆内容",
            memory_type=MemoryType.FACT,
            importance=0.8,
            tags=["测试", "示例"],
            metadata={"source": "unit_test"}
        )
        
        assert memory.content == "测试记忆内容"
        assert memory.memory_type == MemoryType.FACT
        assert memory.importance == 0.8
        assert len(memory.tags) == 2
    
    def test_memory_create_minimal(self):
        """测试最小化的记忆创建请求"""
        memory = MemoryCreate(
            agent_id=uuid.uuid4(),
            content="最小记忆"
        )
        
        assert memory.content == "最小记忆"
        assert memory.memory_type == MemoryType.FACT  # 默认值
        assert memory.importance == 0.5  # 默认值
        assert memory.tags == []
    
    def test_memory_create_with_embedding(self):
        """测试带向量的记忆创建"""
        embedding = [0.1] * 512  # bge-small-zh-v1.5: 512维
        memory = MemoryCreate(
            agent_id=uuid.uuid4(),
            content="带向量的记忆",
            embedding=embedding
        )
        
        assert memory.embedding == embedding
    
    def test_memory_create_invalid_embedding_dimension(self):
        """测试无效的向量维度"""
        with pytest.raises(ValidationError) as exc_info:
            MemoryCreate(
                agent_id=uuid.uuid4(),
                content="测试",
                embedding=[0.1] * 100  # 错误维度
            )
        
        assert "512" in str(exc_info.value)
    
    def test_memory_create_invalid_importance_high(self):
        """测试重要性分数超过上限"""
        with pytest.raises(ValidationError):
            MemoryCreate(
                agent_id=uuid.uuid4(),
                content="测试",
                importance=1.5
            )
    
    def test_memory_create_invalid_importance_low(self):
        """测试重要性分数低于下限"""
        with pytest.raises(ValidationError):
            MemoryCreate(
                agent_id=uuid.uuid4(),
                content="测试",
                importance=-0.1
            )
    
    def test_memory_create_empty_content(self):
        """测试空内容"""
        with pytest.raises(ValidationError):
            MemoryCreate(
                agent_id=uuid.uuid4(),
                content=""
            )
    
    def test_memory_update_partial(self):
        """测试部分更新记忆"""
        update = MemoryUpdate(
            content="新内容",
            importance=0.9
        )
        
        assert update.content == "新内容"
        assert update.importance == 0.9
        assert update.memory_type is None
        assert update.tags is None
    
    def test_memory_update_with_embedding(self):
        """测试带向量的记忆更新"""
        embedding = [0.2] * 512
        update = MemoryUpdate(embedding=embedding)
        
        assert update.embedding == embedding
    
    def test_memory_update_invalid_embedding(self):
        """测试更新时无效向量维度"""
        with pytest.raises(ValidationError) as exc_info:
            MemoryUpdate(embedding=[0.1] * 200)
        
        assert "512" in str(exc_info.value)


# ============================================================
# 搜索请求模型测试
# ============================================================

class TestSearchModels:
    """搜索请求模型测试"""
    
    def test_memory_search_request_valid(self):
        """测试有效的搜索请求"""
        request = MemorySearchRequest(
            query_embedding=[0.1] * 512
        )
        
        assert len(request.query_embedding) == 512
        assert request.match_threshold == 0.7  # 默认值
        assert request.match_count == 10  # 默认值
    
    def test_memory_search_request_with_options(self):
        """测试带参数的搜索请求"""
        request = MemorySearchRequest(
            query_embedding=[0.1] * 512,
            agent_id=uuid.uuid4(),
            match_threshold=0.8,
            match_count=5
        )
        
        assert request.match_threshold == 0.8
        assert request.match_count == 5
    
    def test_memory_search_request_invalid_embedding(self):
        """测试无效向量维度"""
        with pytest.raises(ValidationError) as exc_info:
            MemorySearchRequest(query_embedding=[0.1] * 100)
        
        assert "512" in str(exc_info.value)
    
    def test_memory_search_request_invalid_threshold_high(self):
        """测试相似度阈值超过上限"""
        with pytest.raises(ValidationError):
            MemorySearchRequest(
                query_embedding=[0.1] * 512,
                match_threshold=1.5
            )
    
    def test_memory_search_request_invalid_threshold_low(self):
        """测试相似度阈值低于下限"""
        with pytest.raises(ValidationError):
            MemorySearchRequest(
                query_embedding=[0.1] * 512,
                match_threshold=-0.1
            )
    
    def test_memory_search_request_invalid_count_zero(self):
        """测试返回数量为0"""
        with pytest.raises(ValidationError):
            MemorySearchRequest(
                query_embedding=[0.1] * 512,
                match_count=0
            )
    
    def test_memory_search_request_invalid_count_high(self):
        """测试返回数量超过上限"""
        with pytest.raises(ValidationError):
            MemorySearchRequest(
                query_embedding=[0.1] * 512,
                match_count=200
            )
    
    def test_memory_text_search_request_valid(self):
        """测试有效的文本搜索请求"""
        request = MemoryTextSearchRequest(query="测试查询")
        
        assert request.query == "测试查询"
        assert request.match_threshold == 0.7
        assert request.match_count == 10
    
    def test_memory_text_search_request_empty_query(self):
        """测试空查询文本"""
        with pytest.raises(ValidationError):
            MemoryTextSearchRequest(query="")


# ============================================================
# 响应模型测试
# ============================================================

class TestResponseModels:
    """响应模型测试"""
    
    def test_health_response_defaults(self):
        """测试健康检查响应默认值"""
        response = HealthResponse()
        
        assert response.status == "ok"
        assert response.database == "connected"
        assert response.version == "0.1.0"
    
    def test_health_response_custom(self):
        """测试自定义健康检查响应"""
        response = HealthResponse(database="error")
        
        assert response.database == "error"
    
    def test_message_response_defaults(self):
        """测试消息响应默认值"""
        response = MessageResponse(message="操作成功")
        
        assert response.message == "操作成功"
        assert response.success is True
    
    def test_message_response_custom(self):
        """测试自定义消息响应"""
        response = MessageResponse(message="操作失败", success=False)
        
        assert response.success is False
    
    def test_error_response(self):
        """测试错误响应"""
        response = ErrorResponse(
            error="NotFoundError",
            detail="资源不存在",
            status_code=404
        )
        
        assert response.error == "NotFoundError"
        assert response.detail == "资源不存在"
        assert response.status_code == 404