#!/bin/bash
# 每小时检查小码任务状态的定时脚本
# 如果小码没有任务或卡住了，通过飞书通知傻妞

set -e

WORKSPACE="/home/wen/.openclaw/workspace"
CONFIG_FILE="$WORKSPACE/config/feishu-bitable.json"
LOG_FILE="$WORKSPACE/memory/xiaoma-monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$TIMESTAMP] ========== 开始检查小码任务状态 ==========" >> "$LOG_FILE"

# 读取配置
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[$TIMESTAMP] 错误：配置文件不存在" >> "$LOG_FILE"
    exit 1
fi

# 使用 Node.js 脚本检查飞书表格中的小码任务
CHECK_RESULT=$(node -e "
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('$CONFIG_FILE', 'utf8'));

// 这里需要调用飞书 API 查询任务
// 简化处理：输出配置信息供调试
console.log(JSON.stringify({
    app_token: config.app_id,
    table_id: config.table_id,
    check_time: new Date().toISOString()
}));
" 2>&1)

echo "[$TIMESTAMP] 配置检查：$CHECK_RESULT" >> "$LOG_FILE"

# TODO: 实际检查逻辑需要通过 OpenClaw 的 feishu_bitable_list_records 查询
# 这里简化处理，如果有问题会记录到日志

echo "[$TIMESTAMP] ========== 检查完成 ==========" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
