#!/usr/bin/env python3
# ============================================================
# 飞书通知测试脚本
# ============================================================
# 功能：测试所有手下的飞书通知功能
# 作者：小码 🟡
# 日期：2026-03-17
# ============================================================
# 使用方法：
#   python tests/test_feishu_notification.py
# ============================================================

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker import (
    ResearcherWorker,
    WriterWorker,
    ReviewerWorker,
    AnalystWorker,
    BrowserWorker,
    DesignerWorker,
    LayoutWorker,
)


async def test_researcher():
    """测试小搜的飞书通知"""
    print("\n" + "=" * 60)
    print("测试小搜（team-researcher1）飞书通知")
    print("=" * 60)
    
    worker = ResearcherWorker(agent_id="team-researcher1")
    result = await worker.execute_direct(
        "测试搜索任务：搜索 AI 新闻",
        {"source": "twitter", "limit": 5}
    )
    
    print(f"结果: {result}")
    return result


async def test_writer():
    """测试小写的飞书通知"""
    print("\n" + "=" * 60)
    print("测试小写（team-writer1）飞书通知")
    print("=" * 60)
    
    worker = WriterWorker(agent_id="team-writer1")
    result = await worker.execute_direct(
        "测试写作任务：撰写产品说明",
        {"style": "professional", "length": 500}
    )
    
    print(f"结果: {result}")
    return result


async def test_reviewer():
    """测试小审的飞书通知"""
    print("\n" + "=" * 60)
    print("测试小审（team-reviewer1）飞书通知")
    print("=" * 60)
    
    worker = ReviewerWorker(agent_id="team-reviewer1")
    result = await worker.execute_direct(
        "测试审核任务：审核代码质量",
        {"files": ["main.py", "utils.py"]}
    )
    
    print(f"结果: {result}")
    return result


async def test_analyst():
    """测试小析的飞书通知"""
    print("\n" + "=" * 60)
    print("测试小析（team-analyst1）飞书通知")
    print("=" * 60)
    
    worker = AnalystWorker(agent_id="team-analyst1")
    result = await worker.execute_direct(
        "测试分析任务：分析用户行为数据",
        {"period": "2026-03", "metrics": ["active_users", "retention"]}
    )
    
    print(f"结果: {result}")
    return result


async def test_browser():
    """测试小览的飞书通知"""
    print("\n" + "=" * 60)
    print("测试小览（team-browser1）飞书通知")
    print("=" * 60)
    
    worker = BrowserWorker(agent_id="team-browser1")
    result = await worker.execute_direct(
        "测试浏览器任务：访问测试网站",
        {"url": "https://example.com"}
    )
    
    print(f"结果: {result}")
    return result


async def test_designer():
    """测试小图的飞书通知"""
    print("\n" + "=" * 60)
    print("测试小图（team-designer1）飞书通知")
    print("=" * 60)
    
    worker = DesignerWorker(agent_id="team-designer1")
    result = await worker.execute_direct(
        "测试设计任务：生成文章封面图",
        {"style": "cinematic", "aspect_ratio": "16:9"}
    )
    
    print(f"结果: {result}")
    return result


async def test_layout():
    """测试小排的飞书通知"""
    print("\n" + "=" * 60)
    print("测试小排（team-layout1）飞书通知")
    print("=" * 60)
    
    worker = LayoutWorker(agent_id="team-layout1")
    result = await worker.execute_direct(
        "测试排版任务：制作产品演示幻灯片",
        {"slides": 10, "theme": "modern"}
    )
    
    print(f"结果: {result}")
    return result


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 开始测试所有手下的飞书通知功能")
    print("=" * 60)
    
    results = {}
    
    # 测试所有手下
    try:
        results["小搜"] = await test_researcher()
    except Exception as e:
        print(f"❌ 小搜测试失败: {e}")
        results["小搜"] = {"error": str(e)}
    
    try:
        results["小写"] = await test_writer()
    except Exception as e:
        print(f"❌ 小写测试失败: {e}")
        results["小写"] = {"error": str(e)}
    
    try:
        results["小审"] = await test_reviewer()
    except Exception as e:
        print(f"❌ 小审测试失败: {e}")
        results["小审"] = {"error": str(e)}
    
    try:
        results["小析"] = await test_analyst()
    except Exception as e:
        print(f"❌ 小析测试失败: {e}")
        results["小析"] = {"error": str(e)}
    
    try:
        results["小览"] = await test_browser()
    except Exception as e:
        print(f"❌ 小览测试失败: {e}")
        results["小览"] = {"error": str(e)}
    
    try:
        results["小图"] = await test_designer()
    except Exception as e:
        print(f"❌ 小图测试失败: {e}")
        results["小图"] = {"error": str(e)}
    
    try:
        results["小排"] = await test_layout()
    except Exception as e:
        print(f"❌ 小排测试失败: {e}")
        results["小排"] = {"error": str(e)}
    
    # 打印汇总
    print("\n" + "=" * 60)
    print("📊 测试汇总")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for name, result in results.items():
        if "error" in result:
            print(f"  ❌ {name}: 失败 - {result['error']}")
            fail_count += 1
        else:
            print(f"  ✅ {name}: 成功")
            success_count += 1
    
    print(f"\n成功: {success_count} 个，失败: {fail_count} 个")
    print("\n" + "=" * 60)
    print("💡 提示：请检查飞书是否收到 7 条测试通知")
    print("   每条通知应包含：智能体 ID、任务标题、结果摘要")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())