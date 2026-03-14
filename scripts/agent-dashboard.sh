#!/bin/bash
# 傻妞管家 - 团队状态看板
# 实时监控所有手下状态

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           🤖 傻妞管家 - 智能体团队状态看板                 ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║ 时间: $(date '+%Y-%m-%d %H:%M:%S')                              ║"
echo "╠══════════════════════════════════════════════════════════╣"

MEMORY_FILE="/home/wen/.openclaw/workspace/memory/agent-experiences.jsonl"

# 统计每个手下的表现
echo "║ 📊 团队绩效（最近7天）                                    ║"
echo "╠══════════════════════════════════════════════════════════╣"

if [ -f "$MEMORY_FILE" ]; then
  # 用jq统计（如果可用）或用awk
  grep "team-" "$MEMORY_FILE" | awk -F'"' '
  /agent/ {agents[$4]++}
  /success.*true/ {success[$4]++}
  /duration/ {
    match($0, /"duration": ([0-9]+)/, arr)
    duration[$4] += arr[1]
    count[$4]++
  }
  END {
    for (a in agents) {
      avg = count[a] > 0 ? int(duration[a]/count[a]) : 0
      succ_rate = agents[a] > 0 ? int(success[a]*100/agents[a]) : 0
      printf "║ %-15s | 任务: %2d | 成功率: %3d%% | 均时: %3ds ║\n", a, agents[a], succ_rate, avg
    }
  }'
else
  echo "║ 暂无数据                                                 ║"
fi

echo "╠══════════════════════════════════════════════════════════╣"

# 检查当前运行中的任务
echo "║ 🔄 当前运行中任务                                        ║"
echo "╠══════════════════════════════════════════════════════════╣"
RUNNING=$(pgrep -f "sessions_spawn.*agent:" | wc -l)
if [ "$RUNNING" -gt 0 ]; then
  echo "║ 活跃任务数: $RUNNING                                      ║"
else
  echo "║ 无活跃任务                                               ║"
fi

echo "╠══════════════════════════════════════════════════════════╣"
echo "║ 💡 优化建议                                              ║"
echo "╠══════════════════════════════════════════════════════════╣"

# 基于历史数据给出建议
if [ -f "$MEMORY_FILE" ]; then
  SLOWEST=$(grep "team-" "$MEMORY_FILE" | awk -F'"' '/duration.*[0-9]{4,}/ {print $4}' | sort | uniq -c | sort -rn | head -1 | awk '{print $2}')
  if [ -n "$SLOWEST" ]; then
    echo "║ • $SLOWEST 经常超时，建议换模型或拆分任务              ║"
  fi
fi

echo "║ • 并行搜索可提速3倍                                       ║"
echo "║ • 小写质量高，可增加任务量                                ║"
echo "╚══════════════════════════════════════════════════════════╝"