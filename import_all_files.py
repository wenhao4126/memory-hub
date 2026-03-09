#!/usr/bin/env python3
"""导入 Obsidian 所有知识文件到数据库"""
import os
import requests
from pathlib import Path
from datetime import datetime

# 配置
OBSIDIAN_PATH = "/home/wen/tools/obsidian"
API_BASE = "http://localhost:8000/api/v1"

# Agent ID 映射
AGENT_IDS = {
    "傻妞": "83a4c7c5-ab61-43de-b8e1-0a1e688100c0",
    "小搜": "a1b2c3d4-1111-4000-8000-000000000001",
    "小写": "a1b2c3d4-1111-4000-8000-000000000002",
    "小码": "a1b2c3d4-1111-4000-8000-000000000003",
    "小审": "a1b2c3d4-1111-4000-8000-000000000004",
    "小析": "a1b2c3d4-1111-4000-8000-000000000005",
    "小览": "a1b2c3d4-1111-4000-8000-000000000006",
    "小图": "a1b2c3d4-1111-4000-8000-000000000007",
    "小排": "a1b2c3d4-1111-4000-8000-000000000008",
}
DEFAULT_AGENT_ID = "83a4c7c5-ab61-43de-b8e1-0a1e688100c0"

# 排除的文件模式
EXCLUDE_PATTERNS = [
    ".obsidian/",        # Obsidian 插件目录
    ".imported",         # 已导入的文件
    ".swp",              # Vim 交换文件
    ".kate-swp",         # Kate 编辑器交换文件
    ".png",              # 图片
    ".jpg",              # 图片
    ".jpeg",             # 图片
    ".gif",              # 图片
    ".xlsx",             # Excel 文件
    ".xls",              # Excel 文件
    ".base",             # 数据库文件
    "密码",              # 敏感文件
    "password",          # 敏感文件
]

def should_import(file_path: str) -> bool:
    """判断文件是否应该导入"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in file_path:
            return False
    
    # 尝试读取文件（检查是否为文本文件）
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # 尝试读取前 1KB
        return True
    except (UnicodeDecodeError, PermissionError, FileNotFoundError):
        return False

def get_agent_id(filename: str) -> str:
    """根据文件名确定 agent_id"""
    for agent_name, agent_id in AGENT_IDS.items():
        if agent_name in filename:
            return agent_id
    return DEFAULT_AGENT_ID

def get_agent_name(agent_id: str) -> str:
    """根据 agent_id 获取名字"""
    for name, aid in AGENT_IDS.items():
        if aid == agent_id:
            return name
    return "傻妞"

def get_file_type(file_path: str) -> str:
    """获取文件类型"""
    ext = Path(file_path).suffix.lower()
    type_map = {
        ".md": "markdown",
        ".txt": "text",
        ".py": "python",
        ".sh": "shell",
        ".conf": "config",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".xml": "xml",
        ".html": "html",
        ".css": "css",
        ".js": "javascript",
        ".csv": "csv",
        ".bak": "backup",
    }
    return type_map.get(ext, ext or "unknown")

def import_knowledge(file_path: str) -> dict:
    """导入单个文件的知识"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_name = os.path.basename(file_path)
        file_ext = Path(file_path).suffix
        agent_id = get_agent_id(file_name)
        file_type = get_file_type(file_path)
        
        # 限制内容长度，但保留更多内容
        max_content = 2000
        truncated_content = content[:max_content]
        if len(content) > max_content:
            truncated_content += f"\n\n... [截断，原文 {len(content)} 字符]"
        
        knowledge_data = {
            "agent_id": agent_id,
            "content": f"[知识库] {file_name}\n\n{truncated_content}",
            "memory_type": "skill",  # 知识属于技能类型
            "importance": 0.8,
            "tags": ["knowledge", "obsidian", "imported", file_type]
        }
        
        response = requests.post(
            f"{API_BASE}/memories",
            json=knowledge_data,
            timeout=10
        )
        
        if response.status_code == 201:
            # 重命名文件标注已导入
            imported_path = file_path + ".imported"
            os.rename(file_path, imported_path)
            return {
                "file": file_name,
                "ext": file_ext,
                "type": file_type,
                "agent": get_agent_name(agent_id),
                "content_preview": content[:100].replace('\n', ' '),
                "size": len(content),
                "status": "success"
            }
        else:
            return {
                "file": file_name,
                "ext": file_ext,
                "type": file_type,
                "agent": get_agent_name(agent_id),
                "error": response.text,
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
    print("开始导入 Obsidian 知识库...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"路径: {OBSIDIAN_PATH}")
    print("=" * 60)
    
    # 扫描所有文件
    all_files = []
    for root, dirs, files in os.walk(OBSIDIAN_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            if should_import(file_path):
                all_files.append(file_path)
    
    print(f"\n找到 {len(all_files)} 个待导入文件")
    print("-" * 60)
    
    # 显示文件列表
    for i, f in enumerate(all_files, 1):
        print(f"{i}. {os.path.basename(f)}")
    print("-" * 60)
    
    # 统计
    results = {
        "total": len(all_files),
        "success": 0,
        "failed": 0,
        "error": 0,
        "by_agent": {},
        "by_type": {},
        "examples": []
    }
    
    # 导入文件
    for i, file_path in enumerate(all_files, 1):
        print(f"\n[{i}/{len(all_files)}] 处理: {os.path.basename(file_path)}")
        result = import_knowledge(file_path)
        
        if result["status"] == "success":
            results["success"] += 1
            agent = result["agent"]
            results["by_agent"][agent] = results["by_agent"].get(agent, 0) + 1
            
            file_type = result["type"]
            results["by_type"][file_type] = results["by_type"].get(file_type, 0) + 1
            
            if len(results["examples"]) < 5:
                results["examples"].append(result)
            
            print(f"  ✅ 导入成功")
            print(f"     Agent: {agent}")
            print(f"     类型: {file_type}")
            print(f"     大小: {result['size']} 字符")
        elif result["status"] == "failed":
            results["failed"] += 1
            print(f"  ❌ 导入失败: {result.get('error', 'unknown')}")
        else:
            results["error"] += 1
            print(f"  ⚠️ 错误: {result.get('error', 'unknown')}")
    
    # 输出报告
    print("\n" + "=" * 60)
    print("# Obsidian 知识库导入报告")
    print(f"\n**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n## 导入统计\n")
    print("| 项目 | 数量 |")
    print("|------|------|")
    print(f"| 扫描文件数 | {results['total']} |")
    print(f"| 成功导入 | {results['success']} |")
    print(f"| 导入失败 | {results['failed']} |")
    print(f"| 执行错误 | {results['error']} |")
    print(f"| 已标注文件 | {results['success']} |")
    
    print("\n## 按文件类型分类\n")
    print("| 类型 | 数量 |")
    print("|------|------|")
    for file_type, count in sorted(results["by_type"].items()):
        print(f"| {file_type} | {count} |")
    
    print("\n## 按 Agent 分类\n")
    print("| Agent | 导入知识数 |")
    print("|-------|-----------|")
    for agent, count in sorted(results["by_agent"].items()):
        print(f"| {agent} | {count} |")
    
    print("\n## 导入的知识示例\n")
    for i, ex in enumerate(results["examples"], 1):
        print(f"{i}. **文件名**: {ex['file']}")
        print(f"   - Agent: {ex['agent']}")
        print(f"   - 类型: {ex['type']}")
        print(f"   - 大小: {ex['size']} 字符")
        print(f"   - 状态: ✅\n")
    
    print("## 结论\n")
    if results['success'] == results['total']:
        print("✅ 所有文件已成功导入数据库，任务完成！")
    elif results['success'] > 0:
        print(f"⚠️ 部分文件导入成功，请检查失败的文件。")
    else:
        print("❌ 没有文件导入成功，请检查错误日志。")
    
    return results

if __name__ == "__main__":
    main()