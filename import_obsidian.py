#!/usr/bin/env python3
"""
Obsidian 文件导入到 knowledge 表
"""
import os
import requests
from datetime import datetime
from pathlib import Path

obsidian_path = "/home/wen/tools/obsidian"
knowledge_api_url = "http://localhost:8000/api/v1/knowledge"

# 扫描所有文件（排除 .obsidian 目录和已导入的 .dr 文件）
all_files = []
for root, dirs, files in os.walk(obsidian_path):
    # 跳过 .obsidian 插件目录
    dirs[:] = [d for d in dirs if d != '.obsidian']
    for f in files:
        if not f.endswith('.dr'):
            all_files.append(os.path.join(root, f))

print(f"找到 {len(all_files)} 个文件待导入")
print("=" * 60)

# 统计
success_count = 0
fail_count = 0
category_stats = {}
type_stats = {}
imported_files = []

for file_path in all_files:
    try:
        # 读取内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 获取文件名和路径
        file_name = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, obsidian_path)
        file_ext = os.path.splitext(file_name)[1] or '.unknown'
        
        # 跳过二进制文件
        if file_ext in ['.xlsx', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.db']:
            print(f"⏭️ 跳过二进制文件：{file_name}")
            continue
        
        # 提取标题（第一行或文件名）
        title = content.split('\n')[0].lstrip('#').strip() if content.startswith('#') else file_name
        title = title[:500]  # 限制长度
        
        # 确定分类（根据文件路径或内容）
        category = "general"
        path_lower = file_path.lower()
        content_lower = content.lower()
        
        if "编程" in file_path or "python" in path_lower or "code" in path_lower or "编程" in content_lower:
            category = "编程"
        elif "设计" in file_path or "design" in path_lower:
            category = "设计"
        elif "工具" in file_path or "tool" in path_lower:
            category = "工具"
        elif "配置" in file_path or "config" in path_lower or "设置" in file_path:
            category = "配置"
        elif "学习" in file_path or "study" in path_lower:
            category = "学习"
        elif "项目" in file_path or "project" in path_lower:
            category = "项目"
        elif "docs" in path_lower or "api" in path_lower or "指南" in file_path:
            category = "文档"
        
        # 创建知识记录 - 使用 system agent ID
        knowledge_data = {
            "agent_id": "973c8f8b-2b70-4641-9db9-4c04f2e8be10",  # system agent
            "title": title,
            "content": content[:50000],  # 限制 5 万字
            "category": category,
            "tags": ["obsidian", "imported", file_ext.replace('.', '')],
            "source": f"Obsidian/{relative_path}",
            "importance": 0.8,
            "metadata": {
                "original_file": file_name,
                "file_path": relative_path,
                "file_size": os.path.getsize(file_path),
                "import_date": datetime.now().isoformat(),
                "file_extension": file_ext
            }
        }
        
        # 调用 API 创建知识
        response = requests.post(knowledge_api_url, json=knowledge_data, timeout=30)
        
        if response.status_code in [200, 201]:
            print(f"✅ 导入成功：{file_name} ({category})")
            success_count += 1
            
            # 标注已导入（添加 .dr 后缀）
            imported_path = file_path + ".dr"
            os.rename(file_path, imported_path)
            print(f"   已标注：{os.path.basename(imported_path)}")
            
            # 统计
            category_stats[category] = category_stats.get(category, 0) + 1
            type_stats[file_ext] = type_stats.get(file_ext, 0) + 1
            imported_files.append({
                "file": file_name,
                "category": category,
                "title": title[:50] + "..." if len(title) > 50 else title
            })
        else:
            print(f"❌ 导入失败：{file_name} - HTTP {response.status_code}: {response.text[:200]}")
            fail_count += 1
            
    except Exception as e:
        print(f"❌ 处理失败 {file_path}: {e}")
        fail_count += 1

print("\n" + "=" * 60)
print(f"导入完成：成功 {success_count} 个，失败 {fail_count} 个")

# 输出报告
print("\n# Obsidian 知识库导入报告")
print(f"\n**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"\n## 导入统计\n")
print("| 项目 | 数量 |")
print("|------|------|")
print(f"| 扫描文件数 | {len(all_files)} |")
print(f"| 成功导入 | {success_count} |")
print(f"| 导入失败 | {fail_count} |")
print(f"| 已标注文件 | {success_count} |")

print(f"\n## 按分类统计\n")
print("| 分类 | 数量 |")
print("|------|------|")
for cat, count in sorted(category_stats.items()):
    print(f"| {cat} | {count} |")

print(f"\n## 按文件类型统计\n")
print("| 类型 | 数量 |")
print("|------|------|")
for ext, count in sorted(type_stats.items()):
    print(f"| {ext} | {count} |")

print(f"\n## 导入文件列表\n")
for i, f in enumerate(imported_files[:10], 1):
    print(f"{i}. **{f['file']}**")
    print(f"   - 分类：{f['category']}")
    print(f"   - 标题：{f['title']}")
    print(f"   - 状态：✅")

if len(imported_files) > 10:
    print(f"\n... 还有 {len(imported_files) - 10} 个文件")

print("\n## 结论\n")
if fail_count == 0:
    print("[可以交付] 所有文件已成功导入知识库！")
else:
    print(f"[需关注] 有 {fail_count} 个文件导入失败，请检查日志。")