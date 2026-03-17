# ============================================================
# Memory Hub - 权限服务
# ============================================================
# 功能：API 层权限校验，控制智能体对数据库表的访问
# 作者：小码 🟡
# 日期：2026-03-17
# 
# 权限规则（憨货亲定）：
#   - parallel_tasks: 傻妞写，小码读
#   - shared_memories: 全员读，小搜/小写/小审/小析/小览/小图/小排写
#   - knowledge: 全员读写
# ============================================================

import json
import logging
from pathlib import Path
from typing import Optional, Set, Dict, Any
from functools import wraps
import uuid

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class PermissionService:
    """
    权限服务
    
    功能：
        - 加载权限配置
        - 检查智能体对表的访问权限
        - 提供装饰器用于 API 路由权限校验
    
    使用方式：
        from ..services.permission_service import permission_service
        
        # 检查权限
        if not permission_service.check_permission(agent_id, "shared_memories", "write"):
            raise HTTPException(status_code=403, detail="无权限")
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化权限服务
        
        Args:
            config_path: 权限配置文件路径（默认 backend/app/config/permissions.json）
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "permissions.json"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.agents: Dict[str, str] = {}  # name -> uuid
        self.agent_names: Dict[str, str] = {}  # uuid -> name
        self.tables: Dict[str, Dict[str, Any]] = {}
        
        self._load_config()
    
    def _load_config(self):
        """加载权限配置文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"权限配置文件不存在: {self.config_path}")
                self._use_default_config()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # 解析智能体 ID 映射
            self.agents = self.config.get('agents', {})
            self.agent_names = {v: k for k, v in self.agents.items()}
            
            # 解析表权限
            self.tables = self.config.get('tables', {})
            
            logger.info(f"权限配置加载成功: {len(self.agents)} 个智能体, {len(self.tables)} 个表")
        
        except Exception as e:
            logger.error(f"加载权限配置失败: {e}")
            self._use_default_config()
    
    def _use_default_config(self):
        """使用默认配置（兜底）"""
        self.agents = {
            "傻妞": "2ced6241-9915-47f7-86d0-32ea8db0eb68",
            "小搜": "d5fa91a1-dd55-4e26-a151-126c1a977a8d",
            "小写": "7ffb2eab-719c-4894-abba-a84f05e6d6e2",
            "小码": "3c9d696c-62e1-4ecf-9a78-46deed923080",
            "小审": "04a87468-fbf1-4f25-9a4d-4e03f2963a36",
            "小析": "ca71407b-f8c2-43ac-ad40-b50756036e59",
            "小览": "986150df-eb22-4f46-b43f-cc4f632f7314",
            "小图": "86df09c2-2ba8-431e-a376-a76d661fa80b",
            "小排": "cae3ad57-60c2-445a-8356-b8c9293a930c"
        }
        self.agent_names = {v: k for k, v in self.agents.items()}
        
        self.tables = {
            "parallel_tasks": {
                "read": ["小码", "team-coder2", "team-coder3", "team-coder4", "team-coder5"],
                "write": ["傻妞"]
            },
            "shared_memories": {
                "read": ["all"],
                "write": ["小搜", "小写", "小审", "小析", "小览", "小图", "小排"]
            },
            "knowledge": {
                "read": ["all"],
                "write": ["all"]
            }
        }
        
        logger.info("使用默认权限配置")
    
    def get_agent_name(self, agent_id: str) -> str:
        """
        获取智能体名称
        
        Args:
            agent_id: 智能体 ID（UUID 字符串或名称）
        
        Returns:
            智能体名称
        """
        # 如果已经是名称，直接返回
        if agent_id in self.agents:
            return agent_id
        
        # 尝试作为 UUID 查找
        if agent_id in self.agent_names:
            return self.agent_names[agent_id]
        
        # 检查别名
        aliases = self.config.get('agent_aliases', {})
        if agent_id in aliases:
            return aliases[agent_id]
        
        return "未知智能体"
    
    def get_agent_id(self, agent_name: str) -> Optional[str]:
        """
        获取智能体 ID
        
        Args:
            agent_name: 智能体名称
        
        Returns:
            智能体 ID（UUID 字符串）
        """
        return self.agents.get(agent_name)
    
    def _resolve_agent_name(self, agent_id: str) -> str:
        """
        解析智能体名称（支持 UUID、名称、别名）
        
        Args:
            agent_id: 智能体 ID 或名称
        
        Returns:
            智能体名称
        """
        # 1. 如果是名称，直接返回
        if agent_id in self.agents:
            return agent_id
        
        # 2. 如果是 UUID，查找名称
        if agent_id in self.agent_names:
            return self.agent_names[agent_id]
        
        # 3. 检查别名
        aliases = self.config.get('agent_aliases', {})
        if agent_id in aliases:
            return aliases[agent_id]
        
        # 4. 返回原始值（未知智能体）
        return agent_id
    
    def check_permission(
        self,
        agent_id: str,
        table: str,
        action: str
    ) -> bool:
        """
        检查智能体是否有权限访问表
        
        Args:
            agent_id: 智能体 ID（UUID 或名称）
            table: 表名（parallel_tasks, shared_memories, knowledge）
            action: 操作（read, write）
        
        Returns:
            bool: 是否有权限
        """
        # 1. 解析智能体名称
        agent_name = self._resolve_agent_name(agent_id)
        
        # 2. 获取表权限配置
        table_config = self.tables.get(table)
        if not table_config:
            logger.warning(f"未找到表权限配置: {table}")
            return False  # 未知表，拒绝访问
        
        # 3. 获取允许的操作列表
        allowed_agents = table_config.get(action, [])
        
        # 4. 检查权限
        # "all" 表示所有智能体都有权限
        if "all" in allowed_agents:
            # 检查是否在禁止列表中
            forbidden = table_config.get(f"forbidden_{action}", [])
            if agent_name in forbidden:
                logger.warning(f"智能体 {agent_name} 被禁止 {action} {table}")
                return False
            return True
        
        # 检查智能体是否在允许列表中
        if agent_name in allowed_agents:
            return True
        
        # 检查别名
        aliases = self.config.get('agent_aliases', {})
        if agent_id in aliases:
            resolved_name = aliases[agent_id]
            if resolved_name in allowed_agents:
                return True
        
        logger.debug(f"智能体 {agent_name} 无权限 {action} {table}")
        return False
    
    def require_permission(
        self,
        agent_id: str,
        table: str,
        action: str
    ) -> None:
        """
        要求权限（无权限时抛出异常）
        
        Args:
            agent_id: 智能体 ID
            table: 表名
            action: 操作
        
        Raises:
            HTTPException: 403 无权限
        """
        if not self.check_permission(agent_id, table, action):
            agent_name = self.get_agent_name(agent_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"智能体 {agent_name} 无权限 {action} {table}"
            )
    
    def get_allowed_agents(self, table: str, action: str) -> Set[str]:
        """
        获取有权限的智能体列表
        
        Args:
            table: 表名
            action: 操作
        
        Returns:
            智能体名称集合
        """
        table_config = self.tables.get(table, {})
        allowed = table_config.get(action, [])
        
        if "all" in allowed:
            return set(self.agents.keys())
        
        return set(allowed)
    
    def reload_config(self):
        """重新加载权限配置"""
        self._load_config()
        logger.info("权限配置已重新加载")


# 全局权限服务实例
permission_service = PermissionService()


# ============================================================
# 装饰器：用于 API 路由权限校验
# ============================================================

def require_table_permission(table: str, action: str, agent_id_param: str = "agent_id"):
    """
    权限校验装饰器
    
    使用方式：
        @router.post("/memories")
        @require_table_permission("shared_memories", "write")
        async def create_memory(memory: MemoryCreate):
            ...
    
    Args:
        table: 表名
        action: 操作（read/write）
        agent_id_param: 请求中 agent_id 的参数名
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 获取 agent_id
            agent_id = kwargs.get(agent_id_param)
            
            # 如果是从请求体获取，尝试从第一个参数获取
            if agent_id is None and args:
                request_body = args[0]
                if hasattr(request_body, agent_id_param):
                    agent_id = getattr(request_body, agent_id_param)
                elif hasattr(request_body, 'model_dump'):
                    data = request_body.model_dump()
                    agent_id = data.get(agent_id_param)
            
            if agent_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"缺少 {agent_id_param} 参数"
                )
            
            # 检查权限
            permission_service.require_permission(agent_id, table, action)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator