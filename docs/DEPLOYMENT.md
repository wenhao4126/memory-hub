# Memory Hub 部署指南

本文档介绍如何在不同配置的服务器上部署 Memory Hub。

## 目录

- [快速部署](#快速部署)
- [低配服务器部署（2 核 2G）](#低配服务器部署2-核-2g)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [性能调优](#性能调优)

---

## 快速部署

### 标准服务器（推荐 4 核 8G 以上）

```bash
# 1. 克隆项目
git clone https://github.com/wenhao4126/memory-hub.git
cd memory-hub

# 2. 配置环境变量
cp .env.example .env
vim .env  # 修改必要配置

# 3. 启动服务
docker compose up -d

# 4. 检查状态
docker compose ps
```

---

## 低配服务器部署（2 核 2G）

### 自动部署脚本

我们为低配服务器提供了专用的部署脚本：

```bash
# 下载并执行部署脚本
curl -fsSL https://raw.githubusercontent.com/wenhao4126/memory-hub/master/scripts/deploy-low-end.sh | bash
```

或者手动克隆后执行：

```bash
git clone https://github.com/wenhao4126/memory-hub.git
cd memory-hub
chmod +x scripts/deploy-low-end.sh
sudo ./scripts/deploy-low-end.sh
```

### 脚本功能

1. **系统检测**：自动检测 CPU 和内存配置
2. **Swap 创建**：自动创建 4GB swap 空间
3. **Docker 安装**：轻量级 Docker 安装
4. **项目克隆**：自动克隆并更新代码
5. **配置优化**：
   - Docker daemon 日志限制
   - PostgreSQL 内存参数优化
   - 容器资源限制
6. **服务启动**：使用优化配置启动服务

### 手动部署步骤

如果需要手动部署，按以下步骤操作：

#### 1. 创建 Swap（重要！）

```bash
# 检查是否已有 swap
swapon --show

# 如果没有，创建 4GB swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 添加到 fstab 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 优化 swappiness
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### 2. 安装 Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo systemctl enable docker
```

#### 3. 优化 Docker 配置

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "live-restore": true
}
EOF
sudo systemctl restart docker
```

#### 4. 部署项目

```bash
cd /opt
git clone https://github.com/wenhao4126/memory-hub.git
cd memory-hub

# 配置环境变量
cp .env.example .env
vim .env

# 使用低内存配置启动
docker compose -f docker-compose.lowmem.yml up -d
```

---

## 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

```bash
# 数据库配置
DB_NAME=memory_hub
DB_USER=memory_user
DB_PASSWORD=your_secure_password_here  # 必须修改！

# 应用配置
SECRET_KEY=your_secret_key_here  # 必须修改！建议使用: openssl rand -hex 32

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # 或自定义端点
MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# 日志级别
LOG_LEVEL=INFO
```

### 低内存配置文件

`docker-compose.lowmem.yml` 针对低配服务器进行了以下优化：

#### PostgreSQL 优化

| 参数 | 默认值 | 低配值 | 说明 |
|------|--------|--------|------|
| shared_buffers | 128MB | 256MB | 共享内存缓冲区 |
| effective_cache_size | 4GB | 768MB | 预估可用缓存 |
| work_mem | 4MB | 16MB | 单查询内存 |
| maintenance_work_mem | 64MB | 64MB | 维护操作内存 |
| max_connections | 100 | 50 | 最大连接数 |

#### 容器资源限制

| 服务 | 内存限制 | 内存预留 |
|------|----------|----------|
| db (PostgreSQL) | 1G | 512M |
| api (FastAPI) | 512M | 256M |

---

## 常见问题

### 1. 内存不足导致服务崩溃

**症状**：容器频繁重启，OOM (Out of Memory) 错误

**解决方案**：
```bash
# 检查 swap 是否启用
swapon --show

# 如果没有，创建 swap（见上方步骤）

# 检查当前内存使用
free -h
docker stats
```

### 2. 数据库连接失败

**症状**：API 报错 "connection refused" 或 "could not connect to server"

**解决方案**：
```bash
# 检查数据库是否运行
docker compose ps

# 查看数据库日志
docker compose logs db

# 等待数据库完全启动（健康检查）
docker compose logs -f db
```

### 3. 磁盘空间不足

**症状**：部署失败或服务异常

**解决方案**：
```bash
# 检查磁盘空间
df -h

# 清理 Docker 资源
docker system prune -a

# 清理旧日志
sudo journalctl --vacuum-time=3d
```

### 4. 权限问题

**症状**：脚本执行失败，权限拒绝

**解决方案**：
```bash
# 给脚本执行权限
chmod +x scripts/deploy-low-end.sh

# 使用 root 或 sudo 执行
sudo ./scripts/deploy-low-end.sh
```

### 5. 端口被占用

**症状**：端口 8000 已被使用

**解决方案**：
```bash
# 检查端口占用
sudo lsof -i :8000

# 修改 .env 中的 API_PORT
echo "API_PORT=8001" >> .env

# 重启服务
docker compose down
docker compose up -d
```

---

## 性能调优

### 1. 监控资源使用

```bash
# 实时监控
docker stats

# 查看容器资源限制
docker inspect memory-hub-db | grep -A 10 "Memory"

# 查看系统内存
free -h
```

### 2. 调整 PostgreSQL 参数

根据实际使用情况，可以在 `docker-compose.lowmem.yml` 中调整：

```yaml
# 增加连接数（如果需要）
-c max_connections=100

# 减少内存使用（如果仍然不足）
-c shared_buffers=128MB
-c work_mem=8MB
```

### 3. 日志管理

```bash
# 限制 Docker 日志大小
# 在 daemon.json 中已配置：
# "log-opts": {"max-size": "10m", "max-file": "3"}

# 手动清理日志
docker compose logs --no-log-prefix > /dev/null
```

### 4. 定期备份

```bash
# 备份数据库
docker compose exec db pg_dump -U memory_user memory_hub > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker compose exec -T db psql -U memory_user memory_hub < backup_20260314.sql
```

---

## 升级指南

```bash
cd /opt/memory-hub

# 拉取最新代码
git pull origin master

# 重建并重启
docker compose down
docker compose -f docker-compose.lowmem.yml up -d --build

# 检查状态
docker compose ps
docker compose logs -f
```

---

## 支持

如有问题，请提交 [GitHub Issue](https://github.com/wenhao4126/memory-hub/issues)。