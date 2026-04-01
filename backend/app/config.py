# ============================================================
# 多智能体记忆中枢 - 配置管理
# ============================================================
# 功能：管理应用配置，支持环境变量覆盖
# 作者：小码
# 日期：2026-03-05
# ============================================================

import os
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def validate_password_strength(password: str, field_name: str = "密码") -> None:
    """
    验证密码强度
    
    要求：
    - 至少 8 个字符
    - 至少包含一个大写字母
    - 至少包含一个小写字母
    - 至少包含一个数字
    - 至少包含一个特殊字符
    
    Args:
        password: 要验证的密码
        field_name: 字段名称（用于错误消息）
    
    Raises:
        ValueError: 密码不符合强度要求
    """
    if len(password) < 8:
        raise ValueError(f"{field_name}长度至少为8个字符")
    
    if not re.search(r'[A-Z]', password):
        raise ValueError(f"{field_name}必须包含至少一个大写字母")
    
    if not re.search(r'[a-z]', password):
        raise ValueError(f"{field_name}必须包含至少一个小写字母")
    
    if not re.search(r'\d', password):
        raise ValueError(f"{field_name}必须包含至少一个数字")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError(f"{field_name}必须包含至少一个特殊字符")


class Settings:
    """应用配置类"""
    
    def __init__(self):
        """初始化配置并验证必需的环境变量"""
        # 数据库配置
        self.DB_HOST: str = os.getenv("DB_HOST", "localhost")
        self.DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
        self.DB_USER: str = os.getenv("DB_USER", "memory_user")
        self.DB_NAME: str = os.getenv("DB_NAME", "memory_hub")
        
        # 数据库密码（可选，默认 memory_pass_2026）
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD", "memory_pass_2026")
        
        # 嵌入模型配置（DashScope API）
        # text-embedding-v4 输出 1024 维向量
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
        self.EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", os.getenv("VECTOR_DIMENSIONS", "1024")))
        
        # DashScope API 配置
        # ⚠️ 重要：两个 API Key 用途不同，不能混用！
        # LLM API Key - 用于对话增强（月会员套餐）
        self.DASHSCOPE_LLM_API_KEY: str = os.getenv("DASHSCOPE_LLM_API_KEY", "")
        # Embedding API Key - 用于向量生成
        self.DASHSCOPE_EMBEDDING_API_KEY: str = os.getenv("DASHSCOPE_EMBEDDING_API_KEY", "")
        
        # 兼容旧配置（如果只设置了 DASHSCOPE_API_KEY）
        if not self.DASHSCOPE_LLM_API_KEY and not self.DASHSCOPE_EMBEDDING_API_KEY:
            old_key = os.getenv("DASHSCOPE_API_KEY", "")
            if old_key:
                logger.warning("使用旧版 DASHSCOPE_API_KEY 配置，建议分别设置 DASHSCOPE_LLM_API_KEY 和 DASHSCOPE_EMBEDDING_API_KEY")
                self.DASHSCOPE_LLM_API_KEY = old_key
                self.DASHSCOPE_EMBEDDING_API_KEY = old_key
        
        self.DASHSCOPE_BASE_URL: str = os.getenv(
            "DASHSCOPE_BASE_URL", 
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # LLM 配置（用于对话增强）
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3.5-plus")
        self.LLM_BASE_URL: str = os.getenv(
            "LLM_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # API 配置
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8000"))
        self.API_DEBUG: bool = os.getenv("API_DEBUG", "false").lower() == "true"
        
        # CORS 配置
        self.ALLOWED_ORIGINS: str = os.getenv(
            "ALLOWED_ORIGINS", 
            "http://localhost:3000,http://localhost:8080"
        )
        
        # API 安全配置
        self.API_KEY: str = os.getenv("MEMORY_HUB_API_KEY", "")
        self.API_KEY_ENABLED: bool = os.getenv("API_KEY_ENABLED", "true").lower() == "true"
        
        # 限流配置
        self.RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.RATE_LIMIT_PER_MINUTE: int = self._validate_rate_limit_value(
            os.getenv("RATE_LIMIT_PER_MINUTE", "60"),
            "RATE_LIMIT_PER_MINUTE",
            min_value=1,
            max_value=10000
        )
        self.RATE_LIMIT_PER_HOUR: int = self._validate_rate_limit_value(
            os.getenv("RATE_LIMIT_PER_HOUR", "1000"),
            "RATE_LIMIT_PER_HOUR",
            min_value=1,
            max_value=100000
        )
        
        # Redis 配置（可选，用于限流存储）
        self.REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "")
        if self.REDIS_URL == "":
            self.REDIS_URL = None

        # 插件仓配置（可选）
        self.MEMORY_HUB_MODULES_ROOT: Optional[str] = os.getenv("MEMORY_HUB_MODULES_ROOT", "")
        if self.MEMORY_HUB_MODULES_ROOT == "":
            self.MEMORY_HUB_MODULES_ROOT = None
    
    def _validate_rate_limit_value(
        self, 
        value: str, 
        name: str, 
        min_value: int = 1, 
        max_value: int = 10000
    ) -> int:
        """
        验证限流配置值
        
        Args:
            value: 配置值字符串
            name: 配置项名称
            min_value: 最小允许值
            max_value: 最大允许值
        
        Returns:
            int: 验证后的整数值
        
        Raises:
            ValueError: 配置值无效
        """
        try:
            int_value = int(value)
        except ValueError:
            raise ValueError(
                f"{name} 必须是整数，当前值: '{value}'"
            )
        
        if int_value < min_value:
            raise ValueError(
                f"{name} 不能小于 {min_value}，当前值: {int_value}"
            )
        
        if int_value > max_value:
            raise ValueError(
                f"{name} 不能大于 {max_value}，当前值: {int_value}"
            )
        
        return int_value
    
    @property
    def allowed_origins_list(self) -> list:
        """获取 CORS 允许的来源列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def database_url(self) -> str:
        """获取数据库连接 URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def async_database_url(self) -> str:
        """获取异步数据库连接 URL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# 全局配置实例
settings = Settings()