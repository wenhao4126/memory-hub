#!/bin/bash
# 傻妞管家 - 智能编排引擎
# 根据历史经验自动分配任务和优化策略

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🧠 启动智能编排引擎"

TASK_TYPE="$1"  # news-search / summary / code / analysis
MEMORY_FILE="/home/wen/.openclaw/workspace/memory/agent-experiences.jsonl"

# ========== 读取历史经验 ==========
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📚 读取历史经验..."

# 找出最适合当前任务的手下
BEST_AGENT=$(grep "$TASK_TYPE" "$MEMORY_FILE" | \
  jq -s 'group_by(.agent) | map({agent: .[0].agent, avg_quality: (map(.quality) | add / length), avg_duration: (map(.duration) | add / length)}) | sort_by(-.avg_quality, .avg_duration) | .[0].agent' -r 2>/dev/null || echo "team-researcher")

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎯 最佳人选: $BEST_AGENT"

# 获取该手下的最优策略
BEST_STRATEGY=$(grep "$BEST_AGENT.*$TASK_TYPE" "$MEMORY_FILE" | \
  jq -s 'sort_by(-.quality) | .[0].optimization' -r 2>/dev/null || echo "default")

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 💡 推荐策略: $BEST_STRATEGY"

# ========== 动态组建团队 ==========
case "$TASK_TYPE" in
  "news-search")
    TEAM=("team-researcher:hn" "team-researcher:mtp" "team-researcher:ph")
    STRATEGY="并行搜索3个源，各拿2-3条"
    ;;
  "summary")
    TEAM=("team-writer:A" "team-writer:B" "team-writer:C")
    STRATEGY="分组总结，每组处理2条"
    ;;
  "code")
    TEAM=("team-coder:impl" "team-coder:review")
    STRATEGY="实现+审核双保险"
    ;;
  *)
    TEAM=("$BEST_AGENT:main")
    STRATEGY="单兵作战"
    ;;
esac

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 👥 组建团队: ${TEAM[@]}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📋 执行策略: $STRATEGY"

# 输出给傻妞管家决策
echo "ORCHESTRATION_RESULT|${TASK_TYPE}|${BEST_AGENT}|${STRATEGY}|${TEAM[*]}"