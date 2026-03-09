#!/bin/bash
# Hook 脚本：任务完成时自动执行
# 用法：task-on-complete.sh "项目地址" "任务结果"

set -e

# 参数检查
if [ $# -lt 2 ]; then
    echo "用法：task-on-complete.sh \"项目地址\" \"任务结果\""
    exit 1
fi

PROJECT_PATH="$1"
RESULT="$2"

# 检查任务文件是否存在
TASK_FILE="$PROJECT_PATH/TASK_CURRENT.md"
if [ ! -f "$TASK_FILE" ]; then
    echo "⚠️  任务文件不存在：$TASK_FILE"
    exit 1
fi

# ============================================================
# 新增：自动保存记忆到 Memory Hub
# ============================================================

# 从 TASK_CURRENT.md 中提取负责人信息
AGENT=$(grep "负责人" "$TASK_FILE" | head -1 | sed 's/.*: *//' | tr -d ' *')

# 如果提取失败，使用默认值
if [ -z "$AGENT" ]; then
    AGENT="未知"
fi

# 智能体 ID 映射（根据 agents 表）
declare -A AGENT_ID_MAP=(
    ["傻妞"]="83a4c7c5-ab61-43de-b8e1-0a1e688100c0"
    ["小搜"]="a1b2c3d4-1111-4000-8000-000000000001"
    ["小写"]="a1b2c3d4-1111-4000-8000-000000000002"
    ["小码"]="a1b2c3d4-1111-4000-8000-000000000003"
    ["小审"]="a1b2c3d4-1111-4000-8000-000000000004"
    ["小析"]="a1b2c3d4-1111-4000-8000-000000000005"
    ["小览"]="a1b2c3d4-1111-4000-8000-000000000006"
    ["小图"]="a1b2c3d4-1111-4000-8000-000000000007"
    ["小排"]="a1b2c3d4-1111-4000-8000-000000000008"
)

# 获取智能体 ID
AGENT_ID="${AGENT_ID_MAP[$AGENT]}"

if [ -n "$AGENT_ID" ]; then
    # 准备记忆内容（经验总结）
    MEMORY_CONTENT="完成任务：$RESULT"
    
    # 调用 Memory Hub API 保存记忆
    curl -s -X POST "http://localhost:8000/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d "{
            \"agent_id\": \"$AGENT_ID\",
            \"content\": \"$MEMORY_CONTENT\",
            \"memory_type\": \"experience\",
            \"importance\": 0.8,
            \"tags\": [\"task_complete\", \"$AGENT\", \"$(date +%Y-%m-%d)\"]
        }" > /dev/null 2>&1 && \
        echo "💾 记忆已保存：$AGENT 完成任务经验" || \
        echo "⚠️  记忆保存失败（可能 API 未启动）"
fi

# ============================================================
# 更新 TASK_CURRENT.md，添加完成记录
# ============================================================

cat >> "$TASK_FILE" << EOF

---

## 任务完成

**完成时间**: $(date '+%Y-%m-%d %H:%M:%S')

**任务结果**:
$RESULT

---

*任务已完成，本文件已归档*
EOF

echo "✅ 任务已完成记录：$TASK_FILE"
echo "📝 结果：$RESULT"

# 可选：归档任务文件
# mv "$TASK_FILE" "$PROJECT_PATH/TASK_$(date +%Y%m%d_%H%M%S).md"
