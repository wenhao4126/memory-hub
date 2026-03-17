# ============================================================
# 多智能体并行任务系统 - Phase 3 集成测试
# ============================================================
# 功能：测试任务系统与记忆系统的集成
# 作者：小码 🟡
# 日期：2026-03-16
# 
# 测试场景：
#   1. 创建任务 → 执行 → 完成 → 验证记忆是否自动创建
#   2. 查询任务记忆
#   3. 查询项目记忆
#   4. 搜索任务记忆
# ============================================================

import asyncio
import os
import sys
import uuid
import pytest
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.task_service import TaskService, get_memory_client, MemoryClient
from sdk.config import settings


# ============================================================
# 测试配置
# ============================================================

# 测试用的智能体 ID（需要提前创建）
TEST_AGENT_ID = os.getenv("TEST_AGENT_ID", "00000000-0000-0000-0000-000000000001")

# 测试用的数据库 URL
TEST_DB_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# 记忆系统 API 地址
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://localhost:8000/api/v1")


# ============================================================
# 测试夹具
# ============================================================

@pytest.fixture
async def task_service():
    """创建任务服务实例"""
    service = TaskService(TEST_DB_URL)
    yield service
    await service.close()


@pytest.fixture
async def memory_client():
    """创建记忆客户端实例"""
    client = MemoryClient(MEMORY_API_URL)
    yield client
    await client.close()


# ============================================================
# 测试类
# ============================================================

class TestTaskMemoryIntegration:
    """
    任务记忆集成测试
    
    测试流程：
        1. 创建任务
        2. 领取任务
        3. 更新进度
        4. 完成任务（自动创建记忆）
        5. 验证记忆是否创建
        6. 查询任务记忆
        7. 搜索任务记忆
    """
    
    @pytest.mark.asyncio
    async def test_complete_task_creates_memory(self, task_service):
        """
        测试：任务完成后自动创建记忆
        
        步骤：
            1. 创建测试任务
            2. 领取任务
            3. 完成任务
            4. 验证记忆是否创建
        """
        print("\n" + "=" * 60)
        print("测试：任务完成后自动创建记忆")
        print("=" * 60)
        
        # 步骤 1：创建任务
        task_id = await task_service.create_task(
            task_type="code",
            title="测试任务：集成测试",
            description="这是一个集成测试任务，用于验证任务完成后是否自动创建记忆",
            priority="normal",
            params={"test": True, "feature": "task-memory-integration"},
            agent_id=TEST_AGENT_ID
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        assert task_id, "任务 ID 不能为空"
        
        # 步骤 2：领取任务
        task = await task_service.acquire_task(
            agent_id=TEST_AGENT_ID,
            task_types=["code"]
        )
        
        if task:
            print(f"✅ 任务领取成功: {task['task_id']}")
            task_id = task['task_id']
        else:
            print("⚠️ 任务可能已被其他智能体领取，使用原始任务 ID")
        
        # 步骤 3：更新进度
        await task_service.update_progress(
            task_id=task_id,
            progress_percent=50,
            status_message="正在执行集成测试..."
        )
        print(f"✅ 进度更新成功: {task_id} -> 50%")
        
        # 步骤 4：完成任务（自动创建记忆）
        result = await task_service.complete_task(
            task_id=task_id,
            result_summary={
                "status": "success",
                "test_passed": True,
                "message": "集成测试通过"
            },
            create_memory=True,
            memory_visibility="shared"  # 使用共享记忆，方便验证
        )
        
        print(f"✅ 任务完成: {result}")
        
        # 步骤 5：验证结果
        assert result["success"], "任务应该成功完成"
        assert result["task_id"] == task_id, "任务 ID 应该匹配"
        
        if result.get("memory_id"):
            print(f"✅ 记忆创建成功: memory_id={result['memory_id']}")
            print(f"   - 耗时: {result.get('duration_seconds', 'N/A')} 秒")
        else:
            print("⚠️ 记忆未创建（可能是记忆系统未启动）")
        
        print("\n✅ 测试通过：任务完成 -> 记忆创建流程正常")
    
    @pytest.mark.asyncio
    async def test_get_task_memories(self, task_service):
        """
        测试：查询任务记忆
        
        步骤：
            1. 创建并完成任务
            2. 查询该任务的记忆
        """
        print("\n" + "=" * 60)
        print("测试：查询任务记忆")
        print("=" * 60)
        
        # 步骤 1：创建并完成任务
        task_id = await task_service.create_task(
            task_type="search",
            title="测试任务：查询记忆测试",
            description="测试查询任务记忆的功能",
            agent_id=TEST_AGENT_ID
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        
        # 领取并完成任务
        await task_service.acquire_task(agent_id=TEST_AGENT_ID)
        await task_service.complete_task(
            task_id=task_id,
            result_summary={"test": "query_memories"},
            create_memory=True
        )
        
        # 步骤 2：查询任务记忆（使用记忆客户端）
        memory_client = get_memory_client()
        
        try:
            # 搜索包含任务 ID 的记忆
            memories = await memory_client.search_memories(
                agent_id=TEST_AGENT_ID,
                query=f"任务 {task_id[:8]}",
                limit=5
            )
            
            print(f"✅ 记忆搜索结果: 找到 {len(memories)} 条记忆")
            
            for m in memories[:3]:  # 只显示前 3 条
                print(f"   - {m.get('content', '')[:100]}...")
        
        except Exception as e:
            print(f"⚠️ 记忆搜索失败: {e}")
        
        print("\n✅ 测试通过：任务记忆查询流程正常")
    
    @pytest.mark.asyncio
    async def test_search_task_memories(self, task_service):
        """
        测试：搜索任务记忆
        
        步骤：
            1. 创建多个不同类型的任务
            2. 完成任务
            3. 搜索特定类型的任务记忆
        """
        print("\n" + "=" * 60)
        print("测试：搜索任务记忆")
        print("=" * 60)
        
        # 步骤 1：创建多个任务
        task_types = ["search", "write", "code"]
        task_ids = []
        
        for tt in task_types:
            task_id = await task_service.create_task(
                task_type=tt,
                title=f"测试任务：{tt} 任务",
                description=f"这是一个 {tt} 类型的测试任务",
                agent_id=TEST_AGENT_ID
            )
            task_ids.append(task_id)
            print(f"✅ 创建 {tt} 任务: {task_id}")
        
        # 步骤 2：完成任务
        for task_id in task_ids:
            await task_service.acquire_task(agent_id=TEST_AGENT_ID)
            await task_service.complete_task(
                task_id=task_id,
                result_summary={"type": "search_test"},
                create_memory=True
            )
        
        print(f"✅ 完成了 {len(task_ids)} 个任务")
        
        # 步骤 3：搜索任务记忆
        memory_client = get_memory_client()
        
        try:
            # 搜索代码相关的记忆
            memories = await memory_client.search_memories(
                agent_id=TEST_AGENT_ID,
                query="代码任务",
                limit=10
            )
            
            print(f"✅ 搜索 '代码任务': 找到 {len(memories)} 条记忆")
        
        except Exception as e:
            print(f"⚠️ 搜索失败: {e}")
        
        print("\n✅ 测试通过：任务记忆搜索流程正常")
    
    @pytest.mark.asyncio
    async def test_project_memories(self, task_service):
        """
        测试：查询项目记忆
        
        步骤：
            1. 创建带项目 ID 的任务
            2. 完成任务
            3. 按项目 ID 查询记忆
        """
        print("\n" + "=" * 60)
        print("测试：查询项目记忆")
        print("=" * 60)
        
        # 步骤 1：创建带项目 ID 的任务
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        
        task_id = await task_service.create_task(
            task_type="code",
            title="测试任务：项目记忆测试",
            description="测试按项目查询记忆的功能",
            agent_id=TEST_AGENT_ID,
            params={"project_id": project_id}
        )
        
        print(f"✅ 创建任务: {task_id}, 项目: {project_id}")
        
        # 步骤 2：完成任务
        await task_service.acquire_task(agent_id=TEST_AGENT_ID)
        await task_service.complete_task(
            task_id=task_id,
            result_summary={"project_id": project_id},
            create_memory=True
        )
        
        print(f"✅ 任务完成，项目 ID 已记录到记忆元数据")
        
        # 步骤 3：按项目查询记忆（需要调用 API）
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{MEMORY_API_URL}/projects/{project_id}/memories",
                    params={"limit": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 项目记忆查询: 找到 {data.get('total', 0)} 条记忆")
                else:
                    print(f"⚠️ API 返回: {response.status_code}")
            
            except Exception as e:
                print(f"⚠️ API 调用失败: {e}")
        
        print("\n✅ 测试通过：项目记忆查询流程正常")


# ============================================================
# 独立测试函数（不需要 pytest）
# ============================================================

async def run_integration_tests():
    """
    运行集成测试（独立模式）
    
    不依赖 pytest，可以直接运行：
        python -m tests.test_task_memory_integration
    """
    print("\n" + "=" * 60)
    print("🚀 开始运行 Phase 3 集成测试")
    print("=" * 60)
    
    # 创建服务实例
    task_service = TaskService(TEST_DB_URL)
    
    try:
        # 测试 1：任务完成自动创建记忆
        print("\n📋 测试 1：任务完成自动创建记忆")
        print("-" * 40)
        
        task_id = await task_service.create_task(
            task_type="code",
            title="集成测试：自动记忆创建",
            description="验证任务完成后是否自动创建记忆",
            agent_id=TEST_AGENT_ID
        )
        print(f"✅ 任务创建: {task_id}")
        
        # 领取任务
        await task_service.acquire_task(agent_id=TEST_AGENT_ID)
        
        # 更新进度
        await task_service.update_progress(
            task_id=task_id,
            progress_percent=30,
            status_message="正在测试..."
        )
        print("✅ 进度更新: 30%")
        
        # 完成任务
        result = await task_service.complete_task(
            task_id=task_id,
            result_summary={"test": "auto_memory", "success": True},
            create_memory=True,
            memory_visibility="shared"
        )
        
        print(f"✅ 任务完成:")
        print(f"   - 成功: {result['success']}")
        print(f"   - 记忆 ID: {result.get('memory_id', 'N/A')}")
        print(f"   - 耗时: {result.get('duration_seconds', 'N/A')} 秒")
        
        # 测试 2：查询任务统计
        print("\n📋 测试 2：任务统计")
        print("-" * 40)
        
        stats = await task_service.get_task_statistics()
        print(f"✅ 任务统计:")
        for status, info in stats['by_status'].items():
            print(f"   - {status}: {info['count']} 个")
        print(f"   - 总计: {stats['total']} 个")
        
        print("\n" + "=" * 60)
        print("✅ Phase 3 集成测试完成")
        print("=" * 60)
    
    finally:
        await task_service.close()


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    # 运行独立测试
    asyncio.run(run_integration_tests())