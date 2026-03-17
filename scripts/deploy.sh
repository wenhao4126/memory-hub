#!/bin/bash
# ============================================================
# 多智能体记忆中枢 - 生产环境部署脚本
# ============================================================
# 用法: ./scripts/deploy.sh [环境]
# 环境: dev | staging | prod
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
NC='\033[0m'

# ============================================================
# 项目根目录
# ============================================================
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# ============================================================
# 配置
# ============================================================
ENVIRONMENT="${1:-prod}"
COMPOSE_FILE="docker-compose.yml"

# 环境特定配置
case "$ENVIRONMENT" in
    dev)
        API_PORT=8000
        DB_PORT=5432
        ADMIN_PORT=5050
        ;;
    staging)
        API_PORT=8100
        DB_PORT=5433
        ADMIN_PORT=5051
        ;;
    prod)
        API_PORT=8000
        DB_PORT=5432
        ADMIN_PORT=5050
        ;;
    *)
        echo -e "${RED}错误: 未知环境 '$ENVIRONMENT'${NC}"
        echo "可用环境: dev, staging, prod"
        exit 1
        ;;
esac

# ============================================================
# 打印函数
# ============================================================
print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║   多智能体记忆中枢 - 生产部署               ║${NC}"
    echo -e "${BOLD}${CYAN}║   环境: ${ENVIRONMENT^^}                              ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

print_info() { echo -e "${BLUE}ℹ ${NC}$1"; }
print_success() { echo -e "${GREEN}✓ ${NC}$1"; }
print_warning() { echo -e "${YELLOW}⚠ ${NC}$1"; }
print_error() { echo -e "${RED}✗ ${NC}$1"; }
print_step() { echo -e "${CYAN}→ ${NC}$1"; }

# ============================================================
# 前置检查
# ============================================================
pre_check() {
    print_info "执行前置检查..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装"
        exit 1
    fi
    
    # 检查 .env 文件
    if [ ! -f .env ]; then
        print_warning ".env 文件不存在，从模板创建..."
        cp .env.example .env
        print_warning "请修改 .env 文件中的生产环境配置！"
        print_warning "特别是数据库密码和 API 密钥！"
    fi
    
    # 生产环境额外检查
    if [ "$ENVIRONMENT" == "prod" ]; then
        print_warning "生产环境部署，请确认："
        echo "  1. 已修改 .env 中的数据库密码"
        echo "  2. 已配置防火墙规则"
        echo "  3. 已设置 SSL 证书（如需 HTTPS）"
        echo ""
        read -p "确认继续？(yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            print_info "部署已取消"
            exit 0
        fi
    fi
    
    print_success "前置检查通过"
}

# ============================================================
# 拉取最新代码
# ============================================================
pull_code() {
    print_info "拉取最新代码..."
    
    if [ -d .git ]; then
        git pull origin main || git pull origin master
        print_success "代码已更新"
    else
        print_warning "不是 Git 仓库，跳过拉取"
    fi
}

# ============================================================
# 构建镜像
# ============================================================
build() {
    print_info "构建 Docker 镜像..."
    
    # 构建镜像（不使用缓存）
    docker-compose build --no-cache
    
    print_success "镜像构建完成"
}

# ============================================================
# 备份数据库
# ============================================================
backup_database() {
    print_info "备份数据库..."
    
    BACKUP_DIR="./backups"
    BACKUP_FILE="$BACKUP_DIR/memory_hub_$(date +%Y%m%d_%H%M%S).sql"
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    
    # 检查数据库是否运行
    if docker ps | grep -q memory-hub-db; then
        # 执行备份
        docker exec memory-hub-db pg_dump -U memory_user memory_hub > "$BACKUP_FILE"
        print_success "数据库已备份到: $BACKUP_FILE"
    else
        print_warning "数据库未运行，跳过备份"
    fi
}

# ============================================================
# 停止旧服务
# ============================================================
stop_old() {
    print_info "停止旧服务..."
    docker-compose down
    print_success "旧服务已停止"
}

# ============================================================
# 启动新服务
# ============================================================
start_new() {
    print_info "启动新服务..."
    
    # 设置环境变量
    export API_PORT
    export DB_PORT
    export ADMIN_PORT
    
    # 启动服务
    docker-compose up -d
    
    print_success "新服务已启动"
}

# ============================================================
# 健康检查
# ============================================================
health_check() {
    print_info "执行健康检查..."
    
    # 等待服务启动
    sleep 10
    
    # 检查数据库
    for i in {1..30}; do
        if docker exec memory-hub-db pg_isready -U memory_user -d memory_hub &> /dev/null; then
            print_success "数据库健康检查通过"
            break
        fi
        sleep 1
    done
    
    # 检查 API
    for i in {1..30}; do
        if curl -s "http://localhost:${API_PORT}/api/v1/health" &> /dev/null; then
            print_success "API 健康检查通过"
            break
        fi
        sleep 1
    done
    
    print_success "健康检查完成"
}

# ============================================================
# 清理旧镜像
# ============================================================
cleanup() {
    print_info "清理旧镜像..."
    
    # 删除未使用的镜像
    docker image prune -f
    
    print_success "清理完成"
}

# ============================================================
# 显示状态
# ============================================================
show_status() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║              部署完成                        ║${NC}"
    echo -e "${BOLD}${CYAN}╠══════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}${CYAN}║  环境: ${ENVIRONMENT^^}                              ║${NC}"
    echo -e "${BOLD}${CYAN}║  API:  http://localhost:${API_PORT}/docs         ║${NC}"
    echo -e "${BOLD}${CYAN}║  DB:   localhost:${DB_PORT}                     ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    
    docker-compose ps
}

# ============================================================
# 回滚函数
# ============================================================
rollback() {
    print_error "部署失败，执行回滚..."
    
    # 停止当前服务
    docker-compose down
    
    # 恢复最近备份
    LATEST_BACKUP=$(ls -t ./backups/*.sql 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        print_info "恢复数据库备份: $LATEST_BACKUP"
        # 这里需要手动恢复，因为数据库可能未运行
        print_warning "请手动恢复数据库备份"
    fi
    
    print_error "回滚完成，请检查错误"
    exit 1
}

# ============================================================
# 主流程
# ============================================================
main() {
    print_header
    
    # 设置错误时回滚
    trap rollback ERR
    
    pre_check
    pull_code
    backup_database
    stop_old
    build
    start_new
    health_check
    cleanup
    
    # 取消错误陷阱
    trap - ERR
    
    show_status
    
    print_success "部署成功！"
}

# 执行部署
main