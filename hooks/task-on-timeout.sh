#!/bin/bash
# 任务超时 Hook

TASK_ID="$1"
AGENT="$2"

# 更新任务状态为已超时
/home/wen/.openclaw/workspace/scripts/task-manager.sh update "$TASK_ID" "已超时"

# 通知傻妞
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 任务超时：$TASK_ID | $AGENT" >> /home/wen/.openclaw/workspace/logs/task-timeout.log
