#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：MEMORY.md → Memory Hub
功能：将 OpenClaw 的 MEMORY.md 内容迁移到 Memory Hub 数据库
用法：python migrate_memory_md_to_hub.py [--dry-run] [--agent-name "傻妞"]
作者：小码
日期：2026-03-17
"""

import argparse
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import requests

# 配置
MEMORY_HUB_API = os.environ.get("MEMORY_HUB_API", "http://localhost:8000/api/v1")
DATA_DIR = Path(__file__).parent.parent / "data"
REGISTRY_FILE = DATA_DIR / "agent-registry.json"

# 颜色输出
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    MAGENTA = "\033[0;35m"
    NC = "\033[0m"


def print_color(color: str, text: str):
    print(f"{color}{text}{Colors.NC}")


def print_header():
    print_color(Colors.MAGENTA, "━" * 60)
    print_color(Colors.MAGENTA, "  📦 MEMORY.md → Memory Hub 迁移脚本")
    print_color(Colors.MAGENTA, "━" * 60)


def print_success(text: str):
    print_color(Colors.GREEN, f"✅ {text}")


def print_error(text: str):
    print_color(Colors.RED, f"❌ {text}")


def print_warning(text: str):
    print_color(Colors.YELLOW, f"⚠️  {text}")


def print_info(text: str):
    print_color(Colors.BLUE, f"ℹ️  {text}")


def get_agent_id(agent_name: str) -> str | None:
    """从注册表获取智能体 ID"""
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            registry = json.load(f)
            return registry.get(agent_name)
    return None


def detect_memory_type(content: str) -> str:
    """检测记忆类型"""
    if any(kw in content for kw in ["喜欢", "讨厌", "偏好", "习惯", "风格", "要求"]):
        return "preference"
    elif any(kw in content for kw in ["职责", "专长", "能力", "擅长", "可以", "会写"]):
        return "skill"
    elif any(kw in content for kw in ["是", "叫", "住在", "等于", "配置", "地址", "ID", "密钥"]):
        return "fact"
    return "experience"


def estimate_importance(content: str) -> float:
    """估算重要性"""
    if any(kw in content for kw in ["重要", "必须", "红线", "禁止", "核心", "关键"]):
        return 0.9
    elif any(kw in content for kw in ["踩坑", "问题", "错误", "失败", "教训"]):
        return 0.85
    elif any(kw in content for kw in ["配置", "设置", "安装", "更新"]):
        return 0.75
    return 0.7


def extract_tags(section_title: str, content: str) -> list[str]:
    """提取标签"""
    tags = []
    
    # 从标题提取
    if section_title:
        tags.extend(section_title.replace("🎯", "").replace("👥", "").replace("🛠️", "")
                   .replace("📁", "").replace("⚡", "").replace("📰", "")
                   .replace("🔔", "").replace("🧠", "").replace("🎨", "")
                   .replace("⚠️", "").replace("💬", "").strip().split()[:3])
    
    # 从内容提取关键词
    keywords = ["配置", "优化", "任务", "文档", "智能体", "脚本", "API", "数据"]
    for kw in keywords:
        if kw in content:
            tags.append(kw)
    
    # 添加日期
    tags.append(datetime.now().strftime("%Y-%m-%d"))
    tags.append("迁移")
    
    return list(set(tags))[:10]


def parse_memory_md(file_path: Path) -> list[dict]:
    """解析 MEMORY.md 文件"""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    
    # 按二级标题分割
    sections = re.split(r"\n## ", content)
    
    memories = []
    for section in sections[1:]:  # 跳过第一个空部分
        lines = section.strip().split("\n")
        if not lines:
            continue
        
        # 提取标题
        title = lines[0].strip()
        
        # 提取内容（去除标题后的内容）
        section_content = "\n".join(lines[1:]).strip()
        
        # 清理内容
        section_content = re.sub(r"\n{3,}", "\n\n", section_content)  # 多个换行合并
        section_content = re.sub(r"^---+$", "", section_content, flags=re.MULTILINE)  # 移除分隔线
        
        # 跳过太短的内容
        if len(section_content) < 50:
            continue
        
        memories.append({
            "title": title,
            "content": section_content[:2000],  # 限制长度
        })
    
    return memories


def store_memory(agent_id: str, content: str, memory_type: str, importance: float, tags: list[str], dry_run: bool) -> bool:
    """存储记忆到 Memory Hub"""
    if dry_run:
        print_color(Colors.YELLOW, f"[DRY-RUN] 将存储: {memory_type} ({importance})")
        print(f"  内容: {content[:80]}...")
        return True
    
    try:
        response = requests.post(
            f"{MEMORY_HUB_API}/memories",
            json={
                "agent_id": agent_id,
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "tags": tags,
                "auto_route": True,
            },
            timeout=30,
        )
        
        # 检查响应内容
        result = response.json()
        if response.status_code == 200 and (result.get("success") or "成功" in str(result)):
            return True
        else:
            print_error(f"存储失败: {result}")
            return False
    except Exception as e:
        print_error(f"存储异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="迁移 MEMORY.md 到 Memory Hub")
    parser.add_argument("--dry-run", "-d", action="store_true", help="预览模式，不实际存储")
    parser.add_argument("--agent-name", "-a", default="傻妞", help="智能体名称")
    args = parser.parse_args()
    
    print_header()
    print()
    
    memory_md = Path.home() / ".openclaw" / "workspace" / "MEMORY.md"
    backup_dir = Path.home() / ".openclaw" / "workspace" / "memory-backup"
    
    # 显示配置
    print_info(f"智能体: {args.agent_name}")
    print_info(f"源文件: {memory_md}")
    print_info(f"Memory Hub API: {MEMORY_HUB_API}")
    print_info(f"模式: {'预览' if args.dry_run else '执行'}")
    print()
    
    # 检查源文件
    if not memory_md.exists():
        print_error(f"MEMORY.md 文件不存在: {memory_md}")
        return 1
    print_success("源文件存在")
    
    # 获取智能体 ID
    agent_id = get_agent_id(args.agent_name)
    if not agent_id:
        print_error(f"未找到智能体 '{args.agent_name}' 的注册信息")
        print_info("请先运行注册脚本: ./scripts/register-agent.sh")
        return 1
    print_success(f"智能体 ID: {agent_id}")
    
    # 检查 API
    try:
        response = requests.get(f"{MEMORY_HUB_API}/health", timeout=5)
        if response.status_code != 200:
            raise Exception("API 不可用")
        print_success("Memory Hub API 可用")
    except Exception as e:
        print_error(f"Memory Hub API 不可用: {e}")
        print_info("请先启动: cd /home/wen/projects/memory-hub && ./scripts/start.sh start")
        return 1
    
    # 备份
    if not args.dry_run:
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"MEMORY.md.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        shutil.copy(memory_md, backup_file)
        print_success(f"已备份到: {backup_file}")
    
    print()
    print_color(Colors.CYAN, "━" * 40 + " 解析 MEMORY.md " + "━" * 40)
    
    # 解析
    memories = parse_memory_md(memory_md)
    print_info(f"解析到 {len(memories)} 个记忆段落")
    print()
    
    # 迁移
    success_count = 0
    fail_count = 0
    
    for i, mem in enumerate(memories, 1):
        memory_type = detect_memory_type(mem["content"])
        importance = estimate_importance(mem["content"])
        tags = extract_tags(mem["title"], mem["content"])
        
        print_info(f"[{i}/{len(memories)}] {mem['title']}")
        print(f"  类型: {memory_type}, 重要性: {importance}")
        
        if store_memory(agent_id, mem["content"], memory_type, importance, tags, args.dry_run):
            success_count += 1
            print_success("存储成功")
        else:
            fail_count += 1
        print()
    
    # 汇总
    print_color(Colors.CYAN, "━" * 40 + " 迁移结果 " + "━" * 40)
    print_info(f"总计: {len(memories)} 条记忆")
    print_success(f"成功: {success_count}")
    if fail_count > 0:
        print_error(f"失败: {fail_count}")
    
    if not args.dry_run:
        print()
        print_success("迁移完成！")
        print_info(f"原文件已备份到: {backup_dir}/")
        print_info("原文件保留作为历史记录，但不再更新")
        print_warning("请更新 AGENTS.md 和相关文档，说明不再使用 MEMORY.md")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit(main())