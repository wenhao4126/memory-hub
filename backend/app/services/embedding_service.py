# ============================================================
# 多智能体记忆中枢 - 向量嵌入服务
# ============================================================
# 功能：使用 DashScope API 生成文本向量（text-embedding-v4）
# 作者：小码
# 日期：2026-03-06
# 更新：2026-03-07 - 使用官方 dashscope SDK 替代 httpx
# ============================================================

import logging
from typing import List
import asyncio
from http import HTTPStatus

import dashscope
from dashscope import TextEmbedding

from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """向量嵌入服务：使用 DashScope SDK 生成文本向量"""
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        # 使用专门的 Embedding API Key（向量模型）
        self.api_key = settings.DASHSCOPE_EMBEDDING_API_KEY
        
        if not self.api_key:
            raise ValueError("DASHSCOPE_EMBEDDING_API_KEY 未配置，请在 .env 文件中设置")
        
        logger.info(f"EmbeddingService 初始化完成，模型: {self.model_name}, 维度: {self.dimension}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        将文本转换为向量（调用 DashScope SDK）
        
        Args:
            text: 输入文本
        
        Returns:
            向量列表（1024 维，text-embedding-v4）
        
        Raises:
            ValueError: 文本为空或 API 调用失败
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        try:
            logger.info(f"开始生成向量，文本长度: {len(text)}")
            
            # 每次调用前设置 API key（避免与 LLM 服务冲突）
            def _call_with_api_key():
                dashscope.api_key = self.api_key
                return TextEmbedding.call(
                    model=self.model_name,
                    input=text
                )
            
            # 使用 asyncio.to_thread 包装同步调用，避免阻塞
            resp = await asyncio.to_thread(_call_with_api_key)
            
            # 检查响应状态
            if resp.status_code != HTTPStatus.OK:
                error_msg = f"DashScope API 调用失败: {resp.status_code}"
                if hasattr(resp, 'message'):
                    error_msg += f" - {resp.message}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 提取 embedding 向量
            # 响应格式: {"output": {"embeddings": [{"embedding": [...], "text_index": 0}]}, ...}
            embedding = resp.output['embeddings'][0]['embedding']
            
            # 验证维度
            if len(embedding) != self.dimension:
                logger.warning(
                    f"向量维度不匹配: 期望 {self.dimension}, 实际 {len(embedding)}"
                )
            
            logger.info(f"✅ 成功生成向量，维度: {len(embedding)}")
            return embedding
        
        except Exception as e:
            logger.error(f"❌ 生成向量失败: {e}", exc_info=True)
            raise ValueError(f"生成向量失败: {str(e)}")


# 全局服务实例
embedding_service = EmbeddingService()