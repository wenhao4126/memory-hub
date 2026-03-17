#!/usr/bin/env python3
# ============================================================
# Worker 启动入口 - 支持 daemon 模式
# ============================================================
# 功能：启动单个小码 Worker 进程
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================
# 使用方法：
#   python worker_cli.py --agent-id team-coder1 --poll-interval 30
#   python worker_cli.py --agent-id team-coder1 --poll-interval 30 --daemon
# ============================================================

import asyncio
import argparse
import logging
import os
import sys
import signal
from typing import Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker.agent_worker import SimpleWorker
from sdk.task_service import TaskService
from sdk.config import get_database_url

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerCLI:
    """Worker 命令行接口"""
    
    def __init__(self, agent_id: str, poll_interval: int = 30):
        self.agent_id = agent_id
        self.poll_interval = poll_interval
        self.worker: Optional[SimpleWorker] = None
        self._stop_event = asyncio.Event()
    
    async def run(self):
        """运行 Worker"""
        logger.info(f"启动 Worker: {self.agent_id}")
        
        # 创建任务服务
        database_url = get_database_url()
        task_service = TaskService(database_url)
        
        # 创建 Worker（使用简单的处理器）
        # 注意：agent_type 必须是 'coder' 而不是 'code'，才能启用数据库持久化
        self.worker = SimpleWorker(
            agent_id=self.agent_id,
            agent_type="coder",
            task_service=task_service,
            handler=self._handle_task
        )
        
        # 注册信号处理器
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._signal_handler)
        
        try:
            # 启动工作循环
            await self.worker.start(poll_interval=self.poll_interval)
        except asyncio.CancelledError:
            logger.info("Worker 被取消")
        finally:
            await task_service.close()
    
    async def _handle_task(self, task: dict) -> dict:
        """
        处理任务
        
        Args:
            task: 任务信息
        
        Returns:
            任务结果
        """
        task_id = task.get('task_id', 'unknown')
        task_type = task.get('task_type', 'code')
        title = task.get('title', '未命名任务')
        params = task.get('params', {})
        
        logger.info(f"[{self.agent_id}] 开始处理任务: {title}")
        logger.info(f"  任务ID: {task_id}")
        logger.info(f"  任务类型: {task_type}")
        
        try:
            # 模拟处理过程
            # TODO: 在这里实现真正的任务处理逻辑
            # 例如：调用代码生成、执行测试等
            
            # 更新进度
            await self.worker.update_progress(10, "初始化...")
            await asyncio.sleep(1)
            
            await self.worker.update_progress(30, "分析任务...")
            await asyncio.sleep(1)
            
            await self.worker.update_progress(50, "执行中...")
            await asyncio.sleep(2)
            
            await self.worker.update_progress(80, "完成收尾...")
            await asyncio.sleep(1)
            
            await self.worker.update_progress(100, "完成")
            
            result = {
                'status': 'success',
                'message': f'任务 {title} 已完成',
                'output': f'这是任务 {task_id} 的处理结果'
            }
            
            logger.info(f"[{self.agent_id}] 任务完成: {title}")
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] 任务失败: {e}")
            raise
    
    def _signal_handler(self):
        """处理停止信号"""
        logger.info(f"收到停止信号，正在关闭 Worker...")
        self._stop_event.set()
        if self.worker:
            asyncio.create_task(self.worker.stop())


def daemonize():
    """
    将进程转为守护进程（Unix/Linux）
    
    参考：Python daemon 模式的标准实现
    """
    # 第一次 fork，创建子进程
    pid = os.fork()
    if pid > 0:
        # 父进程退出
        sys.exit(0)
    
    # 子进程成为新的会话组长
    os.setsid()
    
    # 第二次 fork，确保不会获得 TTY
    pid = os.fork()
    if pid > 0:
        # 父进程退出
        sys.exit(0)
    
    # 重定向标准文件描述符
    sys.stdout.flush()
    sys.stderr.flush()
    
    # 将 stdin、stdout、stderr 重定向到 /dev/null
    with open('/dev/null', 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())
    with open('/dev/null', 'a+') as devnull:
        os.dup2(devnull.fileno(), sys.stdout.fileno())
        os.dup2(devnull.fileno(), sys.stderr.fileno())
    
    # 切换工作目录
    os.chdir('/')
    
    # 设置文件创建掩码
    os.umask(0)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='小码 Worker 启动器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 前台运行
  python worker_cli.py --agent-id team-coder1 --poll-interval 30
  
  # 后台运行（守护进程模式）
  python worker_cli.py --agent-id team-coder1 --poll-interval 30 --daemon
        """
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        required=True,
        help='智能体 ID（如：team-coder1）'
    )
    
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=30,
        help='轮询间隔（秒），默认 30 秒'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='以守护进程模式运行（后台运行）'
    )
    
    parser.add_argument(
        '--pid-file',
        type=str,
        default=None,
        help='PID 文件路径（可选）'
    )
    
    args = parser.parse_args()
    
    # 守护进程模式
    if args.daemon:
        print(f"启动守护进程: {args.agent_id}")
        daemonize()
    
    # 写入 PID 文件
    if args.pid_file:
        with open(args.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    # 创建并运行 Worker
    cli = WorkerCLI(
        agent_id=args.agent_id,
        poll_interval=args.poll_interval
    )
    
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        logger.info("Worker 已停止")
    finally:
        # 清理 PID 文件
        if args.pid_file and os.path.exists(args.pid_file):
            os.remove(args.pid_file)


if __name__ == '__main__':
    main()