#!/bin/bash
# Hook 脚本：任务开始时自动执行
# 用法：task-on-start.sh "任务描述" "负责人" "项目地址" "优先级" "截止时间"

set -e

# 参数检查
if [ $# -lt 3 ]; then
    echo "用法：task-on-start.sh \"任务描述\" \"负责人\" \"项目地址\" [\"优先级\"] [\"截止时间\"]"
    exit 1
fi

TASK_DESC="$1"
AGENT="$2"
PROJECT_PATH="$3"
PRIORITY="${4:-中}"
DEADLINE="${5:-未设定}"

# 确保项目目录存在
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ 项目目录不存在：$PROJECT_PATH"
    exit 1
fi

# ============================================================
# 新增：自动保存记忆到 Memory Hub
# ============================================================

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
    # 准备记忆内容
    MEMORY_CONTENT="开始任务：$TASK_DESC（优先级：$PRIORITY，截止：$DEADLINE）"
    
    # 调用 Memory Hub API 保存记忆
    curl -s -X POST "http://localhost:8000/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d "{
            \"agent_id\": \"$AGENT_ID\",
            \"content\": \"$MEMORY_CONTENT\",
            \"memory_type\": \"experience\",
            \"importance\": 0.7,
            \"tags\": [\"task_start\", \"$AGENT\", \"$(date +%Y-%m-%d)\"]
        }" > /dev/null 2>&1 && \
        echo "💾 记忆已保存：$AGENT 开始新任务" || \
        echo "⚠️  记忆保存失败（可能 API 未启动）"
fi

# ============================================================
# 创建/更新 TASK_CURRENT.md
# ============================================================

TASK_FILE="$PROJECT_PATH/TASK_CURRENT.md"

cat > "$TASK_FILE" << EOF
# 当前任务 - $AGENT

**任务开始时间**: $(date '+%Y-%m-%d %H:%M:%S')
**优先级**: $PRIORITY
**截止时间**: $DEADLINE

---

## 任务描述

$TASK_DESC

---

## 项目信息

**项目地址**: \`$PROJECT_PATH\`
**负责人**: $AGENT

---

## 必读文档（开工前先读）

- [ ] TASK_CURRENT.md - 当前任务
- [ ] README.md - 项目背景
- [ ] docs/ 下的相关文档 - 技术细节

## 下一步行动

- [ ] 开始执行任务
- [ ] 完成后更新本文件

---

## 进度记录

$(date '+%Y-%m-%d %H:%M:%S') - 任务开始

---

## ⚠️ 强制汇报机制（必须执行）

1. **代码写到项目目录**，不是工作区
2. 每完成一个功能，更新"进度记录"
3. 遇到问题立即记录到"问题日志"
4. **任务完成后必须运行**：
   ```bash
   bash /home/wen/.openclaw/workspace/hooks/task-on-complete.sh \
     "$PROJECT_PATH" \
     "任务结果描述"
   ```
5. **无论成功失败，都必须汇报**（失败也要说明原因）
6. **超时前必须汇报**（如果任务超过 5 分钟，先汇报进度）

---

*本文件由 Hook 脚本自动生成，请勿删除*
EOF

echo "✅ 任务卡片已创建：$TASK_FILE"
echo "📋 任务信息:"
echo "   负责人：$AGENT"
echo "   项目：$PROJECT_PATH"
echo "   优先级：$PRIORITY"
echo "   截止：$DEADLINE"
