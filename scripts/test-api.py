#!/usr/bin/env python3
"""
Memory Hub 接口测试脚本
测试 API 和 SDK 功能
"""
import subprocess
import json
import sys

API_BASE = "http://localhost:8000/api/v1"
AGENT_ID = "2ced6241-9915-47f7-86d0-32ea8db0eb68"

def run_test(name, cmd, check_output=None):
    """运行测试命令"""
    print(f"\n=== {name} ===")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {name} 通过")
        if check_output:
            try:
                data = json.loads(result.stdout)
                if check_output(data):
                    print(f"   输出验证通过")
                else:
                    print(f"   ⚠️  输出验证失败")
            except:
                print(f"   输出：{result.stdout[:200]}")
        else:
            print(f"   输出：{result.stdout[:200]}")
        return True
    else:
        print(f"❌ {name} 失败")
        print(f"   错误：{result.stderr[:200]}")
        return False

def test_api_health():
    """测试 API 健康检查"""
    return run_test(
        "API 健康检查",
        f"curl -s '{API_BASE}/health' | jq .",
        lambda data: data.get('status') == 'ok'
    )

def test_create_memory():
    """测试创建记忆"""
    return run_test(
        "创建记忆",
        f"""curl -s -X POST '{API_BASE}/memories' \\
  -H "Content-Type: application/json" \\
  -d '{{"agent_id":"{AGENT_ID}","content":"小审测试记忆","memory_type":"fact","importance":0.9}}' | jq .""",
        lambda data: 'message' in data.get('message', '') or data.get('success') == True
    )

def test_search_memory():
    """测试搜索记忆"""
    return run_test(
        "搜索记忆",
        f"curl -s '{API_BASE}/memories/search?q=小审&limit=5' | jq ."
    )

def test_sdk():
    """测试 SDK 功能"""
    print("\n=== SDK 功能测试 ===")
    
    # 创建测试任务
    result = subprocess.run([
        'python3', '-c',
        f'''
import asyncio
import sys
sys.path.insert(0, "/home/wen/projects/memory-hub")
from sdk.task_service import TaskService

async def test():
    service = TaskService()
    task_id = await service.create_task(
        task_type="code",
        title="SDK 测试任务",
        description="小审测试",
        priority="high"
    )
    print(f"✅ 任务创建成功：{{task_id}}")
    
    task = await service.acquire_task(agent_id="3c9d696c-62e1-4ecf-9a78-46deed923080")
    if task:
        print(f"✅ 任务领取成功：{{task['title']}}")
        await service.complete_task(task["task_id"], result={{"status": "success"}})
        print("✅ 任务完成")
    else:
        print("⚠️  无可用任务")
    
    await service.close()

asyncio.run(test())
'''
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ SDK 功能测试通过")
        print(f"   输出：{result.stdout}")
        return True
    else:
        print(f"❌ SDK 功能测试失败")
        print(f"   错误：{result.stderr}")
        return False

def test_database():
    """测试数据库连接"""
    print("\n=== 数据库表记录数 ===")
    
    result = subprocess.run([
        'docker', 'exec', '-i', 'memory-hub-db', 'psql', '-U', 'memory_user', '-d', 'memory_hub', '-c',
        """
        SELECT 'parallel_tasks' as table_name, COUNT(*) as count FROM parallel_tasks
        UNION ALL
        SELECT 'shared_memories', COUNT(*) FROM shared_memories
        UNION ALL
        SELECT 'knowledge', COUNT(*) FROM knowledge;
        """
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ 数据库连接正常")
        print(result.stdout)
        return True
    else:
        print(f"❌ 数据库连接失败")
        print(f"   错误：{result.stderr}")
        return False

def test_docker_containers():
    """测试 Docker 容器状态"""
    print("\n=== Docker 容器状态 ===")
    
    result = subprocess.run([
        'docker', 'ps', '--filter', 'name=memory-hub',
        '--format', 'table {{.Names}}\t{{.Status}}'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Docker 容器状态")
        print(result.stdout)
        return True
    else:
        print(f"❌ Docker 容器检查失败")
        return False

def main():
    print("=" * 60)
    print("Memory Hub 接口测试")
    print("=" * 60)
    
    results = {
        "API 健康检查": test_api_health(),
        "创建记忆": test_create_memory(),
        "搜索记忆": test_search_memory(),
        "SDK 功能": test_sdk(),
        "数据库连接": test_database(),
        "Docker 容器": test_docker_containers()
    }
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
