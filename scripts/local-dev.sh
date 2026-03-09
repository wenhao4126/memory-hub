#!/bin/bash
# ============================================================
# 多智能体记忆中枢 - 本地开发启动脚本
# ============================================================
# 功能：无需 Docker，直接在本地运行 Python + PostgreSQL
# 作者：小码
# 日期：2026-03-06
# ============================================================

# 彩色输出函数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$PROJECT_ROOT/venv"
ENV_FILE="$PROJECT_ROOT/.env"

# 打印函数
print_header() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${CYAN}多智能体记忆中枢 - 本地开发环境${NC}                       ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════╝${NC}"
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

print_step() {
    echo -e "${CYAN}🔧 $1${NC}"
}

# 检查 PostgreSQL 是否安装
check_postgresql() {
    print_step "检查 PostgreSQL..."
    
    if command -v psql &> /dev/null; then
        local pg_version=$(psql --version | awk '{print $3}')
        print_success "PostgreSQL 已安装 (版本: $pg_version)"
        
        # 检查 PostgreSQL 服务是否运行
        if pg_isready -q 2>/dev/null; then
            print_success "PostgreSQL 服务正在运行"
        else
            print_warning "PostgreSQL 服务未运行"
            print_info "请启动 PostgreSQL 服务："
            echo -e "  ${YELLOW}sudo systemctl start postgresql${NC}  # Linux (systemd)"
            echo -e "  ${YELLOW}brew services start postgresql${NC}   # macOS (Homebrew)"
            echo -e "  ${YELLOW}pg_ctl -D /usr/local/var/postgres start${NC}  # macOS 手动"
            return 1
        fi
        return 0
    else
        print_error "PostgreSQL 未安装"
        print_info "安装方法："
        echo -e "  ${YELLOW}Ubuntu/Debian: sudo apt install postgresql postgresql-contrib${NC}"
        echo -e "  ${YELLOW}macOS: brew install postgresql${NC}"
        echo -e "  ${YELLOW}Arch Linux: sudo pacman -S postgresql${NC}"
        return 1
    fi
}

# 检查 pgvector 扩展
check_pgvector() {
    print_step "检查 pgvector 扩展..."
    
    # 从 .env 读取数据库配置
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
    else
        DB_USER="${DB_USER:-memory_user}"
        DB_NAME="${DB_NAME:-memory_hub}"
    fi
    
    # 检查 pgvector 扩展
    local result=$(psql -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT 1 FROM pg_available_extensions WHERE name = 'vector';" 2>/dev/null)
    
    if [ "$result" = "1" ]; then
        print_success "pgvector 扩展已安装"
        return 0
    else
        print_warning "pgvector 扩展未安装"
        print_info "安装方法："
        echo -e "  ${YELLOW}Ubuntu/Debian: sudo apt install postgresql-${PG_VERSION:-16}-pgvector${NC}"
        echo -e "  ${YELLOW}macOS: brew install pgvector${NC}"
        echo -e "  ${YELLOW}Arch Linux: sudo pacman -S pgvector${NC}"
        echo ""
        print_info "或者从源码编译："
        echo -e "  ${YELLOW}git clone https://github.com/pgvector/pgvector.git${NC}"
        echo -e "  ${YELLOW}cd pgvector && make && sudo make install${NC}"
        return 1
    fi
}

# 检查 Python 环境
check_python() {
    print_step "检查 Python 环境..."
    
    local python_cmd=""
    
    # 优先使用 python3
    if command -v python3 &> /dev/null; then
        python_cmd="python3"
    elif command -v python &> /dev/null; then
        python_cmd="python"
    else
        print_error "Python 未安装"
        print_info "请安装 Python 3.10 或更高版本"
        return 1
    fi
    
    # 检查 Python 版本
    local py_version=$($python_cmd --version 2>&1 | awk '{print $2}')
    local major=$(echo "$py_version" | cut -d. -f1)
    local minor=$(echo "$py_version" | cut -d. -f2)
    
    if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; then
        print_success "Python 版本符合要求 ($py_version)"
        export PYTHON_CMD="$python_cmd"
        return 0
    else
        print_error "Python 版本过低 ($py_version)，需要 3.10+"
        return 1
    fi
}

# 检查虚拟环境
check_venv() {
    print_step "检查 Python 虚拟环境..."
    
    if [ -d "$VENV_DIR" ]; then
        print_success "虚拟环境已存在"
        
        # 检查虚拟环境是否完整
        if [ -f "$VENV_DIR/bin/activate" ]; then
            return 0
        else
            print_warning "虚拟环境不完整，需要重新创建"
            return 1
        fi
    else
        print_info "虚拟环境不存在"
        return 1
    fi
}

# 创建虚拟环境
create_venv() {
    print_step "创建 Python 虚拟环境..."
    
    cd "$PROJECT_ROOT"
    
    $PYTHON_CMD -m venv venv
    
    if [ $? -eq 0 ]; then
        print_success "虚拟环境创建成功"
        return 0
    else
        print_error "虚拟环境创建失败"
        return 1
    fi
}

# 安装依赖
install_dependencies() {
    print_step "安装 Python 依赖..."
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级 pip
    pip install --upgrade pip -q
    
    # 安装依赖
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        pip install -r "$BACKEND_DIR/requirements.txt" -q
        
        if [ $? -eq 0 ]; then
            print_success "依赖安装成功"
            return 0
        else
            print_error "依赖安装失败"
            return 1
        fi
    else
        print_error "requirements.txt 不存在"
        return 1
    fi
}

# 检查依赖是否已安装
check_dependencies() {
    print_step "检查依赖安装状态..."
    
    source "$VENV_DIR/bin/activate"
    
    # 检查关键依赖
    local missing=0
    
    for pkg in fastapi uvicorn asyncpg psycopg pydantic; do
        if ! pip show "$pkg" &> /dev/null; then
            print_warning "缺失依赖: $pkg"
            missing=1
        fi
    done
    
    if [ $missing -eq 0 ]; then
        print_success "所有依赖已安装"
        return 0
    else
        print_info "需要安装缺失的依赖"
        return 1
    fi
}

# 检查 .env 文件
check_env_file() {
    print_step "检查环境变量配置..."
    
    if [ -f "$ENV_FILE" ]; then
        print_success ".env 文件已存在"
        
        # 检查必需的环境变量
        source "$ENV_FILE"
        
        if [ -z "$DB_PASSWORD" ]; then
            print_error "DB_PASSWORD 未设置"
            print_info "请在 .env 文件中设置数据库密码"
            return 1
        fi
        
        return 0
    else
        print_warning ".env 文件不存在"
        
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            print_info "正在从 .env.example 创建 .env 文件..."
            cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
            print_success ".env 文件已创建"
            print_warning "请编辑 .env 文件，设置数据库密码："
            echo -e "  ${YELLOW}vim $ENV_FILE${NC}"
            return 1
        else
            print_error ".env.example 也不存在"
            return 1
        fi
    fi
}

# 初始化数据库
init_database() {
    print_step "初始化数据库..."
    
    # 从 .env 读取配置
    source "$ENV_FILE"
    
    # 设置默认值
    DB_USER="${DB_USER:-memory_user}"
    DB_NAME="${DB_NAME:-memory_hub}"
    DB_PORT="${DB_PORT:-5432}"
    
    # 检查数据库是否存在
    local db_exists=$(psql -U "$DB_USER" -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME" && echo "yes" || echo "no")
    
    if [ "$db_exists" = "yes" ]; then
        print_info "数据库 '$DB_NAME' 已存在"
        
        # 检查表是否存在
        local table_count=$(psql -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null)
        
        if [ "$table_count" -gt 0 ]; then
            print_success "数据库已初始化 (表数量: $table_count)"
            return 0
        fi
    fi
    
    # 创建数据库（如果不存在）
    print_info "创建数据库 '$DB_NAME'..."
    createdb -U "$DB_USER" "$DB_NAME" 2>/dev/null || true
    
    # 执行初始化脚本
    if [ -f "$PROJECT_ROOT/scripts/init-db.sql" ]; then
        print_info "执行数据库初始化脚本..."
        psql -U "$DB_USER" -d "$DB_NAME" -f "$PROJECT_ROOT/scripts/init-db.sql"
        
        if [ $? -eq 0 ]; then
            print_success "数据库初始化成功"
            return 0
        else
            print_error "数据库初始化失败"
            return 1
        fi
    else
        print_error "init-db.sql 不存在"
        return 1
    fi
}

# 创建数据库用户（如果不存在）
create_db_user() {
    print_step "检查数据库用户..."
    
    source "$ENV_FILE"
    
    DB_USER="${DB_USER:-memory_user}"
    DB_PASSWORD="${DB_PASSWORD:-}"
    
    # 检查用户是否存在
    local user_exists=$(psql -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER';" 2>/dev/null)
    
    if [ "$user_exists" = "1" ]; then
        print_success "数据库用户 '$DB_USER' 已存在"
        return 0
    fi
    
    # 创建用户
    if [ -n "$DB_PASSWORD" ]; then
        print_info "创建数据库用户 '$DB_USER'..."
        psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null
        psql -U postgres -c "ALTER USER $DB_USER CREATEDB;" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            print_success "数据库用户创建成功"
            return 0
        else
            print_error "数据库用户创建失败"
            print_info "可能需要使用 sudo 或 postgres 用户权限："
            echo -e "  ${YELLOW}sudo -u postgres createuser -d $DB_USER${NC}"
            echo -e "  ${YELLOW}sudo -u postgres psql -c \"ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"${NC}"
            return 1
        fi
    else
        print_error "DB_PASSWORD 未设置"
        return 1
    fi
}

# 启动 API 服务
start_api() {
    print_step "启动 API 服务..."
    
    cd "$BACKEND_DIR"
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 加载环境变量
    source "$ENV_FILE"
    
    # 设置默认值
    export API_HOST="${API_HOST:-0.0.0.0}"
    export API_PORT="${API_PORT:-8000}"
    export DB_HOST="${DB_HOST:-localhost}"
    export DB_PORT="${DB_PORT:-5432}"
    export DB_USER="${DB_USER:-memory_user}"
    export DB_NAME="${DB_NAME:-memory_hub}"
    
    print_success "API 服务启动中..."
    print_info "服务地址: http://localhost:$API_PORT"
    print_info "API 文档: http://localhost:$API_PORT/docs"
    print_info "按 Ctrl+C 停止服务"
    echo ""
    
    # 启动 uvicorn
    uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" --reload
}

# 显示帮助
show_help() {
    echo ""
    echo -e "${CYAN}用法：${NC}"
    echo -e "  $0 [命令]"
    echo ""
    echo -e "${CYAN}命令：${NC}"
    echo -e "  ${GREEN}start${NC}       启动 API 服务（默认命令）"
    echo -e "  ${GREEN}init-db${NC}     初始化数据库"
    echo -e "  ${GREEN}install${NC}     安装 Python 依赖"
    echo -e "  ${GREEN}check${NC}       检查环境状态"
    echo -e "  ${GREEN}help${NC}        显示帮助信息"
    echo ""
    echo -e "${CYAN}示例：${NC}"
    echo -e "  $0              # 一键启动（检查环境 → 初始化 → 启动）"
    echo -e "  $0 start        # 启动 API 服务"
    echo -e "  $0 init-db       # 初始化数据库"
    echo -e "  $0 install       # 安装依赖"
    echo -e "  $0 check         # 检查环境状态"
    echo ""
}

# 检查环境状态
check_status() {
    echo ""
    print_info "环境检查结果："
    echo ""
    
    # 检查各项
    local all_ok=true
    
    check_python || all_ok=false
    echo ""
    
    check_postgresql || all_ok=false
    echo ""
    
    check_venv || all_ok=false
    echo ""
    
    check_env_file || all_ok=false
    echo ""
    
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
        check_pgvector || all_ok=false
        echo ""
    fi
    
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        check_dependencies || all_ok=false
        echo ""
    fi
    
    # 总结
    echo "══════════════════════════════════════════════════════════"
    if $all_ok; then
        print_success "所有检查通过！可以启动服务"
        echo -e "  运行 ${GREEN}./scripts/local-dev.sh${NC} 或 ${GREEN}./scripts/local-dev.sh start${NC}"
    else
        print_warning "部分检查未通过，请按提示修复"
    fi
    echo "══════════════════════════════════════════════════════════"
    echo ""
    
    $all_ok
}

# 主流程
main() {
    print_header
    
    local command="${1:-start}"
    
    case "$command" in
        start)
            # 完整启动流程
            check_python || exit 1
            check_postgresql || exit 1
            check_venv || create_venv || exit 1
            check_env_file || exit 1
            check_dependencies || install_dependencies || exit 1
            
            # 检查 pgvector（可选，给出警告但不阻止）
            check_pgvector || print_warning "pgvector 扩展未安装，向量搜索功能可能不可用"
            
            # 初始化数据库（可选，用户可能已经初始化）
            init_database || print_warning "数据库初始化失败，可能需要手动处理"
            
            # 启动服务
            start_api
            ;;
        
        init-db)
            check_python || exit 1
            check_postgresql || exit 1
            check_env_file || exit 1
            create_db_user || true
            init_database
            ;;
        
        install)
            check_python || exit 1
            check_venv || create_venv || exit 1
            install_dependencies
            ;;
        
        check)
            check_status
            ;;
        
        help|--help|-h)
            show_help
            ;;
        
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主流程
main "$@"