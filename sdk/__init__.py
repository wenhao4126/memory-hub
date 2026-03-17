# ============================================================
# 多智能体并行任务系统 - SDK 模块
# ============================================================
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================
# 更新记录（2026-03-16）：
# - 添加智能体类型配置
# - 添加傻妞任务派发器
# - 只持久化小码（team-coder）的任务
# ============================================================

from .task_service import TaskService, TaskServiceSync, get_memory_client, MemoryClient
from .config import (
    settings,
    AGENT_TYPES,
    PERSISTENCE_ENABLED,
    get_agent_type,
    is_persistence_enabled
)
from .shaniu_dispatcher import ShaniuDispatcher, create_dispatcher

__all__ = [
    # 任务服务
    'TaskService',
    'TaskServiceSync',
    
    # 记忆客户端
    'get_memory_client',
    'MemoryClient',
    
    # 配置
    'settings',
    'AGENT_TYPES',
    'PERSISTENCE_ENABLED',
    'get_agent_type',
    'is_persistence_enabled',
    
    # 派发器
    'ShaniuDispatcher',
    'create_dispatcher',
]

__version__ = '1.1.0'