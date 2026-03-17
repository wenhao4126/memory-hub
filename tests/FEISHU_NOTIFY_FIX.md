# 飞书通知修复报告

**日期**: 2026-03-16
**作者**: 小码 🟡
**问题**: Worker 完成任务后不发送飞书通知

---

## 问题根因

### 1. 启动方式差异

| 启动方式 | 自动通告机制 | 适用场景 |
|---------|------------|---------|
| `sessions_spawn` | ✅ 生效 | OpenClaw 会话内启动 |
| **systemd 服务** | ❌ 不生效 | 独立后台服务 |

### 2. 原有设计问题

`agent_worker.py` 的 `_on_task_complete()` 和 `_on_task_error()` 方法：
- **原设计**: 返回包含 `message` 字段的字典，期望 OpenClaw 自动发送
- **实际**: systemd 启动的 Worker 没有会话上下文，OpenClaw 无法自动通告

---

## 修复方案

### 使用 OpenClaw CLI 主动发送消息

```bash
openclaw message send \
  --channel feishu \
  --target ou_c869d2aa0f7bacfefb13eb5fb7dd668a \
  --message "通知内容"
```

### 修改文件

**文件**: `/home/wen/projects/memory-hub/worker/agent_worker.py`

**修改内容**:

1. **添加导入**:
```python
import subprocess
```

2. **修改 `_on_task_complete()` 方法**:
```python
async def _on_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]):
    # ... 构建消息 ...
    
    # ✅ 使用 OpenClaw CLI 发送消息到飞书
    try:
        subprocess.run([
            'openclaw', 'message', 'send',
            '--channel', 'feishu',
            '--target', 'ou_c869d2aa0f7bacfefb13eb5fb7dd668a',
            '--message', message
        ], check=True, capture_output=True, text=True, timeout=30)
        
        logger.info(f"✅ 已发送飞书完成通知：{task_title}")
    except subprocess.TimeoutExpired:
        logger.error(f"❌ 发送飞书通知超时：{task_title}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 发送飞书通知失败：{task_title}, 错误: {e.stderr}")
    except Exception as e:
        logger.error(f"❌ 发送飞书通知异常：{task_title}, 错误: {e}")
```

3. **修改 `_on_task_error()` 方法**:
```python
async def _on_task_error(self, task: Dict[str, Any], error: str, retried: bool):
    # ... 构建消息 ...
    
    # ✅ 使用 OpenClaw CLI 发送消息到飞书
    try:
        subprocess.run([
            'openclaw', 'message', 'send',
            '--channel', 'feishu',
            '--target', 'ou_c869d2aa0f7bacfefb13eb5fb7dd668a',
            '--message', message
        ], check=True, capture_output=True, text=True, timeout=30)
        
        logger.info(f"✅ 已发送飞书失败通知：{task_title}")
    except subprocess.TimeoutExpired:
        logger.error(f"❌ 发送飞书通知超时：{task_title}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 发送飞书通知失败：{task_title}, 错误: {e.stderr}")
    except Exception as e:
        logger.error(f"❌ 发送飞书通知异常：{task_title}, 错误: {e}")
```

---

## 验证结果

### 测试任务

```bash
# 创建测试任务
python3 -c "
from sdk.task_service import TaskService
import asyncio

async def test():
    service = TaskService()
    task_id = await service.create_task(
        task_type='code',
        title='飞书通知测试 - OpenClaw CLI',
        description='测试任务完成后是否通过 OpenClaw CLI 发送到飞书',
        agent_type='coder'
    )
    print(f'✅ 任务已创建：{task_id}')

asyncio.run(test())
"
```

### 执行日志

```
2026-03-16 21:08:40 - INFO - coder 领取任务: ed311ebd-9a15-43b8-b974-4b9629f5021c
2026-03-16 21:08:40 - INFO - 开始执行任务: ed311ebd-9a15-43b8-b974-4b9629f5021c
2026-03-16 21:08:45 - INFO - [team-coder1] 任务完成: 飞书通知测试 - OpenClaw CLI
2026-03-16 21:08:45 - INFO - 任务完成: ed311ebd-9a15-43b8-b974-4b9629f5021c
2026-03-16 21:08:52 - INFO - ✅ 已发送飞书完成通知：飞书通知测试 - OpenClaw CLI
```

### 数据库状态

```
id: ed311ebd-9a15-43b8-b974-4b9629f5021c
title: 飞书通知测试 - OpenClaw CLI
status: completed
```

---

## 总结

✅ **问题已修复**

- Worker 完成任务后会主动调用 OpenClaw CLI 发送飞书通知
- 支持完成通知和失败通知
- 包含完善的错误处理和日志记录
- 飞书已收到完成通知

---

## 后续建议

1. **监控**: 定期检查日志，确保通知正常发送
2. **重试机制**: 如果发送失败，可以考虑添加重试逻辑
3. **目标配置**: 飞书用户 ID 目前硬编码，可以考虑从配置文件读取