#!/usr/bin/env python3
"""
验证 coder_tasks API 结构
不依赖数据库和环境变量
"""

import ast
import re

def verify_api_file():
    """验证 API 文件结构"""
    print("=" * 60)
    print("🟡 验证 coder_tasks API 结构")
    print("=" * 60)
    
    with open('app/api/coder_tasks.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查必要的导入
    required_imports = [
        'from fastapi import APIRouter',
        'from pydantic import BaseModel',
        'from ..services.coder_task_service import coder_task_service',
        'from ..auth import verify_api_key',
    ]
    
    print("\n1️⃣  检查导入语句")
    for imp in required_imports:
        if imp in content:
            print(f"   ✅ {imp.split('import')[1].strip()}")
        else:
            print(f"   ❌ 缺少：{imp}")
            return False
    
    # 检查路由装饰器
    print("\n2️⃣  检查 API 端点")
    endpoints = [
        ('@router.get', '/coder-tasks', 'GET 查询任务列表'),
        ('@router.post', '/coder-tasks', 'POST 创建任务'),
        ('@router.get', '/coder-tasks/{task_id}', 'GET 任务详情'),
    ]
    
    for decorator, path, desc in endpoints:
        # 使用正则匹配
        pattern = rf'{decorator}\s*\(\s*["\']{path}["\']'
        if re.search(pattern, content):
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ 缺少：{desc}")
            return False
    
    # 检查请求/响应模型
    print("\n3️⃣  检查 Pydantic 模型")
    models = [
        'CoderTaskCreateRequest',
        'CoderTaskCreateResponse',
        'CoderTaskListResponse',
    ]
    
    for model in models:
        if f'class {model}(BaseModel):' in content:
            print(f"   ✅ {model}")
        else:
            print(f"   ❌ 缺少：{model}")
            return False
    
    # 检查函数定义
    print("\n4️⃣  检查端点函数")
    functions = [
        'async def get_coder_tasks(',
        'async def create_coder_task(request: CoderTaskCreateRequest):',
        'async def get_coder_task(task_id: str):',
    ]
    
    for func in functions:
        if func in content:
            print(f"   ✅ {func.strip()}")
        else:
            print(f"   ❌ 缺少：{func.strip()}")
            return False
    
    # 检查 main.py 中的注册
    print("\n5️⃣  检查 main.py 路由注册")
    with open('app/main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    checks = [
        ('from .api.coder_tasks import router as coder_tasks_router', '导入语句'),
        ('app.include_router(coder_tasks_router, prefix="/api/v1")', '路由注册'),
        ('"小码任务"', 'Swagger 标签'),
    ]
    
    for check, desc in checks:
        if check in main_content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ 缺少：{desc}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ 所有检查通过！API 结构正确")
    print("=" * 60)
    return True

if __name__ == '__main__':
    import os
    os.chdir('/home/wen/projects/memory-hub/backend')
    success = verify_api_file()
    exit(0 if success else 1)
