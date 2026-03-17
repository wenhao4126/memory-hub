#!/bin/bash
# ============================================================
# 迁移脚本：MEMORY.md → Memory Hub
# ============================================================
# 功能：将 OpenClaw 的 MEMORY.md 内容迁移到 Memory Hub 数据库
# 用法：./migrate-memory-md-to-hub.sh [--dry-run] [--agent-name "傻妞"]
# 作者：小码
# 日期：2026-03-17
# ============================================================

set -e

# 配置
MEMORY_HUB_API="${MEMORY_HUB_API:-http://localhost:8000/api/v1}"
DATA_DIR="$(dirname "$0")/../data"
REGISTRY_FILE="$DATA_DIR/agent-registry.json"

# 默认参数
DRY_RUN="false"
AGENT_NAME="傻妞"
MEMORY_MD="$HOME/.openclaw/workspace/MEMORY.md"
BACKUP_DIR="$HOME/.openclaw/workspace/memory-backup"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ============================================================
# 辅助函数
# ============================================================

print_header() {
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  📦 MEMORY.md → Memory Hub 迁移脚本${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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

print_section() {
    echo ""
    echo -e "${CYAN}━━━ $1 ━━━${NC}"
}

# 获取智能体 ID
get_agent_id() {
    local name="$1"
    
    # 从本地注册表获取
    if [ -f "$REGISTRY_FILE" ]; then
        local id=$(jq -r ".\"$name\"" "$REGISTRY_FILE" 2>/dev/null)
        if [ -n "$id" ] && [ "$id" != "null" ]; then
            echo "$id"
            return 0
        fi
    fi
    
    return 1
}

# 检测记忆类型
detect_memory_type() {
    local content="$1"
    local type="experience"  # 默认类型
    
    # 根据关键词判断类型
    if [[ "$content" =~ (喜欢|讨厌|偏好|习惯|风格|要求) ]]; then
        type="preference"
    elif [[ "$content" =~ (职责|专长|能力|擅长|可以|会) ]]; then
        type="skill"
    elif [[ "$content" =~ (是|叫|在|住|等于|配置|地址|ID|密钥) ]]; then
        type="fact"
    fi
    
    echo "$type"
}

# 估算重要性
estimate_importance() {
    local content="$1"
    local importance=0.7  # 默认重要性
    
    # 根据关键词调整重要性
    if [[ "$content" =~ (重要|必须|红线|禁止|核心|关键) ]]; then
        importance=0.9
    elif [[ "$content" =~ (踩坑|问题|错误|失败|教训) ]]; then
        importance=0.85
    elif [[ "$content" =~ (配置|设置|安装|更新) ]]; then
        importance=0.75
    fi
    
    echo "$importance"
}

# 存储记忆到 Memory Hub
store_memory() {
    local agent_id="$1"
    local content="$2"
    local memory_type="$3"
    local importance="$4"
    local tags="$5"
    
    # 转义内容中的特殊字符
    local escaped_content=$(echo "$content" | sed 's/"/\\"/g' | tr '\n' ' ')
    
    # 构建请求
    local request=$(cat <<EOF
{
    "agent_id": "$agent_id",
    "content": "$escaped_content",
    "memory_type": "$memory_type",
    "importance": $importance,
    "tags": $tags,
    "auto_route": true
}
EOF
)
    
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} 将存储: $memory_type ($importance)"
        echo "内容: ${content:0:80}..."
        return 0
    fi
    
    # 调用 Memory Hub API
    local response=$(curl -s -X POST "$MEMORY_HUB_API/memories" \
        -H "Content-Type: application/json" \
        -d "$request" 2>&1)
    
    if echo "$response" | grep -q "成功"; then
        return 0
    else
        echo -e "${RED}存储失败: $response${NC}"
        return 1
    fi
}

# ============================================================
# 主流程
# ============================================================

main() {
    print_header
    echo ""
    
    # 解析参数
    while [ $# -gt 0 ]; do
        case "$1" in
            --dry-run|-d)
                DRY_RUN="true"
                shift
                ;;
            --agent-name|-a)
                AGENT_NAME="$2"
                shift 2
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --dry-run, -d          预览模式，不实际存储"
                echo "  --agent-name, -a NAME  指定智能体名称（默认：傻妞）"
                echo "  --help, -h             显示帮助信息"
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 显示配置
    print_info "智能体: $AGENT_NAME"
    print_info "源文件: $MEMORY_MD"
    print_info "Memory Hub API: $MEMORY_HUB_API"
    print_info "模式: $([ "$DRY_RUN" = "true" ] && echo "预览" || echo "执行")"
    echo ""
    
    # 检查源文件
    if [ ! -f "$MEMORY_MD" ]; then
        print_error "MEMORY.md 文件不存在: $MEMORY_MD"
        exit 1
    fi
    print_success "源文件存在"
    
    # 获取智能体 ID
    AGENT_ID=$(get_agent_id "$AGENT_NAME")
    if [ -z "$AGENT_ID" ] || [ "$AGENT_ID" == "null" ]; then
        print_error "未找到智能体 '$AGENT_NAME' 的注册信息"
        print_info "请先运行注册脚本: /home/wen/projects/memory-hub/scripts/register-agent.sh"
        exit 1
    fi
    print_success "智能体 ID: $AGENT_ID"
    
    # 检查 Memory Hub API
    if ! curl -s -f "$MEMORY_HUB_API/health" > /dev/null 2>&1; then
        print_error "Memory Hub API 不可用"
        print_info "请先启动: cd /home/wen/projects/memory-hub && ./scripts/start.sh start"
        exit 1
    fi
    print_success "Memory Hub API 可用"
    
    # 备份原文件
    if [ "$DRY_RUN" = "false" ]; then
        mkdir -p "$BACKUP_DIR"
        BACKUP_FILE="$BACKUP_DIR/MEMORY.md.$(date +%Y%m%d_%H%M%S).bak"
        cp "$MEMORY_MD" "$BACKUP_FILE"
        print_success "已备份到: $BACKUP_FILE"
    fi
    
    echo ""
    print_section "解析 MEMORY.md"
    
    # 读取并解析 MEMORY.md
    local total_count=0
    local success_count=0
    local fail_count=0
    local current_section=""
    local current_content=""
    
    # 按段落解析
    while IFS= read -r line; do
        # 检测标题
        if [[ "$line" =~ ^##\ (.+) ]]; then
            # 保存上一个段落
            if [ -n "$current_content" ] && [ ${#current_content} -gt 50 ]; then
                ((total_count++))
                
                # 检测记忆类型和重要性
                MEMORY_TYPE=$(detect_memory_type "$current_content")
                IMPORTANCE=$(estimate_importance "$current_content")
                
                # 生成标签
                TAGS=$(echo "$current_section 迁移 2026-03-17" | tr ' ' '\n' | grep -v '^$' | jq -R . | jq -s .)
                
                print_info "[$total_count] 类型: $MEMORY_TYPE, 重要性: $IMPORTANCE"
                
                if store_memory "$AGENT_ID" "$current_content" "$MEMORY_TYPE" "$IMPORTANCE" "$TAGS"; then
                    ((success_count++))
                else
                    ((fail_count++))
                fi
            fi
            
            # 开始新段落
            current_section="${BASH_REMATCH[1]}"
            current_content=""
        else
            # 累积内容（跳过空行和分隔线）
            if [ -n "$line" ] && [[ ! "$line" =~ ^---+$ ]]; then
                current_content="$current_content $line"
            fi
        fi
    done < "$MEMORY_MD"
    
    # 处理最后一个段落
    if [ -n "$current_content" ] && [ ${#current_content} -gt 50 ]; then
        ((total_count++))
        
        MEMORY_TYPE=$(detect_memory_type "$current_content")
        IMPORTANCE=$(estimate_importance "$current_content")
        TAGS=$(echo "$current_section 迁移 2026-03-17" | tr ' ' '\n' | grep -v '^$' | jq -R . | jq -s .)
        
        print_info "[$total_count] 类型: $MEMORY_TYPE, 重要性: $IMPORTANCE"
        
        if store_memory "$AGENT_ID" "$current_content" "$MEMORY_TYPE" "$IMPORTANCE" "$TAGS"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    fi
    
    # 汇总
    echo ""
    print_section "迁移结果"
    print_info "总计: $total_count 条记忆"
    print_success "成功: $success_count"
    [ $fail_count -gt 0 ] && print_error "失败: $fail_count"
    
    if [ "$DRY_RUN" = "false" ]; then
        echo ""
        print_success "迁移完成！"
        print_info "原文件已备份到: $BACKUP_DIR/"
        print_info "原文件保留作为历史记录，但不再更新"
        print_warning "请更新 AGENTS.md 和相关文档，说明不再使用 MEMORY.md"
    fi
}

main "$@"