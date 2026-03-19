#!/bin/bash

# ============================================================
# Memory Hub 一键安装脚本
# ============================================================
# 作者：小码 4 🟡
# 日期：2026-03-19
# 
# 使用方法：
#   curl -fsSL https://raw.githubusercontent.com/wen41/memory-hub/master/scripts/install.sh | bash
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查系统要求
check_requirements() {
    info "检查系统要求..."
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        error "未找到 Node.js，请先安装 Node.js 16+"
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        error "Node.js 版本过低 ($NODE_VERSION)，需要 16+"
    fi
    success "Node.js 版本：$(node -v)"
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        error "未找到 npm"
    fi
    success "npm 版本：$(npm -v)"
    
    # 检查 Docker（可选）
    if command -v docker &> /dev/null; then
        success "Docker 版本：$(docker --version)"
        HAS_DOCKER=true
    else
        warning "未找到 Docker，将使用 Node.js 模式安装"
        HAS_DOCKER=false
    fi
    
    # 检查 Git
    if ! command -v git &> /dev/null; then
        warning "未找到 Git，部分功能可能不可用"
    fi
}

# 安装 Memory Hub CLI
install_cli() {
    info "安装 Memory Hub CLI..."
    
    # 全局安装
    npm install -g memory-hub
    
    # 验证安装
    if ! command -v memory-hub &> /dev/null; then
        error "CLI 安装失败"
    fi
    
    success "Memory Hub CLI 安装成功：$(memory-hub --version)"
}

# 初始化配置
init_config() {
    info "初始化配置..."
    
    # 创建项目目录
    INSTALL_DIR="${INSTALL_DIR:-$HOME/memory-hub}"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # 初始化配置
    memory-hub init -d "$INSTALL_DIR"
    
    success "配置初始化完成：$INSTALL_DIR"
}

# 安装 Docker 版本（如果有 Docker）
install_docker() {
    if [ "$HAS_DOCKER" = false ]; then
        return
    fi
    
    info "检测 Docker 可用，是否使用 Docker 部署？(y/n)"
    read -r USE_DOCKER
    
    if [ "$USE_DOCKER" = "y" ] || [ "$USE_DOCKER" = "Y" ]; then
        info "克隆项目..."
        git clone https://github.com/wen41/memory-hub.git "$INSTALL_DIR" 2>/dev/null || {
            warning "Git 克隆失败，尝试下载..."
            # 备用方案：下载 ZIP
            cd "$INSTALL_DIR"
            curl -fsSL https://github.com/wen41/memory-hub/archive/refs/heads/master.zip -o memory-hub.zip
            unzip -o memory-hub.zip
            mv memory-hub-master/* .
            rm -rf memory-hub-master memory-hub.zip
        }
        
        cd "$INSTALL_DIR"
        
        info "配置环境变量..."
        if [ ! -f ".env" ]; then
            cp .env.example .env
            success "环境变量配置完成"
        fi
        
        info "启动 Docker 服务..."
        docker-compose up -d
        
        # 等待服务启动
        info "等待服务启动（约 30 秒）..."
        sleep 30
        
        # 验证安装
        if curl -fsSL http://localhost:8000/api/v1/health &> /dev/null; then
            success "Docker 部署成功！"
        else
            warning "服务可能还在启动中，请稍后检查"
        fi
    else
        info "使用 Node.js 模式..."
        install_cli
        init_config
    fi
}

# 创建系统服务（Linux）
create_systemd_service() {
    if [ "$(uname)" != "Linux" ]; then
        return
    fi
    
    if [ ! -f "/etc/systemd/system/memory-hub.service" ]; then
        info "是否创建 systemd 服务？(y/n)"
        read -r CREATE_SERVICE
        
        if [ "$CREATE_SERVICE" = "y" ] || [ "$CREATE_SERVICE" = "Y" ]; then
            sudo memory-hub config systemd > /etc/systemd/system/memory-hub.service
            sudo systemctl daemon-reload
            sudo systemctl enable memory-hub
            sudo systemctl start memory-hub
            success "systemd 服务创建成功"
        fi
    fi
}

# 显示完成信息
show_complete_message() {
    echo ""
    success "============================================"
    success "  Memory Hub 安装完成！"
    success "============================================"
    echo ""
    info "安装目录：$INSTALL_DIR"
    info "配置文件：$INSTALL_DIR/config.yaml"
    info "环境变量：$INSTALL_DIR/.env"
    echo ""
    info "常用命令:"
    echo "  memory-hub start     # 启动服务"
    echo "  memory-hub stop      # 停止服务"
    echo "  memory-hub status    # 查看状态"
    echo "  memory-hub logs -f   # 查看日志"
    echo ""
    info "访问 API 文档:"
    echo "  http://localhost:8000/docs"
    echo ""
    info "下一步:"
    echo "  1. 编辑 config.yaml 配置你的参数"
    echo "  2. 运行 memory-hub start 启动服务"
    echo "  3. 访问 http://localhost:8000/docs 测试 API"
    echo ""
}

# 主函数
main() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Memory Hub 一键安装脚本${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --no-docker)
                HAS_DOCKER=false
                shift
                ;;
            -h|--help)
                echo "用法：install.sh [选项]"
                echo ""
                echo "选项:"
                echo "  -d, --dir <目录>    安装目录（默认：~/memory-hub）"
                echo "  --no-docker        不使用 Docker"
                echo "  -h, --help         显示帮助"
                exit 0
                ;;
            *)
                error "未知选项：$1"
                ;;
        esac
    done
    
    # 执行安装步骤
    check_requirements
    install_docker
    create_systemd_service
    show_complete_message
}

# 运行主函数
main "$@"
