# ============================================================
# 多智能体记忆中枢 - API 端点测试
# ============================================================
# 功能：测试所有 RESTful API 端点
# 作者：小码
# 日期：2026-03-05
# ============================================================

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

# 导入应用
from app.main import app
from app.models.schemas import Agent, Memory


client = TestClient(app)


# ============================================================
# 健康检查测试
# ============================================================

class TestHealthCheck:
    """健康检查端点测试"""
    
    def test_health_check_success(self):
        """测试健康检查成功"""
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = 1
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["database"] == "connected"
    
    def test_health_check_database_error(self):
        """测试数据库连接失败"""
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.side_effect = Exception("Connection refused")
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "error" in data["database"]


# ============================================================
# 智能体 API 测试
# ============================================================

class TestAgentAPI:
    """智能体管理 API 测试"""
    
    def test_create_agent_success(self):
        """测试创建智能体成功"""
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = uuid.uuid4()
            
            response = client.post(
                "/api/v1/agents",
                json={
                    "name": "TestAgent",
                    "description": "测试智能体",
                    "capabilities": ["对话", "分析"],
                    "metadata": {"version": "1.0"}
                }
            )
            
            assert response.status_code == 201
            assert "创建成功" in response.json()["message"]
    
    def test_create_agent_missing_name(self):
        """测试创建智能体缺少名称"""
        response = client.post(
            "/api/v1/agents",
            json={
                "description": "测试智能体"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_agent_name_too_long(self):
        """测试创建智能体名称超长"""
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "a" * 256  # 超过 255 字符限制
            }
        )
        
        assert response.status_code == 422
    
    def test_get_agent_success(self):
        """测试获取智能体成功"""
        from datetime import datetime
        agent_id = str(uuid.uuid4())
        
        # 使用 asyncpg Record 模拟对象
        class MockRecord(dict):
            pass
        
        mock_row = MockRecord({
            "id": uuid.UUID(agent_id),
            "name": "TestAgent",
            "description": "测试智能体",
            "capabilities": ["对话"],
            "metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        with patch('app.api.routes.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = mock_row
            
            response = client.get(f"/api/v1/agents/{agent_id}")
            
            assert response.status_code == 200
    
    def test_get_agent_invalid_id(self):
        """测试获取智能体无效 ID"""
        response = client.get("/api/v1/agents/invalid-uuid")
        
        assert response.status_code == 400
        assert "无效" in response.json()["detail"]
    
    def test_get_agent_not_found(self):
        """测试获取不存在的智能体"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = None
            
            response = client.get(f"/api/v1/agents/{agent_id}")
            
            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]
    
    def test_list_agents_success(self):
        """测试列出智能体成功"""
        with patch('app.api.routes.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            response = client.get("/api/v1/agents")
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    def test_list_agents_with_pagination(self):
        """测试列出智能体分页参数"""
        with patch('app.api.routes.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            response = client.get("/api/v1/agents?limit=10&offset=5")
            
            assert response.status_code == 200
    
    def test_update_agent_success(self):
        """测试更新智能体成功"""
        from datetime import datetime
        agent_id = str(uuid.uuid4())
        
        # 使用 asyncpg Record 模拟对象
        class MockRecord(dict):
            pass
        
        mock_row = MockRecord({
            "id": uuid.UUID(agent_id),
            "name": "UpdatedAgent",
            "description": "更新后的描述",
            "capabilities": ["对话"],
            "metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        with patch('app.api.routes.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = mock_row
            
            response = client.put(
                f"/api/v1/agents/{agent_id}",
                json={"name": "UpdatedAgent"}
            )
            
            assert response.status_code == 200
    
    def test_update_agent_invalid_id(self):
        """测试更新智能体无效 ID"""
        response = client.put(
            "/api/v1/agents/invalid-uuid",
            json={"name": "Test"}
        )
        
        assert response.status_code == 400
    
    def test_update_agent_no_fields(self):
        """测试更新智能体没有提供字段"""
        agent_id = str(uuid.uuid4())
        
        response = client.put(
            f"/api/v1/agents/{agent_id}",
            json={}
        )
        
        assert response.status_code == 400
    
    def test_delete_agent_success(self):
        """测试删除智能体成功"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "DELETE 1"
            
            response = client.delete(f"/api/v1/agents/{agent_id}")
            
            assert response.status_code == 200
            assert "删除成功" in response.json()["message"]
    
    def test_delete_agent_not_found(self):
        """测试删除不存在的智能体"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "DELETE 0"
            
            response = client.delete(f"/api/v1/agents/{agent_id}")
            
            assert response.status_code == 404


# ============================================================
# 记忆 API 测试
# ============================================================

class TestMemoryAPI:
    """记忆管理 API 测试"""
    
    def test_create_memory_success(self):
        """测试创建记忆成功"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = True  # agent exists
            
            with patch('app.services.memory_service.memory_service.create_memory', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = str(uuid.uuid4())
                
                response = client.post(
                    "/api/v1/memories",
                    json={
                        "agent_id": agent_id,
                        "content": "测试记忆内容",
                        "memory_type": "fact",
                        "importance": 0.5
                    }
                )
                
                assert response.status_code == 201
    
    def test_create_memory_agent_not_found(self):
        """测试创建记忆智能体不存在"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = False  # agent not exists
            
            response = client.post(
                "/api/v1/memories",
                json={
                    "agent_id": agent_id,
                    "content": "测试记忆内容"
                }
            )
            
            assert response.status_code == 404
    
    def test_create_memory_invalid_embedding(self):
        """测试创建记忆 embedding 维度错误"""
        agent_id = str(uuid.uuid4())
        
        response = client.post(
            "/api/v1/memories",
            json={
                "agent_id": agent_id,
                "content": "测试记忆",
                "embedding": [0.1] * 100  # 错误维度
            }
        )
        
        assert response.status_code == 422
    
    def test_get_memory_success(self):
        """测试获取记忆成功"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.get_memory', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "id": memory_id,
                "content": "测试记忆"
            }
            
            response = client.get(f"/api/v1/memories/{memory_id}")
            
            assert response.status_code == 200
    
    def test_get_memory_invalid_id(self):
        """测试获取记忆无效 ID"""
        response = client.get("/api/v1/memories/invalid-uuid")
        
        assert response.status_code == 400
    
    def test_get_memory_not_found(self):
        """测试获取不存在的记忆"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.get_memory', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            response = client.get(f"/api/v1/memories/{memory_id}")
            
            assert response.status_code == 404
    
    def test_update_memory_success(self):
        """测试更新记忆成功"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.update_memory', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = {
                "id": memory_id,
                "content": "更新后的内容"
            }
            
            response = client.put(
                f"/api/v1/memories/{memory_id}",
                json={"content": "更新后的内容"}
            )
            
            assert response.status_code == 200
    
    def test_update_memory_no_fields(self):
        """测试更新记忆没有提供字段"""
        memory_id = str(uuid.uuid4())
        
        response = client.put(
            f"/api/v1/memories/{memory_id}",
            json={}
        )
        
        assert response.status_code == 400
    
    def test_delete_memory_success(self):
        """测试删除记忆成功"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.delete_memory', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(f"/api/v1/memories/{memory_id}")
            
            assert response.status_code == 200
    
    def test_delete_memory_not_found(self):
        """测试删除不存在的记忆"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.delete_memory', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete(f"/api/v1/memories/{memory_id}")
            
            assert response.status_code == 404
    
    def test_search_memories_success(self):
        """测试搜索记忆成功"""
        with patch('app.services.memory_service.memory_service.search_similar', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            response = client.post(
                "/api/v1/memories/search",
                json={
                    "query_embedding": [0.1] * 512
                }
            )
            
            assert response.status_code == 200
    
    def test_search_memories_invalid_embedding(self):
        """测试搜索记忆 embedding 维度错误"""
        response = client.post(
            "/api/v1/memories/search",
            json={
                "query_embedding": [0.1] * 100  # 错误维度
            }
        )
        
        assert response.status_code == 422
    
    def test_search_memories_by_text_success(self):
        """测试文本搜索记忆成功"""
        with patch('app.services.memory_service.memory_service.search_by_text', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            response = client.post(
                "/api/v1/memories/search/text",
                json={
                    "query": "谁是主人？",
                    "match_count": 5
                }
            )
            
            assert response.status_code == 200
    
    def test_search_memories_by_text_empty_query(self):
        """测试文本搜索记忆空查询"""
        response = client.post(
            "/api/v1/memories/search/text",
            json={
                "query": ""
            }
        )
        
        assert response.status_code == 422
    
    def test_search_memories_by_text_embedding_error(self):
        """测试文本搜索记忆 embedding 服务错误"""
        with patch('app.services.memory_service.memory_service.search_by_text', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = ValueError("生成向量失败: 模型加载错误")
            
            response = client.post(
                "/api/v1/memories/search/text",
                json={
                    "query": "测试查询"
                }
            )
            
            assert response.status_code == 400
    
    def test_list_agent_memories_success(self):
        """测试列出智能体记忆成功"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = True  # agent exists
            
            with patch('app.services.memory_service.memory_service.list_memories_by_agent', new_callable=AsyncMock) as mock_list:
                mock_list.return_value = []
                
                response = client.get(f"/api/v1/agents/{agent_id}/memories")
                
                assert response.status_code == 200
    
    def test_list_agent_memories_agent_not_found(self):
        """测试列出智能体记忆智能体不存在"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = False  # agent not exists
            
            response = client.get(f"/api/v1/agents/{agent_id}/memories")
            
            assert response.status_code == 404
    
    def test_cleanup_memories_success(self):
        """测试清理记忆成功"""
        with patch('app.services.memory_service.memory_service.cleanup_old_memories', new_callable=AsyncMock) as mock_cleanup:
            mock_cleanup.return_value = 5
            
            response = client.post("/api/v1/memories/cleanup")
            
            assert response.status_code == 200
            assert "5 条" in response.json()["message"]


# ============================================================
# 参数验证测试
# ============================================================

class TestParameterValidation:
    """参数验证测试"""
    
    def test_list_agents_limit_validation(self):
        """测试列表智能体 limit 参数验证"""
        with patch('app.api.routes.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            # 测试有效范围
            response = client.get("/api/v1/agents?limit=50")
            assert response.status_code == 200
            
            # 测试超过最大值
            response = client.get("/api/v1/agents?limit=200")
            assert response.status_code == 422
            
            # 测试负数
            response = client.get("/api/v1/agents?limit=-1")
            assert response.status_code == 422
    
    def test_create_memory_importance_validation(self):
        """测试创建记忆 importance 参数验证"""
        agent_id = str(uuid.uuid4())
        
        # 测试超过范围
        response = client.post(
            "/api/v1/memories",
            json={
                "agent_id": agent_id,
                "content": "测试",
                "importance": 1.5  # 超过 1.0
            }
        )
        
        assert response.status_code == 422
    
    def test_cleanup_parameters_validation(self):
        """测试清理记忆参数验证"""
        with patch('app.services.memory_service.memory_service.cleanup_old_memories', new_callable=AsyncMock) as mock_cleanup:
            mock_cleanup.return_value = 0
            
            # 测试有效参数
            response = client.post("/api/v1/memories/cleanup?days_old=30&min_importance=0.3&max_access_count=3")
            assert response.status_code == 200
            
            # 测试超过范围
            response = client.post("/api/v1/memories/cleanup?days_old=500")
            assert response.status_code == 422


# ============================================================
# 错误处理测试（补充覆盖率）
# ============================================================

class TestErrorHandling:
    """错误处理测试"""
    
    def test_create_agent_server_error(self):
        """测试创建智能体服务器错误"""
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.side_effect = Exception("数据库连接失败")
            
            response = client.post(
                "/api/v1/agents",
                json={"name": "TestAgent"}
            )
            
            assert response.status_code == 500
            assert "创建智能体失败" in response.json()["detail"]
    
    def test_update_agent_server_error(self):
        """测试更新智能体服务器错误"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            # 第一次检查存在，然后抛出异常
            mock_fetchrow.side_effect = Exception("数据库错误")
            
            response = client.put(
                f"/api/v1/agents/{agent_id}",
                json={"name": "NewName"}
            )
            
            assert response.status_code == 500
            assert "更新智能体失败" in response.json()["detail"]
    
    def test_update_memory_invalid_id(self):
        """测试更新记忆无效 ID"""
        response = client.put(
            "/api/v1/memories/invalid-uuid",
            json={"content": "新内容"}
        )
        
        assert response.status_code == 400
        assert "无效" in response.json()["detail"]
    
    def test_update_memory_not_found(self):
        """测试更新不存在的记忆"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.update_memory', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = None
            
            response = client.put(
                f"/api/v1/memories/{memory_id}",
                json={"content": "新内容"}
            )
            
            assert response.status_code == 404
    
    def test_update_memory_server_error(self):
        """测试更新记忆服务器错误"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.update_memory', new_callable=AsyncMock) as mock_update:
            mock_update.side_effect = Exception("数据库错误")
            
            response = client.put(
                f"/api/v1/memories/{memory_id}",
                json={"content": "新内容"}
            )
            
            assert response.status_code == 500
            assert "更新记忆失败" in response.json()["detail"]
    
    def test_delete_memory_invalid_id(self):
        """测试删除记忆无效 ID"""
        response = client.delete("/api/v1/memories/invalid-uuid")
        
        assert response.status_code == 400
    
    def test_list_agent_memories_invalid_id(self):
        """测试列出智能体记忆无效 ID"""
        response = client.get("/api/v1/agents/invalid-uuid/memories")
        
        assert response.status_code == 400
    
    def test_create_memory_server_error(self):
        """测试创建记忆服务器错误"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = True  # agent exists
            
            with patch('app.services.memory_service.memory_service.create_memory', new_callable=AsyncMock) as mock_create:
                mock_create.side_effect = Exception("数据库错误")
                
                response = client.post(
                    "/api/v1/memories",
                    json={
                        "agent_id": agent_id,
                        "content": "测试记忆"
                    }
                )
                
                assert response.status_code == 500
    
    def test_search_memories_server_error(self):
        """测试搜索记忆服务器错误"""
        with patch('app.services.memory_service.memory_service.search_similar', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("向量搜索失败")
            
            response = client.post(
                "/api/v1/memories/search",
                json={"query_embedding": [0.1] * 512}
            )
            
            assert response.status_code == 500
    
    def test_search_memories_by_text_server_error(self):
        """测试文本搜索记忆服务器错误"""
        with patch('app.services.memory_service.memory_service.search_by_text', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("服务不可用")
            
            response = client.post(
                "/api/v1/memories/search/text",
                json={"query": "测试"}
            )
            
            assert response.status_code == 500
    
    def test_cleanup_memories_server_error(self):
        """测试清理记忆服务器错误"""
        with patch('app.services.memory_service.memory_service.cleanup_old_memories', new_callable=AsyncMock) as mock_cleanup:
            mock_cleanup.side_effect = Exception("清理失败")
            
            response = client.post("/api/v1/memories/cleanup")
            
            assert response.status_code == 500


# ============================================================
# 边界条件测试
# ============================================================

class TestEdgeCases:
    """边界条件测试"""
    
    def test_update_memory_with_all_fields(self):
        """测试更新记忆所有字段"""
        memory_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.update_memory', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = {
                "id": memory_id,
                "content": "新内容",
                "importance": 0.9,
                "tags": ["新标签"]
            }
            
            response = client.put(
                f"/api/v1/memories/{memory_id}",
                json={
                    "content": "新内容",
                    "importance": 0.9,
                    "tags": ["新标签"],
                    "metadata": {"key": "value"}
                }
            )
            
            assert response.status_code == 200
    
    def test_update_agent_with_all_fields(self):
        """测试更新智能体所有字段"""
        from datetime import datetime
        agent_id = str(uuid.uuid4())
        
        class MockRecord(dict):
            pass
        
        mock_row = MockRecord({
            "id": uuid.UUID(agent_id),
            "name": "新名称",
            "description": "新描述",
            "capabilities": ["新能力"],
            "metadata": {"key": "value"},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        with patch('app.api.routes.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = mock_row
            
            response = client.put(
                f"/api/v1/agents/{agent_id}",
                json={
                    "name": "新名称",
                    "description": "新描述",
                    "capabilities": ["新能力"],
                    "metadata": {"key": "value"}
                }
            )
            
            assert response.status_code == 200
    
    def test_list_agents_with_max_limit(self):
        """测试列出智能体最大限制"""
        with patch('app.api.routes.db.fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            response = client.get("/api/v1/agents?limit=100")
            
            assert response.status_code == 200
    
    def test_list_agent_memories_with_pagination(self):
        """测试列出智能体记忆分页"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.api.routes.db.fetchval', new_callable=AsyncMock) as mock_fetchval:
            mock_fetchval.return_value = True
            
            with patch('app.services.memory_service.memory_service.list_memories_by_agent', new_callable=AsyncMock) as mock_list:
                mock_list.return_value = []
                
                response = client.get(f"/api/v1/agents/{agent_id}/memories?limit=10&offset=20")
                
                assert response.status_code == 200
    
    def test_search_memories_with_agent_filter(self):
        """测试带智能体过滤的搜索"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.search_similar', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            response = client.post(
                "/api/v1/memories/search",
                json={
                    "query_embedding": [0.1] * 512,
                    "agent_id": agent_id,
                    "match_threshold": 0.8,
                    "match_count": 5
                }
            )
            
            assert response.status_code == 200
    
    def test_search_memories_by_text_with_options(self):
        """测试带选项的文本搜索"""
        agent_id = str(uuid.uuid4())
        
        with patch('app.services.memory_service.memory_service.search_by_text', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            response = client.post(
                "/api/v1/memories/search/text",
                json={
                    "query": "测试查询",
                    "agent_id": agent_id,
                    "match_threshold": 0.9,
                    "match_count": 20
                }
            )
            
            assert response.status_code == 200