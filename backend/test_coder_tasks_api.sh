#!/bin/bash

# ============================================================
# Memory Hub - 小码任务 API 测试脚本
# ============================================================
# 功能：测试 coder_tasks API 端点
# 作者：小码 1 号 🟡
# 日期：2026-03-24
# ============================================================

# 配置
BASE_URL="${API_BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-test_api_key}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "🟡 小码任务 API 测试"
echo "============================================================"
echo "BASE_URL: $BASE_URL"
echo "API_KEY:  $API_KEY"
echo "============================================================"
echo ""

# 测试健康检查
echo -e "${YELLOW}[测试 1] 健康检查${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/v1/health")
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HEALTH_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
    echo "$HEALTH_BODY" | jq .
else
    echo -e "${RED}❌ 健康检查失败 (HTTP $HEALTH_CODE)${NC}"
    echo "$HEALTH_BODY"
    exit 1
fi
echo ""

# 测试 1: 创建小码任务
echo -e "${YELLOW}[测试 2] 创建小码任务 (POST /api/v1/coder-tasks)${NC}"

CREATE_PAYLOAD='{
    "coder_id": "550e8400-e29b-41d4-a716-446655440001",
    "coder_name": "小码 1 号",
    "task_id": "task_001",
    "task_type": "code",
    "title": "实现 API 路由",
    "project_path": "/home/wen/projects/memory-hub/backend",
    "status": "completed",
    "result": "成功创建 coder_tasks API 路由",
    "duration_seconds": 180,
    "description": "测试任务描述",
    "priority": "高"
}'

echo "请求体:"
echo "$CREATE_PAYLOAD" | jq .

CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/api/v1/coder-tasks" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$CREATE_PAYLOAD")

CREATE_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
CREATE_BODY=$(echo "$CREATE_RESPONSE" | head -n-1)

if [ "$CREATE_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 创建任务成功${NC}"
    echo "响应:"
    echo "$CREATE_BODY" | jq .
    TASK_ID=$(echo "$CREATE_BODY" | jq -r '.id')
    echo "任务 ID: $TASK_ID"
else
    echo -e "${RED}❌ 创建任务失败 (HTTP $CREATE_CODE)${NC}"
    echo "$CREATE_BODY"
fi
echo ""

# 测试 2: 创建另一个任务
echo -e "${YELLOW}[测试 3] 创建第二个任务${NC}"

CREATE_PAYLOAD_2='{
    "coder_id": "550e8400-e29b-41d4-a716-446655440002",
    "coder_name": "小码 2 号",
    "task_id": "task_002",
    "task_type": "search",
    "title": "搜索文档",
    "status": "pending",
    "priority": "中"
}'

CREATE_RESPONSE_2=$(curl -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/api/v1/coder-tasks" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$CREATE_PAYLOAD_2")

CREATE_CODE_2=$(echo "$CREATE_RESPONSE_2" | tail -n1)
CREATE_BODY_2=$(echo "$CREATE_RESPONSE_2" | head -n-1)

if [ "$CREATE_CODE_2" = "200" ]; then
    echo -e "${GREEN}✅ 创建第二个任务成功${NC}"
    echo "响应:"
    echo "$CREATE_BODY_2" | jq .
else
    echo -e "${RED}❌ 创建第二个任务失败 (HTTP $CREATE_CODE_2)${NC}"
    echo "$CREATE_BODY_2"
fi
echo ""

# 测试 3: 查询任务列表（无过滤）
echo -e "${YELLOW}[测试 4] 查询任务列表 - 无过滤 (GET /api/v1/coder-tasks)${NC}"

LIST_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/api/v1/coder-tasks?limit=10" \
    -H "X-API-Key: $API_KEY")

LIST_CODE=$(echo "$LIST_RESPONSE" | tail -n1)
LIST_BODY=$(echo "$LIST_RESPONSE" | head -n-1)

if [ "$LIST_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 查询任务列表成功${NC}"
    echo "响应:"
    echo "$LIST_BODY" | jq .
    TOTAL=$(echo "$LIST_BODY" | jq -r '.total')
    echo "总记录数：$TOTAL"
else
    echo -e "${RED}❌ 查询任务列表失败 (HTTP $LIST_CODE)${NC}"
    echo "$LIST_BODY"
fi
echo ""

# 测试 4: 按 coder_name 过滤
echo -e "${YELLOW}[测试 5] 按小码名称过滤 (coder_name=小码 1 号)${NC}"

FILTER_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/api/v1/coder-tasks?coder_name=小码 1 号&limit=10" \
    -H "X-API-Key: $API_KEY")

FILTER_CODE=$(echo "$FILTER_RESPONSE" | tail -n1)
FILTER_BODY=$(echo "$FILTER_RESPONSE" | head -n-1)

if [ "$FILTER_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 按名称过滤成功${NC}"
    echo "响应:"
    echo "$FILTER_BODY" | jq .
else
    echo -e "${RED}❌ 按名称过滤失败 (HTTP $FILTER_CODE)${NC}"
    echo "$FILTER_BODY"
fi
echo ""

# 测试 5: 按 status 过滤
echo -e "${YELLOW}[测试 6] 按状态过滤 (status=completed)${NC}"

STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/api/v1/coder-tasks?status=completed&limit=10" \
    -H "X-API-Key: $API_KEY")

STATUS_CODE=$(echo "$STATUS_RESPONSE" | tail -n1)
STATUS_BODY=$(echo "$STATUS_RESPONSE" | head -n-1)

if [ "$STATUS_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 按状态过滤成功${NC}"
    echo "响应:"
    echo "$STATUS_BODY" | jq .
else
    echo -e "${RED}❌ 按状态过滤失败 (HTTP $STATUS_CODE)${NC}"
    echo "$STATUS_BODY"
fi
echo ""

# 测试 6: 获取单个任务详情
if [ -n "$TASK_ID" ]; then
    echo -e "${YELLOW}[测试 7] 获取单个任务详情 (GET /api/v1/coder-tasks/$TASK_ID)${NC}"
    
    DETAIL_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X GET "$BASE_URL/api/v1/coder-tasks/$TASK_ID" \
        -H "X-API-Key: $API_KEY")
    
    DETAIL_CODE=$(echo "$DETAIL_RESPONSE" | tail -n1)
    DETAIL_BODY=$(echo "$DETAIL_RESPONSE" | head -n-1)
    
    if [ "$DETAIL_CODE" = "200" ]; then
        echo -e "${GREEN}✅ 获取任务详情成功${NC}"
        echo "响应:"
        echo "$DETAIL_BODY" | jq .
    else
        echo -e "${RED}❌ 获取任务详情失败 (HTTP $DETAIL_CODE)${NC}"
        echo "$DETAIL_BODY"
    fi
    echo ""
fi

# 测试 7: 测试分页
echo -e "${YELLOW}[测试 8] 测试分页 (limit=1, offset=0)${NC}"

PAGINATION_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/api/v1/coder-tasks?limit=1&offset=0" \
    -H "X-API-Key: $API_KEY")

PAGINATION_CODE=$(echo "$PAGINATION_RESPONSE" | tail -n1)
PAGINATION_BODY=$(echo "$PAGINATION_RESPONSE" | head -n-1)

if [ "$PAGINATION_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 分页查询成功${NC}"
    echo "响应:"
    echo "$PAGINATION_BODY" | jq .
else
    echo -e "${RED}❌ 分页查询失败 (HTTP $PAGINATION_CODE)${NC}"
    echo "$PAGINATION_BODY"
fi
echo ""

echo "============================================================"
echo "🎉 测试完成"
echo "============================================================"
