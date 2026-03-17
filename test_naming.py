#!/usr/bin/env python3
# ============================================================
# 测试文档命名服务
# ============================================================

import asyncio
import sys
sys.path.insert(0, '/home/wen/projects/memory-hub/backend')

from app.services.document_naming_service import document_naming_service


async def test_naming_service():
    """测试命名服务"""
    
    print("=" * 60)
    print("测试文档命名服务")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        {
            "title": "Python 基础教程 | 菜鸟教程",
            "url": "https://www.runoob.com/python/python-tutorial.html",
            "expected": "Python 基础教程"
        },
        {
            "title": "快速上手 - Vue.js",
            "url": "https://vuejs.org/guide/introduction.html",
            "expected": "Vue.js 快速上手"
        },
        {
            "title": "Deno 示例与教程 - Deno 文档",
            "url": "https://deno.land/manual/examples",
            "expected": "Deno 示例与教程"
        },
        {
            "title": "快速入门 - React 中文文档",
            "url": "https://zh-hans.reactjs.org/docs/getting-started.html",
            "expected": "React 快速入门"
        },
        {
            "title": "Docker 入门教程（非常详细）从零基础入门到精通，看完这一篇就够了",
            "url": "https://blog.csdn.net/docker",
            "expected": "Docker 入门教程"
        },
    ]
    
    for idx, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {idx}:")
        print(f"  原始标题: {case['title']}")
        print(f"  URL: {case['url']}")
        
        # 生成中文名字
        chinese_name = await document_naming_service.generate_chinese_name(
            title=case['title'],
            url=case['url'],
            source="小搜"
        )
        
        print(f"  生成结果: {chinese_name}")
        print(f"  期望结果: {case['expected']}")
        
        # 检查是否包含关键词
        if chinese_name and len(chinese_name) > 0:
            print(f"  ✅ 成功生成中文名字")
        else:
            print(f"  ❌ 生成失败")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_naming_service())