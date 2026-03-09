#!/bin/bash
# 傻妞管家 - 并行AI新闻工作流
# 多个手下同时工作，最后汇总

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 启动并行AI新闻任务"

WORK_DIR="/home/wen/.openclaw/workspace/tmp/news-$(date +%s)"
mkdir -p "$WORK_DIR"

# ========== 并行阶段1：多源搜索 ==========
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📋 同时派出多个小搜..."

# 小搜A - Hacker News
sessions_spawn --agent team-researcher --mode run \
  --task "搜索Hacker News最新AI新闻，获取4条，输出JSON到 $WORK_DIR/hn.json" &
PID_HN=$!

# 小搜B - 技术博客  
sessions_spawn --agent team-researcher --mode run \
  --task "搜索MarkTechPost最新AI新闻，获取3条，输出JSON到 $WORK_DIR/mtp.json" &
PID_MTP=$!

# 小搜C - 产品动态
sessions_spawn --agent team-researcher --mode run \
  --task "搜索Product Hunt最新AI工具，获取2条，输出JSON到 $WORK_DIR/ph.json" &
PID_PH=$!

# 等待所有小搜完成（最多5分钟）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏱️ 等待小搜们回来（最多5分钟）..."
wait -n $PID_HN $PID_MTP $PID_PH
timeout 300 wait $PID_HN $PID_MTP $PID_PH || echo "⚠️ 有任务超时"

# ========== 并行阶段2：分组总结 ==========
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📝 同时派出多个小写..."

# 小写A - 总结Hacker News
if [ -f "$WORK_DIR/hn.json" ]; then
  sessions_spawn --agent team-writer --mode run \
    --task "读取$WORK_DIR/hn.json，每条翻译成3句话中文总结，输出到$WORK_DIR/summary-hn.txt" &
  PID_WRITE_HN=$!
fi

# 小写B - 总结技术博客
if [ -f "$WORK_DIR/mtp.json" ]; then
  sessions_spawn --agent team-writer --mode run \
    --task "读取$WORK_DIR/mtp.json，每条翻译成3句话中文总结，输出到$WORK_DIR/summary-mtp.txt" &
  PID_WRITE_MTP=$!
fi

# 小写C - 总结产品动态
if [ -f "$WORK_DIR/ph.json" ]; then
  sessions_spawn --agent team-writer --mode run \
    --task "读取$WORK_DIR/ph.json，每条翻译成3句话中文总结，输出到$WORK_DIR/summary-ph.txt" &
  PID_WRITE_PH=$!
fi

# 等待所有小写完成（最多5分钟）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏱️ 等待小写们回来（最多5分钟）..."
timeout 300 wait $PID_WRITE_HN $PID_WRITE_MTP $PID_WRITE_PH || echo "⚠️ 有任务超时"

# ========== 阶段3：傻妞审核汇总 ==========
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 傻妞管家审核汇总..."

# 合并所有总结
cat $WORK_DIR/summary-*.txt > $WORK_DIR/final-summary.txt 2>/dev/null

# 去重、排序、选最优的4-5条
# （实际由傻妞管家读取后处理）

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 并行任务完成，结果在: $WORK_DIR/final-summary.txt"

# 清理临时文件（保留1天）
find /home/wen/.openclaw/workspace/tmp/news-* -mtime +1 -delete 2>/dev/null