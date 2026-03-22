# ============================================================
# 多智能体记忆中枢 - API 限流模块
# ============================================================
# 功能：请求限流和速率限制
# 作者：小码 1 号
# 日期：2026-03-22
# ============================================================

from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from typing import Callable
import logging

from .config import settings

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    """
    获取客户端标识符（用于限流）
    
    优先使用 X-Forwarded-For 头（反向代理场景），
    其次使用 X-Real-IP 头，
    最后使用远程地址
    
    Args:
        request: FastAPI 请求对象
    
    Returns:
        客户端标识符（IP 地址）
    """
    # 尝试从 X-Forwarded-For 获取真实 IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 可能包含多个 IP，取第一个（客户端 IP）
        return forwarded_for.split(",")[0].strip()
    
    # 尝试从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 使用远程地址
    return get_remote_address(request)


# 创建限流器实例
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    enabled=settings.RATE_LIMIT_ENABLED,
    storage_uri="memory://",  # 使用内存存储（生产环境可改为 Redis）
)


def setup_rate_limiting(app):
    """
    配置应用的限流中间件
    
    Args:
        app: FastAPI 应用实例
    """
    if not settings.RATE_LIMIT_ENABLED:
        logger.info("限流功能未启用")
        return
    
    # 添加限流器状态
    app.state.limiter = limiter
    
    # 添加异常处理器
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # 添加中间件
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info(
        f"限流功能已启用 - "
        f"默认限制: {settings.RATE_LIMIT_PER_MINUTE}/分钟, "
        f"每小时限制: {settings.RATE_LIMIT_PER_HOUR}/小时"
    )


# 预定义的限流装饰器
def rate_limit_10_per_minute():
    """严格限流：10 次/分钟（用于敏感操作）"""
    return limiter.limit("10/minute")


def rate_limit_30_per_minute():
    """中等限流：30 次/分钟（用于普通操作）"""
    return limiter.limit("30/minute")


def rate_limit_60_per_minute():
    """标准限流：60 次/分钟（默认）"""
    return limiter.limit("60/minute")


def rate_limit_100_per_hour():
    """宽松限流：100 次/小时（用于批量操作）"""
    return limiter.limit("100/hour")


def no_rate_limit():
    """不限流（用于健康检查等）"""
    return limiter.exempt