# ============================================================
# 示例 1：基础用法
# ============================================================
# 功能：演示 TaskService 的基本使用方法
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================

import asyncio
import logging
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.task_service import TaskService
from sdk.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    演示 TaskService 的基本使用方法
    
    流程：
        1. 创建任务服务实例
        2. 创建测试任务
        3. 查询任务详情
        4. 更新任务进度
        5. 完成任务
        6. 获取任务统计
    """
    
    print("=" * 60)
    print("示例 1：TaskService 基础用法")
    print("=" * 60)
    
    # ============================================================
    # 1. 创建任务服务实例
    # ============================================================
    print("\n[步骤 1] 创建任务服务实例...")
    service = TaskService()  # 从环境变量读取数据库连接
    
    try:
        # ============================================================
        # 2. 创建测试任务
        # ============================================================
        print("\n[步骤 2] 创建测试任务...")
        
        task_id = await service.create_task(
            task_type="code",
            title="示例代码任务",
            description="这是一个示例任务，用于演示 TaskService 的基本用法",
            priority="normal",
            params={
                "language": "python",
                "action": "demo"
            },
            timeout_minutes=10,
            max_retries=3
        )
        print(f"✅ 任务创建成功: {task_id}")
        
        # ============================================================
        # 3. 查询任务详情
        # ============================================================
        print("\n[步骤 3] 查询任务详情...")
        
        task = await service.get_task(task_id)
        print(f"任务类型: {task['task_type']}")
        print(f"任务标题: {task['title']}")
        print(f"任务状态: {task['status']}")
        print(f"任务优先级: {task['priority']}")
        print(f"任务参数: {task['params']}")
        
        # ============================================================
        # 4. 模拟领取任务（需要智能体 ID）
        # ============================================================
        print("\n[步骤 4] 模拟领取任务...")
        
        # 注意：实际使用时需要真实的智能体 ID（agents 表中的记录）
        # 这里我们直接更新任务状态来模拟
        agent_id = "00000000-0000-0000-0000-000000000001"  # 测试用智能体 ID
        
        try:
            task = await service.acquire_task(
                agent_id=agent_id,
                task_types=["code"]
            )
            
            if task:
                print(f"✅ 任务领取成功: {task['task_id']}")
            else:
                print("⚠️ 无可用任务（可能没有对应的智能体记录）")
                print("    直接演示进度更新和完成...")
        except Exception as e:
            print(f"⚠️ 领取任务失败（可能没有对应的智能体记录）: {e}")
            print("    跳过领取，直接演示其他功能...")
        
        # ============================================================
        # 5. 获取任务统计
        # ============================================================
        print("\n[步骤 5] 获取任务统计...")
        
        stats = await service.get_task_statistics()
        print(f"总任务数: {stats['total']}")
        print("按状态统计:")
        for status, info in stats['by_status'].items():
            print(f"  - {status}: {info['count']} 个")
        
        # ============================================================
        # 6. 清理过期锁
        # ============================================================
        print("\n[步骤 6] 清理过期锁...")
        
        count = await service.cleanup_expired_locks()
        print(f"✅ 清理了 {count} 个过期锁")
        
        # ============================================================
        # 7. 列出任务
        # ============================================================
        print("\n[步骤 7] 列出任务...")
        
        tasks = await service.list_tasks(limit=5)
        print(f"最近 {len(tasks)} 个任务:")
        for t in tasks:
            print(f"  - [{t['status']}] {t['title']} ({t['task_type']})")
        
        print("\n" + "=" * 60)
        print("示例完成！")
        print("=" * 60)
    
    finally:
        # 关闭连接池
        await service.close()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())