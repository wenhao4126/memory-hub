#!/bin/bash
# 傻妞定时任务：每小时检查小码任务状态
# 通过 OpenClaw 发送飞书消息通知

WORKSPACE="/home/wen/.openclaw/workspace"
cd "$WORKSPACE"

# 调用 OpenClaw 发送消息给自己，提醒检查小码
openclaw message send --channel feishu --message "🔔 定时任务提醒：该检查小码的任务状态了！

请检查：
1. 小码是否有进行中的任务
2. 任务是否超时（超过 5 分钟）
3. 如有问题，立即处理

检查时间：$(date '+%Y-%m-%d %H:%M:%S')"
