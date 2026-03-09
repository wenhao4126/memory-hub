#!/bin/bash
# 傻妞管家 - 经验学习Hook
# 每次任务后自动记录经验，用于下次优化

AGENT="$1"
TASK="$2"
DURATION="$3"
SUCCESS="$4"
QUALITY="$5"  # 1-10分
NOTES="$6"
OPTIMIZATION="$7"

MEMORY_FILE="/home/wen/.openclaw/workspace/memory/agent-experiences.jsonl"

# 生成经验记录
EXPERIENCE=$(jq -n \
  --arg ts "$(date -Iseconds)" \
  --arg agent "$AGENT" \
  --arg task "$TASK" \
  --argjson duration "$DURATION" \
  --argjson success "$SUCCESS" \
  --argjson quality "$QUALITY" \
  --arg notes "$NOTES" \
  --arg optimization "$OPTIMIZATION" \
  '{timestamp: $ts, agent: $agent, task: $task, duration: $duration, success: $success, quality: $quality, notes: $notes, optimization: $optimization}')

# 追加到记忆库
echo "$EXPERIENCE" >> "$MEMORY_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🧠 经验已记录: $AGENT 完成 $TASK | 质量: ${QUALITY}/10"

# 如果质量低，触发自动优化
if [ "$QUALITY" -lt 6 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 质量偏低，触发优化流程..."
  
  # 分析原因并建议改进
  if [ "$DURATION" -gt 300 ]; then
    echo "SUGGESTION|${AGENT}|${TASK}|超时，建议换模型或拆分任务"
  else
    echo "SUGGESTION|${AGENT}|${TASK}|质量低，建议调整prompt或增加示例"
  fi
fi