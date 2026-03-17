# ============================================================
# 傻妞任务派发器 - ShaniuDispatcher
# ============================================================
# 功能：傻妞（主智能体）派发任务给各个手下（子智能体）
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================
# 设计决策：
# - 只有小码（team-coder）的任务才持久化到数据库
# - 其他智能体（小搜、小写、小审等）直接执行，不保存任务
# - 这样可以避免数据混乱，减少数据库负担
# ============================================================

import asyncio
import logging
import uuid
from typing import Optional, Dict, Any, Callable

from .task_service import TaskService
from .config import (
    AGENT_TYPES, 
    PERSISTENCE_ENABLED, 
    get_agent_type, 
    is_persistence_enabled
)

# 配置日志
logger = logging.getLogger(__name__)


class ShaniuDispatcher:
    """
    傻妞任务派发器
    
    功能：
        - dispatch_task(): 派发任务给指定智能体
        - 自动判断是否需要持久化（只有 coder 需要）
        - 支持直接执行模式（其他智能体）
    
    使用示例：
        dispatcher = ShaniuDispatcher(task_service)
        
        # 派发任务给小码（持久化模式）
        result = await dispatcher.dispatch_task(
            agent_name="team-coder",
            task_description="修复用户登录 bug",
            params={"bug_id": "123"}
        )
        
        # 派发任务给小搜（直接执行模式）
        result = await dispatcher.dispatch_task(
            agent_name="team-researcher",
            task_description="搜索 AI 新闻",
            params={"source": "twitter"}
        )
    
    设计说明：
        - 小码（team-coder）：创建数据库任务，轮询执行
        - 其他智能体：直接 spawn，不保存任务
    """
    
    def __init__(self, task_service: TaskService = None):
        """
        初始化派发器
        
        Args:
            task_service: TaskService 实例（可选，用于小码的持久化任务）
        """
        self.task_service = task_service
        
        # 智能体处理器注册表（运行时注入）
        self._handlers: Dict[str, Callable] = {}
        
        logger.info("ShaniuDispatcher 初始化完成")
    
    def register_handler(self, agent_name: str, handler: Callable):
        """
        注册智能体处理器
        
        Args:
            agent_name: 智能体名称（如 "team-coder"）
            handler: 处理函数（异步函数）
        """
        self._handlers[agent_name] = handler
        logger.info(f"注册智能体处理器: {agent_name}")
    
    async def dispatch_task(
        self,
        agent_name: str,
        task_description: str,
        params: Dict[str, Any] = None,
        priority: str = "normal",
        timeout_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        派发任务给指定智能体
        
        Args:
            agent_name: 智能体名称（如 "team-coder", "team-researcher"）
            task_description: 任务描述
            params: 任务参数
            priority: 优先级（low/normal/high/urgent）
            timeout_minutes: 超时时间（分钟）
        
        Returns:
            执行结果字典，包含：
            - success: 是否成功
            - task_id: 任务ID（仅持久化模式）
            - result: 任务结果
            - mode: 执行模式（"persistent" 或 "direct"）
        
        设计说明：
            - coder 类型：创建数据库任务，等待执行
            - 其他类型：直接执行，返回结果
        """
        agent_type = get_agent_type(agent_name)
        
        logger.info(f"派发任务: {agent_name} ({agent_type}) - {task_description[:50]}...")
        
        # ============================================================
        # 核心逻辑：根据智能体类型选择执行模式
        # ============================================================
        
        if is_persistence_enabled(agent_type):
            # 小码：持久化模式
            return await self._dispatch_persistent(
                agent_name=agent_name,
                agent_type=agent_type,
                task_description=task_description,
                params=params,
                priority=priority,
                timeout_minutes=timeout_minutes
            )
        else:
            # 其他智能体：直接执行模式
            return await self._dispatch_direct(
                agent_name=agent_name,
                agent_type=agent_type,
                task_description=task_description,
                params=params
            )
    
    async def _dispatch_persistent(
        self,
        agent_name: str,
        agent_type: str,
        task_description: str,
        params: Dict[str, Any],
        priority: str,
        timeout_minutes: int
    ) -> Dict[str, Any]:
        """
        持久化模式：创建数据库任务
        
        用于小码（team-coder），任务会保存到数据库
        
        Returns:
            {
                "success": bool,
                "task_id": str,
                "mode": "persistent",
                "message": str
            }
        """
        if self.task_service is None:
            raise ValueError("小码模式需要传入 task_service 参数")
        
        try:
            # 创建数据库任务
            task_id = await self.task_service.create_task(
                task_type=agent_type,  # "code"
                title=task_description[:100],
                description=task_description,
                priority=priority,
                params=params,
                agent_type=agent_type,  # 重要：指定智能体类型
                timeout_minutes=timeout_minutes
            )
            
            if task_id is None:
                # 理论上不会发生，因为 coder 类型一定返回 task_id
                return {
                    "success": False,
                    "task_id": None,
                    "mode": "persistent",
                    "message": "任务创建失败（非 coder 类型）"
                }
            
            logger.info(f"小码任务已创建: {task_id} - {task_description[:50]}...")
            
            return {
                "success": True,
                "task_id": task_id,
                "mode": "persistent",
                "message": f"任务已创建，等待小码执行: {task_id}"
            }
        
        except Exception as e:
            logger.error(f"创建小码任务失败: {e}")
            return {
                "success": False,
                "task_id": None,
                "mode": "persistent",
                "message": f"任务创建失败: {str(e)}"
            }
    
    async def _dispatch_direct(
        self,
        agent_name: str,
        agent_type: str,
        task_description: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        直接执行模式：立即执行任务
        
        用于其他智能体（小搜、小写、小审等），不保存到数据库
        
        Returns:
            {
                "success": bool,
                "result": dict,
                "mode": "direct",
                "message": str
            }
        """
        # 检查是否有注册的处理器
        handler = self._handlers.get(agent_name)
        
        if handler is None:
            logger.warning(f"智能体 {agent_name} 没有注册处理器，返回待执行状态")
            return {
                "success": True,
                "result": None,
                "mode": "direct",
                "message": f"任务已派发给 {agent_name}，等待执行"
            }
        
        try:
            # 直接执行任务
            task = {
                "task_id": f"one-time-{uuid.uuid4()}",
                "task_type": agent_type,
                "title": task_description,
                "description": task_description,
                "params": params or {}
            }
            
            result = await handler(task)
            
            logger.info(f"直接执行任务完成: {agent_name} - {task_description[:50]}...")
            
            return {
                "success": True,
                "result": result,
                "mode": "direct",
                "message": f"任务已执行完成"
            }
        
        except Exception as e:
            logger.error(f"直接执行任务失败: {agent_name} - {e}")
            return {
                "success": False,
                "result": None,
                "mode": "direct",
                "message": f"任务执行失败: {str(e)}"
            }
    
    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """
        获取智能体信息
        
        Args:
            agent_name: 智能体名称
        
        Returns:
            智能体信息字典
        """
        agent_type = get_agent_type(agent_name)
        persistence = is_persistence_enabled(agent_type)
        
        return {
            "agent_name": agent_name,
            "agent_type": agent_type,
            "persistence_enabled": persistence,
            "mode": "persistent" if persistence else "direct"
        }
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有智能体信息
        
        Returns:
            智能体信息字典
        """
        return {
            name: self.get_agent_info(name)
            for name in AGENT_TYPES.keys()
        }


# ============================================================
# 便捷函数
# ============================================================

def create_dispatcher(db_url: str = None) -> ShaniuDispatcher:
    """
    创建派发器实例（便捷函数）
    
    Args:
        db_url: 数据库连接字符串（可选）
    
    Returns:
        ShaniuDispatcher 实例
    """
    task_service = None
    if db_url:
        task_service = TaskService(db_url)
    
    return ShaniuDispatcher(task_service)