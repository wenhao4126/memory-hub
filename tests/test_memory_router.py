#!/usr/bin/env python3
"""
测试记忆路由器
"""

import asyncio
from backend.app.services.memory_router import memory_router

# 模拟数据库连接
class MockDB:
    async def fetchval(self, query, *args):
        import uuid
        return uuid.uuid4()

async def test_router():
    db = MockDB()
    
    test_cases = [
        # (内容，期望表)
        ("憨货喜欢喝拿铁咖啡", "private"),
        ("小码学会了数据库迁移", "shared"),
        ("项目架构设计文档", "shared"),
        ("今天心情不错", "private"),
    ]
    
    print("开始测试记忆路由器...\n")
    
    passed = 0
    failed = 0
    
    for content, expected_table in test_cases:
        memory_id, table_name, visibility = await memory_router.save(
            db=db,
            content=content,
            agent_id="83a4c7c5-ab61-43de-b8e1-0a1e688100c0",
            memory_type="fact",
            agent_name="傻妞",
            embedding=[0.1] * 1024
        )
        
        if table_name == expected_table:
            print(f"✅ 通过：'{content[:20]}...' → {table_name}")
            passed += 1
        else:
            print(f"❌ 失败：'{content[:20]}...' → {table_name} (期望：{expected_table})")
            failed += 1
    
    print(f"\n测试结果：{passed} 通过，{failed} 失败")

if __name__ == "__main__":
    asyncio.run(test_router())