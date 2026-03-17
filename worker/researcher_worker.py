# ============================================================
# 多智能体并行任务系统 - Researcher Worker
# ============================================================
# 功能：小搜（研究员）工作器，负责信息采集和搜索任务
# 作者：小码 🟡
# 日期：2026-03-17
# ============================================================
# 设计说明：
#   - 不使用数据库持久化（一次性任务）
#   - 完成任务后发送飞书通知
#   - 通过 execute_direct() 方法执行一次性任务
# ============================================================

import asyncio
import logging
from typing import Dict, Any, Optional

from worker.agent_worker import AgentWorker

# 配置日志
logger = logging.getLogger(__name__)


class ResearcherWorker(AgentWorker):
    """
    小搜工作器 - 信息采集专家
    
    功能：
        - 执行搜索任务
        - 信息收集和整理
        - 完成后发送飞书通知
    
    使用方法：
        # 直接执行任务（不使用数据库）
        worker = ResearcherWorker(agent_id="team-researcher1")
        result = await worker.execute_direct("搜索 AI 新闻", {"source": "twitter"})
    """
    
    def __init__(self, agent_id: str = "team-researcher1"):
        """
        初始化小搜工作器
        
        Args:
            agent_id: 智能体 ID（默认：team-researcher1）
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="researcher",
            task_service=None,  # 不使用数据库
            supported_types=["search"]
        )
        
        logger.info(f"小搜工作器初始化: {agent_id}")
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理搜索任务
        
        Args:
            task: 任务信息
        
        Returns:
            任务结果
        """
        task_id = task.get('task_id', 'unknown')
        title = task.get('title', '未命名任务')
        params = task.get('params', {})
        
        logger.info(f"[{self.agent_id}] 开始处理搜索任务: {title}")
        
        try:
            # 模拟搜索过程
            # TODO: 实现真正的搜索逻辑（调用 agent-reach skill）
            
            await asyncio.sleep(1)  # 模拟处理时间
            
            result = {
                'status': 'completed',
                'summary': f'搜索任务 "{title}" 已完成',
                'results': [],
                'message': '搜索完成'
            }
            
            logger.info(f"[{self.agent_id}] 搜索任务完成: {title}")
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] 搜索任务失败: {e}")
            raise


# ============================================================
# 小搜池 - 管理多个小搜工作器
# ============================================================

class ResearcherPool:
    """
    小搜池 - 管理多个小搜工作器
    
    注意：小搜不使用数据库持久化，这个池主要用于批量创建和管理
    """
    
    def __init__(self, pool_size: int = 2):
        """
        初始化小搜池
        
        Args:
            pool_size: 池大小（默认 2 个）
        """
        self.pool_size = pool_size
        self.workers = [
            ResearcherWorker(agent_id=f"team-researcher{i+1}")
            for i in range(pool_size)
        ]
        
        logger.info(f"小搜池初始化，共 {pool_size} 个工作器")
    
    async def execute_task(self, task_description: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行任务（选择第一个可用的工作器）
        
        Args:
            task_description: 任务描述
            params: 任务参数
        
        Returns:
            任务结果
        """
        # 选择第一个工作器
        worker = self.workers[0]
        return await worker.execute_direct(task_description, params)