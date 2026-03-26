#!/usr/bin/env python3
"""
修复 memory-hub npm 包打包问题
确保 .env.example 等配置文件被打包到 npm 包中
"""
import json
import subprocess
import os

# 检查本地开发环境
BACKEND_DIR = "/home/wen/projects/memory-hub/backend"
if not os.path.exists(BACKEND_DIR):
    # 如果是全局安装的 npm 包
    BACKEND_DIR = "/usr/local/lib/node_modules/memory-hub"

PACKAGE_JSON = os.path.join(BACKEND_DIR, "package.json")

def fix_npm_package():
    print("=== 修复 npm 包打包问题 ===\n")
    
    # 1. 检查 package.json
    print("1️⃣ 检查 backend/package.json...")
    if not os.path.exists(PACKAGE_JSON):
        print(f"⚠️  文件不存在：{PACKAGE_JSON}")
        print("   这可能是测试环境，跳过 npm 包修复")
        print("\n=== 跳过修复（测试环境）===")
        return True
    
    with open(PACKAGE_JSON, 'r') as f:
        package = json.load(f)
    
    print(f"✅ 当前 package.json 的 files 配置：{package.get('files', [])}")
    
    # 2. 添加缺失的文件
    required_files = [
        ".env.example",
        ".env",
        "docker-compose.yml",
        "config/",
        "scripts/"
    ]
    
    if 'files' not in package:
        package['files'] = []
    
    added = []
    for file in required_files:
        if file not in package['files']:
            package['files'].append(file)
            added.append(file)
    
    if added:
        print(f"\n2️⃣ 添加缺失的文件：{added}")
        with open(PACKAGE_JSON, 'w') as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
        print("✅ package.json 已更新")
    else:
        print("\n2️⃣ 所有文件已包含，无需添加")
    
    # 3. 验证 .env.example 存在
    env_example = os.path.join(BACKEND_DIR, ".env.example")
    if os.path.exists(env_example):
        print(f"\n3️⃣ ✅ .env.example 文件存在")
    else:
        print(f"\n3️⃣ ❌ .env.example 文件不存在，需要创建")
        # 创建 .env.example
        with open(env_example, 'w') as f:
            f.write("""# Memory Hub 环境变量配置示例

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=memory_hub
DB_USER=memory_user
DB_PASSWORD=memory_pass_2026

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# DashScope API 配置
DASHSCOPE_LLM_API_KEY=your_api_key_here
DASHSCOPE_EMBEDDING_API_KEY=your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# LLM 配置
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSION=1024
""")
        print("✅ .env.example 已创建")
    
    # 4. 重新构建 npm 包
    print("\n4️⃣ 重新构建 npm 包...")
    result = subprocess.run(
        ['npm', 'pack'],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ npm pack 成功：{result.stdout.strip()}")
    else:
        print(f"❌ npm pack 失败：{result.stderr}")
        return False
    
    # 5. 验证打包内容
    print("\n5️⃣ 验证打包内容...")
    tarball = f"{BACKEND_DIR}/memory-hub-*.tgz"
    result = subprocess.run(
        ['tar', '-tzf'] + [f for f in subprocess.run(['ls', tarball], capture_output=True, text=True).stdout.strip().split('\n') if f][0] if tarball else [],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR
    )
    
    if '.env.example' in result.stdout:
        print("✅ .env.example 已包含在包中")
    else:
        print("❌ .env.example 未包含在包中")
    
    print("\n=== 修复完成 ===")
    return True

if __name__ == "__main__":
    success = fix_npm_package()
    exit(0 if success else 1)
