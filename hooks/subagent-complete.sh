#!/bin/bash
# 傻妞管家 - 手下任务完成回调Hook
# 功能：任务完成后通知管家，触发下一步

AGENT_NAME="$1"
TASK_TYPE="$2"
RESULT_FILE="$3"
START_TIME="$4"
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 任务完成: $AGENT_NAME | 类型: $TASK_TYPE | 耗时: ${DURATION}秒"

# 记录到日志
echo "COMPLETE|$AGENT_NAME|$TASK_TYPE|$DURATION|$RESULT_FILE" >> /home/wen/.openclaw/workspace/logs/agent-callbacks.log

# 如果所有并行任务都完成了，通知傻妞汇总
PENDING_COUNT=$(pgrep -f "sessions_spawn.*team-" | wc -l)
if [ "$PENDING_COUNT" -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔔 所有并行任务完成，通知傻妞汇总..."
  # 触发汇总流程
fi