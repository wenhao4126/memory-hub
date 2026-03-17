# ============================================================
# 示例 3：多 Worker 并发
# ============================================================
# 功能：演示如何同时运行多个 Worker 并发处理任务
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================

import asyncio
import logging
import sys
import os
import random
import uuid

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.task_service import TaskService
from sdk.config import settings
from worker.agent_worker import AgentWorker, WorkerPool, SimpleWorker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# 自定义 Worker 类
# ============================================================

class SearchWorker(AgentWorker):
    """搜索工作器"""
    
    async def _process_task(self, task: dict) -> dict:
        """处理搜索任务"""
        await self.update_progress(20, "正在连接搜索引擎...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.update_progress(50, "正在执行搜索...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.update_progress(80, "正在整理结果...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        return {
            "results_count": random.randint(10, 100),
            "top_results": ["结果1", "结果2", "结果3"]
        }


class WriteWorker(AgentWorker):
    """写作工作器"""
    
    async def _process_task(self, task: dict) -> dict:
        """处理写作任务"""
        await self.update_progress(30, "正在分析需求...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.update_progress(60, "正在生成内容...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.update_progress(90, "正在优化表达...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        return {
            "word_count": random.randint(500, 2000),
            "content": "这是一篇示例文章..."
        }


class CodeWorker(AgentWorker):
    """代码工作器"""
    
    async def _process_task(self, task: dict) -> dict:
        """处理代码任务"""
        await self.update_progress(25, "正在分析需求...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.update_progress(50, "正在编写代码...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.update_progress(75, "正在测试...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        await self.update_progress(95, "正在优化...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        return {
            "lines": random.randint(50, 500),
            "files": random.randint(1, 10),
            "status": "completed"
        }


# ============================================================
# 主函数
# ============================================================

async def main():
    """
    演示多 Worker 并发处理任务
    """
    
    print("=" * 60)
    print("示例 3：多 Worker 并发")
    print("=" * 60)
    
    service = TaskService()
    
    try:
        # ============================================================
        # 1. 创建测试任务
        # ============================================================
        print("\n[步骤 1] 创建多个测试任务...")
        
        tasks = []
        task_configs = [
            ("search", "搜索 AI 相关新闻"),
            ("search", "搜索技术博客文章"),
            ("write", "撰写产品说明文档"),
            ("write", "撰写用户手册"),
            ("code", "开发用户登录功能"),
            ("code", "开发数据导出功能"),
        ]
        
        for task_type, title in task_configs:
            task_id = await service.create_task(
                task_type=task_type,
                title=title,
                priority=random.choice(["low", "normal", "high"])
            )
            tasks.append(task_id)
            print(f"   ✅ 创建任务: {title} ({task_type})")
        
        print(f"\n共创建 {len(tasks)} 个任务")
        
        # ============================================================
        # 2. 创建 Worker 池
        # ============================================================
        print("\n[步骤 2] 创建 Worker 池...")
        
        pool = WorkerPool()
        
        # 注意：实际使用时需要真实的智能体 ID（agents 表中的记录）
        # 这里使用测试 ID，实际运行需要在数据库中创建对应的智能体
        
        # 创建 2 个搜索 Worker
        for i in range(2):
            worker = SearchWorker(
                agent_id=str(uuid.uuid4()),  # 实际使用时应使用真实的智能体 ID
                agent_type="search",
                task_service=service
            )
            pool.register_worker(worker)
            print(f"   ✅ 注册搜索 Worker #{i+1}")
        
        # 创建 2 个写作 Worker
        for i in range(2):
            worker = WriteWorker(
                agent_id=str(uuid.uuid4()),
                agent_type="write",
                task_service=service
            )
            pool.register_worker(worker)
            print(f"   ✅ 注册写作 Worker #{i+1}")
        
        # 创建 2 个代码 Worker
        for i in range(2):
            worker = CodeWorker(
                agent_id=str(uuid.uuid4()),
                agent_type="code",
                task_service=service
            )
            pool.register_worker(worker)
            print(f"   ✅ 注册代码 Worker #{i+1}")
        
        print(f"\n共注册 {len(pool.workers)} 个 Worker")
        
        # ============================================================
        # 3. 查看工作池状态
        # ============================================================
        print("\n[步骤 3] 查看工作池状态...")
        
        status = pool.get_status()
        print(f"总 Worker 数: {status['total_workers']}")
        for w in status['workers']:
            print(f"   - {w['agent_type']}: 支持类型 {w['supported_types']}")
        
        # ============================================================
        # 4. 使用 SimpleWorker（简化版）
        # ============================================================
        print("\n[步骤 4] 演示 SimpleWorker 用法...")
        
        async def simple_handler(task: dict) -> dict:
            """简单任务处理器"""
            await asyncio.sleep(1)
            return {"processed": True, "task_id": task['task_id']}
        
        simple_worker = SimpleWorker(
            agent_id=str(uuid.uuid4()),
            agent_type="custom",
            task_service=service,
            handler=simple_handler,
            supported_types=["custom"]
        )
        print(f"   ✅ 创建 SimpleWorker: {simple_worker.agent_type}")
        
        # ============================================================
        # 5. 获取任务统计
        # ============================================================
        print("\n[步骤 5] 获取任务统计...")
        
        stats = await service.get_task_statistics()
        print(f"总任务数: {stats['total']}")
        for status_name, info in stats['by_status'].items():
            print(f"   - {status_name}: {info['count']} 个")
        
        # ============================================================
        # 6. 说明
        # ============================================================
        print("\n" + "=" * 60)
        print("⚠️ 注意事项")
        print("=" * 60)
        print("""
实际运行 Worker 需要满足以下条件：

1. 数据库中存在对应的智能体记录（agents 表）
   - 可以通过插入测试数据创建：
     INSERT INTO agents (id, name, type) 
     VALUES ('uuid-here', '小搜-1', 'search');

2. 环境变量配置正确
   - DATABASE_URL 或 DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD

3. 启动 Worker
   - await pool.start_all(poll_interval=5)  # 开始轮询任务
   - await pool.stop_all()                  # 停止所有 Worker

4. 并发控制
   - 通过 FOR UPDATE SKIP LOCKED 保证任务不被重复领取
   - 通过 task_locks 表实现分布式锁
   - 锁过期时间默认 30 分钟
""")
        
        print("=" * 60)
        print("示例完成！")
        print("=" * 60)
        
        print("\n💡 使用说明:")
        print("   1. 使用 WorkerPool 管理多个 Worker")
        print("   2. 调用 register_worker() 注册 Worker")
        print("   3. 调用 start_all() 启动所有 Worker")
        print("   4. 调用 stop_all() 停止所有 Worker")
        print("   5. Worker 会自动轮询并处理任务")
    
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())