#!/bin/bash
# ============================================================
# 多智能体记忆中枢 - 一键启动脚本
# ============================================================
# 用法: ./scripts/start.sh [命令]
# 命令: start | stop | restart | status | logs | build | test | clean | help
# 作者：小码
# 日期：2026-03-06
# ============================================================

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
# 项目根目录
# ============================================================
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# ============================================================
# 打印函数
# ============================================================
print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║   多智能体记忆中枢 - 启动脚本               ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

print_info() { echo -e "${BLUE}ℹ ${NC}$1"; }
print_success() { echo -e "${GREEN}✓ ${NC}$1"; }
print_warning() { echo -e "${YELLOW}⚠ ${NC}$1"; }
print_error() { echo -e "${RED}✗ ${NC}$1"; }
print_step() { echo -e "${CYAN}→ ${NC}$1"; }

# ============================================================
# 显示帮助
# ============================================================
show_help() {
    print_header
    echo "用法: $0 [命令]"
    echo ""
    echo -e "${BOLD}命令:${NC}"
    echo "  start       启动所有服务（数据库 + API + 管理界面）"
    echo "  stop        停止所有服务"
    echo "  restart     重启所有服务"
    echo "  status      查看服务状态"
    echo "  logs        查看日志（实时）"
    echo "  build       构建 Docker 镜像"
    echo "  test        测试 API 连接"
    echo "  clean       清理所有数据（危险！）"
    echo "  help        显示帮助信息"
    echo ""
    echo -e "${BOLD}示例:${NC}"
    echo "  $0 start      # 一键启动"
    echo "  $0 logs       # 查看实时日志"
    echo "  $0 status     # 检查服务状态"
    echo "  $0 stop       # 停止服务"
    echo ""
    echo -e "${BOLD}服务地址:${NC}"
    echo "  - API 文档:  http://localhost:8000/docs"
    echo "  - API 接口:  http://localhost:8000/api/v1"
    echo "  - 数据库:    localhost:5432"
    echo "  - pgAdmin:   http://localhost:5050"
    echo ""
}

# ============================================================
# 检查依赖
# ============================================================
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装"
        exit 1
    fi
    
    print_success "依赖检查通过"
}

# ============================================================
# 检查环境变量
# ============================================================
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env 文件不存在，从模板创建..."
        cp .env.example .env
        print_success ".env 文件已创建"
    fi
}

# ============================================================
# 构建镜像
# ============================================================
build_images() {
    print_info "构建 Docker 镜像..."
    check_dependencies
    check_env
    
    docker-compose build --no-cache
    print_success "镜像构建完成"
}

# ============================================================
# 启动服务
# ============================================================
start_services() {
    print_header
    check_dependencies
    check_env
    
    print_info "启动多智能体记忆中枢..."
    echo ""
    
    # 启动所有服务
    print_step "启动 Docker 容器..."
    docker-compose up -d
    
    echo ""
    print_info "等待服务就绪..."
    sleep 5
    
    # 检查服务状态
    print_step "检查服务健康状态..."
    
    # 等待数据库
    for i in {1..30}; do
        if docker exec memory-hub-db pg_isready -U memory_user -d memory_hub &> /dev/null; then
            print_success "数据库已就绪"
            break
        fi
        sleep 1
    done
    
    # 等待 API
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v1/health &> /dev/null; then
            print_success "API 已就绪"
            break
        fi
        sleep 1
    done
    
    echo ""
    print_success "所有服务启动成功！"
    echo ""
    
    # 显示服务地址
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║              服务地址一览                    ║${NC}"
    echo -e "${BOLD}${CYAN}╠══════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}${CYAN}║  📚 API 文档:  http://localhost:8000/docs   ║${NC}"
    echo -e "${BOLD}${CYAN}║  🔌 API 接口:  http://localhost:8000/api/v1 ║${NC}"
    echo -e "${BOLD}${CYAN}║  🗄️  数据库:    localhost:5432               ║${NC}"
    echo -e "${BOLD}${CYAN}║  🛠️  pgAdmin:   http://localhost:5050        ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${BOLD}快速测试:${NC}"
    echo "  curl http://localhost:8000/api/v1/health"
    echo "  curl http://localhost:8000/"
    echo ""
}

# ============================================================
# 停止服务
# ============================================================
stop_services() {
    print_info "停止所有服务..."
    docker-compose down
    print_success "服务已停止"
}

# ============================================================
# 重启服务
# ============================================================
restart_services() {
    print_info "重启所有服务..."
    stop_services
    echo ""
    start_services
}

# ============================================================
# 查看状态
# ============================================================
show_status() {
    print_header
    print_info "服务状态："
    echo ""
    docker-compose ps
    echo ""
    
    # 检查 API 健康状态
    if curl -s http://localhost:8000/api/v1/health &> /dev/null; then
        print_success "API 健康检查: 正常"
    else
        print_warning "API 健康检查: 无法连接或异常"
    fi
}

# ============================================================
# 查看日志
# ============================================================
show_logs() {
    print_info "查看实时日志（Ctrl+C 退出）..."
    docker-compose logs -f
}

# ============================================================
# 测试 API
# ============================================================
test_api() {
    print_header
    print_info "测试 API 连接..."
    echo ""
    
    # 检查服务是否运行
    if ! docker-compose ps | grep -q "running"; then
        print_error "服务未运行，请先执行: $0 start"
        exit 1
    fi
    
    # 测试根路径
    print_step "测试根路径..."
    curl -s http://localhost:8000/ | jq . || curl -s http://localhost:8000/
    echo ""
    
    # 测试健康检查
    print_step "测试健康检查..."
    curl -s http://localhost:8000/api/v1/health | jq . || curl -s http://localhost:8000/api/v1/health
    echo ""
    
    # 测试数据库连接
    print_step "测试数据库连接..."
    docker exec -it memory-hub-db psql -U memory_user -d memory_hub -c "SELECT version();" | head -5
    echo ""
    
    print_success "API 测试完成"
}

# ============================================================
# 清理数据
# ============================================================
clean_data() {
    print_warning "⚠️  这将删除所有数据（包括数据库）！"
    echo ""
    read -p "确定要继续吗？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "操作已取消"
        exit 0
    fi
    
    print_info "停止服务并清理数据..."
    docker-compose down -v
    docker-compose rm -f
    docker volume prune -f
    
    print_success "数据已清理"
}

# ============================================================
# 主入口
# ============================================================
case "${1:-help}" in
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
    build)
        build_images
        ;;
    test)
        test_api
        ;;
    clean)
        clean_data
        ;;
    help|*)
        show_help
        ;;
esac