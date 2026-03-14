#!/bin/bash
# 2 核 2G 服务器部署脚本
# 适用于低配服务器，自动创建 swap 并优化资源配置

set -e

echo "🚀 Memory Hub 低配服务器部署脚本"
echo "================================"

# 1. 检查配置
echo "📊 检查系统配置..."
CPU_CORES=$(nproc)
MEM_TOTAL=$(free -m | awk '/^Mem:/{print $2}')

echo "   CPU: ${CPU_CORES} 核心"
echo "   内存：${MEM_TOTAL} MB"

if [ $MEM_TOTAL -lt 1800 ]; then
    echo "⚠️  检测到内存小于 2GB，将启用优化模式"
    LOW_MEM_MODE=true
else
    LOW_MEM_MODE=false
fi

# 2. 创建 swap（仅低配模式）
if [ "$LOW_MEM_MODE" = true ]; then
    echo "💾 创建 4GB swap..."
    if [ ! -f /swapfile ]; then
        # 检查磁盘空间
        DISK_AVAIL=$(df -m / | awk 'NR==2 {print $4}')
        if [ $DISK_AVAIL -lt 5000 ]; then
            echo "❌ 磁盘空间不足，至少需要 5GB 可用空间"
            exit 1
        fi
        
        fallocate -l 4G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        
        # 添加到 fstab 永久生效
        if ! grep -q '/swapfile' /etc/fstab; then
            echo '/swapfile none swap sw 0 0' >> /etc/fstab
        fi
        echo "✅ swap 创建成功"
    else
        echo "ℹ️  swap 已存在"
    fi
fi

# 3. 安装 Docker
echo "🐳 安装 Docker..."
if ! command -v docker &> /dev/null; then
    echo "   正在安装 Docker（轻量级安装）..."
    curl -fsSL https://get.docker.com | sh
    
    # 启动 Docker 服务
    systemctl start docker
    systemctl enable docker
    
    echo "✅ Docker 安装完成"
else
    echo "ℹ️  Docker 已安装: $(docker --version)"
fi

# 4. 克隆项目
echo "📦 克隆项目..."
cd /opt
if [ ! -d memory-hub ]; then
    git clone https://github.com/wen41/memory-hub.git
    echo "✅ 项目克隆完成"
else
    echo "ℹ️  项目已存在，正在更新..."
    cd memory-hub
    git pull origin master || true
fi
cd memory-hub

# 5. 配置环境变量
echo "⚙️  配置环境变量..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ 环境变量已创建"
        echo ""
        echo "⚠️  重要：请编辑 .env 文件修改以下配置："
        echo "   - DB_PASSWORD: 数据库密码"
        echo "   - SECRET_KEY: 应用密钥"
        echo "   - 其他敏感信息"
    else
        echo "⚠️  .env.example 不存在，请手动创建 .env 文件"
        exit 1
    fi
else
    echo "ℹ️  环境变量已存在"
fi

# 6. 优化配置（低配模式）
if [ "$LOW_MEM_MODE" = true ]; then
    echo "🔧 应用低配优化..."
    
    # 使用低内存配置
    if [ -f docker-compose.lowmem.yml ]; then
        COMPOSE_FILE="docker-compose.lowmem.yml"
        echo "   使用 docker-compose.lowmem.yml 配置"
    else
        echo "   ⚠️  docker-compose.lowmem.yml 不存在，使用默认配置"
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    # 优化 Docker daemon 配置
    mkdir -p /etc/docker
    if [ ! -f /etc/docker/daemon.json ]; then
        cat > /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "live-restore": true,
    "default-ulimits": {
        "nofile": {
            "Name": "nofile",
            "Hard": 65536,
            "Soft": 65536
        }
    }
}
EOF
        systemctl restart docker
        echo "   ✅ Docker daemon 配置优化完成"
    fi
    
    # 设置 swappiness
    echo "vm.swappiness=10" >> /etc/sysctl.conf
    sysctl -p > /dev/null 2>&1 || true
    echo "   ✅ 系统参数优化完成"
else
    COMPOSE_FILE="docker-compose.yml"
fi

# 7. 启动服务
echo "🚀 启动服务..."
if [ "$LOW_MEM_MODE" = true ] && [ -f docker-compose.lowmem.yml ]; then
    docker compose -f docker-compose.lowmem.yml up -d --build
else
    docker compose up -d --build
fi

# 8. 验证
echo "⏳ 等待服务启动..."
sleep 10

echo "🔍 检查服务状态..."
docker compose ps

# 获取公网 IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ip.sb 2>/dev/null || echo "YOUR_SERVER_IP")

echo ""
echo "================================"
echo "✅ 部署完成！"
echo ""
echo "📚 API 文档：http://${PUBLIC_IP}:8000/docs"
echo "🔌 API 接口：http://${PUBLIC_IP}:8000"
echo ""

if [ "$LOW_MEM_MODE" = true ]; then
    echo "💡 低配模式已启用："
    echo "   - 4GB swap 已创建"
    echo "   - 内存限制：db 1G / api 512M"
    echo "   - PostgreSQL 参数已优化"
    echo ""
fi

echo "⚠️  请记得修改 .env 中的密码和密钥！"
echo "   文件位置：/opt/memory-hub/.env"
echo ""

# 显示健康检查命令
echo "🔍 常用命令："
echo "   查看日志：docker compose logs -f"
echo "   重启服务：docker compose restart"
echo "   停止服务：docker compose down"