# ============================================================
# 多智能体并行任务系统 - Agent Worker
# ============================================================
# 功能：智能体工作器基类，处理任务轮询和执行
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================
# 修改记录（2026-03-16）：
# - 只有 coder 类型使用数据库持久化
# - 其他智能体类型不使用数据库，直接执行任务
# - 添加 agent_type 参数，用于判断是否需要持久化
# ============================================================

import asyncio
import logging
import uuid
import subprocess
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable

from sdk.task_service import TaskService
from sdk.config import is_persistence_enabled, get_agent_type

# 配置日志
logger = logging.getLogger(__name__)


class AgentWorker(ABC):
    """
    智能体工作器基类
    
    功能：
        - 自动轮询待执行任务（仅 coder 类型）
        - 调用子类实现的 _process_task() 处理任务
        - 自动更新进度、完成/失败状态
        - 支持停止信号
    
    设计决策（2026-03-16）：
        - 只有 coder 类型（小码）使用数据库任务持久化
        - 其他智能体类型直接执行任务，不需要数据库
        - 这样可以避免数据混乱，减少数据库负担
    
    使用方法：
        1. 继承 AgentWorker 类
        2. 实现 _process_task() 方法（具体任务处理逻辑）
        3. 可选：重写 _on_task_complete() 和 _on_task_error() 回调
        4. 调用 start() 启动工作循环
    
    示例：
        class MyWorker(AgentWorker):
            async def _process_task(self, task: dict) -> dict:
                # 实现具体任务处理逻辑
                await self.update_progress(50, "处理中...")
                result = await do_something(task)
                return result
        
        worker = MyWorker("agent-001", "code", task_service)
        await worker.start()
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        task_service: TaskService = None,
        supported_types: List[str] = None
    ):
        """
        初始化工作器
        
        Args:
            agent_id: 智能体ID（UUID字符串）
            agent_type: 智能体类型（如 "code", "search", "write" 等）
            task_service: TaskService 实例（可选，只有 coder 需要传入）
            supported_types: 支持的任务类型列表（可选，默认根据 agent_type 推断）
        
        设计说明：
            - agent_type 为 'coder' 时，需要传入 task_service
            - 其他类型可以不传 task_service，直接执行任务
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        
        # ============================================================
        # 【核心逻辑】只有小码使用数据库持久化
        # ============================================================
        if is_persistence_enabled(agent_type):
            # 小码：使用数据库任务服务
            if task_service is None:
                raise ValueError(f"小码（coder）必须传入 task_service 参数")
            self.task_service = task_service
            logger.info(f"小码模式启用：使用数据库持久化任务")
        else:
            # 其他智能体：不使用数据库
            self.task_service = None
            logger.info(f"一次性任务模式：{agent_type} 不使用数据库持久化")
        
        # 根据智能体类型推断支持的任务类型
        if supported_types is None:
            # 注意：agent_type 可能是 'researcher'，但任务类型是 'search'
            type_mapping = {
                'search': ['search'],
                'researcher': ['search'],  # 小搜的 agent_type 是 researcher，任务类型是 search
                'write': ['write'],
                'writer': ['write'],       # 小写
                'code': ['code'],
                'coder': ['code'],         # 小码
                'review': ['review'],
                'reviewer': ['review'],    # 小审
                'analyze': ['analyze'],
                'analyst': ['analyze'],    # 小析
                'design': ['design'],
                'designer': ['design'],    # 小图
                'layout': ['layout'],      # 小排
                'browser': ['custom'],     # 小览（浏览器操作）
            }
            self.supported_types = type_mapping.get(agent_type, ['custom'])
        else:
            self.supported_types = supported_types
        
        self.current_task_id: Optional[str] = None
        self._running = False
        self._stop_event = asyncio.Event()
        
        logger.info(f"AgentWorker 初始化: {agent_type} ({agent_id}), 支持类型: {self.supported_types}")
    
    # ============================================================
    # 生命周期控制
    # ============================================================
    
    async def start(self, poll_interval: int = 5):
        """
        启动工作循环
        
        Args:
            poll_interval: 轮询间隔（秒），默认 5 秒
        """
        self._running = True
        self._stop_event.clear()
        
        logger.info(f"工作器启动: {self.agent_type} ({self.agent_id})")
        
        while self._running and not self._stop_event.is_set():
            try:
                # 尝试获取任务
                task = await self._acquire_task()
                
                if task:
                    # 执行任务
                    await self._execute_task(task)
                else:
                    # 没有任务，等待一段时间
                    await asyncio.sleep(poll_interval)
            
            except asyncio.CancelledError:
                logger.info(f"工作器被取消: {self.agent_type}")
                break
            
            except Exception as e:
                logger.error(f"工作器异常: {e}", exc_info=True)
                await asyncio.sleep(10)  # 出错后等待一段时间再重试
        
        logger.info(f"工作器停止: {self.agent_type} ({self.agent_id})")
    
    async def stop(self):
        """停止工作器"""
        logger.info(f"正在停止工作器: {self.agent_type}")
        self._running = False
        self._stop_event.set()
    
    # ============================================================
    # 任务获取
    # ============================================================
    
    async def _acquire_task(self) -> Optional[Dict[str, Any]]:
        """
        获取待执行任务
        
        Returns:
            任务信息字典，如果没有可用任务返回 None
        
        设计说明：
            - 只有 coder 类型才会从数据库获取任务
            - 其他类型直接返回 None（直接执行模式）
        """
        # 非持久化模式：不获取任务
        if self.task_service is None:
            logger.debug(f"{self.agent_type} 非持久化模式，不获取数据库任务")
            return None
        
        # 持久化模式：从数据库获取任务
        task = await self.task_service.acquire_task(
            agent_id=self.agent_id,
            task_types=self.supported_types
        )
        
        if task:
            self.current_task_id = task['task_id']
            logger.info(f"{self.agent_type} 领取任务: {self.current_task_id}")
        
        return task
    
    # ============================================================
    # 任务执行
    # ============================================================
    
    async def _execute_task(self, task: Dict[str, Any]):
        """
        执行任务
        
        Args:
            task: 任务信息字典
        
        设计说明：
            - 持久化模式：更新数据库状态
            - 非持久化模式：直接执行，只打印日志
        """
        task_id = task.get('task_id', 'one-time-task')
        task_type = task.get('task_type', self.agent_type)
        params = task.get('params', {})
        
        try:
            logger.info(f"开始执行任务: {task_id}, 类型: {task_type}")
            
            # 调用子类实现的处理方法
            result = await self._process_task(task)
            
            # 完成任务
            if self.task_service is not None:
                # 持久化模式：更新数据库
                await self.task_service.complete_task(task_id, result)
            else:
                # 非持久化模式：只打印日志
                logger.info(f"[{self.agent_type}] 任务完成: {task_id}")
            
            # 触发完成回调
            await self._on_task_complete(task, result)
            
        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, 错误: {e}", exc_info=True)
            
            # 标记任务失败
            if self.task_service is not None:
                # 持久化模式：更新数据库
                retried = await self.task_service.fail_task(
                    task_id=task_id,
                    error_message=str(e),
                    retry=True
                )
            else:
                # 非持久化模式：只打印日志
                logger.error(f"[{self.agent_type}] 任务失败: {task_id}, 错误: {e}")
                retried = False
            
            # 触发失败回调
            await self._on_task_error(task, str(e), retried)
        
        finally:
            self.current_task_id = None
    
    # ============================================================
    # 进度更新（提供给子类使用的便捷方法）
    # ============================================================
    
    async def update_progress(self, progress_percent: int, status_message: str = ""):
        """
        更新当前任务进度
        
        Args:
            progress_percent: 进度百分比（0-100）
            status_message: 进度描述信息
        
        设计说明：
            - 只有 coder 类型才会更新数据库进度
            - 其他类型只打印日志
        """
        if self.task_service is None:
            # 非持久化模式：只打印日志
            logger.info(f"[{self.agent_type}] 进度: {progress_percent}% - {status_message}")
            return
        
        # 持久化模式：更新数据库
        if self.current_task_id:
            await self.task_service.update_progress(
                task_id=self.current_task_id,
                progress_percent=progress_percent,
                status_message=status_message
            )
    
    # ============================================================
    # 子类必须实现的方法
    # ============================================================
    
    @abstractmethod
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个任务（子类必须实现）
        
        Args:
            task: 任务信息字典，包含：
                - task_id: 任务ID
                - task_type: 任务类型
                - title: 任务标题
                - description: 任务描述
                - params: 任务参数
                - priority: 任务优先级
                - timeout_minutes: 超时时间
        
        Returns:
            任务结果字典
        
        Raises:
            Exception: 任务执行失败时抛出异常
        """
        pass
    
    # ============================================================
    # 直接执行模式（非持久化）
    # ============================================================
    
    async def execute_direct(self, task_description: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        直接执行任务（非持久化模式专用）
        
        用于一次性任务，不需要保存到数据库
        
        Args:
            task_description: 任务描述
            params: 任务参数
        
        Returns:
            任务结果字典
        
        示例：
            # 小搜直接执行搜索任务
            worker = ResearcherWorker(agent_id="xxx", agent_type="researcher")
            result = await worker.execute_direct("搜索 AI 新闻", {"source": "twitter"})
        """
        # 构建任务对象
        task = {
            'task_id': f"one-time-{uuid.uuid4()}",
            'task_type': self.agent_type,
            'title': task_description,
            'description': task_description,
            'params': params or {},
            'priority': 'normal',
            'timeout_minutes': 30
        }
        
        logger.info(f"[{self.agent_type}] 开始执行一次性任务: {task_description}")
        
        try:
            # 执行任务
            result = await self._process_task(task)
            logger.info(f"[{self.agent_type}] 一次性任务完成: {task_description}")
            
            # 触发完成回调（发送飞书通知）
            await self._on_task_complete(task, result)
            
            return result
        
        except Exception as e:
            logger.error(f"[{self.agent_type}] 一次性任务失败: {task_description}, 错误: {e}")
            # 触发失败回调（发送飞书通知）
            await self._on_task_error(task, str(e), retried=False)
            raise
    
    # ============================================================
    # 可选的回调方法
    # ============================================================
    
    async def _on_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]):
        """
        任务完成回调（子类可选重写）
        
        Args:
            task: 任务信息
            result: 任务结果
        
        Returns:
            包含消息的字典
        
        设计说明（2026-03-16）：
            - 小码池是 systemd 服务启动的，不是 sessions_spawn 启动的
            - OpenClaw 的自动通告机制不适用
            - 使用 OpenClaw CLI 主动发送消息到飞书
        
        修改记录（2026-03-16）：
            - 添加智能体中文名显示，让用户知道是哪个智能体完成的任务
        """
        logger.info(f"任务完成: {task['task_id']}")
        
        # 提取任务信息
        task_title = task.get('title', '未知任务')
        task_id = str(task.get('task_id', '未知'))
        
        # 提取结果摘要
        summary = result.get('summary', result.get('result_summary', result.get('message', '无')))
        
        # 构建完成消息（使用 agent_id 作为前缀，格式如 team-coder1）
        message = f"{self.agent_id}: ✅ 完成任务：{task_title}\n\n📋 任务ID：{task_id}\n📝 结果：{summary}"
        
        # ✅ 使用 OpenClaw CLI 发送消息到飞书
        # 注意：使用完整路径，避免 Worker 进程找不到命令
        import shutil
        openclaw_path = shutil.which('openclaw') or '/home/wen/.npm-global/bin/openclaw'
        
        try:
            result = subprocess.run([
                openclaw_path, 'message', 'send',
                '--channel', 'feishu',
                '--target', 'ou_c869d2aa0f7bacfefb13eb5fb7dd668a',
                '--message', message
            ], check=True, capture_output=True, text=True, timeout=30)
            
            # 记录 CLI 输出，便于调试
            if result.stdout:
                logger.info(f"CLI stdout: {result.stdout.strip()}")
            if result.stderr:
                logger.info(f"CLI stderr: {result.stderr.strip()}")
            
            logger.info(f"✅ 已发送飞书完成通知：{task_title}")
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 发送飞书通知超时：{task_title}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 发送飞书通知失败：{task_title}, 返回码: {e.returncode}, stdout: {e.stdout}, stderr: {e.stderr}")
        except Exception as e:
            logger.error(f"❌ 发送飞书通知异常：{task_title}, 错误: {e}")
        
        # 返回结果字典（供日志记录等用途）
        return {
            "status": "completed",
            "agent_name": self.agent_type,
            "task_title": task_title,
            "task_id": task_id,
            "summary": summary,
            "message": message
        }
    
    async def _on_task_error(self, task: Dict[str, Any], error: str, retried: bool):
        """
        任务失败回调（子类可选重写）
        
        Args:
            task: 任务信息
            error: 错误信息
            retried: 是否已重试
        
        Returns:
            包含消息的字典
        
        设计说明（2026-03-16）：
            - 小码池是 systemd 服务启动的，不是 sessions_spawn 启动的
            - OpenClaw 的自动通告机制不适用
            - 使用 OpenClaw CLI 主动发送消息到飞书
        
        修改记录（2026-03-16）：
            - 添加智能体中文名显示，让用户知道是哪个智能体失败的任务
        """
        # 提取任务信息
        task_title = task.get('title', '未知任务')
        task_id = str(task.get('task_id', '未知'))
        
        # 构建失败消息（使用 agent_id 作为前缀，格式如 team-coder1）
        if retried:
            logger.warning(f"任务失败（已重试）: {task_id}, 错误: {error}")
            message = f"{self.agent_id}: ❌ 任务失败：{task_title}\n\n📋 任务ID：{task_id}\n🔴 错误：{error}\n♻️ 已自动重试"
        else:
            logger.error(f"任务失败: {task_id}, 错误: {error}")
            message = f"{self.agent_id}: ❌ 任务失败：{task_title}\n\n📋 任务ID：{task_id}\n🔴 错误：{error}"
        
        # ✅ 使用 OpenClaw CLI 发送消息到飞书
        # 注意：使用完整路径，避免 Worker 进程找不到命令
        import shutil
        openclaw_path = shutil.which('openclaw') or '/home/wen/.npm-global/bin/openclaw'
        
        try:
            result = subprocess.run([
                openclaw_path, 'message', 'send',
                '--channel', 'feishu',
                '--target', 'ou_c869d2aa0f7bacfefb13eb5fb7dd668a',
                '--message', message
            ], check=True, capture_output=True, text=True, timeout=30)
            
            # 记录 CLI 输出，便于调试
            if result.stdout:
                logger.info(f"CLI stdout: {result.stdout.strip()}")
            if result.stderr:
                logger.info(f"CLI stderr: {result.stderr.strip()}")
            
            logger.info(f"✅ 已发送飞书失败通知：{task_title}")
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 发送飞书通知超时：{task_title}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 发送飞书通知失败：{task_title}, 返回码: {e.returncode}, stdout: {e.stdout}, stderr: {e.stderr}")
        except Exception as e:
            logger.error(f"❌ 发送飞书通知异常：{task_title}, 错误: {e}")
        
        # 返回结果字典（供日志记录等用途）
        return {
            "status": "failed",
            "agent_name": self.agent_type,
            "task_title": task_title,
            "task_id": task_id,
            "error": error,
            "retried": retried,
            "message": message
        }


# ============================================================
# 工作池 - 管理多个工作器
# ============================================================

class WorkerPool:
    """
    工作池 - 管理多个智能体工作器
    
    功能：
        - 注册多个工作器
        - 同时启动/停止所有工作器
        - 监控工作器状态
    
    示例：
        pool = WorkerPool()
        pool.register_worker(worker1)
        pool.register_worker(worker2)
        await pool.start_all()
        # ... 运行中 ...
        await pool.stop_all()
    """
    
    def __init__(self):
        self.workers: List[AgentWorker] = []
        self._tasks: List[asyncio.Task] = []
    
    def register_worker(self, worker: AgentWorker):
        """
        注册工作器
        
        Args:
            worker: AgentWorker 实例
        """
        self.workers.append(worker)
        logger.info(f"工作器注册: {worker.agent_type} ({worker.agent_id})")
    
    async def start_all(self, poll_interval: int = 5):
        """
        启动所有工作器
        
        Args:
            poll_interval: 轮询间隔（秒）
        """
        self._tasks = [
            asyncio.create_task(worker.start(poll_interval))
            for worker in self.workers
        ]
        logger.info(f"所有工作器已启动，共 {len(self.workers)} 个")
    
    async def stop_all(self):
        """停止所有工作器"""
        # 发送停止信号
        for worker in self.workers:
            await worker.stop()
        
        # 等待所有任务完成
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        logger.info("所有工作器已停止")
    
    async def wait_all(self):
        """等待所有工作器完成"""
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取工作池状态
        
        Returns:
            状态信息字典
        """
        return {
            'total_workers': len(self.workers),
            'workers': [
                {
                    'agent_id': w.agent_id,
                    'agent_type': w.agent_type,
                    'supported_types': w.supported_types,
                    'current_task': w.current_task_id,
                    'running': w._running
                }
                for w in self.workers
            ]
        }


# ============================================================
# 简单工作器 - 用于快速测试
# ============================================================

class SimpleWorker(AgentWorker):
    """
    简单工作器 - 使用回调函数处理任务
    
    用于快速创建工作器，无需继承类
    
    设计说明：
        - coder 类型：必须传入 task_service，使用数据库持久化
        - 其他类型：可以不传 task_service，使用直接执行模式
    
    示例：
        # 小码（持久化模式）
        worker = SimpleWorker(
            agent_id="agent-001",
            agent_type="code",
            task_service=service,  # 必须传入
            handler=my_handler
        )
        await worker.start()  # 轮询数据库任务
        
        # 小搜（直接执行模式）
        worker = SimpleWorker(
            agent_id="agent-002",
            agent_type="researcher",
            handler=my_handler
        )
        result = await worker.execute_direct("搜索 AI 新闻")  # 直接执行
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        task_service: TaskService = None,
        handler: Callable[[Dict], Dict] = None,
        supported_types: List[str] = None
    ):
        """
        初始化简单工作器
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            task_service: TaskService 实例（coder 必须传入，其他类型可选）
            handler: 任务处理函数（异步函数，接收 task 参数，返回 result）
            supported_types: 支持的任务类型列表
        """
        super().__init__(agent_id, agent_type, task_service, supported_types)
        self.handler = handler
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """调用处理函数"""
        if self.handler is None:
            raise ValueError("必须传入 handler 参数")
        return await self.handler(task)