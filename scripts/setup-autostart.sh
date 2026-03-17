#!/bin/bash
# Memory Hub 开机自启动配置脚本
# 执行方式: sudo bash scripts/setup-autostart.sh

set -e

echo "=== Memory Hub 开机自启动配置 ==="

# 1. 创建 systemd 服务文件
echo "[1/4] 创建 systemd 服务文件..."
cat > /etc/systemd/system/memory-hub.service << 'EOF'
[Unit]
Description=Memory Hub Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/wen/projects/memory-hub
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=wen
Group=wen

[Install]
WantedBy=multi-user.target
EOF
echo "✅ 服务文件已创建"

# 2. 重载 systemd
echo "[2/4] 重载 systemd..."
systemctl daemon-reload
echo "✅ systemd 已重载"

# 3. 启用并启动 Memory Hub 服务
echo "[3/4] 启用 Memory Hub 服务..."
systemctl enable memory-hub
systemctl start memory-hub
echo "✅ Memory Hub 服务已启用并启动"

# 4. 禁用 PostgreSQL 自启动
echo "[4/4] 禁用 PostgreSQL 自启动..."
systemctl stop postgresql
systemctl disable postgresql
echo "✅ PostgreSQL 已停止并禁用自启动"

# 验证
echo ""
echo "=== 验证结果 ==="
echo ""
echo "Memory Hub 服务状态:"
systemctl is-enabled memory-hub 2>/dev/null && echo "✅ 已启用" || echo "❌ 未启用"
echo ""
echo "PostgreSQL 服务状态:"
systemctl is-enabled postgresql 2>/dev/null && echo "⚠️ 仍启用" || echo "✅ 已禁用"
echo ""
echo "Docker 容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null
echo ""
echo "=== 配置完成 ==="
echo "重启后 Memory Hub 将自动启动，PostgreSQL 将不会自动启动"