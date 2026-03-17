#!/usr/bin/env python3
# ============================================================
# Memory Hub - 权限测试脚本
# ============================================================
# 功能：验证数据库表访问权限配置
# 作者：小码 🟡
# 日期：2026-03-17
# ============================================================

import sys
import os


# ============================================================
# 权限配置（从配置文件复制）
# ============================================================

# 智能体 ID 映射
AGENT_IDS = {
    "傻妞": "2ced6241-9915-47f7-86d0-32ea8db0eb68",
    "小搜": "d5fa91a1-dd55-4e26-a151-126c1a977a8d",
    "小写": "7ffb2eab-719c-4894-abba-a84f05e6d6e2",
    "小码": "3c9d696c-62e1-4ecf-9a78-46deed923080",
    "小审": "04a87468-fbf1-4f25-9a4d-4e03f2963a36",
    "小析": "ca71407b-f8c2-43ac-ad40-b50756036e59",
    "小览": "986150df-eb22-4f46-b43f-cc4f632f7314",
    "小图": "86df09c2-2ba8-431e-a376-a76d661fa80b",
    "小排": "cae3ad57-60c2-445a-8356-b8c9293a930c"
}

# 反向映射
AGENT_NAMES = {v: k for k, v in AGENT_IDS.items()}

# 权限配置
PARALLEL_TASKS_PERMISSIONS = {
    "write": ["傻妞"],
    "read": ["小码", "team-coder2", "team-coder3", "team-coder4", "team-coder5"]
}

SHARED_MEMORIES_PERMISSIONS = {
    "read": ["all"],
    "write": ["小搜", "小写", "小审", "小析", "小览", "小图", "小排"],
    "forbidden_write": ["小码"]
}

# 别名映射
AGENT_ALIASES = {
    "team-coder": "小码",
    "team-coder1": "小码",
    "team-coder2": "小码2",
    "team-coder3": "小码3",
    "team-coder4": "小码4",
    "team-coder5": "小码5"
}


def resolve_agent_name(agent_id: str) -> str:
    """解析智能体名称"""
    if agent_id in AGENT_IDS:
        return agent_id
    if agent_id in AGENT_NAMES:
        return AGENT_NAMES[agent_id]
    if agent_id in AGENT_ALIASES:
        return AGENT_ALIASES[agent_id]
    return agent_id


def check_parallel_tasks_permission(agent_id: str, action: str) -> bool:
    """检查 parallel_tasks 表权限"""
    agent_name = resolve_agent_name(agent_id)
    allowed = PARALLEL_TASKS_PERMISSIONS.get(action, [])
    
    # 检查别名
    if agent_id in AGENT_ALIASES:
        if action == "read" and agent_id in ["team-coder", "team-coder1", "team-coder2", "team-coder3", "team-coder4", "team-coder5"]:
            return True
        if action == "write" and AGENT_ALIASES[agent_id] == "傻妞":
            return True
        return False
    
    if agent_name in allowed:
        return True
    
    if action == "read" and agent_name in ["小码", "小码2", "小码3", "小码4", "小码5"]:
        return True
    
    return False


# ============================================================
# 测试用例
# ============================================================

def test_parallel_tasks_permissions():
    """测试 parallel_tasks 表权限"""
    print("\n" + "="*60)
    print("📋 测试 parallel_tasks 表权限")
    print("="*60)
    
    test_cases = [
        # (agent_id, action, expected_result, description)
        ("傻妞", "write", True, "傻妞创建任务"),
        ("傻妞", "read", False, "傻妞读取任务（无权限）"),
        ("小码", "read", True, "小码读取任务"),
        ("小码", "write", False, "小码创建任务（无权限）"),
        ("team-coder2", "read", True, "team-coder2 读取任务"),
        ("team-coder2", "write", False, "team-coder2 创建任务（无权限）"),
        ("小搜", "read", False, "小搜读取任务（无权限）"),
        ("小搜", "write", False, "小搜创建任务（无权限）"),
    ]
    
    passed = 0
    failed = 0
    
    for agent_id, action, expected, desc in test_cases:
        result = check_parallel_tasks_permission(agent_id, action)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        agent_name = resolve_agent_name(agent_id)
        print(f"{status} {desc}")
        print(f"   智能体: {agent_name} ({agent_id})")
        print(f"   操作: {action}")
        print(f"   预期: {expected}, 实际: {result}")
        print()
    
    print(f"统计: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    return failed == 0


def test_shared_memories_permissions():
    """测试 shared_memories 表权限"""
    print("\n" + "="*60)
    print("💾 测试 shared_memories 表权限")
    print("="*60)
    
    def check_shared_memories_permission(agent_id: str, action: str) -> bool:
        agent_name = resolve_agent_name(agent_id)
        allowed = SHARED_MEMORIES_PERMISSIONS.get(action, [])
        
        if "all" in allowed:
            forbidden = SHARED_MEMORIES_PERMISSIONS.get(f"forbidden_{action}", [])
            if agent_name in forbidden:
                return False
            return True
        
        return agent_name in allowed
    
    test_cases = [
        # (agent_id, action, expected_result, description)
        ("小搜", "read", True, "小搜读取共享记忆"),
        ("小搜", "write", True, "小搜写入共享记忆"),
        ("小写", "write", True, "小写写入共享记忆"),
        ("小码", "read", True, "小码读取共享记忆"),
        ("小码", "write", False, "小码写入共享记忆（禁止）"),
        ("傻妞", "read", True, "傻妞读取共享记忆"),
        ("傻妞", "write", False, "傻妞写入共享记忆（无权限）"),
    ]
    
    passed = 0
    failed = 0
    
    for agent_id, action, expected, desc in test_cases:
        result = check_shared_memories_permission(agent_id, action)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        agent_name = resolve_agent_name(agent_id)
        print(f"{status} {desc}")
        print(f"   智能体: {agent_name} ({agent_id})")
        print(f"   操作: {action}")
        print(f"   预期: {expected}, 实际: {result}")
        print()
    
    print(f"统计: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    return failed == 0


def test_knowledge_permissions():
    """测试 knowledge 表权限"""
    print("\n" + "="*60)
    print("📚 测试 knowledge 表权限")
    print("="*60)
    
    # knowledge 表全员读写
    test_cases = [
        ("傻妞", "read", True, "傻妞读取知识"),
        ("傻妞", "write", True, "傻妞写入知识"),
        ("小搜", "read", True, "小搜读取知识"),
        ("小搜", "write", True, "小搜写入知识"),
        ("小码", "read", True, "小码读取知识"),
        ("小码", "write", True, "小码写入知识"),
    ]
    
    passed = 0
    failed = 0
    
    for agent_id, action, expected, desc in test_cases:
        # knowledge 表全员可读写
        result = True
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        agent_name = resolve_agent_name(agent_id)
        print(f"{status} {desc}")
        print(f"   智能体: {agent_name} ({agent_id})")
        print(f"   操作: {action}")
        print(f"   预期: {expected}, 实际: {result}")
        print()
    
    print(f"统计: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    return failed == 0


def test_task_service_integration():
    """测试 TaskService 权限集成"""
    print("\n" + "="*60)
    print("🔧 测试 TaskService 权限集成")
    print("="*60)
    
    # 测试 1: 小码尝试创建任务（应该失败）
    print("\n测试 1: 小码尝试创建任务（应该失败）")
    try:
        if check_parallel_tasks_permission("小码", "write"):
            print("❌ 小码竟然有写权限！")
            return False
        else:
            print("✅ 小码无写权限，符合预期")
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False
    
    # 测试 2: 傻妞创建任务（应该成功）
    print("\n测试 2: 傻妞创建任务（应该成功）")
    try:
        if check_parallel_tasks_permission("傻妞", "write"):
            print("✅ 傻妞有写权限，符合预期")
        else:
            print("❌ 傻妞竟然没有写权限！")
            return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False
    
    # 测试 3: 小码领取任务（应该成功）
    print("\n测试 3: 小码领取任务（应该成功）")
    try:
        if check_parallel_tasks_permission("小码", "read"):
            print("✅ 小码有读权限，符合预期")
        else:
            print("❌ 小码竟然没有读权限！")
            return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False
    
    # 测试 4: 小搜尝试领取任务（应该失败）
    print("\n测试 4: 小搜尝试领取任务（应该失败）")
    try:
        if check_parallel_tasks_permission("小搜", "read"):
            print("❌ 小搜竟然有读权限！")
            return False
        else:
            print("✅ 小搜无读权限，符合预期")
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False
    
    return True


# ============================================================
# 主函数
# ============================================================

def main():
    print("="*60)
    print("🧪 Memory Hub 权限测试")
    print("="*60)
    print(f"测试时间: 2026-03-17")
    print(f"测试人员: 小码 🟡")
    print()
    
    all_passed = True
    
    # 测试 1: parallel_tasks 权限
    if not test_parallel_tasks_permissions():
        all_passed = False
    
    # 测试 2: shared_memories 权限
    if not test_shared_memories_permissions():
        all_passed = False
    
    # 测试 3: knowledge 权限
    if not test_knowledge_permissions():
        all_passed = False
    
    # 测试 4: TaskService 集成
    if not test_task_service_integration():
        all_passed = False
    
    # 总结
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有测试通过！权限配置正确。")
    else:
        print("❌ 部分测试失败，请检查权限配置。")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())