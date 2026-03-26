#!/usr/bin/env python3
"""
导入 Obsidian 文档到 knowledge 表
"""
import os
import asyncpg
import asyncio
from pathlib import Path

OBSIDIAN_DIR = "/home/wen/tools/obsidian/"
DB_URL = "postgresql://memory_user:memory_pass_2026@localhost:5433/memory_hub"

async def import_documents():
    """导入所有 markdown 文档到 knowledge 表"""
    conn = await asyncpg.connect(DB_URL)
    
    # 清空旧数据
    await conn.execute("TRUNCATE knowledge RESTART IDENTITY CASCADE;")
    
    count = 0
    obsidian_path = Path(OBSIDIAN_DIR)
    
    # 递归扫描所有子目录
    for md_file in obsidian_path.rglob("*.md"):
        try:
            # 读取文件内容
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题（第一个 # 开头的行）
            title = md_file.stem
            for line in content.split('\n'):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            import json
            # 插入 knowledge 表
            await conn.execute("""
                INSERT INTO knowledge (title, content, source, category, tags, metadata)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            """, title, content, "obsidian", "documentation", 
                ["obsidian", "imported"], 
                json.dumps({"file_path": str(md_file), "imported_at": "2026-03-20"}))
            
            count += 1
            print(f"✅ 导入：{title}")
            
        except Exception as e:
            print(f"❌ 失败：{md_file.name} - {e}")
    
    await conn.close()
    print(f"\n🎉 完成！共导入 {count} 篇文档到 knowledge 表")

if __name__ == "__main__":
    asyncio.run(import_documents())
