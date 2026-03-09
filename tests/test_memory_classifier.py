#!/usr/bin/env python3
"""
测试记忆分类器
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.memory_classifier import memory_classifier, MemoryVisibility

# 测试用例
test_cases = [
    # (内容，期望结果)
    ("憨货喜欢喝拿铁咖啡", MemoryVisibility.PRIVATE),
    ("小码学会了数据库迁移的最佳实践", MemoryVisibility.SHARED),
    ("傻妞的密码是 123456", MemoryVisibility.PRIVATE),
    ("项目架构设计文档 v2.0", MemoryVisibility.SHARED),
    ("今天心情不错", MemoryVisibility.PRIVATE),
    ("Python 代码规范：函数命名用下划线", MemoryVisibility.SHARED),
    ("憨货的习惯：每天早 8 点起床", MemoryVisibility.PRIVATE),
    ("测试用例设计方法论", MemoryVisibility.SHARED),
]

# 执行测试
print("开始测试记忆分类器...\n")

passed = 0
failed = 0

for content, expected in test_cases:
    visibility, confidence, reason = memory_classifier.classify(content)
    
    if visibility == expected:
        print(f"✅ 通过：'{content[:20]}...' → {visibility.value} ({confidence:.2f})")
        passed += 1
    else:
        print(f"❌ 失败：'{content[:20]}...' → {visibility.value} (期望：{expected.value})")
        print(f"   理由：{reason}")
        failed += 1

print(f"\n测试结果：{passed} 通过，{failed} 失败")