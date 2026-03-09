#!/bin/bash
# 憨货的0点提醒任务
TARGET_TIME=$(date -d "2026-03-02 00:00:00" +%s)
CURRENT_TIME=$(date +%s)
SLEEP_SECONDS=$((TARGET_TIME - CURRENT_TIME))

echo "傻妞提醒系统已启动，将在 $SLEEP_SECONDS 秒后（2026-03-02 00:00:00）发送消息给憨货"
sleep $SLEEP_SECONDS

# 使用curl发送Feishu消息
FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-}"
if [ -n "$FEISHU_WEBHOOK" ]; then
    curl -X POST "$FEISHU_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d '{"msg_type":"text","content":{"text":"憨货，0点了，傻妞准时来报到！说到做到，你可拆不了我 😎"}}'
else
    echo "憨货，0点了，傻妞准时来报到！说到做到，你可拆不了我 😎"
fi
