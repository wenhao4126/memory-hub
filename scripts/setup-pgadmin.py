#!/usr/bin/env python3
"""
自动配置 pgAdmin 数据库连接
"""

import requests
import json
import time

# pgAdmin 配置
PGADMIN_URL = "http://localhost:5050"
PGADMIN_EMAIL = "admin@memory.hub"
PGADMIN_PASSWORD = "memory_pass_2026"

# PostgreSQL 配置
DB_SERVER_NAME = "Memory Hub DB"
DB_HOST = "memory-hub-db"
DB_PORT = 5432
DB_USERNAME = "memory_user"
DB_PASSWORD = "memory_pass_2026"
DB_NAME = "memory_hub"

def login_to_pgadmin():
    """登录 pgAdmin 获取 session"""
    login_url = f"{PGADMIN_URL}/login"
    
    session = requests.Session()
    
    # 先获取 CSRF token
    response = session.get(login_url)
    
    # 登录
    login_data = {
        "email": PGADMIN_EMAIL,
        "password": PGADMIN_PASSWORD,
    }
    
    response = session.post(
        f"{PGADMIN_URL}/authenticate/login",
        data=login_data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )
    
    if response.status_code == 200:
        print("✅ pgAdmin 登录成功")
        return session
    else:
        print(f"❌ pgAdmin 登录失败: {response.status_code}")
        print(response.text)
        return None

def add_server(session):
    """添加数据库服务器连接"""
    
    # pgAdmin 添加服务器的 API
    server_data = {
        "name": DB_SERVER_NAME,
        "host": DB_HOST,
        "port": DB_PORT,
        "username": DB_USERNAME,
        "password": DB_PASSWORD,
        "sslmode": "prefer",
        "maintenance_db": DB_NAME,
        "comment": "Memory Hub PostgreSQL Database"
    }
    
    response = session.post(
        f"{PGADMIN_URL}/browser/server/obj/",
        json=server_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ 成功添加服务器: {DB_SERVER_NAME}")
        result = response.json()
        print(f"   服务器 ID: {result.get('id', 'N/A')}")
        return True
    elif response.status_code == 417:
        # 服务器可能已存在
        print(f"⚠️  服务器可能已存在或需要额外配置")
        print(f"   请手动在 pgAdmin 中添加连接")
        return False
    else:
        print(f"❌ 添加服务器失败: {response.status_code}")
        print(f"   响应: {response.text}")
        return False

def main():
    print("=" * 50)
    print("🔧 pgAdmin 数据库连接配置工具")
    print("=" * 50)
    print()
    
    # 等待 pgAdmin 启动
    print("⏳ 等待 pgAdmin 启动...")
    time.sleep(2)
    
    # 登录
    session = login_to_pgadmin()
    if not session:
        print("\n❌ 无法登录 pgAdmin")
        print("💡 请检查 pgAdmin 是否正常运行")
        return
    
    # 添加服务器
    if add_server(session):
        print("\n✅ 配置完成！")
        print(f"📊 打开浏览器访问: {PGADMIN_URL}")
        print(f"📧 登录邮箱: {PGADMIN_EMAIL}")
        print(f"🔑 登录密码: {PGADMIN_PASSWORD}")
    else:
        print("\n⚠️  自动配置失败，请手动配置：")
        print(f"   1. 打开浏览器: {PGADMIN_URL}")
        print(f"   2. 登录邮箱: {PGADMIN_EMAIL}")
        print(f"   3. 登录密码: {PGADMIN_PASSWORD}")
        print(f"   4. 右键 'Servers' → 'Register' → 'Server'")
        print(f"   5. General 标签:")
        print(f"      - Name: {DB_SERVER_NAME}")
        print(f"   6. Connection 标签:")
        print(f"      - Host: {DB_HOST}")
        print(f"      - Port: {DB_PORT}")
        print(f"      - Username: {DB_USERNAME}")
        print(f"      - Password: {DB_PASSWORD}")
        print(f"      - Database: {DB_NAME}")
        print(f"   7. 点击 'Save'")

if __name__ == "__main__":
    main()