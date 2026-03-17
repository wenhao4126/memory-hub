# ============================================================
# 多智能体并行任务系统 - Python SDK
# ============================================================
# 功能：提供任务创建、领取、进度更新、完成/失败等操作
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================
# Phase 3 集成：任务完成自动写入记忆系统
# 日期：2026-03-16
# ============================================================
# 权限控制：parallel_tasks 表访问权限校验
# 日期：2026-03-17
# 规则：傻妞写，小码读
# ============================================================

import asyncio
import logging
import uuid
import json
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

import asyncpg

from .config import settings

# 配置日志
logger = logging.getLogger(__name__)


# ============================================================
# 权限服务（简化版，用于 SDK 层权限校验）
# ============================================================

# 智能体 ID 映射
AGENT_IDS = {
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

# 反向映射
AGENT_NAMES = {v: k for k, v in AGENT_IDS.items()}

# 权限配置
PARALLEL_TASKS_PERMISSIONS = {
    "write": ["傻妞"],  # 只有傻妞能创建任务
    "read": ["小码", "team-coder2", "team-coder3", "team-coder4", "team-coder5"]  # 小码池能读
}

# 别名映射
AGENT_ALIASES = {
    "team-coder": "小码",
    "team-coder1": "小码",
    "team-coder2": "小码2",
    "team-coder3": "小码3",
    "team-coder4": "小码4",
    "team-coder5": "小码5"
}


def resolve_agent_name(agent_id: str) -> str:
    """解析智能体名称"""
    # 如果是名称，直接返回
    if agent_id in AGENT_IDS:
        return agent_id
    
    # 如果是 UUID，查找名称
    if agent_id in AGENT_NAMES:
        return AGENT_NAMES[agent_id]
    
    # 检查别名
    if agent_id in AGENT_ALIASES:
        return AGENT_ALIASES[agent_id]
    
    return agent_id


def check_parallel_tasks_permission(agent_id: str, action: str) -> bool:
    """
    检查 parallel_tasks 表访问权限
    
    Args:
        agent_id: 智能体 ID 或名称
        action: 操作（read/write）
    
    Returns:
        bool: 是否有权限
    """
    agent_name = resolve_agent_name(agent_id)
    allowed = PARALLEL_TASKS_PERMISSIONS.get(action, [])
    
    # 检查别名
    if agent_id in AGENT_ALIASES:
        resolved = AGENT_ALIASES[agent_id]
        # team-coder2-5 的小码有读权限
        if action == "read" and agent_id in ["team-coder", "team-coder1", "team-coder2", "team-coder3", "team-coder4", "team-coder5"]:
            return True
        # 只有傻妞有写权限
        if action == "write" and resolved == "傻妞":
            return True
        return False
    
    # 直接检查名称
    if agent_name in allowed:
        return True
    
    # 小码的所有别名都有读权限
    if action == "read" and agent_name in ["小码", "小码2", "小码3", "小码4", "小码5"]:
        return True
    
    return False


class PermissionDeniedError(Exception):
    """权限拒绝异常"""
    pass


# ============================================================
# UUID 转换辅助函数
# ============================================================

# 固定的命名空间 UUID（用于生成 agent_id 的 UUID）
AGENT_NAMESPACE_UUID = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # UUID namespace DNS


def agent_id_to_uuid(agent_id: str) -> uuid.UUID:
    """
    将 agent_id 字符串转换为 UUID
    
    如果 agent_id 已经是有效的 UUID 字符串，直接返回
    如果不是，使用 UUID v5 基于固定命名空间生成
    
    Args:
        agent_id: 智能体ID（如 'team-coder1' 或 UUID 字符串）
    
    Returns:
        UUID 对象
    """
    try:
        # 尝试直接解析为 UUID
        return uuid.UUID(agent_id)
    except ValueError:
        # 不是有效的 UUID，使用 UUID v5 生成
        return uuid.uuid5(AGENT_NAMESPACE_UUID, agent_id)


# ============================================================
# 记忆系统客户端（Phase 3 新增）
# ============================================================

class MemoryClient:
    """
    记忆系统 HTTP 客户端
    
    功能：
        - create_memory(): 创建新记忆
        - search_memories(): 搜索记忆
        - get_task_memories(): 获取任务相关记忆
        - get_project_memories(): 获取项目相关记忆
    """
    
    def __init__(self, base_url: str = None):
        """
        初始化记忆客户端
        
        Args:
            base_url: 记忆系统 API 地址（默认从配置读取）
        """
        self.base_url = base_url or settings.MEMORY_API_URL or "http://localhost:8000/api/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"MemoryClient 初始化，API 地址: {self.base_url}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（懒加载）"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("MemoryClient HTTP 客户端已关闭")
    
    async def create_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "experience",
        importance: float = 0.5,
        metadata: Dict[str, Any] = None,
        auto_route: bool = True,
        visibility: str = None
    ) -> Dict[str, Any]:
        """
        创建新记忆
        
        Args:
            agent_id: 智能体 ID
            content: 记忆内容
            memory_type: 记忆类型 (fact/preference/skill/experience)
            importance: 重要性 (0.0-1.0)
            metadata: 元数据
            auto_route: 是否自动路由到合适的表
            visibility: 可见性 (private/shared)
        
        Returns:
            创建结果，包含 memory_id, table, visibility 等
        """
        client = await self._get_client()
        
        payload = {
            "agent_id": agent_id,
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "metadata": metadata or {},
            "auto_route": auto_route
        }
        
        if visibility:
            payload["visibility"] = visibility
            payload["auto_route"] = False
        
        try:
            response = await client.post(
                f"{self.base_url}/memories",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"记忆创建成功: memory_id={result.get('memory_id')}, table={result.get('table')}")
            return result
        
        except httpx.HTTPStatusError as e:
            logger.error(f"创建记忆失败: HTTP {e.response.status_code}, {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"创建记忆失败: {e}")
            raise
    
    async def search_memories(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
        visibility: str = None
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            agent_id: 智能体 ID
            query: 搜索文本
            limit: 返回数量
            visibility: 过滤类型 (private/shared)
        
        Returns:
            记忆列表
        """
        client = await self._get_client()
        
        params = {
            "agent_id": agent_id,
            "query": query,
            "limit": limit
        }
        
        endpoint = "/memories/search/private" if visibility == "private" else "/memories/search/shared"
        
        try:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise


# 全局记忆客户端实例
_memory_client: Optional[MemoryClient] = None


def get_memory_client() -> MemoryClient:
    """获取全局记忆客户端实例"""
    global _memory_client
    if _memory_client is None:
        _memory_client = MemoryClient()
    return _memory_client


class TaskService:
    """
    任务服务类 - 并行任务系统的 Python SDK
    
    功能：
        - create_task(): 创建新任务
        - acquire_task(): 领取待执行任务
        - update_progress(): 更新任务进度
        - complete_task(): 完成任务
        - fail_task(): 标记任务失败
        - get_task(): 查询任务详情
        - get_task_statistics(): 获取任务统计
        - cleanup_expired_locks(): 清理过期锁
    """
    
    def __init__(self, db_url: str = None):
        """
        初始化任务服务
        
        Args:
            db_url: 数据库连接字符串（格式：postgresql://user:pass@host:port/dbname）
                   如果不提供，则从环境变量 DATABASE_URL 读取
        """
        self.db_url = db_url or settings.DATABASE_URL
        self._pool: Optional[asyncpg.Pool] = None
        logger.info(f"TaskService 初始化，数据库: {self._mask_password(self.db_url)}")
    
    def _mask_password(self, url: str) -> str:
        """隐藏密码，用于日志输出"""
        if '@' in url and ':' in url:
            # postgresql://user:password@host:port/db -> postgresql://user:***@host:port/db
            parts = url.split('://')
            if len(parts) == 2:
                auth_host = parts[1].split('@')
                if len(auth_host) == 2:
                    user_pass = auth_host[0].split(':')
                    if len(user_pass) == 2:
                        return f"{parts[0]}://{user_pass[0]}:***@{auth_host[1]}"
        return url
    
    async def _get_pool(self) -> asyncpg.Pool:
        """获取数据库连接池（懒加载）"""
        if self._pool is None:
            # 创建连接池时设置 JSON 编码器
            self._pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                init=self._init_connection
            )
            logger.info("数据库连接池创建成功")
        return self._pool
    
    async def _init_connection(self, conn):
        """初始化数据库连接，设置 JSON 编解码器"""
        # 设置 jsonb 类型的编解码器
        await conn.set_type_codec(
            'jsonb',
            encoder=lambda v: json.dumps(v),
            decoder=lambda v: json.loads(v),
            schema='pg_catalog'
        )
        # 设置 json 类型的编解码器
        await conn.set_type_codec(
            'json',
            encoder=lambda v: json.dumps(v),
            decoder=lambda v: json.loads(v),
            schema='pg_catalog'
        )
    
    async def close(self):
        """关闭数据库连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("数据库连接池已关闭")
    
    # ============================================================
    # 任务创建
    # ============================================================
    
    async def create_task(
        self,
        task_type: str,
        title: str,
        description: str = None,
        priority: str = "normal",
        params: Dict[str, Any] = None,
        agent_id: str = None,
        parent_task_id: str = None,
        timeout_minutes: int = 30,
        max_retries: int = 3,
        agent_type: str = None
    ) -> Optional[str]:
        """
        创建新任务
        
        Args:
            task_type: 任务类型（search/write/code/review/analyze/design/layout/custom）
            title: 任务标题
            description: 任务描述（可选）
            priority: 优先级（low/normal/high/urgent），默认 normal
            params: 任务参数（可选）
            agent_id: 指定执行智能体ID（可选）
            parent_task_id: 父任务ID（支持子任务，可选）
            timeout_minutes: 超时时间（分钟），默认 30
            max_retries: 最大重试次数，默认 3
            agent_type: 智能体类型（coder/researcher/writer/reviewer/analyst/browser/designer/layout）
                       【重要】只有 'coder' 类型才会保存到数据库，其他类型直接返回 None
        
        Returns:
            task_id: 任务ID（UUID字符串）
            None: 非小码任务，不保存到数据库
        
        Raises:
            PermissionDeniedError: 无权限创建任务
            ValueError: 参数验证失败
            Exception: 数据库操作失败
        
        设计决策（2026-03-16）:
            - 只有小码（team-coder）的任务才持久化到数据库
            - 其他智能体（小搜、小写、小审等）的任务是一次性的，不需要保存
            - 这样可以避免数据混乱，减少数据库负担
        
        权限规则（2026-03-17 憨货亲定）:
            - 只有傻妞能创建任务（写入 parallel_tasks）
            - 小码池只能读取任务，不能创建
        """
        # ============================================================
        # 【权限校验】只有傻妞能创建任务
        # ============================================================
        # 获取调用者 agent_id（从参数或环境变量）
        caller_agent_id = agent_id or params.get('creator_agent_id') if params else None
        
        if caller_agent_id:
            if not check_parallel_tasks_permission(caller_agent_id, "write"):
                agent_name = resolve_agent_name(caller_agent_id)
                logger.warning(f"权限拒绝：智能体 {agent_name} 无权限创建任务")
                raise PermissionDeniedError(
                    f"智能体 {agent_name} 无权限创建任务。只有傻妞能创建任务。"
                )
        
        # ============================================================
        # 【核心逻辑】只有小码的任务才保存到数据库
        # ============================================================
        from .config import is_persistence_enabled
        
        # 如果指定了 agent_type，检查是否需要持久化
        if agent_type is not None and not is_persistence_enabled(agent_type):
            logger.info(f"非小码任务，不保存到数据库：{title} (agent_type={agent_type})")
            return None
        
        # 参数验证
        valid_types = ['search', 'write', 'code', 'review', 'analyze', 'design', 'layout', 'custom']
        if task_type not in valid_types:
            raise ValueError(f"无效的任务类型: {task_type}，有效类型: {valid_types}")
        
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if priority not in valid_priorities:
            raise ValueError(f"无效的优先级: {priority}，有效优先级: {valid_priorities}")
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            task_id = await conn.fetchval(
                """
                INSERT INTO parallel_tasks 
                (task_type, title, description, priority, params, agent_id, 
                 parent_task_id, timeout_minutes, max_retries)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
                """,
                task_type,
                title,
                description,
                priority,
                params or {},
                agent_id_to_uuid(agent_id) if agent_id else None,
                uuid.UUID(parent_task_id) if parent_task_id else None,
                timeout_minutes,
                max_retries
            )
        
        task_id_str = str(task_id)
        logger.info(f"任务创建成功: {task_id_str}, 类型: {task_type}, 优先级: {priority}")
        return task_id_str
    
    # ============================================================
    # 任务领取
    # ============================================================
    
    async def acquire_task(
        self,
        agent_id: str,
        task_types: List[str] = None,
        lock_duration_minutes: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        领取待执行任务
        
        使用数据库函数 acquire_pending_task() 实现原子性获取：
        - 自动创建任务锁
        - 自动更新任务状态为 running
        - 使用 FOR UPDATE SKIP LOCKED 避免并发冲突
        
        Args:
            agent_id: 智能体ID
            task_types: 可接受的任务类型列表（None 表示接受所有类型）
            lock_duration_minutes: 锁持续时间（分钟），默认 30
        
        Returns:
            任务信息字典，包含：
            - task_id: 任务ID
            - task_type: 任务类型
            - title: 任务标题
            - description: 任务描述
            - params: 任务参数
            - priority: 任务优先级
            - timeout_minutes: 超时时间
            如果没有可用任务，返回 None
        
        Raises:
            PermissionDeniedError: 无权限读取任务
            Exception: 数据库操作失败
        
        权限规则（2026-03-17 憨货亲定）:
            - 只有 5 个小码（team-coder1-5）能读取/领取任务
            - 其他智能体无权限
        """
        # ============================================================
        # 【权限校验】只有小码池能读取任务
        # ============================================================
        if not check_parallel_tasks_permission(agent_id, "read"):
            agent_name = resolve_agent_name(agent_id)
            logger.warning(f"权限拒绝：智能体 {agent_name} 无权限领取任务")
            raise PermissionDeniedError(
                f"智能体 {agent_name} 无权限领取任务。只有小码池能领取任务。"
            )
        
        pool = await self._get_pool()
        
        # 将任务类型转换为 PostgreSQL 数组格式
        task_types_pg = task_types if task_types else None
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM acquire_pending_task(
                    $1::uuid,
                    $2::task_type[],
                    $3
                )
                """,
                agent_id_to_uuid(agent_id),
                task_types_pg,
                lock_duration_minutes
            )
        
        if row:
            task = {
                'task_id': str(row['task_id']),
                'task_type': row['task_type'],
                'title': row['title'],
                'description': row['description'],
                'params': row['params'],
                'priority': row['priority'],
                'timeout_minutes': row['timeout_minutes']
            }
            logger.info(f"任务领取成功: {task['task_id']}, 类型: {task['task_type']}, 智能体: {agent_id}")
            return task
        else:
            logger.debug(f"无可用任务，智能体: {agent_id}")
            return None
    
    # ============================================================
    # 进度更新
    # ============================================================
    
    async def update_progress(
        self,
        task_id: str,
        progress_percent: int,
        status_message: str = ""
    ) -> bool:
        """
        更新任务进度
        
        使用数据库函数 update_task_progress() 实现：
        - 更新主表进度
        - 记录进度历史
        
        Args:
            task_id: 任务ID
            progress_percent: 进度百分比（0-100）
            status_message: 进度描述信息（可选）
        
        Returns:
            bool: 更新是否成功
        
        Raises:
            ValueError: 进度值超出范围
            Exception: 任务不存在或状态不正确
        """
        # 参数验证
        if not 0 <= progress_percent <= 100:
            raise ValueError(f"进度值必须在 0-100 范围内，当前值: {progress_percent}")
        
        pool = await self._get_pool()
        
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    "SELECT update_task_progress($1::uuid, $2, $3)",
                    uuid.UUID(task_id),
                    progress_percent,
                    status_message or None
                )
            
            logger.debug(f"任务进度更新: {task_id} -> {progress_percent}%")
            return True
        
        except Exception as e:
            logger.error(f"更新任务进度失败: {task_id}, 错误: {e}")
            raise
    
    # ============================================================
    # 任务完成（Phase 3 增强：自动写入记忆系统）
    # ============================================================
    
    async def complete_task(
        self,
        task_id: str,
        result_summary: Dict[str, Any] = None,
        create_memory: bool = True,
        memory_visibility: str = None
    ) -> Dict[str, Any]:
        """
        完成任务（自动写入记忆系统）
        
        使用数据库函数 complete_task() 实现：
        - 更新任务状态为 completed
        - 设置进度为 100%
        - 删除任务锁
        - 记录完成时间
        - 【Phase 3 新增】自动将任务结果写入记忆系统
        
        Args:
            task_id: 任务ID
            result_summary: 任务结果摘要（可选）
            create_memory: 是否自动创建记忆（默认 True）
            memory_visibility: 记忆可见性（private/shared），None 表示自动路由
        
        Returns:
            完成结果，包含：
            - success: 是否成功
            - task_id: 任务 ID
            - memory_id: 创建的记忆 ID（如果创建）
            - memory_table: 记忆存储的表（private/shared）
            - duration_seconds: 任务执行耗时（秒）
        
        Raises:
            Exception: 任务不存在或状态不正确
        """
        pool = await self._get_pool()
        result = {
            "success": False,
            "task_id": task_id,
            "memory_id": None,
            "memory_table": None,
            "duration_seconds": None
        }
        
        try:
            # ============================================================
            # 步骤 1：获取任务详情（用于创建记忆）
            # ============================================================
            task = await self.get_task(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            # 计算执行耗时
            duration_seconds = None
            if task.get('started_at') and task.get('completed_at'):
                started = datetime.fromisoformat(str(task['started_at']).replace('Z', '+00:00'))
                completed = datetime.fromisoformat(str(task['completed_at']).replace('Z', '+00:00'))
                duration_seconds = (completed - started).total_seconds()
            elif task.get('started_at'):
                started = datetime.fromisoformat(str(task['started_at']).replace('Z', '+00:00'))
                duration_seconds = (datetime.now(started.tzinfo) - started).total_seconds()
            
            result["duration_seconds"] = duration_seconds
            
            # ============================================================
            # 步骤 2：调用数据库函数完成任务
            # ============================================================
            async with pool.acquire() as conn:
                await conn.execute(
                    "SELECT complete_task($1::uuid, $2, NULL)",
                    uuid.UUID(task_id),
                    result_summary or {}
                )
            
            logger.info(f"任务完成: {task_id}, 耗时: {duration_seconds}s")
            
            # ============================================================
            # 步骤 3：【Phase 3 新增】自动写入记忆系统
            # ============================================================
            if create_memory and task.get('agent_id'):
                try:
                    memory_id = await self._create_task_memory(
                        task=task,
                        result_summary=result_summary,
                        duration_seconds=duration_seconds,
                        visibility=memory_visibility
                    )
                    
                    if memory_id:
                        # 更新任务的 memory_id 字段
                        async with pool.acquire() as conn:
                            await conn.execute(
                                "UPDATE parallel_tasks SET memory_id = $1 WHERE id = $2",
                                uuid.UUID(memory_id),
                                uuid.UUID(task_id)
                            )
                        
                        result["memory_id"] = memory_id
                        logger.info(f"任务记忆已创建: task_id={task_id}, memory_id={memory_id}")
                
                except Exception as e:
                    # 记忆创建失败不影响任务完成
                    logger.warning(f"创建任务记忆失败（不影响任务完成）: {e}")
            
            result["success"] = True
            return result
        
        except Exception as e:
            logger.error(f"完成任务失败: {task_id}, 错误: {e}")
            raise
    
    async def _create_task_memory(
        self,
        task: Dict[str, Any],
        result_summary: Dict[str, Any],
        duration_seconds: float,
        visibility: str = None
    ) -> Optional[str]:
        """
        为完成的任务创建记忆（内部方法）
        
        Args:
            task: 任务详情
            result_summary: 任务结果摘要
            duration_seconds: 执行耗时（秒）
            visibility: 记忆可见性（private/shared）
        
        Returns:
            记忆 ID，失败返回 None，没有文档时也返回 None
        """
        try:
            memory_client = get_memory_client()
            
            # ============================================================
            # 【核心逻辑】只保存有文档/资源地址的记忆
            # 憨货决策（2026-03-16）：
            #   - 公共记忆数据表只保存文档位置/资源地址
            #   - 没有文档的搜索结果不保存到记忆系统
            #   - 避免记忆系统被无用数据污染
            # ============================================================
            documents = []
            urls = []
            file_paths = []
            
            if result_summary:
                # 提取文档列表
                documents = result_summary.get('documents', [])
                urls = result_summary.get('urls', [])
                file_paths = result_summary.get('file_paths', [])
                
                # 兼容旧格式：检查 result_summary 顶层是否有 url
                if 'url' in result_summary and result_summary['url']:
                    urls.append(result_summary['url'])
                
                # 兼容旧格式：检查 results 列表中的 url
                results_list = result_summary.get('results', [])
                if isinstance(results_list, list):
                    for r in results_list:
                        if isinstance(r, dict):
                            if r.get('url'):
                                urls.append(r['url'])
                            if r.get('doc_url'):
                                urls.append(r['doc_url'])
            
            # 如果没有文档/资源，不保存到记忆系统
            if not documents and not urls and not file_paths:
                logger.info(
                    f"任务 {task.get('id')} 没有文档/资源地址，不保存到记忆系统"
                )
                return None
            
            # 获取任务信息
            task_type = task.get('task_type', 'custom')
            title = task.get('title', '未知任务')
            description = task.get('description', '')
            agent_name = task.get('agent_name', '未知智能体')
            project_id = task.get('project_id', '')
            
            # ============================================================
            # 构建文档记忆内容
            # ============================================================
            content_parts = [f"【文档记忆】{title}"]
            
            if description:
                desc_short = description[:200] + ('...' if len(description) > 200 else '')
                content_parts.append(f"描述：{desc_short}")
            
            # 添加文档信息
            if documents:
                content_parts.append(f"\n文档 ({len(documents)} 个):")
                for i, doc in enumerate(documents[:5], 1):  # 最多显示 5 个
                    doc_title = doc.get('title', '未知')
                    doc_url = doc.get('url', '')
                    content_parts.append(f"  {i}. {doc_title}")
                    if doc_url:
                        content_parts.append(f"     {doc_url}")
            
            # 添加 URL 信息
            if urls:
                unique_urls = list(set(urls))  # 去重
                content_parts.append(f"\n资源链接 ({len(unique_urls)} 个):")
                for i, url in enumerate(unique_urls[:10], 1):  # 最多显示 10 个
                    content_parts.append(f"  {i}. {url}")
            
            # 添加文件路径信息
            if file_paths:
                content_parts.append(f"\n文件路径 ({len(file_paths)} 个):")
                for i, path in enumerate(file_paths[:10], 1):  # 最多显示 10 个
                    content_parts.append(f"  {i}. {path}")
            
            if agent_name:
                content_parts.append(f"\n执行者：{agent_name}")
            
            content = "\n".join(content_parts)
            
            # ============================================================
            # 构建文档记忆元数据
            # 必须包含 url/title/source 字段
            # ============================================================
            metadata = {
                "task_id": str(task['id']),
                "task_type": task_type,
                "agent_name": agent_name,
                "project_id": project_id,
                "duration_seconds": duration_seconds,
                "created_at": datetime.now().isoformat(),
                
                # 文档记忆必须包含的字段
                "documents": documents,
                "urls": list(set(urls)) if urls else [],  # 去重
                "file_paths": file_paths,
                
                # 记忆来源
                "source": agent_name or "未知",
                "memory_category": "document"  # 标记为文档类型记忆
            }
            
            # ============================================================
            # 文档记忆统一使用 "fact" 类型，重要性 0.8（高优先级）
            # ============================================================
            memory_type = "fact"  # 事实型记忆（文档地址）
            importance = 0.8      # 文档记忆重要性高
            
            # 创建记忆
            create_result = await memory_client.create_memory(
                agent_id=str(task['agent_id']),
                content=content,
                memory_type=memory_type,
                importance=importance,
                metadata=metadata,
                auto_route=True,
                visibility=visibility
            )
            
            logger.info(
                f"文档记忆创建成功: task_id={task['id']}, "
                f"documents={len(documents)}, urls={len(urls)}"
            )
            
            return create_result.get('memory_id')
        
        except Exception as e:
            logger.error(f"创建文档记忆失败: {e}")
            return None
    
    # ============================================================
    # 任务失败
    # ============================================================
    
    async def fail_task(
        self,
        task_id: str,
        error_message: str,
        retry: bool = True
    ) -> bool:
        """
        标记任务失败
        
        使用数据库函数 fail_task() 实现：
        - 如果允许重试且未超过最大重试次数，则重置为 pending
        - 否则标记为 failed
        - 删除任务锁
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            retry: 是否允许重试，默认 True
        
        Returns:
            bool: True 表示已重试，False 表示已标记为失败
        
        Raises:
            Exception: 任务不存在
        """
        pool = await self._get_pool()
        
        try:
            async with pool.acquire() as conn:
                retried = await conn.fetchval(
                    "SELECT fail_task($1::uuid, $2, $3)",
                    uuid.UUID(task_id),
                    error_message,
                    retry
                )
            
            if retried:
                logger.warning(f"任务失败，已重试: {task_id}, 错误: {error_message}")
            else:
                logger.error(f"任务失败，已标记: {task_id}, 错误: {error_message}")
            
            return retried
        
        except Exception as e:
            logger.error(f"标记任务失败时出错: {task_id}, 错误: {e}")
            raise
    
    # ============================================================
    # 任务查询
    # ============================================================
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        查询任务详情
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务信息字典，包含所有字段。如果任务不存在，返回 None
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    pt.*,
                    (SELECT json_agg(tph ORDER BY tph.created_at DESC)
                     FROM task_progress_history tph 
                     WHERE tph.task_id = pt.id) as progress_history
                FROM parallel_tasks pt
                WHERE pt.id = $1
                """,
                uuid.UUID(task_id)
            )
        
        if row:
            task = dict(row)
            # 转换 UUID 为字符串
            task['id'] = str(task['id'])
            if task.get('agent_id'):
                task['agent_id'] = str(task['agent_id'])
            if task.get('parent_task_id'):
                task['parent_task_id'] = str(task['parent_task_id'])
            if task.get('memory_id'):
                task['memory_id'] = str(task['memory_id'])
            return task
        return None
    
    async def list_tasks(
        self,
        status: str = None,
        task_type: str = None,
        agent_id: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            status: 按状态过滤（可选）
            task_type: 按类型过滤（可选）
            agent_id: 按智能体过滤（可选）
            limit: 返回数量限制，默认 50
            offset: 偏移量，默认 0
        
        Returns:
            任务列表
        """
        pool = await self._get_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if task_type:
            conditions.append(f"task_type = ${param_idx}")
            params.append(task_type)
            param_idx += 1
        
        if agent_id:
            conditions.append(f"agent_id = ${param_idx}")
            params.append(agent_id_to_uuid(agent_id))
            param_idx += 1
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT * FROM parallel_tasks
            {where_clause}
            ORDER BY 
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                END,
                created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        tasks = []
        for row in rows:
            task = dict(row)
            task['id'] = str(task['id'])
            if task.get('agent_id'):
                task['agent_id'] = str(task['agent_id'])
            tasks.append(task)
        
        return tasks
    
    # ============================================================
    # 统计信息
    # ============================================================
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        使用数据库函数 get_task_statistics() 实现：
        - 按状态统计任务数量
        - 计算平均执行时间
        
        Returns:
            统计信息字典，包含：
            - by_status: 按状态分组的统计
            - total: 总任务数
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM get_task_statistics()")
        
        stats = {
            'by_status': {},
            'total': 0
        }
        
        for row in rows:
            status = row['status']
            stats['by_status'][status] = {
                'count': row['count'],
                'oldest_pending': str(row['oldest_pending']) if row['oldest_pending'] else None,
                'avg_duration': str(row['avg_duration']) if row['avg_duration'] else None
            }
            stats['total'] += row['count']
        
        logger.debug(f"任务统计: {stats}")
        return stats
    
    # ============================================================
    # 锁清理
    # ============================================================
    
    async def cleanup_expired_locks(self) -> int:
        """
        清理过期的任务锁
        
        使用数据库函数 cleanup_expired_locks() 实现：
        - 将过期锁对应的 running 任务重置为 pending
        - 删除过期锁
        
        Returns:
            int: 清理的锁数量
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT cleanup_expired_locks()")
        
        if count > 0:
            logger.info(f"清理过期锁: {count} 个")
        return count


# ============================================================
# 同步包装器（用于不支持异步的场景）
# ============================================================

class TaskServiceSync:
    """
    TaskService 的同步版本
    
    提供与 TaskService 相同的 API，但使用同步方法调用
    内部使用 asyncio.run() 包装异步方法
    """
    
    def __init__(self, db_url: str = None):
        self._async_service = TaskService(db_url)
    
    def _run(self, coro):
        """运行异步协程"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop:
            # 如果已有事件循环，创建新线程运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)
    
    def create_task(self, **kwargs) -> str:
        return self._run(self._async_service.create_task(**kwargs))
    
    def acquire_task(self, **kwargs) -> Optional[Dict]:
        return self._run(self._async_service.acquire_task(**kwargs))
    
    def update_progress(self, **kwargs) -> bool:
        return self._run(self._async_service.update_progress(**kwargs))
    
    def complete_task(self, **kwargs) -> Dict[str, Any]:
        """
        完成任务（同步版本）
        
        返回：
            - success: 是否成功
            - task_id: 任务 ID
            - memory_id: 创建的记忆 ID（如果有）
            - duration_seconds: 执行耗时
        """
        return self._run(self._async_service.complete_task(**kwargs))
    
    def fail_task(self, **kwargs) -> bool:
        return self._run(self._async_service.fail_task(**kwargs))
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        return self._run(self._async_service.get_task(task_id))
    
    def get_task_statistics(self) -> Dict:
        return self._run(self._async_service.get_task_statistics())
    
    def cleanup_expired_locks(self) -> int:
        return self._run(self._async_service.cleanup_expired_locks())
    
    def close(self):
        self._run(self._async_service.close())


# ============================================================
# 便捷函数（用于快速创建任务记忆）
# ============================================================

async def create_task_memory(
    task_id: str,
    agent_id: str,
    content: str,
    task_type: str = "custom",
    metadata: Dict[str, Any] = None,
    visibility: str = None
) -> Optional[str]:
    """
    为任务创建记忆（便捷函数）
    
    Args:
        task_id: 任务 ID
        agent_id: 智能体 ID
        content: 记忆内容
        task_type: 任务类型
        metadata: 元数据
        visibility: 可见性
    
    Returns:
        记忆 ID
    """
    memory_client = get_memory_client()
    
    metadata = metadata or {}
    metadata["task_id"] = task_id
    metadata["task_type"] = task_type
    
    result = await memory_client.create_memory(
        agent_id=agent_id,
        content=content,
        memory_type="experience",
        importance=0.6,
        metadata=metadata,
        auto_route=True,
        visibility=visibility
    )
    
    return result.get('memory_id')