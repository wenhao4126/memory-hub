# ============================================================
# 示例 2：自定义 Worker + 任务完成流程
# ============================================================
# 功能：
#   1. 演示如何创建自定义的 Agent Worker
#   2. 演示完整的任务创建→领取→完成流程
# 作者：小码 🟡
# 日期：2026-03-16
# 更新：2026-03-16 - 添加完整的任务完成示例
# ============================================================

import asyncio
import logging
import sys
import os
import random

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.task_service import TaskService
from sdk.config import settings
from worker.agent_worker import AgentWorker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# 自定义 Worker：代码审查器
# ============================================================

class CodeReviewWorker(AgentWorker):
    """
    代码审查工作器
    
    功能：
        - 接收 code 类型任务
        - 模拟代码审查过程
        - 返回审查结果
    """
    
    def __init__(self, agent_id: str, task_service: TaskService):
        super().__init__(
            agent_id=agent_id,
            agent_type="review",  # 审查类型
            task_service=task_service,
            supported_types=["code"]  # 可以处理 code 类型任务
        )
    
    async def _process_task(self, task: dict) -> dict:
        """
        处理代码审查任务
        
        Args:
            task: 任务信息
        
        Returns:
            审查结果
        """
        task_id = task['task_id']
        params = task.get('params', {})
        
        logger.info(f"开始代码审查: {task_id}")
        
        # 更新进度：开始分析
        await self.update_progress(10, "正在加载代码文件...")
        await asyncio.sleep(1)
        
        # 更新进度：语法检查
        await self.update_progress(30, "正在进行语法检查...")
        await asyncio.sleep(1)
        
        # 更新进度：代码风格检查
        await self.update_progress(50, "正在进行代码风格检查...")
        await asyncio.sleep(1)
        
        # 更新进度：安全检查
        await self.update_progress(70, "正在进行安全检查...")
        await asyncio.sleep(1)
        
        # 更新进度：生成报告
        await self.update_progress(90, "正在生成审查报告...")
        await asyncio.sleep(1)
        
        # 模拟审查结果
        issues = [
            {"line": 10, "severity": "warning", "message": "建议添加类型注解"},
            {"line": 25, "severity": "info", "message": "可以使用列表推导简化代码"},
        ]
        
        result = {
            "status": "passed",
            "score": random.randint(70, 100),
            "issues": issues,
            "summary": f"代码质量良好，发现 {len(issues)} 个建议改进项"
        }
        
        logger.info(f"代码审查完成: {task_id}, 得分: {result['score']}")
        return result
    
    async def _on_task_complete(self, task: dict, result: dict):
        """任务完成回调"""
        logger.info(f"🎉 代码审查完成！得分: {result['score']}")
    
    async def _on_task_error(self, task: dict, error: str, retried: bool):
        """任务失败回调"""
        logger.error(f"❌ 代码审查失败: {error}")


# ============================================================
# 自定义 Worker：数据分析器
# ============================================================

class DataAnalysisWorker(AgentWorker):
    """
    数据分析工作器
    
    功能：
        - 接收 analyze 类型任务
        - 模拟数据分析过程
        - 返回分析结果
    """
    
    def __init__(self, agent_id: str, task_service: TaskService):
        super().__init__(
            agent_id=agent_id,
            agent_type="analyze",
            task_service=task_service,
            supported_types=["analyze"]
        )
    
    async def _process_task(self, task: dict) -> dict:
        """
        处理数据分析任务
        """
        task_id = task['task_id']
        params = task.get('params', {})
        
        logger.info(f"开始数据分析: {task_id}")
        
        # 模拟数据分析步骤
        steps = [
            (20, "正在加载数据..."),
            (40, "正在进行数据清洗..."),
            (60, "正在进行统计分析..."),
            (80, "正在生成可视化..."),
            (95, "正在编写分析报告...")
        ]
        
        for progress, message in steps:
            await self.update_progress(progress, message)
            await asyncio.sleep(0.5)
        
        # 模拟分析结果
        result = {
            "total_records": random.randint(1000, 10000),
            "valid_records": random.randint(900, 9500),
            "insights": [
                "用户活跃度在周末达到峰值",
                "转化率与访问时长正相关",
                "移动端用户占比超过 60%"
            ]
        }
        
        logger.info(f"数据分析完成: {task_id}")
        return result


# ============================================================
# 主函数
# ============================================================

async def main():
    """
    演示自定义 Worker 的使用
    """
    
    print("=" * 60)
    print("示例 2：自定义 Worker")
    print("=" * 60)
    
    # 创建任务服务
    service = TaskService()
    
    try:
        # 创建测试任务
        print("\n[步骤 1] 创建测试任务...")
        
        task_id = await service.create_task(
            task_type="code",
            title="代码审查测试任务",
            description="用于测试自定义 Worker 的代码审查功能",
            params={"file_path": "/path/to/code.py"}
        )
        print(f"✅ 任务创建成功: {task_id}")
        
        # 创建自定义 Worker（使用测试智能体 ID）
        print("\n[步骤 2] 创建自定义 Worker...")
        
        # 注意：实际使用时需要真实的智能体 ID
        test_agent_id = "00000000-0000-0000-0000-000000000001"
        
        code_reviewer = CodeReviewWorker(
            agent_id=test_agent_id,
            task_service=service
        )
        
        print(f"✅ Worker 创建成功: {code_reviewer.agent_type}")
        print(f"   支持的任务类型: {code_reviewer.supported_types}")
        
        # 注意：实际运行需要 agents 表中有对应的智能体记录
        # 这里仅演示 Worker 的创建方式
        
        print("\n[提示] 完整运行需要在数据库中创建智能体记录")
        print("       运行前请确保 agents 表中有对应的智能体")
        
        # 查看当前任务状态
        print("\n[步骤 3] 查看任务状态...")
        task = await service.get_task(task_id)
        print(f"任务状态: {task['status']}")
        
        print("\n" + "=" * 60)
        print("示例完成！")
        print("=" * 60)
        
        print("\n💡 使用说明:")
        print("   1. 继承 AgentWorker 类")
        print("   2. 实现 _process_task() 方法")
        print("   3. 可选重写 _on_task_complete() 和 _on_task_error()")
        print("   4. 调用 start() 启动工作循环")
        print("   5. 使用 update_progress() 更新进度")
    
    finally:
        await service.close()


# ============================================================
# 完整任务完成示例
# ============================================================

async def complete_task_example():
    """
    演示完整的任务完成流程
    
    流程：
        1. 创建任务
        2. 领取任务
        3. 执行任务（模拟）
        4. 完成任务（带文档信息）
        5. 验证结果
    """
    
    print("\n" + "=" * 60)
    print("📋 完整任务完成流程示例")
    print("=" * 60)
    
    # 创建任务服务实例
    service = TaskService()
    
    try:
        # ----------------------------------------------------
        # 步骤 1：创建任务
        # ----------------------------------------------------
        print("\n[步骤 1] 创建任务...")
        
        task_id = await service.create_task(
            task_type='code',           # 任务类型：代码开发
            title='测试任务完成功能',    # 任务标题
            description='验证任务完成流程是否正常工作',
            agent_type='coder'          # 指定智能体类型
        )
        
        if task_id:
            print(f"✅ 任务创建成功！")
            print(f"   任务 ID: {task_id}")
        else:
            print("❌ 任务创建失败！")
            return
        
        # ----------------------------------------------------
        # 步骤 2：领取任务
        # ----------------------------------------------------
        print("\n[步骤 2] 领取任务...")
        
        # 注意：acquire_task 需要智能体 ID（UUID 格式）
        # 使用 agents 表中存在的智能体 ID（小码）
        test_agent_id = "a1b2c3d4-1111-4000-8000-000000000003"
        
        task = await service.acquire_task(test_agent_id)
        
        if task:
            print(f"✅ 任务领取成功！")
            print(f"   任务标题: {task.get('title')}")
            print(f"   任务类型: {task.get('task_type')}")
        else:
            print("⚠️  没有可领取的任务（可能已被其他智能体领取）")
            # 如果领取失败，直接使用创建的任务 ID
            task = {'task_id': task_id, 'title': '测试任务完成功能'}
        
        # ----------------------------------------------------
        # 步骤 3：执行任务（模拟）
        # ----------------------------------------------------
        print("\n[步骤 3] 执行任务中...")
        
        # 模拟任务执行过程
        print("   [10%] 分析需求...")
        await asyncio.sleep(0.5)
        
        print("   [30%] 设计方案...")
        await asyncio.sleep(0.5)
        
        print("   [50%] 编写代码...")
        await asyncio.sleep(0.5)
        
        print("   [70%] 测试验证...")
        await asyncio.sleep(0.5)
        
        print("   [90%] 整理文档...")
        await asyncio.sleep(0.5)
        
        print("   [100%] 完成！")
        
        # ----------------------------------------------------
        # 步骤 4：完成任务（带文档信息）
        # ----------------------------------------------------
        print("\n[步骤 4] 提交任务结果...")
        
        # 准备任务结果摘要
        result_summary = {
            'status': 'completed',
            'message': '任务已成功完成',
            'documents': [
                {
                    'title': 'API 接口文档',
                    'url': 'https://example.com/docs/api',
                    'description': '新增的知识库搜索接口文档'
                },
                {
                    'title': '代码变更说明',
                    'url': 'https://example.com/docs/changes',
                    'description': '本次修改的详细说明'
                }
            ],
            'stats': {
                'files_changed': 3,
                'lines_added': 150,
                'lines_removed': 20
            }
        }
        
        # 调用 complete_task 完成任务
        # create_memory=True 会自动创建记忆记录
        # 使用领取的任务 ID，而不是创建的任务 ID
        result = await service.complete_task(
            task_id=task['task_id'],
            result_summary=result_summary,
            create_memory=True  # 创建记忆记录
        )
        
        if result:
            print(f"✅ 任务完成成功！")
            print(f"   记忆 ID: {result.get('memory_id', '未创建')}")
            print(f"   状态: {result.get('status', '未知')}")
        else:
            print("⚠️  任务完成，但返回结果为空")
        
        # ----------------------------------------------------
        # 步骤 5：验证结果
        # ----------------------------------------------------
        print("\n[步骤 5] 验证任务状态...")
        
        # 查询任务最终状态（使用领取的任务 ID）
        final_task = await service.get_task(task['task_id'])
        
        if final_task:
            print(f"✅ 任务状态验证成功！")
            print(f"   最终状态: {final_task.get('status')}")
            print(f"   完成时间: {final_task.get('completed_at', '未记录')}")
        else:
            print("⚠️  无法获取任务最终状态")
        
        # ----------------------------------------------------
        # 总结
        # ----------------------------------------------------
        print("\n" + "=" * 60)
        print("🎉 完整任务流程演示成功！")
        print("=" * 60)
        
        print("\n📌 关键步骤回顾：")
        print("   1. create_task()  - 创建新任务")
        print("   2. acquire_task() - 领取任务（指定智能体 ID）")
        print("   3. 执行任务       - 业务逻辑处理")
        print("   4. complete_task() - 完成任务（可选创建记忆）")
        print("   5. get_task()     - 验证最终状态")
        
        print("\n💡 最佳实践：")
        print("   - 完成任务时提供详细的 result_summary")
        print("   - 使用 documents 字段记录相关文档")
        print("   - 开启 create_memory 自动记录到知识库")
    
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭服务连接
        await service.close()


# ============================================================
# 程序入口
# ============================================================

if __name__ == "__main__":
    import sys
    
    # 根据命令行参数选择运行哪个示例
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        # 运行完整任务完成示例
        asyncio.run(complete_task_example())
    else:
        # 默认运行自定义 Worker 示例
        asyncio.run(main())
        
        # 提示用户可以运行完整示例
        print("\n" + "-" * 60)
        print("💡 提示: 运行以下命令查看完整任务完成流程：")
        print("   python examples/02_custom_worker.py --complete")
        print("-" * 60)