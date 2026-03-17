# 小码池（Worker Pool）使用指南

> **作者**: 小码 🟡  
> **日期**: 2026-03-16  
> **版本**: 1.0.0

---

## 📖 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [快速开始](#快速开始)
4. [命令详解](#命令详解)
5. [配置说明](#配置说明)
6. [日志管理](#日志管理)
7. [故障排查](#故障排查)
8. [高级用法](#高级用法)

---

## 概述

### 什么是小码池？

小码池（Worker Pool）是一个多进程任务处理系统，用于并行处理数据库中的任务队列。

### 核心特性

- ✅ **多进程并行**：支持启动多个 Worker 进程同时处理任务
- ✅ **自动轮询**：Worker 自动从数据库获取待处理任务
- ✅ **负载均衡**：多个 Worker 竞争获取任务，自动负载均衡
- ✅ **失败重试**：任务失败后自动重试（可配置重试次数）
- ✅ **进度追踪**：实时更新任务进度到数据库
- ✅ **日志分离**：每个 Worker 独立日志文件，便于排查问题
- ✅ **守护进程**：支持后台运行，不依赖终端会话

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      小码池架构图                            │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   任务提交 API    │
                    │  (POST /tasks)   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │  parallel_tasks  │
                    │   任务队列表      │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
     ┌──────────┐     ┌──────────┐     ┌──────────┐
     │ 小码 1   │     │ 小码 2   │     │ 小码 N   │
     │team-coder1│    │team-coder2│    │team-coderN│
     │ Worker   │     │ Worker   │     │ Worker   │
     └──────────┘     └──────────┘     └──────────┘
         │                │                │
         ▼                ▼                ▼
    worker-1.log    worker-2.log    worker-N.log
```

### 工作流程

1. **任务提交**：通过 API 或直接插入数据库创建任务
2. **任务轮询**：Worker 定期查询 `pending` 状态的任务
3. **任务领取**：使用 `SELECT FOR UPDATE SKIP LOCKED` 实现原子领取
4. **任务执行**：Worker 调用处理器执行任务逻辑
5. **状态更新**：更新任务状态为 `running` → `completed` 或 `failed`

---

## 快速开始

### 1. 启动小码池

```bash
# 默认启动 5 个小码，30 秒轮询间隔
bash scripts/start-worker-pool.sh

# 自定义：启动 3 个小码，10 秒轮询间隔
bash scripts/start-worker-pool.sh 3 10
```

### 2. 查看状态

```bash
# 查看运行状态
bash scripts/worker-status.sh

# 查看完整信息（包括最近完成的任务）
bash scripts/worker-status.sh --full
```

### 3. 查看日志

```bash
# 查看所有小码日志
tail -f logs/worker-*.log

# 查看特定小码日志
tail -f logs/worker-1.log
```

### 4. 停止小码池

```bash
# 正常停止
bash scripts/stop-worker-pool.sh

# 强制停止（如果正常停止失败）
bash scripts/stop-worker-pool.sh --force
```

---

## 命令详解

### start-worker-pool.sh

启动小码池。

**用法**：
```bash
bash scripts/start-worker-pool.sh [小码数量] [轮询间隔]
```

**参数**：
- `小码数量`：启动的 Worker 进程数量（默认：5）
- `轮询间隔`：轮询数据库的间隔秒数（默认：30）

**示例**：
```bash
# 启动 10 个小码，15 秒轮询
bash scripts/start-worker-pool.sh 10 15
```

**输出**：
```
🚀 启动小码池...
  小码数量: 5
  轮询间隔: 30秒

启动小码1 (team-coder1)...
  ✅ 小码1 已启动 (PID: 12345)
     日志: /home/wen/projects/memory-hub/logs/worker-1.log

🎉 小码池启动完成！
  成功: 5 个
```

---

### stop-worker-pool.sh

停止小码池。

**用法**：
```bash
bash scripts/stop-worker-pool.sh [--force]
```

**参数**：
- `--force`：强制停止（使用 `kill -9`）

**示例**：
```bash
# 正常停止
bash scripts/stop-worker-pool.sh

# 强制停止
bash scripts/stop-worker-pool.sh --force
```

---

### worker-status.sh

查看小码池状态。

**用法**：
```bash
bash scripts/worker-status.sh [--full]
```

**参数**：
- `--full`：显示完整信息（包括最近完成的任务详情）

**输出示例**：
```
╔══════════════════════════════════════════╗
║       📊 小码池状态监控面板              ║
╚══════════════════════════════════════════╝

🤖 运行中的小码
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ● team-coder1
    PID: 12345  CPU: 2.5%  MEM: 1.2%
  ● team-coder2
    PID: 12346  CPU: 0.0%  MEM: 1.1%

🗄️  数据库状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ 数据库容器运行中

📋 任务队列
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  待处理: 3 个任务
  运行中: 1 个任务
  今日完成: 15 个任务
  失败: 0 个任务
```

---

## 配置说明

### 环境变量

在 `.env` 文件中配置：

```bash
# 数据库连接
DATABASE_URL=postgresql://memory_user:password@localhost:5432/memory_hub

# Worker 配置
WORKER_POLL_INTERVAL=30      # 轮询间隔（秒）
WORKER_MAX_RETRIES=3         # 最大重试次数
WORKER_TIMEOUT=3600          # 任务超时时间（秒）
```

### Worker 数量建议

| 场景 | Worker 数量 | 轮询间隔 |
|------|------------|---------|
| 开发测试 | 1-2 | 10 秒 |
| 小规模生产 | 3-5 | 30 秒 |
| 高并发场景 | 10+ | 15 秒 |

**注意**：Worker 数量不宜过多，建议不超过 CPU 核心数的 2 倍。

---

## 日志管理

### 日志位置

```
/home/wen/projects/memory-hub/logs/
├── worker-1.log    # 小码1 日志
├── worker-2.log    # 小码2 日志
├── worker-3.log    # 小码3 日志
├── worker-4.log    # 小码4 日志
└── worker-5.log    # 小码5 日志
```

### 日志格式

```
2026-03-16 16:30:00,123 - worker.agent_worker - INFO - 启动 Worker: team-coder1
2026-03-16 16:30:30,456 - worker.agent_worker - INFO - [team-coder1] 领取任务: task-uuid-xxx
2026-03-16 16:30:31,789 - worker.agent_worker - INFO - [team-coder1] 开始处理任务: 测试任务
2026-03-16 16:30:35,012 - worker.agent_worker - INFO - [team-coder1] 任务完成: 测试任务
```

### 日志轮转

建议使用 `logrotate` 管理日志：

```bash
# /etc/logrotate.d/memory-hub-worker
/home/wen/projects/memory-hub/logs/worker-*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 wen wen
}
```

---

## 故障排查

### 问题 1：小码启动失败

**症状**：
```
❌ 小码1 启动失败
   请查看日志: logs/worker-1.log
```

**排查步骤**：
1. 查看日志文件：`cat logs/worker-1.log`
2. 检查 Python 环境：`python --version`
3. 检查依赖：`pip list | grep asyncpg`
4. 检查数据库连接：`docker ps | grep memory-hub-db`

---

### 问题 2：任务一直 pending

**症状**：
```
待处理: 10 个任务
运行中: 0 个任务
```

**排查步骤**：
1. 检查小码是否运行：`bash scripts/worker-status.sh`
2. 检查任务类型是否匹配：
   ```sql
   SELECT DISTINCT task_type FROM parallel_tasks WHERE status='pending';
   ```
3. 检查 Worker 支持的类型：查看日志中的 `支持类型` 信息

---

### 问题 3：任务失败

**症状**：
```
失败: 5 个任务
```

**排查步骤**：
1. 查看失败原因：
   ```sql
   SELECT title, error_message, retry_count 
   FROM parallel_tasks 
   WHERE status='failed' 
   ORDER BY updated_at DESC;
   ```
2. 检查错误日志：`grep ERROR logs/worker-*.log`
3. 手动重试：
   ```sql
   UPDATE parallel_tasks 
   SET status='pending', retry_count=0 
   WHERE id='task-uuid';
   ```

---

### 问题 4：数据库连接失败

**症状**：
```
❌ 数据库容器未运行: memory-hub-db
```

**解决方法**：
```bash
# 启动数据库
cd /home/wen/projects/memory-hub
docker-compose up -d db

# 检查连接
docker exec memory-hub-db psql -U memory_user -d memory_hub -c "SELECT 1;"
```

---

## 高级用法

### 1. 注册为系统服务

```bash
# 复制服务文件
sudo cp scripts/memory-hub-worker-pool.service /etc/systemd/system/

# 重载 systemd
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable memory-hub-worker-pool

# 启动服务
sudo systemctl start memory-hub-worker-pool

# 查看状态
sudo systemctl status memory-hub-worker-pool
```

### 2. 单独启动某个小码

```bash
# 前台运行（调试用）
python worker/worker_cli.py --agent-id team-coder1 --poll-interval 30

# 后台运行
python worker/worker_cli.py --agent-id team-coder1 --poll-interval 30 --daemon
```

### 3. 监控脚本

创建定时监控脚本：

```bash
# /home/wen/projects/memory-hub/scripts/monitor-workers.sh
#!/bin/bash

# 检查小码是否运行
RUNNING=$(ps aux | grep "agent_worker.py" | grep -v grep | wc -l)

if [ "$RUNNING" -eq 0 ]; then
    echo "⚠️ 没有运行中的小码，正在重启..."
    bash /home/wen/projects/memory-hub/scripts/start-worker-pool.sh 5 30
fi
```

添加到 crontab：
```bash
# 每 5 分钟检查一次
*/5 * * * * /home/wen/projects/memory-hub/scripts/monitor-workers.sh
```

---

## 文件清单

```
/home/wen/projects/memory-hub/
├── scripts/
│   ├── start-worker-pool.sh          # 启动脚本
│   ├── stop-worker-pool.sh           # 停止脚本
│   ├── worker-status.sh              # 状态查看脚本
│   └── memory-hub-worker-pool.service # systemd 服务文件
├── worker/
│   ├── agent_worker.py               # Worker 基类
│   └── worker_cli.py                 # 命令行入口
├── logs/
│   └── worker-*.log                  # Worker 日志文件
└── docs/
    └── WORKER_POOL.md                # 本文档
```

---

## 更新日志

### v1.0.0 (2026-03-16)
- ✅ 初始版本
- ✅ 支持多进程并行
- ✅ 支持守护进程模式
- ✅ 支持状态监控
- ✅ 支持 systemd 服务

---

**有问题？** 查看日志或联系小码 🟡