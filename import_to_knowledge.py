#!/usr/bin/env python3
# ============================================================
# 导入 Obsidian 文件到知识库
# ============================================================
# 功能：扫描 Obsidian 文件，导入到 knowledge 表
# 作者：小码
# 日期：2026-03-07
# ============================================================

import os
import requests
from glob import glob
from datetime import datetime
import time

# 配置
OBSIDIAN_PATH = "/home/wen/tools/obsidian"
API_BASE = "http://localhost:8000/api/v1"

# 文件扩展名白名单（只导入这些类型）
ALLOWED_EXTENSIONS = {'.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.conf', '.cfg', '.ini'}

# 分类规则
CATEGORY_RULES = {
    "编程": ["python", "编程", "code", "programming", "api", "mcp", "开发"],
    "配置": ["配置", "config", "docker", "archlinux", "hyprland", "zsh"],
    "学习": ["学习", "教程", "guide", "tutorial", "docs"],
    "设计": ["设计", "design", "ui", "ux"],
    "工具": ["工具", "tool", "cursor", "obsidian", "openclaw"],
    "项目": ["项目", "project", "memory-hub"],
}


def get_knowledge_agent_id():
    """获取知识 agent 的 ID"""
    try:
        response = requests.get(f"{API_BASE}/agents", timeout=10)
        if response.status_code == 200:
            agents = response.json()
            for agent in agents:
                if agent["name"] == "知识":
                    return agent["id"]
        print("❌ 知识 agent 不存在，请先创建")
        return None
    except Exception as e:
        print(f"❌ 获取 agent 列表失败: {e}")
        return None


def get_category(file_path: str) -> str:
    """根据文件路径确定分类"""
    file_path_lower = file_path.lower()
    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in file_path_lower:
                return category
    return "general"


def get_tags(file_path: str, file_ext: str) -> list:
    """根据文件路径和扩展名生成标签"""
    tags = ["obsidian", "imported"]
    
    # 添加扩展名标签
    ext_tag = file_ext.lstrip('.')
    if ext_tag in ['md', 'txt']:
        tags.append('document')
    elif ext_tag in ['json', 'yaml', 'yml', 'toml']:
        tags.append('config')
    
    # 添加目录标签
    parts = file_path.split(os.sep)
    for part in parts:
        if part and part not in ['home', 'wen', 'tools', 'obsidian', '.obsidian']:
            if '学习' in part:
                tags.append('learning')
            elif '配置' in part:
                tags.append('config')
    
    return list(set(tags))[:5]  # 最多 5 个标签


def import_knowledge(file_path: str, knowledge_agent_id: str) -> dict:
    """导入单个文件到知识库"""
    try:
        # 读取内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 获取文件信息
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1]
        relative_path = os.path.relpath(file_path, OBSIDIAN_PATH)
        
        # 提取标题（第一行 # 标题或文件名）
        lines = content.split('\n')
        title = file_name
        for line in lines[:5]:  # 只看前 5 行
            if line.startswith('# '):
                title = line[2:].strip()[:500]
                break
        
        # 限制内容长度
        max_content = 50000
        truncated_content = content[:max_content]
        
        # 确定分类和标签
        category = get_category(file_path)
        tags = get_tags(file_path, file_ext)
        
        # 构建请求数据
        knowledge_data = {
            "agent_id": knowledge_agent_id,
            "title": title,
            "content": truncated_content,
            "category": category,
            "tags": tags,
            "source": f"Obsidian/{relative_path}",
            "importance": 0.8,
            "metadata": {
                "original_file": file_name,
                "file_size": os.path.getsize(file_path),
                "import_date": datetime.now().isoformat()
            }
        }
        
        # 调用 API
        response = requests.post(
            f"{API_BASE}/knowledge",
            json=knowledge_data,
            timeout=60  # 向量生成可能需要更长时间
        )
        
        if response.status_code == 201:
            # 标注已导入
            imported_path = file_path + ".knowledge_imported"
            os.rename(file_path, imported_path)
            return {
                "file": file_name,
                "category": category,
                "content_length": len(content),
                "status": "success"
            }
        else:
            return {
                "file": file_name,
                "error": f"{response.status_code}: {response.text[:200]}",
                "status": "failed"
            }
    except Exception as e:
        return {
            "file": os.path.basename(file_path),
            "error": str(e),
            "status": "error"
        }


def main():
    """主函数"""
    print("=" * 60)
    print("📚 Obsidian 文件导入知识库")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 源路径: {OBSIDIAN_PATH}")
    print(f"🌐 API: {API_BASE}")
    print("-" * 60)
    
    # 获取知识 agent ID
    knowledge_agent_id = get_knowledge_agent_id()
    if not knowledge_agent_id:
        print("\n❌ 无法获取知识 agent ID，请检查 API 服务")
        return
    
    print(f"✅ 知识 Agent ID: {knowledge_agent_id}")
    print("-" * 60)
    
    # 扫描所有文件
    all_files = glob(f"{OBSIDIAN_PATH}/**/*", recursive=True)
    
    # 过滤文件
    files_to_import = []
    for f in all_files:
        # 跳过目录
        if not os.path.isfile(f):
            continue
        # 跳过已导入的知识库文件
        if f.endswith('.knowledge_imported'):
            continue
        # 跳过 .obsidian 目录
        if '/.obsidian/' in f:
            continue
        # 检查扩展名
        ext = os.path.splitext(f)[1].lower()
        # 也导入 .imported 文件
        if ext in ALLOWED_EXTENSIONS:
            files_to_import.append(f)
        # 导入 .md.imported 文件
        elif f.endswith('.md.imported'):
            files_to_import.append(f)
    
    print(f"📊 找到 {len(files_to_import)} 个文件待导入")
    print("-" * 60)
    
    # 统计
    results = {
        "total": len(files_to_import),
        "success": 0,
        "failed": 0,
        "error": 0,
        "by_category": {},
        "failed_files": []
    }
    
    start_time = time.time()
    
    # 导入文件
    for i, file_path in enumerate(files_to_import, 1):
        file_name = os.path.basename(file_path)
        print(f"[{i}/{len(files_to_import)}] 📄 {file_name[:40]}...", end=" ", flush=True)
        
        result = import_knowledge(file_path, knowledge_agent_id)
        
        if result["status"] == "success":
            results["success"] += 1
            cat = result["category"]
            results["by_category"][cat] = results["by_category"].get(cat, 0) + 1
            print(f"✅ ({result['content_length']} 字)")
        elif result["status"] == "failed":
            results["failed"] += 1
            results["failed_files"].append({"file": result["file"], "error": result["error"]})
            print(f"❌ {result['error'][:50]}")
        else:
            results["error"] += 1
            results["failed_files"].append({"file": result["file"], "error": result["error"]})
            print(f"⚠️ {result['error'][:50]}")
        
        # 每 10 个文件暂停一下，避免 API 过载
        if i % 10 == 0:
            time.sleep(0.5)
    
    elapsed = time.time() - start_time
    
    # 输出报告
    print("\n" + "=" * 60)
    print("# 📋 知识库导入报告")
    print("=" * 60)
    print(f"\n**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"**耗时**: {elapsed:.1f} 秒")
    
    print("\n## 📊 导入统计\n")
    print("| 项目 | 数量 |")
    print("|------|------|")
    print(f"| 扫描文件数 | {results['total']} |")
    print(f"| ✅ 成功导入 | {results['success']} |")
    print(f"| ❌ 导入失败 | {results['failed']} |")
    print(f"| ⚠️ 执行错误 | {results['error']} |")
    
    print("\n## 📁 按分类统计\n")
    print("| 分类 | 数量 |")
    print("|------|------|")
    for cat, count in sorted(results["by_category"].items(), key=lambda x: -x[1]):
        print(f"| {cat} | {count} |")
    
    if results["failed_files"]:
        print("\n## ❌ 失败文件列表\n")
        for item in results["failed_files"][:10]:  # 最多显示 10 个
            print(f"- {item['file']}: {item['error'][:100]}")
        if len(results["failed_files"]) > 10:
            print(f"- ... 还有 {len(results['failed_files']) - 10} 个失败")
    
    print("\n## 🎯 结论\n")
    if results['success'] == results['total']:
        print("✅ **全部导入成功！可以交付。**")
    elif results['success'] > results['total'] * 0.8:
        print("⚠️ **大部分导入成功，可以交付。**")
    else:
        print("❌ **导入失败较多，请检查错误日志。**")
    
    print("\n" + "=" * 60)
    
    return results


if __name__ == "__main__":
    main()