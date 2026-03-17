# Systemd 服务启动修复报告

**日期**: 2026-03-16
**作者**: 小码 🟡

---

## 问题描述

systemd 服务 `memory-hub-worker-pool.service` 启动失败，显示 exit-code=1/FAILURE。

---

## 问题根因分析

经过排查，发现 **3 个问题**：

### 1. 交互式提示导致脚本挂起

**问题**：
```bash
# 原代码（第 60-70 行）
RUNNING_COUNT=$(ps aux | grep "agent_worker.py" | grep -v grep | wc -l)
if [ "$RUNNING_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  检测到 $RUNNING_COUNT 个小码已在运行${NC}"
    echo -e "  ${YELLOW}提示：如需重启，请先运行 bash scripts/stop-worker-pool.sh${NC}"
    echo ""
    read -p "是否继续启动新的小码？(y/N) " -n 1 -r  # ❌ 在 systemd 中会挂起！
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}已取消启动${NC}"
        exit 0
    fi
fi
```

**原因**：
- `read -p` 会等待用户输入
- systemd 服务没有 TTY，脚本会一直挂起等待输入
- 导致服务超时失败

**修复**：
```bash
# 检查是否在交互式终端中运行
if [ -t 0 ]; then
    read -p "是否继续启动新的小码？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}已取消启动${NC}"
        exit 0
    fi
else
    echo -e "${YELLOW}非交互模式，跳过确认，直接继续启动${NC}"
fi
```

---

### 2. Grep 匹配错误

**问题**：
```bash
# 原代码
RUNNING_COUNT=$(ps aux | grep "agent_worker.py" | grep -v grep | wc -l)
```

**原因**：
- 脚本检查的是 `agent_worker.py`
- 但实际启动的是 `worker_cli.py`
- 导致检测不准确

**修复**：
```bash
RUNNING_COUNT=$(ps aux | grep "worker_cli.py" | grep -v grep | wc -l)
```

---

### 3. Daemon 模式与 systemd 不兼容

**问题**：
```bash
# 原代码
nohup python "$WORKER_SCRIPT" \
    --agent-id "$AGENT_ID" \
    --poll-interval "$POLL_INTERVAL" \
    --daemon \
    > "$LOG_FILE" 2>&1 &
```

**原因**：
- `--daemon` 会触发二次 fork，进程立即退出
- systemd `Type=forking` 期望的是主进程 fork 后退出，但守护进程逻辑导致追踪混乱
- PID 文件没有正确生成

**修复**：
```bash
# 移除 --daemon 参数，使用 nohup 替代
nohup python "$WORKER_SCRIPT" \
    --agent-id "$AGENT_ID" \
    --poll-interval "$POLL_INTERVAL" \
    --pid-file "$PID_FILE" \
    > "$LOG_FILE" 2>&1 &

# 等待进程启动并检查
sleep 1

# 检查进程是否成功启动（通过 PID 文件或进程列表）
if [ -f "$PID_FILE" ]; then
    ACTUAL_PID=$(cat "$PID_FILE")
    if ps -p $ACTUAL_PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 小码$i 已启动${NC} (PID: $ACTUAL_PID)"
        ((SUCCESS_COUNT++))
    else
        echo -e "  ${RED}❌ 小码$i 启动失败（进程已退出）${NC}"
        ((FAIL_COUNT++))
    fi
elif ps -p $WORKER_PID > /dev/null 2>&1; then
    # 备用：检查 nohup 进程
    echo $WORKER_PID > "$PID_FILE"
    echo -e "  ${GREEN}✅ 小码$i 已启动${NC} (PID: $WORKER_PID)"
    ((SUCCESS_COUNT++))
else
    echo -e "  ${RED}❌ 小码$i 启动失败${NC}"
    ((FAIL_COUNT++))
fi
```

---

## 修复步骤

### 1. 修改启动脚本
```bash
# 文件：/home/wen/projects/memory-hub/scripts/start-worker-pool.sh

# 修改 1：移除交互式提示（第 60-80 行）
# 修改 2：修复 grep 匹配（第 60 行）
# 修改 3：移除 --daemon 参数（第 100 行）
# 修改 4：添加 PID 文件检查逻辑（第 110-130 行）
```

### 2. 测试启动脚本
```bash
cd /home/wen/projects/memory-hub
bash scripts/start-worker-pool.sh 1 30
```

**验证结果**：
```
🔍 前置检查...
  ✓ 日志目录: /home/wen/projects/memory-hub/logs
  ✓ PID 目录: /tmp/memory-hub-workers
  ✓ Python: Python 3.14.3

🚀 启动小码池...
  小码数量: 1
  轮询间隔: 30秒

启动小码1 (team-coder1)...
  ✅ 小码1 已启动 (PID: 155042)
     日志: /home/wen/projects/memory-hub/logs/worker-1.log

🎉 小码池启动完成！
  成功: 1 个
```

### 3. 重启 systemd 服务
```bash
# 需要 root 权限
sudo systemctl daemon-reload
sudo systemctl restart memory-hub-worker-pool
sudo systemctl status memory-hub-worker-pool
```

---

## 验证方法

### 1. 检查服务状态
```bash
sudo systemctl status memory-hub-worker-pool
```

期望输出：
```
Active: active (running)
```

### 2. 检查进程
```bash
ps aux | grep worker_cli | grep -v grep
```

期望输出：
```
wen  xxx  ... python /home/wen/projects/memory-hub/worker/worker_cli.py --agent-id team-coder1 --poll-interval 30 --pid-file /tmp/memory-hub-workers/worker-1.pid
```

### 3. 检查日志
```bash
tail -f /home/wen/projects/memory-hub/logs/worker-1.log
```

期望输出：
```
2026-03-16 19:10:37,264 - __main__ - INFO - 启动 Worker: team-coder1
2026-03-16 19:10:37,264 - sdk.task_service - INFO - TaskService 初始化
2026-03-16 19:10:37,265 - worker.agent_worker - INFO - 工作器启动: coder (team-coder1)
```

### 4. 使用 worker-status.sh
```bash
bash /home/wen/projects/memory-hub/scripts/worker-status.sh
```

---

## 总结

| 问题 | 修复 |
|------|------|
| 交互式提示导致脚本挂起 | 添加 `[ -t 0 ]` 检查，非交互模式跳过 |
| Grep 匹配错误 | 从 `agent_worker.py` 改为 `worker_cli.py` |
| Daemon 模式与 systemd 不兼容 | 移除 `--daemon`，使用 nohup + PID 文件 |

---

## 下一步

**需要用户手动执行**（我没有 sudo 权限）：

```bash
# 1. 重新加载 systemd 配置
sudo systemctl daemon-reload

# 2. 重启服务
sudo systemctl restart memory-hub-worker-pool

# 3. 检查状态
sudo systemctl status memory-hub-worker-pool

# 4. 查看日志
sudo journalctl -u memory-hub-worker-pool -n 50 --no-pager
```

---

**修复完成！等待用户验证。**