# ============================================================
# 多智能体记忆中枢 - API 认证模块
# ============================================================
# 功能：API Key 认证和授权
# 作者：小码 1 号
# 日期：2026-03-22
# ============================================================

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)

# API Key Header 名称
API_KEY_NAME = "X-API-Key"

# 创建 API Key Header 安全方案
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    验证 API Key
    
    Args:
        api_key: 从请求头中获取的 API Key
    
    Returns:
        验证通过的 API Key
    
    Raises:
        HTTPException: API Key 无效或缺失
    """
    # 如果 API Key 未启用，直接通过
    if not settings.API_KEY_ENABLED:
        logger.debug("API Key 认证未启用，跳过验证")
        return "disabled"
    
    # 检查 API Key 是否配置
    if not settings.API_KEY:
        logger.error("API Key 未配置，请设置 MEMORY_HUB_API_KEY 环境变量")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key 未配置，请联系管理员"
        )
    
    # 检查请求中是否提供了 API Key
    if not api_key:
        logger.warning("请求缺少 API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 API Key，请在请求头中提供 X-API-Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # 验证 API Key
    if api_key != settings.API_KEY:
        logger.warning(f"无效的 API Key 尝试: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key 无效",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.debug("API Key 验证通过")
    return api_key


def get_optional_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    获取可选的 API Key（不强制验证）
    
    用于健康检查等不需要认证的端点
    
    Args:
        api_key: 从请求头中获取的 API Key
    
    Returns:
        API Key 或 None
    """
    return api_key