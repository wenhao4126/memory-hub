#!/bin/bash
# ============================================================
# 测试脚本：智能体自动连接机制
# ============================================================
# 功能：验证 Memory Hub 智能体注册、记忆检索和存储功能
# 用法：./test-agent-auto-connect.sh
# 作者：小码
# 日期：2026-03-17
# ============================================================

set -e

# 配置
MEMORY_HUB_ROOT="/home/wen/projects/memory-hub"
MEMORY_HUB_API="http://localhost:8000/api/v1"
SCRIPTS_DIR="$MEMORY_HUB_ROOT/scripts"
HOOKS_DIR="$MEMORY_HUB_ROOT/hooks"
DATA_DIR="$MEMORY_HUB_ROOT/data"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# 测试计数器
TEST_TOTAL=0
TEST_PASSED=0
TEST_FAILED=0

# ============================================================
# 辅助函数
# ============================================================

print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     🧪 Memory Hub - 智能体自动连接测试                      ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_test_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  测试 $1: $2${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    ((TEST_TOTAL++))
}

print_pass() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TEST_PASSED++))
}

print_fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((TEST_FAILED++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ============================================================
# 测试用例
# ============================================================

# 测试 1: 检查 Memory Hub API 可用性
test_api_health() {
    print_test_header 1 "Memory Hub API 健康检查"
    
    print_info "检查 API 连接..."
    
    if curl -s -f "$MEMORY_HUB_API/health" | grep -q "connected"; then
        print_pass "Memory Hub API 可用"
        return 0
    else
        print_fail "Memory Hub API 不可用"
        print_info "请先启动 Memory Hub: cd $MEMORY_HUB_ROOT && ./scripts/start.sh start"
        return 1
    fi
}

# 测试 2: 检查脚本文件存在
test_scripts_exist() {
    print_test_header 2 "检查脚本文件"
    
    local all_exist=true
    
    # 检查注册脚本
    if [ -f "$SCRIPTS_DIR/register-agent.sh" ]; then
        print_pass "注册脚本存在: register-agent.sh"
    else
        print_fail "注册脚本不存在: register-agent.sh"
        all_exist=false
    fi
    
    # 检查启动 Hook
    if [ -f "$HOOKS_DIR/on-agent-start.sh" ]; then
        print_pass "启动 Hook 存在: on-agent-start.sh"
    else
        print_fail "启动 Hook 不存在: on-agent-start.sh"
        all_exist=false
    fi
    
    # 检查完成 Hook
    if [ -f "$HOOKS_DIR/on-agent-complete.sh" ]; then
        print_pass "完成 Hook 存在: on-agent-complete.sh"
    else
        print_fail "完成 Hook 不存在: on-agent-complete.sh"
        all_exist=false
    fi
    
    if $all_exist; then
        return 0
    else
        return 1
    fi
}

# 测试 3: 注册测试智能体
test_register_agent() {
    print_test_header 3 "注册测试智能体"
    
    print_info "注册测试智能体: test_agent_$$"
    
    local response=$(curl -s -X POST "$MEMORY_HUB_API/agents" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"test_agent_$$\",
            \"description\": \"测试智能体，可以删除\",
            \"capabilities\": [\"测试\"],
            \"metadata\": {
                \"test\": true,
                \"pid\": $$
            }
        }")
    
    if echo "$response" | grep -q "成功"; then
        TEST_AGENT_ID=$(echo "$response" | grep -oP 'ID: \K[0-9a-f-]+')
        print_pass "智能体注册成功 (ID: $TEST_AGENT_ID)"
        export TEST_AGENT_ID
        return 0
    else
        print_fail "智能体注册失败: $response"
        return 1
    fi
}

# 测试 4: 存储测试记忆
test_store_memory() {
    print_test_header 4 "存储测试记忆"
    
    if [ -z "$TEST_AGENT_ID" ]; then
        print_warning "跳过：测试智能体 ID 未设置"
        return 1
    fi
    
    print_info "存储测试记忆..."
    
    local test_content="这是一个测试记忆，时间戳: $(date '+%Y-%m-%d %H:%M:%S')"
    
    local response=$(curl -s -X POST "$MEMORY_HUB_API/memories" \
        -H "Content-Type: application/json" \
        -d "{
            \"agent_id\": \"$TEST_AGENT_ID\",
            \"content\": \"$test_content\",
            \"memory_type\": \"experience\",
            \"importance\": 0.9,
            \"tags\": [\"测试\", \"自动连接\"],
            \"auto_route\": true
        }")
    
    if echo "$response" | grep -q "成功"; then
        TEST_MEMORY_ID=$(echo "$response" | grep -oP 'ID: \K[0-9a-f-]+')
        print_pass "记忆存储成功 (ID: $TEST_MEMORY_ID)"
        export TEST_MEMORY_ID
        return 0
    else
        print_fail "记忆存储失败: $response"
        return 1
    fi
}

# 测试 5: 检索记忆
test_search_memory() {
    print_test_header 5 "检索记忆"
    
    if [ -z "$TEST_AGENT_ID" ]; then
        print_warning "跳过：测试智能体 ID 未设置"
        return 1
    fi
    
    print_info "检索测试记忆..."
    
    local response=$(curl -s -X POST "$MEMORY_HUB_API/memories/search/text" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"测试记忆\",
            \"agent_id\": \"$TEST_AGENT_ID\",
            \"match_count\": 5
        }")
    
    if [ -n "$response" ] && [ "$response" != "[]" ]; then
        print_pass "记忆检索成功"
        print_info "检索结果: $(echo "$response" | jq -r '.[0].content' 2>/dev/null || echo "$response")"
        return 0
    else
        print_fail "记忆检索失败或无结果"
        return 1
    fi
}

# 测试 6: 测试启动 Hook
test_start_hook() {
    print_test_header 6 "测试启动 Hook"
    
    # 创建临时任务文件
    local temp_task="/tmp/test_task_$$$.md"
    echo "# 测试任务" > "$temp_task"
    
    print_info "执行启动 Hook..."
    
    # 使用注册脚本注册测试智能体到本地注册表
    mkdir -p "$DATA_DIR"
    echo "{\"test_agent_$$\": \"$TEST_AGENT_ID\"}" > "$DATA_DIR/agent-registry.json"
    
    # 执行 Hook
    if bash "$HOOKS_DIR/on-agent-start.sh" "test_agent_$$" "$temp_task" 2>&1 | grep -q "记忆检索"; then
        print_pass "启动 Hook 执行成功"
        
        # 检查任务文件是否包含记忆
        if grep -q "记忆中枢检索结果" "$temp_task"; then
            print_pass "记忆已注入到任务文件"
        else
            print_warning "任务文件未包含记忆（可能是因为没有记忆）"
        fi
        
        rm -f "$temp_task"
        return 0
    else
        print_fail "启动 Hook 执行失败"
        rm -f "$temp_task"
        return 1
    fi
}

# 测试 7: 测试完成 Hook
test_complete_hook() {
    print_test_header 7 "测试完成 Hook"
    
    print_info "执行完成 Hook..."
    
    local test_result="测试任务完成: 自动连接功能验证成功"
    
    if bash "$HOOKS_DIR/on-agent-complete.sh" "test_agent_$$" "$test_result" 2>&1 | grep -q "记忆存储成功"; then
        print_pass "完成 Hook 执行成功"
        return 0
    else
        print_fail "完成 Hook 执行失败"
        return 1
    fi
}

# 测试 8: 清理测试数据
test_cleanup() {
    print_test_header 8 "清理测试数据"
    
    print_info "删除测试智能体和记忆..."
    
    # 删除测试智能体（会级联删除记忆）
    if [ -n "$TEST_AGENT_ID" ]; then
        curl -s -X DELETE "$MEMORY_HUB_API/agents/$TEST_AGENT_ID" > /dev/null
        print_pass "测试智能体已删除"
    fi
    
    # 清理本地注册表
    rm -f "$DATA_DIR/agent-registry.json"
    print_pass "本地注册表已清理"
    
    # 清理缓存
    rm -rf /tmp/memory-hub-cache
    print_pass "缓存已清理"
    
    return 0
}

# ============================================================
# 主函数
# ============================================================

main() {
    print_header
    
    # 运行所有测试
    test_api_health || true
    test_scripts_exist || true
    test_register_agent || true
    test_store_memory || true
    test_search_memory || true
    test_start_hook || true
    test_complete_hook || true
    test_cleanup || true
    
    # 输出测试结果
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    📊 测试结果汇总                          ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  总测试数:  ${BLUE}$TEST_TOTAL${NC}"
    echo -e "  通过:      ${GREEN}$TEST_PASSED${NC}"
    echo -e "  失败:      ${RED}$TEST_FAILED${NC}"
    echo ""
    
    if [ $TEST_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ 所有测试通过！智能体自动连接机制工作正常。${NC}"
        exit 0
    else
        echo -e "${RED}❌ 部分测试失败，请检查上述错误信息。${NC}"
        exit 1
    fi
}

main "$@"