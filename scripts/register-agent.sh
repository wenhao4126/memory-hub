#!/bin/bash
# ============================================================
# 智能体注册脚本
# ============================================================
# 功能：将所有智能体（傻妞和 8 个手下）注册到 Memory Hub
# 用法：./register-agent.sh [--force] [--list]
# 作者：小码
# 日期：2026-03-17
# ============================================================

set -e

# 配置
MEMORY_HUB_API="${MEMORY_HUB_API:-http://localhost:8000/api/v1}"
DATA_DIR="$(dirname "$0")/../data"
REGISTRY_FILE="$DATA_DIR/agent-registry.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# 智能体配置
# ============================================================

# 8 个手下 + 傻妞的配置
declare -A AGENTS=(
    # 傻妞 - CEO 和总管家
    ["傻妞"]="{
        \"name\": \"傻妞\",
        \"description\": \"CEO 和总管家，负责理解需求、拆解任务、派发手下、质量把关\",
        \"capabilities\": [\"任务拆解\", \"派发\", \"审核\", \"沟通\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace/\",
            \"agent_id\": \"team-shaniu\",
            \"role\": \"manager\",
            \"emoji\": \"💜\"
        }
    }"
    # 小搜 - 信息采集专家
    ["小搜"]="{
        \"name\": \"小搜\",
        \"description\": \"信息采集专家，擅长搜索信息、调研、收集资料\",
        \"capabilities\": [\"搜索\", \"调研\", \"收集\", \"信息整理\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace-team-researcher/\",
            \"agent_id\": \"team-researcher\",
            \"role\": \"worker\",
            \"emoji\": \"🟢\"
        }
    }"
    # 小写 - 文案撰写专家
    ["小写"]="{
        \"name\": \"小写\",
        \"description\": \"文案撰写专家，擅长写文案、翻译、总结、报告\",
        \"capabilities\": [\"写作\", \"翻译\", \"总结\", \"润色\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace-team-writer/\",
            \"agent_id\": \"team-writer\",
            \"role\": \"worker\",
            \"emoji\": \"🟢\"
        }
    }"
    # 小码 - 代码开发专家
    ["小码"]="{
        \"name\": \"小码\",
        \"description\": \"代码开发专家，擅长写代码、脚本、自动化、系统集成\",
        \"capabilities\": [\"编程\", \"脚本\", \"自动化\", \"集成\", \"调试\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace-team-coder/\",
            \"agent_id\": \"team-coder\",
            \"role\": \"worker\",
            \"emoji\": \"🟡\"
        }
    }"
    # 小审 - 质量审核专家
    ["小审"]="{
        \"name\": \"小审\",
        \"description\": \"质量审核专家，擅长审核代码、文案、输出质量\",
        \"capabilities\": [\"审核\", \"代码审查\", \"文案审查\", \"质量把关\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace-team-reviewer/\",
            \"agent_id\": \"team-reviewer\",
            \"role\": \"worker\",
            \"emoji\": \"🔴\"
        }
    }"
    # 小析 - 数据分析专家
    ["小析"]="{
        \"name\": \"小析\",
        \"description\": \"数据分析专家，擅长数据分析、洞察、排序筛选\",
        \"capabilities\": [\"数据分析\", \"可视化\", \"洞察\", \"报表\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace-team-analyst/\",
            \"agent_id\": \"team-analyst\",
            \"role\": \"worker\",
            \"emoji\": \"🟡\"
        }
    }"
    # 小览 - 浏览器操作专家
    ["小览"]="{
        \"name\": \"小览\",
        \"description\": \"浏览器操作专家，擅长处理动态网页、需登录的网站\",
        \"capabilities\": [\"浏览器\", \"自动化\", \"网页交互\", \"截图\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace-team-browser/\",
            \"agent_id\": \"team-browser\",
            \"role\": \"worker\",
            \"emoji\": \"🟡\"
        }
    }"
    # 小图 - 视觉设计专家
    ["小图"]="{
        \"name\": \"小图\",
        \"description\": \"视觉设计专家，擅长生成图片、设计、配图\",
        \"capabilities\": [\"图片生成\", \"设计\", \"配图\", \"视觉优化\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace-team-designer/\",
            \"agent_id\": \"team-designer\",
            \"role\": \"worker\",
            \"emoji\": \"🎨\"
        }
    }"
    # 小排 - 内容排版专家
    ["小排"]="{
        \"name\": \"小排\",
        \"description\": \"内容排版专家，擅长排版、幻灯片、信息图\",
        \"capabilities\": [\"排版\", \"幻灯片\", \"信息图\", \"布局\"],
        \"metadata\": {
            \"workspace\": \"$HOME/.openclaw/workspace-team-layout/\",
            \"agent_id\": \"team-layout\",
            \"role\": \"worker\",
            \"emoji\": \"📐\"
        }
    }"
)

# ============================================================
# 辅助函数
# ============================================================

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  Memory Hub - 智能体注册系统${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 检查 Memory Hub API 是否可用
check_api() {
    print_info "检查 Memory Hub API 连接..."
    if curl -s -f "$MEMORY_HUB_API/health" > /dev/null 2>&1; then
        print_success "Memory Hub API 可用"
        return 0
    else
        print_error "Memory Hub API 不可用: $MEMORY_HUB_API"
        print_info "请先启动 Memory Hub: cd /home/wen/projects/memory-hub && ./scripts/start.sh start"
        return 1
    fi
}

# 注册单个智能体
register_agent() {
    local name="$1"
    local config="$2"
    local force="${3:-false}"
    
    # 检查是否已注册
    local existing_id=$(cat "$REGISTRY_FILE" 2>/dev/null | jq -r ".\"$name\"" 2>/dev/null)
    
    if [ "$existing_id" != "null" ] && [ -n "$existing_id" ] && [ "$force" != "true" ]; then
        print_warning "$name 已注册 (ID: $existing_id)，跳过。使用 --force 重新注册。"
        return 0
    fi
    
    # 发送注册请求
    print_info "注册智能体: $name"
    
    local response=$(curl -s -X POST "$MEMORY_HUB_API/agents" \
        -H "Content-Type: application/json" \
        -d "$config" 2>&1)
    
    # 解析响应
    if echo "$response" | grep -q "成功"; then
        local agent_id=$(echo "$response" | grep -oP 'ID: \K[0-9a-f-]+')
        print_success "$name 注册成功 (ID: $agent_id)"
        
        # 保存到注册表
        mkdir -p "$DATA_DIR"
        if [ ! -f "$REGISTRY_FILE" ]; then
            echo "{}" > "$REGISTRY_FILE"
        fi
        local tmp=$(mktemp)
        jq ". + {\"$name\": \"$agent_id\"}" "$REGISTRY_FILE" > "$tmp" && mv "$tmp" "$REGISTRY_FILE"
        
        return 0
    else
        print_error "$name 注册失败: $response"
        return 1
    fi
}

# 列出已注册的智能体
list_agents() {
    print_info "从 Memory Hub 获取智能体列表..."
    echo ""
    
    local response=$(curl -s "$MEMORY_HUB_API/agents?limit=20")
    
    if [ -z "$response" ] || [ "$response" == "[]" ]; then
        print_warning "暂无已注册的智能体"
        return 0
    fi
    
    echo "$response" | jq -r '.[] | "  \(.name) (\(.id)) - \(.description[0:50])..."' 2>/dev/null || \
        echo "$response"
}

# 显示本地注册表
show_registry() {
    if [ ! -f "$REGISTRY_FILE" ]; then
        print_warning "本地注册表不存在: $REGISTRY_FILE"
        return 0
    fi
    
    echo ""
    print_info "本地注册表内容:"
    cat "$REGISTRY_FILE" | jq '.' 2>/dev/null || cat "$REGISTRY_FILE"
}

# ============================================================
# 主函数
# ============================================================

main() {
    print_header
    
    # 解析参数
    local force="false"
    local list_only="false"
    local show_reg="false"
    
    while [ $# -gt 0 ]; do
        case "$1" in
            --force|-f)
                force="true"
                shift
                ;;
            --list|-l)
                list_only="true"
                shift
                ;;
            --registry|-r)
                show_reg="true"
                shift
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --force, -f    强制重新注册已存在的智能体"
                echo "  --list, -l     仅列出已注册的智能体"
                echo "  --registry, -r 显示本地注册表内容"
                echo "  --help, -h     显示帮助信息"
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 仅列出模式
    if [ "$list_only" == "true" ]; then
        list_agents
        exit 0
    fi
    
    # 显示注册表模式
    if [ "$show_reg" == "true" ]; then
        show_registry
        exit 0
    fi
    
    # 检查 API
    if ! check_api; then
        exit 1
    fi
    
    # 注册所有智能体
    echo ""
    print_info "开始注册智能体..."
    echo ""
    
    local success_count=0
    local fail_count=0
    
    for name in "${!AGENTS[@]}"; do
        if register_agent "$name" "${AGENTS[$name]}" "$force"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
        echo ""
    done
    
    # 汇总
    echo -e "${BLUE}============================================================${NC}"
    print_info "注册完成: ${GREEN}成功 $success_count${NC} / ${RED}失败 $fail_count${NC}"
    echo -e "${BLUE}============================================================${NC}"
    
    # 显示注册表
    show_registry
    
    exit $fail_count
}

main "$@"