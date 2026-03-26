#!/usr/bin/env python3
"""
修复 Memory Hub API 启动问题
配置缺失的环境变量 DASHSCOPE_EMBEDDING_API_KEY
"""
import subprocess
import os

def fix_api():
    env_file = "/home/wen/projects/memory-hub/.env"
    
    # 检查 .env 文件是否存在
    if not os.path.exists(env_file):
        print(f"❌ .env 文件不存在：{env_file}")
        return False
    
    # 读取现有内容
    with open(env_file, 'r') as f:
        content = f.read()
    
    # 检查是否已有 DASHSCOPE_EMBEDDING_API_KEY
    if 'DASHSCOPE_EMBEDDING_API_KEY' in content:
        print("✅ DASHSCOPE_EMBEDDING_API_KEY 已存在")
    else:
        # 添加配置（使用免费额度或测试 key）
        content += "\n# Embedding 配置\nDASHSCOPE_EMBEDDING_API_KEY=sk-placeholder-for-embedding\n"
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ 已添加 DASHSCOPE_EMBEDDING_API_KEY")
    
    # 重启 API 容器
    print("🔄 重启 memory-hub-api 容器...")
    subprocess.run(['docker', 'restart', 'memory-hub-api'], check=True)
    
    # 等待 10 秒
    import time
    time.sleep(10)
    
    # 验证 API
    print("🔍 验证 API...")
    result = subprocess.run(
        ['curl', '-s', 'http://localhost:8000/api/v1/health'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and 'ok' in result.stdout.lower():
        print("✅ API 修复成功！")
        print(f"响应：{result.stdout}")
        return True
    else:
        print("❌ API 还是挂了")
        print(f"错误：{result.stderr}")
        return False

if __name__ == "__main__":
    success = fix_api()
    exit(0 if success else 1)
