#!/bin/bash
# 傻妞管家 - 每日AI新闻自动化脚本
# 运行时间：每天10:00

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 启动每日AI新闻任务"

# Step 1: 派小搜去搜新闻（限时5分钟）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📋 派小搜(team-researcher)搜索新闻..."
/home/wen/.openclaw/workspace/hooks/subagent-monitor.sh "team-researcher-search" &
MONITOR_PID=$!

# 这里调用subagent（实际由傻妞管家通过sessions_spawn执行）
# 结果会写入 /home/wen/.openclaw/workspace/tmp/news-raw.json

# Step 2: 等小搜回来，派小写去总结（限时5分钟）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📝 派小写(team-writer)总结翻译..."
/home/wen/.openclaw/workspace/hooks/subagent-monitor.sh "team-writer-summary" &
MONITOR_PID2=$!

# Step 3: 我审核并发送
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 傻妞管家审核中..."

# Step 4: 发送到飞书
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📤 发送到飞书..."

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 任务完成"