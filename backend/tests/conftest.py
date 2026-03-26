"""
Pytest 配置文件
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env')

# Mock embedding service before importing app
from unittest.mock import MagicMock
import app.services.embedding_service as emb_module
emb_module.EmbeddingService = MagicMock
emb_module.embedding_service = MagicMock()
emb_module.embedding_service.get_embedding.return_value = [0.1] * 1024
