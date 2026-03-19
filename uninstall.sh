#!/bin/bash

# ============================================================
# Memory Hub 一键卸载脚本
# ============================================================
# 作者：小码 3 🟡
# 版本：1.0.0
# 日期：2026-03-19
#
# 用法：
#   bash uninstall.sh              # 交互式卸载
#   bash uninstall.sh --force      # 强制卸载，不确认
#   bash uninstall.sh --keep-data  # 保留数据卷
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# 默认配置
INSTALL_DIR="$HOME/memory-hub"
FORCE=false
KEEP_DATA=false

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${CYAN}${BOLD}==>${NC} ${BOLD}$1${NC}"
}

# 帮助信息
show_help() {
    cat << EOF
${BOLD}Memory Hub 一键卸载脚本${NC}

${CYAN}用法:${NC}
  $0 [选项]

${CYAN}选项:${NC}
  -h, --help          显示帮助信息
  -d, --dir <路径>    安装目录 (默认：~/memory-hub)
  -f, --force         强制卸载，不确认
  -k, --keep-data     保留数据卷
  -v, --verbose       详细输出模式

${CYAN}示例:${NC}
  # 交互式卸载
  $0

  # 强制卸载
  $0 --force

  # 保留数据卸载
  $0 --keep-data

EOF
}

# 解析参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -k|--keep-data)
                KEEP_DATA=true
                shift
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            *)
                log_error "未知选项：$1"
                exit 1
                ;;
        esac
    done
}

# 主函数
main() {
    echo -e "${RED}${BOLD}"
    cat << EOF
 __  __ _     _     _ _        _   _   _                 
|  \/  (_) __| | __| | | ___  | | | | | |_ __   ___ _ __ 
| |\/| | |/_\` |/ _\` | |/ _ \ | | | | | | '_ \ / _ \ '__|
| |  | | | (_| | (_| | |  __/ | | |_| | | |_) |  __/ |   
|_|  |_|_|\__,_|\__,_|_|\___| | | \___/|_| .__/ \___|_|   
                               |_|        |_|              
EOF
    echo -e "${NC}"
    echo -e "${RED}多智能体记忆中枢 - 一键卸载脚本${NC}"
    echo ""
    
    parse_args "$@"
    
    # 检查目录是否存在
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "安装目录不存在：$INSTALL_DIR"
        exit 1
    fi
    
    # 确认卸载
    if [ "$FORCE" = false ]; then
        echo -e "${RED}${BOLD}警告：此操作将删除 Memory Hub 的所有组件！${NC}"
        echo ""
        echo "安装目录：$INSTALL_DIR"
        echo ""
        
        if [ "$KEEP_DATA" = false ]; then
            echo -e "${YELLOW}注意：数据库数据卷也将被删除！${NC}"
            echo "如需保留数据，请使用 --keep-data 选项"
            echo ""
        fi
        
        echo -n "是否继续卸载？[y/N]: "
        read -r confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "卸载已取消"
            exit 0
        fi
        
        echo ""
        echo -n "再次确认：确定要删除所有数据吗？[y/N]: "
        read -r confirm2
        if [[ ! "$confirm2" =~ ^[Yy]$ ]]; then
            log_info "卸载已取消"
            exit 0
        fi
    fi
    
    cd "$INSTALL_DIR"
    
    # 停止服务
    log_step "停止 Docker 服务"
    if docker compose ps &> /dev/null 2>&1; then
        docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
        log_success "服务已停止"
    else
        log_warning "未发现运行中的服务"
    fi
    
    # 删除数据卷（如果未选择保留）
    if [ "$KEEP_DATA" = false ]; then
        log_step "删除数据卷"
        docker volume rm memory-hub_pgadmin_data 2>/dev/null || true
        log_success "数据卷已删除"
    else
        log_info "保留数据卷"
    fi
    
    # 删除安装目录
    log_step "删除安装目录"
    cd /
    rm -rf "$INSTALL_DIR"
    log_success "安装目录已删除"
    
    # 完成
    echo ""
    echo -e "${GREEN}${BOLD}========================================${NC}"
    echo -e "${GREEN}${BOLD}   Memory Hub 卸载完成！${NC}"
    echo -e "${GREEN}${BOLD}========================================${NC}"
    echo ""
    echo "已删除："
    echo "  - 所有 Docker 容器"
    if [ "$KEEP_DATA" = false ]; then
        echo "  - 数据卷（包括数据库数据）"
    else
        echo "  - 数据卷（已保留）"
    fi
    echo "  - 安装目录：$INSTALL_DIR"
    echo ""
    echo "如需重新安装，请运行："
    echo "  curl -fsSL https://raw.githubusercontent.com/wenhao4126/memory-hub/main/install.sh | bash"
    echo ""
}

main "$@"
