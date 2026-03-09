#!/bin/bash
# 傻妞管家 - 手下任务监控Hook
# 功能：监控subagent任务，超过5分钟自动报警并优化

TASK_NAME="$1"
START_TIME=$(date +%s)
MAX_WAIT=300  # 5分钟 = 300秒

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始监控任务: $TASK_NAME"

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 任务超时！已运行 ${ELAPSED}秒"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 触发优化流程..."
        
        # 发送通知给傻妞管家
        echo "TASK_TIMEOUT|$TASK_NAME|$ELAPSED" >> /home/wen/.openclaw/workspace/logs/hook-alerts.log
        
        exit 1
    fi
    
    # 每30秒检查一次
    sleep 30
done