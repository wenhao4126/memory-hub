#!/bin/bash

# AI 新闻 + GitHub 趋势推送脚本 - 每天 10:00 执行
# 推送 3 条最新 AI 新闻 + GitHub 趋势榜 Top 5 到飞书

cd /home/wen/.openclaw/workspace

# 调用小搜使用 agent-reach 技能搜集 AI 新闻 + GitHub 趋势榜
# 使用 --to 参数指定目标会话（飞书用户）
openclaw agent \
  --agent team-researcher \
  --message "你是小搜 🟢，负责信息采集。

📋 你的任务：
搜集最新 AI 新闻 + GitHub 趋势榜并推送给憨货

**任务 1：AI 新闻搜索**
使用 agent-reach 技能搜索：
- Hacker News AI 板块
- Reddit r/MachineLearning
- Twitter/X AI 相关话题
- TechCrunch、The Verge AI 专栏
- 机器之心、量子位（中文源）

**任务 2：GitHub 趋势榜**
使用 GitHub CLI (gh) 获取：
- GitHub Trending AI/ML 分类
- 今日趋势项目 Top 10
- 包含：项目名称、Star 数、**4 句话中文总结**、GitHub 链接

**输出要求**：
1. AI 新闻 3 条（24-48 小时内）
   - 每条 2-3 句通俗总结
   - 附带原文链接

2. GitHub 趋势 Top 10
   - 项目名称 + Star 数
   - 4 句话中文总结描述
   - GitHub 链接

**格式**：Markdown

开始搜索！" \
  --channel feishu \
  --deliver

echo "AI 新闻 + GitHub 趋势推送任务已启动 - $(date)"
