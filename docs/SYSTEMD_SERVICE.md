# Memory Hub Worker Pool - Systemd 服务管理

## 概述

小码池已注册为 systemd 服务，实现开机自启和故障自动重启。

## 服务信息

- **服务名称**: `memory-hub-worker-pool`
- **服务文件**: `/etc/systemd/system/memory-hub-worker-pool.service`
- **工作目录**: `/home/wen/projects/memory-hub`
- **运行用户**: `wen`
- **默认配置**: 5 个 Worker，30 秒轮询间隔

## 常用命令

### 启动服务

```bash
sudo systemctl start memory-hub-worker-pool
```

### 停止服务

```bash
sudo systemctl stop memory-hub-worker-pool
```

### 重启服务

```bash
sudo systemctl restart memory-hub-worker-pool
```

### 查看服务状态

```bash
sudo systemctl status memory-hub-worker-pool
```

### 查看服务是否运行

```bash
sudo systemctl is-active memory-hub-worker-pool
```

## 开机自启

### 启用开机自启

```bash
sudo systemctl enable memory-hub-worker-pool
```

### 禁用开机自启

```bash
sudo systemctl disable memory-hub-worker-pool
```

### 查看是否已启用

```bash
sudo systemctl is-enabled memory-hub-worker-pool
```

## 日志查看

### 实时查看日志

```bash
sudo journalctl -u memory-hub-worker-pool -f
```

### 查看最近 100 条日志

```bash
sudo journalctl -u memory-hub-worker-pool -n 100
```

### 查看今天的日志

```bash
sudo journalctl -u memory-hub-worker-pool --since today
```

### 查看某时间段日志

```bash
sudo journalctl -u memory-hub-worker-pool --since "2024-03-16 10:00" --until "2024-03-16 12:00"
```

## 故障排查

### 服务无法启动

1. **检查脚本权限**
   ```bash
   ls -la /home/wen/projects/memory-hub/scripts/start-worker-pool.sh
   chmod +x /home/wen/projects/memory-hub/scripts/start-worker-pool.sh
   ```

2. **检查 Docker 权限**
   ```bash
   # 确保 wen 用户在 docker 组
   groups wen
   # 如果没有 docker 组，添加
   sudo usermod -aG docker wen
   # 需要重新登录生效
   ```

3. **查看详细错误日志**
   ```bash
   sudo journalctl -u memory-hub-worker-pool -n 50 --no-pager
   ```

### 服务频繁重启

1. **检查重启原因**
   ```bash
   sudo journalctl -u memory-hub-worker-pool -n 100 | grep -i error
   ```

2. **检查 Docker 容器状态**
   ```bash
   docker ps -a | grep memory-hub
   ```

3. **手动运行启动脚本调试**
   ```bash
   cd /home/wen/projects/memory-hub
   bash scripts/start-worker-pool.sh 5 30
   ```

### Worker 状态异常

```bash
# 查看 Worker 状态
cd /home/wen/projects/memory-hub
bash scripts/worker-status.sh

# 查看 Docker 容器
docker ps | grep memory-hub-worker

# 查看 Docker 日志
docker logs memory-hub-worker-1
docker logs memory-hub-worker-2
```

## 服务配置

编辑服务文件后需要重载：

```bash
sudo systemctl daemon-reload
sudo systemctl restart memory-hub-worker-pool
```

## 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| Worker 数量 | 5 | 同时运行的小码数量 |
| 轮询间隔 | 30 秒 | 从任务队列获取任务的间隔 |
| 重启延迟 | 10 秒 | 服务失败后等待重启的时间 |

修改参数：编辑 `/etc/systemd/system/memory-hub-worker-pool.service` 中的 `ExecStart` 行。

## 相关脚本

- **启动脚本**: `scripts/start-worker-pool.sh`
- **停止脚本**: `scripts/stop-worker-pool.sh`
- **状态检查**: `scripts/worker-status.sh`
- **部署脚本**: `scripts/deploy-systemd.sh`

---

**最后更新**: 2026-03-16