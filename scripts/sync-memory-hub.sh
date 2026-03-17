#!/bin/bash
# sync-memory-hub.sh - 同步 Memory Hub 数据库到 MEMORY.md
# 用途：每次启动或完成时自动同步，保证符号链接指向最新数据

MEMORY_HUB_API="http://localhost:8000/api/v1"
EXPORT_FILE="/home/wen/projects/memory-hub/data/memory-hub-export.md"
SYMLINK="/home/wen/.openclaw/workspace/MEMORY.md"

echo "🔄 正在从 Memory Hub 数据库同步记忆..."

# 从 API 导出记忆
curl -s "$MEMORY_HUB_API/memories/export/markdown" -o "$EXPORT_FILE"

if [ -f "$EXPORT_FILE" ] && [ -s "$EXPORT_FILE" ]; then
    echo "✅ 记忆已同步到 $EXPORT_FILE"
    echo "📎 符号链接：$SYMLINK"
    ls -la "$SYMLINK"
else
    echo "❌ 同步失败：导出文件为空或不存在"
    exit 1
fi
