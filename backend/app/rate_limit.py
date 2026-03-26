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
from limits.storage import RedisStorage
from typing import Callable, Optional, Union
import logging
import re

from .config import settings

logger = logging.getLogger(__name__)

# 限流规则格式验证正则表达式
RATE_LIMIT_PATTERN = re.compile(r'^(\d+)/(second|minute|hour|day)$')

# 限流规则范围限制
RATE_LIMIT_MIN = 1
RATE_LIMIT_MAX = 10000


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


def validate_rate_limit_rule(rule: str) -> bool:
    """
    验证限流规则格式
    
    格式要求：数字/单位，如 "10/minute"
    单位支持：second, minute, hour, day
    
    Args:
        rule: 限流规则字符串
    
    Returns:
        bool: 是否有效
    
    Raises:
        ValueError: 规则格式无效
    """
    if not rule or not isinstance(rule, str):
        raise ValueError(f"限流规则不能为空，当前值: {rule}")
    
    match = RATE_LIMIT_PATTERN.match(rule.strip())
    if not match:
        raise ValueError(
            f"无效的限流规则格式: '{rule}'，应为 '数字/单位'，"
            f"如 '10/minute'，支持单位: second, minute, hour, day"
        )
    
    count = int(match.group(1))
    if count < RATE_LIMIT_MIN:
        raise ValueError(
            f"限流规则数值过小: {count}，最小允许值为 {RATE_LIMIT_MIN}"
        )
    if count > RATE_LIMIT_MAX:
        raise ValueError(
            f"限流规则数值过大: {count}，最大允许值为 {RATE_LIMIT_MAX}"
        )
    
    return True


def create_storage_backend(redis_url: Optional[str] = None) -> Union[str, RedisStorage]:
    """
    创建限流存储后端
    
    优先使用 Redis（如果配置了 REDIS_URL），
    Redis 连接失败时自动降级到内存存储
    
    Args:
        redis_url: Redis 连接 URL
    
    Returns:
        存储后端实例或 URI 字符串
    """
    # 获取 Redis URL（从参数或配置）
    redis_url = redis_url or getattr(settings, 'REDIS_URL', None)
    
    if redis_url:
        try:
            storage = RedisStorage(redis_url)
            logger.info(f"✅ 限流存储：Redis ({redis_url})")
            return storage
        except Exception as e:
            logger.warning(f"⚠️ Redis 连接失败，自动降级到内存存储: {e}")
    
    logger.info("✅ 限流存储：内存")
    return "memory://"


def create_limiter(
    key_func: Callable = get_client_identifier,
    redis_url: Optional[str] = None,
    enabled: Optional[bool] = None,
    default_limits: Optional[list] = None
) -> Limiter:
    """
    创建限流器实例（工厂函数）
    
    Args:
        key_func: 客户端标识函数
        redis_url: Redis 连接 URL
        enabled: 是否启用限流
        default_limits: 默认限流规则列表
    
    Returns:
        Limiter: 配置好的限流器实例
    """
    enabled = enabled if enabled is not None else settings.RATE_LIMIT_ENABLED
    
    # 验证默认限制格式
    if default_limits is None:
        default_rule = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
        validate_rate_limit_rule(default_rule)
        default_limits = [default_rule]
    else:
        for rule in default_limits:
            validate_rate_limit_rule(rule)
    
    # 创建存储后端
    storage = create_storage_backend(redis_url)
    
    # 创建限流器
    # slowapi Limiter 只接受 storage_uri 参数，不接受 storage 对象
    if isinstance(storage, str):
        limiter = Limiter(
            key_func=key_func,
            default_limits=default_limits,
            enabled=enabled,
            storage_uri=storage,
        )
    else:
        # RedisStorage 对象 - 使用 memory:// 作为 URI，后续手动设置存储
        limiter = Limiter(
            key_func=key_func,
            default_limits=default_limits,
            enabled=enabled,
            storage_uri="memory://",
        )
        # 手动替换存储后端
        limiter._storage = storage
    
    logger.info(
        f"限流器创建成功: enabled={enabled}, "
        f"storage={'Redis' if isinstance(storage, RedisStorage) else 'memory'}"
    )
    return limiter


# 全局限流器实例
limiter: Optional[Limiter] = None


def init_limiter() -> Limiter:
    """初始化全局限流器实例"""
    global limiter
    if limiter is None:
        limiter = create_limiter()
    return limiter


# 初始化限流器
limiter = init_limiter()


def setup_rate_limiting(app):
    """
    配置应用的限流中间件
    
    Args:
        app: FastAPI 应用实例
    """
    global limiter
    
    if limiter is None:
        limiter = init_limiter()
    
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


async def close_rate_limiter():
    """
    关闭限流器资源
    
    关闭存储连接（Redis 连接等），应在应用关闭时调用
    """
    global limiter
    
    if limiter is None:
        return
    
    try:
        # 关闭存储连接
        if hasattr(limiter, '_storage') and limiter._storage:
            storage = limiter._storage
            # 检查是否有 close 方法
            if hasattr(storage, 'close') and callable(getattr(storage, 'close')):
                # 检查是否是异步方法
                import inspect
                if inspect.iscoroutinefunction(storage.close):
                    await storage.close()
                else:
                    storage.close()
                logger.info("🔴 限流器存储连接已关闭")
        
        # 清理限流器实例
        limiter = None
        logger.info("🔴 限流器资源已清理")
        
    except Exception as e:
        logger.error(f"关闭限流器资源失败: {e}")


def __del__():
    """
    模块析构函数
    
    尝试在模块被垃圾回收时清理资源
    注意：Python 不保证析构函数一定被调用
    """
    global limiter
    if limiter is not None:
        try:
            # 尝试同步关闭存储
            if hasattr(limiter, '_storage') and limiter._storage:
                storage = limiter._storage
                if hasattr(storage, 'close') and callable(getattr(storage, 'close')):
                    # 避免在析构函数中使用异步操作
                    if not hasattr(storage.close, '__code__') or \
                       storage.close.__code__.co_flags & 0x80 == 0:  # 检查是否是协程
                        storage.close()
        except Exception:
            # 析构函数中不应抛出异常
            pass
        finally:
            limiter = None


# 预定义的限流装饰器
def rate_limit_10_per_minute():
    """严格限流：10 次/分钟（用于敏感操作）"""
    rule = "10/minute"
    validate_rate_limit_rule(rule)
    return limiter.limit(rule)


def rate_limit_30_per_minute():
    """中等限流：30 次/分钟（用于普通操作）"""
    rule = "30/minute"
    validate_rate_limit_rule(rule)
    return limiter.limit(rule)


def rate_limit_60_per_minute():
    """标准限流：60 次/分钟（默认）"""
    rule = "60/minute"
    validate_rate_limit_rule(rule)
    return limiter.limit(rule)


def rate_limit_100_per_hour():
    """宽松限流：100 次/小时（用于批量操作）"""
    rule = "100/hour"
    validate_rate_limit_rule(rule)
    return limiter.limit(rule)


def no_rate_limit():
    """不限流（用于健康检查等）"""
    return limiter.exempt