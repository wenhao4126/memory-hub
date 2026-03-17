#!/bin/bash
# Systemd 服务部署脚本
# 执行方式: sudo bash scripts/deploy-systemd.sh

set -e

echo "=== Memory Hub Worker Pool Systemd 服务部署 ==="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    echo "用法: sudo bash scripts/deploy-systemd.sh"
    exit 1
fi

PROJECT_DIR="/home/wen/projects/memory-hub"
SERVICE_FILE="/etc/systemd/system/memory-hub-worker-pool.service"

echo "1. 创建 systemd 服务文件..."
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Memory Hub Worker Pool - 小码池服务
After=network.target docker.service
Wants=docker.service

[Service]
Type=forking
User=wen
Group=wen
WorkingDirectory=/home/wen/projects/memory-hub

# 启动脚本（5 个小码，30 秒轮询）
ExecStart=/home/wen/projects/memory-hub/scripts/start-worker-pool.sh 5 30

# 停止脚本
ExecStop=/home/wen/projects/memory-hub/scripts/stop-worker-pool.sh

# 失败后 10 秒重启
Restart=on-failure
RestartSec=10

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=memory-hub-worker-pool

[Install]
WantedBy=multi-user.target
EOF
echo "   ✓ 服务文件已创建: $SERVICE_FILE"

echo ""
echo "2. 重载 systemd 配置..."
systemctl daemon-reload
echo "   ✓ 配置已重载"

echo ""
echo "3. 启用开机自启..."
systemctl enable memory-hub-worker-pool
echo "   ✓ 已设置开机自启"

echo ""
echo "4. 启动服务..."
systemctl start memory-hub-worker-pool
echo "   ✓ 服务已启动"

echo ""
echo "5. 查看服务状态..."
systemctl status memory-hub-worker-pool --no-pager

echo ""
echo "=== 部署完成 ==="
echo ""
echo "常用命令:"
echo "  查看状态: sudo systemctl status memory-hub-worker-pool"
echo "  查看日志: sudo journalctl -u memory-hub-worker-pool -f"
echo "  重启服务: sudo systemctl restart memory-hub-worker-pool"
echo "  停止服务: sudo systemctl stop memory-hub-worker-pool"