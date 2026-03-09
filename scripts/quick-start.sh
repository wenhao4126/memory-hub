#!/bin/bash
# ============================================================
# 多智能体记忆中枢 - 傻瓜式一键启动脚本
# ============================================================
# 专为新手设计，自动处理 Docker 权限和环境问题
# 作者：小码
# 日期：2026-03-06
# ============================================================

# 遇到错误立即退出
set -e

# ============================================================
# 颜色定义
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================================
# 全局变量
# ============================================================
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_CMD="docker"
COMPOSE_CMD="docker-compose"
NEED_SUDO=false

# ============================================================
# 打印函数
# ============================================================
print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║      🚀 多智能体记忆中枢 - 一键启动脚本             ║${NC}"
    echo -e "${BOLD}${CYAN}║         (专为新手设计，有问题随时问！)              ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_info() { echo -e "${BLUE}ℹ️  ${NC}$1"; }
print_success() { echo -e "${GREEN}✅ ${NC}$1"; }
print_warning() { echo -e "${YELLOW}⚠️  ${NC}$1"; }
print_error() { echo -e "${RED}❌ ${NC}$1"; }
print_step() { echo -e "${CYAN}👉 ${NC}$1"; }
print_tip() { echo -e "${GREEN}💡 提示: ${NC}$1"; }

# ============================================================
# 1. 检查 Docker 是否安装
# ============================================================
check_docker_installed() {
    print_info "检查 Docker 是否安装..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        echo ""
        echo -e "${YELLOW}请按照以下步骤安装 Docker:${NC}"
        echo ""
        echo "  Ubuntu/Debian:"
        echo "    curl -fsSL https://get.docker.com | sh"
        echo "    sudo usermod -aG docker \$USER"
        echo ""
        echo "  macOS:"
        echo "    brew install --cask docker"
        echo "    # 然后启动 Docker Desktop 应用"
        echo ""
        echo "  Windows:"
        echo "    # 下载并安装 Docker Desktop"
        echo "    # https://www.docker.com/products/docker-desktop"
        echo ""
        echo "安装完成后，请重新运行此脚本。"
        exit 1
    fi
    
    print_success "Docker 已安装: $(docker --version)"
}

# ============================================================
# 2. 检查 Docker Compose 是否可用
# ============================================================
check_docker_compose() {
    print_info "检查 Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose 已安装: $(docker compose version)"
    else
        print_error "Docker Compose 未安装"
        echo ""
        echo -e "${YELLOW}请安装 Docker Compose:${NC}"
        echo "  Ubuntu/Debian: sudo apt-get install docker-compose-plugin"
        echo "  或访问: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# ============================================================
# 3. 检查 Docker 权限
# ============================================================
check_docker_permission() {
    print_info "检查 Docker 权限..."
    
    # 尝试运行一个简单的 docker 命令
    if docker ps &> /dev/null; then
        print_success "Docker 权限正常"
        NEED_SUDO=false
        DOCKER_CMD="docker"
        return 0
    fi
    
    # 权限不足，检查是否在 docker 组
    if groups | grep -q docker; then
        # 在 docker 组但仍无权限，可能需要重新登录
        print_warning "您已在 docker 组，但权限未生效"
        echo ""
        echo -e "${YELLOW}请执行以下命令后重试:${NC}"
        echo "  newgrp docker"
        echo ""
        echo "或重新登录系统。"
        exit 1
    fi
    
    # 不在 docker 组
    print_warning "检测到 Docker 权限不足"
    echo ""
    echo -e "${YELLOW}解决方案（推荐方案1）:${NC}"
    echo ""
    echo "  方案 1: 加入 docker 组（推荐，一次设置永久有效）"
    echo "    sudo usermod -aG docker \$USER"
    echo "    newgrp docker  # 或重新登录"
    echo "    然后重新运行此脚本"
    echo ""
    echo "  方案 2: 使用 sudo 运行此脚本"
    echo "    sudo ./scripts/quick-start.sh"
    echo ""
    
    # 询问用户选择
    read -p "是否使用 sudo 继续运行？(y/n): " choice
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        print_info "将使用 sudo 运行 Docker 命令"
        NEED_SUDO=true
        DOCKER_CMD="sudo docker"
        COMPOSE_CMD="sudo docker-compose"
        print_success "已配置使用 sudo"
    else
        print_info "已取消，请先解决权限问题后重试"
        exit 1
    fi
}

# ============================================================
# 4. 检查 .env 文件
# ============================================================
check_env_file() {
    print_info "检查环境变量配置..."
    cd "$PROJECT_ROOT"
    
    if [ ! -f .env ]; then
        print_warning ".env 文件不存在"
        print_step "从模板创建 .env 文件..."
        cp .env.example .env
        print_success ".env 文件已创建"
        print_tip "您可以编辑 .env 文件修改数据库密码等配置"
    else
        print_success ".env 文件已存在"
    fi
}

# ============================================================
# 5. 检查端口占用
# ============================================================
check_ports() {
    print_info "检查端口占用..."
    
    local ports_in_use=()
    local ports=(5432 8000 5050)
    local port_names=("数据库" "API" "pgAdmin")
    
    for i in "${!ports[@]}"; do
        local port="${ports[$i]}"
        local name="${port_names[$i]}"
        
        if $DOCKER_CMD ps --format '{{.Ports}}' 2>/dev/null | grep -q ":$port->"; then
            # 被 Docker 容器占用，跳过
            continue
        elif netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            # 被其他进程占用
            local process=$(lsof -i :$port 2>/dev/null | tail -1 | awk '{print $1}' || echo "未知进程")
            ports_in_use+=("$port ($name) - 被 $process 占用")
        fi
    done
    
    if [ ${#ports_in_use[@]} -gt 0 ]; then
        print_warning "检测到端口占用:"
        for port_info in "${ports_in_use[@]}"; do
            echo "  - $port_info"
        done
        echo ""
        echo -e "${YELLOW}解决方法:${NC}"
        echo "  1. 停止占用端口的进程"
        echo "  2. 或修改 .env 文件中的端口配置"
        echo ""
        read -p "是否继续启动？(y/n): " choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "端口检查通过"
    fi
}

# ============================================================
# 6. 拉取 Docker 镜像
# ============================================================
pull_images() {
    print_info "拉取 Docker 镜像..."
    
    # 获取需要的镜像列表
    local images=(
        "pgvector/pgvector:pg16"
        "dpage/pgadmin4:latest"
    )
    
    for image in "${images[@]}"; do
        print_step "拉取镜像: $image"
        if $DOCKER_CMD pull "$image"; then
            print_success "镜像拉取成功: $image"
        else
            print_warning "镜像拉取失败: $image"
            print_tip "可能是网络问题，尝试使用镜像加速器"
            echo "  国内镜像加速器设置: https://yeasy.gitbook.io/docker_practice/install/mirror"
        fi
    done
    
    # 构建本地镜像
    print_step "构建 API 服务镜像..."
    if $COMPOSE_CMD build; then
        print_success "API 镜像构建成功"
    else
        print_error "API 镜像构建失败"
        exit 1
    fi
}

# ============================================================
# 7. 启动服务
# ============================================================
start_services() {
    print_header
    print_info "正在启动服务..."
    cd "$PROJECT_ROOT"
    
    # 检查环境
    check_docker_installed
    check_docker_compose
    check_docker_permission
    check_env_file
    check_ports
    
    echo ""
    print_info "拉取/构建镜像..."
    pull_images
    
    echo ""
    print_info "启动 Docker 容器..."
    if $COMPOSE_CMD up -d; then
        print_success "容器启动成功"
    else
        print_error "容器启动失败"
        echo ""
        echo "查看日志: $COMPOSE_CMD logs"
        exit 1
    fi
    
    echo ""
    print_info "等待服务就绪..."
    
    # 等待数据库
    print_step "等待数据库启动..."
    for i in {1..30}; do
        if $DOCKER_CMD exec memory-hub-db pg_isready -U memory_user -d memory_hub &> /dev/null 2>&1; then
            print_success "数据库已就绪"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    
    # 等待 API
    print_step "等待 API 启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v1/health &> /dev/null; then
            print_success "API 已就绪"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    
    # 显示服务地址
    show_service_info
}

# ============================================================
# 8. 停止服务
# ============================================================
stop_services() {
    print_info "停止所有服务..."
    cd "$PROJECT_ROOT"
    
    if $COMPOSE_CMD down; then
        print_success "服务已停止"
    else
        print_warning "停止服务时遇到问题"
    fi
}

# ============================================================
# 9. 重启服务
# ============================================================
restart_services() {
    print_info "重启所有服务..."
    stop_services
    echo ""
    start_services
}

# ============================================================
# 10. 查看服务状态
# ============================================================
show_status() {
    print_header
    print_info "服务状态:"
    echo ""
    cd "$PROJECT_ROOT"
    
    $COMPOSE_CMD ps
    
    echo ""
    # 检查 API 健康状态
    if curl -s http://localhost:8000/api/v1/health &> /dev/null; then
        print_success "API 健康检查: 正常"
    else
        print_warning "API 健康检查: 无法连接"
    fi
}

# ============================================================
# 11. 查看日志
# ============================================================
show_logs() {
    print_info "查看实时日志 (按 Ctrl+C 退出)..."
    cd "$PROJECT_ROOT"
    $COMPOSE_CMD logs -f
}

# ============================================================
# 12. 清理数据
# ============================================================
clean_data() {
    print_warning "⚠️  这将删除所有数据（包括数据库）！此操作不可逆！"
    echo ""
    echo -e "${RED}警告：所有记忆数据将被永久删除！${NC}"
    echo ""
    read -p "确定要继续吗？请输入 'DELETE' 确认: " confirm
    
    if [ "$confirm" != "DELETE" ]; then
        print_info "操作已取消"
        return
    fi
    
    cd "$PROJECT_ROOT"
    print_info "停止服务并清理数据..."
    
    $COMPOSE_CMD down -v
    $DOCKER_CMD volume prune -f 2>/dev/null || true
    
    print_success "数据已清理"
}

# ============================================================
# 13. 显示服务信息
# ============================================================
show_service_info() {
    echo ""
    echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║          🎉 服务启动成功！                    ║${NC}"
    echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}${GREEN}║  📚 API 文档:  http://localhost:8000/docs    ║${NC}"
    echo -e "${BOLD}${GREEN}║  🔌 API 接口:  http://localhost:8000/api/v1  ║${NC}"
    echo -e "${BOLD}${GREEN}║  🗄️  数据库:    localhost:5432              ║${NC}"
    echo -e "${BOLD}${GREEN}║  🛠️  pgAdmin:   http://localhost:5050        ║${NC}"
    echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}${GREEN}║  📧 pgAdmin 登录:                            ║${NC}"
    echo -e "${BOLD}${GREEN}║     邮箱: admin@memory.hub                  ║${NC}"
    echo -e "${BOLD}${GREEN}║     密码: admin123                           ║${NC}"
    echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}快速测试:${NC}"
    echo "  curl http://localhost:8000/api/v1/health"
    echo ""
}

# ============================================================
# 14. 交互式菜单
# ============================================================
show_menu() {
    print_header
    
    echo -e "${BOLD}请选择操作:${NC}"
    echo ""
    echo "  1) 🚀 启动所有服务"
    echo "  2) 🛑 停止所有服务"
    echo "  3) 🔄 重启所有服务"
    echo "  4) 📊 查看服务状态"
    echo "  5) 📝 查看日志"
    echo "  6) 🗑️  清理数据（危险！）"
    echo "  7) 🚪 退出"
    echo ""
    
    read -p "请输入选项 [1-7]: " choice
    echo ""
    
    case $choice in
        1)
            start_services
            ;;
        2)
            stop_services
            ;;
        3)
            restart_services
            ;;
        4)
            show_status
            ;;
        5)
            show_logs
            ;;
        6)
            clean_data
            ;;
        7)
            print_info "再见！"
            exit 0
            ;;
        *)
            print_error "无效选项，请重新选择"
            show_menu
            ;;
    esac
}

# ============================================================
# 15. 命令行参数处理
# ============================================================
# 如果有命令行参数，直接执行对应命令
if [ $# -gt 0 ]; then
    case "$1" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        clean)
            clean_data
            ;;
        help|--help|-h)
            print_header
            echo "用法: $0 [命令]"
            echo ""
            echo "命令:"
            echo "  start     启动所有服务"
            echo "  stop      停止所有服务"
            echo "  restart   重启所有服务"
            echo "  status    查看服务状态"
            echo "  logs      查看日志"
            echo "  clean     清理数据（危险）"
            echo "  help      显示帮助"
            echo ""
            echo "不带参数运行将进入交互式菜单"
            echo ""
            ;;
        *)
            print_error "未知命令: $1"
            echo "运行 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
else
    # 无参数，进入交互式菜单
    show_menu
fi