# systemd 服务启动失败修复报告 - 第 3 次

**日期**: 2026-03-16  
**修复者**: 小审 🔴  
**状态**: ✅ 已修复

---

## 📋 问题描述

systemd 服务 `memory-hub-worker-pool.service` 启动失败，错误现象：
- 手动执行启动脚本成功
- systemd 服务启动失败，报错 "control process exited with error code"
- 日志显示小码已成功启动，但服务仍然失败

---

## 🔍 问题根因

**根本原因**: bash 脚本中的 `set -e` 与算术运算 `((SUCCESS_COUNT++))` 的兼容性问题

### 详细分析

1. **启动脚本行为**:
   - 脚本开头有 `set -e`（遇到错误立即退出）
   - 脚本中使用 `((SUCCESS_COUNT++))` 进行计数
   - 在 bash 中，`((expr))` 返回的是表达式的真假值，不是计算结果
   - 当 `SUCCESS_COUNT` 为 0 时，`((SUCCESS_COUNT++))` 返回 1（false）
   - `set -e` 捕获到这个非零退出码，触发脚本立即退出

2. **为什么手动测试成功**:
   - 手动执行时，即使脚本返回非零退出码，也不影响 worker 进程运行
   - 但 systemd 会检查 `ExecStart` 的退出码，非零即认为服务启动失败

3. **日志证据**:
   ```
   3 月 16 19:15:20 arch memory-hub-worker-pool[156282]:   ✅ 小码 1 已启动 (PID: 156292)
   3 月 16 19:15:20 arch systemd[1]: memory-hub-worker-pool.service: Control process exited, code=exited, status=1/FAILURE
   ```
   - 小码确实启动成功了
   - 但控制进程（启动脚本）返回了 status=1

---

## 🔧 修复方案

### 修改文件
`/home/wen/projects/memory-hub/scripts/start-worker-pool.sh`

### 修改内容

将 bash 算术运算从 `((var++))` 改为 `var=$((var + 1))`：

**修改前**:
```bash
((SUCCESS_COUNT++))
((FAIL_COUNT++))
```

**修改后**:
```bash
SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
FAIL_COUNT=$((FAIL_COUNT + 1))
```

### 为什么这样修复

- `var=$((var + 1))` 是赋值语句，始终返回 0（成功）
- `((var++))` 是算术评估，返回表达式的真假值（0 为 false，非 0 为 true）
- 在 `set -e` 模式下，只有赋值语句能保证不会因为返回非零而触发退出

---

## ✅ 验证结果

### 1. 脚本退出码测试
```bash
$ bash scripts/start-worker-pool.sh 1 30
...
🎉 小码池启动完成！
  成功：1 个
退出码：0  # ✅ 修复前为 1
```

### 2. systemd 服务状态
```bash
$ systemctl status memory-hub-worker-pool
● memory-hub-worker-pool.service - Memory Hub Worker Pool - 小码池服务
     Loaded: loaded (/etc/systemd/system/memory-hub-worker-pool.service; enabled)
     Active: active (running) ✅
     Process: 157754 ExecStart=/home/wen/projects/memory-hub/scripts/start-worker-pool.sh 5 30 (code=exited, status=0/SUCCESS) ✅
       Tasks: 14
     Memory: 147.2M
     CGroup: /system.slice/memory-hub-worker-pool.service
             ├─157764 python ... --agent-id team-coder1 ✅
             ├─157777 python ... --agent-id team-coder2 ✅
             ├─157787 python ... --agent-id team-coder3 ✅
             ├─157817 python ... --agent-id team-coder4 ✅
             └─157830 python ... --agent-id team-coder5 ✅
```

### 3. 所有小码正常运行
- team-coder1: PID 157764 ✅
- team-coder2: PID 157777 ✅
- team-coder3: PID 157787 ✅
- team-coder4: PID 157817 ✅
- team-coder5: PID 157830 ✅

---

## 📚 经验教训

### bash 陷阱
在 `set -e` 模式下使用算术运算时要格外小心：

| 写法 | 返回值 | 是否安全 |
|------|--------|---------|
| `((var++))` | 表达式的真假值（0=false） | ❌ 不安全 |
| `((var += 1))` | 表达式的真假值 | ❌ 不安全 |
| `var=$((var + 1))` | 始终为 0（成功） | ✅ 安全 |
| `((var++)) || true` | 始终为 0（成功） | ✅ 安全 |

### 最佳实践
1. 在 `set -e` 脚本中，优先使用 `var=$((var + 1))` 而非 `((var++))`
2. 如果必须使用 `((expr))`，加上 `|| true` 后缀
3. systemd 服务的 `ExecStart` 脚本必须返回 0 才算启动成功

---

## 🎯 修复完成确认

- [x] 问题根因已查明
- [x] 修复方案已实施
- [x] 脚本退出码测试通过（0）
- [x] systemd 服务启动成功
- [x] 5 个小码全部正常运行
- [x] 修复报告已生成

**服务现在可以正常使用了！** 🎉
