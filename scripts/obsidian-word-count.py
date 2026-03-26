#!/usr/bin/env python3
"""
统计 Obsidian 文档字数并生成报告
"""
import os
from pathlib import Path

OBSIDIAN_DIR = "/home/wen/tools/obsidian/"
OUTPUT_FILE = "/home/wen/tools/obsidian/文档统计报告.md"

def count_words(file_path):
    """统计文件字数（不含空行）"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line for line in f.readlines() if line.strip()]
        return sum(len(line.split()) for line in lines)

def main():
    obsidian_path = Path(OBSIDIAN_DIR)
    stats = []
    
    # 递归扫描所有 .md 文件
    for md_file in obsidian_path.rglob("*.md"):
        try:
            word_count = count_words(md_file)
            rel_path = md_file.relative_to(obsidian_path)
            stats.append((str(rel_path), word_count))
        except Exception as e:
            print(f"❌ 失败：{md_file.name} - {e}")
    
    # 按字数排序
    stats.sort(key=lambda x: x[1], reverse=True)
    
    # 计算统计信息
    total_docs = len(stats)
    total_words = sum(x[1] for x in stats)
    avg_words = total_words // total_docs if total_docs > 0 else 0
    
    # 生成报告
    report = f"""# Obsidian 文档统计报告

**生成时间**: 2026-03-20  
**扫描目录**: {OBSIDIAN_DIR}

## 📊 总体统计

- **文档总数**: {total_docs} 篇
- **总字数**: {total_words:,} 字
- **平均每篇**: {avg_words:,} 字

## 🔝 TOP 10 最长文档

| 排名 | 文件名 | 字数 |
|------|--------|------|
"""
    
    for i, (filename, count) in enumerate(stats[:10], 1):
        report += f"| {i} | {filename} | {count:,} |\n"
    
    report += f"""
## 🔻 TOP 10 最短文档

| 排名 | 文件名 | 字数 |
|------|--------|------|
"""
    
    for i, (filename, count) in enumerate(stats[-10:], 1):
        report += f"| {i} | {filename} | {count:,} |\n"
    
    # 保存报告
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已保存到：{OUTPUT_FILE}")
    print(f"📊 共统计 {total_docs} 篇文档，总计 {total_words:,} 字")

if __name__ == "__main__":
    main()
