#!/bin/bash
# 傻妞管家 - 飞书 Bitable 任务管理脚本

CONFIG_FILE="/home/wen/.openclaw/workspace/config/feishu-bitable.json"

# 读取配置
APP_ID=$(jq -r '.app_id' "$CONFIG_FILE")
APP_SECRET=$(jq -r '.app_secret' "$CONFIG_FILE")
BASE_TOKEN=$(jq -r '.base_token' "$CONFIG_FILE")
TABLE_ID=$(jq -r '.table_id' "$CONFIG_FILE")

# 获取访问令牌
get_access_token() {
  curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/" \
    -H "Content-Type: application/json" \
    -d "{\"app_id\":\"$APP_ID\",\"app_secret\":\"$APP_SECRET\"}" | \
    jq -r '.tenant_access_token'
}

# 创建任务
create_task() {
  local description="$1"
  local agent="$2"
  local priority="${3:-中}"
  local due_minutes="${4:-5}"
  
  local token=$(get_access_token)
  local task_id="task-$(date +%s)-$$"
  local start_time=$(($(date +%s) * 1000))
  local due_time=$(($(date -d "+${due_minutes} minutes" +%s) * 1000))
  
  curl -s -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/$BASE_TOKEN/tables/$TABLE_ID/records" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{
      \"fields\": {
        \"任务 ID\": \"$task_id\",
        \"任务描述\": \"$description\",
        \"负责人\": \"$agent\",
        \"状态\": \"进行中\",
        \"优先级\": \"$priority\",
        \"开始时间\": \"$start_time\",
        \"截止时间\": \"$due_time\"
      }
    }" | jq '.'
}

# 更新任务状态
update_task() {
  local task_id="$1"
  local status="$2"
  local result="${3:-}"
  
  local token=$(get_access_token)
  
  # 先查找任务记录 ID
  local record_id=$(curl -s -X GET "https://open.feishu.cn/open-apis/bitable/v1/apps/$BASE_TOKEN/tables/$TABLE_ID/records" \
    -H "Authorization: Bearer $token" | \
    jq -r ".items[] | select(.fields.\"任务 ID\"==\"$task_id\") | .record_id")
  
  if [ -z "$record_id" ]; then
    echo "任务未找到：$task_id"
    return 1
  fi
  
  # 更新状态
  local update_data="{\"fields\": {\"状态\": \"$status\""
  if [ "$status" = "已完成" ] || [ "$status" = "已超时" ]; then
    local complete_time=$(date -Iseconds)
    update_data="$update_data, \"完成时间\": \"$complete_time\""
  fi
  if [ -n "$result" ]; then
    update_data="$update_data, \"任务结果\": \"$result\""
  fi
  update_data="$update_data}}"
  
  curl -s -X PUT "https://open.feishu.cn/open-apis/bitable/v1/apps/$BASE_TOKEN/tables/$TABLE_ID/records/$record_id" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$update_data" | jq '.'
}

# 查询任务
query_tasks() {
  local status="${1:-}"
  local agent="${2:-}"
  
  local token=$(get_access_token)
  
  local url="https://open.feishu.cn/open-apis/bitable/v1/apps/$BASE_TOKEN/tables/$TABLE_ID/records"
  local filter=""
  
  if [ -n "$status" ]; then
    filter="filter={\"conjunction\":\"and\",\"conditions\":[{\"field\":\"状态\",\"operator\":\"equals\",\"value\":\"$status\"}]}"
  fi
  
  curl -s -X GET "$url" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" | \
    jq '.items[] | {id: .fields."任务 ID", desc: .fields."任务描述", agent: .fields."负责人", status: .fields."状态", due: .fields."截止时间"}'
}

# 检查超时任务
check_timeout() {
  local token=$(get_access_token)
  local now=$(date +%s)
  
  curl -s -X GET "https://open.feishu.cn/open-apis/bitable/v1/apps/$BASE_TOKEN/tables/$TABLE_ID/records" \
    -H "Authorization: Bearer $token" | \
    jq -r ".items[] | select(.fields.\"状态\"==\"进行中\") | select(.fields.\"截止时间\" < \"$(date -Iseconds)\") | .fields.\"任务 ID\"" | \
    while read task_id; do
      echo "⚠️ 任务超时：$task_id"
      update_task "$task_id" "已超时"
    done
}

# 显示帮助
show_help() {
  echo "傻妞任务管理系统"
  echo ""
  echo "用法："
  echo "  $0 create <描述> <负责人> [优先级] [截止分钟]"
  echo "  $0 update <任务 ID> <状态> [结果]"
  echo "  $0 query [状态] [负责人]"
  echo "  $0 timeout"
  echo ""
  echo "状态选项：待办/进行中/已完成/已超时/已取消"
  echo "负责人选项：小搜/小写/小码/小审/小析/小览/小图/小排"
}

# 主程序
case "$1" in
  create)
    create_task "$2" "$3" "$4" "$5"
    ;;
  update)
    update_task "$2" "$3" "$4"
    ;;
  query)
    query_tasks "$2" "$3"
    ;;
  timeout)
    check_timeout
    ;;
  *)
    show_help
    ;;
esac
