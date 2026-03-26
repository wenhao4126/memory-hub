#!/usr/bin/env python3
"""
测试 Memory Hub SDK 派发任务功能
"""
import asyncio
import sys
sys.path.insert(0, '/home/wen/projects/memory-hub')

from sdk.task_service import TaskService

async def test_sdk():
    print("=== 测试 Memory Hub SDK ===\n")
    
    # 创建服务实例
    print("1️⃣ 创建 TaskService 实例...")
    service = TaskService()
    print(f"✅ 数据库连接：{service.db_url.split('@')[1] if '@' in service.db_url else 'unknown'}\n")
    
    # 创建任务
    print("2️⃣ 创建测试任务...")
    try:
        task_id = await service.create_task(
            task_type="code",
            title="SDK 测试任务",
            description="通过 Memory Hub SDK 创建的测试任务",
            priority="high",
            params={
                "script_path": "/home/wen/projects/memory-hub/scripts/obsidian-word-count.py",
                "test": True
            }
        )
        print(f"✅ 任务创建成功：{task_id}\n")
        
        # 查询任务
        print("3️⃣ 查询任务...")
        task = await service.get_task(task_id)
        if task:
            print(f"✅ 任务信息:")
            print(f"   - ID: {task['id']}")
            print(f"   - 标题：{task['title']}")
            print(f"   - 类型：{task['task_type']}")
            print(f"   - 状态：{task['status']}")
            print(f"   - 优先级：{task['priority']}")
        else:
            print("❌ 任务查询失败")
        
        print("\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await service.close()

if __name__ == "__main__":
    success = asyncio.run(test_sdk())
    exit(0 if success else 1)
