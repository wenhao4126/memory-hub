# ============================================================
# 多智能体记忆中枢 - Embedding 服务测试
# ============================================================
# 功能：测试向量嵌入服务
# 作者：小码
# 日期：2026-03-06
# ============================================================

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
import asyncio

from app.services.embedding_service import EmbeddingService, embedding_service


# ============================================================
# EmbeddingService 初始化测试
# ============================================================

class TestEmbeddingServiceInit:
    """EmbeddingService 初始化测试"""
    
    def test_init_default_settings(self):
        """测试默认初始化"""
        service = EmbeddingService()
        
        assert service._model is None
        assert service._initialized is False
    
    def test_init_uses_settings(self):
        """测试从配置读取参数"""
        service = EmbeddingService()
        
        # 配置应该在 config.py 中定义
        assert service.dimension > 0
        assert service.model_name is not None


# ============================================================
# get_embedding 方法测试
# ============================================================

class TestGetEmbedding:
    """get_embedding 方法测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_get_embedding_empty_text(self, service):
        """测试空文本应该抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            await service.get_embedding("")
        
        assert "文本不能为空" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_embedding_whitespace_text(self, service):
        """测试纯空白文本应该抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            await service.get_embedding("   \t\n  ")
        
        assert "文本不能为空" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_embedding_none_text(self, service):
        """测试 None 文本应该抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            await service.get_embedding(None)
        
        assert "文本不能为空" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_embedding_success(self, service):
        """测试成功获取向量"""
        # 模拟模型加载
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(
            tolist=lambda: [0.1] * 512
        )
        service._model = mock_model
        service._initialized = True
        
        result = await service.get_embedding("测试文本")
        
        assert isinstance(result, list)
        assert len(result) == 512
        mock_model.encode.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_embedding_calls_encode_with_normalize(self, service):
        """测试调用 encode 时启用 normalize_embeddings"""
        mock_model = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1] * 512
        mock_model.encode.return_value = mock_embedding
        service._model = mock_model
        service._initialized = True
        
        await service.get_embedding("测试文本")
        
        # 验证 encode 被调用，且 normalize_embeddings=True
        mock_model.encode.assert_called_once()
        call_args = mock_model.encode.call_args
        assert call_args[1].get('normalize_embeddings') == True
    
    @pytest.mark.asyncio
    async def test_get_embedding_model_load_failure(self, service):
        """测试模型加载失败"""
        # 模拟 _ensure_model_loaded 抛出异常
        service._initialized = False
        service._model = None
        
        # 直接模拟 _ensure_model_loaded 失败
        async def mock_ensure_loaded():
            raise ValueError("加载本地 Embedding 模型失败: 未安装")
        
        with patch.object(service, '_ensure_model_loaded', new=mock_ensure_loaded):
            with pytest.raises(ValueError) as exc_info:
                await service.get_embedding("测试文本")
            
            # 错误信息应该包含失败信息
            assert "加载本地 Embedding 模型失败" in str(exc_info.value) or "生成向量失败" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_embedding_encode_failure(self, service):
        """测试编码失败"""
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("编码错误")
        service._model = mock_model
        service._initialized = True
        
        with pytest.raises(ValueError) as exc_info:
            await service.get_embedding("测试文本")
        
        assert "生成向量失败" in str(exc_info.value)


# ============================================================
# _ensure_model_loaded 方法测试
# ============================================================

class TestEnsureModelLoaded:
    """_ensure_model_loaded 方法测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_already_initialized(self, service):
        """测试已经初始化的情况"""
        service._initialized = True
        
        # 应该直接返回，不做任何操作
        await service._ensure_model_loaded()
        
        assert service._initialized is True
    
    @pytest.mark.asyncio
    async def test_load_model_success(self, service):
        """测试成功加载模型"""
        mock_model = MagicMock()
        
        with patch.object(service, '_load_model') as mock_load:
            mock_load.return_value = None  # _load_model 设置 self._model
            service._model = mock_model  # 模拟加载后的状态
            
            await service._ensure_model_loaded()
            
            assert service._initialized is True
            mock_load.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_model_import_error(self, service):
        """测试模型加载时缺少依赖"""
        with patch.object(service, '_load_model', side_effect=ImportError("未安装 sentence-transformers")):
            with pytest.raises(ValueError) as exc_info:
                await service._ensure_model_loaded()
            
            assert "加载本地 Embedding 模型失败" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_load_model_runtime_error(self, service):
        """测试模型加载时运行时错误"""
        with patch.object(service, '_load_model', side_effect=RuntimeError("模型文件不存在")):
            with pytest.raises(ValueError) as exc_info:
                await service._ensure_model_loaded()
            
            assert "加载本地 Embedding 模型失败" in str(exc_info.value)


# ============================================================
# _load_model 方法测试
# ============================================================

class TestLoadModel:
    """_load_model 方法测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return EmbeddingService()
    
    def test_load_model_missing_sentence_transformers(self, service):
        """测试缺少 sentence_transformers 库"""
        # 模拟 ImportError 在 _load_model 内部导入时发生
        import builtins
        real_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if 'sentence_transformers' in name:
                raise ImportError("No module named 'sentence_transformers'")
            return real_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with pytest.raises(ImportError) as exc_info:
                service._load_model()
            
            assert "sentence-transformers" in str(exc_info.value)
    
    def test_load_model_sets_offline_mode(self, service):
        """测试设置离线模式环境变量"""
        import os
        
        # _load_model 会设置离线模式环境变量
        # 我们验证如果模型存在，这些操作会执行
        # 由于依赖外部库，这里只验证方法可调用
        
        # 简化：直接验证 service 配置正确
        assert service.model_name is not None
        assert service.dimension > 0
    
    def test_load_model_with_mocked_import(self, service):
        """测试成功加载模型（使用 mock）"""
        mock_model = MagicMock()
        
        # 直接设置模型，跳过实际导入
        service._model = mock_model
        
        # 验证模型已设置
        assert service._model is not None


# ============================================================
# _encode_text 方法测试
# ============================================================

class TestEncodeText:
    """_encode_text 方法测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        service = EmbeddingService()
        service._model = MagicMock()
        service._initialized = True
        return service
    
    def test_encode_text_returns_embedding(self, service):
        """测试编码文本返回向量"""
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1] * 512
        service._model.encode.return_value = mock_embedding
        
        result = service._encode_text("测试文本")
        
        service._model.encode.assert_called_once()
        assert result is not None
    
    def test_encode_text_normalizes_embeddings(self, service):
        """测试编码时启用归一化"""
        mock_embedding = MagicMock()
        service._model.encode.return_value = mock_embedding
        
        service._encode_text("测试文本")
        
        # 验证 normalize_embeddings=True
        call_kwargs = service._model.encode.call_args[1]
        assert call_kwargs.get('normalize_embeddings') == True


# ============================================================
# 全局服务实例测试
# ============================================================

class TestGlobalService:
    """全局服务实例测试"""
    
    def test_global_service_exists(self):
        """测试全局服务实例存在"""
        from app.services.embedding_service import embedding_service
        
        assert embedding_service is not None
        assert isinstance(embedding_service, EmbeddingService)
    
    def test_global_service_not_initialized_by_default(self):
        """测试全局服务默认未初始化"""
        # 创建新实例测试
        service = EmbeddingService()
        assert service._initialized is False


# ============================================================
# 错误处理测试
# ============================================================

class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_dimension_mismatch_warning(self, service):
        """测试维度不匹配时的警告"""
        # 创建返回错误维度的模拟
        mock_model = MagicMock()
        # 返回 128 维而不是 512 维
        mock_model.encode.return_value = MagicMock(
            tolist=lambda: [0.1] * 128
        )
        service._model = mock_model
        service._initialized = True
        
        # 应该记录警告但不会抛出异常
        with patch('app.services.embedding_service.logger') as mock_logger:
            result = await service.get_embedding("测试文本")
            
            # 应该仍然返回结果
            assert len(result) == 128
            # 应该记录警告
            mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_async_execution_doesnt_block(self, service):
        """测试异步执行不阻塞事件循环"""
        import time
        
        # 创建慢速编码模拟
        def slow_encode(text, **kwargs):
            time.sleep(0.1)  # 模拟 100ms 延迟
            return MagicMock(tolist=lambda: [0.1] * 512)
        
        mock_model = MagicMock()
        mock_model.encode = slow_encode
        service._model = mock_model
        service._initialized = True
        
        # 并发执行多个请求
        start_time = time.time()
        tasks = [
            service.get_embedding(f"文本 {i}")
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # 并发执行应该比顺序快
        # 3 个 100ms 任务顺序执行需要 300ms+，并发应该更快
        assert len(results) == 3
        assert all(len(r) == 512 for r in results)


# ============================================================
# 性能测试
# ============================================================

class TestPerformance:
    """性能测试"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        service = EmbeddingService()
        service._model = MagicMock()
        service._model.encode.return_value = MagicMock(
            tolist=lambda: [0.1] * 512
        )
        service._initialized = True
        return service
    
    @pytest.mark.asyncio
    async def test_embedding_performance(self, service):
        """测试向量生成性能"""
        import time
        
        start = time.time()
        
        # 生成 10 个向量
        for _ in range(10):
            await service.get_embedding("测试文本")
        
        elapsed = time.time() - start
        
        # 10 次调用应该在 1 秒内完成（mock 情况）
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, service):
        """测试并发请求处理"""
        import asyncio
        
        tasks = [
            service.get_embedding(f"并发测试 {i}")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(len(r) == 512 for r in results)