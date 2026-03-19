#!/bin/bash

# ============================================================
# Memory Hub 一键安装脚本
# ============================================================
# 作者：小码 3 🟡
# 版本：1.0.0
# 日期：2026-03-19
#
# 支持的安装方式：
#   方式 1：curl 管道（推荐）
#     curl -fsSL https://raw.githubusercontent.com/xxx/memory-hub/main/install.sh | bash
#
#   方式 2：下载后执行
#     wget https://.../install.sh
#     bash install.sh
#
#   方式 3：带参数
#     bash install.sh --port 9000 --no-prompt
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
NC='\033[0m' # No Color
BOLD='\033[1m'

# ============================================================
# 默认配置
# ============================================================
DEFAULT_INSTALL_DIR="$HOME/memory-hub"
DEFAULT_PORT=8000
DEFAULT_ADMIN_PORT=5050
DEFAULT_DB_PORT=5433
GITHUB_REPO="https://github.com/wenhao4126/memory-hub.git"
BRANCH="main"

# ============================================================
# 全局变量
# ============================================================
INSTALL_DIR=""
PORT=""
ADMIN_PORT=""
DB_PORT=""
NO_PROMPT=false
SKIP_DOCKER_CHECK=false

# ============================================================
# 帮助信息
# ============================================================
show_help() {
    cat << EOF
${BOLD}Memory Hub 一键安装脚本${NC}

${CYAN}用法:${NC}
  $0 [选项]

${CYAN}选项:${NC}
  -h, --help              显示帮助信息
  -d, --dir <路径>        安装目录 (默认：~/memory-hub)
  -p, --port <端口>       API 端口 (默认：8000)
  -a, --admin-port <端口> pgAdmin 端口 (默认：5050)
  -b, --db-port <端口>    数据库端口 (默认：5433)
  -y, --no-prompt         静默安装，使用默认配置
  --skip-docker-check     跳过 Docker 检查
  -v, --verbose           详细输出模式

${CYAN}示例:${NC}
  # 交互式安装
  $0

  # 静默安装，使用默认配置
  $0 --no-prompt

  # 自定义端口
  $0 --port 9000 --admin-port 6050

  # 自定义安装目录
  $0 --dir /opt/memory-hub

EOF
}

# ============================================================
# 日志函数
# ============================================================
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

# ============================================================
# 进度条函数
# ============================================================
show_progress() {
    local duration=$1
    local message=$2
    local bar_width=40
    local start_time=$(date +%s)
    
    for i in $(seq 0 $bar_width); do
        local percent=$((i * 100 / bar_width))
        local filled=$((i))
        local empty=$((bar_width - i))
        
        printf "\r${CYAN}[%${filled}s%${empty}s]${NC} %3d%% %s" \
            $(printf '#%.0s' $(seq 1 $filled)) \
            $(printf ' %.0s' $(seq 1 $empty)) \
            $percent \
            "$message"
        
        sleep $(echo "scale=3; $duration / $bar_width" | bc)
    done
    
    printf "\r${GREEN}[========================================]${NC} 100%% ${message}\n"
}

# ============================================================
# 解析命令行参数
# ============================================================
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
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -a|--admin-port)
                ADMIN_PORT="$2"
                shift 2
                ;;
            -b|--db-port)
                DB_PORT="$2"
                shift 2
                ;;
            -y|--no-prompt)
                NO_PROMPT=true
                shift
                ;;
            --skip-docker-check)
                SKIP_DOCKER_CHECK=true
                shift
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            *)
                log_error "未知选项：$1"
                echo "使用 --help 查看帮助"
                exit 1
                ;;
        esac
    done
}

# ============================================================
# 检查系统要求
# ============================================================
check_requirements() {
    log_step "检查系统要求"
    
    local has_error=false
    
    # 检查 Docker
    if [ "$SKIP_DOCKER_CHECK" = false ]; then
        if command -v docker &> /dev/null; then
            log_success "Docker 已安装：$(docker --version)"
        else
            log_error "Docker 未安装"
            log_info "请先安装 Docker: https://docs.docker.com/get-docker/"
            has_error=true
        fi
        
        # 检查 docker-compose
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            if command -v docker-compose &> /dev/null; then
                log_success "docker-compose 已安装：$(docker-compose --version)"
            else
                log_success "Docker Compose 已安装：$(docker compose version)"
            fi
        else
            log_error "docker-compose 未安装"
            log_info "请先安装 docker-compose: https://docs.docker.com/compose/install/"
            has_error=true
        fi
    else
        log_warning "跳过 Docker 检查"
    fi
    
    # 检查 Git
    if command -v git &> /dev/null; then
        log_success "Git 已安装：$(git --version)"
    else
        log_error "Git 未安装"
        log_info "请先安装 Git"
        has_error=true
    fi
    
    # 检查 curl/wget
    if command -v curl &> /dev/null; then
        log_success "curl 已安装"
    elif command -v wget &> /dev/null; then
        log_success "wget 已安装"
    else
        log_warning "curl 和 wget 都未安装，部分功能可能受限"
    fi
    
    # 检查 bc（进度条依赖）
    if command -v bc &> /dev/null; then
        log_success "bc 已安装"
    else
        log_warning "bc 未安装，进度条将简化显示"
    fi
    
    if [ "$has_error" = true ] && [ "$SKIP_DOCKER_CHECK" = false ]; then
        log_error "系统要求不满足，请先安装缺失的依赖"
        exit 1
    fi
    
    log_success "系统检查通过"
}

# ============================================================
# 交互式配置
# ============================================================
interactive_config() {
    if [ "$NO_PROMPT" = true ]; then
        log_info "使用默认配置（静默安装）"
        return
    fi
    
    log_step "配置安装选项"
    
    echo -e "${CYAN}========================================${NC}"
    echo -e "${BOLD}Memory Hub 安装配置${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    
    # 安装目录
    echo -n "安装目录 [默认：$DEFAULT_INSTALL_DIR]: "
    read -r input_dir
    INSTALL_DIR="${input_dir:-$DEFAULT_INSTALL_DIR}"
    
    # API 端口
    echo -n "API 端口 [默认：$DEFAULT_PORT]: "
    read -r input_port
    PORT="${input_port:-$DEFAULT_PORT}"
    
    # pgAdmin 端口
    echo -n "pgAdmin 端口 [默认：$DEFAULT_ADMIN_PORT]: "
    read -r input_admin_port
    ADMIN_PORT="${input_admin_port:-$DEFAULT_ADMIN_PORT}"
    
    # 数据库端口
    echo -n "数据库端口 [默认：$DEFAULT_DB_PORT]: "
    read -r input_db_port
    DB_PORT="${input_db_port:-$DEFAULT_DB_PORT}"
    
    echo ""
    echo -e "${CYAN}配置确认:${NC}"
    echo "  安装目录：$INSTALL_DIR"
    echo "  API 端口：$PORT"
    echo "  pgAdmin 端口：$ADMIN_PORT"
    echo "  数据库端口：$DB_PORT"
    echo ""
    
    echo -n "是否继续安装？[Y/n]: "
    read -r confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        log_error "安装已取消"
        exit 1
    fi
}

# ============================================================
# 设置默认值
# ============================================================
set_defaults() {
    INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"
    PORT="${PORT:-$DEFAULT_PORT}"
    ADMIN_PORT="${ADMIN_PORT:-$DEFAULT_ADMIN_PORT}"
    DB_PORT="${DB_PORT:-$DEFAULT_DB_PORT}"
}

# ============================================================
# 下载项目
# ============================================================
download_project() {
    log_step "下载 Memory Hub 项目"
    
    if [ -d "$INSTALL_DIR" ]; then
        log_warning "目录已存在：$INSTALL_DIR"
        if [ "$NO_PROMPT" = false ]; then
            echo -n "是否删除并重新安装？[y/N]: "
            read -r confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                rm -rf "$INSTALL_DIR"
                log_info "已删除旧目录"
            else
                log_info "使用现有目录"
            fi
        else
            log_info "使用现有目录（静默模式）"
        fi
    fi
    
    # 创建安装目录
    mkdir -p "$INSTALL_DIR"
    
    # 检查是否是 Git 仓库
    if [ -d "$INSTALL_DIR/.git" ]; then
        log_info "更新现有仓库..."
        cd "$INSTALL_DIR"
        git pull origin "$BRANCH" || log_warning "Git 更新失败，继续使用现有代码"
    elif [ -d "$LOCAL_SOURCE/.git" ]; then
        log_info "从本地源复制..."
        rm -rf "$INSTALL_DIR"
        cp -r "$LOCAL_SOURCE" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    else
        log_info "克隆仓库..."
        git clone "$GITHUB_REPO" "$INSTALL_DIR" 2>/dev/null || {
            log_warning "Git 克隆失败，尝试下载 ZIP"
            # 备用方案：下载 ZIP
            TEMP_ZIP=$(mktemp)
            curl -fsSL "$GITHUB_REPO/archive/refs/heads/$BRANCH.zip" -o "$TEMP_ZIP" 2>/dev/null || \
            wget -q "$GITHUB_REPO/archive/refs/heads/$BRANCH.zip" -O "$TEMP_ZIP" || {
                log_error "无法下载项目"
                exit 1
            }
            unzip -q "$TEMP_ZIP" -d "$INSTALL_DIR"
            mv "$INSTALL_DIR/memory-hub-$BRANCH"/* "$INSTALL_DIR/"
            rm -rf "$INSTALL_DIR/memory-hub-$BRANCH"
            rm -f "$TEMP_ZIP"
        }
    fi
    
    cd "$INSTALL_DIR"
    log_success "项目下载完成"
}

# ============================================================
# 生成配置文件
# ============================================================
generate_config() {
    log_step "生成配置文件"
    
    cd "$INSTALL_DIR"
    
    # 生成 .env 文件
    if [ -f ".env" ]; then
        log_info "备份现有 .env 文件"
        cp .env .env.backup.$(date +%Y%m%d%H%M%S)
    fi
    
    # 生成 DashScope API Key 提示
    echo -e "\n${YELLOW}注意:${NC}"
    echo "Memory Hub 需要 DashScope API Key 才能运行。"
    echo "如果没有，请在安装后编辑 .env 文件配置。"
    echo "获取地址：https://dashscope.console.aliyun.com/"
    echo ""
    
    if [ "$NO_PROMPT" = false ]; then
        echo -n "是否现在配置 DashScope API Key？[Y/n]: "
        read -r config_api
        if [[ ! "$config_api" =~ ^[Nn]$ ]]; then
            echo -n "请输入 DashScope LLM API Key: "
            read -r llm_key
            echo -n "请输入 DashScope Embedding API Key: "
            read -r embed_key
        fi
    fi
    
    # 创建 .env 文件
    cat > .env << EOF
# ============================================================
# Memory Hub 配置文件
# ============================================================
# 由 install.sh 自动生成
# 日期：$(date '+%Y-%m-%d %H:%M:%S')
# ============================================================

# ============================================================
# 端口配置
# ============================================================
API_PORT=$PORT
ADMIN_PORT=$ADMIN_PORT
DB_PORT=$DB_PORT

# ============================================================
# 数据库配置
# ============================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=memory_hub
DB_USER=memory_user
DB_PASSWORD=memory_pass_$(openssl rand -hex 8 2>/dev/null || echo $RANDOM$RANDOM)

# 数据库连接字符串
DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@\${DB_HOST}:\${DB_PORT}/\${DB_NAME}

# 连接池配置
DB_POOL_MIN=5
DB_POOL_MAX=20

# ============================================================
# API 配置
# ============================================================
API_HOST=0.0.0.0
API_DEBUG=false

# ============================================================
# 嵌入模型配置
# ============================================================
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSION=1536

# ============================================================
# DashScope API 配置
# ============================================================
DASHSCOPE_LLM_API_KEY=${llm_key:-your_llm_api_key_here}
DASHSCOPE_EMBEDDING_API_KEY=${embed_key:-your_embedding_api_key_here}
DASHSCOPE_BASE_URL=https://coding.dashscope.aliyuncs.com/v1

# ============================================================
# LLM 配置
# ============================================================
LLM_MODEL=qwen3.5-plus
LLM_BASE_URL=https://coding.dashscope.aliyuncs.com/v1

# ============================================================
# 管理员配置
# ============================================================
ADMIN_EMAIL=admin@memory.hub
ADMIN_PASSWORD=admin123

# ============================================================
# 任务配置
# ============================================================
DEFAULT_LOCK_DURATION=30
DEFAULT_TIMEOUT=30
DEFAULT_MAX_RETRIES=3

# ============================================================
# 日志配置
# ============================================================
LOG_LEVEL=INFO
LOG_TO_FILE=false
EOF

    log_success "配置文件已生成：$INSTALL_DIR/.env"
    
    # 显示 API Key 配置提示
    if [[ "$llm_key" == "your_llm_api_key_here" ]]; then
        log_warning "请编辑 .env 文件配置 DashScope API Key"
        echo "  编辑命令：nano $INSTALL_DIR/.env"
        echo "  配置项：DASHSCOPE_LLM_API_KEY, DASHSCOPE_EMBEDDING_API_KEY"
    fi
}

# ============================================================
# 启动服务
# ============================================================
start_services() {
    log_step "启动服务"
    
    cd "$INSTALL_DIR"
    
    # 检查 Docker 是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
    
    # 停止现有服务（如果有）
    if docker compose ps &> /dev/null; then
        log_info "停止现有服务..."
        docker compose down 2>/dev/null || true
    fi
    
    # 启动服务
    log_info "启动 Docker 容器..."
    show_progress 3 "启动数据库服务"
    docker compose up -d postgres 2>/dev/null || docker-compose up -d postgres
    
    log_info "等待数据库就绪..."
    sleep 5
    
    show_progress 5 "启动 API 服务"
    docker compose up -d api 2>/dev/null || docker-compose up -d api
    
    show_progress 3 "启动管理界面"
    docker compose up -d pgadmin 2>/dev/null || docker-compose up -d pgadmin
    
    log_success "服务启动完成"
}

# ============================================================
# 健康检查
# ============================================================
health_check() {
    log_step "健康检查"
    
    cd "$INSTALL_DIR"
    
    local has_error=false
    
    # 检查容器状态
    log_info "检查容器状态..."
    docker compose ps 2>/dev/null || docker-compose ps
    
    # 检查数据库
    log_info "检查数据库连接..."
    if docker compose exec -T postgres pg_isready -U memory_user -d memory_hub &> /dev/null 2>/dev/null || \
       docker-compose exec -T postgres pg_isready -U memory_user -d memory_hub &> /dev/null 2>/dev/null; then
        log_success "数据库运行正常"
    else
        log_warning "数据库连接检查失败（可能正在启动）"
    fi
    
    # 检查 API
    log_info "检查 API 服务..."
    sleep 5
    if curl -fs "http://localhost:$PORT/api/v1/health" &> /dev/null; then
        log_success "API 服务运行正常"
    else
        log_warning "API 服务尚未就绪，请稍后检查"
    fi
    
    # 检查 pgAdmin
    log_info "检查 pgAdmin..."
    if curl -fs "http://localhost:$ADMIN_PORT" &> /dev/null; then
        log_success "pgAdmin 运行正常"
    else
        log_warning "pgAdmin 尚未就绪"
    fi
}

# ============================================================
# 显示完成信息
# ============================================================
show_completion() {
    log_step "安装完成"
    
    cat << EOF

${GREEN}${BOLD}========================================${NC}
${GREEN}${BOLD}   Memory Hub 安装成功！${NC}
${GREEN}${BOLD}========================================${NC}

${CYAN}安装目录:${NC} $INSTALL_DIR

${CYAN}服务端口:${NC}
  API 服务：    http://localhost:$PORT
  pgAdmin:      http://localhost:$ADMIN_PORT
  数据库：      localhost:$DB_PORT

${CYAN}快速开始:${NC}
  1. 配置 API Key（如果尚未配置）
     ${YELLOW}nano $INSTALL_DIR/.env${NC}
     
     配置项：
     - DASHSCOPE_LLM_API_KEY
     - DASHSCOPE_EMBEDDING_API_KEY

  2. 查看 API 文档
     ${BLUE}http://localhost:$PORT/docs${NC}

  3. 访问 pgAdmin
     ${BLUE}http://localhost:$ADMIN_PORT${NC}
     默认账号：admin@memory.hub
     默认密码：admin123

${CYAN}常用命令:${NC}
  # 查看服务状态
  cd $INSTALL_DIR && docker compose ps

  # 重启服务
  cd $INSTALL_DIR && docker compose restart

  # 停止服务
  cd $INSTALL_DIR && docker compose down

  # 查看日志
  cd $INSTALL_DIR && docker compose logs -f

  # 更新项目
  cd $INSTALL_DIR && git pull && docker compose up -d --build

${CYAN}卸载:${NC}
  bash $INSTALL_DIR/uninstall.sh

${YELLOW}注意:${NC}
  - 请妥善保管 .env 文件中的密码
  - 建议修改默认的管理员密码
  - 生产环境请配置防火墙规则

${GREEN}========================================${NC}
EOF
}

# ============================================================
# 主函数
# ============================================================
main() {
    echo -e "${CYAN}${BOLD}"
    cat << EOF
 __  __ _     _     _ _        _   _   _                 
|  \/  (_) __| | __| | | ___  | | | | | |_ __   ___ _ __ 
| |\/| | |/_\` |/ _\` | |/ _ \ | | | | | | '_ \ / _ \ '__|
| |  | | | (_| | (_| | |  __/ | | |_| | | |_) |  __/ |   
|_|  |_|_|\__,_|\__,_|_|\___| | | \___/|_| .__/ \___|_|   
                               |_|        |_|              
EOF
    echo -e "${NC}"
    echo -e "${BLUE}多智能体记忆中枢 - 一键安装脚本${NC}"
    echo -e "${BLUE}版本：1.0.0 | 日期：2026-03-19${NC}"
    echo ""
    
    # 解析参数
    parse_args "$@"
    
    # 设置默认值
    set_defaults
    
    # 检查系统要求
    check_requirements
    
    # 交互式配置
    interactive_config
    
    # 下载项目
    download_project
    
    # 生成配置文件
    generate_config
    
    # 启动服务
    start_services
    
    # 健康检查
    health_check
    
    # 显示完成信息
    show_completion
    
    # 写入安装记录
    echo "安装时间：$(date '+%Y-%m-%d %H:%M:%S')" > "$INSTALL_DIR/.install_info"
    echo "安装版本：1.0.0" >> "$INSTALL_DIR/.install_info"
    echo "安装目录：$INSTALL_DIR" >> "$INSTALL_DIR/.install_info"
    echo "API 端口：$PORT" >> "$INSTALL_DIR/.install_info"
}

# 执行主函数
main "$@"
