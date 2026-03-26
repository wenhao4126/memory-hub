#!/usr/bin/env python3
"""
检查 Memory Hub API 端点并测试任务派发功能
"""
import subprocess
import json

API_BASE = "http://localhost:8000/api/v1"

def check_api():
    print("=== 1. 检查 API 健康状态 ===")
    result = subprocess.run(['curl', '-s', f'{API_BASE}/health'], capture_output=True, text=True)
    print(result.stdout)
    
    print("\n=== 2. 检查可用端点 ===")
    # 尝试常见端点
    endpoints = [
        '/tasks',
        '/agents',
        '/memories',
        '/chat',
        '/knowledge',
    ]
    
    available = []
    for endpoint in endpoints:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', f'{API_BASE}{endpoint}'], capture_output=True, text=True)
        status = "✅" if result.stdout in ['200', '201'] else "❌"
        print(f"{status} {endpoint} - HTTP {result.stdout}")
        if result.stdout in ['200', '201']:
            available.append(endpoint)
    
    print(f"\n=== 3. 可用端点：{available} ===")
    
    if '/tasks' not in available:
        print("\n❌ /tasks 端点不存在，需要添加或修改文档")
        print("建议：修改 TOOLS.md，说明直接操作数据库或使用其他 API")
        return False
    else:
        print("\n✅ /tasks 端点可用，测试任务派发...")
        # 测试创建任务
        test_task = {
            "agent_id": "3c9d696c-62e1-4ecf-9a78-46deed923080",
            "task_title": "API 测试任务",
            "task_description": "通过 API 创建的测试任务",
            "priority": "normal"
        }
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', f'{API_BASE}/tasks', 
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(test_task)],
            capture_output=True, text=True
        )
        print(f"创建任务结果：{result.stdout}")
        return True

if __name__ == "__main__":
    success = check_api()
    exit(0 if success else 1)
