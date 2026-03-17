# Systemd 服务部署报告

**部署时间**: 2026-03-16
**部署人员**: 小码 🟡
**服务名称**: memory-hub-worker-pool

---

## 一、部署目标

将 Memory Hub Worker Pool（小码池）注册为 systemd 服务，实现：
- ✅ 开机自启动
- ✅ 故障自动重启（10 秒延迟）
- ✅ 统一的日志管理
- ✅ 标准化的服务管理

---

## 二、部署前检查

### 2.1 脚本文件检查

| 文件 | 状态 | 权限 | 大小 |
|------|------|------|------|
| `scripts/start-worker-pool.sh` | ✅ 存在 | -rwxr-xr-x | 5491 字节 |
| `scripts/stop-worker-pool.sh` | ✅ 存在 | -rwxr-xr-x | 3231 字节 |

### 2.2 用户权限检查

用户 `wen` 属于以下组：
- `wen` - 用户主组
- `wheel` - 管理员组（sudo 权限）
- `docker` - Docker 用户组

**结论**: 用户有权运行 Docker 命令。

---

## 三、部署步骤

### 3.1 创建 systemd 服务文件

**文件位置**: `/etc/systemd/system/memory-hub-worker-pool.service`

**服务配置**:
```ini
[Unit]
Description=Memory Hub Worker Pool - 小码池服务
After=network.target docker.service
Wants=docker.service

[Service]
Type=forking
User=wen
Group=wen
WorkingDirectory=/home/wen/projects/memory-hub
ExecStart=/home/wen/projects/memory-hub/scripts/start-worker-pool.sh 5 30
ExecStop=/home/wen/projects/memory-hub/scripts/stop-worker-pool.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=memory-hub-worker-pool

[Install]
WantedBy=multi-user.target
```

### 3.2 部署脚本

创建了自动化部署脚本：`scripts/deploy-systemd.sh`

**功能**:
- 创建 systemd 服务文件
- 重载 systemd 配置
- 启用开机自启
- 启动服务
- 显示服务状态

**使用方法**:
```bash
sudo bash scripts/deploy-systemd.sh
```

---

## 四、验证结果

### 4.1 服务状态验证

执行部署脚本后，验证以下内容：

```bash
# 查看服务状态
sudo systemctl status memory-hub-worker-pool

# 查看是否启用开机自启
sudo systemctl is-enabled memory-hub-worker-pool

# 查看服务是否运行
sudo systemctl is-active memory-hub-worker-pool

# 查看 Worker 状态
bash scripts/worker-status.sh
```

### 4.2 日志验证

```bash
# 查看服务日志
sudo journalctl -u memory-hub-worker-pool -f
```

---

## 五、文档输出

### 5.1 创建的文件

| 文件路径 | 说明 |
|----------|------|
| `scripts/deploy-systemd.sh` | 自动化部署脚本 |
| `docs/SYSTEMD_SERVICE.md` | 服务管理文档 |
| `tests/SYSTEMD_DEPLOYMENT.md` | 本部署报告 |

### 5.2 服务文件

| 文件路径 | 说明 |
|----------|------|
| `/etc/systemd/system/memory-hub-worker-pool.service` | Systemd 服务定义 |

---

## 六、常用命令速查

```bash
# 启动服务
sudo systemctl start memory-hub-worker-pool

# 停止服务
sudo systemctl stop memory-hub-worker-pool

# 重启服务
sudo systemctl restart memory-hub-worker-pool

# 查看状态
sudo systemctl status memory-hub-worker-pool

# 查看日志
sudo journalctl -u memory-hub-worker-pool -f

# 查看是否开机自启
sudo systemctl is-enabled memory-hub-worker-pool

# 禁用开机自启
sudo systemctl disable memory-hub-worker-pool
```

---

## 七、注意事项

1. **首次部署** 需要执行：
   ```bash
   sudo bash scripts/deploy-systemd.sh
   ```

2. **修改配置后** 需要：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart memory-hub-worker-pool
   ```

3. **故障恢复**：服务失败后 10 秒自动重启

4. **日志位置**：使用 systemd journal，通过 `journalctl` 查看

---

## 八、后续建议

1. **监控告警**：可考虑添加 Prometheus/Grafana 监控
2. **日志轮转**：systemd journal 默认有日志轮转机制
3. **健康检查**：可在启动脚本中添加健康检查逻辑

---

**部署状态**: ⏳ 待执行（需要 sudo 密码）

**执行命令**:
```bash
sudo bash scripts/deploy-systemd.sh
```

---

*报告生成时间: 2026-03-16 18:14*
*生成者: 小码 🟡*